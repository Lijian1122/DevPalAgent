# -*- coding: utf-8 -*-
"""
Cache Strategy - Prompt Caching 策略和 Metrics 计算

提供缓存指标计算、统计输出和可观测性支持。
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any
from pathlib import Path
import json


@dataclass
class CacheMetrics:
    """缓存统计指标"""
    cache_hit_rate: float
    cache_read_tokens: int
    cache_creation_tokens: int
    total_input_tokens: int
    total_cache_tokens: int
    cost_reduction_percentage: float
    phases: Dict[str, Dict[str, int]]

    @classmethod
    def from_context(cls, context) -> "CacheMetrics":
        """从 OpenSpecContext 计算缓存指标

        Args:
          context: OpenSpecContext 实例

        Returns:
         CacheMetrics 实例
        """
        cache_read = context.llm_cache_read_tokens
        cache_creation = context.llm_cache_creation_tokens
        input_tokens = context.llm_input_tokens

        # 总缓存 tokens
        total_cache = cache_read + cache_creation

        # 缓存命中率
        cache_hit_rate = (
            cache_read / total_cache
            if total_cache > 0 else 0.0
        )

        # 成本降低百分比（缓存读取便宜 90%）
        if total_cache > 0:
         # 节省的 tokens（缓存读取便宜 90%）
            saved_tokens = cache_read * 0.9
            # 原始成本（如果没有缓存）
            original_cost_tokens = input_tokens + total_cache
            # 成本降低比例
            cost_reduction = saved_tokens / original_cost_tokens if original_cost_tokens > 0 else 0.0
        else:
            cost_reduction = 0.0

        # 按阶段统计（如果有的话）
        phases = getattr(context, 'phase_cache_stats', {})

        return cls(
            cache_hit_rate=cache_hit_rate,
            cache_read_tokens=cache_read,
            cache_creation_tokens=cache_creation,
            total_input_tokens=input_tokens,
            total_cache_tokens=total_cache,
          cost_reduction_percentage=cost_reduction,
          phases=phases
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    def save_to_file(self, file_path: Path) -> None:
        """保存到 JSON 文件

        Args:
            file_path: 目标文件路径
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
         json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    def format_summary(self) -> str:
        """格式化为可读摘要

        Returns:
            格式化的摘要字符串
        """
        return f"""Cache Performance Summary:
- Cache Hit Rate: {self.cache_hit_rate:.1%}
- Cache Read Tokens: {self.cache_read_tokens:,}
- Cache Creation Tokens: {self.cache_creation_tokens:,}
- Total Input Tokens: {self.total_input_tokens:,}
- Cost Reduction: {self.cost_reduction_percentage:.1%}""".strip()
