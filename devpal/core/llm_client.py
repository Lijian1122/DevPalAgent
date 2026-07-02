# -*- coding: utf-8 -*-
"""
LLM Client - Multi-provider LLM client with fallback support

Supports Anthropic Claude, OpenAI GPT-4, and other providers.
"""

from typing import Any, Callable, Dict, List, Optional

from .llm_providers.base import BaseLLMProvider, LLMUsage, ToolUseResult
from .llm_providers.anthropic import AnthropicProvider
from .llm_providers.openai import OpenAIProvider


class LLMClient:
    """Multi-provider LLM client with fallback support"""
    
    def __init__(
        self,
        provider: str = "openai",
        model: Optional[str] = None,
        fallback_providers: Optional[List[str]] = None,
        **kwargs
    ):
        """Initialize LLM Client

        Args:
        provider: Provider name ("openai", "anthropic", etc.)
            model: Model name (if None, use provider default)
            fallback_providers: List of fallback provider names
            **kwargs: Provider-specific configuration
        """
        self.provider_name = provider
        self.fallback_providers = fallback_providers or []
        self.kwargs = kwargs

        # Create main provider
        self.provider = self._create_provider(provider, model, **kwargs)

        # Fallback provider instances (lazy initialization)
        self._fallback_instances = {}
    
    def _create_provider(
        self,
        provider: str,
        model: Optional[str],
        **kwargs
    ) -> BaseLLMProvider:
        """Create provider instance"""
        if provider == "anthropic":
            return AnthropicProvider(model=model, **kwargs)
        elif provider == "openai":
            return OpenAIProvider(model=model, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def generate(self, *args, **kwargs) -> str:
        """Generate text response with fallback"""
        try:
            return self.provider.generate(*args, **kwargs)
        except Exception as e:
            return self._fallback_generate(*args, error=e, **kwargs)

    def generate_with_tool_loop(self, *args, **kwargs) -> ToolUseResult:
        """Generate with tool loop (backward compatibility)"""
        # Map to generate_with_tools
        return self.generate_with_tools(*args, **kwargs)

    def generate_with_tools(self, *args, **kwargs) -> ToolUseResult:
        """Generate response with tool calls, with fallback"""
        try:
            return self.provider.generate_with_tools(*args, **kwargs)
        except Exception as e:
            return self._fallback_generate_with_tools(*args, error=e, **kwargs)

    def _fallback_generate(self, *args, error, **kwargs) -> str:
        """Fallback to alternative provider"""
        for fallback_name in self.fallback_providers:
            try:
                # Lazy initialization
                if fallback_name not in self._fallback_instances:
                    self._fallback_instances[fallback_name] = self._create_provider(
                        fallback_name, None, **self.kwargs
                    )

                fallback = self._fallback_instances[fallback_name]
                result = fallback.generate(*args, **kwargs)

                # Merge usage statistics
                self._merge_usage(fallback.usage)

                return result
            except Exception:
                continue

        # All fallbacks failed, raise original error
        raise error

    def _fallback_generate_with_tools(self, *args, error, **kwargs) -> ToolUseResult:
        """Fallback to alternative provider for tool calls"""
        for fallback_name in self.fallback_providers:
            try:
                if fallback_name not in self._fallback_instances:
                    self._fallback_instances[fallback_name] = self._create_provider(
                        fallback_name, None, **self.kwargs
                    )

                fallback = self._fallback_instances[fallback_name]
                result = fallback.generate_with_tools(*args, **kwargs)

                # Merge usage statistics
                self._merge_usage(fallback.usage)

                return result
            except Exception:
                continue

        # All fallbacks failed, raise original error
        raise error

    def _merge_usage(self, fallback_usage: LLMUsage):
        """Merge fallback provider usage into main provider"""
        self.provider.usage.calls += fallback_usage.calls
        self.provider.usage.input_tokens += fallback_usage.input_tokens
        self.provider.usage.output_tokens += fallback_usage.output_tokens
        self.provider.usage.cache_read_tokens += fallback_usage.cache_read_tokens
        self.provider.usage.cache_creation_tokens += fallback_usage.cache_creation_tokens

    @property
    def usage(self) -> LLMUsage:
        """Get usage statistics"""
        return self.provider.usage

    def reset_usage(self):
        """Reset usage statistics"""
        self.provider.reset_usage()
        for fallback in self._fallback_instances.values():
            fallback.reset_usage()


# Global singleton instance
_llm_client_instance = None


def get_llm_client(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    fallback_providers: Optional[List[str]] = None,
    **kwargs
) -> LLMClient:
    """Get LLM Client instance (from config or parameters)

    Args:
        provider: Provider name (if None, use config default)
        model: Model name (if None, use provider default)
        fallback_providers: List of fallback provider names
        **kwargs: Provider-specific configuration
    Returns:
        LLMClient instance
    """
    global _llm_client_instance

    # If no parameters provided, return singleton
    if provider is None and model is None and not kwargs:
        if _llm_client_instance is None:
            # Load from config
            from devpal.config import get_config
            config = get_config()

            # Use config default provider
            default_provider = config.llm_default_provider
            fallback_list = config.llm_fallback_providers
            provider_config = config.get_provider_config(default_provider)

            _llm_client_instance = LLMClient(
                provider=default_provider,
                fallback_providers=fallback_list,
              **provider_config
          )
        return _llm_client_instance

    # Create new instance with provided parameters
    return LLMClient(
        provider=provider or "openai",
        model=model,
        fallback_providers=fallback_providers,
        **kwargs
    )


def reset_llm_client() -> None:
    """Reset singleton (for tests)"""
    global _llm_client_instance
    _llm_client_instance = None
