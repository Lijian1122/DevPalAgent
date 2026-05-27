# -*- coding: utf-8 -*-
"""
EventBus 工作流事件单元测试
"""

import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import json

from devpal.core.schema.event_bus import EventBus
from devpal.core.schema.workflow_events import (
    WorkflowStartedEvent,
    WorkflowCompletedEvent,
    PhaseStartedEvent,
    PhaseCompletedEvent,
    ToolCalledEvent,
    LLMRequestCompletedEvent,
    WorkflowEventType
)
from devpal.core.schema.event_logger import EventLogger, EventStatistics


class TestWorkflowEvents:
    """工作流事件测试"""

    def test_workflow_started_event(self):
        """测试工作流开始事件"""
        event = WorkflowStartedEvent(
            workflow_id="test-workflow-1",
            requirements_file="requirements/test.md",
            project_name="test_project",
            language="python",
            project_type="web"
        )

        assert event.event_type == WorkflowEventType.WORKFLOW_STARTED.value
        assert event.workflow_id == "test-workflow-1"
        assert event.source == "scheduler"

    def test_phase_completed_event(self):
        """测试阶段完成事件"""
        event = PhaseCompletedEvent(
            workflow_id="test-workflow-1",
            phase_num=4,
            phase_name="Generate Code",
         success=True,
            duration_ms=5000,
            result_summary="Generated 10 files",
            artifacts=["src/main.py", "src/utils.py"]
        )

        assert event.event_type == WorkflowEventType.PHASE_COMPLETED.value
        assert event.phase_num == 4
      assert event.source == "phase4"
        assert len(event.artifacts) == 2

    def test_llm_request_completed_event(self):
        """测试 LLM 请求完成事件"
        event = LLMRequestCompletedEvent(
            workflow_id="test-workflow-1",
            model="claude-sonnet-4-6",
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
            duration_ms=2000,
            cache_hit=True,
            cache_read_tokens=800
      )

        assert event.event_type == WorkflowEventType.LLM_REQUEST_COMPLETED.value
        assert event.cache_hit is True
        assert event.total_tokens == 1500


class TestEventLogger:
    """事件日志记录器测试"""

    def test_log_and_read_events(self):
        """测试事件记录和读取""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "events.jsonl"
            logger = EventLogger(log_file)

            # 记录事件
            event1 = WorkflowStartedEvent(
          workflow_id="test-1",
                requirements_file="test.md",
                project_name="test",
            language="python",
          project_type="web"
         )
     logger.log_event(event1)

            event2 = PhaseCompletedEvent(
                workflow_id="test-1",
           phase_num=4,
         phase_name="Generate Code",
       success=True,
                duration_ms=5000
            )
            logger.log_event(event2)

            # 读取事件
            events = logger.read_events()
            assert len(events) == 2
          assert events[0]['workflow_id'] == "test-1"
        assert events[1]['phase_num'] == 4

    def test_filter_events(self):
        """测试事件过滤"""
        with tempfile.TemporaryDirectory() as tmpdir:
      log_file = Path(tmpdir) / "events.jsonl"
            logger = EventLogger(log_file)

            # 记录多个事件
            for i in range(5):
                event = PhaseCompletedEvent(
                workflow_id="test-1",
             phase_num=i + 1,
                    phase_name=f"Phase {i+1}",
            success=True,
                duration_ms=1000
                )
                logger.log_event(event)

            # 过滤读取
            events = logger.read_events(
                event_type=WorkflowEventType.PHASE_COMPLETED.value,
                limit=3
            )
          assert len(events) == 3


