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

class Phase5GenerateTests(PhaseInterface):
    """Phase 5: 验证测试文件并生成测试文档"""

    def __init__(self, context: OpenSpecContext, tool_registry):
        super().__init__(context)
        self.phase_number = 5
        self.phase_name = "Generate test documentation"
        self.tool_registry = tool_registry

    def execute(self) -> PhaseResult:
        self.log("Phase 5: scanning tests/ and generating test documentation...")

        tests_dir = self.context.project_dir / "tests"
        if not tests_dir.exists():
            self.log("  [WARN] tests/ directory not found")
            return PhaseResult.fail(
                "tests/ directory missing",
                errors=["tests directory does not exist"],
            )

        test_files = sorted(tests_dir.glob("test_*.cpp"))
        if not test_files:
            self.log("  [WARN] no test_*.cpp files found in tests/")
            return PhaseResult.fail(
                "No test files found",
                errors=["expected at least one tests/test_*.cpp"],
            )

        self.log("  [OK] found {} test file(s)".format(len(test_files)))
        for tf in test_files:
            self.log("    - {} ({} bytes)".format(tf.name, tf.stat().st_size))

        # 生成测试文档
        docs_dir = self.context.project_dir / "docs"
        docs_dir.mkdir(exist_ok=True)

        test_docs_generated = []
        errors = []

        for test_file in test_files:
            try:
                # 找到对应的源文件
                source_file = self._find_source_file(test_file)

                # 生成测试文档
                doc_file = docs_dir / f"test_{test_file.stem}_doc.md"

                self.log(f"  [DOC] Generating test documentation for {test_file.name}...")

                # 使用 test_doc_generator 工具
                result = self.tool_registry.execute_tool('test_doc_generator', {
                    'file_path': str(source_file) if source_file else str(test_file),
                    'output_doc': str(doc_file),
                    'test_file': str(test_file)
                })

                if result.success:
                    test_docs_generated.append(str(doc_file))
                    test_cases_count = result.metadata.get('test_cases_generated', 0)
                    self.log(f"    [OK] Test doc generated: {doc_file.name} ({test_cases_count} test cases)")
                else:
                    errors.append(f"Failed to generate doc for {test_file.name}: {result.content}")
                    self.log(f"    [FAIL] {result.content}")

            except Exception as exc:
                error_msg = f"Error generating doc for {test_file.name}: {exc}"
                errors.append(error_msg)
                self.log(f"    [ERROR] {error_msg}")

        # 保存测试文档路径到 context，供 Phase 10 使用
        # 保存测试文档路径到 context，供 Phase 10 使用
        self.context.test_docs = test_docs_generated

        if errors:
            return PhaseResult.ok(
                f"Test files verified, {len(test_docs_generated)}/{len(test_files)} docs generated",
                test_count=len(test_files),
                files=[tf.name for tf in test_files],
                test_docs=test_docs_generated,
                errors=errors
            )

        return PhaseResult.ok(
            f"Test files verified and {len(test_docs_generated)} test docs generated",
            test_count=len(test_files),
            files=[tf.name for tf in test_files],
            test_docs=test_docs_generated
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
