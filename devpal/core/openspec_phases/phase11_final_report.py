# -*- coding: utf-8 -*-
"""Phase 11: final verification report (with LLM usage stats)."""

import json
from pathlib import Path
from typing import Dict, List

from ..cache_strategy import CacheMetrics
from ..schema.artifact_graph import ArtifactNode, ArtifactType, DependencyType
from .base import OpenSpecContext, PhaseInterface, PhaseResult


class Phase11FinalReport(PhaseInterface):
    """Phase 11: emit docs/final_report.md summarising the whole run."""

    def __init__(self, context: OpenSpecContext):
        super().__init__(context)
        self.phase_number = 11
        self.phase_name = "Final report"

    def execute(self) -> PhaseResult:
        self.log("Phase 11: generating final report...")

        # 生成 cache metrics
        cache_metrics = CacheMetrics.from_context(self.context)
        cache_metrics_path = self.context.project_dir / ".spec" / "cache_metrics.json"
        cache_metrics.save_to_file(cache_metrics_path)
        self.log(f"  [OK] Cache metrics saved: {cache_metrics_path}")
        self.log(cache_metrics.format_summary())

        artifact_graph_path = self._write_artifact_graph()
        report_content = self._generate_final_report(artifact_graph_path, cache_metrics)
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
        self.log("  files generated: {}".format(len(set(self.context.generated_files))))
        self.log(
            "  llm: {} calls, in={} out={} cache_read={} cache_create={}".format(
                self.context.llm_calls,
                self.context.llm_input_tokens,
                self.context.llm_output_tokens,
                self.context.llm_cache_read_tokens,
                self.context.llm_cache_creation_tokens,
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
            vector_retrieval_enabled=self.context.vector_retrieval_enabled,
            vector_retrieval_stats=dict(self.context.vector_retrieval_stats),
        )

    def _generate_final_report(
        self, artifact_graph_path: Path, cache_metrics: CacheMetrics
    ) -> str:
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
            9.5: "LLM Critique",
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
            "- Artifact graph: `{}`".format(
                (artifact_graph_path.resolve() if not artifact_graph_path.is_absolute() else artifact_graph_path).relative_to(self.context.project_dir.resolve())
            ),
            "",
            "## 2. AI Usage",
            "",
            "- LLM calls: {}".format(self.context.llm_calls),
            "- Input tokens: {}".format(self.context.llm_input_tokens),
            "- Output tokens: {}".format(self.context.llm_output_tokens),
            "- Cache read tokens: {}".format(self.context.llm_cache_read_tokens),
            "- Cache creation tokens: {}".format(
                self.context.llm_cache_creation_tokens
            ),
            "",
            "### Cache Performance",
            "",
            "- Cache hit rate: {:.1%}".format(cache_metrics.cache_hit_rate),
            "- Cost reduction: {:.1%}".format(cache_metrics.cost_reduction_percentage),
            "- Total cache tokens: {:,}".format(cache_metrics.total_cache_tokens),
            "",
            "- Self-heal attempts: {}".format(self.context.self_heal_attempts),
            "- AI-generated files: {}".format(len(self.context.ai_generated_files)),
            "",
        ]
        lines.extend(self._generate_vector_retrieval_section())
        lines.extend(self._generate_parallel_execution_section())
        lines.extend(self._generate_archive_section())
        lines.extend(
            [
                "## 3. Test Results",
                "",
                "- Status: {}".format("skipped" if test_skipped else "completed"),
                "- Summary: {}".format(test_summary),
                "- Passed: {}".format(
                    "not applicable" if test_skipped else "{}/{}".format(passed, total)
                ),
                "- Pass rate: {}".format("not applicable" if test_skipped else rate),
                "",
            ]
        )

        # Add Critique section if available
        if hasattr(self.context, "critique_result") and self.context.critique_result:
            critique = self.context.critique_result
            overall_score = critique.get("overall_score", "N/A")
            dimensions = critique.get("dimensions", {})
            critical_issues = critique.get("critical_issues", [])

            lines.extend(
                [
                    "## 3.5. Code Quality Critique (LLM-as-a-Judge)",
                    "",
                    f"**Overall Score**: **{overall_score}/100**",
                    "",
                    "| Dimension | Score |",
                    "|-----------|-------|",
                ]
            )

            dim_name_map = {
                "readability": "Code Readability",
                "architecture": "Architecture",
                "security": "Security",
                "performance": "Performance",
                "maintainability": "Maintainability",
            }

            for dim in [
                "readability",
                "architecture",
                "security",
                "performance",
                "maintainability",
            ]:
                if dim in dimensions:
                    score = dimensions[dim].get("score", 0)
                    dim_name = dim_name_map.get(dim, dim)
                    lines.append(f"| {dim_name} | {score}/100 |")

                lines.extend(
                    [
                        "",
                        f"**Critical Issues**: {len(critical_issues)}",
                        "",
                        "Detailed report: [critique_report.md](critique_report.md)",
                        "",
                    ]
                )

        lines.extend(
            [
                "### Requirement Status",
                "",
            ]
            + [
                "",
            ]
        )

        # M2: Add Change Artifacts section
        if (
            hasattr(self.context, "current_change_id")
            and self.context.current_change_id
        ):
            lines.extend(self._generate_change_artifacts_section())

        lines.extend(
            [
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
        )

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
        # Include Phase 9.5 in the status table
        phase_list = list(range(1, 10)) + [9.5, 10, 11]
        for phase_num in phase_list:
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

    def _generate_vector_retrieval_section(self) -> List[str]:
        stats = dict(getattr(self.context, "vector_retrieval_stats", {}) or {})
        if not getattr(self.context, "vector_retrieval_enabled", False) and not stats:
            return []
        return [
            "### Semantic Retrieval",
            "",
            "- Enabled: {}".format(getattr(self.context, "vector_retrieval_enabled", False)),
            "- Search count: {}".format(stats.get("search_count", 0)),
            "- Fallback count: {}".format(stats.get("fallback_count", 0)),
            "- Indexed documents: {}".format(stats.get("indexed_documents", 0)),
            "- Retrieval latency ms: {}".format(stats.get("retrieval_latency_ms", 0)),
            "- Retrieved context count: {}".format(stats.get("retrieved_context_count", 0)),
            "- Last result count: {}".format(stats.get("last_result_count", 0)),
            "",
        ]

    def _generate_archive_section(self) -> List[str]:
        archive_dir = self.context.project_dir / ".spec" / "archive"
        coverage_path = self.context.project_dir / ".spec" / "coverage_matrix.md"
        manifests = []
        if archive_dir.exists():
            manifests = sorted(archive_dir.glob("*.json"))
        if not manifests and not coverage_path.exists():
            return []
        lines = ["### Archive Summary", ""]
        if manifests:
            lines.extend([
                "| Change | Status | Archived At | Coverage |",
                "|--------|--------|-------------|----------|",
            ])
            for manifest_path in manifests:
                try:
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                except Exception:
                    continue
                coverage = manifest.get("coverage", {}) or {}
                lines.append(
                    "| {} | {} | {} | {}% |".format(
                        manifest.get("change_id", manifest_path.stem),
                        manifest.get("status", "UNKNOWN"),
                        manifest.get("archived_at", ""),
                        coverage.get("coverage_percent", 0),
                    )
                )
        if coverage_path.exists():
            rel = coverage_path.relative_to(self.context.project_dir)
            lines.extend(["", f"Coverage matrix: `{rel.as_posix()}`", ""])
        else:
            lines.append("")
        return lines

    def _generate_parallel_execution_section(self) -> List[str]:
        stats = dict(getattr(self.context, "parallel_execution_stats", {}) or {})
        if not stats:
            return []
        lines = [
            "### Parallel Execution Summary",
            "",
            "| Phase | Total Tasks | Success | Failed | Retry | Max Concurrency | Fallback | Task Duration ms |",
            "|-------|-------------|---------|--------|-------|-----------------|----------|------------------|",
        ]
        for phase_num, summary in sorted(stats.items(), key=lambda item: float(item[0])):
            lines.append(
                "| {} | {} | {} | {} | {} | {} | {} | {} |".format(
                    phase_num,
                    summary.get("total_tasks", 0),
                    summary.get("success_count", 0),
                    summary.get("failed_count", 0),
                    summary.get("retry_count", 0),
                    summary.get("max_concurrency", 0),
                    summary.get("fallback_used", False),
                    summary.get("total_task_duration_ms", 0),
                )
            )
        lines.append("")
        return lines

    def _write_artifact_graph(self) -> Path:
        graph_path = self.context.project_dir / ".spec" / "artifact_graph.json"
        graph_path.parent.mkdir(parents=True, exist_ok=True)

        # Try using full ArtifactGraph instance
        graph = self.context.artifact_graph
        if graph is not None:
            # M2: Add change node to artifact graph
            if self.context.current_change_id and self.context.current_change_dir:
                change_path = "openspec/changes/{}".format(
                    self.context.current_change_id
                )

                change_node = ArtifactNode(
                    id="change:{}".format(self.context.current_change_id),
                    type=ArtifactType.SPEC,
                    path=change_path,
                    name=self.context.current_change_id,
                    description="OpenSpec change {}".format(
                        self.context.current_change_id
                    ),
                    metadata={"change_type": "openspec_change"},
                )
                graph.add_node(change_node)

                # Link change to affected requirements
                for req in self.context.structured_requirements:
                    req_id = req.get("id")
                    if req_id:
                        graph.add_dependency(
                            "change:{}".format(self.context.current_change_id),
                            "req:{}".format(req_id),
                            DependencyType.REFERENCES,
                        )

            try:
                graph.save_to_file(graph_path)
                self.context.artifact_graph_data = json.loads(
                    graph_path.read_text(encoding="utf-8")
                )
                self.context.generated_files.append(graph_path)
                self.log("  [OK] Saved using ArtifactGraph.save_to_file()")
                return graph_path
            except Exception as e:
                self.log("  [WARN] ArtifactGraph.save_to_file() failed: {}".format(e))

        # Fallback: simple JSON
        simple_graph = self._build_artifact_graph_data()
        self.context.artifact_graph_data = simple_graph
        graph_path.write_text(
            json.dumps(simple_graph, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self.context.generated_files.append(graph_path)
        self.log("  [OK] Saved using fallback JSON")
        return graph_path

    def _build_artifact_graph_data(self) -> Dict[str, object]:
        requirements = self.context.structured_requirements or []
        source_files = self._relative_files(self._source_file_patterns())
        test_files = self._relative_files(self._test_file_patterns())

        nodes: List[Dict[str, object]] = []
        edges: List[Dict[str, str]] = []

        for requirement in requirements:
            req_id = str(requirement.get("id", "REQ-UNKNOWN"))
            nodes.append(
                {
                    "id": req_id,
                    "type": "requirement",
                    "label": requirement.get("title", req_id),
                    "description": requirement.get("description", ""),
                }
            )
            for source_file in source_files:
                edges.append(
                    {"from": req_id, "to": source_file, "relation": "implemented_by"}
                )
            for test_file in test_files:
                edges.append(
                    {"from": req_id, "to": test_file, "relation": "verified_by"}
                )

        for source_file in source_files:
            nodes.append(
                {"id": source_file, "type": "source", "label": Path(source_file).name}
            )
        for test_file in test_files:
            nodes.append(
                {"id": test_file, "type": "test", "label": Path(test_file).name}
            )

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
        return (
            "Passed"
            if self.context.test_total > 0 and self.context.test_failed == 0
            else "Failed"
        )

    def _generate_status_summary(self) -> list:
        """Return markdown lines showing requirement status distribution."""
        summary = self.context.get_status_summary()
        reqs = self.context.structured_requirements or []
        lines = []
        for req in reqs:
            req_id = req.get("id", "REQ-???")
            status = self.context.get_requirement_status(req_id)
            icon = {"VERIFIED": "OK", "FAILED": "FAIL", "IN_PROGRESS": "WIP"}.get(
                status, "NEW"
            )
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
                matrix = graph.get_traceability_matrix()

                for requirement in requirements:
                    req_id = str(requirement.get("id", "REQ-UNKNOWN"))
                    title = str(requirement.get("title", req_id))
                    req_node_id = "req:{}".format(req_id)

                    code_files = []
                    test_files = []
                    try:
                        dependents = graph.get_dependents(req_node_id)
                        for node, dep_type in dependents:
                            if (
                                node
                                and dep_type == DependencyType.IMPLEMENTS
                                and node.type == ArtifactType.CODE
                            ):
                                code_files.append(
                                    Path(node.path).name if node.path else node.id
                                )
                            elif (
                                node
                                and dep_type == DependencyType.TESTS
                                and node.type == ArtifactType.TEST
                            ):
                                test_files.append(
                                    Path(node.path).name if node.path else node.id
                                )
                    except Exception:
                        pass

                    implementation = ", ".join(code_files) if code_files else "(none)"
                    tests = ", ".join(test_files) if test_files else "(none)"
                    status = self._acceptance_status()

                    lines.append(
                        "| {} {} | {} | {} | {} |".format(
                            req_id, title, implementation, tests, status
                        )
                    )

                coverage = matrix.get("coverage", {})
                if coverage:
                    lines.extend(
                        [
                            "",
                            "### Coverage Statistics",
                            "",
                            "- Requirements with code: {}/{}".format(
                                coverage.get("requirements_with_code", 0),
                                matrix.get(
                                    "total_requirements",
                                    len(matrix.get("requirements", [])),
                                ),
                            ),
                            "- Requirements with tests: {}/{}".format(
                                coverage.get(
                                    "requirements_with_tests",
                                    coverage.get("requirements_with_test", 0),
                                ),
                                matrix.get(
                                    "total_requirements",
                                    len(matrix.get("requirements", [])),
                                ),
                            ),
                            "- Code files: {}".format(
                                len(matrix.get("code_files", []))
                            ),
                        ]
                    )

                return lines
            except Exception as e:
                self.log("  [WARN] ArtifactGraph traceability failed: {}".format(e))

        source_files = self._relative_files(self._source_file_patterns())
        test_files = self._relative_files(self._test_file_patterns())
        status = self._acceptance_status()

        implementation = ", ".join(source_files) if source_files else "(none)"
        tests = ", ".join(test_files) if test_files else "(none)"
        for requirement in requirements:
            req_id = str(requirement.get("id", "REQ-UNKNOWN"))
            title = str(requirement.get("title", req_id))
            lines.append(
                "| {} {} | {} | {} | {} |".format(
                    req_id, title, implementation, tests, status
                )
            )
        return lines

    def _source_file_patterns(self) -> List[str]:
        language = getattr(self.context, "language", "cpp")
        project_type = getattr(self.context, "project_type", "")
        if language == "cpp" or self.context.is_cpp:
            return [
                "src/*.cpp",
                "src/*.cc",
                "src/*.cxx",
                "include/*.h",
                "include/*.hpp",
            ]
        if language == "python":
            return ["src/*.py"]
        if language == "shell" or project_type in {"installer", "tooling"}:
            return ["scripts/*.sh", "scripts/*.bat", "src/*.sh"]
        return ["src/*"]

    def _test_file_patterns(self) -> List[str]:
        language = getattr(self.context, "language", "cpp")
        if language == "cpp" or self.context.is_cpp:
            return ["tests/test_*.cpp", "tests/*_test.cpp"]
        if language == "python":
            return ["tests/test_*.py"]
        if language == "shell":
            return ["tests/test_*.sh"]
        return ["tests/test_*"]

    def _language_features(self):
        try:
            from devpal.core.schema.languages.language_config import (
                get_language_features,
            )

            return get_language_features(getattr(self.context, "language", "cpp"))
        except Exception:
            return None

    def _file_structure_lines(self) -> List[str]:
        features = self._language_features()
        project_type = getattr(self.context, "project_type", "")
        if project_type in {"installer", "tooling"}:
            return [
                "scripts/    # Platform installer scripts (.sh for macOS/Linux, .bat for Windows)",
                "tests/      # Optional shell test files (test_*.sh)",
                "docs/       # Generated documentation",
                ".spec/      # OpenSpec artifacts",
            ]
        if features:
            return [
                "{:<11} # {}".format(name + "/", desc)
                for name, desc in features.project_structure.items()
            ]
        return [
            "src/        # Source files",
            "tests/      # Test files",
            "docs/       # Generated documentation",
            ".spec/      # OpenSpec artifacts",
        ]

    def _coding_convention_lines(self, namespace: str) -> List[str]:
        features = self._language_features()
        if not features:
            return ["- Namespace: {}".format(namespace)]
        lines = []
        for element, convention in features.naming_conventions.items():
            lines.append("- {} names: {}".format(element.capitalize(), convention))
        lines.append("- Test framework: {}".format(features.test_framework))
        lines.append("- Build system: {}".format(features.build_system))
        if getattr(self.context, "project_type", "") in {"installer", "tooling"}:
            lines.append(
                "- Project type: installer/tooling; native build phases are not applicable"
            )
        return lines

    def _relative_files(self, patterns: List[str]) -> List[str]:
        files = []
        for pattern in patterns:
            for path in sorted(self.context.project_dir.glob(pattern)):
                if path.is_file():
                    resolved_path = path.resolve() if not path.is_absolute() else path
                    files.append(resolved_path.relative_to(self.context.project_dir.resolve()).as_posix())
        return files

    def _generate_claude_md(self) -> "Path | None":
        """Generate CLAUDE.md for AI tool integration (Claude Code, Cursor, etc.)."""
        try:
            reqs = self.context.structured_requirements or []
            project_name = self.context.project_name or self.context.project_dir.name
            features = self._language_features()
            lang = (
                features.language_name
                if features
                else ("C++" if self.context.is_cpp else "Python")
            )
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
                lines.append(
                    "### {} {} [{}] [{}]".format(req_id, title, priority, status)
                )
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
            ]
            lines.extend(self._file_structure_lines())
            lines += [
                "```",
                "",
                "## Coding Conventions",
                "",
            ]
            lines.extend(self._coding_convention_lines(ns))
            lines += [
                "",
                "## Test Results",
                "",
                "- Status: {}".format(
                    "skipped" if self._is_test_skipped() else "completed"
                ),
                "- Summary: {}".format(self._test_summary()),
                "",
            ]

            claude_md_path = self.context.project_dir / "CLAUDE.md"
            claude_md_path.write_text("\n".join(lines), encoding="utf-8")
            self.context.generated_files.append(claude_md_path)
            return claude_md_path
        except Exception as e:
            self.log("  [WARN] CLAUDE.md generation failed: {}".format(e))

    def _generate_change_artifacts_section(self) -> List[str]:
        """Generate Change Artifacts section for final report (M2 implementation)"""
        lines = [
            "",
            "## 3.6. OpenSpec Change Artifacts",
            "",
            f"**Change ID**: `{self.context.current_change_id}`",
            "",
            f"**Change Directory**: `openspec/changes/{self.context.current_change_id}/`",
            "",
            "**Generated Artifacts**:",
            "",
        ]

        # List all files in change directory
        if (
            hasattr(self.context, "current_change_dir")
            and self.context.current_change_dir
        ):
            change_dir = self.context.current_change_dir
            if change_dir.exists():
                artifact_files = [
                    "proposal.md",
                    "specs/spec.md",
                    "tasks.md",
                    "design.md",
                    "metadata.json",
                ]

                for file_name in artifact_files:
                    file_path = change_dir / file_name
                    if file_path.exists():
                        resolved_file_path = (
                            file_path.resolve()
                            if not file_path.is_absolute()
                            else file_path
                        )
                        try:
                            rel_path = resolved_file_path.relative_to(
                                self.context.project_dir.resolve()
                            ).as_posix()
                        except ValueError:
                            rel_path = resolved_file_path.as_posix()
                        file_size = resolved_file_path.stat().st_size
                        lines.append(
                            f"- [{file_name}]({rel_path}) ({file_size} bytes)"
                        )
                    else:
                        lines.append(f"- {file_name} (not generated)")

            lines.extend(
                [
                    "",
                    "**Contents**:",
                    "",
                    "- `proposal.md` - Change proposal and impact analysis",
                    "- `specs/spec.md` - Specification delta (ADDED/MODIFIED/REMOVED)",
                    "- `tasks.md` - Implementation task checklist",
                    "- `design.md` - Technical design document",
                    "- `metadata.json` - Change metadata and tracking info",
                    "",
                ]
            )

        return lines

        return None
