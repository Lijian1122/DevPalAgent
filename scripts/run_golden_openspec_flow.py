# -*- coding: utf-8 -*-
"""Run or preview the OpenSpec AI-agnostic golden lifecycle."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class GoldenStep:
    name: str
    command: List[str]
    returncode: Optional[int] = None
    stdout_tail: str = ""
    stderr_tail: str = ""


@dataclass
class GoldenCheck:
    name: str
    success: bool
    path: str = ""
    detail: str = ""


@dataclass
class GoldenFlowReport:
    requirements: str
    project_dir: str
    change_id: str
    dry_run: bool
    steps: List[GoldenStep]
    checks: List[GoldenCheck] = field(default_factory=list)
    success: bool = True
    failure: str = ""

    def to_dict(self) -> dict:
        data = asdict(self)
        data["steps"] = [asdict(step) for step in self.steps]
        data["checks"] = [asdict(check) for check in self.checks]
        return data


def build_steps(requirements: str, change_id: str, project_dir: str) -> List[GoldenStep]:
    python = sys.executable
    return [
        GoldenStep("propose", [python, "run_ai_flow.py", "-r", requirements, "--propose-only"]),
        GoldenStep("apply", [python, "run_ai_flow.py", "-r", requirements, "--apply-change", change_id]),
        GoldenStep("validate", [python, "run_ai_flow.py", "-r", requirements, "--validate-change", change_id]),
        GoldenStep("archive", [python, "-m", "devpal.openspec", "archive", change_id, "--project-dir", project_dir]),
    ]


def discover_latest_change(changes_dir: Path) -> str:
    candidates = [path for path in changes_dir.iterdir() if path.is_dir()] if changes_dir.exists() else []
    if not candidates:
        raise FileNotFoundError(f"no OpenSpec changes found in {changes_dir}")
    latest = max(candidates, key=lambda path: path.stat().st_mtime)
    return latest.name


def infer_project_dir(requirements: str) -> str:
    stem = Path(requirements).stem
    if stem.endswith("_requirements"):
        stem = stem[: -len("_requirements")]
    if stem.startswith("req_"):
        stem = stem[4:]
    return f"cpp_{stem}"


def run_step(step: GoldenStep, cwd: Path, timeout: int) -> GoldenStep:
    completed = subprocess.run(
        step.command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    step.returncode = completed.returncode
    step.stdout_tail = (completed.stdout or "")[-2000:]
    step.stderr_tail = (completed.stderr or "")[-2000:]
    return step


def _resolve_project_dir(project_dir: str) -> Path:
    path = Path(project_dir)
    return path if path.is_absolute() else ROOT / path


def _find_change_dir(project_dir: Path, change_id: str) -> Path:
    root_change = ROOT / "openspec" / "changes" / change_id
    if root_change.exists():
        return root_change
    return project_dir / "openspec" / "changes" / change_id


def _check_path(name: str, path: Path) -> GoldenCheck:
    return GoldenCheck(
        name=name,
        success=path.exists(),
        path=path.as_posix(),
        detail="exists" if path.exists() else "missing",
    )


def validate_outputs(change_id: str, project_dir: str) -> List[GoldenCheck]:
    checks: List[GoldenCheck] = []
    project_path = _resolve_project_dir(project_dir)
    change_dir = _find_change_dir(project_path, change_id)
    checks.append(_check_path("project directory", project_path))
    for rel in [
        "proposal.md",
        "tasks.md",
        "design.md",
        "metadata.json",
        "specs/spec.md",
    ]:
        checks.append(_check_path(f"change artifact: {rel}", change_dir / rel))

    final_report = project_path / "docs" / "final_report.md"
    checks.append(_check_path("final report", final_report))
    if final_report.exists():
        text = final_report.read_text(encoding="utf-8", errors="replace")
        checks.append(
            GoldenCheck(
                name="final report has acceptance matrix",
                success="## 6. Acceptance Matrix" in text,
                path=final_report.as_posix(),
            )
        )
        zero_zero = "0/0 passed" in text or "0/0 通过" in text
        checks.append(
            GoldenCheck(
                name="final report avoids 0/0 false success",
                success=not zero_zero,
                path=final_report.as_posix(),
                detail="ok" if not zero_zero else "found 0/0 success text",
            )
        )

    generated_sources = [
        path
        for pattern in ["src/**/*", "include/**/*", "tests/**/*", "scripts/**/*"]
        for path in project_path.glob(pattern)
        if path.is_file()
    ]
    checks.append(
        GoldenCheck(
            name="generated source/test artifacts",
            success=bool(generated_sources),
            path=project_path.as_posix(),
            detail=f"{len(generated_sources)} files",
        )
    )
    checks.append(_check_path("archive manifest", project_path / ".spec" / "archive" / f"{change_id}.json"))
    checks.append(_check_path("coverage matrix", project_path / ".spec" / "coverage_matrix.md"))
    return checks


def write_report(report: GoldenFlowReport, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "golden_flow_report.json"
    md_path = output_dir / "golden_flow_report.md"
    json_path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# OpenSpec Golden Flow Report",
        "",
        f"- Requirements: `{report.requirements}`",
        f"- Project dir: `{report.project_dir}`",
        f"- Change ID: `{report.change_id}`",
        f"- Dry run: {report.dry_run}",
        "",
        "| Step | Return code | Command |",
        "|------|-------------|---------|",
    ]
    for step in report.steps:
        rc = "preview" if step.returncode is None else str(step.returncode)
        lines.append(f"| {step.name} | {rc} | `{' '.join(step.command)}` |")
    if report.checks:
        lines.extend([
            "",
            "## Output Checks",
            "",
            "| Check | Status | Path | Detail |",
            "|-------|--------|------|--------|",
        ])
        for check in report.checks:
            status = "OK" if check.success else "FAIL"
            lines.append(
                f"| {check.name} | {status} | `{check.path}` | {check.detail} |"
            )
    if not report.success:
        lines.extend([
            "",
            "## Failure",
            "",
            report.failure or "Golden flow failed.",
            "",
            "## Step Output Tails",
            "",
        ])
        for step in report.steps:
            if step.returncode not in (None, 0) or step.stdout_tail or step.stderr_tail:
                lines.extend([
                    f"### {step.name}",
                    "",
                    f"- Return code: {step.returncode}",
                    "",
                    "Stdout tail:",
                    "",
                    "```text",
                    step.stdout_tail or "",
                    "```",
                    "",
                    "Stderr tail:",
                    "",
                    "```text",
                    step.stderr_tail or "",
                    "```",
                    "",
                ])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the DevPalAgent golden OpenSpec lifecycle")
    parser.add_argument("--requirements", default="requirements/simple_login.md")
    parser.add_argument("--change-id", help="Existing change id; discovered after propose when omitted")
    parser.add_argument("--project-dir", help="Project directory; inferred from requirements when omitted")
    parser.add_argument("--output-dir", default=".spec/golden_flow")
    parser.add_argument("--dry-run", action="store_true", help="Write planned commands without executing them")
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args(argv)

    project_dir = args.project_dir or infer_project_dir(args.requirements)
    change_id = args.change_id or "<discover-after-propose>"
    steps = build_steps(args.requirements, change_id, project_dir)

    success = True
    failure = ""
    if not args.dry_run:
        steps[0] = run_step(steps[0], ROOT, args.timeout)
        if steps[0].returncode != 0:
            success = False
            failure = f"golden step failed: {steps[0].name} rc={steps[0].returncode}"
        if success and args.change_id is None:
            change_id = discover_latest_change(ROOT / "openspec" / "changes")
            steps = build_steps(args.requirements, change_id, project_dir)
            steps[0].returncode = 0
        for index in range(1, len(steps)):
            if not success:
                break
            steps[index] = run_step(steps[index], ROOT, args.timeout)
            if steps[index].returncode != 0:
                success = False
                failure = f"golden step failed: {steps[index].name} rc={steps[index].returncode}"
                break
    checks = [] if args.dry_run or not success else validate_outputs(change_id, project_dir)
    if any(not check.success for check in checks):
        success = False
        failure = "golden output validation failed"

    report = GoldenFlowReport(
        requirements=args.requirements,
        project_dir=project_dir,
        change_id=change_id,
        dry_run=args.dry_run,
        steps=steps,
        checks=checks,
        success=success,
        failure=failure,
    )
    json_path, md_path = write_report(report, ROOT / args.output_dir)
    print(json.dumps({"json": json_path.as_posix(), "markdown": md_path.as_posix(), "change_id": change_id}, ensure_ascii=False, indent=2))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
