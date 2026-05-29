# -*- coding: utf-8 -*-
"""Vector retrieval document types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class VectorDocument:
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "metadata": dict(self.metadata),
            "score": self.score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VectorDocument":
        return cls(
            id=str(data.get("id", "")),
            content=str(data.get("content", "")),
            metadata=dict(data.get("metadata", {}) or {}),
            score=float(data.get("score", 0.0) or 0.0),
        )