class TestEventStatistics:
    """事件统计测试"""

    def test_phase_duration_stats(self):
        ""测试阶段耗时统计"""
        stats = EventStatistics()

        # 处理阶段完成事件
        for i in range(1, 4):
            event = PhaseCompletedEvent(
                workflow_id="test-1",
                phase_num=i,
                phase_name=f"Phase {i}",
             success=True,
                duration_ms=i * 1000
            )
        stats.process_event(event)

        summary = stats.get_summary()
        assert len(summary['phase_durations']) == 3
        assert summary['phase_durations'][1] == 1000
        assert summary['phase_durations'][3] == 3000
        assert summary['slowest_phase'] == (3, 3000)

    def test_llm_token_stats(self):
        """测试 LLM token 统计"""
        stats = EventStatistics()

      # 处理 LLM 请求事件
        event1 = LLMRequestCompletedEvent(
            workflow_id="test-1",
         model="claude-sonnet-4-6",
            prompt_tokens=1000,
        completion_tokens=500,
            total_tokens=1500,
            duration_ms=2000,
       cache_hit=False
        )
        stats.process_event(event1)
        event2 = LLMRequestCompletedEvent(
            workflow_id="test-1",
          model="claude-sonnet-4-6",
            prompt_tokens=800,
            completion_tokens=400,
            total_tokens=1200,
            duration_ms=1500,
          cache_hit=True,
        cache_read_tokens=600
     )
        stats.process_event(event2)

      summary = stats.get_summary()
        llm_stats = summary['llm_stats']

        assert llm_stats['total_calls'] == 2
        assert llm_stats['total_tokens'] == 2700
        assert llm_stats['prompt_tokens'] == 1800
        assert llm_stats['completion_tokens'] == 900
        assert llm_stats['cache_hit_rate'] == 0.5  # 1/2

    def test_tool_call_stats(self):
        """测试工具调用统计"""
        stats = EventStatistics()

        # 处理工具调用事件
        event1 = ToolCalledEvent(
            workflow_id="test-1",
            tool_name="file_writer",
            caller="phase4"
    )
        stats.process_event(event1)

        event2 = ToolCalledEvent(
        workflow_id="test-1",
            tool_name="file_writer",
            caller="phase4"
        )
      stats.process_event(event2)

        event3 = ToolCalledEvent(
            workflow_id="test-1",
            tool_name="code_validator",
         caller="phase9"
        )
        stats.process_event(event3)

        summary = stats.get_summary()
    assert summary['event_counts'][WorkflowEventType.TOOL_CALLED.value] == 3


class TestEventBusIntegration:
    """EventBus 集成测试"""

    def test_publish_and_subscribe(self):
        """测试发布订阅"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "events.jsonl"
            event_bus = EventBus(event_store_path=log_file)

         # 订阅事件
          received_events = []

            def handler(event):
             received_events.append(event)

            event_bus.subscribe(
                event_type=WorkflowEventType.PHASE_COMPLETED.value,
              handler=handler
            )

            # 发布事件
            event = PhaseCompletedEvent(
                workflow_id="test-1",
              phase_num=4,
         phase_name="Generate Code",
             success=True,
                duration_ms=5000
            )
            event_bus.publish(event)

            # 验证
            assert len(received_events) == 1
       assert received_events[0].phase_num == 4

    def test_event_logger_integration(self):
        """测试事件日志集成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "events.jsonl"
         event_bus = EventBus(event_store_path=log_file)
          logger = EventLogger(log_file)

          # 订阅所有事件并记录
            event_bus.subscribe_all(handler=logger.log_event)

            # 发布事件
            event1 = WorkflowStartedEvent(
           workflow_id="test-1",
                requirements_file="test.md",
                project_name="test",
        language="python",
            project_type="web"
            )
            event_bus.publish(event1)

            event2 = PhaseCompletedEvent(
          workflow_id="test-1",
                phase_num=4,
          phase_name="Generate Code",
                success=True,
            duration_ms=5000
            )
            event_bus.publish(event2)

            # 读取日志
            events = logger.read_events()
            assert len(events) == 2

    def test_event_statistics_integration(self):
        """测试事件统计集成"""
        event_bus = EventBus()
        stats = EventStatistics()

        # 订阅所有事件并统计
        event_bus.subscribe_all(handler=stats.process_event)

        # 发布工作流开始事件
        start_event = WorkflowStartedEvent(
            workflow_id="test-1",
            requirements_file="test.md",
         project_name="test",
            language="python",
            project_type="web"
        )
        event_bus.publish(start_event)

        # 发布阶段完成事件
        for i in range(1, 4):
            event = PhaseCompletedEvent(
            workflow_id="test-1",
          phase_num=i,
            phase_name=f"Phase {i}",
            success=True,
           duration_ms=i * 1000
         )
            event_bus.publish(event)

        # 发布工作流完成事件
        end_event = WorkflowCompletedEvent(
            workflow_id="test-1",
            success=True,
      total_duration_ms=10000,
            phases_completed=3
        )
        event_bus.publish(end_event)

        # 获取统计
        summary = stats.get_summary()
        assert summary['total_events'] == 5
        assert len(summary['phase_durations']) == 3
        assert summary['total_duration_ms'] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
