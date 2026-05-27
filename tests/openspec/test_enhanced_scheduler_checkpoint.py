# -*- coding: utf-8 -*-

import json
from pathlib import Path

from devpal.core.openspec_phases.base import OpenSpecContext, PhaseResult
from devpal.core.openspec_phases.enhanced_scheduler import (
    CheckpointManager,
    EnhancedOpenSpecScheduler,
)
from devpal.core.schema.event_bus import EventBus, set_global_event_bus


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
    context.set_phase_result(
        10,
        PhaseResult.ok(
            "phase 10",
            test_status="completed",
            test_summary="3/3 passed",
        ),
    )
    return context


class _DummyRegistry:
    pass


def test_scheduler_checkpoint_path_matches_cpp_project_dir_naming(tmp_path):
    requirements_file = tmp_path / "simple_login.md"
    requirements_file.write_text("cpp login project", encoding="utf-8")

    scheduler = EnhancedOpenSpecScheduler(
        str(requirements_file),
        _DummyRegistry(),
        enable_progress=False,
    )

    assert scheduler.checkpoint.checkpoint_file == Path("cpp_simple_login") / ".spec" / "checkpoint.json"


def test_checkpoint_clear_removes_completed_phases(tmp_path):
    requirements_file = tmp_path / "requirements.md"
    requirements_file.write_text("requirement", encoding="utf-8")
    checkpoint_file = tmp_path / ".spec" / "checkpoint.json"
    checkpoint_file.parent.mkdir()
    checkpoint_file.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "requirements_file": requirements_file.as_posix(),
                "last_phase": 9,
                "last_success": True,
                "completed_phases": list(range(1, 10)),
            }
        ),
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


def test_checkpoint_manager_reads_legacy_path_and_saves_to_canonical_path(tmp_path):
    requirements_file = tmp_path / "simple_login.md"
    requirements_file.write_text("cpp login project", encoding="utf-8")
    legacy_checkpoint = tmp_path / "simple_login" / ".spec" / "checkpoint.json"
    canonical_checkpoint = tmp_path / "cpp_simple_login" / ".spec" / "checkpoint.json"
    legacy_checkpoint.parent.mkdir(parents=True, exist_ok=True)

    context = _make_context(tmp_path)
    legacy_manager = CheckpointManager(legacy_checkpoint, requirements_file)
    legacy_manager.save(4, True, context)

    manager = CheckpointManager(
        canonical_checkpoint,
        requirements_file,
        fallback_file=legacy_checkpoint,
    )
    fresh = OpenSpecContext(project_dir=Path(""), requirements_file=requirements_file)
    assert manager.loaded_from_checkpoint_file == legacy_checkpoint
    assert manager.restore_context(fresh)
    assert fresh.project_dir == context.project_dir

    manager.save(5, True, fresh)
    assert canonical_checkpoint.exists()
    assert manager.loaded_from_checkpoint_file == canonical_checkpoint


def test_completed_checkpoint_resume_returns_success_without_running_phases(tmp_path, monkeypatch):
    requirements_file = tmp_path / "simple_login.md"
    requirements_file.write_text("cpp login project", encoding="utf-8")
    context = _make_context(tmp_path)
    context.set_phase_result(11, PhaseResult.ok("phase 11"))

    checkpoint_file = tmp_path / "cpp_simple_login" / ".spec" / "checkpoint.json"
    manager = CheckpointManager(checkpoint_file, requirements_file)
    manager.save(11, True, context)

    monkeypatch.chdir(tmp_path)
    scheduler = EnhancedOpenSpecScheduler(
        str(requirements_file),
        _DummyRegistry(),
        enable_progress=False,
    )
    scheduler.context.project_dir = context.project_dir
    scheduler.context.project_name = context.project_name
    scheduler.context.test_passed = context.test_passed
    scheduler.context.test_total = context.test_total

    result = scheduler.run_all_phases(resume=True)

    assert result["success"] is True
    assert result["project_name"] == "cpp_simple_login"
    assert result["test_summary"] == "3/3 passed"
    assert result["phases"][11].success is True


def test_archive_keeps_live_checkpoint_file(tmp_path):
    context = _make_context(tmp_path)
    checkpoint_file = context.project_dir / ".spec" / "checkpoint.json"
    manager = CheckpointManager(checkpoint_file, context.requirements_file)
    manager.save(11, True, context)

    archive_path = manager.archive("completed")

    assert checkpoint_file.exists()
    assert archive_path is not None
    assert archive_path.exists()


def test_completed_checkpoint_resume_emits_workflow_completed_event(tmp_path, monkeypatch):
    event_bus = EventBus()
    set_global_event_bus(event_bus)
    received = []
    event_bus.subscribe("workflow.completed", received.append)

    requirements_file = tmp_path / "simple_login.md"
    requirements_file.write_text("cpp login project", encoding="utf-8")
    context = _make_context(tmp_path)
    context.set_phase_result(11, PhaseResult.ok("phase 11"))

    checkpoint_file = tmp_path / "cpp_simple_login" / ".spec" / "checkpoint.json"
    manager = CheckpointManager(checkpoint_file, requirements_file)
    manager.save(11, True, context)

    monkeypatch.chdir(tmp_path)
    scheduler = EnhancedOpenSpecScheduler(
        str(requirements_file),
        _DummyRegistry(),
        enable_progress=False,
    )
    scheduler.context.project_dir = context.project_dir
    scheduler.context.project_name = context.project_name
    scheduler.context.test_passed = context.test_passed
    scheduler.context.test_total = context.test_total

    result = scheduler.run_all_phases(resume=True)

    assert result["success"] is True
    assert len(received) == 1
    assert received[0].success is True
    assert received[0].phases_completed >= 2
