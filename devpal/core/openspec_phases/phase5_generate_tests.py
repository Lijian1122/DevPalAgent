# -*- coding: utf-8 -*-
"""Phase 5: 生成测试文档并验证测试文件

流程：
1. 扫描 tests/ 目录，验证测试文件存在
2. 为每个测试文件生成详细的测试文档
3. 测试文档包含：测试用例列表、测试目标、预期结果等
4. 文档保存到 docs/test_*.md
"""

from pathlib import Path
from .base import PhaseInterface, PhaseResult, OpenSpecContext
from .parallel_executor import ParallelTask, ParallelTaskResult, PhaseParallelExecutor

class Phase5GenerateTests(PhaseInterface):
    """Phase 5: 验证测试文件并生成测试文档"""

    def __init__(self, context: OpenSpecContext, tool_registry):
        super().__init__(context)
        self.phase_number = 5
        self.phase_name = "Generate test documentation"
        self.tool_registry = tool_registry

    def should_skip(self) -> tuple:
        """判断是否应该跳过当前阶段"""
        from .phase_skip_rules import should_skip_for_non_cpp_project
        return should_skip_for_non_cpp_project(self.phase_number, self.context)

    def execute(self) -> PhaseResult:
        self.log("Phase 5: scanning tests/ and generating test documentation...")

        tests_dir = self.context.project_dir / "tests"
        if not tests_dir.exists():
            self.log("  [WARN] tests/ directory not found")
            return PhaseResult.fail(
                "tests/ directory missing",
                errors=["tests directory does not exist"],
            )

        # Check for test files based on language
        language = self.context.language
        if language == 'cpp':
            test_files = sorted(tests_dir.glob("test_*.cpp"))
            test_pattern = "test_*.cpp"
        elif language == 'python':
            test_files = sorted(tests_dir.glob("test_*.py"))
            test_pattern = "test_*.py"
        elif language == 'shell':
            test_files = sorted(tests_dir.glob("test_*.sh"))
            test_pattern = "test_*.sh"
        else:
            test_files = []
            test_pattern = "test_*"

        if not test_files:
            self.log(f"  [WARN] no {test_pattern} files found in tests/")
            return PhaseResult.fail(
                "No test files found",
                errors=[f"expected at least one tests/{test_pattern}"],
            )

        self.log("  [OK] found {} test file(s)".format(len(test_files)))
        for tf in test_files:
            self.log("    - {} ({} bytes)".format(tf.name, tf.stat().st_size))

        docs_dir = self.context.project_dir / "docs"
        docs_dir.mkdir(exist_ok=True)

        tasks = [self._build_test_doc_task(test_file, docs_dir) for test_file in test_files]
        max_concurrency = getattr(self.context, "phase5_max_concurrency", 3)
        executor = PhaseParallelExecutor(
            max_concurrency=max_concurrency,
            retry_limit=1,
            serial_fallback=True,
            log=self.log,
            event_integration=getattr(self.context, "event_integration", None),
        )
        results = executor.execute(tasks, self._generate_test_doc_task)
        parallel_summary = executor.aggregate(results)
        self.context.parallel_execution_stats[str(self.phase_number)] = parallel_summary
        event_integration = getattr(self.context, "event_integration", None)
        if event_integration:
            event_integration.emit_phase_parallel_summary(
                self.phase_number,
                parallel_summary,
                executor.max_concurrency,
            )

        test_docs_generated = [
            str(result.artifact_path)
            for result in results
            if result.success and result.artifact_path
        ]
        errors = [
            result.error or f"Failed to generate doc for {result.task_id}"
            for result in results
            if not result.success
        ]

        test_doc_summary = {
            "phase": self.phase_number,
            "test_count": len(test_files),
            "docs_generated": len(test_docs_generated),
            "doc_paths": test_docs_generated,
            "errors": errors,
            "parallel_summary": parallel_summary,
        }
        self.context.test_docs = test_docs_generated
        self.context.test_doc_summary = test_doc_summary

        if errors:
            return PhaseResult.ok(
                f"Test files verified, {len(test_docs_generated)}/{len(test_files)} docs generated",
                test_count=len(test_files),
                files=[tf.name for tf in test_files],
                test_docs=test_docs_generated,
                errors=errors,
                parallel_summary=parallel_summary,
                test_doc_summary=test_doc_summary,
            )

        return PhaseResult.ok(
            f"Test files verified and {len(test_docs_generated)} test docs generated",
            test_count=len(test_files),
            files=[tf.name for tf in test_files],
            test_docs=test_docs_generated,
            parallel_summary=parallel_summary,
            test_doc_summary=test_doc_summary,
        )

    def _build_test_doc_task(self, test_file: Path, docs_dir: Path) -> ParallelTask:
        source_file = self._find_source_file(test_file)
        doc_file = docs_dir / f"test_{test_file.stem}_doc.md"
        return ParallelTask(
            task_id=f"phase5:{test_file.name}",
            phase_number=self.phase_number,
            task_type="test_doc",
            input_payload={
                "test_file": test_file,
                "source_file": source_file,
                "doc_file": doc_file,
            },
        )

    def _generate_test_doc_task(self, task: ParallelTask) -> ParallelTaskResult:
        test_file = task.input_payload["test_file"]
        source_file = task.input_payload["source_file"]
        doc_file = task.input_payload["doc_file"]

        self.log(f"  [DOC] Generating test documentation for {test_file.name}...")
        result = self.tool_registry.execute_tool('test_doc_generator', {
            'file_path': str(source_file) if source_file else str(test_file),
            'output_doc': str(doc_file),
            'test_file': str(test_file)
        })

        if result.success:
            test_cases_count = result.metadata.get('test_cases_generated', 0)
            self.log(f"    [OK] Test doc generated: {doc_file.name} ({test_cases_count} test cases)")
            return ParallelTaskResult(
                task_id=task.task_id,
                success=True,
                artifact_path=doc_file,
                metadata={
                    "test_file": test_file.name,
                    "test_cases_generated": test_cases_count,
                },
            )

        error = result.error_message or result.content or "unknown test_doc_generator failure"
        self.log(f"    [FAIL] {error}")
        return ParallelTaskResult(
            task_id=task.task_id,
            success=False,
            error=f"Failed to generate doc for {test_file.name}: {error}",
            metadata={"test_file": test_file.name},
        )

    def _find_source_file(self, test_file: Path) -> Path:
        """根据测试文件名查找对应的源文件"""
        # test_login_service.cpp -> login_service.cpp
        source_name = test_file.name.replace('test_', '')

        # 在 src/ 目录查找
        src_dir = self.context.project_dir / "src"
        source_file = src_dir / source_name

        if source_file.exists():
            return source_file

        # 如果找不到，返回 test_file 本身
        return test_file
