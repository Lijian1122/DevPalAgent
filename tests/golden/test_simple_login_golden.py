# -*- coding: utf-8 -*-

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tests.golden.golden_report import (
    GoldenCaseSummary,
    render_markdown,
    write_summary_to_final_report,
)


ROOT = Path(__file__).resolve().parents[2]
PROJECT_DIR = ROOT / "cpp_simple_login"


def _relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _failure_context(output: str) -> str:
    logs = sorted(PROJECT_DIR.glob("cpp_simple_login_*.log"), key=lambda p: p.stat().st_mtime)
    latest_log = logs[-1] if logs else None
    final_report = PROJECT_DIR / "docs" / "final_report.md"
    lines = [
        "Golden case command failed.",
        f"Project dir: {_relative(PROJECT_DIR)}",
        f"Final report: {_relative(final_report)} ({'exists' if final_report.exists() else 'missing'})",
        f"Latest log: {_relative(latest_log) if latest_log else 'missing'}",
        "Last output:",
        output[-4000:],
    ]
    return "\n".join(lines)


@pytest.mark.golden
@pytest.mark.e2e
def test_simple_login_golden_flow():
    started_at = time.time()

    if os.environ.get("DEVPAL_GOLDEN_CLEAN") == "1" and PROJECT_DIR.exists():
        shutil.rmtree(PROJECT_DIR)
    elif PROJECT_DIR.exists():
        for build_name in ["build", "build_test", "build_verify"]:
            build_dir = PROJECT_DIR / build_name
            if build_dir.exists():
                shutil.rmtree(build_dir)

    command = [sys.executable, "run_ai_flow.py", "-r", "requirements/simple_login.md"]
    display_command = "python run_ai_flow.py -r requirements/simple_login.md"
    force_regenerate_code = os.environ.get("DEVPAL_GOLDEN_FORCE_REGENERATE") == "1"
    if force_regenerate_code:
        command.append("--force-regenerate-code")
        display_command += " --force-regenerate-code"

    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=1800,
    )

    output = (result.stdout or "") + "\n" + (result.stderr or "")

    assert result.returncode == 0, _failure_context(output)
    for phase_num in range(1, 10):
        assert f"[SKIP] Phase {phase_num}" not in output
    assert "0/0 passed" not in output
    assert "0/0 通过" not in output

    assert PROJECT_DIR.exists()
    final_report = PROJECT_DIR / "docs" / "final_report.md"
    assert final_report.exists()
    final_report_text = final_report.read_text(encoding="utf-8", errors="replace")
    passed_match = re.search(r"Passed:\s+(\d+)/(\d+)", final_report_text)
    assert passed_match, final_report_text[-2000:]
    passed = int(passed_match.group(1))
    total = int(passed_match.group(2))
    assert total > 0
    assert passed == total
    assert "| 10 | Compile and run tests | OK |" in final_report_text
    assert "| 11 | Final report | OK |" in final_report_text

    logs = sorted(PROJECT_DIR.glob("cpp_simple_login_*.log"), key=lambda p: p.stat().st_mtime)
    assert logs, "expected an OpenSpec log file"
    latest_log = logs[-1].read_text(encoding="utf-8", errors="replace")

    assert "Phase 1" in output
    assert "Phase 2" in output
    for marker in ["Phase 3/11", "Phase 4/11", "Phase 10/11", "Phase 11/11"]:
        assert marker in latest_log

    assert "0/0 passed" not in latest_log
    assert "0/0 通过" not in latest_log
    assert "tests:" in latest_log or "All tests passed" in latest_log

    build_test_dir = PROJECT_DIR / "build_test"
    assert build_test_dir.exists(), "expected build_test directory"
    test_binaries = [
        path for path in build_test_dir.glob("**/test_*")
        if path.is_file() and path.suffix in {"", ".exe"}
    ]
    assert test_binaries, "expected at least one compiled test executable"

    duration = time.time() - started_at
    summary = GoldenCaseSummary(
        name="simple_login",
        requirement="requirements/simple_login.md",
        command=display_command,
        result="PASSED",
        duration_seconds=duration,
        project=_relative(PROJECT_DIR),
        final_report=_relative(final_report),
        latest_log=_relative(logs[-1]),
        tests_passed=passed,
        tests_total=total,
        test_binary_count=len(test_binaries),
        force_regenerate_code=force_regenerate_code,
        checks=[
            ("Exit code is zero", "OK"),
            ("No unexpected `[SKIP] Phase 1-9`", "OK"),
            ("No `0/0` false success", "OK"),
            ("Phase 1/2 observed in stdout", "OK"),
            ("Phase 3/4/10/11 observed in project log", "OK"),
            ("Phase 10 final report status", "OK"),
            ("Phase 11 final report status", "OK"),
            ("Compiled test executables exist", "OK"),
        ],
    )
    summary_markdown = render_markdown(summary)
    write_summary_to_final_report(final_report, summary_markdown)

    print("\n================ GOLDEN CASE SUMMARY ================")
    print(summary_markdown)
    print("=====================================================\n")
