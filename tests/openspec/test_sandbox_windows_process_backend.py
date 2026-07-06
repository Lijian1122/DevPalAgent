# -*- coding: utf-8 -*-

import json
import sys
import textwrap
from pathlib import Path

import pytest

from devpal.core.multi_agent import CommandSpec
from devpal.core.sandbox import SandboxRequest, read_manifest_v2
from devpal.core.sandbox.backends import WindowsProcessSandboxBackend
import devpal.core.sandbox.backends.windows_process as windows_process_backend


def _fake_runner(tmp_path):
    runner = tmp_path / "fake_runner.py"
    runner.write_text(
        textwrap.dedent(
            """
            import json
            import sys

            request_path = sys.argv[1]
            request = json.loads(open(request_path, encoding="utf-8").read())
            command = request["command"]
            result = {
                "schema_version": "devpal.sandbox.runner_result.v1",
                "sandbox_id": request["sandbox_id"],
                "execution_id": request["execution_id"],
                "status": "completed",
                "success": True,
                "argv": command["argv"],
                "cwd": command["cwd"],
                "pid": 1234,
                "exit_code": 0,
                "stdout": "fake stdout",
                "stderr": "",
                "duration_ms": 7,
                "timed_out": False,
                "cleanup_status": "clean",
                "job_object": "fake-job"
            }
            with open(request["result_path"], "w", encoding="utf-8") as handle:
                json.dump(result, handle)
            """
        ).strip(),
        encoding="utf-8",
    )
    return runner


