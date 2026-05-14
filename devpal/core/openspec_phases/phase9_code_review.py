# -*- coding: utf-8 -*-
"""Phase 9: code quality review on AI-generated source files."""

from pathlib import Path
from typing import List

from .base import PhaseInterface, PhaseResult, OpenSpecContext


class Phase9CodeReview(PhaseInterface):
    """Phase 9: run code_review tool over every AI-generated file."""

    def __init__(self, context: OpenSpecContext, tool_registry):
        super().__init__(context)
        self.phase_number = 9
        self.phase_name = "Code review"
        self.tool_registry = tool_registry

    def execute(self) -> PhaseResult:
        self.log("Phase 9: code quality review...")

        files_to_review = self._collect_review_targets()
        if not files_to_review:
            self.log("  [WARN] no source files to review")
            return PhaseResult.ok(
                "No files to review",
                total_issues=0,
                reviewed_files=0,
            )

        review_results = []
        for file_path in files_to_review:
            self.log("  reviewing {}".format(file_path.name))
            result = self.tool_registry.execute_tool(
                "code_review", {"file_path": str(file_path)}
            )
            if result.success:
                issues = (
                    result.metadata.get("issues", [])
                    if hasattr(result, "metadata")
                    else []
                )
                review_results.append(
                    {
                        "file": str(file_path),
                        "issues_count": len(issues),
                        "issues": issues,
                    }
                )
                self.log("    [OK] {} issues".format(len(issues)))
            else:
                err = getattr(result, "error_message", "unknown error")
                self.log("    [WARN] review failed: {}".format(err))

        total_issues = sum(r["issues_count"] for r in review_results)
        self.log(
            "[OK] code review done: {} issues in {} files".format(
                total_issues, len(review_results)
            )
        )

        report_content = self._generate_review_report(review_results)
        report_path = self.context.project_dir / "docs" / "code_review_report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report_content, encoding="utf-8")
        self.context.generated_files.append(report_path)

        return PhaseResult.ok(
            "Code review complete",
            total_issues=total_issues,
            reviewed_files=len(review_results),
            report_path=str(report_path),
        )

    def _collect_review_targets(self) -> List[Path]:
        """Prefer AI-generated files; fall back to scanning include/src/tests."""
        ai_files = [Path(p) for p in self.context.ai_generated_files if Path(p).exists()]
        if ai_files:
            return sorted(set(ai_files))

        project_dir = self.context.project_dir
        candidates: List[Path] = []
        for sub in ("include", "src", "tests"):
            base = project_dir / sub
            if not base.exists():
                continue
            for ext in ("*.h", "*.hpp", "*.cpp"):
                candidates.extend(base.glob(ext))
        return sorted(set(candidates))

    def _generate_review_report(self, review_results) -> str:
        lines = ["# Code Review Report", ""]
        total_issues = sum(r["issues_count"] for r in review_results)
        lines.append("- Files reviewed: {}".format(len(review_results)))
        lines.append("- Total issues: {}".format(total_issues))
        lines.append("")

        for result in review_results:
            lines.append("## {}".format(result["file"]))
            lines.append("- Issues: {}".format(result["issues_count"]))
            if result["issues_count"] > 0:
                lines.append("")
                for i, issue in enumerate(result["issues"], 1):
                    lines.append("{}. {}".format(i, issue))
            lines.append("")

        return "\n".join(lines)
