# -*- coding: utf-8 -*-

from pathlib import Path

from devpal.core.openspec_phases.base import OpenSpecContext
from devpal.core.openspec_phases.phase4_generate_code import Phase4GenerateCode
from devpal.core.openspec_phases.enhanced_scheduler import EnhancedOpenSpecScheduler


class _DummyRegistry:
    pass


def _make_context(project_dir: Path) -> OpenSpecContext:
    context = OpenSpecContext(
        project_dir=project_dir,
        requirements_file=project_dir / "requirements.md",
    )
    context.project_name = "cpp_simple_login"
    context.tech_design_content = "design"
    context.requirements_content = "requirements"
    return context


def test_phase4_detects_existing_business_files(tmp_path):
    project_dir = tmp_path / "cpp_simple_login"
    (project_dir / "src").mkdir(parents=True)
    (project_dir / "include").mkdir()
    (project_dir / "tests").mkdir()
    (project_dir / "src" / "main.cpp").write_text("int main() { return 0; }", encoding="utf-8")
    (project_dir / "include" / "cpp_simple_login.h").write_text("#pragma once", encoding="utf-8")
    (project_dir / "tests" / "test_base.h").write_text("#pragma once", encoding="utf-8")

    phase = Phase4GenerateCode(_make_context(project_dir), _DummyRegistry())

    business_files = [path.relative_to(project_dir).as_posix() for path in phase._find_existing_business_files(project_dir, "cpp_simple_login")]

    assert "src/main.cpp" in business_files
    assert "include/cpp_simple_login.h" not in business_files
    assert "tests/test_base.h" not in business_files


def test_enhanced_scheduler_defaults_to_force_regenerate_for_non_script_entries(tmp_path):
    req_file = tmp_path / "requirements.md"
    req_file.write_text("C++ login requirement", encoding="utf-8")

    scheduler = EnhancedOpenSpecScheduler(
        str(req_file),
        _DummyRegistry(),
        enable_checkpoint=False,
        enable_progress=False,
    )

    assert scheduler.context.force_regenerate_code is True


def test_enhanced_scheduler_can_disable_force_regenerate_for_run_ai_flow(tmp_path):
    req_file = tmp_path / "requirements.md"
    req_file.write_text("C++ login requirement", encoding="utf-8")

    scheduler = EnhancedOpenSpecScheduler(
        str(req_file),
        _DummyRegistry(),
        force_regenerate_code=False,
        enable_checkpoint=False,
        enable_progress=False,
    )

    assert scheduler.context.force_regenerate_code is False
