# -*- coding: utf-8 -*-
"""Phase 4: Generate core implementation code via templates + AI.

Step 1: apply infrastructure templates (CMake, README, skeleton, test_base).
Step 2: invoke Claude with a write_file tool to emit business headers,
        implementations, main.cpp, and unit tests.
"""

from pathlib import Path
from typing import Any, Dict, List

from .base import PhaseInterface, PhaseResult, OpenSpecContext
from ..compiledb import CompileDB
from ..llm_client import get_llm_client
from ..templates import registry, TemplateContext
from ..templates.install_script_generator import InstallScriptGenerator
from ..prompts import get_prompt_engine




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
        existing_business_files = self._find_existing_business_files(project_dir, project_name)
        if self._is_installer_project():
            script_files = [path.resolve() for path in InstallScriptGenerator().generate_all(project_dir / "scripts")]
            self.context.ai_generated_files.extend(script_files)
            self.context.generated_files.extend(infra_files + script_files)
            for req in (self.context.structured_requirements or []):
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
            self.log("  [INCREMENTAL] No requirement changes detected, skipping AI generation")
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
            affected_requirements = (
            requirements_delta.get("added", []) +
            requirements_delta.get("modified", [])
            )
            if affected_requirements:
                self.log("  [SELECTIVE] Requirements changed: {}".format(
                    ", ".join(affected_requirements)))
                # 使用 ArtifactGraph 确定受影响的文件（如果可用）
                affected_files = self._get_affected_files_from_graph(affected_requirements)
                if affected_files:
                    self.log("  [SELECTIVE] Will regenerate {} affected files".format(
                    len(affected_files)))
                    # 将受影响的文件信息存储到 context
                    self.context.selective_regenerate_files = affected_files
                else:
                    self.log("  [SELECTIVE] Cannot determine affected files, will regenerate all")


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
                return "[skipped] {} already exists".format(rel)
            if target.exists() and not force_regenerate:
                self.log("    [SKIP] {} already exists, not overwriting".format(rel))
                return "[skipped] {} already exists".format(rel)
            if target.exists():
                self.log("    [OVERWRITE] {} already exists, overwriting".format(rel))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            ai_files.append(target)
            self.log("    [AI] wrote {} ({} chars)".format(rel, len(content)))
            return "wrote {}".format(rel)

        existing_overview = self._build_existing_files_overview(project_dir)
        namespace = (
            project_name.lower().replace("-", "_").replace(" ", "_")
        )
        # Use Prompt engine to generate dynamic System Prompt based on language
        prompt_engine = get_prompt_engine()
        system_prompt = prompt_engine.generate_code_gen_prompt(
            language=self.context.language,
            features=getattr(self.context, 'features', None),
        )
        # Build user message based on language and whether tech design exists
        language = self.context.language
        if language == 'cpp':
            file_instruction = "Use write_file for each .h/.cpp."
            infra_files_list = "CMakeLists.txt, README.md, tests/test_base.h, include/<project>.h"
            test_framework_note = "Do not invent test framework APIs; test_base.h provides ASSERT_TRUE, ASSERT_EQ, RUN_TEST, TEST_MAIN_BEGIN, TEST_MAIN_END.\n"
        elif language == 'python':
            file_instruction = "Use write_file for each .py file."
            infra_files_list = "README.md, requirements.txt, .gitignore, src/__init__.py, tests/__init__.py"
            test_framework_note = ""
        elif language == 'shell':
            file_instruction = "Use write_file for each shell script."
            infra_files_list = "README.md"
            test_framework_note = ""
        else:
            file_instruction = "Use write_file for each source file."
            infra_files_list = "README.md"
            test_framework_note = ""

        if self.context.tech_design_content:
            design_instruction = "- You MUST generate ALL business code files based on the technical design.\n"
        else:
            design_instruction = "- You MUST generate ALL business code files based on the requirements document.\n"

        user_message = (
            f"Produce all business code now. {file_instruction}\n\n"
            "IMPORTANT INSTRUCTIONS:\n"
            f"{design_instruction}"
            "- This run was explicitly configured to regenerate business files; overwrite existing business files when needed.\n"
            f"- ONLY skip infrastructure files: {infra_files_list}.\n"
            f"{test_framework_note}"
            "=== EXISTING FILES (regenerate business, skip infrastructure) ===\n"
            f"Current Time: 2026-05-15 10:00:00 (Beijing, China)\n\n"
            + existing_overview
        )
        # Build cached context: always include requirements, optionally include tech design
        cached_context = [self.context.requirements_content]
        if self.context.tech_design_content:
            cached_context.append(self.context.tech_design_content)

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
                    ai_files_generated=0
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
        for req in (self.context.structured_requirements or []):
            self.context.update_requirement_status(
                req.get("id", ""), "IN_PROGRESS")
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
            llm_calls=client.usage.calls,
            llm_input_tokens=client.usage.input_tokens,
            llm_output_tokens=client.usage.output_tokens,
            turns=result.turns,
        )

    def _is_installer_project(self) -> bool:
        project_type = getattr(self.context, 'project_type', '')
        return project_type in {'installer', 'tooling'}

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

    def _find_existing_business_files(self, project_dir: Path, project_name: str) -> List[Path]:
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
                ArtifactGraph, ArtifactNode, ArtifactType, DependencyType,
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
                graph.add_node(ArtifactNode(
              id=node_id,
            type=ArtifactType.REQUIREMENT,
             name=req_id,
             description=str(req.get("title", "")),
                ))

        for file_path in ai_files:
            # 确保 project_dir 是绝对路径
            abs_project_dir = project_dir.resolve() if not project_dir.is_absolute() else project_dir
            rel = file_path.relative_to(abs_project_dir).as_posix()
            is_test = rel.startswith("tests/")
            artifact_type = ArtifactType.TEST if is_test else ArtifactType.CODE
            file_node_id = f"file:{rel}"
            if not graph.get_node(file_node_id):
                graph.add_node(ArtifactNode(
                    id=file_node_id,
            type=artifact_type,
                    path=file_path,
                name=file_path.name,
             ))
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

        for req_id in changed_req_ids:
            req_node_id = f"req:{req_id}"

            # 获取实现该需求的代码文件
            for node, dep_type in graph.get_dependents(req_node_id):
                if node.type in (ArtifactType.CODE, ArtifactType.TEST):
                    if node.path:
                      rel_path = node.path.relative_to(self.context.project_dir).as_posix()
                      affected_files.add(rel_path)

        return sorted(list(affected_files))
