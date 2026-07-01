# -*- coding: utf-8 -*-
"""Manifest v2 helpers for sandbox audit records."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .models import (
    SANDBOX_MANIFEST_SCHEMA_VERSION,
    SandboxArtifact,
    SandboxRequest,
    SandboxViolation,
)


class ManifestValidationError(ValueError):
    """Raised when a sandbox manifest does not match the v2 schema."""


def _now_utc() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _path_to_string(path: Path | str | None) -> Optional[str]:
    if path is None:
        return None
    return Path(path).as_posix()


def _artifact_to_dict(artifact: SandboxArtifact | Path | str) -> Dict[str, Any]:
    if isinstance(artifact, SandboxArtifact):
        return artifact.to_dict()
    return {
        "workspace_artifact": _path_to_string(artifact),
        "target_path": None,
        "content_sha256": "",
        "artifact_type": "file",
        "metadata": {},
    }


def _violation_to_dict(violation: SandboxViolation | Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(violation, SandboxViolation):
        return violation.to_dict()
    return dict(violation)


def build_manifest_v2(
    request: SandboxRequest,
    *,
    sandbox_id: str,
    sandbox_dir: Path,
    workspace_dir: Path,
    manifest_path: Path,
    status: str = "created",
    backend: Optional[str] = None,
    isolation_level: Optional[str] = None,
    artifacts: Iterable[SandboxArtifact | Path | str] = (),
    violations: Iterable[SandboxViolation | Dict[str, Any]] = (),
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a manifest v2 dictionary and validate its shape."""

    execution_id = request.execution_id or f"{sandbox_id}-{_now_utc()}"
    data: Dict[str, Any] = {
        "schema_version": SANDBOX_MANIFEST_SCHEMA_VERSION,
        "sandbox_id": sandbox_id,
        "execution_id": execution_id,
        "workflow_id": str(request.metadata.get("workflow_id", "")),
        "task_id": request.task_id,
        "phase_number": int(request.phase_number),
        "role": request.role,
        "backend": backend or request.policy.backend,
        "isolation_level": isolation_level or request.policy.isolation_level,
        "status": status,
        "created_at": _now_utc(),
        "policy": request.policy.to_dict(),
        "workspace": {
            "project_dir": _path_to_string(request.project_dir),
            "sandbox_dir": _path_to_string(sandbox_dir),
            "workspace_dir": _path_to_string(workspace_dir),
            "manifest_path": _path_to_string(manifest_path),
        },
        "artifacts": [_artifact_to_dict(artifact) for artifact in artifacts],
        "violations": [_violation_to_dict(violation) for violation in violations],
        "trace": {
            "trace_id": request.trace_id,
            "event_log": str(request.metadata.get("event_log", "")),
        },
        "metadata": dict(metadata or {}),
    }
    errors = validate_manifest_v2(data)
    if errors:
        raise ManifestValidationError("; ".join(errors))
    return data


def validate_manifest_v2(data: Any) -> List[str]:
    """Return schema errors for a manifest v2 dictionary."""

    errors: List[str] = []
    if not isinstance(data, dict):
        return ["manifest must be a JSON object"]

    required = {
        "schema_version": str,
        "sandbox_id": str,
        "execution_id": str,
        "task_id": str,
        "phase_number": int,
        "role": str,
        "backend": str,
        "isolation_level": str,
        "status": str,
        "policy": dict,
        "workspace": dict,
        "artifacts": list,
        "violations": list,
        "trace": dict,
    }
    for key, expected_type in required.items():
        if key not in data:
            errors.append(f"missing required field: {key}")
            continue
        if not isinstance(data[key], expected_type):
            errors.append(f"{key} must be {expected_type.__name__}")

    if data.get("schema_version") != SANDBOX_MANIFEST_SCHEMA_VERSION:
        errors.append(
            f"schema_version must be {SANDBOX_MANIFEST_SCHEMA_VERSION}"
        )

    policy = data.get("policy")
    if isinstance(policy, dict):
        if not isinstance(policy.get("allowed_paths", []), list):
            errors.append("policy.allowed_paths must be list")
        if not isinstance(policy.get("allowed_commands", []), list):
            errors.append("policy.allowed_commands must be list")
        if not isinstance(policy.get("denied_commands", []), list):
            errors.append("policy.denied_commands must be list")
        if policy.get("network", "deny") not in {"allow", "deny", "restricted"}:
            errors.append("policy.network must be allow, deny, or restricted")
        timeout = policy.get("timeout_seconds", 0)
        if not isinstance(timeout, int) or timeout < 0:
            errors.append("policy.timeout_seconds must be a non-negative int")

    workspace = data.get("workspace")
    if isinstance(workspace, dict):
        for key in ("project_dir", "sandbox_dir", "workspace_dir", "manifest_path"):
            if key not in workspace:
                errors.append(f"workspace missing {key}")

    artifacts = data.get("artifacts")
    if isinstance(artifacts, list):
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                errors.append(f"artifacts[{index}] must be object")
                continue
            if "workspace_artifact" not in artifact:
                errors.append(f"artifacts[{index}] missing workspace_artifact")

    violations = data.get("violations")
    if isinstance(violations, list):
        for index, violation in enumerate(violations):
            if not isinstance(violation, dict):
                errors.append(f"violations[{index}] must be object")
            elif "reason" not in violation:
                errors.append(f"violations[{index}] missing reason")

    return errors


def write_manifest_v2(path: Path | str, manifest: Dict[str, Any]) -> Path:
    errors = validate_manifest_v2(manifest)
    if errors:
        raise ManifestValidationError("; ".join(errors))
    manifest_path = Path(path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest_path


def read_manifest_v2(path: Path | str) -> Dict[str, Any]:
    manifest_path = Path(path)
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestValidationError(f"invalid manifest JSON: {exc}") from exc
    errors = validate_manifest_v2(data)
    if errors:
        raise ManifestValidationError("; ".join(errors))
    return data
