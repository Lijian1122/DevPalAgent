# -*- coding: utf-8 -*-
"""
Performance Analyzer - 性能分析器

分析工作流性能，识别瓶颈
"""

from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

from .event_bus import Event, EventBus, get_global_event_bus
from .workflow_events import (
    LLMRequestCompletedEvent,
    PhaseCompletedEvent,
    ToolCompletedEvent,
    WorkflowCompletedEvent,
    WorkflowStartedEvent,
)


class PerformanceAnalyzer:
    """性能分析器

    订阅工作流事件并分析性能指标
    """

    def __init__(self, event_bus: Optional[EventBus] = None):
        """初始化性能分析器

        Args:
            event_bus: EventBus 实例，如果为 None 则使用全局实例
        """
        self.event_bus = event_bus or get_global_event_bus()

        # 性能数据
        self.workflow_id: Optional[str] = None
        self.workflow_start_time: Optional[datetime] = None
        self.workflow_end_time: Optional[datetime] = None
        self.workflow_total_duration_ms: int = 0

        # 阶段性能
        self.phase_durations: Dict[int, int] = {}  # phase_num -> duration_ms
        self.phase_names: Dict[int, str] = {}  # phase_num -> phase_name

        # 工具性能
        self.tool_calls: Dict[str, int] = defaultdict(int)  # tool_name -> count
        self.tool_durations: Dict[str, List[int]] = defaultdict(
            list
        )  # tool_name -> [duration_ms]

        # LLM 性能
        self.llm_calls: int = 0
        self.llm_total_tokens: int = 0
        self.llm_prompt_tokens: int = 0
        self.llm_completion_tokens: int = 0
        self.llm_cache_hits: int = 0
        self.llm_cache_misses: int = 0
        self.llm_durations: List[int] = []

        # 订阅事件
        self.event_bus.subscribe(
            event_type="workflow.started", handler=self._on_workflow_started
        )
        self.event_bus.subscribe(
            event_type="phase.completed", handler=self._on_phase_completed
        )
        self.event_bus.subscribe(
            event_type="tool.completed", handler=self._on_tool_completed
        )
        self.event_bus.subscribe(
            event_type="llm.request_completed", handler=self._on_llm_request_completed
        )
        self.event_bus.subscribe(
            event_type="workflow.completed", handler=self._on_workflow_completed
        )

    def _on_workflow_started(self, event: Event) -> None:
        """处理工作流开始事件"""
        if isinstance(event, WorkflowStartedEvent):
            self.workflow_id = event.workflow_id
            self.workflow_start_time = event.timestamp
            self._reset()

    def _on_phase_completed(self, event: Event) -> None:
        """处理阶段完成事件"""
        if isinstance(event, PhaseCompletedEvent):
            self.phase_durations[event.phase_num] = event.duration_ms
            self.phase_names[event.phase_num] = event.phase_name

    def _on_tool_completed(self, event: Event) -> None:
        """处理工具完成事件"""
        if isinstance(event, ToolCompletedEvent):
            self.tool_calls[event.tool_name] += 1
            self.tool_durations[event.tool_name].append(event.duration_ms)

    def _on_llm_request_completed(self, event: Event) -> None:
        """处理 LLM 请求完成事件"""
        if isinstance(event, LLMRequestCompletedEvent):
            self.llm_calls += 1
            self.llm_total_tokens += event.total_tokens
            self.llm_prompt_tokens += event.prompt_tokens
            self.llm_completion_tokens += event.completion_tokens
            self.llm_durations.append(event.duration_ms)

            if event.cache_hit:
                self.llm_cache_hits += 1
            else:
                self.llm_cache_misses += 1

    def _on_workflow_completed(self, event: Event) -> None:
        """处理工作流完成事件"""
        if isinstance(event, WorkflowCompletedEvent):
            self.workflow_end_time = event.timestamp
            self.workflow_total_duration_ms = event.total_duration_ms
            self._print_analysis()

    def _reset(self) -> None:
        """重置统计数据"""
        self.phase_durations.clear()
        self.phase_names.clear()
        self.tool_calls.clear()
        self.tool_durations.clear()
        self.llm_calls = 0
        self.llm_total_tokens = 0
        self.llm_prompt_tokens = 0
        self.llm_completion_tokens = 0
        self.llm_cache_hits = 0
        self.llm_cache_misses = 0
        self.llm_durations.clear()
        self.workflow_total_duration_ms = 0

    def _print_analysis(self) -> None:
        """打印性能分析报告"""
        if not self.workflow_start_time or not self.workflow_end_time:
            return

        total_duration_ms = self.workflow_total_duration_ms
        if total_duration_ms <= 0:
            total_duration_ms = int(
                (self.workflow_end_time - self.workflow_start_time).total_seconds() * 1000
            )
        total_duration_sec = total_duration_ms / 1000

        print("\n" + "=" * 70)
        print("Performance Analysis Report")
        print("=" * 70)
        print()

        # 总体统计
        print(f"Workflow ID: {self.workflow_id[:8] if self.workflow_id else 'N/A'}")
        print(f"Total Duration: {total_duration_sec:.2f}s ({total_duration_ms}ms)")
        print()

        # 阶段性能分析
        if self.phase_durations:
            print("Phase Performance:")
            print("-" * 70)

            # 按耗时排序
            sorted_phases = sorted(
                self.phase_durations.items(), key=lambda x: x[1], reverse=True
            )

            for phase_num, duration_ms in sorted_phases:
                phase_name = self.phase_names.get(phase_num, f"Phase {phase_num}")
                duration_sec = duration_ms / 1000
                percentage = (
                    (duration_ms / total_duration_ms) * 100
                    if total_duration_ms > 0
                    else 0
                )

                # 进度条
                bar_length = 30
                filled = int(bar_length * percentage / 100)
                bar = "#" * filled + "-" * (bar_length - filled)

                print(
                    f"  Phase {phase_num:>4}: {phase_name:25s} {duration_sec:6.2f}s [{bar}] {percentage:5.1f}%"
                )

            # 最慢的阶段
            slowest_phase = sorted_phases[0]
            slowest_name = self.phase_names.get(
                slowest_phase[0], f"Phase {slowest_phase[0]}"
            )
            slowest_duration_sec = slowest_phase[1] / 1000
            slowest_pct = (
                (slowest_phase[1] / total_duration_ms) * 100
                if total_duration_ms > 0
                else 0
            )

            print()
            print(f"  Slowest Phase: Phase {slowest_phase[0]} ({slowest_name})")
            print(
                f"    Duration: {slowest_duration_sec:.2f}s ({slowest_pct:.1f}% of total)"
            )
            print()

        # 工具性能分析
        if self.tool_calls:
            print("Tool Performance:")
            print("-" * 70)

            for tool_name, count in sorted(
                self.tool_calls.items(), key=lambda x: x[1], reverse=True
            ):
                durations = self.tool_durations[tool_name]
                if durations:
                    avg_duration_ms = sum(durations) / len(durations)
                    total_tool_duration_ms = sum(durations)
                    avg_duration_sec = avg_duration_ms / 1000
                    total_tool_duration_sec = total_tool_duration_ms / 1000

            print(
                f"  {tool_name:20s}: {count:3d} calls, avg {avg_duration_sec:.3f}s, total {total_tool_duration_sec:.2f}s"
            )
            print()

        # LLM 性能分析
        if self.llm_calls > 0:
            print("LLM Performance:")
            print("-" * 70)

            avg_duration_ms = (
                sum(self.llm_durations) / len(self.llm_durations)
                if self.llm_durations
                else 0
            )
            avg_duration_sec = avg_duration_ms / 1000
            total_llm_duration_ms = sum(self.llm_durations)
            total_llm_duration_sec = total_llm_duration_ms / 1000

            cache_hit_rate = (
                (self.llm_cache_hits / self.llm_calls) * 100
                if self.llm_calls > 0
                else 0
            )

            print(f"  Total Calls: {self.llm_calls}")
            print(f"  Average Duration: {avg_duration_sec:.3f}s per call")
            print(f"  Total LLM Time: {total_llm_duration_sec:.2f}s")
            print()
            print(f"  Total Tokens: {self.llm_total_tokens:,}")
            print(f"    Prompt Tokens: {self.llm_prompt_tokens:,}")
            print(f"    Completion Tokens: {self.llm_completion_tokens:,}")
            print()
            print("  Cache Performance:")
            print(f"    Cache Hits: {self.llm_cache_hits}")
            print(f"    Cache Misses: {self.llm_cache_misses}")
            print(f"    Hit Rate: {cache_hit_rate:.1f}%")
            print()

        # 性能建议
        print("Performance Recommendations:")
        print("-" * 70)

        recommendations = []

        # 检查慢阶段
        if self.phase_durations:
            slowest_phase = max(self.phase_durations.items(), key=lambda x: x[1])
            slowest_pct = (
                (slowest_phase[1] / total_duration_ms) * 100
                if total_duration_ms > 0
                else 0
            )
            if slowest_pct > 40:
                slowest_name = self.phase_names.get(
                    slowest_phase[0], f"Phase {slowest_phase[0]}"
                )
                recommendations.append(
                    f"Phase {slowest_phase[0]} ({slowest_name}) takes {slowest_pct:.1f}% of total time. Consider optimizing this phase."
                )

        # 检查缓存命中率
        if self.llm_calls > 0:
            cache_hit_rate = (self.llm_cache_hits / self.llm_calls) * 100
            if cache_hit_rate < 50:
                recommendations.append(
                    f"LLM cache hit rate is low ({cache_hit_rate:.1f}%). Consider enabling prompt caching."
                )

        # 检查 LLM 调用次数
        if self.llm_calls > 20:
            recommendations.append(
                f"High number of LLM calls ({self.llm_calls}). Consider batching requests or caching results."
            )

        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        else:
            print("  No performance issues detected. Good job!")

        print()
        print("=" * 70)
        print()

    def get_analysis(self) -> Dict:
        """获取性能分析数据

         Returns:
        包含性能分析数据的字典
        """
        total_duration_ms = self.workflow_total_duration_ms
        if total_duration_ms <= 0 and self.workflow_start_time and self.workflow_end_time:
            total_duration_ms = int(
                (self.workflow_end_time - self.workflow_start_time).total_seconds()
                * 1000
            )

        # 计算工具统计
        tool_stats = {}
        for tool_name, durations in self.tool_durations.items():
            if durations:
                tool_stats[tool_name] = {
                    "count": len(durations),
                    "avg_ms": sum(durations) / len(durations),
                    "total_ms": sum(durations),
                    "min_ms": min(durations),
                    "max_ms": max(durations),
                }

        # 计算 LLM 统计
        llm_stats = {
            "total_calls": self.llm_calls,
            "total_tokens": self.llm_total_tokens,
            "prompt_tokens": self.llm_prompt_tokens,
            "completion_tokens": self.llm_completion_tokens,
            "cache_hits": self.llm_cache_hits,
            "cache_misses": self.llm_cache_misses,
            "cache_hit_rate": (self.llm_cache_hits / self.llm_calls) * 100
            if self.llm_calls > 0
            else 0,
            "avg_duration_ms": sum(self.llm_durations) / len(self.llm_durations)
            if self.llm_durations
            else 0,
        }

        # 找出最慢的阶段
        slowest_phase = None
        if self.phase_durations:
            slowest_phase_tuple = max(self.phase_durations.items(), key=lambda x: x[1])
            slowest_phase = {
                "phase_num": slowest_phase_tuple[0],
                "phase_name": self.phase_names.get(
                    slowest_phase_tuple[0], f"Phase {slowest_phase_tuple[0]}"
                ),
                "duration_ms": slowest_phase_tuple[1],
                "percentage": (slowest_phase_tuple[1] / total_duration_ms) * 100
                if total_duration_ms > 0
                else 0,
            }

        return {
            "workflow_id": self.workflow_id,
            "total_duration_ms": total_duration_ms,
            "phase_durations": self.phase_durations.copy(),
            "phase_names": self.phase_names.copy(),
            "slowest_phase": slowest_phase,
            "tool_stats": tool_stats,
            "llm_stats": llm_stats,
        }


