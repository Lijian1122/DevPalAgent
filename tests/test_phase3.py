# -*- coding: utf-8 -*-
"""Tests for Phase 3 technical design generation."""

from pathlib import Path
from types import SimpleNamespace

from devpal.core.openspec_phases.base import OpenSpecContext
from devpal.core.openspec_phases.phase3_technical_design import Phase3TechnicalDesign


class _FakeLLMClient:
    def __init__(self, response: str):
        self.response = response
        self.usage = SimpleNamespace(
            calls=1,
            input_tokens=120,
            output_tokens=80,
            cache_read_tokens=30,
            cache_creation_tokens=10,
        )
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


def test_phase3_generates_design_with_injected_llm(tmp_path, monkeypatch):
    requirements_file = tmp_path / "requirements.md"
    requirements_file.write_text("# Simple Login\n\n用户可以使用密码登录。", encoding="utf-8")
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    fake_client = _FakeLLMClient("# Technical Design\n\nUse LoginService for authentication.")
    context = OpenSpecContext(
        project_dir=project_dir,
        requirements_file=requirements_file,
        requirements_content=requirements_file.read_text(encoding="utf-8"),
        project_name="simple_login",
        language="cpp",
    )

    monkeypatch.setattr(
        "devpal.core.openspec_phases.phase3_technical_design.get_llm_client",
        lambda: fake_client,
    )

    result = Phase3TechnicalDesign(context).execute()

    assert result.success is True
    assert context.tech_design_content == fake_client.response
    assert (project_dir / "docs" / "技术实现文档.md").read_text(encoding="utf-8") == fake_client.response
    assert context.llm_calls == 1
    assert context.llm_input_tokens == 120
    assert context.llm_output_tokens == 80
    assert context.llm_cache_read_tokens == 30
    assert context.llm_cache_creation_tokens == 10
    assert fake_client.calls[0]["cached_context"] == [context.requirements_content]


def test_phase3_fails_without_requirements_content(tmp_path):
    context = OpenSpecContext(
        project_dir=tmp_path,
        requirements_file=Path("requirements.md"),
        requirements_content="",
    )

    result = Phase3TechnicalDesign(context).execute()

    assert result.success is False
    assert "requirements_content" in result.errors[0]
