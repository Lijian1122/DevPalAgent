# -*- coding: utf-8 -*-
"""Bounded parallel execution helpers for OpenSpec phases."""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ParallelTask:
    task_id: str
    phase_number: int
    task_type: str
    input_payload: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParallelTaskResult:
    task_id: str
    success: bool
    artifact_path: Optional[Path] = None
    duration_ms: int = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "success": self.success,
            "artifact_path": self.artifact_path.as_posix() if self.artifact_path else None,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "metadata": dict(self.metadata),
        }


TaskHandler = Callable[[ParallelTask], ParallelTaskResult]
LogHandler = Callable[[str], None]


class PhaseParallelExecutor:
    def __init__(
        self,
        max_concurrency: int = 3,
        retry_limit: int = 1,
        serial_fallback: bool = True,
        log: Optional[LogHandler] = None,
        event_integration: Any = None,
    ):
        self.max_concurrency = max(1, int(max_concurrency or 1))
        self.retry_limit = max(0, int(retry_limit or 0))
        self.serial_fallback = serial_fallback
        self.log = log
        self.event_integration = event_integration
        self.fallback_used = False

    def execute(self, tasks: List[ParallelTask], handler: TaskHandler) -> List[ParallelTaskResult]:
        self.fallback_used = False
        if not tasks:
            return []
        if self.max_concurrency == 1 or len(tasks) == 1:
            return self._execute_serial(tasks, handler)
        try:
            if any(task.dependencies for task in tasks):
                return self._execute_by_dependency_stage(tasks, handler)
            return self._execute_parallel(tasks, handler)
        except Exception as exc:
            if not self.serial_fallback:
                raise
            self.fallback_used = True
            self._log(f"[PHASE-PARALLEL] falling back to serial execution: {exc}")
            return self._execute_serial(tasks, handler)

    def aggregate(self, results: List[ParallelTaskResult]) -> Dict[str, Any]:
        total = len(results)
        success_count = sum(1 for result in results if result.success)
        failed_count = total - success_count
        retry_count = sum(int(result.metadata.get("retry_attempts", 0)) for result in results)
        total_duration_ms = sum(result.duration_ms for result in results)
        return {
            "total_tasks": total,
            "success_count": success_count,
            "failed_count": failed_count,
            "retry_count": retry_count,
            "max_concurrency": self.max_concurrency,
            "fallback_used": self.fallback_used,
            "total_task_duration_ms": total_duration_ms,
            "results": [result.to_dict() for result in results],
        }

    def _execute_parallel(self, tasks: List[ParallelTask], handler: TaskHandler) -> List[ParallelTaskResult]:
        results_by_id: Dict[str, ParallelTaskResult] = {}
        with ThreadPoolExecutor(max_workers=min(self.max_concurrency, len(tasks))) as executor:
            futures = {executor.submit(self._run_one, task, handler): task for task in tasks}
            for future in as_completed(futures):
                task = futures[future]
                results_by_id[task.task_id] = future.result()
        return [results_by_id[task.task_id] for task in tasks]

    def _execute_serial(self, tasks: List[ParallelTask], handler: TaskHandler) -> List[ParallelTaskResult]:
        return [self._run_one(task, handler) for task in tasks]

    def _execute_by_dependency_stage(self, tasks: List[ParallelTask], handler: TaskHandler) -> List[ParallelTaskResult]:
        task_ids = {task.task_id for task in tasks}
        missing_dependencies = sorted(
            {dep for task in tasks for dep in task.dependencies if dep not in task_ids}
        )
        if missing_dependencies:
            raise ValueError(
                "Unknown parallel task dependencies: " + ", ".join(missing_dependencies)
            )

        pending = {task.task_id: task for task in tasks}
        successful = set()
        completed = set()
        results_by_id: Dict[str, ParallelTaskResult] = {}

        while pending:
            blocked = [
                task
                for task in pending.values()
                if any(dep in completed and dep not in successful for dep in task.dependencies)
            ]
            for task in blocked:
                failed_deps = [dep for dep in task.dependencies if dep in completed and dep not in successful]
                thread_id = threading.get_ident()
                thread_name = threading.current_thread().name
                result = ParallelTaskResult(
                    task_id=task.task_id,
                    success=False,
                    error="Skipped because dependencies failed: " + ", ".join(failed_deps),
                    metadata={
                        "failed_dependencies": failed_deps,
                        "thread_id": thread_id,
                        "thread_name": thread_name,
                    },
                )
                self._log(
                    f"[PHASE-PARALLEL] skip {task.task_id} type={task.task_type} "
                    f"thread={thread_name}/{thread_id} failed_deps={','.join(failed_deps)}"
                )
                results_by_id[task.task_id] = result
                completed.add(task.task_id)
                pending.pop(task.task_id, None)

            if not pending:
                break

            ready = [
                task
                for task in pending.values()
                if all(dep in successful for dep in task.dependencies)
            ]
            if not ready:
                unresolved = ", ".join(sorted(pending))
                raise ValueError(f"Unresolvable parallel task dependencies: {unresolved}")

            stage_results = self._execute_parallel(ready, handler) if len(ready) > 1 else self._execute_serial(ready, handler)
            for result in stage_results:
                results_by_id[result.task_id] = result
                completed.add(result.task_id)
                if result.success:
                    successful.add(result.task_id)
                pending.pop(result.task_id, None)

        return [results_by_id[task.task_id] for task in tasks]

    def _run_one(self, task: ParallelTask, handler: TaskHandler) -> ParallelTaskResult:
        attempts = max(self.retry_limit, task.retry_count) + 1
        last_result: Optional[ParallelTaskResult] = None
        for attempt in range(attempts):
            start = time.time()
            thread_id = threading.get_ident()
            thread_name = threading.current_thread().name
            try:
                self._log(
                    f"[PHASE-PARALLEL] start {task.task_id} type={task.task_type} "
                    f"attempt={attempt + 1}/{attempts} thread={thread_name}/{thread_id}"
                )
                self._emit_file_task_started(task, attempt)
                result = handler(task)
                result.duration_ms = int((time.time() - start) * 1000)
                result.metadata["retry_attempts"] = attempt
                result.metadata["thread_id"] = thread_id
                result.metadata["thread_name"] = thread_name
                if result.success or attempt == attempts - 1:
                    self._log(
                        f"[PHASE-PARALLEL] done {task.task_id} type={task.task_type} "
                        f"success={result.success} duration_ms={result.duration_ms} "
                        f"thread={thread_name}/{thread_id}"
                    )
                    if result.success:
                        self._emit_file_task_completed(task, result)
                    else:
                        self._emit_file_task_failed(task, result)
                    return result
                last_result = result
                self._emit_file_task_retrying(task, attempt, result.error or "task returned failure")
            except Exception as exc:
                last_result = ParallelTaskResult(
                    task_id=task.task_id,
                    success=False,
                    duration_ms=int((time.time() - start) * 1000),
                    error=str(exc),
                    metadata={
                        "retry_attempts": attempt,
                        "thread_id": thread_id,
                        "thread_name": thread_name,
                    },
                )
                if attempt == attempts - 1:
                    self._log(
                        f"[PHASE-PARALLEL] failed {task.task_id} type={task.task_type} "
                        f"duration_ms={last_result.duration_ms} thread={thread_name}/{thread_id}: {exc}"
                    )
                    self._emit_file_task_failed(task, last_result)
                    return last_result
                self._emit_file_task_retrying(task, attempt, str(exc))
        return last_result or ParallelTaskResult(task_id=task.task_id, success=False, error="unknown parallel task failure")

    def _task_path(self, task: ParallelTask) -> str:
        payload = task.input_payload or {}
        for key in ("doc_file", "test_file"):
            if key in payload and payload[key]:
                return str(payload[key])
        plan_item = payload.get("plan_item")
        if plan_item is not None and hasattr(plan_item, "path"):
            return str(plan_item.path)
        return str(task.metadata.get("path", ""))

    def _emit_file_task_started(self, task: ParallelTask, attempt: int) -> None:
        if self.event_integration:
            self.event_integration.emit_file_task_started(
                task.phase_number,
                task.task_id,
                task.task_type,
                path=self._task_path(task),
                retry_count=attempt,
            )

    def _emit_file_task_completed(self, task: ParallelTask, result: ParallelTaskResult) -> None:
        if self.event_integration:
            self.event_integration.emit_file_task_completed(
                task.phase_number,
                task.task_id,
                task.task_type,
                path=str(result.artifact_path or self._task_path(task)),
                duration_ms=result.duration_ms,
                retry_count=int(result.metadata.get("retry_attempts", 0) or 0),
            )

    def _emit_file_task_failed(self, task: ParallelTask, result: ParallelTaskResult) -> None:
        if self.event_integration:
            self.event_integration.emit_file_task_failed(
                task.phase_number,
                task.task_id,
                task.task_type,
                path=self._task_path(task),
                duration_ms=result.duration_ms,
                retry_count=int(result.metadata.get("retry_attempts", 0) or 0),
                error=result.error or "",
            )

    def _emit_file_task_retrying(self, task: ParallelTask, attempt: int, error: str) -> None:
        if self.event_integration:
            self.event_integration.emit_file_task_retrying(
                task.phase_number,
                task.task_id,
                task.task_type,
                path=self._task_path(task),
                retry_count=attempt + 1,
                error=error,
            )

    def _log(self, message: str) -> None:
        if self.log:
            self.log(message)
