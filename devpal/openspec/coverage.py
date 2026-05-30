# -*- coding: utf-8 -*-
"""Coverage matrix generation for archived OpenSpec changes."""

from __future__ import annotations

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
        rows = []
        for requirement in requirements:
            status = "VERIFIED" if code_files and test_files else "MISSING"
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
        covered = sum(1 for row in rows if row["status"] == "VERIFIED")
        return CoverageMatrixResult(
            path=output_path,
            total_requirements=len(rows),
            covered_requirements=covered,
            rows=rows,
        )

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
