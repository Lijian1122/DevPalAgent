# -*- coding: utf-8 -*-
"""Optional vector database adapters."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Optional

from .documents import VectorDocument
from .embeddings import EmbeddingProvider, MockEmbeddingProvider

try:
    import chromadb  # type: ignore
except ImportError:  # pragma: no cover - depends on optional dependency
    chromadb = None


class DisabledVectorStore:
    enabled = False

    def upsert(self, documents: List[VectorDocument]) -> None:
        return None

    def search(self, query: str, top_k: int = 5, filters: Optional[Dict] = None) -> List[VectorDocument]:
        return []

    def delete_by_project(self, project_name: str) -> None:
        return None


class InMemoryVectorStore:
    enabled = True

    def __init__(self, embedding_provider: Optional[EmbeddingProvider] = None):
        self.embedding_provider = embedding_provider or MockEmbeddingProvider()
        self._documents: Dict[str, VectorDocument] = {}
        self._embeddings: Dict[str, List[float]] = {}

    def upsert(self, documents: List[VectorDocument]) -> None:
        for document in documents:
            self._documents[document.id] = document
            self._embeddings[document.id] = self.embedding_provider.embed_text(document.content)

    def search(self, query: str, top_k: int = 5, filters: Optional[Dict] = None) -> List[VectorDocument]:
        query_embedding = self.embedding_provider.embed_text(query)
        scored = []
        for document_id, document in self._documents.items():
            if filters and not self._matches_filters(document, filters):
                continue
            score = _cosine_similarity(query_embedding, self._embeddings[document_id])
            scored.append(VectorDocument(
                id=document.id,
                content=document.content,
                metadata=dict(document.metadata),
                score=score,
            ))
        scored.sort(key=lambda doc: doc.score, reverse=True)
        return scored[:max(0, top_k)]

    def delete_by_project(self, project_name: str) -> None:
        to_delete = [
            doc_id
            for doc_id, doc in self._documents.items()
            if doc.metadata.get("project_name") == project_name
        ]
        for doc_id in to_delete:
            self._documents.pop(doc_id, None)
            self._embeddings.pop(doc_id, None)

    def _matches_filters(self, document: VectorDocument, filters: Dict) -> bool:
        return all(document.metadata.get(key) == value for key, value in filters.items())


class ChromaVectorStore:
    enabled = True

    def __init__(
        self,
        persist_dir: Path,
        collection_name: str = "devpal_artifacts",
        embedding_provider: Optional[EmbeddingProvider] = None,
    ):
        if chromadb is None:
            raise RuntimeError("ChromaDB is not installed")
        self.embedding_provider = embedding_provider or MockEmbeddingProvider()
        self.client = chromadb.PersistentClient(path=str(persist_dir))
        self.collection = self.client.get_or_create_collection(collection_name)

    def upsert(self, documents: List[VectorDocument]) -> None:
        if not documents:
            return
        embeddings = self.embedding_provider.embed_batch([doc.content for doc in documents])
        self.collection.upsert(
            ids=[doc.id for doc in documents],
            documents=[doc.content for doc in documents],
            metadatas=[doc.metadata for doc in documents],
            embeddings=embeddings,
        )

    def search(self, query: str, top_k: int = 5, filters: Optional[Dict] = None) -> List[VectorDocument]:
        query_embedding = self.embedding_provider.embed_text(query)
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=max(1, top_k),
            where=filters or None,
        )
        docs = result.get("documents", [[]])[0]
        ids = result.get("ids", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0] if result.get("distances") else [0.0] * len(docs)
        output = []
        for doc_id, content, metadata, distance in zip(ids, docs, metadatas, distances):
            output.append(VectorDocument(
                id=doc_id,
                content=content,
                metadata=dict(metadata or {}),
                score=1.0 / (1.0 + float(distance or 0.0)),
            ))
        return output

    def delete_by_project(self, project_name: str) -> None:
        self.collection.delete(where={"project_name": project_name})


def create_vector_store(
    enabled: bool = False,
    persist_dir: Optional[Path] = None,
    embedding_provider: Optional[EmbeddingProvider] = None,
    prefer_chroma: bool = True,
):
    if not enabled:
        return DisabledVectorStore()
    if prefer_chroma and chromadb is not None and persist_dir is not None:
        return ChromaVectorStore(persist_dir=persist_dir, embedding_provider=embedding_provider)
    return InMemoryVectorStore(embedding_provider=embedding_provider)


def _cosine_similarity(left: List[float], right: List[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)
