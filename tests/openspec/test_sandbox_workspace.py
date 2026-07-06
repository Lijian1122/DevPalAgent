# -*- coding: utf-8 -*-

import pytest

from devpal.core.sandbox.workspace import (
    SandboxWorkspacePlan,
    default_cpp_phase10_workspace_plan,
    default_python_phase10_workspace_plan,
)


def test_workspace_plan_copies_files_and_collects_hashes(tmp_path):
    project = tmp_path / "project"
    workspace = tmp_path / "sandbox" / "workspace"
    (project / "src").mkdir(parents=True)
    (project / "src" / "main.cpp").write_text("int main() { return 0; }\n", encoding="utf-8")
    (project / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.14)\n", encoding="utf-8")

    plan = SandboxWorkspacePlan(
        project_dir=project,
        workspace_dir=workspace,
        copy_in=["src", "CMakeLists.txt"],
        copy_out=["src"],
    )

    copied = plan.prepare()
    collected = plan.collect()

    assert (workspace / "src" / "main.cpp").exists()
    assert (workspace / "CMakeLists.txt").exists()
    assert copied
    assert collected
    assert collected[0].content_sha256


def test_workspace_plan_rejects_copy_in_escape(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    workspace = tmp_path / "sandbox" / "workspace"
    plan = SandboxWorkspacePlan(project_dir=project, workspace_dir=workspace, copy_in=["../outside"])

    with pytest.raises(ValueError):
        plan.prepare()


def test_default_cpp_workspace_plan_selects_existing_inputs(tmp_path):
    project = tmp_path / "project"
    workspace = tmp_path / "sandbox" / "workspace"
    (project / "src").mkdir(parents=True)
    (project / "tests").mkdir()

    plan = default_cpp_phase10_workspace_plan(project, workspace)

    assert plan.copy_in == ["src", "tests"]
    assert plan.copy_out == ["build", "build_test"]


def test_default_python_workspace_plan_selects_existing_inputs(tmp_path):
    project = tmp_path / "project"
    workspace = tmp_path / "sandbox" / "workspace"
    (project / "src").mkdir(parents=True)
    (project / "tests").mkdir()
    (project / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")

    plan = default_python_phase10_workspace_plan(project, workspace)

    assert plan.copy_in == ["pyproject.toml", "src", "tests"]
    assert plan.copy_out == []
