# -*- coding: utf-8 -*-

from devpal.core.openspec_phases.base import OpenSpecContext
from devpal.core.openspec_phases.phase11_final_report import Phase11FinalReport


class _FallbackStats:
    def get_statistics_summary(self):
        return {
            "agent_fallbacks": {"phase4.serial_tool_loop": 1},
            "agent_fallback_details": [
                {
                    "phase_num": 4,
                    "fallback": "phase4.serial_tool_loop",
                    "reason": "multi-agent generation failed",
                }
            ],
        }


def test_phase11_report_includes_test_documentation_and_sandbox_summary(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    doc = project / "docs" / "test_doc.md"
    doc.parent.mkdir()
    doc.write_text("doc", encoding="utf-8")
    context = OpenSpecContext(project_dir=project, requirements_file=tmp_path / "requirements.md")
    context.enable_multi_agent = True
    context.sandbox_level = "staging"
    context.sandbox_backend = "windows_process"
    context.agent_pool_size = 3
    context.agent_backend = "local"
    context.event_integration = _FallbackStats()
    manifest_v1 = project / ".spec" / "sandboxes" / "phase10-test-abc" / "manifest.json"
    manifest_v2 = project / ".spec" / "sandboxes" / "phase10-test-abc" / "manifest.v2.json"
    runner_request = project / ".spec" / "sandboxes" / "phase10-test-abc" / "runner_request.json"
    runner_result = project / ".spec" / "sandboxes" / "phase10-test-abc" / "runner_result.json"
    context.test_doc_summary = {
        "phase": 5,
        "test_count": 2,
        "docs_generated": 1,
        "doc_paths": [str(doc)],
        "errors": ["failed to generate one doc"],
    }
    context.parallel_execution_stats = {
        "10": {
            "total_tasks": 1,
            "success_count": 1,
            "failed_count": 0,
            "retry_count": 0,
            "max_concurrency": 1,
            "fallback_used": False,
            "total_task_duration_ms": 12,
            "results": [
                {
                    "task_id": "phase10:python:pytest",
                    "success": True,
                    "duration_ms": 12,
                    "metadata": {
                        "sandbox_id": "phase10-test-abc",
                        "backend": "windows_process",
                        "isolation_level": "process",
                        "manifest_path": str(manifest_v1),
                        "manifest_v2_path": str(manifest_v2),
                        "runner_request_path": str(runner_request),
                        "runner_result_path": str(runner_result),
                        "cleanup_status": "clean",
                        "timed_out": False,
                    },
                }
            ],
        }
    }

    result = Phase11FinalReport(context).execute()
    report = (project / "docs" / "final_report.md").read_text(encoding="utf-8")

    assert result.success is True
    assert "Test Documentation" in report
    assert "test_doc.md" in report
    assert "failed to generate one doc" in report
    assert "Multi-Agent Sandbox Summary" in report
    assert "Multi-agent enabled: True" in report
    assert "Sandbox execution enabled: True" in report
    assert "phase10-test-abc" in report
    assert ".spec/sandboxes/phase10-test-abc/manifest.json" in report
    assert ".spec/sandboxes/phase10-test-abc/manifest.v2.json" in report
    assert ".spec/sandboxes/phase10-test-abc/runner_result.json" in report
    assert "windows_process" in report
    assert "process" in report
    assert "clean" in report
    assert "Fallback Events" in report
    assert "phase4.serial_tool_loop" in report
    assert result.data["sandbox_task_count"] == 1
    assert result.data["sandbox_backend"] == "windows_process"
    assert result.data["agent_backend"] == "local"


def test_phase11_report_includes_requirement_status_rows(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    context = OpenSpecContext(project_dir=project, requirements_file=tmp_path / "requirements.md")
    context.structured_requirements = [{"id": "REQ-001", "title": "Login"}]
    context.update_requirement_status("REQ-001", "VERIFIED")

    result = Phase11FinalReport(context).execute()
    report = (project / "docs" / "final_report.md").read_text(encoding="utf-8")

    assert result.success is True
    assert "### Requirement Status" in report
    assert "`REQ-001`: VERIFIED" in report
    assert "**VERIFIED**: 1" in report
