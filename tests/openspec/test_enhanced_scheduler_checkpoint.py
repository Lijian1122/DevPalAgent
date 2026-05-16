# -*- coding: utf-8 -*-

import json
from pathlib import Path

from devpal.core.openspec_phases.base import OpenSpecContext, PhaseResult
from devpal.core.openspec_phases.enhanced_scheduler import CheckpointManager


def _make_context(tmp_path: Path) -> OpenSpecContext:
    project_dir = tmp_path / "cpp_simple_login"
    project_dir.mkdir(parents=True, exist_ok=True)
    requirements_file = tmp_path / "requirements.md"
    requirements_file.write_text("requirement", encoding="utf-8")
    context = OpenSpecContext(project_dir=project_dir, requirements_file=requirements_file)
    context.project_name = "cpp_simple_login"
    context.tech_design_content = "design"
    context.structured_requirements = [{"id": "REQ-001", "title": "登录"}]
    context.test_passed = 3
    context.test_total = 3
    context.set_phase_result(3, PhaseResult.ok("phase 3", artifact="design.md"))
    return context


def test_checkpoint_clear_removes_completed_phases(tmp_path):
    requirements_file = tmp_path / "requirements.md"
    requirements_file.write_text("requirement", encoding="utf-8")
    checkpoint_file = tmp_path / ".spec" / "checkpoint.json"
    checkpoint_file.parent.mkdir()
    checkpoint_file.write_text(
        json.dumps({
            "schema_version": 1,
          "requirements_file": requirements_file.as_posix(),
            "last_phase": 9,
            "last_success": True,
            "completed_phases": list(range(1, 10)),
        }),
        encoding="utf-8",
    )

    checkpoint = CheckpointManager(checkpoint_file, requirements_file)
    assert checkpoint.is_phase_completed(1)
    assert checkpoint.get_resume_phase() == 10

    checkpoint.clear()

    assert not checkpoint_file.exists()
    assert not checkpoint.is_phase_completed(1)
    assert checkpoint.get_resume_phase() == 0


def test_checkpoint_save_and_restore_round_trip(tmp_path):
    context = _make_context(tmp_path)
    checkpoint_file = context.project_dir / ".spec" / "checkpoint.json"

    manager = CheckpointManager(checkpoint_file, context.requirements_file)
    manager.save(3, True, context)

    reloaded = CheckpointManager(checkpoint_file, context.requirements_file)
    assert reloaded.is_valid_for_current_run()

    fresh = OpenSpecContext(project_dir=Path(""), requirements_file=context.requirements_file)
    assert reloaded.restore_context(fresh)
    assert fresh.tech_design_content == "design"
    assert fresh.project_name == "cpp_simple_login"
    assert fresh.structured_requirements[0]["id"] == "REQ-001"
    assert fresh.test_total == 3
    assert 3 in fresh.phase_results
    assert fresh.phase_results[3].data.get("artifact") == "design.md"


def test_checkpoint_rejects_mismatched_requirements_file(tmp_path):
    context = _make_context(tmp_path)
    checkpoint_file = context.project_dir / ".spec" / "checkpoint.json"
    CheckpointManager(checkpoint_file, context.requirements_file).save(1, True, context)

    other_requirements = tmp_path / "other.md"
    other_requirements.write_text("other", encoding="utf-8")

    manager = CheckpointManager(checkpoint_file, other_requirements)
    assert not manager.is_valid_for_current_run()

    fresh = OpenSpecContext(project_dir=Path(""), requirements_file=other_requirements)
    assert not manager.restore_context(fresh)
    assert fresh.tech_design_content == ""
