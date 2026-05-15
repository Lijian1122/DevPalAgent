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

        self.log("")
        self.log("=" * 60)
        self.log("  OpenSpec 11-phase pipeline complete")
        self.log("  project: {}".format(self.context.project_dir))
        self.log(
            "  tests: {}/{} passed".format(
                self.context.test_passed, self.context.test_total
            )
        )
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
            "- Passed: {}/{}".format(passed, total),
            "- Pass rate: {}".format(rate),
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
        graph = self._build_artifact_graph_data()
        self.context.artifact_graph_data = graph
        graph_path = self.context.project_dir / ".spec" / "artifact_graph.json"
        graph_path.parent.mkdir(parents=True, exist_ok=True)
        graph_path.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
        self.context.generated_files.append(graph_path)
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

    def _generate_acceptance_matrix(self) -> List[str]:
        requirements = self.context.structured_requirements or []
        source_files = self._relative_files(["src/*.cpp", "include/*.h"])
        test_files = self._relative_files(["tests/test_*.cpp"])
        status = "Passed" if self.context.test_total > 0 and self.context.test_failed == 0 else "Failed"

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
