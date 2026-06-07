# -*- coding: utf-8 -*-
"""Adapters between OpenSpec parallel tasks and multi-agent tasks."""

from __future__ import annotations

from .models import AgentPolicy, AgentResult, AgentTask
from devpal.core.openspec_phases.parallel_executor import ParallelTask, ParallelTaskResult


def parallel_task_to_agent_task(
    task: ParallelTask,
    policy: AgentPolicy,
    role: str = "codegen",
    allowed_paths: list[str] | None = None,
) -> AgentTask:
    return AgentTask(
        task_id=task.task_id,
        phase_number=task.phase_number,
        role=role,
        task_type=task.task_type,
        input_payload=dict(task.input_payload),
        dependencies=list(task.dependencies),
        allowed_paths=list(allowed_paths or policy.allowed_write_paths),
        allowed_tools=list(policy.allowed_tools),
        timeout_seconds=policy.timeout_seconds,
        token_budget=policy.token_budget,
        metadata=dict(task.metadata),
    )


def agent_result_to_parallel_task_result(result: AgentResult) -> ParallelTaskResult:
    metadata = dict(result.metadata)
    metadata["sandbox_id"] = result.sandbox_id
    if result.policy_violations:
        metadata["policy_violations"] = result.policy_violations
    return ParallelTaskResult(
        task_id=result.task_id,
        success=result.success,
        artifact_path=result.artifact_path,
        duration_ms=result.duration_ms,
        error=result.error,
        metadata=metadata,
    )
