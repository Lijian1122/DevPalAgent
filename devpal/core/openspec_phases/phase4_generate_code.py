# -*- coding: utf-8 -*-
"""Phase 4: Generate core implementation code via templates + AI.

Step 1: apply infrastructure templates (CMake, README, skeleton, test_base).
Step 2: invoke Claude with a write_file tool to emit business headers,
        implementations, main.cpp, and unit tests.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ..compiledb import CompileDB
from ..llm_client import get_llm_client
from ..prompts import get_prompt_engine
from ..templates import TemplateContext, registry
from ..templates.install_script_generator import InstallScriptGenerator
from .base import OpenSpecContext, PhaseInterface, PhaseResult
from .parallel_executor import ParallelTask, ParallelTaskResult, PhaseParallelExecutor
from .phase4_file_plan import Phase4FilePlanner

_WRITE_FILE_TOOL: Dict[str, Any] = {
    "name": "write_file",
    "description": (
        "Write a single source file. Path is relative to project root. "
        "Overwrites if path exists."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Project-relative path (e.g. include/user.h)",
            },
            "content": {
                "type": "string",
                "description": "Full file content to write.",
            },
            "description": {
                "type": "string",
                "description": "Optional human-readable description.",
            },
        },
        "required": ["path", "content"],
    },
}


class Phase4GenerateCode(PhaseInterface):
    """Phase 4: infrastructure templates + AI-generated business code."""

    def __init__(self, context: OpenSpecContext, tool_registry):
        super().__init__(context)
        self.phase_number = 4
        self.phase_name = "Generate core code"
        self.tool_registry = tool_registry
        self.compiledb = CompileDB()
        self.skipped_files = []  # Track skipped files for better reporting

    def _read_change_artifacts(self) -> Dict[str, str]:
        """Read change directory artifacts if available (M2 implementation)"""
        artifacts = {}

        if not self.context.current_change_dir:
            return artifacts

        # 从变更目录读取关键产物
        artifacts = {}

        # 读取 spec.md（设计规范）
        spec_path = self.context.current_change_dir / "specs" / "spec.md"
        if spec_path.exists():
            artifacts["spec"] = spec_path.read_text(encoding="utf-8")
        self.log("  [M2] Read spec.md from change directory")

        # 读取 tasks.md（任务清单）
        tasks_path = self.context.current_change_dir / "tasks.md"
        if tasks_path.exists():
            artifacts["tasks"] = tasks_path.read_text(encoding="utf-8")
            self.log("  [M2] Read tasks.md from change directory")

        # 读取 design.md（设计文档）
        design_path = self.context.current_change_dir / "design.md"
        if design_path.exists():
            artifacts["design"] = design_path.read_text(encoding="utf-8")
            self.log("  [M2] Read design.md from change directory")
        return artifacts

    def execute(self) -> PhaseResult:
        self.log("Phase 4 start: infrastructure templates + AI code generation")
        self.skipped_files = []  # Reset for each execution (important for retries)
        project_dir = self.context.project_dir
        project_name = self.context.project_name or "myproject"
        project_dir.mkdir(parents=True, exist_ok=True)

        infra_files, infra_errors = self._apply_infrastructure_templates(project_name)
        self.log("  [Infra] generated {} scaffolding files".format(len(infra_files)))

        # 检查增量模式和需求变更
        force_regenerate = bool(getattr(self.context, "force_regenerate_code", False))
        requirements_delta = getattr(self.context, "requirements_delta", {})
        delta_changed = requirements_delta.get("changed", False)

        # 如果需求未变更且不强制重新生成，跳过 AI 生成
        existing_business_files = self._find_existing_business_files(
            project_dir, project_name
        )
        if self._is_installer_project():
            script_files = [
                path.resolve()
                for path in InstallScriptGenerator().generate_all(
                    project_dir / "scripts"
                )
            ]
            self.context.ai_generated_files.extend(script_files)
            self.context.generated_files.extend(infra_files + script_files)
            for req in self.context.structured_requirements or []:
                self.context.update_requirement_status(req.get("id", ""), "IN_PROGRESS")
            self._update_artifact_graph(project_dir, script_files)
            self.compiledb.index_project(project_dir, use_cache=False)
            self.compiledb.save_cache(project_dir)
            return PhaseResult.ok(
                "Phase 4 complete: generated installer scripts",
                infra_count=len(infra_files),
                ai_count=len(script_files),
                total_files=len(infra_files) + len(script_files),
                deterministic_installer=True,
            )

        if existing_business_files and not force_regenerate and not delta_changed:
            self.log(
                "  [INCREMENTAL] No requirement changes detected, skipping AI generation"
            )
            self.context.ai_generated_files.extend(existing_business_files)
            self.context.generated_files.extend(infra_files + existing_business_files)
            self.compiledb.index_project(project_dir, use_cache=False)
            self.compiledb.save_cache(project_dir)
            return PhaseResult.ok(
                "Phase 4 skipped: no requirement changes",
                infra_count=len(infra_files),
                ai_count=0,
                reused_count=len(existing_business_files),
                total_files=len(infra_files) + len(existing_business_files),
                skipped_ai_generation=True,
                incremental_mode=True,
            )

        # 选择性文件重新生成：如果有需求变更，确定受影响的文件
        affected_requirements = []
        if delta_changed and not force_regenerate:
            affected_requirements = requirements_delta.get(
                "added", []
            ) + requirements_delta.get("modified", [])
            if affected_requirements:
                self.log(
                    "  [SELECTIVE] Requirements changed: {}".format(
                        ", ".join(affected_requirements)
                    )
                )
                # 使用 ArtifactGraph 确定受影响的文件（如果可用）
                affected_files = self._get_affected_files_from_graph(
                    affected_requirements
                )
                if affected_files:
                    self.log(
                        "  [SELECTIVE] Will regenerate {} affected files".format(
                            len(affected_files)
                        )
                    )
                    # 将受影响的文件信息存储到 context
                    self.context.selective_regenerate_files = affected_files
                else:
                    self.log(
                        "  [SELECTIVE] Cannot determine affected files, will regenerate all"
                    )

        # Check if we should skip AI generation

        delta = self.context.requirements_delta

        delta_changed = delta.get("changed", False) if delta else False

        if existing_business_files and not force_regenerate and not delta_changed:
            self.log(
                "  [SKIP] business code already exists and requirements unchanged; use --force-regenerate-code to regenerate"
            )
            self.context.ai_generated_files.extend(existing_business_files)
            self.context.generated_files.extend(infra_files + existing_business_files)
            self.compiledb.index_project(project_dir, use_cache=False)
            self.compiledb.save_cache(project_dir)
            return PhaseResult.ok(
                "Phase 4 skipped existing business code (no delta)",
                infra_count=len(infra_files),
                ai_count=0,
                reused_count=len(existing_business_files),
                total_files=len(infra_files) + len(existing_business_files),
                skipped_ai_generation=True,
            )

        # Note: tech_design_content may be empty if Phase 3 was skipped
        # (e.g., for installer projects), but we still call AI to generate code
        # based on requirements alone

        try:
            client = get_llm_client()
        except Exception as exc:
            return PhaseResult.fail(
                "LLM client init failed: {}".format(exc),
                errors=[str(exc)],
            )

        file_plan = Phase4FilePlanner().build_plan(self.context, project_name)
        self.context.phase4_file_plan = [item.to_dict() for item in file_plan]
        self.log("  [PLAN] prepared {} file generation tasks".format(len(file_plan)))

        ai_files: List[Path] = []
        ai_errors: List[str] = []

        def tool_handler(tool_name, tool_input):
            if tool_name != "write_file":
                return "[error] unknown tool {}".format(tool_name)
            rel = (tool_input.get("path") or "").strip()
            content = tool_input.get("content") or ""
            if not rel or not content:
                return "[error] path and content are required"
            target = (project_dir / rel).resolve()

            # PRE-CHECK: Block retry attempts for already-skipped files
            if target in self.skipped_files:
                return "[ERROR] File {} was already skipped. This file CANNOT be generated. You MUST generate OTHER required files instead.".format(
                    rel
                )
            try:
                target.relative_to(project_dir.resolve())
            except ValueError:
                return "[error] path escapes project root: {}".format(rel)

            infrastructure_files = {
                "CMakeLists.txt",
                "README.md",
                "tests/test_base.h",
                f"include/{namespace}.h",
            }
            normalized_rel = rel.replace("\\", "/")
            if target.exists() and normalized_rel in infrastructure_files:
                self.log("    [SKIP] {} already exists, not overwriting".format(rel))
                self.skipped_files.append(target)
                return "[SKIP] Infrastructure file {} already exists. Do NOT retry this file. Generate other required files instead.".format(
                    rel
                )
            if target.exists() and not force_regenerate and not delta_changed:
                self.log("    [SKIP] {} already exists, not overwriting".format(rel))
                self.skipped_files.append(target)
                return "[SKIP] File {} already exists. Do NOT retry this file. Generate other required files instead.".format(
                    rel
                )

            if target.exists():
                self.log("    [OVERWRITE] {} already exists, overwriting".format(rel))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            ai_files.append(target)
            self.log("    [AI] wrote {} ({} chars)".format(rel, len(content)))
            return "wrote {}".format(rel)

        existing_overview = self._build_existing_files_overview(project_dir)
        namespace = project_name.lower().replace("-", "_").replace(" ", "_")
        # Use Prompt engine to generate dynamic System Prompt based on language
        prompt_engine = get_prompt_engine()
        system_prompt = prompt_engine.generate_code_gen_prompt(
            language=self.context.language,
            features=getattr(self.context, "features", None),
        )
        # Build user message based on language and whether tech design exists
        language = self.context.language

        # Try to use LanguagePlugin for language-specific instructions
        infra_files_list = None
        try:
            from devpal.core.schema.languages.cpp_plugin import CppLanguagePlugin
            from devpal.core.schema.languages.python_plugin import PythonLanguagePlugin
            from devpal.core.schema.languages.shell_plugin import ShellLanguagePlugin

            if language == "python":
                plugin = PythonLanguagePlugin()
            elif language == "shell":
                plugin = ShellLanguagePlugin()
            else:  # cpp
                plugin = CppLanguagePlugin()

            # Get required files from plugin
            required_files = plugin.get_required_files_template()
            infra_files_list = ", ".join(required_files.keys())
            self.log(
                f"  [LanguagePlugin] Using {language} plugin for infrastructure files"
            )
        except Exception as e:
            self.log(f"  [WARNING] Failed to load language plugin: {e}, using fallback")

        # Language-specific file instructions and fallback
        if language == "cpp":
            file_instruction = "Use write_file for each .h/.cpp."
            if not infra_files_list:
                infra_files_list = (
                    "CMakeLists.txt, README.md, tests/test_base.h, include/<project>.h"
                )
            test_framework_note = "Do not invent test framework APIs; test_base.h provides ASSERT_TRUE, ASSERT_EQ, RUN_TEST, TEST_MAIN_BEGIN, TEST_MAIN_END. You MUST include tests/test_base.h and generate test entry code that is fully compatible with those macros. Emit the test main section exactly as standalone macro statements on separate lines: TEST_MAIN_BEGIN, then one RUN_TEST(...) per line with a trailing semicolon, then TEST_MAIN_END. Do not mix gtest/doctest/Catch2 syntax. Do not wrap these macros in extra control flow, streams, or expressions.\n"
        elif language == "python":
            file_instruction = "Use write_file for each .py file."
            if not infra_files_list:
                infra_files_list = "README.md, requirements.txt, .gitignore, src/__init__.py, tests/__init__.py"
            test_framework_note = ""
        elif language == "shell":
            file_instruction = "Use write_file for each shell script."
            if not infra_files_list:
                infra_files_list = "README.md"
            test_framework_note = ""
        else:
            file_instruction = "Use write_file for each source file."
            if not infra_files_list:
                infra_files_list = "README.md"
            test_framework_note = ""

        if self.context.tech_design_content:
            design_instruction = "- You MUST generate ALL business code files based on the technical design.\n"
        else:
            design_instruction = "- You MUST generate ALL business code files based on the requirements document.\n"

        file_plan_section = ""
        if file_plan:
            file_plan_lines = [
                "\n=== FILE GENERATION PLAN (planned Phase 4 parallelization unit) ==="
            ]
            for item in file_plan:
                deps = ", ".join(item.dependencies) if item.dependencies else "none"
                file_plan_lines.append(
                    f"- {item.path} | stage={item.stage} | deps={deps} | purpose={item.purpose}"
                )
            file_plan_lines.append(
                "Use this plan as guidance for required business files, but still use write_file for each generated file.\n"
            )
            file_plan_section = "\n".join(file_plan_lines)

        # M2: Read change artifacts if available
        change_artifacts = self._read_change_artifacts()
        change_context_section = ""
        if change_artifacts:
            change_context_section = (
                "\n=== CHANGE ARTIFACTS (from openspec/changes/) ===\n"
            )
            if "spec" in change_artifacts:
                change_context_section += f"\n**Specification Delta** (specs/spec.md):\n{change_artifacts['spec'][:1000]}...\n"
            if "tasks" in change_artifacts:
                change_context_section += f"\n**Implementation Tasks** (tasks.md):\n{change_artifacts['tasks'][:500]}...\n"
            if "design" in change_artifacts:
                change_context_section += f"\n**Technical Design** (design.md):\n{change_artifacts['design'][:1000]}...\n"
            change_context_section += "\n"

        user_message = (
            f"Produce all business code now. {file_instruction}\n\n"
            "IMPORTANT INSTRUCTIONS:\n"
            f"{design_instruction}"
            "- This run was explicitly configured to regenerate business files; overwrite existing business files when needed.\n"
            "- Generate BOTH source files (.cpp in src/) AND header files (.h in include/) for each class.\n"
            "- Generate main.cpp if required by the specification.\n"
            "- Generate test files (.cpp in tests/) for each module.\n"
            "- YOU MUST GENERATE ALL FILES. Do not stop until you have generated: headers (.h), implementations (.cpp in src/), main.cpp, and tests."
            "- If you have only generated headers or only tests, you are NOT done. Continue generating the missing files."
            f"- ONLY skip infrastructure files: {infra_files_list}.\n"
            f"{test_framework_note}"
            f"{file_plan_section}"
            f"{change_context_section}"
            f"{self._build_retrieved_context_section(project_name)}"
            "=== EXISTING FILES (regenerate business, skip infrastructure) ===\n"
            f"Current Time: 2026-05-15 10:00:00 (Beijing, China)\n\n"
            + existing_overview
        )
        # Build cached context: always include requirements, optionally include tech design
        cached_context = [self.context.requirements_content]
        if self.context.tech_design_content:
            cached_context.append(self.context.tech_design_content)

        parallel_enabled = bool(getattr(self.context, "phase4_parallel_enabled", True))
        parallel_safe = self._is_parallel_file_plan_safe(file_plan)
        if parallel_enabled and file_plan and not parallel_safe:
            self.log("  [PARALLEL] disabled for dependency-coupled file plan; using serial tool loop")
        if parallel_enabled and file_plan and parallel_safe:
            parallel_result = self._try_generate_files_parallel(
                file_plan=file_plan,
                project_dir=project_dir,
                infra_files=infra_files,
                infra_errors=infra_errors,
                system_prompt=system_prompt,
                base_user_message=user_message,
                cached_context=cached_context,
                client=client,
            )
            if parallel_result.success:
                return parallel_result
            self.log("  [PARALLEL] fallback to serial tool loop after parallel failure")

        try:
            result = client.generate_with_tool_loop(
                system=system_prompt,
                user_message=user_message,
                tools=[_WRITE_FILE_TOOL],
                tool_handler=tool_handler,
                cached_context=cached_context,
                max_turns=15,
                max_tokens=8192,
            )
        except Exception as exc:
            self.log("  [FAIL] AI tool loop exception: {}".format(exc))
            return PhaseResult.fail(
                "AI code generation exception: {}".format(exc),
                errors=[str(exc)],
            )

        self._update_usage_stats(client)
        # Log LLM result for debugging
        self.log(
            f"  [DEBUG] LLM stop_reason: {result.stop_reason}, turns: {result.turns}/{15}"
        )

        # Check if no AI files were generated
        if not ai_files:
            # Distinguish between "skipped" (files exist) and "failed" (AI error)
            if self.skipped_files or infra_files:
                # Files were skipped because they already exist - this is OK
                self.log("  [INFO] Code generation skipped (all files already exist)")
                self.log(f"  [SUMMARY] Skipped: {len(self.skipped_files)} files")
                self.log(f"  [SUMMARY] Infrastructure: {len(infra_files)} files")

                # Mark as successful with skipped flag
                return PhaseResult.ok(
                    "Code generation completed (files already exist)",
                    skipped=True,
                    skipped_count=len(self.skipped_files),
                    infra_files=len(infra_files),
                    ai_files_generated=0,
                    skipped_ai_generation=True,
                )
            else:
                # True failure: AI didn't generate files and nothing was skipped
                return PhaseResult.fail(
                    "AI produced no code files",
                    errors=[
                        "stop_reason={}".format(result.stop_reason),
                        "turns={}".format(result.turns),
                        "text={}".format(result.text_output[:500]),
                    ],
                )

        self.context.ai_generated_files.extend(ai_files)
        # P2.3: mark all requirements as IN_PROGRESS
        for req in self.context.structured_requirements or []:
            self.context.update_requirement_status(req.get("id", ""), "IN_PROGRESS")
        self.context.generated_files.extend(infra_files + ai_files)

        self._update_artifact_graph(project_dir, ai_files)

        self.compiledb.index_project(project_dir, use_cache=False)
        self.compiledb.save_cache(project_dir)
        self.log(
            "  [OK] re-indexed {} files".format(len(self.compiledb.get_all_files()))
        )

        errors = infra_errors + ai_errors
        if errors:
            return PhaseResult.fail(
                "Code generation completed with errors",
                errors=errors,
            )

        # Log summary statistics
        self.log(f"  [SUMMARY] Generated: {len(ai_files)} AI files")
        self.log(f"  [SUMMARY] Skipped: {len(self.skipped_files)} existing files")
        self.log(f"  [SUMMARY] Infrastructure: {len(infra_files)} files")

        return PhaseResult.ok(
            "Phase 4 complete",
            infra_count=len(infra_files),
            ai_count=len(ai_files),
            total_files=len(infra_files) + len(ai_files),
            file_plan=[item.to_dict() for item in file_plan],
            file_plan_count=len(file_plan),
            llm_calls=client.usage.calls,
            llm_input_tokens=client.usage.input_tokens,
            llm_output_tokens=client.usage.output_tokens,
            turns=result.turns,
        )

    def _build_retrieved_context_section(self, project_name: str) -> str:
        if not bool(getattr(self.context, "vector_retrieval_enabled", False)):
            return ""
        try:
            from devpal.vector_store.semantic_search import SemanticSearchService

            service = SemanticSearchService.from_context(self.context, log=self.log)
            service.index_context(self.context, project_name)
            query_parts = [
                self.context.requirements_content,
                self.context.tech_design_content,
                project_name,
                self.context.language,
            ]
            retrieved_context = service.build_context(
                query="\n".join(part for part in query_parts if part),
                project_name=project_name,
                artifact_types=["requirements", "change", "source", "test", "error"],
                top_k=int(getattr(self.context, "vector_top_k", 5) or 5),
                event_integration=getattr(self.context, "event_integration", None),
            )
            self.context.vector_retrieval_stats = dict(service.stats)
            if retrieved_context:
                return "\n" + retrieved_context + "\n"
        except Exception as exc:
            self.log(f"  [VECTOR] retrieval context unavailable: {exc}")
        return ""

    def _is_parallel_file_plan_safe(self, file_plan) -> bool:
        return bool(file_plan) and not any(item.dependencies for item in file_plan)

    def _try_generate_files_parallel(
        self,
        file_plan,
        project_dir: Path,
        infra_files: List[Path],
        infra_errors: List[str],
        system_prompt: str,
        base_user_message: str,
        cached_context: List[str],
        client,
    ) -> PhaseResult:
        tasks = [
            ParallelTask(
                task_id=f"phase4:{item.path}",
                phase_number=self.phase_number,
                task_type="code_file",
                input_payload={
                    "plan_item": item,
                    "project_dir": project_dir,
                    "system_prompt": system_prompt,
                    "base_user_message": base_user_message,
                    "cached_context": cached_context,
                },
                dependencies=[f"phase4:{dep}" for dep in item.dependencies],
            )
            for item in file_plan
        ]
        snapshots = self._snapshot_parallel_targets(file_plan, project_dir)
        executor = PhaseParallelExecutor(
            max_concurrency=getattr(self.context, "phase4_max_concurrency", 2),
            retry_limit=0,
            serial_fallback=False,
            log=self.log,
            event_integration=getattr(self.context, "event_integration", None),
        )
        try:
            results = executor.execute(tasks, self._generate_single_file_task)
        except Exception as exc:
            self._restore_parallel_targets(snapshots)
            return PhaseResult.fail(
                "Phase 4 parallel generation failed",
                errors=[str(exc)],
            )

        summary = executor.aggregate(results)
        self.context.parallel_execution_stats[str(self.phase_number)] = summary
        event_integration = getattr(self.context, "event_integration", None)
        if event_integration:
            event_integration.emit_phase_parallel_summary(
                self.phase_number,
                summary,
                executor.max_concurrency,
            )
        ai_files = [result.artifact_path for result in results if result.success and result.artifact_path]
        errors = infra_errors + [
            result.error for result in results if not result.success and result.error
        ]
        if errors:
            self._restore_parallel_targets(snapshots)
            return PhaseResult.fail(
                "Phase 4 parallel generation failed",
                errors=errors,
            )

        self.context.ai_generated_files.extend(ai_files)
        for req in self.context.structured_requirements or []:
            self.context.update_requirement_status(req.get("id", ""), "IN_PROGRESS")
        self.context.generated_files.extend(infra_files + ai_files)
        self._update_artifact_graph(project_dir, ai_files)
        self.compiledb.index_project(project_dir, use_cache=False)
        self.compiledb.save_cache(project_dir)
        self._update_parallel_usage_stats(results)
        self.log(f"  [PARALLEL] generated {len(ai_files)} files")
        return PhaseResult.ok(
            "Phase 4 complete (parallel)",
            infra_count=len(infra_files),
            ai_count=len(ai_files),
            total_files=len(infra_files) + len(ai_files),
            file_plan=[item.to_dict() for item in file_plan],
            file_plan_count=len(file_plan),
            parallel_summary=summary,
            llm_calls=self.context.llm_calls,
            llm_input_tokens=self.context.llm_input_tokens,
            llm_output_tokens=self.context.llm_output_tokens,
        )

    def _snapshot_parallel_targets(self, file_plan, project_dir: Path) -> Dict[Path, Optional[str]]:
        snapshots: Dict[Path, Optional[str]] = {}
        for item in file_plan:
            target = (project_dir / item.path).resolve()
            snapshots[target] = target.read_text(encoding="utf-8") if target.exists() else None
        return snapshots

    def _restore_parallel_targets(self, snapshots: Dict[Path, Optional[str]]) -> None:
        for target, content in snapshots.items():
            try:
                if content is None:
                    if target.exists():
                        target.unlink()
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            except Exception as exc:
                self.log(f"  [WARN] Failed to restore {target}: {exc}")

    def _generate_single_file_task(self, task: ParallelTask) -> ParallelTaskResult:
        item = task.input_payload["plan_item"]
        project_dir = task.input_payload["project_dir"]
        target = (project_dir / item.path).resolve()
        try:
            target.relative_to(project_dir.resolve())
        except ValueError:
            return ParallelTaskResult(
                task_id=task.task_id,
                success=False,
                error=f"path escapes project root: {item.path}",
            )

        single_file_content = []
        def single_file_tool_handler(tool_name, tool_input):
            if tool_name != "write_file":
                return "[error] unknown tool {}".format(tool_name)
            rel = (tool_input.get("path") or "").strip()
            content = tool_input.get("content") or ""
            if rel.replace("\\", "/") != item.path:
                return "[error] this task may only write {}".format(item.path)
            if not content:
                return "[error] content is required"
            single_file_content.append(content)
            return "accepted {}".format(rel)

        user_message = (
            task.input_payload["base_user_message"]
            + "\n\n=== SINGLE FILE TASK ===\n"
            + f"Generate exactly one file: {item.path}\n"
            + f"Purpose: {item.purpose}\n"
            + f"Stage: {item.stage}\n"
            + "Call write_file exactly once for this path and do not write any other file.\n"
        )

        task_client = self._create_parallel_llm_client()
        try:
            result = task_client.generate_with_tool_loop(
                system=task.input_payload["system_prompt"],
                user_message=user_message,
                tools=[_WRITE_FILE_TOOL],
                tool_handler=single_file_tool_handler,
                cached_context=task.input_payload["cached_context"],
                max_turns=5,
                max_tokens=4096,
            )
        except Exception as exc:
            return ParallelTaskResult(
                task_id=task.task_id,
                success=False,
                error=str(exc),
                metadata={"path": item.path},
            )

        if not single_file_content:
            return ParallelTaskResult(
                task_id=task.task_id,
                success=False,
                error=f"LLM did not produce {item.path}: stop_reason={result.stop_reason}",
                metadata={"path": item.path, "turns": result.turns},
            )

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(single_file_content[-1], encoding="utf-8")
        self.log("    [PARALLEL AI] wrote {} ({} chars)".format(item.path, len(single_file_content[-1])))
        return ParallelTaskResult(
            task_id=task.task_id,
            success=True,
            artifact_path=target,
            metadata={
                "path": item.path,
                "turns": result.turns,
                "llm_calls": task_client.usage.calls,
                "llm_input_tokens": task_client.usage.input_tokens,
                "llm_output_tokens": task_client.usage.output_tokens,
                "llm_cache_read_tokens": task_client.usage.cache_read_tokens,
                "llm_cache_creation_tokens": task_client.usage.cache_creation_tokens,
            },
        )

    def _create_parallel_llm_client(self):
        from devpal.config import get_config

        config = get_config()
        provider = getattr(self.context, "phase4_parallel_provider", None) or config.llm_default_provider
        provider_config = config.get_provider_config(provider)
        return get_llm_client(
            provider=provider,
            fallback_providers=list(config.llm_fallback_providers),
            **provider_config,
        )

    def _update_parallel_usage_stats(self, results: List[ParallelTaskResult]) -> None:
        self.context.llm_calls = sum(int(result.metadata.get("llm_calls", 0)) for result in results)
        self.context.llm_input_tokens = sum(int(result.metadata.get("llm_input_tokens", 0)) for result in results)
        self.context.llm_output_tokens = sum(int(result.metadata.get("llm_output_tokens", 0)) for result in results)
        self.context.llm_cache_read_tokens = sum(int(result.metadata.get("llm_cache_read_tokens", 0)) for result in results)
        self.context.llm_cache_creation_tokens = sum(int(result.metadata.get("llm_cache_creation_tokens", 0)) for result in results)

    def _is_installer_project(self) -> bool:
        project_type = getattr(self.context, "project_type", "")
        return project_type in {"installer", "tooling"}

    def _apply_infrastructure_templates(self, project_name):
        """Apply CMake/README/skeleton/test_base templates."""
        project_dir = self.context.project_dir
        if project_dir.exists():
            self.compiledb.index_project(project_dir)
        template_ctx = TemplateContext(
            project_name=project_name,
            language=self.context.language,
            features=self._detect_features(),
            existing_files=self.compiledb.get_all_files(),
            existing_symbols=[s.name for s in self.compiledb.get_all_symbols()],
        )
        matching = registry.get_matching_templates(template_ctx)
        self.log(
            "  [Infra] matched {} templates: {}".format(
                len(matching), [t.name for t in matching]
            )
        )
        generated: List[Path] = []
        errors: List[str] = []
        for gen_file in registry.generate_all(template_ctx):
            out = project_dir / gen_file.path
            if out.exists():
                self.log("    [SKIP] {} already exists".format(gen_file.path))
                continue
            try:
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(gen_file.content, encoding="utf-8")
                generated.append(out)
                self.log("    [OK] {}".format(gen_file.path))
            except Exception as exc:
                errors.append("{}: {}".format(gen_file.path, exc))
        return generated, errors

    def _find_existing_business_files(
        self, project_dir: Path, project_name: str
    ) -> List[Path]:
        """Return existing generated business files that make AI regeneration optional."""
        if not project_dir.exists():
            return []

        namespace = project_name.lower().replace("-", "_").replace(" ", "_")
        infrastructure_files = {
            "CMakeLists.txt",
            "README.md",
            "tests/test_base.h",
            f"include/{namespace}.h",
        }
        business_files: List[Path] = []
        if self._is_installer_project():
            scripts_dir = project_dir / "scripts"
            if scripts_dir.exists():
                business_files.extend(sorted(scripts_dir.glob("*.sh")))
                business_files.extend(sorted(scripts_dir.glob("*.bat")))
            business_files.extend(sorted(project_dir.glob("install*.sh")))
            business_files.extend(sorted(project_dir.glob("install*.bat")))
            return business_files

        for folder in ("src", "include", "tests"):
            root = project_dir / folder
            if not root.exists():
                continue
            for path in sorted(root.glob("*.cpp" if folder != "include" else "*.h")):
                rel = path.relative_to(project_dir).as_posix()
                if rel not in infrastructure_files:
                    business_files.append(path)
        return business_files

    def _update_artifact_graph(self, project_dir: Path, ai_files: List[Path]) -> None:
        """Populate context.artifact_graph with requirement->source/test edges."""
        try:
            from devpal.core.schema.artifact_graph import (
                ArtifactGraph,
                ArtifactNode,
                ArtifactType,
                DependencyType,
            )
        except ImportError:
            return

        graph = self.context.artifact_graph
        if graph is None:
            graph = ArtifactGraph()
            self.context.artifact_graph = graph

        requirements = self.context.structured_requirements or []
        for req in requirements:
            req_id = str(req.get("id", "REQ-UNKNOWN"))
            node_id = f"req:{req_id}"
            if not graph.get_node(node_id):
                graph.add_node(
                    ArtifactNode(
                        id=node_id,
                        type=ArtifactType.REQUIREMENT,
                        name=req_id,
                        description=str(req.get("title", "")),
                    )
                )

        for file_path in ai_files:
            # 确保 project_dir 是绝对路径
            abs_project_dir = (
                project_dir.resolve() if not project_dir.is_absolute() else project_dir
            )
            rel = file_path.relative_to(abs_project_dir).as_posix()
            is_test = rel.startswith("tests/")
            artifact_type = ArtifactType.TEST if is_test else ArtifactType.CODE
            file_node_id = f"file:{rel}"
            if not graph.get_node(file_node_id):
                graph.add_node(
                    ArtifactNode(
                        id=file_node_id,
                        type=artifact_type,
                        path=file_path,
                        name=file_path.name,
                    )
                )
            for req in requirements:
                req_id = str(req.get("id", "REQ-UNKNOWN"))
                req_node_id = f"req:{req_id}"
                dep = DependencyType.TESTS if is_test else DependencyType.IMPLEMENTS
            try:
                graph.add_dependency(file_node_id, req_node_id, dep)
            except ValueError:
                pass

    def _build_existing_files_overview(self, project_dir):
        """Return a short bullet list of existing files for AI context."""
        lines: List[str] = []
        if project_dir.exists():
            for path in sorted(project_dir.rglob("*")):
                if not path.is_file():
                    continue
                rel = path.relative_to(project_dir).as_posix()
                if rel.startswith(("build", ".spec", "data")):
                    continue
                lines.append("- {}".format(rel))
        return "\n".join(lines) if lines else "(empty project)"

    def _update_usage_stats(self, client):
        """Sync LLM usage stats from client to context."""
        ctx = self.context
        ctx.llm_calls = client.usage.calls
        ctx.llm_input_tokens = client.usage.input_tokens
        ctx.llm_output_tokens = client.usage.output_tokens
        ctx.llm_cache_read_tokens = client.usage.cache_read_tokens
        ctx.llm_cache_creation_tokens = client.usage.cache_creation_tokens

    def _detect_features(self) -> list:
        """Phase 4 no longer keyword-matches business features; AI parses reqs."""
        return ["test", "docs"]

    def _get_affected_files_from_graph(self, changed_req_ids: List[str]) -> List[str]:
        """使用 ArtifactGraph 确定受需求变更影响的文件列表

        Args:
            changed_req_ids: 变更的需求 ID 列表（added + modified）

        Returns:
            受影响的文件路径列表（相对于项目根目录）
        """
        graph = self.context.artifact_graph
        if graph is None:
            return []

        try:
            from devpal.core.schema.artifact_graph import ArtifactType
        except ImportError:
            return []

        affected_files = set()

        # Ensure project_dir is absolute for relative_to() comparison
        project_dir_abs = (
            self.context.project_dir.resolve()
            if self.context.project_dir
            else Path.cwd()
        )
        for req_id in changed_req_ids:
            req_node_id = f"req:{req_id}"

            # 获取实现该需求的代码文件
            for node, dep_type in graph.get_dependents(req_node_id):
                if node.type in (ArtifactType.CODE, ArtifactType.TEST):
                    if node.path:
                        rel_path = node.path.relative_to(project_dir_abs).as_posix()
                        affected_files.add(rel_path)

        return sorted(list(affected_files))
