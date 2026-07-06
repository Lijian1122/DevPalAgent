# -*- coding: utf-8 -*-

import json
from pathlib import Path
import sys
import textwrap

from devpal.core.openspec_phases.base import OpenSpecContext, PhaseResult
from devpal.core.openspec_phases.phase10_run_tests import Phase10RunTests


class _DummyRegistry:
    pass


def _fake_windows_runner(tmp_path, stdout="fake runner output\n", returncode=0):
    runner = tmp_path / "fake_windows_runner.py"
    runner.write_text(
        textwrap.dedent(
            f"""
            import json
            import sys
            from pathlib import Path

            request = json.loads(Path(sys.argv[-1]).read_text(encoding="utf-8"))
            result_path = Path(request["result_path"])
            result_path.parent.mkdir(parents=True, exist_ok=True)
            result_path.write_text(
                json.dumps({{
                    "schema_version": "devpal.sandbox.runner_result.v1",
                    "sandbox_id": request["sandbox_id"],
                    "execution_id": request["execution_id"],
                    "status": "completed" if {returncode} == 0 else "failed",
                    "success": {returncode} == 0,
                    "argv": request["command"]["argv"],
                    "cwd": request["command"]["cwd"],
                    "exit_code": {returncode},
                    "stdout": {stdout!r},
                    "stderr": "",
                    "duration_ms": 7,
                    "timed_out": False,
                    "cleanup_status": "clean"
                }}),
                encoding="utf-8",
            )
            """
        ).strip(),
        encoding="utf-8",
    )
    return runner


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


def test_phase10_runs_python_tests_with_windows_process_backend(tmp_path):
    _, context = _make_python_project(tmp_path)
    fake_runner = _fake_windows_runner(
        tmp_path,
        stdout="tests/test_main.py::test_add PASSED\n",
    )
    context.sandbox_backend = "windows_process"
    context.sandbox_level = "strict"
    context.sandbox_backend_options = {
        "runner_path": sys.executable,
        "runner_args": [str(fake_runner)],
    }

    result = Phase10RunTests(context, _DummyRegistry()).execute()

    assert result.success is True
    assert context.test_total == 1
    assert context.test_passed == 1
    assert "test_add" in context.test_output
    summary = context.parallel_execution_stats["10"]
    assert summary["success_count"] == 1
    metadata = summary["results"][0]["metadata"]
    assert metadata["backend"] == "windows_process"
    assert metadata["isolation_level"] == "process"
    assert metadata["cleanup_status"] == "clean"
    assert Path(metadata["manifest_v2_path"]).exists()


def test_phase10_runs_python_tests_with_windows_process_workspace_execution(tmp_path):
    project_dir, context = _make_python_project(tmp_path)
    fake_runner = _fake_windows_runner(
        tmp_path,
        stdout="tests/test_main.py::test_add PASSED\n",
    )
    context.sandbox_backend = "windows_process"
    context.sandbox_level = "strict"
    context.sandbox_backend_options = {
        "phase10_workspace_execution": True,
        "runner_path": sys.executable,
        "runner_args": [str(fake_runner)],
    }

    result = Phase10RunTests(context, _DummyRegistry()).execute()

    assert result.success is True
    metadata = context.parallel_execution_stats["10"]["results"][0]["metadata"]
    request = json.loads(Path(metadata["runner_request_path"]).read_text(encoding="utf-8"))
    workspace_root = Path(context.sandbox_backend_options["phase10_workspace_dir"])
    assert Path(request["project_dir"]) == workspace_root
    assert Path(request["command"]["cwd"]) == workspace_root
    assert (workspace_root / "src" / "main.py").exists()
    assert (workspace_root / "tests" / "test_main.py").exists()
    assert request["command"]["env"]["PYTHONPATH"].split(";")[0] == str(workspace_root / "src")


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


def test_phase10_command_can_use_windows_process_backend(tmp_path):
    project_dir, context = _make_cpp_context(tmp_path)
    fake_runner = _fake_windows_runner(tmp_path, stdout="Python 3.12.0\n")
    context.sandbox_backend = "windows_process"
    context.sandbox_level = "strict"
    context.sandbox_backend_options = {
        "runner_path": sys.executable,
        "runner_args": [str(fake_runner)],
    }
    phase = Phase10RunTests(context, _DummyRegistry())

    result = phase._run_phase10_command(
        task_id="phase10:python:version",
        argv=["python", "--version"],
        timeout_seconds=30,
        legacy_cwd=project_dir,
        agent_cwd=project_dir,
    )

    assert result.returncode == 0
    assert "Python" in result.stdout
    summary = context.parallel_execution_stats["10"]
    assert summary["total_tasks"] == 1
    metadata = summary["results"][0]["metadata"]
    assert metadata["backend"] == "windows_process"
    assert metadata["isolation_level"] == "process"
    assert metadata["cleanup_status"] == "clean"
    assert Path(metadata["manifest_v2_path"]).exists()
    assert Path(metadata["runner_request_path"]).exists()
    assert Path(metadata["runner_result_path"]).exists()