def test_default_runner_invocation_prefers_bundled_dotnet(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    output_dir = repo / "runners" / "windows" / "devpal-sandbox-runner" / "bin" / "Release" / "net8.0"
    dotnet = repo / ".tmp" / "dotnet8" / "dotnet.exe"
    runner_dll = output_dir / "devpal-sandbox-runner.dll"
    runner_exe = output_dir / "devpal-sandbox-runner.exe"
    dotnet.parent.mkdir(parents=True)
    output_dir.mkdir(parents=True)
    dotnet.write_text("", encoding="utf-8")
    runner_dll.write_text("", encoding="utf-8")
    runner_exe.write_text("", encoding="utf-8")

    monkeypatch.delenv("DEVPAL_SANDBOX_RUNNER", raising=False)
    monkeypatch.setattr(windows_process_backend, "_repo_root", lambda: repo)

    runner_path, runner_args = windows_process_backend._resolve_runner_invocation(
        None,
        ["--extra"],
    )

    assert runner_path == dotnet
    assert runner_args == [str(runner_dll), "--extra"]


def test_default_runner_invocation_honors_configured_env_runner(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    dotnet = repo / ".tmp" / "dotnet8" / "dotnet.exe"
    runner_dll = (
        repo
        / "runners"
        / "windows"
        / "devpal-sandbox-runner"
        / "bin"
        / "Release"
        / "net8.0"
        / "devpal-sandbox-runner.dll"
    )
    configured = tmp_path / "configured-runner.exe"
    dotnet.parent.mkdir(parents=True)
    runner_dll.parent.mkdir(parents=True)
    dotnet.write_text("", encoding="utf-8")
    runner_dll.write_text("", encoding="utf-8")
    configured.write_text("", encoding="utf-8")

    monkeypatch.setenv("DEVPAL_SANDBOX_RUNNER", str(configured))
    monkeypatch.setattr(windows_process_backend, "_repo_root", lambda: repo)

    runner_path, runner_args = windows_process_backend._resolve_runner_invocation(
        None,
        ["--extra"],
    )

    assert runner_path == configured
    assert runner_args == ["--extra"]


def test_windows_process_backend_builds_runner_request(tmp_path):
    request = SandboxRequest.from_legacy(
        tmp_path,
        task_id="phase10:test",
        phase_number=10,
        role="test",
        sandbox_level="strict",
        allowed_paths=["tests/test_example.py"],
        execution_id="exec-windows-process",
        trace_id="trace-windows-process",
    )
    session = WindowsProcessSandboxBackend(
        runner_path=sys.executable,
        runner_args=[str(_fake_runner(tmp_path))],
    ).create_session(request)
    command = CommandSpec(
        argv=["python", "-m", "pytest"],
        cwd=tmp_path,
        timeout_seconds=10,
        env={
            "PATH": "safe-path",
            "INCLUDE": "safe-include",
            "ANTHROPIC_AUTH_TOKEN": "secret-token",
            "OPENAI_API_KEY": "secret-key",
            "CUSTOM_PASSWORD": "secret-password",
        },
    )

    request_path = session.write_runner_request(command)
    data = json.loads(request_path.read_text(encoding="utf-8"))

    assert data["schema_version"] == "devpal.sandbox.runner_request.v1"
    assert data["backend"] == "windows_process"
    assert data["isolation_level"] == "process"
    assert data["execution_id"] == "exec-windows-process"
    assert Path(data["project_dir"]) == tmp_path
    assert Path(data["sandbox_dir"]) == session.sandbox_dir
    assert data["command"]["argv"] == ["python", "-m", "pytest"]
    assert data["command"]["env"]["PATH"] == "safe-path"
    assert "INCLUDE" not in data["command"]["env"]
    assert "ANTHROPIC_AUTH_TOKEN" not in data["command"]["env"]
    assert "OPENAI_API_KEY" not in data["command"]["env"]
    assert "CUSTOM_PASSWORD" not in data["command"]["env"]
    assert data["policy"]["backend"] == "windows_process"
    assert data["policy"]["isolation_level"] == "process"
    assert data["isolation"] == {
        "low_integrity": False,
        "harden_workspace_acl": False,
        "network_deny": False,
        "restricted_token": False,
    }


def test_windows_process_backend_writes_requested_isolation_features(tmp_path):
    request = SandboxRequest.from_legacy(
        tmp_path,
        task_id="phase10:test",
        phase_number=10,
        role="test",
        sandbox_level="strict",
        allowed_paths=["tests/test_example.py"],
    )
    request.policy.metadata["isolation_features"] = {
        "low_integrity": True,
        "harden_workspace_acl": True,
        "network_deny": True,
        "restricted_token": True,
    }
    request.policy.max_memory_mb = 64
    session = WindowsProcessSandboxBackend(
        runner_path=sys.executable,
        runner_args=[str(_fake_runner(tmp_path))],
    ).create_session(request)

    request_path = session.write_runner_request(
        CommandSpec(argv=["python", "-m", "pytest"], cwd=tmp_path, timeout_seconds=10)
    )
    data = json.loads(request_path.read_text(encoding="utf-8"))

    assert data["isolation"] == {
        "low_integrity": True,
        "harden_workspace_acl": True,
        "network_deny": True,
        "restricted_token": True,
    }
    assert data["policy"]["max_memory_mb"] == 64


def test_windows_process_backend_sanitizes_current_env_when_command_env_absent(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("DEVPAL_SAFE_ENV", "safe-value")
    monkeypatch.setenv("OPENAI_API_KEY", "secret-key")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "secret-token")
    request = SandboxRequest.from_legacy(
        tmp_path,
        task_id="phase10:test",
        phase_number=10,
        role="test",
        sandbox_level="strict",
        allowed_paths=["tests/test_example.py"],
    )
    session = WindowsProcessSandboxBackend(
        runner_path=sys.executable,
        runner_args=[str(_fake_runner(tmp_path))],
    ).create_session(request)
    command = CommandSpec(argv=["python", "-m", "pytest"], cwd=tmp_path, timeout_seconds=10)

    request_path = session.write_runner_request(command)
    data = json.loads(request_path.read_text(encoding="utf-8"))

    assert data["command"]["env"]["DEVPAL_SAFE_ENV"] == "safe-value"
    assert "OPENAI_API_KEY" not in data["command"]["env"]
    assert "ANTHROPIC_AUTH_TOKEN" not in data["command"]["env"]


def test_windows_process_backend_executes_fake_runner_and_writes_manifest_v2(tmp_path):
    request = SandboxRequest.from_legacy(
        tmp_path,
        task_id="phase10:test",
        phase_number=10,
        role="test",
        sandbox_level="strict",
        allowed_paths=["tests/test_example.py"],
        execution_id="exec-windows-process",
    )
    session = WindowsProcessSandboxBackend(
        runner_path=sys.executable,
        runner_args=[str(_fake_runner(tmp_path))],
    ).create_session(request)
    command = CommandSpec(argv=["python", "-m", "pytest"], cwd=tmp_path, timeout_seconds=10)

    result = session.execute_command(command)
    manifest = read_manifest_v2(session.manifest_v2_path)

    assert result.returncode == 0
    assert result.stdout == "fake stdout"
    assert session.runner_request_path.exists()
    assert session.runner_result_path.exists()
    assert manifest["backend"] == "windows_process"
    assert manifest["isolation_level"] == "process"
    assert manifest["status"] == "completed"
    assert manifest["metadata"]["command_result"]["returncode"] == 0
    assert manifest["metadata"]["runner_result"]["job_object"] == "fake-job"
    assert manifest["metadata"]["runner_executable_path"] == sys.executable
    assert manifest["metadata"]["runner_args"] == [str(session.runner_args[0])]
    assert manifest["metadata"]["runner_invocation"][-1] == str(session.runner_request_path)


def test_windows_process_backend_preserves_production_command_block(tmp_path):
    request = SandboxRequest.from_legacy(
        tmp_path,
        task_id="phase10:test",
        phase_number=10,
        role="test",
        sandbox_level="production",
        allowed_paths=["tests/test_example.py"],
    )
    session = WindowsProcessSandboxBackend(
        runner_path=sys.executable,
        runner_args=[str(_fake_runner(tmp_path))],
    ).create_session(request)

    with pytest.raises(ValueError, match="production sandbox does not allow local command execution"):
        session.execute_command(CommandSpec(argv=["python", "-m", "pytest"], cwd=tmp_path))


def test_windows_process_backend_reports_missing_runner(tmp_path):
    request = SandboxRequest.from_legacy(
        tmp_path,
        task_id="phase10:test",
        phase_number=10,
        role="test",
        sandbox_level="strict",
        allowed_paths=["tests/test_example.py"],
    )
    session = WindowsProcessSandboxBackend(
        runner_path=tmp_path / "missing-runner.exe",
    ).create_session(request)

    with pytest.raises(FileNotFoundError, match="missing Windows sandbox runner"):
        session.execute_command(CommandSpec(argv=["python", "-m", "pytest"], cwd=tmp_path))
