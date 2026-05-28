# -*- coding: utf-8 -*-
"""
事件日志记录器和统计分析器

提供事件持久化、统计分析和查询功能
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from .event_bus import Event
from .workflow_events import (
    LLMRequestCompletedEvent,
    PhaseCompletedEvent,
    ToolCompletedEvent,
    WorkflowEventType,
)


class EventLogger:
    """事件日志记录器 将事件持久化到 JSONL 文件"""

    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log_event(self, event: Event):
        """记录事件到文件"""
        event_dict = self._event_to_ordered_dict(event)

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event_dict, ensure_ascii=False, default=str) + "\n")

    @staticmethod
    def _event_to_ordered_dict(event: Event) -> Dict[str, Any]:
        ordered_keys = [
            "event_id",
            "source",
            "phase_name",
            "event_type",
            "timestamp",
            "priority",
            "scope",
            "metadata",
        ]
        base_values = {
            "event_id": event.event_id,
            "source": event.source,
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "priority": event.priority.value,
            "scope": event.scope.value,
            "metadata": event.metadata,
        }
        event_dict = {}

        for key in ordered_keys:
            if key in base_values:
                event_dict[key] = base_values[key]
            elif hasattr(event, key):
                event_dict[key] = getattr(event, key)

        for key, value in event.__dict__.items():
            if key not in event_dict and not key.startswith("_"):
                event_dict[key] = value

        return event_dict

    def read_events(
        self,
        event_type: Optional[str] = None,
        source: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """读取事件日志"""
        events = []

        if not self.log_file.exists():
            return events

        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    event_dict = json.loads(line)

                    # 过滤
                    if event_type and event_dict.get("event_type") != event_type:
                        continue
                    if source and event_dict.get("source") != source:
                        continue

                    events.append(event_dict)

                    if limit and len(events) >= limit:
                        break
                except json.JSONDecodeError:
                    continue

        return events

    def clear(self):
        """清空日志文件"""
        if self.log_file.exists():
            self.log_file.unlink()


class EventStatistics:
    """事件统计分析器

    实时收集和分析事件统计数据
    """

    def __init__(self, workflow_id: Optional[str] = None):
        self.workflow_id = workflow_id
        self.event_counts = defaultdict(int)
        self.phase_durations = {}
        self.tool_calls = defaultdict(int)
        self.tool_durations = defaultdict(list)
        self.llm_tokens = {
            "prompt": 0,
            "completion": 0,
            "total": 0,
            "cache_creation": 0,
            "cache_read": 0,
        }
        self.llm_calls = []
        self.workflow_start_time = None
        self.workflow_end_time = None
        self.workflow_total_duration_ms = 0

    def process_event(self, event: Event):
        """处理事件并更新统计"""
        if self.workflow_id and getattr(event, "workflow_id", None) != self.workflow_id:
            return

        self.event_counts[event.event_type] += 1

        # 工作流时间
        if event.event_type == WorkflowEventType.WORKFLOW_STARTED.value:
            self.workflow_start_time = event.timestamp
        elif event.event_type == WorkflowEventType.WORKFLOW_COMPLETED.value:
            self.workflow_end_time = event.timestamp
            self.workflow_total_duration_ms = getattr(event, "total_duration_ms", 0) or 0

        # 阶段耗时
        if isinstance(event, PhaseCompletedEvent):
            self.phase_durations[event.phase_num] = event.duration_ms

        # 工具调用
        if event.event_type == WorkflowEventType.TOOL_CALLED.value:
            tool_name = getattr(event, "tool_name", "unknown")
            self.tool_calls[tool_name] += 1

        if isinstance(event, ToolCompletedEvent):
            self.tool_durations[event.tool_name].append(event.duration_ms)

        # LLM 统计
        if isinstance(event, LLMRequestCompletedEvent):
            self.llm_tokens["prompt"] += event.prompt_tokens
            self.llm_tokens["completion"] += event.completion_tokens
            self.llm_tokens["total"] += event.total_tokens
            self.llm_tokens["cache_creation"] += event.cache_creation_tokens
            self.llm_tokens["cache_read"] += event.cache_read_tokens

            self.llm_calls.append(
                {
                    "model": event.model,
                    "duration_ms": event.duration_ms,
                    "tokens": event.total_tokens,
                    "cache_hit": event.cache_hit,
                }
            )

    def get_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
        # 计算总耗时
        total_duration_ms = self.workflow_total_duration_ms
        if total_duration_ms <= 0 and self.workflow_start_time and self.workflow_end_time:
            total_duration_ms = int(
                (self.workflow_end_time - self.workflow_start_time).total_seconds()
                * 1000
            )

        # 工具统计
        tool_stats = {}
        for tool, durations in self.tool_durations.items():
            if durations:
                tool_stats[tool] = {
                    "count": len(durations),
                    "avg_ms": sum(durations) / len(durations),
                    "total_ms": sum(durations),
                    "min_ms": min(durations),
                    "max_ms": max(durations),
                }

        # LLM 统计
        llm_stats = {
            "total_calls": len(self.llm_calls),
            "total_tokens": self.llm_tokens["total"],
            "prompt_tokens": self.llm_tokens["prompt"],
            "completion_tokens": self.llm_tokens["completion"],
            "cache_creation_tokens": self.llm_tokens["cache_creation"],
            "cache_read_tokens": self.llm_tokens["cache_read"],
        }

        if self.llm_calls:
            llm_stats["cache_hit_rate"] = sum(
                1 for call in self.llm_calls if call["cache_hit"]
            ) / len(self.llm_calls)
            llm_stats["avg_duration_ms"] = sum(
                call["duration_ms"] for call in self.llm_calls
            ) / len(self.llm_calls)
        else:
            llm_stats["cache_hit_rate"] = 0.0
            llm_stats["avg_duration_ms"] = 0.0

        return {
            "total_events": sum(self.event_counts.values()),
            "event_counts": dict(self.event_counts),
            "total_duration_ms": total_duration_ms,
            "phase_durations": self.phase_durations,
            "slowest_phase": max(self.phase_durations.items(), key=lambda x: x[1])
            if self.phase_durations
            else None,
            "tool_stats": tool_stats,
            "llm_stats": llm_stats,
        }

    def reset(self):
        """重置统计"""
        self.event_counts.clear()
        self.phase_durations.clear()
        self.tool_calls.clear()
        self.tool_durations.clear()
        self.llm_tokens = {
            "prompt": 0,
            "completion": 0,
            "total": 0,
            "cache_creation": 0,
            "cache_read": 0,
        }
        self.llm_calls.clear()
        self.workflow_start_time = None
        self.workflow_end_time = None
        self.workflow_total_duration_ms = 0


class EventFilter:
    """事件过滤器"""

    def __init__(
        self,
        event_types: Optional[List[str]] = None,
        source_pattern: Optional[str] = None,
        phase_nums: Optional[List[int]] = None,
    ):
        self.event_types = event_types
        self.source_pattern = source_pattern
        self.phase_nums = phase_nums

    def matches(self, event: Event) -> bool:
        """判断事件是否匹配过滤条件"""
        if self.event_types and event.event_type not in self.event_types:
            return False

        if self.source_pattern and not event.source.startswith(self.source_pattern):
            return False

        if self.phase_nums:
            phase_num = getattr(event, "phase_num", None)
            if phase_num not in self.phase_nums:
                return False

        return True