def test_phase10_workspace_execution_uses_copied_project_root(tmp_path):
    project_dir, context = _make_cpp_context(tmp_path)
    (project_dir / "src").mkdir()
    (project_dir / "include").mkdir()
    (project_dir / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.14)\n", encoding="utf-8")
    (project_dir / "src" / "main.cpp").write_text("int main() { return 0; }\n", encoding="utf-8")
    (project_dir / "tests" / "test_sample.cpp").write_text("int main() { return 0; }\n", encoding="utf-8")
    fake_runner = _fake_windows_runner(tmp_path, stdout="ok\n")
    context.sandbox_backend = "windows_process"
    context.sandbox_level = "strict"
    context.sandbox_backend_options = {
        "phase10_workspace_execution": True,
        "runner_path": sys.executable,
        "runner_args": [str(fake_runner)],
    }
    phase = Phase10RunTests(context, _DummyRegistry())

    workspace_context = phase._prepare_phase10_workspace_execution(
        project_dir,
        language="cpp",
    )
    assert workspace_context is not None
    workspace_root, workspace_tests_dir, workspace_test_files = workspace_context
    assert (workspace_root / "CMakeLists.txt").exists()
    assert (workspace_root / "src" / "main.cpp").exists()
    assert workspace_tests_dir == workspace_root / "tests"
    assert [path.name for path in workspace_test_files] == ["test_sample.cpp"]
    assert Path(context.sandbox_backend_options["execution_project_dir"]) == workspace_root

    result = phase._run_phase10_command(
        task_id="phase10:workspace:probe",
        argv=["python", "--version"],
        timeout_seconds=30,
        legacy_cwd=workspace_root,
        agent_cwd=workspace_root,
    )

    metadata = context.parallel_execution_stats["10"]["results"][0]["metadata"]
    request_path = Path(metadata["runner_request_path"])
    request = json.loads(request_path.read_text(encoding="utf-8"))
    assert result.returncode == 0
    assert Path(request["project_dir"]) == workspace_root
    assert Path(request["command"]["cwd"]) == workspace_root


def test_phase10_workspace_execution_writes_copy_out_manifest(tmp_path):
    project_dir, context = _make_cpp_context(tmp_path)
    (project_dir / "src").mkdir()
    (project_dir / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.14)\n", encoding="utf-8")
    (project_dir / "src" / "main.cpp").write_text("int main() { return 0; }\n", encoding="utf-8")
    (project_dir / "tests" / "test_sample.cpp").write_text("int main() { return 0; }\n", encoding="utf-8")
    context.sandbox_backend = "windows_process"
    context.sandbox_backend_options = {"phase10_workspace_execution": True}
    phase = Phase10RunTests(context, _DummyRegistry())

    workspace_context = phase._prepare_phase10_workspace_execution(
        project_dir,
        language="cpp",
    )
    assert workspace_context is not None
    workspace_root, _workspace_tests_dir, _workspace_test_files = workspace_context
    artifact = workspace_root / "build" / "result.bin"
    artifact.parent.mkdir()
    artifact.write_bytes(b"compiled")
    context.parallel_execution_stats["10"] = {"results": []}

    result = phase._finalize_phase10_copy_out(PhaseResult.ok("ok"))
    manifest_path = Path(context.sandbox_backend_options["phase10_copy_out_manifest"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert result.success is True
    assert manifest["status"] == "copy_out_pending"
    assert manifest["artifact_count"] == 1
    assert manifest["artifacts"][0]["target_relpath"] == "build/result.bin"
    assert context.parallel_execution_stats["10"]["copy_out"]["artifact_count"] == 1


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


def test_phase10_compile_test_msvc_uses_version_neutral_nmake_generator(
    tmp_path, monkeypatch
):
    project_dir, context = _make_cpp_context(tmp_path)
    test_file = project_dir / "tests" / "test_sample.cpp"
    test_file.write_text("int main() { return 0; }", encoding="utf-8")
    build_dir = project_dir / "build_test"
    build_dir.mkdir()
    exe = build_dir / "test_sample.exe"
    phase = Phase10RunTests(context, _DummyRegistry())
    captured_argv = []

    def fake_command(**kwargs):
        captured_argv.append(kwargs["argv"])
        if str(kwargs.get("task_id", "")).endswith(":build"):
            exe.write_text("binary", encoding="utf-8")
        return type("CommandResultLike", (), {"returncode": 0, "stdout": "ok", "stderr": ""})()

    monkeypatch.setattr(phase, "_run_phase10_command", fake_command)

    exe_path, success, _ = phase._compile_test(
        test_file,
        project_dir,
        build_dir,
        compiler="msvc",
        force_rebuild=True,
    )

    configure_argv = captured_argv[0]
    assert success is True
    assert exe_path == exe
    assert configure_argv[:3] == ["cmake", "-G", "NMake Makefiles"]
    assert "-A" not in configure_argv


def test_phase10_compile_test_fails_when_build_command_fails_even_if_stale_exe_exists(
    tmp_path, monkeypatch
):
    project_dir, context = _make_cpp_context(tmp_path)
    test_file = project_dir / "tests" / "test_sample.cpp"
    test_file.write_text("int main() { return 0; }", encoding="utf-8")
    build_dir = project_dir / "build_test"
    build_dir.mkdir()
    (build_dir / "CMakeCache.txt").write_text("cached", encoding="utf-8")
    exe = build_dir / "test_sample.exe"
    exe.write_text("stale binary", encoding="utf-8")
    phase = Phase10RunTests(context, _DummyRegistry())

    def fake_command(**kwargs):
        if str(kwargs.get("task_id", "")).endswith(":configure"):
            return type(
                "CommandResultLike",
                (),
                {"returncode": 0, "stdout": "configured", "stderr": ""},
            )()
        return type(
            "CommandResultLike",
            (),
            {"returncode": 1, "stdout": "build failed", "stderr": "compiler error"},
        )()

    monkeypatch.setattr(phase, "_run_phase10_command", fake_command)

    exe_path, success, output = phase._compile_test(
        test_file,
        project_dir,
        build_dir,
        compiler="g++",
        force_rebuild=True,
    )

    assert success is False
    assert exe_path is None
    assert "build failed" in output
    assert "compiler error" in output


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
