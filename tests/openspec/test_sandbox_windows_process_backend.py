# -*- coding: utf-8 -*-

import json
import sys
import textwrap
from pathlib import Path

import pytest

from devpal.core.multi_agent import CommandSpec
from devpal.core.sandbox import SandboxRequest, read_manifest_v2
from devpal.core.sandbox.backends import WindowsProcessSandboxBackend


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
    assert data["command"]["env"]["INCLUDE"] == "safe-include"
    assert "ANTHROPIC_AUTH_TOKEN" not in data["command"]["env"]
    assert "OPENAI_API_KEY" not in data["command"]["env"]
    assert "CUSTOM_PASSWORD" not in data["command"]["env"]
    assert data["policy"]["backend"] == "windows_process"
    assert data["policy"]["isolation_level"] == "process"


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
