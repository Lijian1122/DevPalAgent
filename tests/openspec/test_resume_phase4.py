# -*- coding: utf-8 -*-

from pathlib import Path

from devpal.core.openspec_phases.base import OpenSpecContext, PhaseResult
from devpal.core.openspec_phases.enhanced_scheduler import (
    CheckpointManager,
    EnhancedOpenSpecScheduler,
)
from devpal.core.openspec_phases.phase11_final_report import Phase11FinalReport


class _DummyRegistry:
    pass


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


def test_checkpoint_restores_project_type_features_and_cache_creation_tokens(tmp_path):
    project_dir = tmp_path / "installer_project"
    project_dir.mkdir(parents=True, exist_ok=True)
    requirements_file = tmp_path / "requirements.md"
    requirements_file.write_text("installer requirement", encoding="utf-8")
    context = OpenSpecContext(project_dir=project_dir, requirements_file=requirements_file)
    context.project_type = "installer"
    context.features = ["install"]
    context.llm_cache_creation_tokens = 123

    checkpoint_path = project_dir / ".spec" / "checkpoint.json"
    saver = CheckpointManager(checkpoint_path, requirements_file)
    saver.save(3, True, context)

    fresh = OpenSpecContext(project_dir=Path(""), requirements_file=requirements_file)
    reloader = CheckpointManager(checkpoint_path, requirements_file)
    assert reloader.restore_context(fresh)

    assert fresh.project_type == "installer"
    assert fresh.features == ["install"]
    assert fresh.llm_cache_creation_tokens == 123


def test_resume_reapplies_current_vector_options_after_checkpoint_restore(tmp_path, monkeypatch):
    project_dir = tmp_path / "cpp_simple_login"
    project_dir.mkdir(parents=True, exist_ok=True)
    requirements_file = tmp_path / "simple_login.md"
    requirements_file.write_text("cpp login requirement", encoding="utf-8")
    context = OpenSpecContext(project_dir=project_dir, requirements_file=requirements_file)
    context.project_name = "cpp_simple_login"
    context.vector_retrieval_enabled = False
    context.vector_top_k = 5
    context.set_phase_result(11, PhaseResult.ok("phase 11"))

    checkpoint_path = project_dir / ".spec" / "checkpoint.json"
    checkpoint = CheckpointManager(checkpoint_path, requirements_file)
    checkpoint.save(11, True, context)

    monkeypatch.chdir(tmp_path)
    scheduler = EnhancedOpenSpecScheduler(
        str(requirements_file),
        _DummyRegistry(),
        enable_progress=False,
        vector_retrieval_enabled=True,
        vector_top_k=3,
        vector_prefer_chroma=False,
    )
    result = scheduler.run_all_phases(resume=True)

    assert result["success"] is True
    assert scheduler.context.vector_retrieval_enabled is True
    assert scheduler.context.vector_top_k == 3
    assert scheduler.context.vector_prefer_chroma is False


def test_resume_after_completed_workflow_returns_noop_success(tmp_path, monkeypatch):
    project_dir = tmp_path / "cpp_simple_login"
    project_dir.mkdir(parents=True, exist_ok=True)
    requirements_file = tmp_path / "simple_login.md"
    requirements_file.write_text("cpp login requirement", encoding="utf-8")

    context = OpenSpecContext(project_dir=project_dir, requirements_file=requirements_file)
    context.project_name = "cpp_simple_login"
    context.test_passed = 4
    context.test_total = 4
    context.set_phase_result(
        10,
        PhaseResult.ok(
            "phase 10",
            test_status="completed",
            test_summary="4/4 passed",
        ),
    )
    context.set_phase_result(11, PhaseResult.ok("phase 11"))

    checkpoint_path = project_dir / ".spec" / "checkpoint.json"
    checkpoint = CheckpointManager(checkpoint_path, requirements_file)
    checkpoint.save(11, True, context)

    monkeypatch.chdir(tmp_path)
    scheduler = EnhancedOpenSpecScheduler(
        str(requirements_file),
        _DummyRegistry(),
        enable_progress=False,
    )
    result = scheduler.run_all_phases(resume=True)

    assert result["success"] is True
    assert result["project_dir"] == str(project_dir)
    assert result["project_name"] == "cpp_simple_login"
    assert result["test_summary"] == "4/4 passed"
    assert result["phases"][11].success is True


def test_phase11_artifact_graph_falls_back_cleanly_when_graph_missing(tmp_path):
    project_dir = tmp_path / "cpp_simple_login"
    docs_dir = project_dir / "docs"
    spec_dir = project_dir / ".spec"
    docs_dir.mkdir(parents=True, exist_ok=True)
    spec_dir.mkdir(parents=True, exist_ok=True)
    requirements_file = tmp_path / "simple_login.md"
    requirements_file.write_text("cpp login requirement", encoding="utf-8")

    context = OpenSpecContext(project_dir=project_dir, requirements_file=requirements_file)
    context.project_name = "cpp_simple_login"
    context.structured_requirements = [
        {"id": "REQ-001", "title": "login", "description": "", "acceptance_criteria": []}
    ]
    context.test_passed = 1
    context.test_total = 1
    context.llm_calls = 0
    context.llm_input_tokens = 0
    context.llm_output_tokens = 0
    context.llm_cache_read_tokens = 0
    context.llm_cache_creation_tokens = 0
    context.generated_files = []
    context.artifact_graph = None
    context.current_change_id = None
    context.current_change_dir = None
    context.set_phase_result(
        10,
        PhaseResult.ok("phase 10", test_status="completed", test_summary="1/1 passed"),
    )

    phase = Phase11FinalReport(context)
    result = phase.execute()

    assert result.success is True
    artifact_graph_path = project_dir / ".spec" / "artifact_graph.json"
    assert artifact_graph_path.exists()
    assert context.artifact_graph_data
