# -*- coding: utf-8 -*-

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
PROJECT_DIR = ROOT / "cpp_simple_login"


@pytest.mark.golden
@pytest.mark.e2e
def test_simple_login_golden_flow():
    if os.environ.get("DEVPAL_GOLDEN_CLEAN") == "1" and PROJECT_DIR.exists():
        shutil.rmtree(PROJECT_DIR)
    elif PROJECT_DIR.exists():
        for build_name in ["build", "build_test", "build_verify"]:
            build_dir = PROJECT_DIR / build_name
            if build_dir.exists():
                shutil.rmtree(build_dir)

    result = subprocess.run(
        [sys.executable, "run_ai_flow.py", "-r", "requirements/simple_login.md"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=1800,
    )

    output = (result.stdout or "") + "\n" + (result.stderr or "")

    assert result.returncode == 0, output[-4000:]
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

    for marker in ["Phase 1/11", "Phase 4/11", "Phase 10/11", "Phase 11/11"]:
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
