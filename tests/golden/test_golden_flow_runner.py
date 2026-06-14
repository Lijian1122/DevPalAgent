# -*- coding: utf-8 -*-

import json
import sys

from scripts.run_golden_openspec_flow import (
    GoldenCheck,
    GoldenFlowReport,
    GoldenStep,
    build_steps,
    infer_project_dir,
    validate_outputs,
    write_report,
)


def test_build_steps_uses_collaboration_lifecycle_commands():
    steps = build_steps("requirements/simple_login.md", "change-001", "cpp_simple_login")

    assert [step.name for step in steps] == ["propose", "apply", "validate", "archive"]
    assert steps[0].command == [sys.executable, "run_ai_flow.py", "-r", "requirements/simple_login.md", "--propose-only"]
    assert steps[1].command[-2:] == ["--apply-change", "change-001"]
    assert steps[2].command[-2:] == ["--validate-change", "change-001"]
    assert steps[3].command == [
        sys.executable,
        "-m",
        "devpal.openspec",
        "archive",
        "change-001",
        "--project-dir",
        "cpp_simple_login",
    ]


def test_infer_project_dir_matches_cpp_requirement_convention():
    assert infer_project_dir("requirements/simple_login.md") == "cpp_simple_login"
    assert infer_project_dir("requirements/login_requirements.md") == "cpp_login"
    assert infer_project_dir("requirements/req_login.md") == "cpp_login"


def test_write_report_outputs_json_and_markdown(tmp_path):
    report = GoldenFlowReport(
        requirements="requirements/simple_login.md",
        project_dir="cpp_simple_login",
        change_id="change-001",
        dry_run=True,
        steps=[GoldenStep("propose", ["python", "run_ai_flow.py"], returncode=None)],
        checks=[GoldenCheck("final report", True, "docs/final_report.md", "exists")],
    )

    json_path, md_path = write_report(report, tmp_path)

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["change_id"] == "change-001"
    assert data["dry_run"] is True
    markdown = md_path.read_text(encoding="utf-8")
    assert "OpenSpec Golden Flow Report" in markdown
    assert "propose" in markdown
    assert "Output Checks" in markdown
    assert "final report" in markdown


def test_write_report_includes_failure_details(tmp_path):
    report = GoldenFlowReport(
        requirements="requirements/simple_login.md",
        project_dir="cpp_simple_login",
        change_id="change-001",
        dry_run=False,
        success=False,
        failure="golden step failed: apply rc=1",
        steps=[
            GoldenStep(
                "apply",
                ["python", "run_ai_flow.py", "--apply-change", "change-001"],
                returncode=1,
                stdout_tail="phase 4 failed",
                stderr_tail="provider denied",
            )
        ],
    )

    json_path, md_path = write_report(report, tmp_path)

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["success"] is False
    assert data["failure"] == "golden step failed: apply rc=1"
    markdown = md_path.read_text(encoding="utf-8")
    assert "## Failure" in markdown
    assert "provider denied" in markdown


def test_validate_outputs_reports_expected_artifacts(tmp_path, monkeypatch):
    from scripts import run_golden_openspec_flow as runner

    monkeypatch.setattr(runner, "ROOT", tmp_path)
    project = tmp_path / "cpp_simple_login"
    change = tmp_path / "openspec" / "changes" / "change-001"
    (change / "specs").mkdir(parents=True)
    for rel in ["proposal.md", "tasks.md", "design.md", "metadata.json", "specs/spec.md"]:
        (change / rel).write_text("ok", encoding="utf-8")
    (project / "docs").mkdir(parents=True)
    (project / "docs" / "final_report.md").write_text(
        "# report\n\n## 6. Acceptance Matrix\n\n1/1 passed\n",
        encoding="utf-8",
    )
    (project / "src").mkdir(parents=True)
    (project / "src" / "app.py").write_text("print('ok')\n", encoding="utf-8")
    (project / ".spec" / "archive").mkdir(parents=True)
    (project / ".spec" / "archive" / "change-001.json").write_text("{}", encoding="utf-8")
    (project / ".spec" / "coverage_matrix.md").write_text("# coverage\n", encoding="utf-8")

    checks = validate_outputs("change-001", "cpp_simple_login")

    assert checks
    assert all(check.success for check in checks)
