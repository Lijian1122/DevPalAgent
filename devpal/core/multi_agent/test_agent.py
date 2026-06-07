# -*- coding: utf-8 -*-
"""Deterministic test execution agent for OpenSpec Phase 10."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Callable, List, Optional

from .models import AgentPolicy, AgentResult, AgentTask, CommandResult, CommandSpec
from .sandbox import SandboxSession

Runner = Callable[[CommandSpec], CommandResult]


class TestAgent:
    __test__ = False

    def __init__(self, policy: AgentPolicy, runner: Optional[Runner] = None):
        self.policy = policy
        self.runner = runner or self._default_runner

    def execute(self, task: AgentTask) -> AgentResult:
        start = time.time()
        project_dir = Path(task.input_payload["project_dir"])
        sandbox = SandboxSession(
            project_dir=project_dir,
            task_id=task.task_id,
            phase_number=task.phase_number,
            role=task.role,
            sandbox_level=self.policy.sandbox_level,
        )
        commands = task.input_payload.get("commands") or []
        command_results: List[CommandResult] = []
        policy_violations = []

        for command in commands:
            try:
                sandbox.validate_command(command)
            except ValueError as exc:
                violation = {"reason": str(exc), "argv": getattr(command, "argv", [])}
                policy_violations.append(violation)
                metadata = self._metadata(task, sandbox, command_results)
                manifest_path = sandbox.write_manifest(
                    [],
                    status="policy_violation",
                    policy_violations=policy_violations,
                )
                metadata["manifest_path"] = str(manifest_path)
                return AgentResult(
                    task_id=task.task_id,
                    success=False,
                    duration_ms=int((time.time() - start) * 1000),
                    error=str(exc),
                    sandbox_id=sandbox.sandbox_id,
                    policy_violations=policy_violations,
                    metadata=metadata,
                )

            result = self.runner(command)
            command_results.append(result)
            if result.timed_out or result.error or result.returncode != 0:
                metadata = self._metadata(task, sandbox, command_results)
                manifest_path = sandbox.write_manifest(
                    [],
                    status="failed",
                    commands=metadata["commands"],
                    error=result.error or result.stderr or f"command failed: {result.returncode}",
                )
                metadata["manifest_path"] = str(manifest_path)
                return AgentResult(
                    task_id=task.task_id,
                    success=False,
                    duration_ms=int((time.time() - start) * 1000),
                    error=result.error or result.stderr or f"command failed: {result.returncode}",
                    sandbox_id=sandbox.sandbox_id,
                    metadata=metadata,
                )

        metadata = self._metadata(task, sandbox, command_results)
        manifest_path = sandbox.write_manifest(
            [],
            status="completed",
            commands=metadata["commands"],
        )
        metadata["manifest_path"] = str(manifest_path)
        return AgentResult(
            task_id=task.task_id,
            success=True,
            duration_ms=int((time.time() - start) * 1000),
            sandbox_id=sandbox.sandbox_id,
            metadata=metadata,
        )

    def _metadata(
        self,
        task: AgentTask,
        sandbox: SandboxSession,
        command_results: List[CommandResult],
    ) -> dict:
        stdout = "\n".join(result.stdout for result in command_results if result.stdout)
        stderr = "\n".join(result.stderr for result in command_results if result.stderr)
        output = stdout + ("\n" + stderr if stderr else "")
        return {
            "language": task.input_payload.get("language"),
            "test_files": list(task.input_payload.get("test_files") or []),
            "stdout": stdout,
            "stderr": stderr,
            "output": output,
            "commands": [
                {
                    "argv": list(result.argv),
                    "cwd": str(result.cwd),
                    "returncode": result.returncode,
                    "duration_ms": result.duration_ms,
                    "timed_out": result.timed_out,
                    "error": result.error,
                }
                for result in command_results
            ],
            "sandbox": sandbox.manifest(),
        }

    def _default_runner(self, command: CommandSpec) -> CommandResult:
        start = time.time()
        try:
            completed = subprocess.run(
                command.argv,
                cwd=command.cwd,
                capture_output=command.capture_output,
                text=command.text,
                timeout=command.timeout_seconds,
                env=command.env,
                encoding=command.encoding,
                errors=command.errors,
            )
            return CommandResult(
                argv=list(command.argv),
                cwd=command.cwd,
                returncode=completed.returncode,
                stdout=completed.stdout or "",
                stderr=completed.stderr or "",
                duration_ms=int((time.time() - start) * 1000),
            )
        except subprocess.TimeoutExpired as exc:
            return CommandResult(
                argv=list(command.argv),
                cwd=command.cwd,
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
                duration_ms=int((time.time() - start) * 1000),
                timed_out=True,
                error=f"timeout after {command.timeout_seconds}s",
            )
        except Exception as exc:
            return CommandResult(
                argv=list(command.argv),
                cwd=command.cwd,
                duration_ms=int((time.time() - start) * 1000),
                error=str(exc),
            )
