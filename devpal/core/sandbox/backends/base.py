# -*- coding: utf-8 -*-
"""Backend protocols for sandbox implementations."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Protocol

from devpal.core.multi_agent.models import CommandSpec

from ..models import SandboxArtifact, SandboxRequest


class SandboxSessionHandle(Protocol):
    sandbox_id: str
    sandbox_dir: Path
    workspace_dir: Path
    manifest_path: Path

    def prepare_workspace(self) -> Path:
        ...

    def resolve_workspace_target(self, rel_path: str) -> Path:
        ...

    def resolve_target(self, rel_path: str) -> Path:
        ...

    def validate_command(self, command: CommandSpec) -> CommandSpec:
        ...

    def write_manifest(self, artifacts: Iterable[Path] = (), **metadata) -> Path:
        ...

    def write_manifest_v2(
        self,
        artifacts: Iterable[SandboxArtifact | Path | str] = (),
        **metadata,
    ) -> Path:
        ...


class SandboxBackend(Protocol):
    backend_name: str
    isolation_level: str

    def create_session(self, request: SandboxRequest) -> SandboxSessionHandle:
        ...
