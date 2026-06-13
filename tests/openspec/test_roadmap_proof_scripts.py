# -*- coding: utf-8 -*-

from scripts.benchmark_parallel_executor import benchmark, render_markdown as render_benchmark
from scripts.evaluate_vector_retrieval import evaluate, render_markdown as render_vector_eval


def test_parallel_benchmark_result_shape():
    result = benchmark(task_count=4, task_delay_ms=1, max_concurrency=2)
    data = result.to_dict()

    assert data["task_count"] == 4
    assert data["max_concurrency"] == 2
    assert data["serial_ms"] >= 0
    assert data["parallel_ms"] >= 0
    assert "speedup" in data
    assert "Parallel Executor Benchmark" in render_benchmark(result)


def test_vector_retrieval_smoke_result_shape():
    result = evaluate()
    data = result.to_dict()

    assert data["total_cases"] == 3
    assert data["hits"] == data["total_cases"]
    assert data["recall_at_k"] == 1.0
    assert len(data["cases"]) == 3
    assert all(row["hit"] for row in data["cases"])
    assert all("result_ids" in row for row in data["cases"])
    assert "Vector Retrieval Smoke Evaluation" in render_vector_eval(result)
