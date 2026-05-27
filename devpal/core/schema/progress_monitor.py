# -*- coding: utf-8 -*-
"""
Progress Monitor - 实时进度监控器

订阅工作流事件并显示实时进度
"""

import time
from datetime import datetime
from typing import Dict, Optional

from .event_bus import Event, EventBus, get_global_event_bus
from .workflow_events import (
    PhaseCompletedEvent,
    PhaseStartedEvent,
    WorkflowCompletedEvent,
    WorkflowStartedEvent,
)


class ProgressMonitor:
    """实时进度监控器
    订阅工作流事件并显示实时进度条和统计信息
    """

    def __init__(self, event_bus: Optional[EventBus] = None, total_phases: int = 11):
        """初始化进度监控器

        Args:
            event_bus: EventBus 实例，如果为 None 则使用全局实例
            total_phases: 总阶段数，默认 11 (OpenSpec 标准流程)
        """
        self.event_bus = event_bus or get_global_event_bus()
        self.total_phases = total_phases

        # 状态追踪
        self.workflow_id: Optional[str] = None
        self.workflow_start_time: Optional[datetime] = None
        self.current_phase: Optional[int] = None
        self.phase_start_time: Optional[datetime] = None
        self.completed_phases: int = 0
        self.failed_phases: int = 0

        # 阶段耗时记录
        self.phase_durations: Dict[int, int] = {}  # phase_num -> duration_ms

        # 订阅事件
        self.event_bus.subscribe(
            event_type="workflow.started", handler=self._on_workflow_started
        )
        self.event_bus.subscribe(
            event_type="phase.started", handler=self._on_phase_started
        )
        self.event_bus.subscribe(
            event_type="phase.completed", handler=self._on_phase_completed
        )
        self.event_bus.subscribe(
            event_type="workflow.completed", handler=self._on_workflow_completed
        )

    def _on_workflow_started(self, event: Event) -> None:
        """处理工作流开始事件"""
        if isinstance(event, WorkflowStartedEvent):
            self.workflow_id = event.workflow_id
            self.workflow_start_time = event.timestamp
            self.completed_phases = 0
            self.failed_phases = 0
            self.phase_durations.clear()

            print(f"\n[ProgressMonitor] Workflow started: {event.workflow_id[:8]}")
            print(f"  Project: {event.project_name}")
            print(f"  Language: {event.language}")
            print(f"  Type: {event.project_type}")
            print()

    def _on_phase_started(self, event: Event) -> None:
        """处理阶段开始事件"""
        if isinstance(event, PhaseStartedEvent):
            self.current_phase = event.phase_num
            self.phase_start_time = event.timestamp

            # 计算进度百分比
            progress_pct = (self.completed_phases / self.total_phases) * 100

            # 显示进度条
            bar_length = 20
            filled = int(bar_length * self.completed_phases / self.total_phases)
            bar = "=" * filled + ">" + " " * (bar_length - filled - 1)

            print(
                f"[{bar}] {progress_pct:3.0f}% Phase {event.phase_num}: {event.phase_name}"
            )

    def _on_phase_completed(self, event: Event) -> None:
        """处理阶段完成事件"""
        if isinstance(event, PhaseCompletedEvent):
            self.completed_phases += 1
            self.phase_durations[event.phase_num] = event.duration_ms

            # 计算进度百分比
            progress_pct = (self.completed_phases / self.total_phases) * 100

            # 显示完成状态
            bar_length = 20
            filled = int(bar_length * self.completed_phases / self.total_phases)
            bar = "=" * filled + " " * (bar_length - filled)

            status = "OK" if event.success else "FAIL"
            duration_sec = event.duration_ms / 1000

            print(
                f"[{bar}] {progress_pct:3.0f}% Phase {event.phase_num}: {event.phase_name} - {status} ({duration_sec:.1f}s)"
            )

            # 估算剩余时间
            if self.completed_phases > 0 and self.workflow_start_time:
                elapsed_ms = (
                    event.timestamp - self.workflow_start_time
                ).total_seconds() * 1000
                avg_phase_ms = elapsed_ms / self.completed_phases
                remaining_phases = self.total_phases - self.completed_phases
                estimated_remaining_ms = avg_phase_ms * remaining_phases
                estimated_remaining_sec = estimated_remaining_ms / 1000
                if remaining_phases > 0:
                    print(f"  Estimated remaining time: {estimated_remaining_sec:.1f}s")

    def _on_workflow_completed(self, event: Event) -> None:
        """处理工作流完成事件"""

        if isinstance(event, WorkflowCompletedEvent):
            total_duration_sec = event.total_duration_ms / 1000

            print()
            print(f"[ProgressMonitor] Workflow completed: {event.workflow_id[:8]}")
            print(f"  Status: {'SUCCESS' if event.success else 'FAILED'}")
            print(f"  Total duration: {total_duration_sec:.1f}s")
            print(f"  Phases completed: {event.phases_completed}")
            print(f"  Phases failed: {event.phases_failed}")
            print(f"  Phases skipped: {event.phases_skipped}")

            # 显示最慢的阶段
            if self.phase_durations:
                slowest_phase = max(self.phase_durations.items(), key=lambda x: x[1])
                slowest_duration_sec = slowest_phase[1] / 1000
                slowest_pct = (
                    (slowest_phase[1] / event.total_duration_ms) * 100
                    if event.total_duration_ms > 0
                    else 0
                )
                print(
                    f"  Slowest phase: Phase {slowest_phase[0]} ({slowest_duration_sec:.1f}s, {slowest_pct:.1f}% of total)"
                )
        print()

    def get_progress(self) -> Dict:
        """获取当前进度信息

        Returns:
          包含进度信息的字典
        """
        progress_pct = (
            (self.completed_phases / self.total_phases) * 100
            if self.total_phases > 0
            else 0
        )

        elapsed_ms = 0
        if self.workflow_start_time:
            elapsed_ms = int(
                (datetime.now() - self.workflow_start_time).total_seconds() * 1000
            )

        return {
            "workflow_id": self.workflow_id,
            "total_phases": self.total_phases,
            "completed_phases": self.completed_phases,
            "failed_phases": self.failed_phases,
            "current_phase": self.current_phase,
            "progress_percent": progress_pct,
            "elapsed_ms": elapsed_ms,
            "phase_durations": self.phase_durations.copy(),
        }


