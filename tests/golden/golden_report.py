# -*- coding: utf-8 -*-

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple


@dataclass(frozen=True)
class GoldenCaseSummary:
    name: str
    requirement: str
    command: str
    result: str
    duration_seconds: float
    project: str
    final_report: str
    latest_log: str
    tests_passed: int
    tests_total: int
    test_binary_count: int
    checks: List[Tuple[str, str]]


def render_markdown(summary: GoldenCaseSummary) -> str:
    lines = [
        "## Golden Case Validation",
        "",
        "| Item | Value |",
        "|------|-------|",
        f"| Name | `{summary.name}` |",
        f"| Requirement | `{summary.requirement}` |",
        f"| Command | `{summary.command}` |",
        f"| Result | {summary.result} |",
        f"| Duration | {summary.duration_seconds:.2f}s |",
        f"| Project | `{summary.project}` |",
        f"| Final report | `{summary.final_report}` |",
        f"| Latest log | `{summary.latest_log}` |",
        f"| Tests | {summary.tests_passed}/{summary.tests_total} passed |",
        f"| Test binaries | {summary.test_binary_count} |",
        "",
        "### Golden Checks",
        "",
        "| Check | Status |",
        "|-------|--------|",
    ]
    lines.extend(f"| {check} | {status} |" for check, status in summary.checks)
    lines.append("")
    return "\n".join(lines)


def write_summary_to_final_report(final_report: Path, summary_markdown: str) -> None:
    content = final_report.read_text(encoding="utf-8", errors="replace")
    marker = "## Golden Case Validation"
    if marker in content:
        content = content[:content.index(marker)].rstrip()
    final_report.write_text(content + "\n\n" + summary_markdown, encoding="utf-8")
