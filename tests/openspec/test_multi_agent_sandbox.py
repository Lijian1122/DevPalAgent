# -*- coding: utf-8 -*-

import pytest

from devpal.core.multi_agent import CommandSpec, SandboxSession


def _sandbox(tmp_path, allowed_paths=None):
    return SandboxSession(
        project_dir=tmp_path,
        task_id="phase4:src/example.cpp",
        phase_number=4,
        role="codegen",
        allowed_paths=allowed_paths,
    )


@pytest.mark.parametrize(
    "path",
    ["src/example.cpp", "include/example.h", "tests/test_example.cpp", "scripts/install.sh"],
)
def test_sandbox_accepts_allowed_project_paths(tmp_path, path):
    sandbox = _sandbox(tmp_path)

    target = sandbox.resolve_target(path)

    assert target == (tmp_path / path).resolve()


@pytest.mark.parametrize("path", ["../escape.cpp", "src/../escape.cpp", "/tmp/escape.cpp"])
def test_sandbox_rejects_paths_that_escape_project(tmp_path, path):
    sandbox = _sandbox(tmp_path)

    with pytest.raises(ValueError):
        sandbox.resolve_target(path)


def test_sandbox_rejects_disallowed_root(tmp_path):
    sandbox = _sandbox(tmp_path)

    with pytest.raises(ValueError):
        sandbox.resolve_target("docs/readme.md")


def test_sandbox_rejects_path_not_allowed_for_task(tmp_path):
    sandbox = _sandbox(tmp_path, allowed_paths=["src/example.cpp"])

    with pytest.raises(ValueError):
        sandbox.resolve_target("src/other.cpp")


def test_sandbox_accepts_exact_allowed_task_path(tmp_path):
    sandbox = _sandbox(tmp_path, allowed_paths=["src/example.cpp"])

    assert sandbox.normalize_relative_path("src/example.cpp") == "src/example.cpp"


def test_sandbox_accepts_pytest_command_at_project_root(tmp_path):
    sandbox = _sandbox(tmp_path)
    command = CommandSpec(argv=["pytest", "tests", "-v"], cwd=tmp_path)

    assert sandbox.validate_command(command) is command


def test_sandbox_accepts_cmake_command_at_project_root(tmp_path):
    sandbox = _sandbox(tmp_path)
    build_dir = tmp_path / "build_test"
    command = CommandSpec(argv=["cmake", "--build", str(build_dir)], cwd=tmp_path)

    assert sandbox.validate_command(command) is command


def test_sandbox_accepts_build_test_executable(tmp_path):
    sandbox = _sandbox(tmp_path)
    exe = tmp_path / "build_test" / "test_app.exe"
    command = CommandSpec(argv=[str(exe)], cwd=exe.parent)

    assert sandbox.validate_command(command) is command


@pytest.mark.parametrize("argv", [["cmd", "/c", "dir"], ["powershell", "dir"], ["curl", "https://example.com"]])
def test_sandbox_rejects_denied_command_names(tmp_path, argv):
    sandbox = _sandbox(tmp_path)

    with pytest.raises(ValueError):
        sandbox.validate_command(CommandSpec(argv=argv, cwd=tmp_path))


def test_sandbox_rejects_shell_string_command(tmp_path):
    sandbox = _sandbox(tmp_path)

    with pytest.raises(ValueError):
        sandbox.validate_command(CommandSpec(argv="pytest tests", cwd=tmp_path))


def test_sandbox_rejects_command_cwd_outside_project(tmp_path):
    sandbox = _sandbox(tmp_path)

    with pytest.raises(ValueError):
        sandbox.validate_command(CommandSpec(argv=["pytest", "tests"], cwd=tmp_path.parent))


def test_sandbox_rejects_executable_outside_project(tmp_path):
    sandbox = _sandbox(tmp_path)
    outside = tmp_path.parent / "tool.exe"

    with pytest.raises(ValueError):
        sandbox.validate_command(CommandSpec(argv=[str(outside)], cwd=tmp_path))


def test_sandbox_accepts_cmake_configure_to_build_test(tmp_path):
    sandbox = _sandbox(tmp_path)
    command = CommandSpec(
        argv=["cmake", "-S", str(tmp_path), "-B", str(tmp_path / "build_test")],
        cwd=tmp_path,
    )

    assert sandbox.validate_command(command) is command


@pytest.mark.parametrize("build_name", ["build", "build_test"])
def test_sandbox_accepts_cmake_build_dirs(tmp_path, build_name):
    sandbox = _sandbox(tmp_path)
    command = CommandSpec(argv=["cmake", "--build", str(tmp_path / build_name)], cwd=tmp_path)

    assert sandbox.validate_command(command) is command


def test_sandbox_rejects_cmake_build_dir_outside_project(tmp_path):
    sandbox = _sandbox(tmp_path)
    outside = tmp_path.parent / "build_test"

    with pytest.raises(ValueError):
        sandbox.validate_command(CommandSpec(argv=["cmake", "--build", str(outside)], cwd=tmp_path))


def test_sandbox_rejects_cmake_configure_build_dir_outside_project(tmp_path):
    sandbox = _sandbox(tmp_path)
    outside = tmp_path.parent / "build_test"

    with pytest.raises(ValueError):
        sandbox.validate_command(CommandSpec(argv=["cmake", "-S", str(tmp_path), "-B", str(outside)], cwd=tmp_path))


@pytest.mark.parametrize("argv", [["cmake", "-S"], ["cmake", "-B"], ["cmake", "--build"]])
def test_sandbox_rejects_cmake_missing_path_argument(tmp_path, argv):
    sandbox = _sandbox(tmp_path)

    with pytest.raises(ValueError):
        sandbox.validate_command(CommandSpec(argv=argv, cwd=tmp_path))
