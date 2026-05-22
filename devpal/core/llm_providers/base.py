# -*- coding: utf-8 -*-
"""
BaseLLMProvider - LLM Provider abstract base class
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


@dataclass
class LLMUsage:
    """LLM usage statistics"""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    calls: int = 0


@dataclass
class ToolUseResult:
    """Tool use result"""
    stop_reason: str = ""
    text_output: str = ""
    tool_calls_handled: int = 0
    turns: int = 0


class BaseLLMProvider(ABC):
    """Base class for LLM providers"""

    def __init__(self, model: Optional[str] = None, **kwargs):
        self.model = model
        self.usage = LLMUsage()
        self.kwargs = kwargs

    @abstractmethod
    def generate(
        self,
        system: str,
        user_message: str,
        cached_context: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """Generate text response"""
        pass

    @abstractmethod
    def generate_with_tools(
        self,
        system: str,
        user_message: str,
        tools: List[Dict],
        tool_handler: Callable,
        cached_context: Optional[List[str]] = None,
        max_iterations: int = 10,
      **kwargs
    ) -> ToolUseResult:
        """Generate response with tool calls"""
        pass

    @abstractmethod
    def supports_caching(self) -> bool:
        """Whether this provider supports prompt caching"""
        pass

    def get_usage(self) -> LLMUsage:
        """Get usage statistics"""
        return self.usage

    def reset_usage(self):
        """Reset usage statistics"""
        self.usage = LLMUsage()
