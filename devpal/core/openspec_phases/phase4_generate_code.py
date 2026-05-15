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


_AI_SYSTEM_PROMPT = (
    "You are a senior C++ developer. Given a software requirements document "
    "and a technical design document, write concrete, compilable C++17 code.\n\n"
    "CRITICAL RULES:\n"
    "- You MUST use the write_file tool for EVERY file. Do NOT write code in prose.\n"
    "- Call write_file once per file immediately. No planning, no discussion first.\n"
    "- Start with your first write_file call right away.\n\n"
    "REQUIRED FILES (you MUST generate ALL of these):\n"
    "1. For each class: include/<name>.h AND src/<name>.cpp (both header and implementation)\n"
    "2. src/main.cpp - a working main program that demonstrates the core functionality\n"
    "3. At least one tests/test_<class>.cpp for each non-trivial class\n"
    "Output rules:\n"
    "- path is relative to project root (include/user.h, src/user.cpp, "
    "src/main.cpp, tests/test_user.cpp).\n"
    "- Each class lives in its own pair of include/<name>.h plus src/<name>.cpp "
    "(snake_case file, PascalCase class).\n"
    "- Include guards use the uppercase filename (e.g. #ifndef USER_H).\n"
    "- All code goes inside namespace {namespace}.\n"
    "- Use only C++17 STL unless the design mandates otherwise.\n"
    "- src/main.cpp must include a working main() function that exercises the primary workflow.\n"
    "- For every non-trivial class, emit at least one tests/test_<class>.cpp "
    "that includes \"test_base.h\" and uses ASSERT_TRUE / ASSERT_EQ macros.\n"
    "- Do NOT regenerate CMakeLists.txt, README.md, include/<project>.h, "
    "or tests/test_base.h - they already exist.\n"
    "- After all files are written, respond with a one-line summary and stop.\n\n"
    "C++ BEST PRACTICES (CRITICAL):\n"
    "- ALWAYS provide a default constructor for classes that will be stored in STL containers "
    "(std::vector, std::map, std::unordered_map, etc.).\n"
    "- If a class has member variables, provide BOTH a default constructor AND a parameterized constructor.\n"
    "- Example: class User should have User() and User(params...).\n"
    "- Initialize all member variables in the constructor initializer list.\n"
    "- Use const references for string parameters to avoid unnecessary copies.\n\n"
    "C++ INCLUDE REQUIREMENTS (CRITICAL):\n"
    "- Include the actual standard header that defines each STL type or function you use.\n"
    "- std::mutex, std::lock_guard, std::unique_lock require #include <mutex>. Never include <lock_guard>.\n"
    "- std::vector requires #include <vector>; std::string requires #include <string>.\n"
    "- std::map requires #include <map>; std::unordered_map requires #include <unordered_map>.\n"
    "- std::chrono types require #include <chrono>; streams require #include <iostream> or <sstream>.\n"
    "- std::hash requires #include <functional>; algorithms require #include <algorithm>.\n"
    "- Do NOT invent non-existent standard headers such as <lock_guard>, <hash>, or <time_point>.\n\n"
    "TEST FRAMEWORK REQUIREMENTS (CRITICAL):\n"
    "- Each test file MUST include test_base.h and use exactly these provided macros: ASSERT_TRUE, ASSERT_EQ, RUN_TEST, TEST_MAIN_BEGIN, TEST_MAIN_END.\n"
    "- Each test file MUST define int main() with TEST_MAIN_BEGIN as the first statement and TEST_MAIN_END as the last statement.\n"
    "- Example test structure:\n"
    "  int main() {{\n"
    "      TEST_MAIN_BEGIN\n"
    "      RUN_TEST(testFunction1);\n"
    "      RUN_TEST(testFunction2);\n"
    "      TEST_MAIN_END\n"
    "  }}\n"
    "- Do NOT define custom pass/fail counters, custom try-catch wrappers, or custom assertion macros.\n"
    "- Do NOT call throw directly in generated test files; ASSERT_TRUE/ASSERT_EQ already signal failures.\n"
    "- Ensure test data is valid and matches the requirements (e.g., passwords must have both letters and digits).\n"
)


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

    def execute(self) -> PhaseResult:
        self.log("Phase 4 start: infrastructure templates + AI code generation")
        project_dir = self.context.project_dir
        project_name = self.context.project_name or "myproject"
        project_dir.mkdir(parents=True, exist_ok=True)

        infra_files, infra_errors = self._apply_infrastructure_templates(project_name)
        self.log("  [Infra] generated {} scaffolding files".format(len(infra_files)))

        if not self.context.tech_design_content:
            return PhaseResult.fail(
                "tech_design_content is empty - did Phase 3 succeed?",
                errors=["missing tech_design_content"],
            )

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
        system_prompt = _AI_SYSTEM_PROMPT.format(namespace=namespace)
        user_message = (
            "Produce all business code now. Use write_file for each .h/.cpp.\n\n"
            "IMPORTANT INSTRUCTIONS:\n"
            "- You MUST generate ALL business code files based on the technical design.\n"
            "- Even if files exist, REGENERATE business files (*.cpp, *.h in src/ and include/).\n"
            "- ONLY skip infrastructure files: CMakeLists.txt, README.md, tests/test_base.h, include/<project>.h.\n"
            "- Do not invent test framework APIs; test_base.h provides ASSERT_TRUE, ASSERT_EQ, RUN_TEST, TEST_MAIN_BEGIN, TEST_MAIN_END.\n"
            "=== EXISTING FILES (regenerate business, skip infrastructure) ===\n"
            f"Current Time: 2026-05-15 10:00:00 (Beijing, China)\n\n"
            + existing_overview
        )
        cached_context = [
            self.context.requirements_content,
            self.context.tech_design_content,
        ]

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

        if not ai_files:
            return PhaseResult.fail(
                "AI produced no code files",
                errors=[
                    "stop_reason={}".format(result.stop_reason),
                    "turns={}".format(result.turns),
                    "text={}".format(result.text_output[:500]),
                ],
            )

        self.context.ai_generated_files.extend(ai_files)
        self.context.generated_files.extend(infra_files + ai_files)

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

    def _detect_features(self) -> list:
        """Phase 4 no longer keyword-matches business features; AI parses reqs."""
        return ["test", "docs"]
