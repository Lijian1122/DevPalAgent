# -*- coding: utf-8 -*-
"""
EventBus 主流程接入示例

演示如何在 EnhancedOpenSpecScheduler 中集成 EventBus
"""

import uuid
from datetime import datetime
from pathlib import Path

from devpal.core.schema.event_bus import get_global_event_bus
from devpal.core.schema.event_logger import EventLogger, EventStatistics
from devpal.core.schema.workflow_events import (
    AgentCompletedEvent,
    AgentFallbackUsedEvent,
    AgentMergeCompletedEvent,
    AgentStartedEvent,
    ArchiveLifecycleEvent,
    CheckpointCreatedEvent,
    FileTaskCompletedEvent,
    FileTaskFailedEvent,
    FileTaskRetryingEvent,
    FileTaskStartedEvent,
    PhaseCompletedEvent,
    PhaseParallelSummaryEvent,
    PhaseSkippedEvent,
    PhaseStartedEvent,
    SandboxViolationEvent,
    VectorIndexCompletedEvent,
    VectorIndexStartedEvent,
    VectorSearchCompletedEvent,
    VectorSearchStartedEvent,
    WorkflowCompletedEvent,
    WorkflowFailedEvent,
    WorkflowStartedEvent,
)


class EventBusIntegration:
    """EventBus 集成辅助类

    提供便捷方法在 Scheduler 中发出事件
    """

    def _handle_workflow_event(self, handler, event):
        if getattr(event, "workflow_id", None) != self.workflow_id:
            return
        handler(event)

    def __init__(self, requirements_file: str, project_name: str):
        """初始化 EventBus 集成

        Args:
          requirements_file: 需求文件路径
            project_name: 项目名称
        """
        # 生成唯一的工作流 ID
        self.workflow_id = str(uuid.uuid4())
        self.run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.requirements_file = requirements_file
        self.project_name = project_name

        # 获取全局 EventBus 实例
        self.event_bus = get_global_event_bus()

        # 初始化事件日志
        log_file, latest_log_file = self._event_log_paths(project_name)
        self.event_logger = EventLogger(log_file, latest_log_file=latest_log_file)

        # 订阅当前工作流事件并记录
        self.event_bus.subscribe_all(
            handler=lambda event: self._handle_workflow_event(
                self.event_logger.log_event,
                event,
            )
        )

        # 初始化事件统计
        self.event_stats = EventStatistics(workflow_id=self.workflow_id)
        self.event_bus.subscribe_all(
            handler=lambda event: self._handle_workflow_event(
                self.event_stats.process_event,
                event,
            )
        )

        print(f"[EventBus] Initialized for workflow {self.workflow_id[:8]}")
        print(f"[EventBus] Event log: {log_file}")
        print(f"[EventBus] Latest event log: {latest_log_file}")

    def _event_log_paths(self, project_name: str) -> tuple[Path, Path]:
        spec_dir = Path(project_name) / ".spec"
        run_log = spec_dir / "events" / f"{self.run_timestamp}_{self.workflow_id[:8]}.jsonl"
        latest_log = spec_dir / "events.jsonl"
        return run_log, latest_log

    def update_project_name(self, new_project_name: str):
        """Update project name and event log path after Phase 2 determines actual name

        Args:
               new_project_name: The actual project name from Phase 2
        """
        if new_project_name == self.project_name:
            return  # No change needed

        old_log_file = self.event_logger.log_file
        old_latest_log_file = self.event_logger.latest_log_file
        new_log_file, new_latest_log_file = self._event_log_paths(new_project_name)

        # Update project name
        self.project_name = new_project_name

        # Update event logger path
        self.event_logger.log_file = new_log_file
        self.event_logger.latest_log_file = new_latest_log_file

        # If old log files exist and have content, move them to new location
        for old_path, new_path in [
            (old_log_file, new_log_file),
            (old_latest_log_file, new_latest_log_file),
        ]:
            if old_path and old_path.exists() and old_path.stat().st_size > 0:
                new_path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    old_content = old_path.read_text(encoding="utf-8")
                    new_path.write_text(old_content, encoding="utf-8")
                    old_path.unlink()
                    print(f"[EventBus] Migrated event log: {old_path} -> {new_path}")
                except Exception as e:
                    print(f"[EventBus] Warning: Failed to migrate event log: {e}")
            elif new_path:
                new_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"[EventBus] Updated event log path: {new_log_file}")

    def emit_workflow_started(self, language: str, project_type: str):
        """发出工作流开始事件"""
        event = WorkflowStartedEvent(
            workflow_id=self.workflow_id,
            requirements_file=self.requirements_file,
            project_name=self.project_name,
            language=language,
            project_type=project_type,
        )
        self.event_bus.publish(event)
        print(f"[EventBus] Workflow started: {self.workflow_id[:8]}")

    def emit_workflow_completed(
        self,
        success: bool,
        phases_completed: int,
        phases_failed: int,
        phases_skipped: int,
    ):
        """发出工作流完成事件"""
        summary = self.event_stats.get_summary()

        event = WorkflowCompletedEvent(
            workflow_id=self.workflow_id,
            success=success,
            total_duration_ms=summary.get("total_duration_ms", 0),
            phases_completed=phases_completed,
            phases_failed=phases_failed,
            phases_skipped=phases_skipped,
            statistics=summary,
        )
        self.event_bus.publish(event)
        print(f"[EventBus] Workflow completed: success={success}")

    def emit_workflow_failed(self, error: str, failed_phase: int = None):
        """发出工作流失败事件"""
        event = WorkflowFailedEvent(
            workflow_id=self.workflow_id, error=error, failed_phase=failed_phase
        )
        self.event_bus.publish(event)
        print(f"[EventBus] Workflow failed at phase {failed_phase}: {error}")

    def emit_phase_started(self, phase_num: int, phase_name: str):
        """发出阶段开始事件"""
        event = PhaseStartedEvent(
            workflow_id=self.workflow_id, phase_num=phase_num, phase_name=phase_name
        )
        self.event_bus.publish(event)

    def emit_phase_completed(
        self,
        phase_num: int,
        phase_name: str,
        success: bool,
        duration_ms: int,
        result_summary: str = "",
        artifacts: list = None,
    ):
        """发出阶段完成事件"""
        event = PhaseCompletedEvent(
            workflow_id=self.workflow_id,
            phase_num=phase_num,
            phase_name=phase_name,
            success=success,
            duration_ms=duration_ms,
            result_summary=result_summary,
            artifacts=artifacts or [],
        )
        self.event_bus.publish(event)

    def emit_phase_skipped(self, phase_num: int, phase_name: str, skip_reason: str):
        """发出阶段跳过事件"""
        event = PhaseSkippedEvent(
            workflow_id=self.workflow_id,
            phase_num=phase_num,
            phase_name=phase_name,
            skip_reason=skip_reason,
        )
        self.event_bus.publish(event)

    def emit_checkpoint_created(self, checkpoint_file: str, phase_num: int):
        """发出 checkpoint 创建事件"""
        event = CheckpointCreatedEvent(
            workflow_id=self.workflow_id,
            checkpoint_file=checkpoint_file,
            phase_num=phase_num,
        )
        self.event_bus.publish(event)

    def emit_file_task_started(self, phase_num: int, task_id: str, task_type: str, path: str = "", retry_count: int = 0):
        event = FileTaskStartedEvent(
            workflow_id=self.workflow_id,
            phase_num=phase_num,
            task_id=task_id,
            task_type=task_type,
            path=path,
            retry_count=retry_count,
        )
        self.event_bus.publish(event)

    def emit_file_task_completed(self, phase_num: int, task_id: str, task_type: str, path: str = "", duration_ms: int = 0, retry_count: int = 0):
        event = FileTaskCompletedEvent(
            workflow_id=self.workflow_id,
            phase_num=phase_num,
            task_id=task_id,
            task_type=task_type,
            path=path,
            duration_ms=duration_ms,
            retry_count=retry_count,
            success=True,
        )
        self.event_bus.publish(event)

    def emit_file_task_failed(self, phase_num: int, task_id: str, task_type: str, path: str = "", duration_ms: int = 0, retry_count: int = 0, error: str = ""):
        event = FileTaskFailedEvent(
            workflow_id=self.workflow_id,
            phase_num=phase_num,
            task_id=task_id,
            task_type=task_type,
            path=path,
            duration_ms=duration_ms,
            retry_count=retry_count,
            error=error,
        )
        self.event_bus.publish(event)

    def emit_file_task_retrying(self, phase_num: int, task_id: str, task_type: str, path: str = "", retry_count: int = 0, error: str = ""):
        event = FileTaskRetryingEvent(
            workflow_id=self.workflow_id,
            phase_num=phase_num,
            task_id=task_id,
            task_type=task_type,
            path=path,
            retry_count=retry_count,
            error=error,
        )
        self.event_bus.publish(event)

    def emit_phase_parallel_summary(self, phase_num: int, summary: dict, max_concurrency: int):
        event = PhaseParallelSummaryEvent(
            workflow_id=self.workflow_id,
            phase_num=phase_num,
            total_tasks=int(summary.get("total_tasks", 0) or 0),
            success_count=int(summary.get("success_count", 0) or 0),
            failed_count=int(summary.get("failed_count", 0) or 0),
            retry_count=int(summary.get("retry_count", 0) or 0),
            max_concurrency=max_concurrency,
            total_task_duration_ms=int(summary.get("total_task_duration_ms", 0) or 0),
        )
        self.event_bus.publish(event)

    def emit_agent_started(self, phase_num: int, task_id: str, role: str, task_type: str, sandbox_id: str = ""):
        event = AgentStartedEvent(
            workflow_id=self.workflow_id,
            phase_num=phase_num,
            task_id=task_id,
            role=role,
            task_type=task_type,
            sandbox_id=sandbox_id,
        )
        self.event_bus.publish(event)

    def emit_agent_completed(
        self,
        phase_num: int,
        task_id: str,
        role: str,
        task_type: str,
        sandbox_id: str = "",
        success: bool = True,
        duration_ms: int = 0,
        error: str = "",
    ):
        event = AgentCompletedEvent(
            workflow_id=self.workflow_id,
            phase_num=phase_num,
            task_id=task_id,
            role=role,
            task_type=task_type,
            sandbox_id=sandbox_id,
            success=success,
            duration_ms=duration_ms,
            error=error,
        )
        self.event_bus.publish(event)

    def emit_agent_merge_completed(
        self,
        phase_num: int,
        task_id: str,
        sandbox_id: str = "",
        artifact_path: str = "",
        success: bool = True,
        error: str = "",
    ):
        event = AgentMergeCompletedEvent(
            workflow_id=self.workflow_id,
            phase_num=phase_num,
            task_id=task_id,
            sandbox_id=sandbox_id,
            artifact_path=artifact_path,
            success=success,
            error=error,
        )
        self.event_bus.publish(event)

    def emit_agent_fallback_used(self, phase_num: int, reason: str, fallback: str):
        event = AgentFallbackUsedEvent(
            workflow_id=self.workflow_id,
            phase_num=phase_num,
            reason=reason,
            fallback=fallback,
        )
        self.event_bus.publish(event)

    def emit_sandbox_violation(
        self,
        phase_num: int,
        task_id: str,
        sandbox_id: str = "",
        reason: str = "",
        path: str = "",
        command: list | None = None,
    ):
        event = SandboxViolationEvent(
            workflow_id=self.workflow_id,
            phase_num=phase_num,
            task_id=task_id,
            sandbox_id=sandbox_id,
            reason=reason,
            path=path,
            command=command or [],
        )
        self.event_bus.publish(event)

    def emit_vector_index_started(self, project_name: str, artifact_types: list = None):
        event = VectorIndexStartedEvent(
            workflow_id=self.workflow_id,
            project_name=project_name,
            artifact_types=artifact_types or [],
        )
        self.event_bus.publish(event)

    def emit_vector_index_completed(self, project_name: str, indexed_documents: int, duration_ms: int):
        event = VectorIndexCompletedEvent(
            workflow_id=self.workflow_id,
            project_name=project_name,
            indexed_documents=indexed_documents,
            duration_ms=duration_ms,
        )
        self.event_bus.publish(event)

    def emit_vector_search_started(self, project_name: str, top_k: int, artifact_types: list = None):
        event = VectorSearchStartedEvent(
            workflow_id=self.workflow_id,
            project_name=project_name,
            top_k=top_k,
            artifact_types=artifact_types or [],
        )
        self.event_bus.publish(event)

    def emit_vector_search_completed(self, project_name: str, top_k: int, result_count: int, retrieval_latency_ms: int, fallback: bool = False):
        event = VectorSearchCompletedEvent(
            workflow_id=self.workflow_id,
            project_name=project_name,
            top_k=top_k,
            result_count=result_count,
            retrieval_latency_ms=retrieval_latency_ms,
            fallback=fallback,
        )
        self.event_bus.publish(event)

    def emit_archive_event(self, event_name: str, payload: dict):
        event = ArchiveLifecycleEvent(
            workflow_id=self.workflow_id,
            change_id=str(payload.get("change_id", "")),
            archive_event=event_name,
            payload=payload,
        )
        self.event_bus.publish(event)

    def get_statistics_summary(self) -> dict:
        """获取事件统计摘要"""
        return self.event_stats.get_summary()


