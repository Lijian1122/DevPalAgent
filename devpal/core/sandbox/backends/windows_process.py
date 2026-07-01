# -*- coding: utf-8 -*-
"""Windows process sandbox backend wrapper.

This backend is the Python orchestration side of the Phase 2 MVP. It writes a
runner request JSON, invokes an external Windows runner process, reads the
runner result JSON, and records manifest v2 audit data. The runner itself lives
under ``runners/windows/devpal-sandbox-runner``.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from devpal.core.multi_agent.models import CommandResult, CommandSpec
from devpal.core.multi_agent.sandbox import SandboxSession

from ..manifest import build_manifest_v2, write_manifest_v2
from ..models import SandboxArtifact, SandboxPolicy, SandboxRequest


RUNNER_REQUEST_SCHEMA_VERSION = "devpal.sandbox.runner_request.v1"
RUNNER_RESULT_SCHEMA_VERSION = "devpal.sandbox.runner_result.v1"


def _now_utc() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _path_to_string(path: Path | str | None) -> Optional[str]:
    if path is None:
        return None
    return Path(path).as_posix()


def _default_runner_path() -> Path:
    configured = os.environ.get("DEVPAL_SANDBOX_RUNNER")
    if configured:
        return Path(configured)
    return (
        Path(__file__).resolve().parents[4]
        / "runners"
        / "windows"
        / "devpal-sandbox-runner"
        / "bin"
        / "Release"
        / "net8.0"
        / "devpal-sandbox-runner.exe"
    )


class WindowsProcessSandboxSession:
    """Backend-shaped session that delegates execution to a Windows runner."""

    backend_name = "windows_process"
    isolation_level = "process"

    def __init__(
        self,
        request: SandboxRequest,
        runner_path: Path | str | None = None,
        runner_args: Optional[List[str]] = None,
        runner_timeout_grace_seconds: int = 5,
    ):
        policy = replace(
            request.policy,
            backend=self.backend_name,
            isolation_level=self.isolation_level,
        )
        self.request = replace(request, policy=policy)
        self.runner_path = Path(runner_path) if runner_path else _default_runner_path()
        self.runner_args = list(runner_args or [])
        self.runner_timeout_grace_seconds = runner_timeout_grace_seconds
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

    def write_manifest(self, artifacts: Iterable[Path] = (), **metadata) -> Path:
        return self._session.write_manifest(artifacts, **metadata)

    def manifest(self, artifacts: Iterable[Path] = ()) -> dict:
        data = self._session.manifest(artifacts)
        data.update(
            {
                "backend": self.backend_name,
                "isolation_level": self.isolation_level,
                "runner_request_path": str(self.runner_request_path),
                "runner_result_path": str(self.runner_result_path),
            }
        )
        return data

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
                "env": dict(command.env or {}),
                "capture_output": bool(command.capture_output),
                "text": bool(command.text),
                "encoding": command.encoding or "utf-8",
                "errors": command.errors or "replace",
            },
            "policy": self.request.policy.to_dict(),
            "trace": {
                "trace_id": self.request.trace_id,
                "event_log": str(self.request.metadata.get("event_log", "")),
            },
            "metadata": dict(self.request.metadata),
        }

    def write_runner_request(self, command: CommandSpec) -> Path:
        self.validate_command(command)
        request = self.build_runner_request(command)
        self.runner_request_path.parent.mkdir(parents=True, exist_ok=True)
        self.runner_request_path.write_text(
            json.dumps(request, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self.runner_request_path

    def execute_command(self, command: CommandSpec) -> CommandResult:
        request_path = self.write_runner_request(command)
        if not self.runner_path.exists():
            raise FileNotFoundError(f"missing Windows sandbox runner: {self.runner_path}")

        started = datetime.now(UTC)
        try:
            completed = subprocess.run(
                [str(self.runner_path), *self.runner_args, str(request_path)],
                capture_output=True,
                text=True,
                encoding=command.encoding or "utf-8",
                errors=command.errors or "replace",
                timeout=max(1, int(command.timeout_seconds) + self.runner_timeout_grace_seconds),
            )
        except subprocess.TimeoutExpired as exc:
            result = CommandResult(
                argv=list(command.argv),
                cwd=command.cwd,
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
                timed_out=True,
                error=f"sandbox runner timeout after {command.timeout_seconds}s",
                duration_ms=int((datetime.now(UTC) - started).total_seconds() * 1000),
            )
            self.write_manifest_v2(status="timeout", command_result=result.to_dict() if hasattr(result, "to_dict") else _command_result_to_dict(result))
            return result

        if not self.runner_result_path.exists():
            result = CommandResult(
                argv=list(command.argv),
                cwd=command.cwd,
                returncode=completed.returncode,
                stdout=completed.stdout or "",
                stderr=completed.stderr or "",
                duration_ms=int((datetime.now(UTC) - started).total_seconds() * 1000),
                error=f"sandbox runner did not write result: {self.runner_result_path}",
            )
            self.write_manifest_v2(
                status="failed",
                runner_returncode=completed.returncode,
                runner_stdout=completed.stdout or "",
                runner_stderr=completed.stderr or "",
                command_result=_command_result_to_dict(result),
            )
            return result

        runner_result = json.loads(self.runner_result_path.read_text(encoding="utf-8-sig"))
        result = _command_result_from_runner(command, runner_result)
        status = "timeout" if result.timed_out else ("completed" if result.returncode == 0 and not result.error else "failed")
        self.write_manifest_v2(
            status=status,
            runner_returncode=completed.returncode,
            runner_stdout=completed.stdout or "",
            runner_stderr=completed.stderr or "",
            runner_result=runner_result,
            command_result=_command_result_to_dict(result),
        )
        return result

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


class WindowsProcessSandboxBackend:
    backend_name = "windows_process"
    isolation_level = "process"

    def __init__(
        self,
        runner_path: Path | str | None = None,
        runner_args: Optional[List[str]] = None,
        runner_timeout_grace_seconds: int = 5,
    ):
        self.runner_path = runner_path
        self.runner_args = list(runner_args or [])
        self.runner_timeout_grace_seconds = runner_timeout_grace_seconds

    def create_session(self, request: SandboxRequest) -> WindowsProcessSandboxSession:
        return WindowsProcessSandboxSession(
            request,
            runner_path=self.runner_path,
            runner_args=self.runner_args,
            runner_timeout_grace_seconds=self.runner_timeout_grace_seconds,
        )


def _command_result_to_dict(result: CommandResult) -> Dict[str, Any]:
    return {
        "argv": list(result.argv),
        "cwd": str(result.cwd),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "duration_ms": result.duration_ms,
        "timed_out": result.timed_out,
        "error": result.error,
    }


def _command_result_from_runner(command: CommandSpec, data: Dict[str, Any]) -> CommandResult:
    return CommandResult(
        argv=list(data.get("argv") or command.argv),
        cwd=data.get("cwd") or command.cwd,
        returncode=int(data.get("exit_code", data.get("returncode", -1))),
        stdout=str(data.get("stdout") or ""),
        stderr=str(data.get("stderr") or ""),
        duration_ms=int(data.get("duration_ms", 0) or 0),
        timed_out=bool(data.get("timed_out", False)),
        error=data.get("error") or None,
    )
