# -*- coding: utf-8 -*-
"""Sandbox workspace copy-in/copy-out helpers."""

from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from .models import SandboxArtifact


@dataclass
class SandboxWorkspacePlan:
    project_dir: Path
    workspace_dir: Path
    copy_in: List[str] = field(default_factory=list)
    copy_out: List[str] = field(default_factory=list)

    def prepare(self) -> List[SandboxArtifact]:
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        artifacts: List[SandboxArtifact] = []
        for rel_path in self.copy_in:
            src = _safe_project_path(self.project_dir, rel_path)
            dst = _safe_workspace_path(self.workspace_dir, rel_path)
            if src.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                artifacts.extend(_artifacts_for_dir(dst, rel_path))
            elif src.is_file():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                artifacts.append(_artifact_for_file(dst, rel_path))
        return artifacts

    def collect(self) -> List[SandboxArtifact]:
        artifacts: List[SandboxArtifact] = []
        for rel_path in self.copy_out:
            workspace_path = _safe_workspace_path(self.workspace_dir, rel_path)
            if workspace_path.is_dir():
                artifacts.extend(_artifacts_for_dir(workspace_path, rel_path))
            elif workspace_path.is_file():
                artifacts.append(_artifact_for_file(workspace_path, rel_path))
        return artifacts


def default_cpp_phase10_workspace_plan(project_dir: Path, workspace_dir: Path) -> SandboxWorkspacePlan:
    candidates = ["CMakeLists.txt", "include", "src", "tests"]
    copy_in = [item for item in candidates if (project_dir / item).exists()]
    return SandboxWorkspacePlan(
        project_dir=project_dir,
        workspace_dir=workspace_dir,
        copy_in=copy_in,
        copy_out=["build", "build_test"],
    )


def default_python_phase10_workspace_plan(project_dir: Path, workspace_dir: Path) -> SandboxWorkspacePlan:
    candidates = [
        "pyproject.toml",
        "pytest.ini",
        "setup.cfg",
        "setup.py",
        "requirements.txt",
        "src",
        "tests",
    ]
    copy_in = [item for item in candidates if (project_dir / item).exists()]
    return SandboxWorkspacePlan(
        project_dir=project_dir,
        workspace_dir=workspace_dir,
        copy_in=copy_in,
        copy_out=[],
    )


def _safe_project_path(project_dir: Path, rel_path: str) -> Path:
    root = project_dir.resolve()
    target = (root / rel_path).resolve()
    target.relative_to(root)
    return target


def _safe_workspace_path(workspace_dir: Path, rel_path: str) -> Path:
    root = workspace_dir.resolve()
    target = (root / rel_path).resolve()
    target.relative_to(root)
    return target


def _artifacts_for_dir(root: Path, rel_root: str) -> List[SandboxArtifact]:
    return [
        _artifact_for_file(path, str(Path(rel_root) / path.relative_to(root)))
        for path in root.rglob("*")
        if path.is_file()
    ]


def _artifact_for_file(path: Path, rel_path: str) -> SandboxArtifact:
    return SandboxArtifact(
        workspace_artifact=path,
        target_path=Path(rel_path),
        content_sha256=_sha256_file(path),
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
