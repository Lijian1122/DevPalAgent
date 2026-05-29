# -*- coding: utf-8 -*-
"""Stable semantic search API for OpenSpec phases."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, List, Optional

from .documents import VectorDocument
from .embeddings import EmbeddingProvider, MockEmbeddingProvider
from .indexer import ProjectArtifactIndexer
from .vector_db import create_vector_store


class SemanticSearchService:
    def __init__(
        self,
        enabled: bool = False,
        persist_dir: Optional[Path] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        top_k: int = 5,
        prefer_chroma: bool = True,
        log=None,
    ):
        self.enabled = enabled
        self.top_k = top_k
        self.log = log
        self.embedding_provider = embedding_provider or MockEmbeddingProvider()
        self.store = create_vector_store(
            enabled=enabled,
            persist_dir=persist_dir,
            embedding_provider=self.embedding_provider,
            prefer_chroma=prefer_chroma,
        )
        self.indexer = ProjectArtifactIndexer()
        self.stats: Dict[str, int] = {
            "indexed_documents": 0,
            "search_count": 0,
            "fallback_count": 0,
            "retrieval_latency_ms": 0,
        }

    @classmethod
    def from_context(cls, context, log=None) -> "SemanticSearchService":
        enabled = bool(getattr(context, "vector_retrieval_enabled", False))
        project_dir = getattr(context, "project_dir", None)
        persist_dir = getattr(context, "vector_persist_dir", None)
        if persist_dir is None and project_dir is not None:
            persist_dir = Path(project_dir) / ".spec" / "vector_store"
        cache_key = (
            enabled,
            Path(persist_dir).as_posix() if persist_dir else "",
            int(getattr(context, "vector_top_k", 5) or 5),
            bool(getattr(context, "vector_prefer_chroma", True)),
        )
        service = getattr(context, "_vector_search_service", None)
        if service is not None and getattr(context, "_vector_search_service_key", None) == cache_key:
            service.log = log
            return service
        service = cls(
            enabled=enabled,
            persist_dir=Path(persist_dir) if persist_dir else None,
            top_k=cache_key[2],
            prefer_chroma=cache_key[3],
            log=log,
        )
        context._vector_search_service = service
        context._vector_search_service_key = cache_key
        return service

    def index_context(self, context, project_name: str) -> int:
        if not self.enabled or not getattr(self.store, "enabled", False):
            return 0
        started = time.time()
        event_integration = getattr(context, "event_integration", None)
        if event_integration:
            event_integration.emit_vector_index_started(
                project_name,
                artifact_types=["requirements", "change", "source", "test", "report"],
            )
        project_dir = Path(getattr(context, "project_dir", "."))
        language = getattr(context, "language", "")
        documents: List[VectorDocument] = []
        requirements_file = getattr(context, "requirements_file", None)
        if requirements_file:
            documents.extend(
                self.indexer.index_file(
                    Path(requirements_file),
                    project_dir,
                    project_name,
                    "requirements",
                    language=language,
                )
            )
        current_change_dir = getattr(context, "current_change_dir", None)
        if current_change_dir:
            documents.extend(
                self.indexer.index_change_artifacts(
                    Path(current_change_dir),
                    project_dir,
                    project_name,
                    language=language,
                )
            )
        documents.extend(self.indexer.index_project(project_dir, project_name, language=language))
        self.store.delete_by_project(project_name)
        self.store.upsert(documents)
        self.stats["indexed_documents"] = len(documents)
        if event_integration:
            event_integration.emit_vector_index_completed(
                project_name,
                indexed_documents=len(documents),
                duration_ms=int((time.time() - started) * 1000),
            )
        return len(documents)

    def index_project(self, project_dir: Path, project_name: str, language: str = "") -> int:
        if not self.enabled or not getattr(self.store, "enabled", False):
            return 0
        documents = self.indexer.index_project(project_dir, project_name, language=language)
        self.store.delete_by_project(project_name)
        self.store.upsert(documents)
        self.stats["indexed_documents"] = len(documents)
        return len(documents)

    def search(
        self,
        query: str,
        project_name: str,
        artifact_types: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        event_integration=None,
    ) -> List[VectorDocument]:
        effective_top_k = top_k or self.top_k
        if event_integration:
            event_integration.emit_vector_search_started(
                project_name,
                top_k=effective_top_k,
                artifact_types=artifact_types or [],
            )
        if not self.enabled or not query.strip() or not getattr(self.store, "enabled", False):
            self.stats["fallback_count"] += 1
            if event_integration:
                event_integration.emit_vector_search_completed(
                    project_name,
                    top_k=effective_top_k,
                    result_count=0,
                    retrieval_latency_ms=0,
                    fallback=True,
                )
            return []
        filters = {"project_name": project_name}
        started = time.time()
        try:
            if artifact_types and len(artifact_types) > 1:
                by_id: Dict[str, VectorDocument] = {}
                for artifact_type in artifact_types:
                    typed_filters = {**filters, "artifact_type": artifact_type}
                    for document in self.store.search(query, top_k=effective_top_k, filters=typed_filters):
                        existing = by_id.get(document.id)
                        if existing is None or document.score > existing.score:
                            by_id[document.id] = document
                results = sorted(by_id.values(), key=lambda doc: doc.score, reverse=True)
            else:
                if artifact_types:
                    filters["artifact_type"] = artifact_types[0]
                results = self.store.search(query, top_k=effective_top_k, filters=filters)
        except Exception as exc:
            self.stats["fallback_count"] += 1
            if self.log:
                self.log(f"  [VECTOR] search unavailable: {exc}")
            if event_integration:
                event_integration.emit_vector_search_completed(
                    project_name,
                    top_k=effective_top_k,
                    result_count=0,
                    retrieval_latency_ms=int((time.time() - started) * 1000),
                    fallback=True,
                )
            return []
        self.stats["search_count"] += 1
        latency_ms = int((time.time() - started) * 1000)
        self.stats["retrieval_latency_ms"] += latency_ms
        results = results[:effective_top_k]
        if event_integration:
            event_integration.emit_vector_search_completed(
                project_name,
                top_k=effective_top_k,
                result_count=len(results),
                retrieval_latency_ms=latency_ms,
                fallback=False,
            )
        return results

    def build_context(
        self,
        query: str,
        project_name: str,
        artifact_types: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        event_integration=None,
    ) -> str:
        results = self.search(
            query,
            project_name,
            artifact_types=artifact_types,
            top_k=top_k,
            event_integration=event_integration,
        )
        if not results:
            return ""
        lines = ["=== RETRIEVED RELATED CONTEXT ==="]
        for index, document in enumerate(results, 1):
            path = document.metadata.get("path", "unknown")
            artifact_type = document.metadata.get("artifact_type", "unknown")
            lines.append(f"\n[{index}] {artifact_type}: {path} (score={document.score:.3f})")
            lines.append(document.content[:1200])
        lines.append("=== END RETRIEVED RELATED CONTEXT ===")
        return "\n".join(lines)

    def search_similar_errors(self, error_message: str, project_name: str, top_k: int = 3, event_integration=None) -> List[VectorDocument]:
        return self.search(
            error_message,
            project_name,
            artifact_types=["error"],
            top_k=top_k,
            event_integration=event_integration,
        )
