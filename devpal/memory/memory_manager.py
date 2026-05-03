# -*- coding: utf-8 -*-
"""
Unified Memory Manager
Integrates 3 memory layers: Short-term, Long-term, Error memory
"""
from typing import Optional, Dict, Any, List
from .short_term import ShortTermMemory
from .long_term import LongTermMemory
from .error_memory import ErrorMemory


class MemoryManager:
    """Main entry point for memory system"""

    def __init__(
        self,
        enable_long_term: bool = True,
        enable_error: bool = True,
        long_term_path: Optional[str] = None,
        error_path: Optional[str] = None
    ):
        # Short-term memory (always enabled)
        self.short_term = ShortTermMemory()

        # Long-term memory
        self.long_term: Optional[LongTermMemory] = None
        if enable_long_term:
            path = long_term_path or "./data/long_term_memory.json"
            self.long_term = LongTermMemory(path)

        # Error memory
        self.error: Optional[ErrorMemory] = None
        if enable_error:
            path = error_path or "./data/error_memory.json"
            self.error = ErrorMemory(path)

    def get_system_prompt_enhancement(self, current_query: str) -> str:
        """
        Get enhanced system prompt with memory context
        """
        enhancements = []

        # Inject long-term memory
        if self.long_term is not None:
            context = self.long_term.get_relevant_context(current_query)
            if context:
                enhancements.append(context)

        # Inject error warnings
        if self.error is not None:
            warning = self.error.generate_warning_prompt(current_query)
            if warning:
                enhancements.append(warning)

        return "\n".join(enhancements)

    def record_success(self, task: str, result: str) -> None:
        """Record successful experience"""
        if self.long_term is not None:
            self.long_term.add_experience(
                f"Success: {task}, result: {result[:100]}..."
            )

    def record_error(
        self,
        error_type: str,
        description: str,
        correction: str,
        context: str = ""
    ) -> None:
        """Record an error"""
        if self.error is not None:
            self.error.add_error(error_type, description, correction, context)

        if self.long_term is not None:
            self.long_term.add_experience(
                f"Error: {description}, fix: {correction}",
                importance=7
            )

    def record_preference(self, preference: str) -> None:
        """Record user preference"""
        if self.long_term is not None:
            self.long_term.add_user_preference(preference)

    def record_knowledge(self, knowledge: str) -> None:
        """Record code knowledge"""
        if self.long_term is not None:
            self.long_term.add_knowledge(knowledge)

    def clear_short_term(self) -> None:
        """Clear short-term memory (for new session)"""
        self.short_term.clear()

    def clear_all(self) -> None:
        """Clear ALL memory (use carefully)"""
        self.short_term.clear()
        if self.long_term is not None:
            self.long_term.clear()
        if self.error is not None:
            self.error.clear()

    def get_statistics(self) -> Dict[str, Any]:
        """Get memory statistics"""
        stats = {
            "short_term_count": len(self.short_term),
            "long_term_enabled": self.long_term is not None,
            "error_memory_enabled": self.error is not None,
        }
        if self.long_term is not None:
            stats["long_term_count"] = len(self.long_term)
            for mem_type in self.long_term.MEMORY_TYPES:
                type_items = self.long_term.get_by_type(mem_type)
                stats[f"long_term_{mem_type}_count"] = len(type_items)
        if self.error is not None:
            stats["error_count"] = len(self.error)
            stats["error_stats"] = self.error.get_statistics()
        return stats

    def retrieve_all(self, query: str, top_k: int = 3) -> List[str]:
        """Retrieve relevant content from all memory sources"""
        results = []

        # Short-term memory
        short_items = self.short_term.retrieve(query, top_k)
        results.extend([item.content for item in short_items])

        # Long-term memory
        if self.long_term is not None:
            long_items = self.long_term.retrieve(query, top_k=top_k)
            results.extend([item.content for item in long_items])

        # Error memory
        if self.error is not None:
            error_items = self.error.retrieve(query, top_k=top_k)
            results.extend([item.content for item in error_items])

        return results
