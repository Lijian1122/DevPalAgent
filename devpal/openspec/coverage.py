# -*- coding: utf-8 -*-
"""Coverage matrix generation for archived OpenSpec changes."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class CoverageMatrixResult:
    path: Path
    total_requirements: int
    covered_requirements: int
    rows: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def coverage_percent(self) -> int:
        if self.total_requirements == 0:
            return 0
        return int(self.covered_requirements / self.total_requirements * 100)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path.as_posix(),
            "total_requirements": self.total_requirements,
            "covered_requirements": self.covered_requirements,
            "coverage_percent": self.coverage_percent,
            "rows": self.rows,
        }


class CoverageMatrixBuilder:
    def build(self, project_dir: Path, change_id: str, metadata: Dict[str, Any]) -> CoverageMatrixResult:
        requirements = self._requirements(metadata)
        code_files = self._relative_files(project_dir, ["src/**/*.py", "src/**/*.cpp", "src/**/*.c", "src/**/*.h", "include/**/*.h", "include/**/*.hpp"])
        test_files = self._relative_files(project_dir, ["tests/**/*.py", "tests/**/*.cpp", "tests/**/*.sh"])
        report_files = self._relative_files(project_dir, ["docs/final_report.md"])
        graph_rows = self._rows_from_artifact_graph(project_dir, requirements, report_files)
        if graph_rows and any(row["code"] or row["tests"] for row in graph_rows):
            rows = graph_rows
        else:
            rows = []
        if not rows:
            for requirement in requirements:
                status = "HEURISTIC" if code_files and test_files else "MISSING"
                rows.append({
                    "requirement": requirement,
                    "code": code_files,
                    "tests": test_files,
                    "report": report_files,
                    "status": status,
                })
        if not rows:
            rows.append({
                "requirement": "(none)",
                "code": code_files,
                "tests": test_files,
                "report": report_files,
                "status": "MISSING",
            })
        output_path = project_dir / ".spec" / "coverage_matrix.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_markdown(output_path, change_id, rows)
        covered = sum(1 for row in rows if row["status"] in {"VERIFIED", "HEURISTIC"})
        return CoverageMatrixResult(
            path=output_path,
            total_requirements=len(rows),
            covered_requirements=covered,
            rows=rows,
        )

    def _rows_from_artifact_graph(self, project_dir: Path, requirements: List[str], report_files: List[str]) -> List[Dict[str, Any]]:
        graph_path = project_dir / ".spec" / "artifact_graph.json"
        if not graph_path.exists() or not requirements:
            return []
        try:
            graph = json.loads(graph_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        nodes = {node.get("id"): node for node in graph.get("nodes", []) if node.get("id")}
        rows = []
        for requirement in requirements:
            req_node_id = f"req:{requirement}"
            related = self._related_graph_files(graph, nodes, requirement, req_node_id)
            code = related["code"]
            tests = related["test"]
            docs = related["doc"] or report_files
            if code and tests:
                status = "VERIFIED"
            elif code or tests:
                status = "PARTIAL"
            else:
                status = "MISSING"
            rows.append({
                "requirement": requirement,
                "code": code,
                "tests": tests,
                "report": docs,
                "status": status,
            })
        return rows

    def _related_graph_files(self, graph: Dict[str, Any], nodes: Dict[str, Dict[str, Any]], requirement: str, req_node_id: str) -> Dict[str, List[str]]:
        related = {"code": [], "test": [], "doc": []}
        for node in nodes.values():
            metadata = node.get("metadata", {}) or {}
            requirement_ids = metadata.get("requirement_ids") or metadata.get("requirements") or []
            if isinstance(requirement_ids, str):
                requirement_ids = [requirement_ids]
            if requirement in requirement_ids:
                self._add_node_file(related, node)
        for edge in graph.get("edges", []) or []:
            source = edge.get("from") or edge.get("from_id") or edge.get("source")
            target = edge.get("to") or edge.get("to_id") or edge.get("target")
            if source == req_node_id and target in nodes:
                self._add_node_file(related, nodes[target])
            elif target == req_node_id and source in nodes:
                self._add_node_file(related, nodes[source])
        return {key: sorted(set(value)) for key, value in related.items()}

    def _add_node_file(self, related: Dict[str, List[str]], node: Dict[str, Any]) -> None:
        node_type = str(node.get("type") or "")
        path = node.get("path") or str(node.get("id", "")).removeprefix("file:")
        if not path:
            return
        if node_type in {"code", "source"}:
            related["code"].append(path)
        elif node_type == "test":
            related["test"].append(path)
        elif node_type == "doc":
            related["doc"].append(path)

    def _requirements(self, metadata: Dict[str, Any]) -> List[str]:
        candidates = metadata.get("requirements") or metadata.get("requirement_ids") or metadata.get("related_requirements") or []
        if not candidates and isinstance(metadata.get("requirements_affected"), dict):
            affected = metadata["requirements_affected"]
            candidates = []
            for key in ("added", "modified", "removed"):
                candidates.extend(affected.get(key, []) or [])
        if isinstance(candidates, str):
            return [candidates]
        output = []
        for item in candidates:
            if isinstance(item, dict):
                output.append(str(item.get("id") or item.get("title") or item))
            else:
                output.append(str(item))
        return [item for item in output if item]

    def _relative_files(self, project_dir: Path, patterns: List[str]) -> List[str]:
        files = []
        seen = set()
        for pattern in patterns:
            for path in sorted(project_dir.glob(pattern)):
                if path.is_file() and path not in seen:
                    seen.add(path)
                    files.append(path.relative_to(project_dir).as_posix())
        return files

    def _write_markdown(self, path: Path, change_id: str, rows: List[Dict[str, Any]]) -> None:
        lines = [
            "# Coverage Matrix",
            "",
            f"Change: `{change_id}`",
            "",
            "| Requirement | Code | Tests | Report | Status |",
            "|-------------|------|-------|--------|--------|",
        ]
        for row in rows:
            lines.append(
                "| {} | {} | {} | {} | {} |".format(
                    row["requirement"],
                    ", ".join(row["code"]) or "(none)",
                    ", ".join(row["tests"]) or "(none)",
                    ", ".join(row["report"]) or "(none)",
                    row["status"],
                )
            )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
