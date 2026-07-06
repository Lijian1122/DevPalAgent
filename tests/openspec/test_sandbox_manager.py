# -*- coding: utf-8 -*-

import json
import sys
import textwrap
from pathlib import Path

import pytest

from devpal.core.multi_agent import CommandSpec
from devpal.core.openspec_phases.base import OpenSpecContext
from devpal.core.sandbox.manager import SandboxManager, SandboxPolicyViolation


def _fake_runner(tmp_path):
    runner = tmp_path / "fake_manager_runner.py"
    runner.write_text(
        textwrap.dedent(
            """
            import json
            import sys
            from pathlib import Path

            request = json.loads(Path(sys.argv[-1]).read_text(encoding="utf-8"))
            command = request["command"]
            Path(request["result_path"]).write_text(
                json.dumps({
                    "schema_version": "devpal.sandbox.runner_result.v1",
                    "sandbox_id": request["sandbox_id"],
                    "execution_id": request["execution_id"],
                    "status": "completed",
                    "success": True,
                    "argv": command["argv"],
                    "cwd": command["cwd"],
                    "exit_code": 0,
                    "stdout": "ok",
                    "stderr": "",
                    "duration_ms": 3,
                    "timed_out": False,
                    "cleanup_status": "clean",
                    "isolation": request["isolation"],
                    "job_memory_limit_mb": request["policy"].get("max_memory_mb"),
                }),
                encoding="utf-8",
            )
            """
        ).strip(),
        encoding="utf-8",
    )
    return runner


def test_sandbox_manager_executes_windows_process_backend_and_records_summary(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    execution_project = project / ".spec" / "sandboxes" / "phase10-workspace-execution" / "workspace"
    execution_project.mkdir(parents=True)
    context = OpenSpecContext(project_dir=project, requirements_file=tmp_path / "requirements.md")
    context.sandbox_backend = "windows_process"
    context.sandbox_level = "staging"
    context.sandbox_backend_options = {
        "runner_path": sys.executable,
        "runner_args": [str(_fake_runner(tmp_path))],
        "execution_project_dir": str(execution_project),
        "low_integrity": True,
        "harden_workspace_acl": True,
        "network_deny": True,
        "restricted_token": True,
        "max_memory_mb": 128,
    }

    execution = SandboxManager(
        phase_number=10,
        context=context,
        workflow_id="wf-test",
    ).execute_command(
        task_id="phase10:manager:probe",
        command=CommandSpec(argv=["python", "--version"], cwd=execution_project, timeout_seconds=10),
    )

    assert execution.command_result.returncode == 0
    assert execution.summary["success_count"] == 1
    metadata = execution.summary["results"][0]["metadata"]
    request = json.loads(Path(metadata["runner_request_path"]).read_text(encoding="utf-8"))
    assert metadata["backend"] == "windows_process"
    assert request["isolation"] == {
        "low_integrity": True,
        "harden_workspace_acl": True,
        "network_deny": True,
        "restricted_token": True,
    }
    assert request["policy"]["max_memory_mb"] == 128
    assert execution.runner_result["isolation"]["low_integrity"] is True
    assert execution.runner_result["job_memory_limit_mb"] == 128


def test_sandbox_manager_rejects_acl_hardening_without_workspace_execution(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    context = OpenSpecContext(project_dir=project, requirements_file=tmp_path / "requirements.md")
    context.sandbox_backend = "windows_process"
    context.sandbox_level = "staging"
    context.sandbox_backend_options = {
        "runner_path": sys.executable,
        "runner_args": [str(_fake_runner(tmp_path))],
        "harden_workspace_acl": True,
    }

    with pytest.raises(SandboxPolicyViolation, match="harden_workspace_acl requires"):
        SandboxManager(
            phase_number=10,
            context=context,
            workflow_id="wf-test",
        ).execute_command(
            task_id="phase10:manager:unsafe-acl",
            command=CommandSpec(argv=["python", "--version"], cwd=project, timeout_seconds=10),
        )
