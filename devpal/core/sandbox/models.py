# -*- coding: utf-8 -*-
"""Shared sandbox models for backend-neutral execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


SANDBOX_MANIFEST_SCHEMA_VERSION = "devpal.sandbox.manifest.v2"


def _path_to_string(path: Path | str | None) -> Optional[str]:
    if path is None:
        return None
    return Path(path).as_posix()


@dataclass
class SandboxViolation:
    reason: str
    path: str = ""
    command: List[str] = field(default_factory=list)
    policy_key: str = ""
    severity: str = "medium"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reason": self.reason,
            "path": self.path,
            "command": list(self.command),
            "policy_key": self.policy_key,
            "severity": self.severity,
            "metadata": dict(self.metadata),
        }


@dataclass
class SandboxPolicy:
    sandbox_level: str = "staging"
    allowed_paths: List[str] = field(default_factory=list)
    allowed_commands: List[str] = field(default_factory=list)
    denied_commands: List[str] = field(default_factory=list)
    network: str = "deny"
    timeout_seconds: int = 300
    max_processes: Optional[int] = None
    max_memory_mb: Optional[int] = None
    backend: str = "policy"
    isolation_level: str = "policy"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_legacy(
        cls,
        sandbox_level: str = "staging",
        allowed_paths: Optional[List[str]] = None,
        timeout_seconds: int = 300,
    ) -> "SandboxPolicy":
        return cls(
            sandbox_level=sandbox_level,
            allowed_paths=list(allowed_paths or []),
            timeout_seconds=timeout_seconds,
            backend="policy",
            isolation_level="policy",
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sandbox_level": self.sandbox_level,
            "allowed_paths": list(self.allowed_paths),
            "allowed_commands": list(self.allowed_commands),
            "denied_commands": list(self.denied_commands),
            "network": self.network,
            "timeout_seconds": self.timeout_seconds,
            "max_processes": self.max_processes,
            "max_memory_mb": self.max_memory_mb,
            "backend": self.backend,
            "isolation_level": self.isolation_level,
            "metadata": dict(self.metadata),
        }


@dataclass
class SandboxRequest:
    project_dir: Path
    task_id: str
    phase_number: int
    role: str
    policy: SandboxPolicy = field(default_factory=SandboxPolicy)
    execution_id: str = ""
    trace_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_legacy(
        cls,
        project_dir: Path | str,
        task_id: str,
        phase_number: int,
        role: str,
        sandbox_level: str = "staging",
        allowed_paths: Optional[List[str]] = None,
        timeout_seconds: int = 300,
        execution_id: str = "",
        trace_id: str = "",
    ) -> "SandboxRequest":
        return cls(
            project_dir=Path(project_dir),
            task_id=task_id,
            phase_number=phase_number,
            role=role,
            policy=SandboxPolicy.from_legacy(
                sandbox_level=sandbox_level,
                allowed_paths=allowed_paths,
                timeout_seconds=timeout_seconds,
            ),
            execution_id=execution_id,
            trace_id=trace_id,
        )


@dataclass
class SandboxArtifact:
    workspace_artifact: Optional[Path] = None
    target_path: Optional[Path] = None
    content_sha256: str = ""
    artifact_type: str = "file"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workspace_artifact": _path_to_string(self.workspace_artifact),
            "target_path": _path_to_string(self.target_path),
            "content_sha256": self.content_sha256,
            "artifact_type": self.artifact_type,
            "metadata": dict(self.metadata),
        }


@dataclass
class SandboxResult:
    success: bool
    sandbox_id: str
    backend: str = "policy"
    isolation_level: str = "policy"
    status: str = "created"
    sandbox_dir: Optional[Path] = None
    workspace_dir: Optional[Path] = None
    manifest_path: Optional[Path] = None
    artifacts: List[SandboxArtifact] = field(default_factory=list)
    violations: List[SandboxViolation] = field(default_factory=list)
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "sandbox_id": self.sandbox_id,
            "backend": self.backend,
            "isolation_level": self.isolation_level,
            "status": self.status,
            "sandbox_dir": _path_to_string(self.sandbox_dir),
            "workspace_dir": _path_to_string(self.workspace_dir),
            "manifest_path": _path_to_string(self.manifest_path),
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "violations": [violation.to_dict() for violation in self.violations],
            "error": self.error,
            "metadata": dict(self.metadata),
        }
