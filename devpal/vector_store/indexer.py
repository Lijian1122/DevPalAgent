# -*- coding: utf-8 -*-
"""Artifact indexing for semantic retrieval."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .documents import VectorDocument

TEXT_PATTERNS = {
    "requirements": ["requirements/*.md"],
    "change": ["openspec/changes/*/proposal.md", "openspec/changes/*/tasks.md", "openspec/changes/*/design.md", "openspec/changes/*/metadata.json", "openspec/changes/*/specs/spec.md"],
    "source": ["src/**/*.py", "src/**/*.cpp", "src/**/*.c", "src/**/*.h", "src/**/*.hpp", "include/**/*.h", "include/**/*.hpp"],
    "test": ["tests/**/*.py", "tests/**/*.cpp", "tests/**/*.sh"],
    "report": ["docs/final_report.md", "docs/*.md"],
}


class ProjectArtifactIndexer:
    def __init__(self, max_chunk_chars: int = 2400):
        self.max_chunk_chars = max(400, max_chunk_chars)

    def index_project(self, project_dir: Path, project_name: str, language: str = "") -> List[VectorDocument]:
        documents: List[VectorDocument] = []
        for artifact_type, patterns in TEXT_PATTERNS.items():
            for path in self._iter_paths(project_dir, patterns):
                documents.extend(self.index_file(path, project_dir, project_name, artifact_type, language=language))
        return documents

    def index_file(
        self,
        path: Path,
        project_dir: Path,
        project_name: str,
        artifact_type: str,
        language: str = "",
        change_id: Optional[str] = None,
        requirement_id: Optional[str] = None,
    ) -> List[VectorDocument]:
        if not path.exists() or not path.is_file():
            return []
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []
        if not content.strip():
            return []

        rel_path = path.relative_to(project_dir).as_posix() if path.is_relative_to(project_dir) else path.as_posix()
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        chunks = self._chunk_markdown(content) if path.suffix.lower() == ".md" else self._chunk_text(content)
        documents = []
        for index, chunk in enumerate(chunks):
            doc_id = f"{project_name}:{artifact_type}:{rel_path}:{index}:{content_hash[:12]}"
            documents.append(VectorDocument(
                id=doc_id,
                content=chunk,
                metadata={
                    "project_name": project_name,
                    "artifact_type": artifact_type,
                    "path": rel_path,
                    "language": language,
                    "phase_number": self._phase_for_artifact(artifact_type),
                    "change_id": change_id or self._infer_change_id(rel_path),
                    "requirement_id": requirement_id or "",
                    "hash": content_hash,
                    "mtime": str(path.stat().st_mtime),
                    "chunk_index": index,
                    "embedding_model": "mock-hash-v1",
                },
            ))
        return documents

    def index_change_artifacts(self, change_dir: Path, project_dir: Path, project_name: str, language: str = "") -> List[VectorDocument]:
        documents: List[VectorDocument] = []
        if not change_dir.exists():
            return documents
        for relative in ("proposal.md", "tasks.md", "design.md", "metadata.json", "specs/spec.md"):
            documents.extend(self.index_file(
                change_dir / relative,
                project_dir,
                project_name,
                "change",
                language=language,
                change_id=change_dir.name,
            ))
        return documents

    def index_error_memory(self, records: Iterable[Dict], project_name: str) -> List[VectorDocument]:
        documents = []
        for index, record in enumerate(records):
            content = "\n".join([
                str(record.get("type", "")),
                str(record.get("description", "")),
                str(record.get("correction", "")),
                str(record.get("context", "")),
            ]).strip()
            if not content:
                continue
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            documents.append(VectorDocument(
                id=f"{project_name}:error:{index}:{content_hash[:12]}",
                content=content,
                metadata={
                    "project_name": project_name,
                    "artifact_type": "error",
                    "path": "error_memory",
                    "language": "",
                    "phase_number": 0,
                    "change_id": "",
                    "requirement_id": "",
                    "hash": content_hash,
                    "mtime": str(record.get("timestamp", "")),
                    "chunk_index": 0,
                    "embedding_model": "mock-hash-v1",
                    "severity": record.get("severity", 0),
                },
            ))
        return documents

    def _iter_paths(self, project_dir: Path, patterns: List[str]) -> Iterable[Path]:
        seen = set()
        for pattern in patterns:
            for path in sorted(project_dir.glob(pattern)):
                if path.is_file() and path not in seen:
                    seen.add(path)
                    yield path

    def _chunk_markdown(self, content: str) -> List[str]:
        chunks = []
        current = []
        for line in content.splitlines():
            if line.startswith("#") and current:
                chunks.extend(self._chunk_text("\n".join(current).strip()))
                current = [line]
            else:
                current.append(line)
        if current:
            chunks.extend(self._chunk_text("\n".join(current).strip()))
        return [chunk for chunk in chunks if chunk.strip()]

    def _chunk_text(self, content: str) -> List[str]:
        text = content.strip()
        if not text:
            return []
        if len(text) <= self.max_chunk_chars:
            return [text]
        chunks = []
        start = 0
        while start < len(text):
            chunks.append(text[start:start + self.max_chunk_chars])
            start += self.max_chunk_chars
        return chunks

    def _phase_for_artifact(self, artifact_type: str) -> int:
        return {
            "requirements": 1,
            "change": 1,
            "source": 4,
            "test": 5,
            "report": 11,
            "error": 10,
        }.get(artifact_type, 0)

    def _infer_change_id(self, rel_path: str) -> str:
        parts = rel_path.split("/")
        if len(parts) >= 3 and parts[0] == "openspec" and parts[1] == "changes":
            return parts[2]
        return ""
