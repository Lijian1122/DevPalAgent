# -*- coding: utf-8 -*-

from pathlib import Path

from devpal.core.openspec_phases.base import OpenSpecContext
from devpal.core.openspec_phases.phase10_run_tests import Phase10RunTests


class _DummyRegistry:
    pass


def test_phase10_runs_python_pytest_and_sets_canonical_counts(tmp_path):
    project_dir = tmp_path / "python_app"
    (project_dir / "src").mkdir(parents=True)
    (project_dir / "tests").mkdir()
    (project_dir / "src" / "main.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (project_dir / "tests" / "test_main.py").write_text(
        "from main import add\n\n"
        "def test_add():\n"
        "    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )

    context = OpenSpecContext(project_dir=project_dir, requirements_file=tmp_path / "requirements.md")
    # 设置为 Python 项目（is_cpp 是只读属性，基于 language 字段）
    context.language = "python"
    context.project_type = "application"

    result = Phase10RunTests(context, _DummyRegistry()).execute()

    assert result.success is True
    assert not result.data.get("skipped")
    assert context.test_total == 1
    assert context.test_passed == 1
    assert context.test_failed == 0
    assert result.data["test_total"] == 1
    assert result.data["test_passed"] == 1
    assert result.data["test_failed"] == 0
    assert "test_add" in context.test_output
