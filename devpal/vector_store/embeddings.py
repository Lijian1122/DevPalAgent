# -*- coding: utf-8 -*-
"""Embedding providers for semantic retrieval."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from typing import List


class EmbeddingProvider(ABC):
    model_name = "base"

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        pass

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(text) for text in texts]


class MockEmbeddingProvider(EmbeddingProvider):
    model_name = "mock-hash-v1"

    def __init__(self, dimensions: int = 32):
        self.dimensions = max(8, dimensions)

    def embed_text(self, text: str) -> List[float]:
        normalized = (text or "").lower().encode("utf-8")
        digest = hashlib.sha256(normalized).digest()
        values = []
        while len(values) < self.dimensions:
            for byte in digest:
                values.append((byte / 127.5) - 1.0)
                if len(values) == self.dimensions:
                    break
            digest = hashlib.sha256(digest).digest()
        return values
