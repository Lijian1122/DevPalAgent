# -*- coding: utf-8 -*-
"""Local multi-agent coordinator for OpenSpec file tasks."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, List, Tuple

from devpal.core.openspec_phases.parallel_executor import (
    ParallelTask,
    ParallelTaskResult,
)
from .adapters import agent_result_to_parallel_task_result, parallel_task_to_agent_task
from .content_sanitizer import has_unified_diff_markers
from .backend import LocalThreadBackend
from .codegen_agent import CodegenAgent
from .models import AgentPolicy, AgentResult
from .review_agent import ReviewAgent
from .sandbox import SandboxSession
from .test_agent import TestAgent


class MultiAgentCoordinator:
    def __init__(
        self,
        policy: AgentPolicy,
        client_factory=None,
        log=None,
        event_integration=None,
        test_runner=None,
        review_checker=None,
    ):
        if policy.backend != "local":
            raise ValueError(f"Unsupported multi-agent backend: {policy.backend}")
        self.policy = policy
        self.client_factory = client_factory
        self.log = log
        self.event_integration = event_integration
        self.test_runner = test_runner
        self.review_checker = review_checker
        self._agent_results: Dict[str, AgentResult] = {}
        self.pending_merge_manifests: List[Path] = []
        self.fallback_used = False

    def execute_codegen_tasks(self, tasks: List[ParallelTask]) -> Tuple[List[ParallelTaskResult], Dict[str, object]]:
        return self._backend().execute(tasks, self._run_codegen_task)

    def execute_test_tasks(self, tasks: List[ParallelTask]) -> Tuple[List[ParallelTaskResult], Dict[str, object]]:
        return self._backend().execute(tasks, self._run_test_task)

    def execute_review_tasks(self, tasks: List[ParallelTask]) -> Tuple[List[ParallelTaskResult], Dict[str, object]]:
        return self._backend().execute(tasks, self._run_review_task)

    def _backend(self) -> LocalThreadBackend:
        return LocalThreadBackend(
            max_concurrency=self.policy.max_concurrency,
            retry_limit=self.policy.retry_limit,
            log=self.log,
            event_integration=self.event_integration,
        )

    def merge_successful_results(self, results: List[ParallelTaskResult], project_dir: Path) -> Tuple[List[Path], List[str]]:
        artifacts: List[Path] = []
        errors: List[str] = []
        pending_writes: List[Tuple[Path, str, SandboxSession, Path | None]] = []
        for result in results:
            if not result.success:
                continue
            agent_result = self._agent_results.get(result.task_id)
            if not agent_result:
                errors.append(f"missing agent result for {result.task_id}")
                break
            rel_path = str(agent_result.metadata.get("path") or "")
            content = agent_result.metadata.get("content")
            workspace_artifact = agent_result.metadata.get("workspace_artifact")
            sandbox = SandboxSession(
                project_dir=project_dir,
                task_id=agent_result.task_id,
                phase_number=int(result.metadata.get("phase_number", 4) or 4),
                role="merge",
                sandbox_level=self.policy.sandbox_level,
                allowed_paths=[rel_path],
            )
            try:
                target = sandbox.resolve_target(rel_path)
            except ValueError as exc:
                errors.append(str(exc))
                break
            source_path = Path(workspace_artifact) if workspace_artifact else None
            if source_path and source_path.exists():
                content = source_path.read_text(encoding="utf-8")
            if not isinstance(content, str) or not content:
                errors.append(f"missing generated content for {result.task_id}")
                break
            if has_unified_diff_markers(content):
                errors.append(
                    f"multi-agent output for {rel_path} is a diff/patch, not a complete file"
                )
                break
            pending_writes.append((target, content, sandbox, source_path))
        if errors:
            return artifacts, errors
        if self.policy.sandbox_level == "production":
            for target, content, sandbox, source_path in pending_writes:
                manifest_path = sandbox.write_manifest(
                    [source_path] if source_path else [],
                    status="merge_pending",
                    target_path=str(target),
                    workspace_artifact=str(source_path) if source_path else None,
                    merge_mode="manual",
                    requires_manual_merge=True,
                    content_sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
                )
                self.pending_merge_manifests.append(manifest_path)
                self._emit_agent_merge_completed(
                    sandbox,
                    target,
                    success=False,
                    error="production sandbox requires manual merge",
                )
            return artifacts, errors
        for target, content, sandbox, source_path in pending_writes:
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                artifacts.append(target)
                sandbox.write_manifest(
                    [target],
                    status="merged",
                    target_path=str(target),
                    workspace_artifact=str(source_path) if source_path else None,
                    merge_mode=self.policy.sandbox_level,
                )
                self._emit_agent_merge_completed(sandbox, target, success=True)
            except Exception as exc:
                errors.append(str(exc))
                break
        return artifacts, errors

    def _emit_agent_merge_completed(
        self,
        sandbox: SandboxSession,
        target: Path,
        success: bool,
        error: str = "",
    ) -> None:
        if self.event_integration and hasattr(self.event_integration, "emit_agent_merge_completed"):
            self.event_integration.emit_agent_merge_completed(
                sandbox.phase_number,
                sandbox.task_id,
                sandbox_id=sandbox.sandbox_id,
                artifact_path=str(target),
                success=success,
                error=error,
            )

    def _run_codegen_task(self, task: ParallelTask) -> ParallelTaskResult:
        item = task.input_payload["plan_item"]
        agent_task = parallel_task_to_agent_task(
            task,
            self.policy,
            role="codegen",
            allowed_paths=[item.path],
        )
        self._emit_agent_started(task, "codegen")
        result = CodegenAgent(self.client_factory, self.policy).execute(agent_task)
        self._emit_agent_completed(task, "codegen", result)
        self._emit_policy_violations(task, result)
        self._agent_results[task.task_id] = result
        parallel_result = agent_result_to_parallel_task_result(result)
        parallel_result.metadata["phase_number"] = task.phase_number
        return parallel_result

    def _run_test_task(self, task: ParallelTask) -> ParallelTaskResult:
        agent_task = parallel_task_to_agent_task(
            task,
            self.policy,
            role="test",
        )
        self._emit_agent_started(task, "test")
        result = TestAgent(self.policy, runner=self.test_runner).execute(agent_task)
        self._emit_agent_completed(task, "test", result)
        self._emit_policy_violations(task, result)
        self._agent_results[task.task_id] = result
        parallel_result = agent_result_to_parallel_task_result(result)
        parallel_result.metadata["phase_number"] = task.phase_number
        return parallel_result

    def _run_review_task(self, task: ParallelTask) -> ParallelTaskResult:
        if self.review_checker is None:
            raise ValueError("review_checker is required for review tasks")
        agent_task = parallel_task_to_agent_task(
            task,
            self.policy,
            role="review",
        )
        self._emit_agent_started(task, "review")
        result = ReviewAgent(self.policy, checker=self.review_checker).execute(agent_task)
        self._emit_agent_completed(task, "review", result)
        self._emit_policy_violations(task, result)
        self._agent_results[task.task_id] = result
        parallel_result = agent_result_to_parallel_task_result(result)
        parallel_result.metadata["phase_number"] = task.phase_number
        return parallel_result

    def _emit_agent_started(self, task: ParallelTask, role: str) -> None:
        if self.event_integration and hasattr(self.event_integration, "emit_agent_started"):
            self.event_integration.emit_agent_started(
                task.phase_number,
                task.task_id,
                role,
                task.task_type,
            )

    def _emit_agent_completed(self, task: ParallelTask, role: str, result: AgentResult) -> None:
        if self.event_integration and hasattr(self.event_integration, "emit_agent_completed"):
            self.event_integration.emit_agent_completed(
                task.phase_number,
                task.task_id,
                role,
                task.task_type,
                sandbox_id=result.sandbox_id,
                success=result.success,
                duration_ms=result.duration_ms,
                error=result.error or "",
            )

    def _emit_policy_violations(self, task: ParallelTask, result: AgentResult) -> None:
        if not self.event_integration or not hasattr(self.event_integration, "emit_sandbox_violation"):
            return
        for violation in result.policy_violations:
            self.event_integration.emit_sandbox_violation(
                task.phase_number,
                task.task_id,
                sandbox_id=result.sandbox_id,
                reason=str(violation.get("reason", "")),
                path=str(violation.get("path", "")),
                command=list(violation.get("argv", []) or []),
            )
