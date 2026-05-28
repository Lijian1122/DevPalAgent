# -*- coding: utf-8 -*-
"""
Anthropic Provider - Claude API implementation
"""

from typing import Any, Callable, Dict, List, Optional

try:
    from anthropic import (
        Anthropic,
        APIConnectionError,
        APIStatusError,
        APITimeoutError,
        AuthenticationError,
        PermissionDeniedError,
        RateLimitError,
    )
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    Anthropic = None
    APIConnectionError = APIStatusError = APITimeoutError = Exception
    AuthenticationError = PermissionDeniedError = RateLimitError = Exception
    _ANTHROPIC_AVAILABLE = False

from .base import BaseLLMProvider, LLMUsage, ToolUseResult


DEFAULT_MAX_TOKENS = 8192
CACHE_MIN_CHARS = 2000


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude Provider with prompt caching support"""

    def __init__(self, model: str = "claude-3-5-sonnet-20241022", **kwargs):
        super().__init__(model, **kwargs)
        
        if not _ANTHROPIC_AVAILABLE:
            raise RuntimeError(
          "anthropic SDK not installed. Run: pip install anthropic>=0.97.0"
          )
      
        api_key = kwargs.get('api_key') or kwargs.get('auth_token')
        if not api_key:
            raise RuntimeError(
                "Anthropic API Key missing. Provide 'api_key' or 'auth_token' parameter"
            )
        
        client_kwargs = {"api_key": api_key}
        base_url = kwargs.get('base_url')
        if base_url and base_url != "https://api.anthropic.com":
          client_kwargs["base_url"] = base_url
        timeout = kwargs.get("timeout") or kwargs.get("request_timeout") or 90
        client_kwargs["timeout"] = float(timeout)
        client_kwargs["max_retries"] = int(kwargs.get("max_retries", 0))

        self._client = Anthropic(**client_kwargs)

    def generate(
        self,
        system: str,
        user_message: str,
      cached_context: Optional[List[str]] = None,
    **kwargs
    ) -> str:
        """Single-turn text generation"""
        max_tokens = kwargs.get('max_tokens', DEFAULT_MAX_TOKENS)
        
        system_blocks = self._build_system_blocks(system)
        user_content = self._build_user_content(cached_context, user_message)
        messages = [{"role": "user", "content": user_content}]
        
        response = self._call(system_blocks, messages, max_tokens=max_tokens)
        
        parts = []
        for block in response.content:
            if getattr(block, "type", None) == "text":
               parts.append(block.text)
     
        return "".join(parts)

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
        """Multi-turn tool_use loop"""
        max_tokens = kwargs.get("max_tokens", DEFAULT_MAX_TOKENS)

        system_blocks = self._build_system_blocks(system)
        user_content = self._build_user_content(cached_context, user_message)
        messages = [{"role": "user", "content": user_content}]

        result = ToolUseResult()
        text_parts = []

        for turn in range(max_iterations):
            result.turns = turn + 1
            response = self._call(
                system_blocks,
                messages,
                tools=tools,
                max_tokens=max_tokens,
            )
            result.stop_reason = response.stop_reason or ""

            assistant_content = []
            for block in response.content:
                assistant_content.append(block)
                if getattr(block, "type", None) == "text" and getattr(block, "text", None):
                    text_parts.append(block.text)

            messages.append({"role": "assistant", "content": assistant_content})

            if response.stop_reason != "tool_use":
                break

            tool_results = []
            for block in response.content:
                if getattr(block, "type", None) != "tool_use":
                    continue
                try:
                    output = tool_handler(block.name, block.input or {})
                    is_error = False
                except Exception as exc:
                    output = f"[tool_error] {exc}"
                    is_error = True

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": output,
                        "is_error": is_error,
                    }
                )
                result.tool_calls_handled += 1

            if tool_results:
                messages.append({"role": "user", "content": tool_results})
            else:
                break

        result.text_output = "".join(text_parts)
        return result

    def supports_caching(self) -> bool:
        """Anthropic supports prompt caching"""
        return True

    def _call(
        self,
        system_blocks: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> Any:
        """Call Anthropic API"""
        kwargs = {
        "model": self.model,
          "max_tokens": max_tokens,
            "system": system_blocks,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
        
        try:
            response = self._client.messages.create(**kwargs)
        except Exception as exc:
            raise RuntimeError(self._format_anthropic_error(exc)) from exc
        self._update_usage(response.usage)
        return response

    def _format_anthropic_error(self, exc: Exception) -> str:
        parts = [f"Anthropic API call failed: {exc.__class__.__name__}: {exc}"]

        status_code = getattr(exc, "status_code", None)
        if status_code is not None:
            parts.append(f"status_code={status_code}")

        request_id = getattr(exc, "request_id", None)
        if not request_id:
            response = getattr(exc, "response", None)
            request_id = getattr(response, "headers", {}).get("request-id") if response else None
        if request_id:
            parts.append(f"request_id={request_id}")

        error_obj = getattr(exc, "body", None) or getattr(exc, "error", None)
        error_type = self._extract_error_value(error_obj, "type")
        error_message = self._extract_error_value(error_obj, "message")
        if error_type:
            parts.append(f"error_type={error_type}")
        if error_message:
            parts.append(f"api_message={error_message}")

        headers = getattr(getattr(exc, "response", None), "headers", {}) or {}
        retry_after = headers.get("retry-after") or headers.get("Retry-After")
        if retry_after:
            parts.append(f"retry_after={retry_after}s")

        diagnosis = self._diagnose_anthropic_error(exc, status_code, error_type)
        if diagnosis:
            parts.append(f"diagnosis={diagnosis}")

        return " | ".join(parts)

    @staticmethod
    def _extract_error_value(error_obj: Any, key: str) -> Optional[str]:
        if not error_obj:
            return None
        if isinstance(error_obj, dict):
            nested = error_obj.get("error") if isinstance(error_obj.get("error"), dict) else error_obj
            value = nested.get(key)
            return str(value) if value else None
        value = getattr(error_obj, key, None)
        return str(value) if value else None

    @staticmethod
    def _diagnose_anthropic_error(
        exc: Exception,
        status_code: Optional[int],
        error_type: Optional[str],
    ) -> str:
        error_type_text = (error_type or "").lower()
        message = str(exc).lower()

        if isinstance(exc, APITimeoutError):
            return "request timed out; check network/proxy connectivity or reduce prompt/output size"
        if isinstance(exc, APIConnectionError):
            return "network connection failed; check base_url, proxy, DNS, and firewall settings"
        if isinstance(exc, AuthenticationError) or status_code == 401:
            return "authentication failed; check ANTHROPIC_API_KEY/ANTHROPIC_AUTH_TOKEN"
        if isinstance(exc, PermissionDeniedError) or status_code == 403:
            return "permission denied; check model access, subscription/billing status, or account permissions"
        if isinstance(exc, RateLimitError) or status_code == 429:
            if "quota" in error_type_text or "quota" in message or "credit" in message or "billing" in message:
                return "quota or credits appear exhausted; check billing/package balance"
            return "rate limited; wait before retrying or reduce request rate"
        if status_code in {500, 502, 503, 504, 529}:
            return "Anthropic service is temporarily unavailable or overloaded; retry later"
        if isinstance(exc, APIStatusError):
            return "API returned a non-success HTTP status; inspect status_code/error_type/request_id"
        return "unexpected Anthropic SDK error; inspect error_class and request_id"

    def _update_usage(self, usage: Any) -> None:
        """Update usage statistics"""
        self.usage.calls += 1
        self.usage.input_tokens += getattr(usage, "input_tokens", 0) or 0
        self.usage.output_tokens += getattr(usage, "output_tokens", 0) or 0
        self.usage.cache_read_tokens += getattr(usage, "cache_read_input_tokens", 0) or 0
        self.usage.cache_creation_tokens += getattr(usage, "cache_creation_input_tokens", 0) or 0

    @staticmethod
    def _build_system_blocks(system: str) -> List[Dict[str, Any]]:
        """Build system blocks with cache_control"""
        block = {"type": "text", "text": system}
        if len(system) >= CACHE_MIN_CHARS:
         block["cache_control"] = {"type": "ephemeral"}
        return [block]

    @staticmethod
    def _build_user_content(
        cached_context: Optional[List[str]],
        user_message: str,
    ) -> List[Dict[str, Any]]:
        """Build user content with cached_context"""
        content = []
        if cached_context:
            for ctx in cached_context:
                if not ctx:
                    continue
            block = {"type": "text", "text": ctx}
            if len(ctx) >= CACHE_MIN_CHARS:
                    block["cache_control"] = {"type": "ephemeral"}
            content.append(block)
        content.append({"type": "text", "text": user_message})
        return content
