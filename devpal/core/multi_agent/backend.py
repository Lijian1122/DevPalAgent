# -*- coding: utf-8 -*-
"""Execution backend seam for multi-agent tasks."""

from __future__ import annotations

from typing import Callable, List, Tuple

from devpal.core.openspec_phases.parallel_executor import (
    ParallelTask,
    ParallelTaskResult,
    PhaseParallelExecutor,
)


class LocalThreadBackend:
    name = "local"

    def __init__(self, max_concurrency: int, retry_limit: int = 0, log=None, event_integration=None):
        self.executor = PhaseParallelExecutor(
            max_concurrency=max_concurrency,
            retry_limit=retry_limit,
            serial_fallback=False,
            log=log,
            event_integration=event_integration,
        )

    def execute(
        self,
        tasks: List[ParallelTask],
        handler: Callable[[ParallelTask], ParallelTaskResult],
    ) -> Tuple[List[ParallelTaskResult], dict]:
        results = self.executor.execute(tasks, handler)
        return results, self.executor.aggregate(results)
