# -*- coding: utf-8 -*-

from pathlib import Path

from devpal.core.openspec_phases.base import OpenSpecContext, PhaseResult
from devpal.core.openspec_phases.enhanced_scheduler import CheckpointManager


def _populate_phase4_state(context: OpenSpecContext) -> None:
    context.requirements_content = "REQ"
    context.tech_design_content = "design"
    context.structured_requirements = [
        {"id": "REQ-001", "title": "用户登录", "description": "", "acceptance_criteria": []}
    ]
    context.set_phase_result(1, PhaseResult.ok("phase 1"))
    context.set_phase_result(2, PhaseResult.ok("phase 2"))
    context.set_phase_result(3, PhaseResult.ok("phase 3"))
    context.set_phase_result(4, PhaseResult.ok("phase 4", ai_count=5))


def test_resume_after_phase4_restores_required_context(tmp_path):
    project_dir = tmp_path / "cpp_simple_login"
    project_dir.mkdir(parents=True, exist_ok=True)
    requirements_file = tmp_path / "requirements.md"
    requirements_file.write_text("requirement", encoding="utf-8")

    context = OpenSpecContext(project_dir=project_dir, requirements_file=requirements_file)
    context.project_name = "cpp_simple_login"
    _populate_phase4_state(context)

    checkpoint_path = project_dir / ".spec" / "checkpoint.json"
    saver = CheckpointManager(checkpoint_path, requirements_file)
    for phase_num in (1, 2, 3, 4):
        saver.save(phase_num, True, context)

    fresh = OpenSpecContext(project_dir=Path(""), requirements_file=requirements_file)
    reloader = CheckpointManager(checkpoint_path, requirements_file)
    assert reloader.is_valid_for_current_run()
    assert reloader.restore_context(fresh)

    assert reloader.get_resume_phase() == 5
    assert reloader.is_phase_completed(4)
    assert fresh.tech_design_content == "design"
    assert fresh.structured_requirements[0]["id"] == "REQ-001"
    assert fresh.project_dir == project_dir
    assert fresh.phase_results[4].data.get("ai_count") == 5
