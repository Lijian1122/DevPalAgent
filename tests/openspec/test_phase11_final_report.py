# -*- coding: utf-8 -*-

from devpal.core.openspec_phases.base import OpenSpecContext
from devpal.core.openspec_phases.phase11_final_report import Phase11FinalReport


def test_phase11_report_includes_test_documentation_and_sandbox_summary(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    doc = project / "docs" / "test_doc.md"
    doc.parent.mkdir()
    doc.write_text("doc", encoding="utf-8")
    context = OpenSpecContext(project_dir=project, requirements_file=tmp_path / "requirements.md")
    context.enable_multi_agent = True
    context.sandbox_level = "staging"
    context.agent_pool_size = 3
    context.agent_backend = "local"
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
                    "metadata": {"sandbox_id": "phase10-test-abc"},
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
    assert "phase10-test-abc" in report
    assert result.data["sandbox_task_count"] == 1
    assert result.data["agent_backend"] == "local"
