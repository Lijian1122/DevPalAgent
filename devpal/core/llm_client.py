# -*- coding: utf-8 -*-
"""
LLM Client - Anthropic Claude API thin wrapper

Supports prompt caching (5-minute TTL) and multi-turn tool_use loops.
Shared across OpenSpec Phase 3/4/10 so the same requirements/tech design
payload can be reused via cache breakpoints.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

try:
    from anthropic import Anthropic
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    Anthropic = None
    _ANTHROPIC_AVAILABLE = False

from devpal.config import get_config


DEFAULT_MAX_TOKENS = 8192
CACHE_MIN_CHARS = 2000


@dataclass
class LLMUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    calls: int = 0

    def add(self, usage: Any) -> None:
        self.calls += 1
        self.input_tokens += getattr(usage, "input_tokens", 0) or 0
        self.output_tokens += getattr(usage, "output_tokens", 0) or 0
        self.cache_read_tokens += getattr(usage, "cache_read_input_tokens", 0) or 0
        self.cache_creation_tokens += getattr(usage, "cache_creation_input_tokens", 0) or 0


@dataclass
class ToolUseResult:
    stop_reason: str = ""
    text_output: str = ""
    tool_calls_handled: int = 0
    turns: int = 0


class LLMClient:
    """Anthropic Claude wrapper with prompt caching and tool_use loop."""

    def __init__(self, model: Optional[str] = None):
        if not _ANTHROPIC_AVAILABLE:
            raise RuntimeError(
                "anthropic SDK not installed. Run: pip install anthropic>=0.97.0"
            )

        config = get_config()
        self.config = config
        self.model = model or config.anthropic_model
        self.api_key = config.anthropic_auth_token
        self.base_url = config.anthropic_base_url

        if not self.api_key:
            raise RuntimeError(
                "Anthropic API Key missing. Set env ANTHROPIC_AUTH_TOKEN or "
                "anthropic.auth_token in config/config.yaml"
            )

        kwargs: Dict[str, Any] = {"api_key": self.api_key}
        if self.base_url and self.base_url != "https://api.anthropic.com":
            kwargs["base_url"] = self.base_url

        self._client = Anthropic(**kwargs)
        self.usage = LLMUsage()

    def _call(
        self,
        system_blocks: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> Any:
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system_blocks,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
        response = self._client.messages.create(**kwargs)
        self.usage.add(response.usage)
        return response

    def generate(
        self,
        system: str,
        user_message: str,
        cached_context: Optional[List[str]] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> str:
        """Single-turn text generation."""
        system_blocks = self._build_system_blocks(system)
        user_content = self._build_user_content(cached_context, user_message)
        messages = [{"role": "user", "content": user_content}]
        response = self._call(system_blocks, messages, max_tokens=max_tokens)
        parts: List[str] = []
        for block in response.content:
            if getattr(block, "type", None) == "text":
                parts.append(block.text)
        return "".join(parts)

    def generate_with_tool_loop(
        self,
        system: str,
        user_message: str,
        tools: List[Dict[str, Any]],
        tool_handler: Callable[[str, Dict[str, Any]], str],
        cached_context: Optional[List[str]] = None,
        max_turns: int = 10,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> ToolUseResult:
        """Multi-turn tool_use loop until end_turn or max_turns reached."""
        system_blocks = self._build_system_blocks(system)
        user_content = self._build_user_content(cached_context, user_message)
        messages: List[Dict[str, Any]] = [{"role": "user", "content": user_content}]

        result = ToolUseResult()
        text_parts: List[str] = []

        for turn in range(max_turns):
            result.turns = turn + 1
            response = self._call(system_blocks, messages, tools=tools, max_tokens=max_tokens)
            result.stop_reason = response.stop_reason or ""

            for block in response.content:
                if getattr(block, "type", None) == "text" and block.text:
                    text_parts.append(block.text)

            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                break

            tool_results: List[Dict[str, Any]] = []
            for block in response.content:
                if getattr(block, "type", None) != "tool_use":
                    continue
                try:
                    output = tool_handler(block.name, block.input or {})
                    is_error = False
                except Exception as exc:
                    output = f"[tool_error] {exc}"
                    is_error = True
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                    "is_error": is_error,
                })
                result.tool_calls_handled += 1

            if tool_results:
                messages.append({"role": "user", "content": tool_results})

        result.text_output = "".join(text_parts)
        return result

    @staticmethod
    def _build_system_blocks(system: str) -> List[Dict[str, Any]]:
        block: Dict[str, Any] = {"type": "text", "text": system}
        if len(system) >= CACHE_MIN_CHARS:
            block["cache_control"] = {"type": "ephemeral"}
        return [block]

    @staticmethod
    def _build_user_content(
        cached_context: Optional[List[str]],
        user_message: str,
    ) -> List[Dict[str, Any]]:
        content: List[Dict[str, Any]] = []
        if cached_context:
            for ctx in cached_context:
                if not ctx:
                    continue
                block: Dict[str, Any] = {"type": "text", "text": ctx}
                if len(ctx) >= CACHE_MIN_CHARS:
                    block["cache_control"] = {"type": "ephemeral"}
                content.append(block)
        content.append({"type": "text", "text": user_message})
        return content


_llm_client_instance = None


def get_llm_client() -> LLMClient:
    """Return global LLMClient singleton."""
    global _llm_client_instance
    if _llm_client_instance is None:
        _llm_client_instance = LLMClient()
    return _llm_client_instance


def reset_llm_client() -> None:
    """Reset singleton (for tests)."""
    global _llm_client_instance
    _llm_client_instance = None
