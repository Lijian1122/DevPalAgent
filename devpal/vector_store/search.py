# -*- coding: utf-8 -*-
"""CLI entrypoint for searching indexed project artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .semantic_search import SemanticSearchService


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Search DevPal semantic artifact index")
    parser.add_argument("query", help="Natural language search query")
    parser.add_argument("--project-dir", default=".", help="Project directory (default: current directory)")
    parser.add_argument("--project-name", help="Project name metadata filter")
    parser.add_argument("--artifact-type", action="append", dest="artifact_types", help="Artifact type filter; may be repeated")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results to return")
    parser.add_argument("--persist-dir", help="Vector store directory (default: <project>/.spec/vector_store)")
    parser.add_argument("--no-chroma", action="store_true", help="Use in-memory vector store instead of ChromaDB")
    parser.add_argument("--index-first", action="store_true", help="Index project artifacts before searching")
    args = parser.parse_args(argv)

    project_dir = Path(args.project_dir).resolve()
    if not project_dir.exists() or not project_dir.is_dir():
        parser.error(f"project_dir does not exist or is not a directory: {project_dir}")

    project_name = args.project_name or project_dir.name
    persist_dir = Path(args.persist_dir).resolve() if args.persist_dir else project_dir / ".spec" / "vector_store"
    service = SemanticSearchService(
        enabled=True,
        persist_dir=persist_dir,
        top_k=args.top_k,
        prefer_chroma=not args.no_chroma,
    )
    if args.index_first:
        service.index_project(project_dir, project_name)

    results = service.search(
        args.query,
        project_name,
        artifact_types=args.artifact_types,
        top_k=args.top_k,
    )
    sys.stdout.buffer.write(json.dumps([
        {
            "path": result.metadata.get("path", ""),
            "artifact_type": result.metadata.get("artifact_type", ""),
            "score": result.score,
            "chunk_index": result.metadata.get("chunk_index", 0),
            "content": result.content[:500],
        }
        for result in results
    ], ensure_ascii=False, indent=2).encode("utf-8"))
    sys.stdout.buffer.write(b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
