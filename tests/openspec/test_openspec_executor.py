# -*- coding: utf-8 -*-

from devpal.core.openspec_executor import OpenSpecRunOptions, OpenSpecWorkflowExecutor
from devpal.core.openspec_phases.base import PhaseResult


class _DummyRegistry:
    pass


def test_executor_default_force_regenerate_is_enabled(tmp_path):
    req_file = tmp_path / "requirements.md"
    req_file.write_text("C++ login requirement", encoding="utf-8")

    executor = OpenSpecWorkflowExecutor(_DummyRegistry())
    scheduler = executor.create_scheduler(str(req_file))

    assert scheduler.context.force_regenerate_code is True


def test_executor_can_disable_force_regenerate_for_script_entry(tmp_path):
    req_file = tmp_path / "requirements.md"
    req_file.write_text("C++ login requirement", encoding="utf-8")

    executor = OpenSpecWorkflowExecutor(_DummyRegistry())
    scheduler = executor.create_scheduler(
        str(req_file),
        OpenSpecRunOptions(force_regenerate_code=False),
    )

    assert scheduler.context.force_regenerate_code is False


def test_executor_preserves_resume_option_without_running(tmp_path):
    options = OpenSpecRunOptions(resume=True, force_regenerate_code=False)

    assert options.resume is True
    assert options.force_regenerate_code is False


def test_scheduler_runs_critique_after_phase9_success(tmp_path, monkeypatch):
    req_file = tmp_path / "requirements.md"
    req_file.write_text("C++ login requirement", encoding="utf-8")
    executor = OpenSpecWorkflowExecutor(_DummyRegistry())
    scheduler = executor.create_scheduler(
        str(req_file),
        OpenSpecRunOptions(enable_checkpoint=False, enable_progress=False),
    )
    scheduler.context.project_dir = tmp_path / "project"
    scheduler.context.project_dir.mkdir()
    scheduler.config = {"enable_critique_phase": True, "critique_config": {}}
    calls = []

    class FakeCritique:
        def __init__(self, context, llm_client=None, config=None):
            self.context = context
            self.phase_name = "Critique Phase"

        def execute_with_timing(self):
            calls.append("ran")
            return PhaseResult.ok("critique", overall_score=88), 0.01

    import devpal.core.openspec_phases.phase9_5_critique as critique_module

    monkeypatch.setattr(critique_module, "Phase9_5Critique", FakeCritique)

    scheduler._run_critique_phase(scheduler.context)

    assert calls == ["ran"]
    assert scheduler.context.phase_results[9.5].success is True
    assert scheduler.context.phase_results[9.5].data["overall_score"] == 88


def test_executor_passes_vector_retrieval_options_to_scheduler(tmp_path):
    req_file = tmp_path / "requirements.md"
    req_file.write_text("C++ login requirement", encoding="utf-8")
    vector_dir = tmp_path / "vectors"

    executor = OpenSpecWorkflowExecutor(_DummyRegistry())
    scheduler = executor.create_scheduler(
        str(req_file),
        OpenSpecRunOptions(
            vector_retrieval_enabled=True,
            vector_persist_dir=str(vector_dir),
            vector_top_k=3,
            vector_prefer_chroma=False,
        ),
    )

    assert scheduler.context.vector_retrieval_enabled is True
    assert scheduler.context.vector_persist_dir == vector_dir
    assert scheduler.context.vector_top_k == 3
    assert scheduler.context.vector_prefer_chroma is False