# 使用示例
if __name__ == "__main__":
    import time

    # 创建性能分析器
    analyzer = PerformanceAnalyzer()

    # 模拟工作流事件
    event_bus = get_global_event_bus()

    # 工作流开始
    workflow_event = WorkflowStartedEvent(
        workflow_id="test-workflow-456",
        requirements_file="requirements/test.md",
        project_name="test_project",
        language="python",
        project_type="web",
    )
    event_bus.publish(workflow_event)

    # 模拟几个阶段
    for phase_num in range(1, 4):
        time.sleep(0.1)
        complete_event = PhaseCompletedEvent(
            workflow_id="test-workflow-456",
            phase_num=phase_num,
            phase_name=f"Phase {phase_num}",
            success=True,
            duration_ms=phase_num * 1000,  # 模拟不同耗时
        )
        event_bus.publish(complete_event)

    # 模拟 LLM 调用
    for i in range(5):
        llm_event = LLMRequestCompletedEvent(
            workflow_id="test-workflow-456",
            model="claude-sonnet-4-6",
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
            duration_ms=2000,
            cache_hit=(i % 2 == 0),  # 50% 缓存命中率
            cache_read_tokens=800 if (i % 2 == 0) else 0,
        )
        event_bus.publish(llm_event)

    # 工作流完成
    time.sleep(0.1)
    workflow_complete = WorkflowCompletedEvent(
        workflow_id="test-workflow-456",
        success=True,
        total_duration_ms=6000,
        phases_completed=3,
        phases_failed=0,
        phases_skipped=0,
    )
    event_bus.publish(workflow_complete)

    # 获取分析数据
    analysis = analyzer.get_analysis()
    print(f"\nAnalysis data: {analysis['slowest_phase']}")
