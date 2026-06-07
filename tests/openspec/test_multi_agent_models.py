# -*- coding: utf-8 -*-

from pathlib import Path

from devpal.core.multi_agent import (
    AgentPolicy,
    AgentResult,
    agent_result_to_parallel_task_result,
    parallel_task_to_agent_task,
)
from devpal.core.openspec_phases.parallel_executor import ParallelTask


def test_parallel_task_converts_to_agent_task_without_losing_fields():
    task = ParallelTask(
        task_id="phase4:src/app.py",
        phase_number=4,
        task_type="code_file",
        input_payload={"path": "src/app.py"},
        dependencies=["phase4:include/app.h"],
        metadata={"priority": "high"},
    )
    policy = AgentPolicy(
        enabled=True,
        allowed_write_paths=["src/app.py"],
        allowed_tools=["write_file"],
        timeout_seconds=99,
        token_budget=1234,
    )

    agent_task = parallel_task_to_agent_task(task, policy)

    assert agent_task.task_id == task.task_id
    assert agent_task.phase_number == 4
    assert agent_task.role == "codegen"
    assert agent_task.task_type == "code_file"
    assert agent_task.input_payload == {"path": "src/app.py"}
    assert agent_task.dependencies == ["phase4:include/app.h"]
    assert agent_task.allowed_paths == ["src/app.py"]
    assert agent_task.allowed_tools == ["write_file"]
    assert agent_task.timeout_seconds == 99
    assert agent_task.token_budget == 1234
    assert agent_task.metadata == {"priority": "high"}


def test_agent_result_converts_to_parallel_task_result():
    artifact = Path("src/app.py")
    result = AgentResult(
        task_id="phase4:src/app.py",
        success=True,
        artifact_path=artifact,
        duration_ms=10,
        sandbox_id="sandbox-1",
        metadata={"path": "src/app.py", "llm_calls": 1},
    )

    parallel_result = agent_result_to_parallel_task_result(result)

    assert parallel_result.task_id == result.task_id
    assert parallel_result.success is True
    assert parallel_result.artifact_path == artifact
    assert parallel_result.duration_ms == 10
    assert parallel_result.metadata["sandbox_id"] == "sandbox-1"
    assert parallel_result.metadata["llm_calls"] == 1


def test_agent_policy_defaults_to_local_backend():
    policy = AgentPolicy()

    assert policy.backend == "local"
    assert policy.backend_options == {}


def test_failed_agent_result_converts_to_failed_parallel_result():
    result = AgentResult(
        task_id="phase4:src/app.py",
        success=False,
        error="boom",
        sandbox_id="sandbox-1",
        policy_violations=[{"reason": "denied"}],
    )

    parallel_result = agent_result_to_parallel_task_result(result)

    assert parallel_result.success is False
    assert parallel_result.error == "boom"
    assert parallel_result.metadata["policy_violations"] == [{"reason": "denied"}]
