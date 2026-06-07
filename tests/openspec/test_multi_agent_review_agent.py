# -*- coding: utf-8 -*-

from pathlib import Path

from devpal.core.multi_agent import AgentPolicy, AgentTask, ReviewAgent


def _task(tmp_path, file_path):
    return AgentTask(
        task_id="phase9:review:src/app.cpp",
        phase_number=9,
        role="review",
        task_type="code_review",
        input_payload={
            "project_dir": tmp_path,
            "file_path": file_path,
            "check_types": ["todo"],
        },
    )


def test_review_agent_returns_issues_for_valid_file(tmp_path):
    source = tmp_path / "src" / "app.cpp"
    source.parent.mkdir()
    source.write_text("// TODO: fix\n", encoding="utf-8")

    def checker(file_path, check_types):
        return [
            {
                "file": str(file_path),
                "line": 1,
                "severity": "warning",
                "category": "todo",
                "message": "TODO found",
                "suggestion": "Resolve TODO",
            }
        ]

    result = ReviewAgent(AgentPolicy(enabled=True), checker).execute(_task(tmp_path, source))

    assert result.success is True
    assert result.metadata["file_path"] == str(source)
    assert result.metadata["issues"][0]["category"] == "todo"
    assert result.metadata["sandbox"]["sandbox_id"] == result.sandbox_id
    assert Path(result.metadata["manifest_path"]).exists()


def test_review_agent_rejects_path_escape(tmp_path):
    outside = tmp_path.parent / "app.cpp"

    result = ReviewAgent(AgentPolicy(enabled=True), lambda *_: []).execute(_task(tmp_path, outside))

    assert result.success is False
    assert result.policy_violations
    assert Path(result.metadata["manifest_path"]).exists()
    assert "escapes project root" in result.error


def test_review_agent_reports_checker_failure(tmp_path):
    source = tmp_path / "src" / "app.cpp"
    source.parent.mkdir()
    source.write_text("int main() { return 0; }", encoding="utf-8")

    def checker(file_path, check_types):
        raise RuntimeError("checker failed")

    result = ReviewAgent(AgentPolicy(enabled=True), checker).execute(_task(tmp_path, source))

    assert result.success is False
    assert result.error == "checker failed"
    assert result.metadata["issues"] == []
