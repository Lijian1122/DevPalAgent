# -*- coding: utf-8 -*-
"""Backend-neutral sandbox execution coordinator."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from devpal.core.multi_agent.models import CommandResult, CommandSpec

from .backends import WindowsContainerSandboxBackend, WindowsProcessSandboxBackend
from .models import SandboxRequest
from .reaper import SandboxReaper


class SandboxPolicyViolation(Exception):
    """Raised when deterministic sandbox policy rejects a command."""


SANDBOX_MANAGER_BACKENDS = ("windows_process", "windows_container")


@dataclass
class SandboxExecution:
    command_result: CommandResult
    summary: Dict[str, Any]
    sandbox_id: str = ""
    cleanup_status: str = "unknown"
    runner_result: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SandboxManager:
    """Own backend selection, audit emission, reaper hook, and fallback policy."""

    def __init__(
        self,
        *,
        phase_number: int,
        context: Any,
        workflow_id: str = "",
        log=None,
    ):
        self.phase_number = phase_number
        self.context = context
        self.workflow_id = workflow_id
        self.log = log or (lambda _message: None)

    def execute_command(
        self,
        *,
        task_id: str,
        command: CommandSpec,
        role: str = "test",
    ) -> SandboxExecution:
        backend_name = getattr(self.context, "sandbox_backend", "policy")
        if backend_name not in SANDBOX_MANAGER_BACKENDS:
            raise ValueError(f"unsupported sandbox backend for manager: {backend_name}")
        return self._execute_backend(
            backend_name=backend_name,
            task_id=task_id,
            command=command,
            role=role,
        )

    def reap_stale(self, *, dry_run: bool = True, stale_after_seconds: int = 3600):
        return SandboxReaper(
            getattr(self.context, "project_dir"),
            stale_after_seconds=stale_after_seconds,
        ).reap(dry_run=dry_run)

    def _execute_backend(
        self,
        *,
        backend_name: str,
        task_id: str,
        command: CommandSpec,
        role: str,
    ) -> SandboxExecution:
        options = dict(getattr(self.context, "sandbox_backend_options", {}) or {})
        original_project_dir = Path(self.context.project_dir).resolve()
        project_dir = Path(
            options.get("execution_project_dir") or original_project_dir
        ).resolve()
        if options.get("harden_workspace_acl"):
            self._validate_acl_hardening_target(
                execution_project_dir=project_dir,
                original_project_dir=original_project_dir,
            )
        request = SandboxRequest.from_legacy(
            project_dir=project_dir,
            task_id=task_id,
            phase_number=self.phase_number,
            role=role,
            sandbox_level=getattr(self.context, "sandbox_level", "staging"),
            allowed_paths=list(options.get("allowed_paths", []) or []),
            timeout_seconds=command.timeout_seconds,
            execution_id=str(options.get("execution_id", "")),
            trace_id=self.workflow_id,
        )
        if options.get("max_processes") is not None:
            request.policy.max_processes = max(1, int(options.get("max_processes") or 1))
        if options.get("max_memory_mb") is not None:
            request.policy.max_memory_mb = max(1, int(options.get("max_memory_mb") or 1))
        request.policy.network = "deny" if options.get("network_deny") else request.policy.network
        request.policy.metadata.update(
            {
                "isolation_features": {
                    "low_integrity": bool(options.get("low_integrity", False)),
                    "harden_workspace_acl": bool(options.get("harden_workspace_acl", False)),
                    "network_deny": bool(options.get("network_deny", False)),
                    "restricted_token": bool(options.get("restricted_token", False)),
                }
            }
        )
        event_logger = getattr(
            getattr(self.context, "event_integration", None),
            "event_logger",
            None,
        )
        request.metadata.update(
            {
                "workflow_id": self.workflow_id,
                "event_log": str(getattr(event_logger, "latest_log_file", "") or ""),
                "original_project_dir": str(original_project_dir),
            }
        )

        backend = self._create_backend(backend_name, options)
        session = backend.create_session(request)
        self._emit_sandbox_created(task_id, session)
        try:
            session.validate_command(command)
        except ValueError as exc:
            self._emit_sandbox_violation(
                task_id,
                session,
                reason=str(exc),
                command=list(command.argv),
            )
            raise SandboxPolicyViolation(str(exc)) from exc

        self._emit_sandbox_policy_applied(task_id, session, request.policy.to_dict())
        self._emit_sandbox_command_started(task_id, session, command)
        try:
            result = session.execute_command(command)
        except FileNotFoundError as exc:
            failure = CommandResult(
                argv=list(command.argv),
                cwd=command.cwd,
                error=str(exc),
            )
            self._emit_sandbox_command_completed(
                task_id,
                session,
                command,
                failure,
                cleanup_status="not_started",
            )
            raise

        runner_result = self._read_runner_result(session.runner_result_path)
        cleanup_status = str(runner_result.get("cleanup_status", "unknown") or "unknown")
        if result.timed_out:
            self._emit_sandbox_timeout(task_id, session, command, command.timeout_seconds)
        self._emit_sandbox_command_completed(
            task_id,
            session,
            command,
            result,
            cleanup_status=cleanup_status,
            runner_result=runner_result,
        )
        self._emit_sandbox_cleanup_completed(task_id, session, cleanup_status)
        return SandboxExecution(
            command_result=result,
            summary=self._build_summary(
                task_id,
                session,
                command,
                result,
                runner_result,
                cleanup_status,
            ),
            sandbox_id=session.sandbox_id,
            cleanup_status=cleanup_status,
            runner_result=runner_result,
        )

    @staticmethod
    def _create_backend(backend_name: str, options: Dict[str, Any]):
        if backend_name == "windows_container":
            return WindowsContainerSandboxBackend(
                container_options=dict(options.get("container_options", {}) or {}),
            )
        return WindowsProcessSandboxBackend(
            runner_path=options.get("runner_path"),
            runner_args=list(options.get("runner_args", []) or []),
            runner_timeout_grace_seconds=int(
                options.get("runner_timeout_grace_seconds", 5) or 5
            ),
        )

    @staticmethod
    def _validate_acl_hardening_target(
        *,
        execution_project_dir: Path,
        original_project_dir: Path,
    ) -> None:
        sandbox_root = original_project_dir / ".spec" / "sandboxes"
        try:
            execution_project_dir.relative_to(sandbox_root.resolve())
        except Exception as exc:
            raise SandboxPolicyViolation(
                "harden_workspace_acl requires phase10_workspace_execution "
                "or an execution_project_dir under .spec/sandboxes"
            ) from exc

    @staticmethod
    def _read_runner_result(path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            return {}

    @staticmethod
    def _build_summary(
        task_id: str,
        session,
        command: CommandSpec,
        result: CommandResult,
        runner_result: Dict[str, Any],
        cleanup_status: str,
    ) -> Dict[str, Any]:
        success = result.returncode == 0 and not result.timed_out and not result.error
        metadata = {
            "sandbox_id": session.sandbox_id,
            "sandbox": session.manifest(),
            "backend": session.backend_name,
            "isolation_level": session.isolation_level,
            "manifest_v2_path": str(session.manifest_v2_path),
            "runner_request_path": str(session.runner_request_path),
            "runner_result_path": str(session.runner_result_path),
            "cleanup_status": cleanup_status,
            "timed_out": result.timed_out,
            "commands": [
                {
                    "argv": list(result.argv),
                    "cwd": str(result.cwd),
                    "returncode": result.returncode,
                    "duration_ms": result.duration_ms,
                    "timed_out": result.timed_out,
                    "error": result.error,
                }
            ],
        }
        if runner_result:
            metadata["runner_result"] = runner_result
        return {
            "total_tasks": 1,
            "success_count": 1 if success else 0,
            "failed_count": 0 if success else 1,
            "retry_count": 0,
            "max_concurrency": 1,
            "fallback_used": False,
            "total_task_duration_ms": int(result.duration_ms or 0),
            "results": [
                {
                    "task_id": task_id,
                    "success": success,
                    "duration_ms": int(result.duration_ms or 0),
                    "sandbox_id": session.sandbox_id,
                    "metadata": metadata,
                }
            ],
        }

    def _emit_sandbox_created(self, task_id: str, session) -> None:
        integration = getattr(self.context, "event_integration", None)
        if integration and hasattr(integration, "emit_sandbox_created"):
            integration.emit_sandbox_created(
                self.phase_number,
                task_id,
                sandbox_id=session.sandbox_id,
                backend=session.backend_name,
                isolation_level=session.isolation_level,
                manifest_path=str(session.manifest_v2_path),
            )

    def _emit_sandbox_policy_applied(
        self,
        task_id: str,
        session,
        policy: Dict[str, Any],
    ) -> None:
        integration = getattr(self.context, "event_integration", None)
        if integration and hasattr(integration, "emit_sandbox_policy_applied"):
            integration.emit_sandbox_policy_applied(
                self.phase_number,
                task_id,
                sandbox_id=session.sandbox_id,
                backend=session.backend_name,
                isolation_level=session.isolation_level,
                policy=policy,
            )

    def _emit_sandbox_command_started(
        self,
        task_id: str,
        session,
        command: CommandSpec,
    ) -> None:
        integration = getattr(self.context, "event_integration", None)
        if integration and hasattr(integration, "emit_sandbox_command_started"):
            integration.emit_sandbox_command_started(
                self.phase_number,
                task_id,
                sandbox_id=session.sandbox_id,
                backend=session.backend_name,
                isolation_level=session.isolation_level,
                command=list(command.argv),
                cwd=str(command.cwd),
            )

    def _emit_sandbox_command_completed(
        self,
        task_id: str,
        session,
        command: CommandSpec,
        result: CommandResult,
        cleanup_status: str = "",
        runner_result: Optional[Dict[str, Any]] = None,
    ) -> None:
        integration = getattr(self.context, "event_integration", None)
        if integration and hasattr(integration, "emit_sandbox_command_completed"):
            integration.emit_sandbox_command_completed(
                self.phase_number,
                task_id,
                sandbox_id=session.sandbox_id,
                backend=session.backend_name,
                isolation_level=session.isolation_level,
                command=list(command.argv),
                returncode=result.returncode,
                duration_ms=int(result.duration_ms or 0),
                timed_out=bool(result.timed_out),
                manifest_path=str(session.manifest_v2_path),
                runner_request_path=str(session.runner_request_path),
                runner_result_path=str(session.runner_result_path),
                cleanup_status=cleanup_status,
                error=result.error or str((runner_result or {}).get("error", "")),
            )

    def _emit_sandbox_timeout(
        self,
        task_id: str,
        session,
        command: CommandSpec,
        timeout_seconds: int,
    ) -> None:
        integration = getattr(self.context, "event_integration", None)
        if integration and hasattr(integration, "emit_sandbox_timeout"):
            integration.emit_sandbox_timeout(
                self.phase_number,
                task_id,
                sandbox_id=session.sandbox_id,
                backend=session.backend_name,
                isolation_level=session.isolation_level,
                command=list(command.argv),
                timeout_seconds=timeout_seconds,
                manifest_path=str(session.manifest_v2_path),
            )

    def _emit_sandbox_cleanup_completed(
        self,
        task_id: str,
        session,
        cleanup_status: str,
    ) -> None:
        integration = getattr(self.context, "event_integration", None)
        if integration and hasattr(integration, "emit_sandbox_cleanup_completed"):
            integration.emit_sandbox_cleanup_completed(
                self.phase_number,
                task_id,
                sandbox_id=session.sandbox_id,
                backend=session.backend_name,
                isolation_level=session.isolation_level,
                cleanup_status=cleanup_status,
                manifest_path=str(session.manifest_v2_path),
            )

    def _emit_sandbox_violation(
        self,
        task_id: str,
        session,
        reason: str,
        command: List[str],
    ) -> None:
        integration = getattr(self.context, "event_integration", None)
        if integration and hasattr(integration, "emit_sandbox_violation"):
            integration.emit_sandbox_violation(
                self.phase_number,
                task_id,
                sandbox_id=session.sandbox_id,
                reason=reason,
                command=command,
            )
