# -*- coding: utf-8 -*-

from pathlib import Path

from devpal.core.openspec_phases.base import OpenSpecContext
from devpal.core.openspec_phases.phase10_run_tests import Phase10RunTests


class DummyToolRegistry:
    pass


def make_context(project_dir: Path) -> OpenSpecContext:
    return OpenSpecContext(
        project_dir=project_dir,
        requirements_file=project_dir / "requirements.md",
    )


def test_phase10_fails_when_tests_directory_is_missing(tmp_path):
    context = make_context(tmp_path)
    phase = Phase10RunTests(context, DummyToolRegistry())

    result = phase.execute()

    assert not result.success
    assert result.message == "No tests to run"
    assert "tests/ directory not found" in result.errors


def test_phase10_fails_when_no_test_cpp_files_exist(tmp_path):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "README.md").write_text("no tests here", encoding="utf-8")
    context = make_context(tmp_path)
    phase = Phase10RunTests(context, DummyToolRegistry())

    result = phase.execute()

    assert not result.success
    assert result.message == "No tests to run"
    assert "no test_*.cpp files found" in result.errors
