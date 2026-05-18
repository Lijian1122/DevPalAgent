# -*- coding: utf-8 -*-

from pathlib import Path

from devpal.core.openspec_phases import OpenSpecPhaseScheduler
from devpal.tools.registry import ToolRegistry


INSTALLER_REQUIREMENTS = """# 安装脚本生成器测试

## 项目概述

这是一个安装脚本项目，用于生成 Claude Code CLI 的安装脚本。

本项目是安装脚本类型，不需要 C++ 编译、CMake 配置和测试。

## 功能需求

### REQ-001: 生成安装脚本
- 生成简单的安装脚本
- 支持基本的环境检查
- 这是一个安装工具项目

## 验收标准

- [ ] 生成安装脚本文件
- [ ] 脚本能够运行
"""


def test_installer_flow_skips_non_applicable_phases(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    requirements_dir = tmp_path / "requirements"
    requirements_dir.mkdir()
    requirements_file = requirements_dir / "test_phase_skip.md"
    requirements_file.write_text(INSTALLER_REQUIREMENTS, encoding="utf-8")

    scheduler = OpenSpecPhaseScheduler(str(requirements_file), ToolRegistry())
    result = scheduler.run_all_phases(resume=False)

    assert result["success"] is True
    assert result["project_name"] == "test_phase_skip"
    assert result["test_skipped"] is True
    assert result["test_summary"].startswith("skipped")
    assert not (tmp_path / "cpp_test_phase_skip").exists()

    phases = result["phases"]
    for phase_num in [3, 5, 6, 7, 10]:
        assert phases[phase_num].success is True
        assert phases[phase_num].data.get("skipped") is True

    project_dir = tmp_path / "test_phase_skip"
    final_report = (project_dir / "docs" / "final_report.md").read_text(encoding="utf-8")
    quality_report = (project_dir / "docs" / "quality_gate_report.md").read_text(encoding="utf-8")
    claude_md = (project_dir / "CLAUDE.md").read_text(encoding="utf-8")

    assert "0/0 passed" not in final_report
    assert "- FORMAT layer: 0 error(s)" in quality_report
    assert "- BUSINESS layer: 0 error(s)" in quality_report
    assert "CMakeLists.txt not found" not in quality_report
    assert "src/main.cpp not found" not in quality_report
    coding_section = claude_md.split("## Coding Conventions", 1)[1]
    assert ".cpp" not in coding_section
    assert "test_base.h" not in coding_section
    assert "CMake" not in coding_section
