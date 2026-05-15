# -*- coding: utf-8 -*-

from pathlib import Path

from devpal.core.openspec_phases.base import OpenSpecContext
from devpal.core.openspec_phases.phase10_run_tests import Phase10RunTests


class DummyToolRegistry:
    pass


def test_compile_error_summary_extracts_msvc_include_error(tmp_path):
    context = OpenSpecContext(
        project_dir=tmp_path,
        requirements_file=tmp_path / "requirements.md",
    )
    phase = Phase10RunTests(context, DummyToolRegistry())
    compile_output = """
=== CMake Build ===
user_repository.cpp
C:\\repo\\src\\user_repository.cpp(3,10): fatal error C1083: 无法打开包括文件: “lock_guard”: No such file or directory
正在生成代码...
"""

    summary = phase._extract_compile_error_summary(compile_output)

    assert len(summary) == 1
    assert "fatal error C1083" in summary[0]
    assert "lock_guard" in summary[0]
