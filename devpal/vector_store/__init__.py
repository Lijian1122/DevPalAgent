# -*- coding: utf-8 -*-
"""Optional semantic retrieval support for DevPalAgent."""

from .documents import VectorDocument
from .embeddings import EmbeddingProvider, MockEmbeddingProvider
from .semantic_search import SemanticSearchService

__all__ = [
    "VectorDocument",
    "EmbeddingProvider",
    "MockEmbeddingProvider",
    "SemanticSearchService",
]
