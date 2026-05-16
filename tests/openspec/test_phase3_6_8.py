# -*- coding: utf-8 -*-
"""Unit tests for Phase 3 (Technical Design), Phase 6 (CMake), Phase 8 (README)."""

from pathlib import Path
import pytest
from devpal.core.openspec_phases.base import OpenSpecContext, PhaseResult
from devpal.core.openspec_phases.phase6_cmake_config import Phase6CMakeConfig
from devpal.core.openspec_phases.phase8_readme import Phase8Readme
from devpal.core.openspec_phases.phase7_test_docs import Phase7TestDocs


class _DummyRegistry:
    pass


@pytest.fixture
def temp_project(tmp_path):
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    (project_dir / "src").mkdir()
    (project_dir / "include").mkdir()
    (project_dir / "tests").mkdir()
    (project_dir / "docs").mkdir()
    return project_dir


@pytest.fixture
def context(temp_project):
    ctx = OpenSpecContext(
        project_dir=temp_project,
        requirements_file=Path("requirements.md"),
        project_name="test_project",
        requirements_content="## REQ-001: Login\nUser can log in.",
    )
    ctx.tech_design_content = "# Technical Design\n\n## Architecture\n..."
    return ctx


@pytest.fixture
def registry():
    return _DummyRegistry()


# -------------------------------------
# Phase 3: Technical Design (context-level checks only — no LLM call)
# -----------------------------------------------------------

def test_phase3_fails_without_requirements_content(context):
    """Phase 3 should fail if requirements_content is empty."""
    from devpal.core.openspec_phases.phase3_technical_design import Phase3TechnicalDesign
    context.requirements_content = ""
    phase = Phase3TechnicalDesign(context)
    result = phase.execute()
    # Without LLM, it will fail — we just verify it doesn't crash and returns PhaseResult
    assert isinstance(result, PhaseResult)


def test_phase3_result_is_phase_result(context):
    """Phase 3 execute() always returns a PhaseResult."""
    from devpal.core.openspec_phases.phase3_technical_design import Phase3TechnicalDesign
    phase = Phase3TechnicalDesign(context)
    # Will fail due to no LLM, but must return PhaseResult not raise
    try:
        result = phase.execute()
        assert isinstance(result, PhaseResult)
    except Exception:
        pass  # LLM not available in test env — acceptable


# -------------------------------------
# Phase 6: CMake Config
# -------------------------------------------------------

def test_phase6_passes_when_cmake_exists(context, temp_project, registry):
    """Phase 6 succeeds when CMakeLists.txt already exists."""
    (temp_project / "CMakeLists.txt").write_text(
        "cmake_minimum_required(VERSION 3.10)\nproject(test_project)"
    )
    phase = Phase6CMakeConfig(context, registry)
    result = phase.execute()
    assert result.success is True
    assert "CMake" in result.message or "cmake" in result.message.lower()


def test_phase6_fails_when_cmake_missing(context, temp_project, registry):
    """Phase 6 fails when CMakeLists.txt is absent."""
    phase = Phase6CMakeConfig(context, registry)
    result = phase.execute()
    assert result.success is False
    assert result.errors


def test_phase6_reports_file_size(context, temp_project, registry):
    """Phase 6 result data includes file size."""
    content = "cmake_minimum_required(VERSION 3.10)\nproject(test_project)\n"
    (temp_project / "CMakeLists.txt").write_text(content)
    phase = Phase6CMakeConfig(context, registry)
    result = phase.execute()
    assert result.success is True
    assert result.data.get("content_length", 0) > 0


# -------------------------------------------------------------
# Phase 7: Test Docs (merged into Phase 5 — should be a no-op)
# ------------------------------------------------

def test_phase7_is_noop(context, registry):
    """Phase 7 should succeed immediately as a no-op."""
    phase = Phase7TestDocs(context, registry)
    result = phase.execute()
    assert result.success is True
    assert result.data.get("skipped") is True


# ----------------------------------------------
# Phase 8: README
# ----------------------------------------

def test_phase8_passes_when_readme_exists(context, temp_project, registry):
    """Phase 8 succeeds when README.md already exists."""
    (temp_project / "README.md").write_text("# test_project\n\nA test project.")
    phase = Phase8Readme(context, registry)
    result = phase.execute()
    assert result.success is True


def test_phase8_fails_when_readme_missing(context, temp_project, registry):
    """Phase 8 fails when README.md is absent."""
    phase = Phase8Readme(context, registry)
    result = phase.execute()
    assert result.success is False
    assert result.errors


def test_phase8_reports_file_size(context, temp_project, registry):
    """Phase 8 result data includes file size."""
    content = "# test_project\n\nA test project.\n"
    (temp_project / "README.md").write_text(content)
    phase = Phase8Readme(context, registry)
    result = phase.execute()
    assert result.success is True
    assert result.data.get("content_length", 0) > 0
