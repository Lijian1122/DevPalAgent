# -*- coding: utf-8 -*-

import pytest

from devpal.core.multi_agent import AgentPolicy, LocalThreadBackend, MultiAgentCoordinator
from devpal.core.openspec_phases.parallel_executor import ParallelTask, ParallelTaskResult


def _task(task_id):
    return ParallelTask(task_id=task_id, phase_number=4, task_type="unit", input_payload={})


def test_local_thread_backend_preserves_parallel_summary_shape():
    backend = LocalThreadBackend(max_concurrency=2)

    results, summary = backend.execute(
        [_task("a"), _task("b")],
        lambda task: ParallelTaskResult(task_id=task.task_id, success=True),
    )

    assert [result.task_id for result in results] == ["a", "b"]
    assert summary["total_tasks"] == 2
    assert summary["success_count"] == 2
    assert summary["failed_count"] == 0
    assert summary["max_concurrency"] == 2
    assert "results" in summary


def test_coordinator_rejects_unsupported_backend():
    with pytest.raises(ValueError, match="Unsupported multi-agent backend"):
        MultiAgentCoordinator(AgentPolicy(backend="remote_queue"))
