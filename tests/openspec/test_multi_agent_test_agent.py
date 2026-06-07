# -*- coding: utf-8 -*-

from pathlib import Path

from devpal.core.multi_agent import AgentPolicy, AgentTask, CommandResult, CommandSpec, TestAgent


def _task(tmp_path, command):
    return AgentTask(
        task_id="phase10:python:pytest",
        phase_number=10,
        role="test",
        task_type="test_run",
        input_payload={
            "project_dir": tmp_path,
            "language": "python",
            "test_files": ["tests/test_main.py"],
            "commands": [command],
        },
    )


def test_test_agent_returns_success_with_command_output(tmp_path):
    command = CommandSpec(argv=["pytest", "tests", "-v"], cwd=tmp_path)

    def runner(command):
        return CommandResult(
            argv=command.argv,
            cwd=command.cwd,
            returncode=0,
            stdout="passed",
            stderr="",
        )

    result = TestAgent(AgentPolicy(enabled=True), runner=runner).execute(_task(tmp_path, command))

    assert result.success is True
    assert result.metadata["stdout"] == "passed"
    assert result.metadata["output"] == "passed"
    assert result.metadata["commands"][0]["returncode"] == 0
    assert Path(result.metadata["manifest_path"]).exists()


def test_test_agent_returns_failure_for_nonzero_command(tmp_path):
    command = CommandSpec(argv=["pytest", "tests", "-v"], cwd=tmp_path)

    def runner(command):
        return CommandResult(
            argv=command.argv,
            cwd=command.cwd,
            returncode=1,
            stdout="",
            stderr="failed",
        )

    result = TestAgent(AgentPolicy(enabled=True), runner=runner).execute(_task(tmp_path, command))

    assert result.success is False
    assert result.error == "failed"
    assert result.metadata["stderr"] == "failed"


def test_test_agent_returns_failure_for_timeout(tmp_path):
    command = CommandSpec(argv=["pytest", "tests", "-v"], cwd=tmp_path)

    def runner(command):
        return CommandResult(
            argv=command.argv,
            cwd=command.cwd,
            timed_out=True,
            error="timeout after 300s",
        )

    result = TestAgent(AgentPolicy(enabled=True), runner=runner).execute(_task(tmp_path, command))

    assert result.success is False
    assert result.error == "timeout after 300s"
    assert result.metadata["commands"][0]["timed_out"] is True


def test_test_agent_fails_closed_on_policy_violation(tmp_path):
    command = CommandSpec(argv=["curl", "https://example.com"], cwd=tmp_path)
    calls = {"count": 0}

    def runner(command):
        calls["count"] += 1
        return CommandResult(argv=command.argv, cwd=command.cwd, returncode=0)

    result = TestAgent(AgentPolicy(enabled=True), runner=runner).execute(_task(tmp_path, command))

    assert result.success is False
    assert result.policy_violations
    assert Path(result.metadata["manifest_path"]).exists()
    assert calls["count"] == 0
