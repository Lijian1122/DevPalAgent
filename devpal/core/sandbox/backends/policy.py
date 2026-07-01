# -*- coding: utf-8 -*-
"""Compatibility backend for the current policy-level SandboxSession."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from devpal.core.multi_agent.models import CommandSpec
from devpal.core.multi_agent.sandbox import SandboxSession

from ..manifest import build_manifest_v2, write_manifest_v2
from ..models import SandboxArtifact, SandboxRequest


class PolicySandboxSession:
    """Backend-shaped wrapper around the legacy SandboxSession."""

    backend_name = "policy"
    isolation_level = "policy"

    def __init__(self, request: SandboxRequest):
        self.request = request
        self._session = SandboxSession(
            project_dir=request.project_dir,
            task_id=request.task_id,
            phase_number=request.phase_number,
            role=request.role,
            sandbox_level=request.policy.sandbox_level,
            allowed_paths=request.policy.allowed_paths,
        )

    @property
    def sandbox_id(self) -> str:
        return self._session.sandbox_id

    @property
    def sandbox_dir(self) -> Path:
        return self._session.sandbox_dir

    @property
    def workspace_dir(self) -> Path:
        return self._session.workspace_dir

    @property
    def manifest_path(self) -> Path:
        return self._session.manifest_path

    @property
    def manifest_v2_path(self) -> Path:
        return self.sandbox_dir / "manifest.v2.json"

    def prepare_workspace(self) -> Path:
        return self._session.prepare_workspace()

    def resolve_workspace_target(self, rel_path: str) -> Path:
        return self._session.resolve_workspace_target(rel_path)

    def resolve_target(self, rel_path: str) -> Path:
        return self._session.resolve_target(rel_path)

    def validate_command(self, command: CommandSpec) -> CommandSpec:
        return self._session.validate_command(command)

    def manifest(self, artifacts: Iterable[Path] = ()) -> dict:
        data = self._session.manifest(artifacts)
        data.update(
            {
                "backend": self.backend_name,
                "isolation_level": self.isolation_level,
            }
        )
        return data

    def write_manifest(self, artifacts: Iterable[Path] = (), **metadata) -> Path:
        return self._session.write_manifest(artifacts, **metadata)

    def build_manifest_v2(
        self,
        artifacts: Iterable[SandboxArtifact | Path | str] = (),
        **metadata,
    ) -> dict:
        status = str(metadata.pop("status", "created"))
        return build_manifest_v2(
            self.request,
            sandbox_id=self.sandbox_id,
            sandbox_dir=self.sandbox_dir,
            workspace_dir=self.workspace_dir,
            manifest_path=self.manifest_v2_path,
            status=status,
            backend=self.backend_name,
            isolation_level=self.isolation_level,
            artifacts=artifacts,
            metadata=metadata,
        )

    def write_manifest_v2(
        self,
        artifacts: Iterable[SandboxArtifact | Path | str] = (),
        **metadata,
    ) -> Path:
        manifest = self.build_manifest_v2(artifacts, **metadata)
        return write_manifest_v2(self.manifest_v2_path, manifest)


class PolicySandboxBackend:
    backend_name = "policy"
    isolation_level = "policy"

    def create_session(self, request: SandboxRequest) -> PolicySandboxSession:
        return PolicySandboxSession(request)
