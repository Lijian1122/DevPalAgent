# -*- coding: utf-8 -*-
"""CLI entrypoint for indexing project artifacts into the local vector store."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .semantic_search import SemanticSearchService


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Index DevPal project artifacts for semantic search")
    parser.add_argument("project_dir", help="Project directory to index")
    parser.add_argument("--project-name", help="Project name metadata override")
    parser.add_argument("--language", default="", help="Project language metadata")
    parser.add_argument("--persist-dir", help="Vector store directory (default: <project>/.spec/vector_store)")
    parser.add_argument("--no-chroma", action="store_true", help="Use in-memory vector store instead of ChromaDB")
    args = parser.parse_args(argv)

    project_dir = Path(args.project_dir).resolve()
    if not project_dir.exists() or not project_dir.is_dir():
        parser.error(f"project_dir does not exist or is not a directory: {project_dir}")

    project_name = args.project_name or project_dir.name
    persist_dir = Path(args.persist_dir).resolve() if args.persist_dir else project_dir / ".spec" / "vector_store"
    service = SemanticSearchService(
        enabled=True,
        persist_dir=persist_dir,
        prefer_chroma=not args.no_chroma,
    )
    count = service.index_project(project_dir, project_name, language=args.language)
    sys.stdout.buffer.write(json.dumps({
        "project_name": project_name,
        "project_dir": project_dir.as_posix(),
        "persist_dir": persist_dir.as_posix(),
        "indexed_documents": count,
    }, ensure_ascii=False, indent=2).encode("utf-8"))
    sys.stdout.buffer.write(b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
