# -*- coding: utf-8 -*-
"""Sandbox path validation for multi-agent tasks."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from .models import CommandSpec


_ALLOWED_ROOTS = ("src/", "include/", "tests/", "scripts/")
_ALLOWED_TOOL_COMMANDS = {"pytest", "python", "python.exe", "cmake"}
_DENIED_COMMANDS = {
    "cmd",
    "cmd.exe",
    "powershell",
    "powershell.exe",
    "bash",
    "sh",
    "curl",
    "wget",
    "ssh",
    "scp",
    "rm",
    "del",
}


@dataclass
class SandboxSession:
    project_dir: Path
    task_id: str
    phase_number: int
    role: str
    sandbox_level: str = "staging"
    allowed_paths: List[str] | None = None

    @property
    def sandbox_id(self) -> str:
        digest = hashlib.sha1(self.task_id.encode("utf-8")).hexdigest()[:10]
        return f"phase{self.phase_number}-{self.role}-{digest}"

    def normalize_relative_path(self, rel_path: str) -> str:
        normalized = (rel_path or "").replace("\\", "/").strip()
        if not normalized:
            raise ValueError("path is required")
        candidate = Path(normalized)
        if candidate.is_absolute():
            raise ValueError(f"absolute paths are not allowed: {rel_path}")
        if any(part == ".." for part in candidate.parts):
            raise ValueError(f"path escapes project root: {rel_path}")
        normalized = candidate.as_posix()
        if not self._is_allowed_root(normalized):
            raise ValueError(f"path is outside allowed write roots: {rel_path}")
        allowed = [path.replace("\\", "/") for path in (self.allowed_paths or [])]
        if allowed and normalized not in allowed:
            raise ValueError(f"path is not allowed for this task: {rel_path}")
        return normalized

    def resolve_target(self, rel_path: str) -> Path:
        normalized = self.normalize_relative_path(rel_path)
        project_root = self.project_dir.resolve()
        target = (project_root / normalized).resolve()
        try:
            target.relative_to(project_root)
        except ValueError as exc:
            raise ValueError(f"path escapes project root: {rel_path}") from exc
        return target

    def validate_command(self, command: CommandSpec) -> CommandSpec:
        if isinstance(command.argv, str) or not isinstance(command.argv, list):
            raise ValueError("command argv must be a list")
        if not command.argv or not command.argv[0]:
            raise ValueError("command argv is required")
        self._validate_command_cwd(command.cwd)
        self._validate_command_executable(command.argv[0])
        if Path(command.argv[0]).name.lower() == "cmake":
            self._validate_cmake_args(command.argv)
        return command

    def manifest(self, artifacts: Iterable[Path] = ()) -> dict:
        return {
            "sandbox_id": self.sandbox_id,
            "task_id": self.task_id,
            "phase_number": self.phase_number,
            "role": self.role,
            "sandbox_level": self.sandbox_level,
            "artifacts": [str(path) for path in artifacts],
        }

    def _validate_command_cwd(self, cwd: Path | str) -> None:
        project_root = self.project_dir.resolve()
        cwd_path = Path(cwd).resolve()
        try:
            rel = cwd_path.relative_to(project_root)
        except ValueError as exc:
            raise ValueError(f"command cwd escapes project root: {cwd}") from exc
        rel_posix = rel.as_posix()
        if rel_posix in {".", ""}:
            return
        if rel_posix == "build" or rel_posix.startswith("build/"):
            return
        if rel_posix == "build_test" or rel_posix.startswith("build_test/"):
            return
        raise ValueError(f"command cwd is not allowed: {cwd}")

    def _validate_command_executable(self, executable: str) -> None:
        exe = (executable or "").strip()
        if not exe:
            raise ValueError("command executable is required")
        exe_path = Path(exe)
        exe_name = exe_path.name.lower()
        if exe_name in _DENIED_COMMANDS:
            raise ValueError(f"command executable is denied: {exe_name}")
        if exe_name in _ALLOWED_TOOL_COMMANDS and not exe_path.is_absolute():
            return
        if exe_path.is_absolute() or len(exe_path.parts) > 1:
            resolved = exe_path.resolve()
            project_root = self.project_dir.resolve()
            try:
                rel = resolved.relative_to(project_root)
            except ValueError as exc:
                raise ValueError(f"command executable escapes project root: {executable}") from exc
            rel_posix = rel.as_posix()
            if rel_posix.startswith("build_test/") or rel_posix.startswith("build/"):
                return
        raise ValueError(f"command executable is not allowed: {executable}")

    def _validate_cmake_args(self, argv: List[str]) -> None:
        for option in ("-S", "-B", "--build"):
            if option not in argv:
                continue
            index = argv.index(option)
            if index + 1 >= len(argv):
                raise ValueError(f"cmake option {option} requires a path")
            path = argv[index + 1]
            if option == "-S":
                self._validate_project_path(path, allow_project_root=True, allow_build=False)
            else:
                self._validate_project_path(path, allow_project_root=False, allow_build=True)

    def _validate_project_path(self, path: str, allow_project_root: bool, allow_build: bool) -> None:
        project_root = self.project_dir.resolve()
        resolved = Path(path).resolve()
        try:
            rel = resolved.relative_to(project_root)
        except ValueError as exc:
            raise ValueError(f"cmake path escapes project root: {path}") from exc
        rel_posix = rel.as_posix()
        if allow_project_root and rel_posix in {".", ""}:
            return
        if allow_build and (
            rel_posix == "build"
            or rel_posix.startswith("build/")
            or rel_posix == "build_test"
            or rel_posix.startswith("build_test/")
        ):
            return
        raise ValueError(f"cmake path is not allowed: {path}")

    def _is_allowed_root(self, rel_path: str) -> bool:
        return any(rel_path == root.rstrip("/") or rel_path.startswith(root) for root in _ALLOWED_ROOTS)
