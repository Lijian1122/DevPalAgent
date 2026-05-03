# -*- coding: utf-8 -*-
"""
记忆系统 - 基础定义
三层记忆架构：短期记忆、长期记忆、错误记忆
"""
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class MemoryItem:
    """记忆项的基础数据结构"""
    content: str
    memory_type: str  # "short_term", "long_term", "error"
    importance: int = 1  # 重要程度，1-10
    timestamp: float = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItem':
        return cls(**data)


class BaseMemory:
    """记忆基类，定义通用接口"""

    def __init__(self, persist_path: Optional[str] = None):
        self.persist_path = Path(persist_path) if persist_path else None
        self._ensure_persist_dir()

    def _ensure_persist_dir(self) -> None:
        """确保持久化目录存在"""
        if self.persist_path:
            self.persist_path.parent.mkdir(parents=True, exist_ok=True)

    def add(self, content: str, **kwargs) -> None:
        """添加一条记忆，子类实现"""
        raise NotImplementedError

    def retrieve(self, query: str, top_k: int = 5) -> List[MemoryItem]:
        """检索相关记忆，子类实现"""
        raise NotImplementedError

    def clear(self) -> None:
        """清空记忆，子类实现"""
        raise NotImplementedError

    def _save_to_disk(self, data: Any) -> None:
        """保存数据到磁盘"""
        if self.persist_path:
            with open(self.persist_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_from_disk(self, default: Any = None) -> Any:
        """从磁盘加载数据"""
        if self.persist_path and self.persist_path.exists():
            try:
                with open(self.persist_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return default or []

    def count_tokens(self, text: str) -> int:
        """简单的 Token 估算，英文平均 4 字符 = 1 token，中文约 2 字符 = 1 token"""
        return len(text) // 3

    def get_context_prompt(self, query: str) -> str:
        """获取用于 LLM 的记忆上下文提示"""
        memories = self.retrieve(query)
        if not memories:
            return ""
        context_parts = [f"- {mem.content}" for mem in memories]
        return "\n".join(context_parts)
