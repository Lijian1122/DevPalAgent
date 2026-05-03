# -*- coding: utf-8 -*-
"""
Error Memory
Records agent mistakes to avoid repetition
"""
import time
from typing import List, Dict, Any, Optional
from .base import BaseMemory, MemoryItem


class ErrorMemory(BaseMemory):
    """Manager for error memory - tracks and avoids historical errors"""

    ERROR_TYPES = {
        "tool_call_error": "Tool Call Error",
        "logic_error": "Logic Reasoning Error",
        "hallucination": "Hallucination",
        "parameter_error": "Parameter Error",
        "format_error": "Format Error",
        "safety_violation": "Safety Violation",
    }

    def __init__(self, persist_path: str = "./data/error_memory.json"):
        super().__init__(persist_path)
        self.errors: List[Dict[str, Any]] = self._load()

    def _load(self) -> List[Dict[str, Any]]:
        """Load error memory from disk"""
        return self._load_from_disk([])

    def _save(self) -> None:
        """Save error memory to disk"""
        self._save_to_disk(self.errors)

    def add(
        self,
        content: str,
        **kwargs
    ) -> None:
        """Compatibility interface with base class"""
        self.add_error(
            error_type=kwargs.get("error_type", "tool_call_error"),
            description=content,
            correction=kwargs.get("correction", ""),
            context=kwargs.get("context", "")
        )

    def add_error(
        self,
        error_type: str,
        description: str,
        correction: str = "",
        context: str = "",
        severity: int = 5
    ) -> None:
        """
        Record an error

        Args:
            error_type: Error type: tool_call_error / logic_error / hallucination / ...
            description: Error description
            correction: Correct approach / fix method
            context: Context when the error occurred
            severity: Severity level 1-10
        """
        if error_type not in self.ERROR_TYPES:
            raise ValueError(f"Error type must be one of: {list(self.ERROR_TYPES.keys())}")

        self.errors.append({
            "type": error_type,
            "description": description,
            "correction": correction,
            "context": context,
            "severity": severity,
            "timestamp": time.time(),
            "occurrences": 1
        })
        self._save()

    def increment_error_count(self, error_idx: int) -> None:
        """Increment error occurrence count"""
        if 0 <= error_idx < len(self.errors):
            self.errors[error_idx]["occurrences"] += 1
            self._save()

    def retrieve(
        self,
        query: str,
        top_k: int = 5
    ) -> List[MemoryItem]:
        """Retrieve similar historical errors"""
        similar_errors = self.check_for_similar_errors(query)
        return [
            MemoryItem(
                content=f"Error: {err['description']}, correct approach: {err['correction']}",
                memory_type="error",
                importance=err["severity"]
            )
            for err in similar_errors[:top_k]
        ]

    def check_for_similar_errors(self, current_context: str) -> List[Dict[str, Any]]:
        """Check for similar historical errors in current context"""
        if not current_context:
            return []

        context_words = set(current_context.lower().split())
        scored_errors = []

        for err in self.errors:
            desc_words = set(err["description"].lower().split())
            ctx_words = set(err["context"].lower().split())
            all_error_words = desc_words | ctx_words

            if all_error_words:
                overlap = len(context_words & all_error_words)
                similarity = overlap / len(all_error_words) if all_error_words else 0

                severity_weight = err["severity"] / 10.0
                occurrence_weight = min(err["occurrences"] * 0.1, 0.5)

                score = similarity * 0.5 + severity_weight * 0.3 + occurrence_weight * 0.2

                if similarity > 0.1 or score > 0.2:
                    scored_errors.append((score, err))

        scored_errors.sort(key=lambda x: x[0], reverse=True)
        return [err for _, err in scored_errors]

    def generate_warning_prompt(self, current_context: str) -> str:
        """Generate error warning prompt for LLM system prompt injection"""
        similar_errors = self.check_for_similar_errors(current_context)
        if not similar_errors:
            return ""

        prompt_parts = ["\n[Warning] Avoid repeating these similar errors:"]
        for i, err in enumerate(similar_errors[:3], 1):
            error_type_name = self.ERROR_TYPES.get(err["type"], err["type"])
            prompt_parts.append(f"{i}. [{error_type_name}] {err['description']}")
            if err["correction"]:
                prompt_parts.append(f"   Correct: {err['correction']}")

        return "\n".join(prompt_parts) + "\n"

    def clear(self) -> None:
        """Clear all error memory"""
        self.errors = []
        self._save()

    def get_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        stats = {
            "total": len(self.errors),
            "by_type": {},
            "frequent_errors": []
        }

        for err_type in self.ERROR_TYPES:
            count = sum(1 for e in self.errors if e["type"] == err_type)
            if count > 0:
                stats["by_type"][err_type] = count

        frequent = sorted(
            self.errors,
            key=lambda x: x["occurrences"],
            reverse=True
        )[:5]
        stats["frequent_errors"] = [
            {"desc": e["description"], "count": e["occurrences"]}
            for e in frequent
            if e["occurrences"] > 1
        ]

        return stats

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all error memories"""
        return list(self.errors)

    def __len__(self) -> int:
        return len(self.errors)
