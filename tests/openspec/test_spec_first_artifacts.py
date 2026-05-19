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


def test_phase1_keeps_python_project_with_install_feature_on_python(tmp_path):
    content = """# Python app

## REQ-001: Package installer
- Build a Python CLI that can install plugins for users.
- Use pytest for tests.
"""
    context = OpenSpecContext(project_dir=tmp_path / "out", requirements_file=tmp_path / "requirements.md")
    context.is_cpp = False
    context.language = "python"
    phase = Phase1ParseRequirements(context, _FileReaderRegistry(content))

    result = phase.execute()

    assert result.success
    assert context.project_type == ""
    assert context.language == "python"
    assert context.is_cpp is False


def test_phase1_classifies_plain_shell_project_without_installer_skip(tmp_path):
    content = """# Maintenance shell script

## REQ-001: Backup job
- Build a shell script project with scripts/main.sh.
- Add bats tests.
"""
    context = OpenSpecContext(project_dir=tmp_path / "out", requirements_file=tmp_path / "requirements.md")
    phase = Phase1ParseRequirements(context, _FileReaderRegistry(content))

    result = phase.execute()

    assert result.success
    assert context.project_type == ""
    assert context.language == "shell"
    assert context.is_cpp is False


def test_phase1_classifies_installer_as_shell_project(tmp_path):
    content = """# 平台安装脚本生成器测试

## REQ-001: 生成平台安装脚本
- 为 macOS/Linux 生成 install_claude_cli.sh shell 脚本
- 为 Windows 生成 install_claude_cli.bat 批处理脚本
- 这是一个安装工具项目
"""
    context = OpenSpecContext(project_dir=tmp_path / "out", requirements_file=tmp_path / "requirements.md")
    phase = Phase1ParseRequirements(context, _FileReaderRegistry(content))

    result = phase.execute()

    assert result.success
    assert context.project_type == "installer"
    assert context.language == "shell"
    assert context.is_cpp is False


def test_phase2_creates_cpp_structure(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    context = OpenSpecContext(project_dir=Path("."), requirements_file=Path("simple_login.md"))
    context.is_cpp = True
    context.language = "cpp"

    result = Phase2CreateStructure(context, _DummyRegistry()).execute()

    assert result.success
    assert context.project_name == "cpp_simple_login"
    assert (context.project_dir / "include").exists()
    assert ".spec" in result.data["subdirs"]


def test_phase2_creates_python_structure_without_include(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    context = OpenSpecContext(project_dir=Path("."), requirements_file=Path("python_app.md"))
    context.is_cpp = False
    context.language = "python"

    result = Phase2CreateStructure(context, _DummyRegistry()).execute()

    assert result.success
    assert context.project_name == "python_app"
    assert "include" not in result.data["subdirs"]
    assert not (context.project_dir / "include").exists()
    assert (context.project_dir / "data").exists()


def test_phase2_creates_installer_structure_without_cpp_prefix_or_include(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    context = OpenSpecContext(project_dir=Path("."), requirements_file=Path("test_phase_skip.md"))
    context.is_cpp = False
    context.language = "shell"
    context.project_type = "installer"

    result = Phase2CreateStructure(context, _DummyRegistry()).execute()

    assert result.success
    assert context.project_name == "test_phase_skip"
    assert "scripts" in result.data["subdirs"]
    assert "include" not in result.data["subdirs"]
    assert not (tmp_path / "cpp_test_phase_skip").exists()


def test_phase2_creates_plain_shell_structure_with_lib(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    context = OpenSpecContext(project_dir=Path("."), requirements_file=Path("backup_job.md"))
    context.is_cpp = False
    context.language = "shell"

    result = Phase2CreateStructure(context, _DummyRegistry()).execute()

    assert result.success
    assert context.project_name == "backup_job"
    assert "scripts" in result.data["subdirs"]
    assert "lib" in result.data["subdirs"]
    assert "include" not in result.data["subdirs"]


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


def test_phase11_python_claude_md_uses_python_conventions(tmp_path):
    project_dir = tmp_path / "python_app"
    for folder in ["src", "tests", "docs", ".spec"]:
        (project_dir / folder).mkdir(parents=True, exist_ok=True)
    (project_dir / "src" / "main.py").write_text("def main():\n    return 0\n", encoding="utf-8")
    (project_dir / "tests" / "test_main.py").write_text("def test_main():\n    assert True\n", encoding="utf-8")

    context = OpenSpecContext(project_dir=project_dir, requirements_file=tmp_path / "requirements.md")
    context.is_cpp = False
    context.language = "python"
    context.project_name = "python_app"
    context.structured_requirements = [
        {"id": "REQ-001", "title": "Python app", "description": "", "acceptance_criteria": []}
    ]
    context.test_passed = 1
    context.test_total = 1
    context.test_failed = 0

    result = Phase11FinalReport(context).execute()

    assert result.success
    report = (project_dir / "docs" / "final_report.md").read_text(encoding="utf-8")
    assert "src/main.py" in report
    assert "tests/test_main.py" in report
    claude_md = (project_dir / "CLAUDE.md").read_text(encoding="utf-8")
    assert "Language: Python" in claude_md
    assert "pytest" in claude_md
    assert "Source code (.py files)" in claude_md
    assert ".cpp" not in claude_md
    assert "test_base.h" not in claude_md
    assert "CMake" not in claude_md


def test_phase11_reports_skipped_phase10_without_zero_of_zero_passed(tmp_path):
    project_dir = tmp_path / "installer_project"
    for folder in ["scripts", "tests", "docs", ".spec"]:
        (project_dir / folder).mkdir(parents=True, exist_ok=True)
    (project_dir / "scripts" / "install_claude_cli.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    (project_dir / "scripts" / "install_claude_cli.bat").write_text("@echo off\n", encoding="utf-8")

    context = OpenSpecContext(project_dir=project_dir, requirements_file=tmp_path / "requirements.md")
    context.is_cpp = False
    context.language = "shell"
    context.project_type = "installer"
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
    assert "install_claude_cli.sh" in report
    assert "install_claude_cli.bat" in report
    assert "- Summary: skipped (installer project)" in report
    assert "| 10 | Compile and run tests | skipped |" in report
    claude_md = (project_dir / "CLAUDE.md").read_text(encoding="utf-8")
    assert "Summary: skipped (installer project)" in claude_md
    assert "Language: Shell Script" in claude_md
    assert "scripts/" in claude_md
    coding_section = claude_md.split("## Coding Conventions", 1)[1]
    assert ".cpp" not in coding_section
    assert "test_base.h" not in coding_section
    assert "CMake" not in coding_section
