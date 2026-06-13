# -*- coding: utf-8 -*-
"""Deterministic vector retrieval smoke evaluation."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from devpal.vector_store.documents import VectorDocument
from devpal.vector_store.vector_db import InMemoryVectorStore


@dataclass
class RetrievalCase:
    query: str
    expected_id: str
    top_k: int = 3


@dataclass
class RetrievalEvalResult:
    total_cases: int
    hits: int
    recall_at_k: float
    cases: list[dict]

    def to_dict(self) -> dict:
        return asdict(self)


def fixture_documents() -> list[VectorDocument]:
    return [
        VectorDocument(
            id="requirements:login",
            content="Login requirements validate username and password and return an error message on failure",
            metadata={"project_name": "vector_eval", "artifact_type": "requirements"},
        ),
        VectorDocument(
            id="source:auth_service",
            content="AuthService validates username and password credentials for login requests",
            metadata={"project_name": "vector_eval", "artifact_type": "source"},
        ),
        VectorDocument(
            id="test:auth_service",
            content="test_login_rejects_invalid_password verifies credential validation failures",
            metadata={"project_name": "vector_eval", "artifact_type": "test"},
        ),
        VectorDocument(
            id="docs:final_report",
            content="Final report summarizes login requirements, generated auth service, and tests",
            metadata={"project_name": "vector_eval", "artifact_type": "report"},
        ),
    ]


def default_cases() -> list[RetrievalCase]:
    docs = {doc.id: doc.content for doc in fixture_documents()}
    return [
        RetrievalCase(docs["source:auth_service"], "source:auth_service"),
        RetrievalCase(docs["test:auth_service"], "test:auth_service"),
        RetrievalCase(docs["requirements:login"], "requirements:login"),
    ]


def evaluate(cases: list[RetrievalCase] | None = None) -> RetrievalEvalResult:
    store = InMemoryVectorStore()
    store.upsert(fixture_documents())
    cases = cases or default_cases()
    rows = []
    hits = 0
    for case in cases:
        results = store.search(case.query, top_k=case.top_k, filters={"project_name": "vector_eval"})
        result_ids = [doc.id for doc in results]
        hit = case.expected_id in result_ids
        hits += int(hit)
        rows.append({
            "query": case.query,
            "expected_id": case.expected_id,
            "top_k": case.top_k,
            "result_ids": result_ids,
            "hit": hit,
        })
    recall = hits / len(cases) if cases else 0.0
    return RetrievalEvalResult(
        total_cases=len(cases),
        hits=hits,
        recall_at_k=round(recall, 3),
        cases=rows,
    )


def render_markdown(result: RetrievalEvalResult) -> str:
    lines = [
        "# Vector Retrieval Smoke Evaluation",
        "",
        f"- Cases: {result.total_cases}",
        f"- Hits: {result.hits}",
        f"- Recall@k: {result.recall_at_k}",
        "",
        "| Query | Expected | Hit | Results |",
        "|-------|----------|-----|---------|",
    ]
    for row in result.cases:
        lines.append(
            "| {} | `{}` | {} | `{}` |".format(
                row["query"],
                row["expected_id"],
                row["hit"],
                ", ".join(row["result_ids"]),
            )
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate deterministic vector retrieval smoke cases")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = evaluate()
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(render_markdown(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
