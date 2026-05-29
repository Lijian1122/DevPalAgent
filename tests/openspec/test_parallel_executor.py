from devpal.core.openspec_phases.parallel_executor import (
    ParallelTask,
    ParallelTaskResult,
    PhaseParallelExecutor,
)


def _task(task_id, dependencies=None):
    return ParallelTask(
        task_id=task_id,
        phase_number=5,
        task_type="unit",
        input_payload={},
        dependencies=dependencies or [],
    )


def test_parallel_executor_preserves_input_order():
    tasks = [_task("b"), _task("a"), _task("c")]
    executor = PhaseParallelExecutor(max_concurrency=3)

    results = executor.execute(
        tasks,
        lambda task: ParallelTaskResult(task_id=task.task_id, success=True),
    )

    assert [result.task_id for result in results] == ["b", "a", "c"]
    assert executor.aggregate(results)["max_concurrency"] == 3


def test_parallel_executor_isolates_failed_task():
    tasks = [_task("ok-1"), _task("bad"), _task("ok-2")]
    executor = PhaseParallelExecutor(max_concurrency=3, retry_limit=0)

    def handler(task):
        if task.task_id == "bad":
            return ParallelTaskResult(task_id=task.task_id, success=False, error="boom")
        return ParallelTaskResult(task_id=task.task_id, success=True)

    results = executor.execute(tasks, handler)
    summary = executor.aggregate(results)

    assert [result.success for result in results] == [True, False, True]
    assert summary["success_count"] == 2
    assert summary["failed_count"] == 1


def test_parallel_executor_retries_failed_result():
    task = _task("flaky")
    executor = PhaseParallelExecutor(max_concurrency=1, retry_limit=1)
    calls = {"count": 0}

    def handler(task):
        calls["count"] += 1
        if calls["count"] == 1:
            return ParallelTaskResult(task_id=task.task_id, success=False, error="temporary")
        return ParallelTaskResult(task_id=task.task_id, success=True)

    result = executor.execute([task], handler)[0]

    assert result.success is True
    assert result.metadata["retry_attempts"] == 1
    assert calls["count"] == 2


def test_parallel_executor_serial_fallback_on_dependency_error():
    tasks = [_task("independent"), _task("dependent", dependencies=["missing"])]
    executor = PhaseParallelExecutor(max_concurrency=2, serial_fallback=True)

    results = executor.execute(
        tasks,
        lambda task: ParallelTaskResult(task_id=task.task_id, success=True),
    )

    assert len(results) == 2
    assert [result.success for result in results] == [True, True]
    assert executor.aggregate(results)["fallback_used"] is True


def test_parallel_executor_dependency_stage_skips_failed_dependents():
    tasks = [_task("header"), _task("impl", dependencies=["header"])]
    executor = PhaseParallelExecutor(max_concurrency=2, retry_limit=0)

    def handler(task):
        if task.task_id == "header":
            return ParallelTaskResult(task_id=task.task_id, success=False, error="compile")
        return ParallelTaskResult(task_id=task.task_id, success=True)

    results = executor.execute(tasks, handler)

    assert results[0].success is False
    assert results[1].success is False
    assert "dependencies failed" in results[1].error
