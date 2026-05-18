# -*- coding: utf-8 -*-

import json
from pathlib import Path

from devpal.core.openspec_phases.base import OpenSpecContext, PhaseResult
from devpal.core.openspec_phases.phase1_parse_requirements import Phase1ParseRequirements
from devpal.core.openspec_phases.phase11_final_report import Phase11FinalReport
from devpal.core.openspec_phases.phase2_create_structure import Phase2CreateStructure


class _ToolResult:
    def __init__(self, success=True, content="", error_message=""):
        self.success = success
        self.content = content
        self.error_message = error_message


class _FileReaderRegistry:
    def __init__(self, content):
        self.content = content

    def execute_tool(self, name, args):
        assert name == "file_reader"
        return _ToolResult(content=self.content)


class _DummyRegistry:
    pass


def test_phase1_extracts_structured_requirements(tmp_path):
    content = """# Login

## REQ-001: 用户登录

**描述**: 用户可以登录。

**验收标准**:
- [ ] 用户名和密码正确时登录成功
- [ ] 密码错误时登录失败
"""
    context = OpenSpecContext(project_dir=tmp_path / "out", requirements_file=tmp_path / "requirements.md")
    phase = Phase1ParseRequirements(context, _FileReaderRegistry(content))

    result = phase.execute()

    assert result.success
    reqs = context.structured_requirements
    assert len(reqs) == 1
    req = reqs[0]
    assert req["id"] == "REQ-001"
    assert req["title"] == "用户登录"
    assert req["description"] == "用户可以登录。"
    assert req["acceptance_criteria"] == ["用户名和密码正确时登录成功", "密码错误时登录失败"]
    # P1.1/P1.2: new fields must be present
    assert "scenarios" in req
    assert "priority" in req
    assert "status" in req
    assert req["status"] == "PROPOSED"


def test_phase2_writes_requirements_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    context = OpenSpecContext(project_dir=Path("."), requirements_file=Path("simple_login.md"))
    context.is_cpp = True
    context.structured_requirements = [{"id": "REQ-001", "title": "用户登录", "description": "", "acceptance_criteria": []}]

    result = Phase2CreateStructure(context, _DummyRegistry()).execute()

    assert result.success
    requirements_json = context.project_dir / ".spec" / "requirements.json"
    assert requirements_json.exists()
    data = json.loads(requirements_json.read_text(encoding="utf-8"))
    assert data["requirements"][0]["id"] == "REQ-001"


def test_phase11_writes_artifact_graph_and_acceptance_matrix(tmp_path):
    project_dir = tmp_path / "cpp_simple_login"
    for folder in ["src", "include", "tests", "docs", ".spec"]:
        (project_dir / folder).mkdir(parents=True, exist_ok=True)
    (project_dir / "src" / "login_service.cpp").write_text("", encoding="utf-8")
    (project_dir / "tests" / "test_login_service.cpp").write_text("", encoding="utf-8")

    context = OpenSpecContext(project_dir=project_dir, requirements_file=tmp_path / "requirements.md")
    context.structured_requirements = [
        {"id": "REQ-001", "title": "用户登录", "description": "", "acceptance_criteria": []}
    ]
    context.test_passed = 2
    context.test_total = 2
    context.test_failed = 0

    result = Phase11FinalReport(context).execute()

    assert result.success
    graph_path = project_dir / ".spec" / "artifact_graph.json"
    assert graph_path.exists()
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    assert any(node["id"] == "REQ-001" for node in graph["nodes"])
    assert any(edge["relation"] == "verified_by" for edge in graph["edges"])

    report = (project_dir / "docs" / "final_report.md").read_text(encoding="utf-8")
    assert "## 6. Acceptance Matrix" in report
    assert "REQ-001 用户登录" in report
    assert "tests/test_login_service.cpp" in report
    assert "Passed" in report


def test_phase11_reports_skipped_phase10_without_zero_of_zero_passed(tmp_path):
    project_dir = tmp_path / "installer_project"
    for folder in ["src", "tests", "docs", ".spec"]:
        (project_dir / folder).mkdir(parents=True, exist_ok=True)

    context = OpenSpecContext(project_dir=project_dir, requirements_file=tmp_path / "requirements.md")
    context.structured_requirements = [
        {"id": "REQ-001", "title": "生成安装脚本", "description": "", "acceptance_criteria": []}
    ]
    context.set_phase_result(
        10,
        PhaseResult.ok(
            "Skipped: installer project",
            skipped=True,
            test_skipped=True,
            test_status="skipped",
            test_summary="skipped (installer project)",
        ),
    )

    result = Phase11FinalReport(context).execute()

    assert result.success
    assert result.data["test_skipped"] is True
    assert result.data["test_summary"] == "skipped (installer project)"
    report = (project_dir / "docs" / "final_report.md").read_text(encoding="utf-8")
    assert "0/0 passed" not in report
    assert "- Summary: skipped (installer project)" in report
    assert "| 10 | Compile and run tests | skipped |" in report
