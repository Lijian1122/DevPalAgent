# -*- coding: utf-8 -*-
"""Phase 11: final verification report (with LLM usage stats)."""

import json
from pathlib import Path
from typing import Dict, List

from .base import PhaseInterface, PhaseResult, OpenSpecContext


class Phase11FinalReport(PhaseInterface):
    """Phase 11: emit docs/final_report.md summarising the whole run."""

    def __init__(self, context: OpenSpecContext):
        super().__init__(context)
        self.phase_number = 11
        self.phase_name = "Final report"

    def execute(self) -> PhaseResult:
        self.log("Phase 11: generating final report...")

        artifact_graph_path = self._write_artifact_graph()
        report_content = self._generate_final_report(artifact_graph_path)
        report_path = self.context.project_dir / "docs" / "final_report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report_content, encoding="utf-8")

        self.context.generated_files.append(report_path)
        self.log("  [OK] report at {}".format(report_path))

        # P2.2: generate CLAUDE.md for AI tool integration
        claude_md = self._generate_claude_md()
        if claude_md:
            self.log("  [OK] CLAUDE.md at {}".format(claude_md))

        self.log("")
        self.log("=" * 60)
        self.log("  OpenSpec 11-phase pipeline complete")
        self.log("  project: {}".format(self.context.project_dir))
        self.log("  tests: {}".format(self._test_summary()))
        self.log(
            "  files generated: {}".format(len(set(self.context.generated_files)))
        )
        self.log(
            "  llm: {} calls, in={} out={} cache_read={}".format(
                self.context.llm_calls,
                self.context.llm_input_tokens,
                self.context.llm_output_tokens,
                self.context.llm_cache_read_tokens,
            )
        )
        self.log("  self-heal attempts: {}".format(self.context.self_heal_attempts))
        self.log("=" * 60)

        return PhaseResult.ok(
            "Final report generated",
            report_path=str(report_path),
            project_dir=str(self.context.project_dir),
            test_passed=self.context.test_passed,
            test_total=self.context.test_total,
            test_skipped=self._is_test_skipped(),
            test_status="skipped" if self._is_test_skipped() else "completed",
            test_summary=self._test_summary(),
            generated_files=len(set(self.context.generated_files)),
            llm_calls=self.context.llm_calls,
            llm_input_tokens=self.context.llm_input_tokens,
            llm_output_tokens=self.context.llm_output_tokens,
            llm_cache_read_tokens=self.context.llm_cache_read_tokens,
            self_heal_attempts=self.context.self_heal_attempts,
        )

    def _generate_final_report(self, artifact_graph_path: Path) -> str:
        unique_files = sorted(set(self.context.generated_files))
        passed = self.context.test_passed
        total = self.context.test_total
        rate = "{:.1f}%".format(passed / total * 100) if total else "n/a"
        test_skipped = self._is_test_skipped()
        test_summary = self._test_summary()

        phase_names = {
            1: "Parse requirements",
            2: "Create project structure",
            3: "Generate tech design (AI)",
            4: "Generate core code (AI)",
            5: "Verify tests",
            6: "CMake config",
            7: "Test docs",
            8: "README",
            9: "Code review",
            10: "Compile and run tests",
            11: "Final report",
        }

        lines = [
            "# OpenSpec - Final Report",
            "",
            "## 1. Project Overview",
            "",
            "- Project dir: `{}`".format(self.context.project_dir),
            "- Requirements: `{}`".format(self.context.requirements_file),
            "- Files generated: {}".format(len(unique_files)),
            "- Artifact graph: `{}`".format(artifact_graph_path.relative_to(self.context.project_dir)),
            "",
            "## 2. AI Usage",
            "",
            "- LLM calls: {}".format(self.context.llm_calls),
            "- Input tokens: {}".format(self.context.llm_input_tokens),
            "- Output tokens: {}".format(self.context.llm_output_tokens),
            "- Cache read tokens: {}".format(self.context.llm_cache_read_tokens),
            "- Self-heal attempts: {}".format(self.context.self_heal_attempts),
            "- AI-generated files: {}".format(len(self.context.ai_generated_files)),
            "",
            "## 3. Test Results",
            "",
            "- Status: {}".format("skipped" if test_skipped else "completed"),
            "- Summary: {}".format(test_summary),
            "- Passed: {}".format("not applicable" if test_skipped else "{}/{}".format(passed, total)),
            "- Pass rate: {}".format("not applicable" if test_skipped else rate),
            "",
            "### Requirement Status",
            "",
      ] + self._generate_status_summary() + [
         "",
            "### Test Output",
            "",
            "```",
            self.context.test_output or "(no test output captured)",
            "```",
            "",
            "## 4. Generated Files",
            "",
            "```",
        ]
        for f in unique_files:
            try:
                rel = Path(f).relative_to(self.context.project_dir.resolve())
            except ValueError:
                rel = Path(f).name
            lines.append("  {}".format(rel))

        lines.extend(
            [
                "```",
                "",
                "## 5. Phase Status",
                "",
                "| Phase | Name | Status |",
                "|-------|------|--------|",
            ]
        )
        for phase_num in range(1, 12):
            result = self.context.get_phase_result(phase_num)
            if phase_num == 11:
                status = "OK"
            elif result and self._is_phase_skipped(result):
                status = "skipped"
            elif result and result.success:
                status = "OK"
            elif result is None:
                status = "skipped"
            else:
                status = "FAIL"
            lines.append(
                "| {} | {} | {} |".format(
                    phase_num, phase_names.get(phase_num, ""), status
                )
            )

        lines.extend(self._generate_acceptance_matrix())
        lines.extend(
            [
                "",
                "## 7. Summary",
                "",
                "OpenSpec 11-phase pipeline finished. Artefacts are in the project directory above.",
                "",
            ]
        )
        return "\n".join(lines)

    def _write_artifact_graph(self) -> Path:
        graph_path = self.context.project_dir / ".spec" / "artifact_graph.json"
        graph_path.parent.mkdir(parents=True, exist_ok=True)

        # Try using full ArtifactGraph instance
        graph = self.context.artifact_graph
        if graph is not None:
         try:
            graph.save_to_file(graph_path)
            self.context.artifact_graph_data = json.loads(
                    graph_path.read_text(encoding="utf-8"))
            self.context.generated_files.append(graph_path)
            self.log("  [OK] Saved using ArtifactGraph.save_to_file()")
            return graph_path
         except Exception as e:
                self.log("  [WARN] ArtifactGraph.save_to_file() failed: {}".format(e))

        # Fallback: simple JSON
        simple_graph = self._build_artifact_graph_data()
        self.context.artifact_graph_data = simple_graph
        graph_path.write_text(json.dumps(simple_graph, ensure_ascii=False, indent=2), encoding="utf-8")
        self.context.generated_files.append(graph_path)
        self.log("  [OK] Saved using fallback JSON")
        return graph_path

    def _build_artifact_graph_data(self) -> Dict[str, object]:
        requirements = self.context.structured_requirements or []
        source_files = self._relative_files(["src/*.cpp", "include/*.h"])
        test_files = self._relative_files(["tests/test_*.cpp"])

        nodes: List[Dict[str, object]] = []
        edges: List[Dict[str, str]] = []

        for requirement in requirements:
            req_id = str(requirement.get("id", "REQ-UNKNOWN"))
            nodes.append({
                "id": req_id,
                "type": "requirement",
                "label": requirement.get("title", req_id),
                "description": requirement.get("description", ""),
            })
            for source_file in source_files:
                edges.append({"from": req_id, "to": source_file, "relation": "implemented_by"})
            for test_file in test_files:
                edges.append({"from": req_id, "to": test_file, "relation": "verified_by"})

        for source_file in source_files:
            nodes.append({"id": source_file, "type": "source", "label": Path(source_file).name})
        for test_file in test_files:
            nodes.append({"id": test_file, "type": "test", "label": Path(test_file).name})

        return {"nodes": nodes, "edges": edges}

    def _phase10_data(self) -> Dict[str, object]:
        result = self.context.get_phase_result(10)
        return result.data if result else {}

    def _is_phase_skipped(self, result: PhaseResult) -> bool:
        return bool(result.data.get("skipped") or result.data.get("test_skipped"))

    def _is_test_skipped(self) -> bool:
        data = self._phase10_data()
        return bool(data.get("test_skipped") or data.get("skipped"))

    def _test_summary(self) -> str:
        data = self._phase10_data()
        if self._is_test_skipped():
            summary = data.get("test_summary")
            if summary:
                return str(summary)
            reason = data.get("skip_reason", "not applicable")
            return "skipped ({})".format(reason)
        return "{}/{} passed".format(self.context.test_passed, self.context.test_total)

    def _acceptance_status(self) -> str:
        if self._is_test_skipped():
            return "Skipped"
        return "Passed" if self.context.test_total > 0 and self.context.test_failed == 0 else "Failed"

    def _generate_status_summary(self) -> list:
        """Return markdown lines showing requirement status distribution."""
        summary = self.context.get_status_summary()
        reqs = self.context.structured_requirements or []
        lines = []
        for req in reqs:
            req_id = req.get("id", "REQ-???")
            status = self.context.get_requirement_status(req_id)
            icon = {"VERIFIED": "OK", "FAILED": "FAIL",
                  "IN_PROGRESS": "WIP"}.get(status, "NEW")
            lines.append("- [{}] `{}`: {}".format(icon, req_id, status))
        if summary:
            lines.append("")
            for st, count in sorted(summary.items()):
                lines.append("- **{}**: {}".format(st, count))
        return lines if lines else ["- No status data available"]

    def _generate_acceptance_matrix(self) -> List[str]:
         requirements = self.context.structured_requirements or []

         lines = [
            "",
            "## 6. Acceptance Matrix",
            "",
            "| Requirement | Implementation | Tests | Status |",
            "|-------------|----------------|-------|--------|",
        ]

         if not requirements:
            lines.append("| (none) | (none) | (none) | Missing |")
            return lines

         graph = self.context.artifact_graph
         if graph is not None:
            try:
                from devpal.core.schema.artifact_graph import ArtifactType, DependencyType
                matrix = graph.get_traceability_matrix()

                for requirement in requirements:
                    req_id = str(requirement.get("id", "REQ-UNKNOWN"))
                    title = str(requirement.get("title", req_id))
                    req_node_id = "req:{}".format(req_id)

                    code_files = []
                    test_files = []
                    try:
                        dependents = graph.get_dependents(req_node_id)
                        for node_id, dep_type in dependents:
                            node = graph.get_node(node_id)
                            if node and dep_type == DependencyType.IMPLEMENTS and node.type == ArtifactType.CODE:
                                code_files.append(Path(node.path).name if node.path else node_id)
                            elif node and dep_type == DependencyType.TESTS and node.type == ArtifactType.TEST:
                                test_files.append(Path(node.path).name if node.path else node_id)
                    except Exception:
                        pass

                    implementation = ", ".join(code_files) if code_files else "(none)"
                    tests = ", ".join(test_files) if test_files else "(none)"
                    status = self._acceptance_status()

                    lines.append(
                        "| {} {} | {} | {} | {} |".format(req_id, title, implementation, tests, status)
                    )

                coverage = matrix.get("coverage", {})
                if coverage:
                    lines.extend([
                        "",
                        "### Coverage Statistics",
                        "",
                        "- Requirements with code: {}/{}".format(
                            coverage.get("requirements_with_code", 0),
                            coverage.get("total_requirements", 0)
                        ),
                        "- Requirements with tests: {}/{}".format(
                            coverage.get("requirements_with_tests", 0),
                            coverage.get("total_requirements", 0)
                        ),
                        "- Code files with tests: {}/{}".format(
                            coverage.get("code_with_tests", 0),
                            coverage.get("total_code", 0)
                        ),
                    ])

                return lines
            except Exception as e:
                self.log("  [WARN] ArtifactGraph traceability failed: {}".format(e))

         source_files = self._relative_files(["src/*.cpp", "include/*.h"])
         test_files = self._relative_files(["tests/test_*.cpp"])
         status = self._acceptance_status()

         implementation = ", ".join(source_files) if source_files else "(none)"
         tests = ", ".join(test_files) if test_files else "(none)"
         for requirement in requirements:
            req_id = str(requirement.get("id", "REQ-UNKNOWN"))
            title = str(requirement.get("title", req_id))
            lines.append(
                "| {} {} | {} | {} | {} |".format(req_id, title, implementation, tests, status)
            )
         return lines


    def _relative_files(self, patterns: List[str]) -> List[str]:
        files = []
        for pattern in patterns:
            for path in sorted(self.context.project_dir.glob(pattern)):
                if path.is_file():
                    files.append(path.relative_to(self.context.project_dir).as_posix())
        return files

    def _generate_claude_md(self) -> "Path | None":
        """Generate CLAUDE.md for AI tool integration (Claude Code, Cursor, etc.)."""
        try:
            reqs = self.context.structured_requirements or []
            project_name = self.context.project_name or self.context.project_dir.name
            lang = "C++" if self.context.is_cpp else "Python"
            ns = project_name.lower().replace("-", "_").replace(" ", "_")

            lines = [
                "# {}".format(project_name),
                "",
                "## Project Overview",
                "",
                "- Language: {}".format(lang),
                "- Generated by: DevPalAgent OpenSpec pipeline",
                "- Requirements: `{}`".format(self.context.requirements_file),
                "",
                "## Requirements",
                "",
            ]

            for req in reqs:
                req_id = req.get("id", "REQ-???")
                title = req.get("title", "")
                priority = req.get("priority", "P1")
                status = req.get("status", "PROPOSED")
                lines.append("### {} {} [{}] [{}]".format(req_id, title, priority, status))
                desc = req.get("description", "")
                if desc:
                    lines.append("")
                    lines.append(desc)
                scenarios = req.get("scenarios", [])
                if scenarios:
                    lines.append("")
                    lines.append("**Acceptance Scenarios:**")
                    for s in scenarios:
                        if s.get("given"):
                            lines.append("- Given: {}".format(s["given"]))
                        if s.get("when"):
                            lines.append("  When: {}".format(s["when"]))
                        if s.get("then"):
                            lines.append("  Then: {}".format(s["then"]))
                lines.append("")

            lines += [
                "## File Structure",
                "",
                "```",
                "src/        # Implementation files (.cpp)",
                "include/    # Header files (.h)",
                "tests/      # Test files (test_*.cpp)",
                "docs/       # Generated documentation",
                ".spec/     # OpenSpec artifacts",
                "```",
                "",
                "## Coding Conventions",
                "",
                "- File names: snake_case",
                "- Class names: PascalCase",
                "- Namespace: {}".format(ns),
                "- Test framework: custom test_base.h (ASSERT_TRUE, ASSERT_EQ, RUN_TEST)",
                "- Build system: CMake",
                "",
                "## Test Results",
                "",
                "- Status: {}".format("skipped" if self._is_test_skipped() else "completed"),
                "- Summary: {}".format(self._test_summary()),
                "",
            ]

            claude_md_path = self.context.project_dir / "CLAUDE.md"
            claude_md_path.write_text("\n".join(lines), encoding="utf-8")
            self.context.generated_files.append(claude_md_path)
            return claude_md_path
        except Exception as e:
            self.log("  [WARN] CLAUDE.md generation failed: {}".format(e))
            return None
