# -*- coding: utf-8 -*-

from devpal.core.openspec_executor import OpenSpecRunOptions, OpenSpecWorkflowExecutor


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
