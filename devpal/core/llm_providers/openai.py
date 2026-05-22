# -*- coding: utf-8 -*-
"""
OpenAI Provider - GPT API implementation
"""

import json
from typing import Any, Callable, Dict, List, Optional

try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    _OPENAI_AVAILABLE = False

from .base import BaseLLMProvider, LLMUsage, ToolUseResult


DEFAULT_MAX_TOKENS = 4096


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT Provider"""

    def __init__(self, model: str = "gpt-4-turbo-2024-04-09", **kwargs):
        super().__init__(model, **kwargs)
        
        if not _OPENAI_AVAILABLE:
            raise RuntimeError(
                "openai SDK not installed. Run: pip install openai>=1.0.0"
            )
        api_key = kwargs.get('api_key')
        if not api_key:
            raise RuntimeError(
                "OpenAI API Key missing. Provide 'api_key' parameter"
        )
        
        client_kwargs = {"api_key": api_key}
        base_url = kwargs.get('base_url')
        if base_url:
          client_kwargs["base_url"] = base_url
        
        self._client = OpenAI(**client_kwargs)

    def generate(
        self,
        system: str,
        user_message: str,
        cached_context: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """Single-turn text generation"""
        max_tokens = kwargs.get('max_tokens', DEFAULT_MAX_TOKENS)
        
        messages = [{"role": "system", "content": system}]
        
        if cached_context:
            for ctx in cached_context:
                if ctx:
                 messages.append({"role": "user", "content": ctx})
        
        messages.append({"role": "user", "content": user_message})
        
        response = self._client.chat.completions.create(
        model=self.model,
         messages=messages,
            max_tokens=max_tokens
        )
        
        self._update_usage(response.usage)
        
        return response.choices[0].message.content or ""

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
        """Multi-turn function calling loop"""
        max_tokens = kwargs.get('max_tokens', DEFAULT_MAX_TOKENS)
        
        functions = self._convert_tools_to_functions(tools)
        
        messages = [{"role": "system", "content": system}]
        
        if cached_context:
         for ctx in cached_context:
             if ctx:
              messages.append({"role": "user", "content": ctx})
        
        messages.append({"role": "user", "content": user_message})
        result = ToolUseResult()
        text_parts = []
        
        for turn in range(max_iterations):
            result.turns = turn + 1
        
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                functions=functions,
                max_tokens=max_tokens
            )
            
            self._update_usage(response.usage)
            
            choice = response.choices[0]
            result.stop_reason = choice.finish_reason or ""
            
            if choice.message.content:
                text_parts.append(choice.message.content)
        
            if choice.finish_reason == "function_call" and choice.message.function_call:
              func_call = choice.message.function_call
                
              messages.append({
                    "role": "assistant",
                  "content": None,
                    "function_call": {
                        "name": func_call.name,
                   "arguments": func_call.arguments
                    }
             })
              
              try:
                 args = json.loads(func_call.arguments)
                 output = tool_handler(func_call.name, args)
                 is_error = False
              except Exception as exc:
                output = f"[tool_error] {exc}"
                is_error = True
                
                messages.append({
           "role": "function",
              "name": func_call.name,
                    "content": output
                })
            
                result.tool_calls_handled += 1
            else:
             break
        result.text_output = "".join(text_parts)
        return result

    def supports_caching(self) -> bool:
        """OpenAI does not support prompt caching"""
        return False
    def _convert_tools_to_functions(self, tools: List[Dict]) -> List[Dict]:
        """Convert Anthropic tool format to OpenAI function format"""
        functions = []
        for tool in tools:
            functions.append({
                "name": tool["name"],
            "description": tool.get("description", ""),
                "parameters": tool.get("input_schema", {})
            })
        return functions

    def _update_usage(self, usage: Any) -> None:
        """Update usage statistics"""
        self.usage.calls += 1
        self.usage.input_tokens += getattr(usage, "prompt_tokens", 0) or 0
        self.usage.output_tokens += getattr(usage, "completion_tokens", 0) or 0
        # OpenAI does not support caching, so cache tokens are 0
