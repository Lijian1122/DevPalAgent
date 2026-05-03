# -*- coding: utf-8 -*-
"""
短期记忆 (Short-term Memory)
负责管理对话上下文，支持滑动窗口、重要性排序、自动截断
"""
import re
from typing import List, Dict, Any, Optional
from .base import BaseMemory, MemoryItem


class ShortTermMemory(BaseMemory):
    """短期记忆管理器 - 负责对话上下文管理"""

    def __init__(self, max_tokens: int = 8000, system_prompt: Optional[str] = None):
        super().__init__()
        self.max_tokens = max_tokens
        self.system_prompt: Optional[str] = system_prompt
        self.messages: List[Dict[str, Any]] = []  # 原始消息列表

    def add_user(self, content: str, importance: int = 2) -> None:
        """添加用户消息"""
        self.messages.append({"role": "user", "content": content})
        self._truncate_if_needed()

    def add_assistant(self, content: str, importance: int = 2) -> None:
        """添加助手消息"""
        self.messages.append({"role": "assistant", "content": content})
        self._truncate_if_needed()

    def add_tool_result(self, tool_use_id: str, content: str) -> None:
        """添加单个工具结果（Claude 格式）"""
        self.add_tool_results([{"tool_use_id": tool_use_id, "content": content}])

    def add_tool_results(self, tool_results: List[Dict[str, str]]) -> None:
        """批量添加多个工具结果（Claude 格式）"""
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

    def get_messages(self) -> List[Dict[str, Any]]:
        """获取完整的消息列表（用于发送给 LLM）"""
        return list(self.messages)

    def clear(self) -> None:
        """清空消息历史"""
        self.messages = []

    def get_last(self, n: int = 1) -> List[Dict[str, Any]]:
        """获取最近的 n 条消息"""
        return self.messages[-n:] if self.messages else []

    def add(self, content: str, **kwargs) -> None:
        """兼容基类接口，添加用户消息"""
        role = kwargs.get("role", "user")
        if role == "user":
            self.add_user(content)
        else:
            self.add_assistant(content)

    def retrieve(self, query: str, top_k: int = 5) -> List[MemoryItem]:
        """检索相关记忆，基于关键词匹配"""
        query_words = set(query.lower().split())
        scored_items = []

        for msg in self.messages:
            content = msg.get("content", "")
            if isinstance(content, list):
                text_parts = [
                    item.get("text", "")
                    for item in content
                    if item.get("type") == "text"
                ]
                content = " ".join(text_parts)

            if isinstance(content, str):
                content_words = set(content.lower().split())
                overlap = len(query_words & content_words)
                if overlap > 0:
                    scored_items.append((overlap, MemoryItem(
                        content=content,
                        memory_type="short_term",
                        importance=overlap
                    )))

        scored_items.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored_items[:top_k]]

    def count_tokens_estimate(self) -> int:
        """估算总 token 数量"""
        total = 0
        for msg in self.messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total += self.count_tokens(content)
            elif isinstance(content, list):
                for item in content:
                    if item.get("type") == "text":
                        total += self.count_tokens(item.get("text", ""))
                    elif item.get("type") == "tool_use":
                        total += self.count_tokens(str(item.get("input", "")))
        return total

    def _truncate_if_needed(self) -> None:
        """智能截断，保留系统提示、重要消息、和最新消息"""
        estimated_tokens = self.count_tokens_estimate()
        if estimated_tokens < self.max_tokens * 0.7:
            return

        # 保留最近的 N 条消息，工具调用结果尽量完整保留
        min_messages = 6  # 至少保留 3 轮对话
        if len(self.messages) > min_messages:
            # 保留最近的消息，移除最早的消息
            self.messages = self.messages[-min_messages:]

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