# ==================================
# 使用示例：如何在 Scheduler 中集成
# ===================


def example_scheduler_integration():
    """Demo: How to integrate EventBus in EnhancedOpenSpecScheduler

    Integration points:
    1. __init__() - Initialize EventBusIntegration
    2. run_all_phases() - Emit workflow_started event
    3. _run_phases_with_enhancements() - Emit phase_started/completed events
    4. checkpoint.save() - Emit checkpoint_created event
    5. Exception handling - Emit workflow_failed event
    """

    # 1. 在 Scheduler __init__ 中初始化
    event_integration = EventBusIntegration(
        requirements_file="requirements/test.md", project_name="test_project"
    )

    # 2. 在 run_all_phases 开始时发出事件
    event_integration.emit_workflow_started(language="python", project_type="web")

    # 3. 在每个 Phase 执行前后发出事件
    phase_num = 4
    phase_name = "Generate Code"

    # Phase 开始
    event_integration.emit_phase_started(phase_num, phase_name)

    # 执行 Phase (模拟)
    import time

    start_time = time.time()
    # ... 实际的 Phase 执行代码 ...
    duration_ms = int((time.time() - start_time) * 1000)

    # Phase 完成
    event_integration.emit_phase_completed(
        phase_num=phase_num,
        phase_name=phase_name,
        success=True,
        duration_ms=duration_ms,
        result_summary="Generated 10 files",
        artifacts=["src/main.py", "src/utils.py"],
    )

    # 4. Phase 跳过示例
    event_integration.emit_phase_skipped(
        phase_num=6,
        phase_name="CMake Config",
        skip_reason="Python project does not need CMake",
    )

    # 5. Checkpoint 创建示例
    event_integration.emit_checkpoint_created(
        checkpoint_file="test_project/.spec/checkpoint.json", phase_num=4
    )

    # 6. 工作流完成
    event_integration.emit_workflow_completed(
        success=True, phases_completed=9, phases_failed=0, phases_skipped=2
    )

    # 7. 获取统计摘要
    summary = event_integration.get_statistics_summary()
    print("\n[EventBus] Statistics Summary:")
    print(f"  Total events: {summary['total_events']}")
    print(f"  Total duration: {summary['total_duration_ms']}ms")
    print(f"  Phase durations: {summary['phase_durations']}")

    return event_integration


if __name__ == "__main__":
    print("=" * 70)
    print("EventBus Integration Example")
    print("=" * 70)
    print()

    integration = example_scheduler_integration()

    print()
    print("=" * 70)
    print("Integration example completed successfully!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Add EventBusIntegration to EnhancedOpenSpecScheduler.__init__()")
    print("2. Call emit_workflow_started() in run_all_phases()")
    print("3. Call emit_phase_started/completed() around each phase execution")
    print("4. Call emit_checkpoint_created() after checkpoint.save()")
    print("5. Call emit_workflow_completed() at the end")
