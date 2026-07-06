# -*- coding: utf-8 -*-
"""Windows container sandbox backend (HCS / Hyper-V) interface skeleton.

This backend is the P3 evolution target described in the design doc. It is the
placeholder for a strongly isolated Windows container backend (Host Compute
System / Hyper-V isolated Windows container), reusing the same
``SandboxRequest -> runner_request.json -> runner_result.json -> manifest.v2``
protocol as the ``windows_process`` backend.

It is intentionally an interface skeleton: ``execute_command`` does not launch a
real container. Instead it fails closed with a structured result and error code
``CONTAINER_BACKEND_NOT_IMPLEMENTED``. This preserves the full audit chain
(runner request + manifest v2 are still written) while making it explicit that
no strong-isolation execution happened. When the real HCS/Hyper-V launcher is
added, only ``execute_command`` needs to change; the wiring, manifest, event and
final-report layers already understand this backend name.
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from devpal.core.multi_agent.models import CommandResult, CommandSpec
from devpal.core.multi_agent.sandbox import SandboxSession

from ..env_profiles import build_env_profile
from ..manifest import build_manifest_v2, write_manifest_v2
from ..models import SandboxArtifact, SandboxRequest
from ..runner_schema import RUNNER_REQUEST_SCHEMA_VERSION, validate_runner_request


ERROR_CODE_CONTAINER_BACKEND_NOT_IMPLEMENTED = "CONTAINER_BACKEND_NOT_IMPLEMENTED"

DEFAULT_CONTAINER_IMAGE = "mcr.microsoft.com/windows/nanoserver:ltsc2022"
DEFAULT_CONTAINER_ISOLATION = "hyperv"
DEFAULT_CONTAINER_WORKSPACE = "C:\\workspace"


def _now_utc() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _path_to_string(path: Path | str | None) -> Optional[str]:
    if path is None:
        return None
    return Path(path).as_posix()


class WindowsContainerSandboxSession:
    """Backend-shaped session for a Windows HCS / Hyper-V container.

    Mirrors :class:`WindowsProcessSandboxSession` so the manager, manifest,
    EventBus and final-report layers treat both backends uniformly. Execution is
    not yet implemented and fails closed.
    """

    backend_name = "windows_container"
    isolation_level = "container"

    def __init__(
        self,
        request: SandboxRequest,
        container_options: Optional[Dict[str, Any]] = None,
    ):
        policy = replace(
            request.policy,
            backend=self.backend_name,
            isolation_level=self.isolation_level,
        )
        self.request = replace(request, policy=policy)
        self.container_options = dict(container_options or {})
        self._session = SandboxSession(
            project_dir=self.request.project_dir,
            task_id=self.request.task_id,
            phase_number=self.request.phase_number,
            role=self.request.role,
            sandbox_level=self.request.policy.sandbox_level,
            allowed_paths=self.request.policy.allowed_paths,
        )

    @property
    def sandbox_id(self) -> str:
        return self._session.sandbox_id

    @property
    def sandbox_dir(self) -> Path:
        return self._session.sandbox_dir

    @property
    def workspace_dir(self) -> Path:
        return self._session.workspace_dir

    @property
    def manifest_path(self) -> Path:
        return self._session.manifest_path

    @property
    def manifest_v2_path(self) -> Path:
        return self.sandbox_dir / "manifest.v2.json"

    @property
    def runner_request_path(self) -> Path:
        return self.sandbox_dir / "runner_request.json"

    @property
    def runner_result_path(self) -> Path:
        return self.sandbox_dir / "runner_result.json"

    def prepare_workspace(self) -> Path:
        return self._session.prepare_workspace()

    def resolve_workspace_target(self, rel_path: str) -> Path:
        return self._session.resolve_workspace_target(rel_path)

    def resolve_target(self, rel_path: str) -> Path:
        return self._session.resolve_target(rel_path)

    def validate_command(self, command: CommandSpec) -> CommandSpec:
        return self._session.validate_command(command)

    def container_spec(self) -> Dict[str, Any]:
        """Container launch parameters recorded in the runner request.

        This is the request-side protocol a future HCS/Hyper-V launcher will
        consume. Populated from ``sandbox_backend_options`` so an operator can
        pin an image and isolation mode without code changes.
        """

        network_deny = str(self.request.policy.network).lower() == "deny"
        return {
            "image": str(self.container_options.get("image", DEFAULT_CONTAINER_IMAGE)),
            "isolation": str(
                self.container_options.get("isolation", DEFAULT_CONTAINER_ISOLATION)
            ),
            "runtime": str(self.container_options.get("runtime", "docker")),
            "container_workspace": str(
                self.container_options.get(
                    "container_workspace", DEFAULT_CONTAINER_WORKSPACE
                )
            ),
            "network": "none" if network_deny else "default",
            "max_memory_mb": self.request.policy.max_memory_mb,
            "max_processes": self.request.policy.max_processes,
            "mounts": [
                {
                    "host_path": _path_to_string(self.workspace_dir),
                    "container_path": str(
                        self.container_options.get(
                            "container_workspace", DEFAULT_CONTAINER_WORKSPACE
                        )
                    ),
                    "read_only": False,
                }
            ],
        }

    def build_runner_request(self, command: CommandSpec) -> Dict[str, Any]:
        self.prepare_workspace()
        return {
            "schema_version": RUNNER_REQUEST_SCHEMA_VERSION,
            "sandbox_id": self.sandbox_id,
            "execution_id": self.request.execution_id or f"{self.sandbox_id}-{_now_utc()}",
            "backend": self.backend_name,
            "isolation_level": self.isolation_level,
            "project_dir": _path_to_string(self.request.project_dir),
            "sandbox_dir": _path_to_string(self.sandbox_dir),
            "workspace_dir": _path_to_string(self.workspace_dir),
            "result_path": _path_to_string(self.runner_result_path),
            "command": {
                "argv": list(command.argv),
                "cwd": _path_to_string(command.cwd),
                "timeout_seconds": int(command.timeout_seconds),
                "env": build_env_profile(command.argv, env=command.env),
                "capture_output": bool(command.capture_output),
                "text": bool(command.text),
                "encoding": command.encoding or "utf-8",
                "errors": command.errors or "replace",
            },
            "policy": self.request.policy.to_dict(),
            "container": self.container_spec(),
            "trace": {
                "trace_id": self.request.trace_id,
                "event_log": str(self.request.metadata.get("event_log", "")),
            },
            "metadata": dict(self.request.metadata),
        }

    def write_runner_request(self, command: CommandSpec) -> Path:
        self.validate_command(command)
        request = self.build_runner_request(command)
        errors = validate_runner_request(request)
        if errors:
            raise ValueError("invalid runner request: " + "; ".join(errors))
        self.runner_request_path.parent.mkdir(parents=True, exist_ok=True)
        self.runner_request_path.write_text(
            json.dumps(request, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self.runner_request_path

    def execute_command(self, command: CommandSpec) -> CommandResult:
        """Fail closed: the HCS / Hyper-V launcher is not implemented yet.

        The runner request and manifest v2 are still written so the audit chain
        and final report show a container-backend attempt that was deliberately
        refused rather than silently downgraded to a weaker backend.
        """

        started = datetime.now(UTC)
        self.write_runner_request(command)
        message = (
            f"{ERROR_CODE_CONTAINER_BACKEND_NOT_IMPLEMENTED}: windows_container "
            "backend is an interface skeleton; HCS/Hyper-V launcher is not "
            "implemented. Use --sandbox-backend windows_process for execution."
        )
        result = CommandResult(
            argv=list(command.argv),
            cwd=command.cwd,
            returncode=-1,
            error=message,
            duration_ms=int((datetime.now(UTC) - started).total_seconds() * 1000),
        )
        self.write_manifest_v2(
            status="failed",
            error_code=ERROR_CODE_CONTAINER_BACKEND_NOT_IMPLEMENTED,
            container=self.container_spec(),
            command_result={
                "argv": list(result.argv),
                "cwd": str(result.cwd),
                "returncode": result.returncode,
                "error": result.error,
                "error_code": ERROR_CODE_CONTAINER_BACKEND_NOT_IMPLEMENTED,
            },
        )
        return result

    def manifest(self, artifacts: Iterable[Path] = ()) -> dict:
        data = self._session.manifest(artifacts)
        data.update(
            {
                "backend": self.backend_name,
                "isolation_level": self.isolation_level,
                "container": self.container_spec(),
                "runner_request_path": str(self.runner_request_path),
                "runner_result_path": str(self.runner_result_path),
            }
        )
        return data

    def write_manifest(self, artifacts: Iterable[Path] = (), **metadata) -> Path:
        return self._session.write_manifest(artifacts, **metadata)

    def build_manifest_v2(
        self,
        artifacts: Iterable[SandboxArtifact | Path | str] = (),
        **metadata,
    ) -> dict:
        status = str(metadata.pop("status", "created"))
        return build_manifest_v2(
            self.request,
            sandbox_id=self.sandbox_id,
            sandbox_dir=self.sandbox_dir,
            workspace_dir=self.workspace_dir,
            manifest_path=self.manifest_v2_path,
            status=status,
            backend=self.backend_name,
            isolation_level=self.isolation_level,
            artifacts=artifacts,
            metadata={
                "container": self.container_spec(),
                "runner_request_path": str(self.runner_request_path),
                "runner_result_path": str(self.runner_result_path),
                **metadata,
            },
        )

    def write_manifest_v2(
        self,
        artifacts: Iterable[SandboxArtifact | Path | str] = (),
        **metadata,
    ) -> Path:
        manifest = self.build_manifest_v2(artifacts, **metadata)
        return write_manifest_v2(self.manifest_v2_path, manifest)


class WindowsContainerSandboxBackend:
    """Backend factory for the Windows container (HCS / Hyper-V) skeleton."""

    backend_name = "windows_container"
    isolation_level = "container"

    def __init__(self, container_options: Optional[Dict[str, Any]] = None):
        self.container_options = dict(container_options or {})

    def create_session(self, request: SandboxRequest) -> WindowsContainerSandboxSession:
        return WindowsContainerSandboxSession(
            request,
            container_options=self.container_options,
        )