# 使用示例
if __name__ == "__main__":
    # 创建进度监控器
    monitor = ProgressMonitor()

    # 模拟工作流事件
    event_bus = get_global_event_bus()

    # 发出工作流开始事件
    workflow_event = WorkflowStartedEvent(
        workflow_id="test-workflow-123",
        requirements_file="requirements/test.md",
        project_name="test_project",
        language="python",
        project_type="web",
    )
    event_bus.publish(workflow_event)

    # 模拟几个阶段
    for phase_num in range(1, 4):
        # 阶段开始
        start_event = PhaseStartedEvent(
            workflow_id="test-workflow-123",
            phase_num=phase_num,
            phase_name=f"Phase {phase_num}",
        )
        event_bus.publish(start_event)

        # 模拟执行
        time.sleep(0.5)

        # 阶段完成
        complete_event = PhaseCompletedEvent(
            workflow_id="test-workflow-123",
            phase_num=phase_num,
            phase_name=f"Phase {phase_num}",
            success=True,
            duration_ms=500,
        )
        event_bus.publish(complete_event)

    # 工作流完成
    workflow_complete = WorkflowCompletedEvent(
        workflow_id="test-workflow-123",
        success=True,
        total_duration_ms=1500,
        phases_completed=3,
        phases_failed=0,
        phases_skipped=0,
    )
    event_bus.publish(workflow_complete)

    # 获取进度信息
    progress = monitor.get_progress()
    print(f"\nFinal progress: {progress['progress_percent']:.1f}%")
