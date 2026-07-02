# -*- coding: utf-8 -*-
"""
EventBus 集成测试

测试 EventBus 在完整工作流中的集成
"""

import tempfile
from pathlib import Path

import pytest

from devpal.core.schema.event_bus import EventBus
from devpal.core.schema.event_logger import EventLogger, EventStatistics
from devpal.core.schema.eventbus_integration import EventBusIntegration
from devpal.core.schema.performance_analyzer import PerformanceAnalyzer
from devpal.core.schema.progress_monitor import ProgressMonitor
from devpal.core.schema.workflow_events import (
    FileGeneratedEvent,
    LLMRequestCompletedEvent,
    PhaseCompletedEvent,
    PhaseStartedEvent,
    ValidationCompletedEvent,
    ValidationStartedEvent,
    WorkflowCompletedEvent,
    WorkflowStartedEvent,
)


class TestEventBusIntegration:
    """EventBus 集成测试"""

    def test_full_workflow_integration(self):
        """测试完整工作流的事件集成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "events.jsonl"
            event_bus = EventBus(event_store_path=log_file)
            logger = EventLogger(log_file)
            stats = EventStatistics()

            # 订阅所有事件
            event_bus.subscribe_all(handler=logger.log_event)
            event_bus.subscribe_all(handler=stats.process_event)

            workflow_id = "test-workflow-integration"

            # 1. 工作流开始
            workflow_start = WorkflowStartedEvent(
                workflow_id=workflow_id,
                requirements_file="requirements/test.md",
                project_name="test_project",
                language="python",
                project_type="web",
            )
            event_bus.publish(workflow_start)

            # 2. Phase 4: 文件生成
            phase4_start = PhaseStartedEvent(
                workflow_id=workflow_id, phase_num=4, phase_name="Generate Code"
            )
            event_bus.publish(phase4_start)

            # 生成几个文件
            for i in range(3):
                file_event = FileGeneratedEvent(
                    workflow_id=workflow_id,
                    phase_num=4,
                    file_path=f"src/file{i}.py",
                    file_type="source",
                    lines_of_code=100 + i * 10,
                    language="python",
                    generated_by="phase4",
                )
                event_bus.publish(file_event)

            # LLM 请求
            llm_event = LLMRequestCompletedEvent(
                workflow_id=workflow_id,
                model="claude-sonnet-4-6",
                prompt_tokens=1000,
                completion_tokens=500,
                total_tokens=1500,
                duration_ms=2000,
                cache_hit=True,
                cache_read_tokens=800,
            )
            event_bus.publish(llm_event)

            phase4_complete = PhaseCompletedEvent(
                workflow_id=workflow_id,
                phase_num=4,
                phase_name="Generate Code",
                success=True,
                duration_ms=5000,
                result_summary="Generated 3 files",
                artifacts=["src/file0.py", "src/file1.py", "src/file2.py"],
            )
            event_bus.publish(phase4_complete)

            # 3. Phase 9: 验证
            phase9_start = PhaseStartedEvent(
                workflow_id=workflow_id, phase_num=9, phase_name="Quality Gate"
            )
            event_bus.publish(phase9_start)

            validation_start = ValidationStartedEvent(
                workflow_id=workflow_id,
                phase_num=9,
                validation_layers=["format", "semantic"],
                files_to_validate=3,
            )
            event_bus.publish(validation_start)

            validation_complete = ValidationCompletedEvent(
                workflow_id=workflow_id,
                phase_num=9,
                total_issues=2,
                issues_by_layer={"format": 1, "semantic": 1},
                passed=True,
            )
            event_bus.publish(validation_complete)

            phase9_complete = PhaseCompletedEvent(
                workflow_id=workflow_id,
                phase_num=9,
                phase_name="Quality Gate",
                success=True,
                duration_ms=3000,
            )
            event_bus.publish(phase9_complete)

            # 4. 工作流完成
            workflow_complete = WorkflowCompletedEvent(
                workflow_id=workflow_id,
                success=True,
                total_duration_ms=8000,
                phases_completed=2,
                phases_failed=0,
                phases_skipped=0,
            )
            event_bus.publish(workflow_complete)

            # 验证事件日志
            events = logger.read_events()
            assert len(events) >= 10  # 至少 10 个事件

            # 验证统计
            summary = stats.get_summary()
            assert summary["total_events"] >= 10
            assert len(summary["phase_durations"]) == 2
            assert summary["phase_durations"][4] == 5000
            assert summary["phase_durations"][9] == 3000
            assert summary["llm_stats"]["total_calls"] == 1
            assert summary["llm_stats"]["cache_hit_rate"] == 1.0

    def test_eventbus_integration_helper(self):
        """测试 EventBusIntegration 辅助类"""
        with tempfile.TemporaryDirectory() as tmpdir:
            integration = EventBusIntegration(
                requirements_file="requirements/test.md", project_name=tmpdir
            )

            integration.emit_workflow_started(language="python", project_type="web")
            integration.emit_phase_started(4, "Generate Code")
            integration.emit_phase_completed(
                phase_num=4,
                phase_name="Generate Code",
                success=True,
                duration_ms=5000,
                result_summary="Generated 10 files",
                artifacts=["src/main.py"],
            )
            integration.emit_file_task_started(4, "phase4:src/main.py", "code_file", "src/main.py")
            integration.emit_file_task_completed(
                4,
                "phase4:src/main.py",
                "code_file",
                "src/main.py",
                duration_ms=120,
            )
            integration.emit_phase_parallel_summary(
                4,
                {
                    "total_tasks": 1,
                    "success_count": 1,
                    "failed_count": 0,
                    "retry_count": 0,
                    "total_task_duration_ms": 120,
                },
                max_concurrency=2,
            )
            integration.emit_vector_index_started("demo", ["source"])
            integration.emit_vector_index_completed("demo", indexed_documents=3, duration_ms=5)
            integration.emit_vector_search_started("demo", top_k=2, artifact_types=["source"])
            integration.emit_vector_search_completed("demo", top_k=2, result_count=1, retrieval_latency_ms=4)
            integration.emit_agent_started(4, "phase4:src/main.py", "codegen", "code_file", "sandbox-1")
            integration.emit_agent_completed(
                4,
                "phase4:src/main.py",
                "codegen",
                "code_file",
                sandbox_id="sandbox-1",
                success=True,
                duration_ms=42,
            )
            integration.emit_agent_merge_completed(
                4,
                "phase4:src/main.py",
                sandbox_id="sandbox-1",
                artifact_path="src/main.py",
            )
            integration.emit_agent_fallback_used(
                4,
                reason="multi-agent generation failed",
                fallback="phase4.serial_tool_loop",
            )
            integration.emit_sandbox_violation(
                10,
                "phase10:test",
                sandbox_id="sandbox-2",
                reason="denied command",
                command=["curl", "https://example.com"],
            )
            integration.emit_sandbox_created(
                10,
                "phase10:python:pytest",
                sandbox_id="sandbox-3",
                backend="windows_process",
                isolation_level="process",
                manifest_path=".spec/sandboxes/sandbox-3/manifest.v2.json",
            )
            integration.emit_sandbox_policy_applied(
                10,
                "phase10:python:pytest",
                sandbox_id="sandbox-3",
                backend="windows_process",
                isolation_level="process",
                policy={"sandbox_level": "strict"},
            )
            integration.emit_sandbox_command_started(
                10,
                "phase10:python:pytest",
                sandbox_id="sandbox-3",
                backend="windows_process",
                isolation_level="process",
                command=["pytest", "tests", "-v"],
                cwd=".",
            )
            integration.emit_sandbox_command_completed(
                10,
                "phase10:python:pytest",
                sandbox_id="sandbox-3",
                backend="windows_process",
                isolation_level="process",
                command=["pytest", "tests", "-v"],
                returncode=0,
                duration_ms=7,
                manifest_path=".spec/sandboxes/sandbox-3/manifest.v2.json",
                runner_request_path=".spec/sandboxes/sandbox-3/runner_request.json",
                runner_result_path=".spec/sandboxes/sandbox-3/runner_result.json",
                cleanup_status="clean",
            )
            integration.emit_sandbox_cleanup_completed(
                10,
                "phase10:python:pytest",
                sandbox_id="sandbox-3",
                backend="windows_process",
                isolation_level="process",
                cleanup_status="clean",
                manifest_path=".spec/sandboxes/sandbox-3/manifest.v2.json",
            )
            integration.emit_workflow_completed(
                success=True, phases_completed=1, phases_failed=0, phases_skipped=0
            )

            summary = integration.get_statistics_summary()
            assert summary["total_events"] >= 4
            assert len(summary["phase_durations"]) == 1
            assert summary["phase_durations"][4] == 5000
            assert summary["agent_fallbacks"]["phase4.serial_tool_loop"] == 1
            assert summary["agent_fallback_details"][0]["reason"] == "multi-agent generation failed"
            run_log = integration.event_logger.log_file
            latest_log = integration.event_logger.latest_log_file
            assert run_log.parent.name == "events"
            assert run_log.name.endswith(f"_{integration.workflow_id[:8]}.jsonl")
            assert latest_log == Path(tmpdir) / ".spec" / "events.jsonl"
            assert run_log.exists()
            assert latest_log.exists()
            log_content = run_log.read_text(encoding="utf-8")
            assert log_content == latest_log.read_text(encoding="utf-8")
            assert "file_task.started" in log_content
            assert "file_task.completed" in log_content
            assert "phase.parallel_summary" in log_content
            assert "vector.index_started" in log_content
            assert "vector.index_completed" in log_content
            assert "vector.search_started" in log_content
            assert "vector.search_completed" in log_content
            assert "agent.started" in log_content
            assert "agent.completed" in log_content
            assert "agent.merge_completed" in log_content
            assert "agent.fallback_used" in log_content
            assert "sandbox.violation" in log_content
            assert "sandbox.created" in log_content
            assert "sandbox.policy_applied" in log_content
            assert "sandbox.command_started" in log_content
            assert "sandbox.command_completed" in log_content
            assert "sandbox.cleanup_completed" in log_content
            assert "windows_process" in log_content

    def test_eventbus_integration_filters_other_workflows(self):
        """测试 EventBusIntegration 只统计当前 workflow_id 的事件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            integration = EventBusIntegration(
                requirements_file="requirements/test.md", project_name=tmpdir
            )
            integration.emit_workflow_started(language="python", project_type="web")
            integration.emit_phase_completed(
                phase_num=4,
                phase_name="Generate Code",
                success=True,
                duration_ms=5000,
            )

            other_event = PhaseCompletedEvent(
                workflow_id="other-workflow",
                phase_num=9,
                phase_name="Quality Gate",
                success=True,
                duration_ms=9000,
            )
            integration.event_bus.publish(other_event)

            summary = integration.get_statistics_summary()
            assert summary["phase_durations"] == {4: 5000}
            assert summary["event_counts"]["phase.completed"] == 1

    def test_progress_monitor_integration(self):
        """测试 ProgressMonitor 集成"""
        event_bus = EventBus()
        monitor = ProgressMonitor(event_bus=event_bus, total_phases=3)

        workflow_id = "test-progress"

        # 工作流开始
        event_bus.publish(
            WorkflowStartedEvent(
                workflow_id=workflow_id,
                requirements_file="test.md",
                project_name="test",
                language="python",
                project_type="web",
            )
        )

        # 执行几个阶段
        for phase_num in range(1, 4):
            event_bus.publish(
                PhaseStartedEvent(
                    workflow_id=workflow_id,
                    phase_num=phase_num,
                    phase_name=f"Phase {phase_num}",
                )
            )

            event_bus.publish(
                PhaseCompletedEvent(
                    workflow_id=workflow_id,
                    phase_num=phase_num,
                    phase_name=f"Phase {phase_num}",
                    success=True,
                    duration_ms=1000,
                )
            )

        # 工作流完成
        event_bus.publish(
            WorkflowCompletedEvent(
                workflow_id=workflow_id,
                success=True,
                total_duration_ms=3000,
                phases_completed=3,
                phases_failed=0,
                phases_skipped=0,
            )
        )

        # 验证进度
        progress = monitor.get_progress()
        assert progress["workflow_id"] == workflow_id
        assert progress["completed_phases"] == 3
        assert progress["progress_percent"] == 100.0
        assert len(progress["phase_durations"]) == 3

    def test_performance_analyzer_integration(self):
        """测试 PerformanceAnalyzer 集成"""
        event_bus = EventBus()
        analyzer = PerformanceAnalyzer(event_bus=event_bus)

        workflow_id = "test-performance"

        # 工作流开始
        event_bus.publish(
            WorkflowStartedEvent(
                workflow_id=workflow_id,
                requirements_file="test.md",
                project_name="test",
                language="python",
                project_type="web",
            )
        )

        # 执行几个阶段（不同耗时）
        for phase_num in range(1, 4):
            event_bus.publish(
                PhaseCompletedEvent(
                    workflow_id=workflow_id,
                    phase_num=phase_num,
                    phase_name=f"Phase {phase_num}",
                    success=True,
                    duration_ms=phase_num * 1000,  # 1s, 2s, 3s
                )
            )

        # LLM 调用
        for i in range(5):
            event_bus.publish(
                LLMRequestCompletedEvent(
                    workflow_id=workflow_id,
                    model="claude-sonnet-4-6",
                    prompt_tokens=1000,
                    completion_tokens=500,
                    total_tokens=1500,
                    duration_ms=2000,
                    cache_hit=(i % 2 == 0),  # 60% 缓存命中率
                    cache_read_tokens=800 if (i % 2 == 0) else 0,
                )
            )

        # 工作流完成
        event_bus.publish(
            WorkflowCompletedEvent(
                workflow_id=workflow_id,
                success=True,
                total_duration_ms=6000,
                phases_completed=3,
                phases_failed=0,
                phases_skipped=0,
            )
        )

        # 验证分析
        analysis = analyzer.get_analysis()
        assert analysis["workflow_id"] == workflow_id
        assert analysis["total_duration_ms"] == 6000
        assert len(analysis["phase_durations"]) == 3
        assert analysis["slowest_phase"]["phase_num"] == 3
        assert analysis["slowest_phase"]["duration_ms"] == 3000
        assert analysis["llm_stats"]["total_calls"] == 5
        assert analysis["llm_stats"]["cache_hit_rate"] == 60.0

    def test_event_filtering(self):
        """测试事件过滤"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "events.jsonl"
            event_bus = EventBus()
            logger = EventLogger(log_file)

            event_bus.subscribe_all(handler=logger.log_event)

            workflow_id = "test-filter"

            # 发出多种类型的事件
            event_bus.publish(
                WorkflowStartedEvent(
                    workflow_id=workflow_id,
                    requirements_file="test.md",
                    project_name="test",
                    language="python",
                    project_type="web",
                )
            )

            for phase_num in range(1, 4):
                event_bus.publish(
                    PhaseCompletedEvent(
                        workflow_id=workflow_id,
                        phase_num=phase_num,
                        phase_name=f"Phase {phase_num}",
                        success=True,
                        duration_ms=1000,
                    )
                )

            event_bus.publish(
                WorkflowCompletedEvent(
                    workflow_id=workflow_id,
                    success=True,
                    total_duration_ms=3000,
                    phases_completed=3,
                    phases_failed=0,
                    phases_skipped=0,
                )
            )

            # 过滤读取
            all_events = logger.read_events()
            assert len(all_events) == 5  # 1 start + 3 phase + 1 complete

            phase_events = logger.read_events(event_type="phase.completed")
            assert len(phase_events) == 3

            workflow_events = logger.read_events(event_type="workflow.started")
            assert len(workflow_events) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
