# -*- coding: utf-8 -*-
"""
长期记忆 (Long-term Memory)
轻量级实现：关键词加权匹配，零依赖向量数据库
支持：用户偏好、历史经验、知识积累
"""
import time
from typing import List, Dict, Any, Optional
from .base import BaseMemory, MemoryItem


class LongTermMemory(BaseMemory):
    """长期记忆管理器 - 持久化存储用户偏好、历史经验"""

    MEMORY_TYPES = {
        "user_preference": "用户偏好",
        "experience": "任务经验",
        "knowledge": "代码知识",
        "pattern": "行为模式",
    }

    def __init__(self, persist_path: str = "./data/long_term_memory.json"):
        super().__init__(persist_path)
        self.memories: List[MemoryItem] = self._load()

    def _load(self) -> List[MemoryItem]:
        """从磁盘加载记忆"""
        data = self._load_from_disk([])
        return [MemoryItem.from_dict(item) for item in data]

    def _save(self) -> None:
        """保存记忆到磁盘"""
        data = [item.to_dict() for item in self.memories]
        self._save_to_disk(data)

    def add(
        self,
        content: str,
        memory_type: str = "experience",
        importance: int = 3,
        **kwargs
    ) -> None:
        """
        添加一条长期记忆
        Args:
            content: 记忆内容
            memory_type: 记忆类型：user_preference / experience / knowledge / pattern
            importance: 重要程度 1-10
            **kwargs: 其他元数据
        """
        if memory_type not in self.MEMORY_TYPES:
            raise ValueError(f"记忆类型必须是: {list(self.MEMORY_TYPES.keys())}")

        # 避免重复：如果内容高度相似就不重复添加
        if self._is_duplicate(content):
            return

        item = MemoryItem(
            content=content,
            memory_type=memory_type,
            importance=importance,
            metadata=kwargs
        )
        self.memories.append(item)
        self._save()

    def add_user_preference(self, preference: str, importance: int = 5) -> None:
        """添加用户偏好"""
        self.add(preference, "user_preference", importance)

    def add_experience(self, experience: str, importance: int = 4) -> None:
        """添加任务经验"""
        self.add(experience, "experience", importance)

    def add_knowledge(self, knowledge: str, importance: int = 4) -> None:
        """添加代码知识"""
        self.add(knowledge, "knowledge", importance)

    def retrieve(
        self,
        query: str,
        memory_type: Optional[str] = None,
        top_k: int = 5
    ) -> List[MemoryItem]:
        """
        检索相关记忆，基于关键词 + 时间 + 重要性加权"""
        query_words = set(query.lower().split())
        scored_items = []

        for item in self.memories:
            # 类型过滤
            if memory_type and item.memory_type != memory_type:
                continue

            # 关键词匹配分数
            content_words = set(item.content.lower().split())
            overlap = len(query_words & content_words)

            # 时间衰减：越新分数越高
            age_days = (time.time() - item.timestamp) / 86400
            recency = 1.0 / (1 + age_days)

            # 重要性加权
            importance_weight = item.importance / 5.0

            # 综合评分
            score = overlap * 0.5 + recency * 0.3 + importance_weight * 0.2

            if overlap > 0 or score > 0.2:  # 有匹配或者分数不错
                scored_items.append((score, item))

        scored_items.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored_items[:top_k]]

    def get_relevant_context(self, query: str) -> str:
        """获取查询相关的记忆上下文，用于注入 LLM system prompt"""
        # 分别检索偏好
        preferences = self.retrieve(query, memory_type="user_preference", top_k=3)
        experiences = self.retrieve(query, memory_type="experience", top_k=3)
        knowledge = self.retrieve(query, memory_type="knowledge", top_k=2)

        context_parts = []

        if preferences:
            context_parts.append("[User Preferences]")
            for p in preferences:
                context_parts.append(f"- {p.content}")

        if experiences:
            context_parts.append("\n[Past Experience]")
            for e in experiences:
                context_parts.append(f"- {e.content}")

        if knowledge:
            context_parts.append("\n[Relevant Knowledge]")
            for k in knowledge:
                context_parts.append(f"- {k.content}")

        return "\n".join(context_parts) if context_parts else ""

    def clear(self) -> None:
        """清空所有记忆"""
        self.memories = []
        self._save()

    def get_by_type(self, memory_type: str) -> List[MemoryItem]:
        """按类型获取所有记忆"""
        return [m for m in self.memories if m.memory_type == memory_type]

    def get_all(self) -> List[MemoryItem]:
        """获取所有记忆"""
        return list(self.memories)

    def _is_duplicate(self, content: str, threshold: float = 0.8) -> bool:
        """简单的重复检测，避免重复添加相似内容"""
        content_lower = content.lower()
        content_words = set(content_lower.split())

        for mem in self.memories:
            mem_words = set(mem.content.lower().split())
            if not content_words or not mem_words:
                continue
            similarity = len(content_words & mem_words) / len(content_words | mem_words)
            if similarity > threshold:
                return True
        return False

    def __len__(self) -> int:
        return len(self.memories)
