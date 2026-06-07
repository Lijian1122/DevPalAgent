# -*- coding: utf-8 -*-

from pathlib import Path

from devpal.core.openspec_phases.base import OpenSpecContext
from devpal.core.openspec_phases.phase10_run_tests import Phase10RunTests


class _DummyRegistry:
    pass


def _make_python_project(tmp_path):
    project_dir = tmp_path / "python_app"
    (project_dir / "src").mkdir(parents=True)
    (project_dir / "tests").mkdir()
    (project_dir / "src" / "main.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (project_dir / "tests" / "test_main.py").write_text(
        "from main import add\n\n"
        "def test_add():\n"
        "    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    context = OpenSpecContext(project_dir=project_dir, requirements_file=tmp_path / "requirements.md")
    context.language = "python"
    context.project_type = "application"
    return project_dir, context


def test_phase10_runs_python_pytest_and_sets_canonical_counts(tmp_path):
    _, context = _make_python_project(tmp_path)

    result = Phase10RunTests(context, _DummyRegistry()).execute()

    assert result.success is True
    assert not result.data.get("skipped")
    assert context.test_total == 1
    assert context.test_passed == 1
    assert context.test_failed == 0
    assert result.data["test_total"] == 1
    assert result.data["test_passed"] == 1
    assert result.data["test_failed"] == 0
    assert "test_add" in context.test_output


def test_phase10_runs_python_pytest_with_multi_agent(tmp_path):
    _, context = _make_python_project(tmp_path)
    context.enable_multi_agent = True
    context.sandbox_level = "staging"
    context.agent_pool_size = 2

    result = Phase10RunTests(context, _DummyRegistry()).execute()

    assert result.success is True
    assert result.data["multi_agent"] is True
    assert context.test_total == 1
    assert context.test_passed == 1
    assert context.test_failed == 0
    assert result.data["test_total"] == 1
    assert result.data["test_passed"] == 1
    assert result.data["test_failed"] == 0
    assert "test_add" in context.test_output
    assert context.parallel_execution_stats["10"]["success_count"] == 1


def _make_cpp_context(tmp_path):
    project_dir = tmp_path / "cpp_app"
    (project_dir / "tests").mkdir(parents=True)
    context = OpenSpecContext(project_dir=project_dir, requirements_file=tmp_path / "requirements.md")
    context.language = "cpp"
    context.project_type = "application"
    return project_dir, context


def test_phase10_legacy_cpp_command_uses_subprocess_when_multi_agent_disabled(tmp_path, monkeypatch):
    project_dir, context = _make_cpp_context(tmp_path)
    phase = Phase10RunTests(context, _DummyRegistry())
    calls = []

    class Completed:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        return Completed()

    monkeypatch.setattr("devpal.core.openspec_phases.phase10_run_tests.subprocess.run", fake_run)

    result = phase._run_phase10_command(
        task_id="phase10:cpp:test:sample:build",
        argv=["cmake", "--build", str(project_dir / "build_test")],
        timeout_seconds=120,
        agent_cwd=project_dir,
    )

    assert result.returncode == 0
    assert calls[0][0][0] == "cmake"
    assert context.parallel_execution_stats == {}


def test_phase10_multi_agent_cpp_command_uses_coordinator(tmp_path, monkeypatch):
    project_dir, context = _make_cpp_context(tmp_path)
    context.enable_multi_agent = True
    phase = Phase10RunTests(context, _DummyRegistry())
    seen = {}

    class FakeCoordinator:
        def __init__(self, policy, log=None, event_integration=None):
            seen["policy"] = policy

        def execute_test_tasks(self, tasks):
            seen["task"] = tasks[0]
            result = type("Result", (), {})()
            result.success = True
            result.duration_ms = 5
            result.error = None
            result.metadata = {"stdout": "built", "stderr": "", "commands": [{"timed_out": False}]}
            return [result], {
                "total_tasks": 1,
                "success_count": 1,
                "failed_count": 0,
                "retry_count": 0,
                "max_concurrency": 1,
                "fallback_used": False,
                "total_task_duration_ms": 5,
                "results": [{"task_id": tasks[0].task_id, "success": True, "duration_ms": 5}],
            }

    monkeypatch.setattr("devpal.core.multi_agent.MultiAgentCoordinator", FakeCoordinator)

    result = phase._run_phase10_command(
        task_id="phase10:cpp:test:sample:build",
        argv=["cmake", "--build", str(project_dir / "build_test")],
        timeout_seconds=120,
        agent_cwd=project_dir,
    )

    assert result.stdout == "built"
    assert seen["policy"].max_concurrency == 1
    assert seen["task"].task_type == "test_run"
    assert seen["task"].input_payload["commands"][0].argv[0] == "cmake"
    assert context.parallel_execution_stats["10"]["success_count"] == 1


def test_phase10_compile_test_multi_agent_preserves_cmake_sections(tmp_path, monkeypatch):
    project_dir, context = _make_cpp_context(tmp_path)
    context.enable_multi_agent = True
    test_file = project_dir / "tests" / "test_sample.cpp"
    test_file.write_text("int main() { return 0; }", encoding="utf-8")
    build_dir = project_dir / "build_test"
    build_dir.mkdir()
    exe = build_dir / "test_sample.exe"
    exe.write_text("binary", encoding="utf-8")
    phase = Phase10RunTests(context, _DummyRegistry())

    def fake_command(**kwargs):
        return type("CommandResultLike", (), {"returncode": 0, "stdout": "ok", "stderr": ""})()

    monkeypatch.setattr(phase, "_run_phase10_command", fake_command)

    exe_path, success, output = phase._compile_test(
        test_file,
        project_dir,
        build_dir,
        compiler="g++",
        force_rebuild=True,
    )

    assert success is True
    assert exe_path == exe
    assert "=== CMake Configure ===" in output
    assert "=== CMake Build ===" in output


def test_phase10_run_test_multi_agent_parses_results(tmp_path, monkeypatch):
    project_dir, context = _make_cpp_context(tmp_path)
    context.enable_multi_agent = True
    exe = project_dir / "build_test" / "test_sample.exe"
    exe.parent.mkdir()
    exe.write_text("binary", encoding="utf-8")
    phase = Phase10RunTests(context, _DummyRegistry())

    def fake_command(**kwargs):
        return type(
            "CommandResultLike",
            (),
            {"returncode": 0, "stdout": "Results: 2/2 passed", "stderr": ""},
        )()

    monkeypatch.setattr(phase, "_run_phase10_command", fake_command)

    success, output, passed, total = phase._run_test(exe)

    assert success is True
    assert passed == 2
    assert total == 2
    assert "Results: 2/2 passed" in output


def test_phase10_cpp_policy_violation_fails_closed_without_self_heal(tmp_path, monkeypatch):
    project_dir, context = _make_cpp_context(tmp_path)
    context.enable_multi_agent = True
    test_file = project_dir / "tests" / "test_sample.cpp"
    test_file.write_text("int main() { return 0; }", encoding="utf-8")
    phase = Phase10RunTests(context, _DummyRegistry())
    monkeypatch.setattr(phase, "_detect_compiler", lambda: ("g++", None))
    monkeypatch.setattr(
        "devpal.core.openspec_phases.phase10_run_tests.get_llm_client",
        lambda: (_ for _ in ()).throw(RuntimeError("no llm")),
    )

    def deny(*args, **kwargs):
        from devpal.core.openspec_phases.phase10_run_tests import CommandPolicyViolation

        raise CommandPolicyViolation("denied")

    monkeypatch.setattr(phase, "_run_phase10_command", deny)

    result = phase._run_cpp_tests(project_dir, project_dir / "tests", [test_file])

    assert result.success is False
    assert result.message == "Command policy violation"
