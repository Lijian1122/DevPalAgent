# -*- coding: utf-8 -*-

import json
from pathlib import Path

from devpal.core.multi_agent import CommandSpec
from devpal.core.openspec_phases.base import OpenSpecContext
from devpal.core.sandbox import SandboxRequest
from devpal.core.sandbox.backends import WindowsContainerSandboxBackend
from devpal.core.sandbox.backends.windows_container import (
    ERROR_CODE_CONTAINER_BACKEND_NOT_IMPLEMENTED,
)
from devpal.core.sandbox.manager import SandboxManager


def _request(project_dir: Path) -> SandboxRequest:
    return SandboxRequest.from_legacy(
        project_dir=project_dir,
        task_id="phase10:container:probe",
        phase_number=10,
        role="test",
        sandbox_level="staging",
        timeout_seconds=10,
    )


def test_container_backend_exposes_session_protocol(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    session = WindowsContainerSandboxBackend().create_session(_request(project))

    assert session.backend_name == "windows_container"
    assert session.isolation_level == "container"
    # Backend-neutral audit paths mirror the windows_process session.
    assert session.manifest_v2_path.name == "manifest.v2.json"
    assert session.runner_request_path.name == "runner_request.json"


def test_container_backend_fails_closed_but_writes_audit_chain(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    session = WindowsContainerSandboxBackend(
        container_options={"image": "custom/image:1", "isolation": "hyperv"}
    ).create_session(_request(project))

    result = session.execute_command(
        CommandSpec(argv=["python", "--version"], cwd=project, timeout_seconds=10)
    )

    # Fail closed: no silent downgrade to a weaker backend.
    assert result.returncode == -1
    assert result.error is not None
    assert ERROR_CODE_CONTAINER_BACKEND_NOT_IMPLEMENTED in result.error

    # Audit chain is still written so the attempt is traceable.
    assert session.runner_request_path.exists()
    request = json.loads(session.runner_request_path.read_text(encoding="utf-8"))
    assert request["backend"] == "windows_container"
    assert request["isolation_level"] == "container"
    assert request["container"]["image"] == "custom/image:1"
    assert request["container"]["isolation"] == "hyperv"

    manifest = json.loads(session.manifest_v2_path.read_text(encoding="utf-8"))
    assert manifest["backend"] == "windows_container"
    assert manifest["status"] == "failed"
    assert manifest["metadata"]["error_code"] == ERROR_CODE_CONTAINER_BACKEND_NOT_IMPLEMENTED
    assert manifest["metadata"]["container"]["runtime"] == "docker"


def test_container_spec_maps_network_deny_and_limits(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    request = _request(project)
    request.policy.network = "deny"
    request.policy.max_memory_mb = 256
    request.policy.max_processes = 4
    session = WindowsContainerSandboxBackend().create_session(request)

    spec = session.container_spec()
    assert spec["network"] == "none"
    assert spec["max_memory_mb"] == 256
    assert spec["max_processes"] == 4
    assert spec["mounts"][0]["container_path"] == spec["container_workspace"]


def test_sandbox_manager_dispatches_container_backend(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    context = OpenSpecContext(
        project_dir=project, requirements_file=tmp_path / "requirements.md"
    )
    context.sandbox_backend = "windows_container"
    context.sandbox_level = "staging"
    context.sandbox_backend_options = {
        "container_options": {"image": "custom/image:2"},
    }

    execution = SandboxManager(
        phase_number=10,
        context=context,
        workflow_id="wf-container",
    ).execute_command(
        task_id="phase10:manager:container",
        command=CommandSpec(argv=["python", "--version"], cwd=project, timeout_seconds=10),
    )

    # Manager routes to the container backend and reports the fail-closed result.
    assert execution.command_result.returncode == -1
    metadata = execution.summary["results"][0]["metadata"]
    assert metadata["backend"] == "windows_container"
    assert metadata["isolation_level"] == "container"
    assert execution.summary["failed_count"] == 1
    request = json.loads(Path(metadata["runner_request_path"]).read_text(encoding="utf-8"))
    assert request["container"]["image"] == "custom/image:2"
