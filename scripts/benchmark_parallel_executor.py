# -*- coding: utf-8 -*-
"""Small deterministic benchmark for PhaseParallelExecutor."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from devpal.core.openspec_phases.parallel_executor import (
    ParallelTask,
    ParallelTaskResult,
    PhaseParallelExecutor,
)


@dataclass
class BenchmarkResult:
    task_count: int
    task_delay_ms: int
    serial_ms: int
    parallel_ms: int
    max_concurrency: int

    @property
    def speedup(self) -> float:
        if self.parallel_ms <= 0:
            return 0.0
        return self.serial_ms / self.parallel_ms

    def to_dict(self) -> dict:
        data = asdict(self)
        data["speedup"] = round(self.speedup, 2)
        return data


def _tasks(task_count: int) -> list[ParallelTask]:
    return [
        ParallelTask(
            task_id=f"bench:{index}",
            phase_number=4,
            task_type="benchmark",
            input_payload={"index": index},
        )
        for index in range(task_count)
    ]


def run_once(task_count: int, task_delay_ms: int, max_concurrency: int) -> int:
    def handler(task: ParallelTask) -> ParallelTaskResult:
        time.sleep(task_delay_ms / 1000.0)
        return ParallelTaskResult(task_id=task.task_id, success=True)

    executor = PhaseParallelExecutor(max_concurrency=max_concurrency, retry_limit=0, serial_fallback=False)
    start = time.perf_counter()
    executor.execute(_tasks(task_count), handler)
    return int((time.perf_counter() - start) * 1000)


def benchmark(task_count: int = 8, task_delay_ms: int = 25, max_concurrency: int = 4) -> BenchmarkResult:
    serial_ms = run_once(task_count, task_delay_ms, max_concurrency=1)
    parallel_ms = run_once(task_count, task_delay_ms, max_concurrency=max_concurrency)
    return BenchmarkResult(
        task_count=task_count,
        task_delay_ms=task_delay_ms,
        serial_ms=serial_ms,
        parallel_ms=parallel_ms,
        max_concurrency=max_concurrency,
    )


def render_markdown(result: BenchmarkResult) -> str:
    data = result.to_dict()
    return "\n".join([
        "# Parallel Executor Benchmark",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Task count | {data['task_count']} |",
        f"| Task delay | {data['task_delay_ms']} ms |",
        f"| Serial duration | {data['serial_ms']} ms |",
        f"| Parallel duration | {data['parallel_ms']} ms |",
        f"| Max concurrency | {data['max_concurrency']} |",
        f"| Observed speedup | {data['speedup']}x |",
        "",
    ])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark DevPalAgent phase parallel execution")
    parser.add_argument("--tasks", type=int, default=8)
    parser.add_argument("--delay-ms", type=int, default=25)
    parser.add_argument("--max-concurrency", type=int, default=4)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output", help="Optional markdown output path")
    args = parser.parse_args(argv)

    result = benchmark(args.tasks, args.delay_ms, args.max_concurrency)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_markdown(result), encoding="utf-8")
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(render_markdown(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
