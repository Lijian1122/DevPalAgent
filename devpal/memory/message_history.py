# -*- coding: utf-8 -*-
"""
消息历史管理
处理多轮对话的消息管理、Token 截断、摘要压缩
"""
import re
from typing import List, Dict, Any, Optional


class MessageHistory:
    """消息历史管理器 - 支持多轮对话和上下文管理"""

    def __init__(self, max_tokens: int = 8000, system_prompt: Optional[str] = None):
        self.max_tokens = max_tokens
        self.messages: List[Dict[str, Any]] = []
        self._system_prompt: Optional[str] = system_prompt

    @property
    def system_prompt(self) -> Optional[str]:
        return self._system_prompt

    @system_prompt.setter
    def system_prompt(self, value: str):
        self._system_prompt = value

    def add_user(self, content: str) -> None:
        """添加用户消息"""
        self.messages.append({"role": "user", "content": content})
        self._truncate_if_needed()

    def add_assistant(self, content: str) -> None:
        """添加助手消息"""
        self.messages.append({"role": "assistant", "content": content})
        self._truncate_if_needed()

    def add_tool_result(self, tool_use_id: str, content: str) -> None:
        """添加单个工具结果（Claude 格式）"""
        self.add_tool_results([{"tool_use_id": tool_use_id, "content": content}])

    def add_tool_results(self, tool_results: List[Dict[str, str]]) -> None:
        """批量添加多个工具结果（Claude 格式）
        tool_results 格式: [{"tool_use_id": "xxx", "content": "xxx"}, ...]
        """
        content = []
        for result in tool_results:
            content.append({
                "type": "tool_result",
                "tool_use_id": result["tool_use_id"],
                "content": result["content"]
            })
        self.messages.append({"role": "user", "content": content})
        self._truncate_if_needed()

    def add_tool_use_message(self, text_content: str, tool_calls: List[Dict]) -> None:
        """添加包含 tool_use 的 assistant 消息"""
        content = []
        if text_content:
            content.append({"type": "text", "text": text_content})

        for tc in tool_calls:
            content.append({
                "type": "tool_use",
                "id": tc["id"],
                "name": tc["name"],
                "input": tc["input"]
            })

        self.messages.append({"role": "assistant", "content": content})
        self._truncate_if_needed()

    def get_messages(self, include_system: bool = True) -> List[Dict[str, Any]]:
        """获取完整的消息列表（用于发送给 LLM）"""
        result = []
        # System prompt 由 LLM 客户端单独设置，不在消息列表里
        return result + self.messages

    def clear(self) -> None:
        """清空消息历史"""
        self.messages = []

    def get_last(self, n: int = 1) -> List[Dict[str, Any]]:
        """获取最近的 n 条消息"""
        return self.messages[-n:] if self.messages else []

    def count_tokens_estimate(self) -> int:
        """估算 token 数量（简化版）"""
        total = 0
        for msg in self.messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total += len(content) // 4
            elif isinstance(content, list):
                # 混合内容（text + tool_use）
                for item in content:
                    if item.get("type") == "text":
                        total += len(item.get("text", "")) // 4
                    elif item.get("type") == "tool_use":
                        total += len(str(item.get("input", ""))) // 4
        return total

    def _truncate_if_needed(self) -> None:
        """截断策略：如果 token 过多，保留最新的消息，旧消息做摘要"""
        estimated_tokens = self.count_tokens_estimate()
        if estimated_tokens > self.max_tokens * 0.7:
            # 只保留最近的消息
            keep_count = max(4, len(self.messages) // 2)
            self.messages = self.messages[-keep_count:]

    def get_conversation_summary(self) -> str:
        """生成对话摘要"""
        if not self.messages:
            return "暂无对话历史"

        summary_lines = [f"共 {len(self.messages)} 条消息"]
        for i, msg in enumerate(self.messages[-5:]):
            role = msg["role"]
            content = msg.get("content", "")
            if isinstance(content, str):
                preview = content[:50] + ("..." if len(content) > 50 else "")
            else:
                preview = f"[混合内容，{len(content)} 项]"
            summary_lines.append(f"{i + 1}. {role}: {preview}")

        return "\n".join(summary_lines)

    def __len__(self) -> int:
        return len(self.messages)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        return self.messages[idx]
