# -*- coding: utf-8 -*-
"""Copy-out approval gate for sandbox workspace artifacts."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .models import SandboxArtifact


COPY_OUT_MANIFEST_SCHEMA_VERSION = "devpal.sandbox.copy_out.v1"
COPY_OUT_PENDING_STATUS = "copy_out_pending"
COPY_OUT_APPLIED_STATUS = "copy_out_applied"
COPY_OUT_ALLOWED_TARGET_ROOTS = (
    "src/",
    "include/",
    "tests/",
    "scripts/",
    "docs/",
    "build/",
    "build_test/",
)


@dataclass
class CopyOutApplyResult:
    success: bool
    status: str
    manifest_path: Optional[Path] = None
    applied: bool = False
    artifact_count: int = 0
    applied_count: int = 0
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "status": self.status,
            "manifest_path": self.manifest_path.as_posix() if self.manifest_path else None,
            "applied": self.applied,
            "artifact_count": self.artifact_count,
            "applied_count": self.applied_count,
            "errors": list(self.errors),
            "metadata": dict(self.metadata),
        }


def _now_utc() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_project_path(project_dir: Path, rel_path: str) -> Path:
    root = project_dir.resolve()
    target = (root / rel_path).resolve()
    target.relative_to(root)
    return target


def _artifact_to_candidate(
    artifact: SandboxArtifact,
    *,
    project_dir: Path,
    workspace_dir: Path,
) -> Dict[str, Any]:
    if artifact.workspace_artifact is None:
        raise ValueError("copy-out artifact missing workspace_artifact")
    if artifact.target_path is None:
        raise ValueError("copy-out artifact missing target_path")
    workspace_artifact = Path(artifact.workspace_artifact).resolve()
    workspace_artifact.relative_to(workspace_dir.resolve())
    target_rel = Path(artifact.target_path).as_posix()
    target = _safe_project_path(project_dir, target_rel)
    content_sha256 = artifact.content_sha256 or _sha256_file(workspace_artifact)
    size_bytes = workspace_artifact.stat().st_size
    return {
        "workspace_artifact": workspace_artifact.as_posix(),
        "target_path": target.as_posix(),
        "target_relpath": target_rel,
        "content_sha256": content_sha256,
        "size_bytes": size_bytes,
        "artifact_type": artifact.artifact_type,
        "applied": False,
        "metadata": dict(artifact.metadata),
    }


def build_copy_out_manifest(
    *,
    project_dir: Path,
    workspace_dir: Path,
    manifest_path: Path,
    artifacts: Iterable[SandboxArtifact],
    task_id: str = "phase10:copy_out",
    phase_number: int = 10,
    workflow_id: str = "",
    sandbox_backend: str = "windows_process",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    project_dir = Path(project_dir).resolve()
    workspace_dir = Path(workspace_dir).resolve()
    manifest_path = Path(manifest_path).resolve()
    candidates = [
        _artifact_to_candidate(
            artifact,
            project_dir=project_dir,
            workspace_dir=workspace_dir,
        )
        for artifact in artifacts
    ]
    total_bytes = sum(int(candidate.get("size_bytes", 0) or 0) for candidate in candidates)
    return {
        "schema_version": COPY_OUT_MANIFEST_SCHEMA_VERSION,
        "status": COPY_OUT_PENDING_STATUS,
        "requires_manual_apply": True,
        "applied": False,
        "created_at": _now_utc(),
        "applied_at": "",
        "workflow_id": workflow_id,
        "task_id": task_id,
        "phase_number": phase_number,
        "sandbox_backend": sandbox_backend,
        "project_dir": project_dir.as_posix(),
        "workspace_dir": workspace_dir.as_posix(),
        "manifest_path": manifest_path.as_posix(),
        "artifact_count": len(candidates),
        "total_bytes": total_bytes,
        "artifacts": candidates,
        "metadata": dict(metadata or {}),
    }


def write_copy_out_manifest(path: Path | str, manifest: Dict[str, Any]) -> Path:
    manifest_path = Path(path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest_path


def create_copy_out_manifest(
    *,
    project_dir: Path,
    workspace_dir: Path,
    manifest_path: Path,
    artifacts: Iterable[SandboxArtifact],
    task_id: str = "phase10:copy_out",
    phase_number: int = 10,
    workflow_id: str = "",
    sandbox_backend: str = "windows_process",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    manifest = build_copy_out_manifest(
        project_dir=project_dir,
        workspace_dir=workspace_dir,
        manifest_path=manifest_path,
        artifacts=artifacts,
        task_id=task_id,
        phase_number=phase_number,
        workflow_id=workflow_id,
        sandbox_backend=sandbox_backend,
        metadata=metadata,
    )
    write_copy_out_manifest(manifest_path, manifest)
    return manifest


class SandboxCopyOutService:
    """Preview or apply a sandbox copy-out manifest."""

    def apply_manifest(
        self,
        project_dir: Path | str,
        manifest_path: Path | str,
        *,
        apply: bool = False,
    ) -> CopyOutApplyResult:
        project_dir = Path(project_dir).resolve()
        manifest_path = Path(manifest_path)
        if not manifest_path.is_absolute():
            manifest_path = (project_dir / manifest_path).resolve()
        else:
            manifest_path = manifest_path.resolve()

        manifest, errors = self._load_manifest(manifest_path)
        if errors:
            return CopyOutApplyResult(
                success=False,
                status="FAILED",
                manifest_path=manifest_path,
                errors=errors,
            )

        errors = self._validate_manifest(project_dir, manifest_path, manifest)
        artifacts = list(manifest.get("artifacts", []) or [])
        if errors:
            return CopyOutApplyResult(
                success=False,
                status="FAILED",
                manifest_path=manifest_path,
                artifact_count=len(artifacts),
                errors=errors,
            )

        metadata = {
            "artifact_count": len(artifacts),
            "total_bytes": int(manifest.get("total_bytes", 0) or 0),
            "requires_manual_apply": bool(manifest.get("requires_manual_apply", True)),
        }
        if not apply:
            return CopyOutApplyResult(
                success=True,
                status="PREVIEW",
                manifest_path=manifest_path,
                artifact_count=len(artifacts),
                applied=False,
                metadata=metadata,
            )

        applied = 0
        for artifact in artifacts:
            src = Path(str(artifact["workspace_artifact"])).resolve()
            dst = Path(str(artifact["target_path"])).resolve()
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            artifact["applied"] = True
            applied += 1

        manifest["status"] = COPY_OUT_APPLIED_STATUS
        manifest["applied"] = True
        manifest["requires_manual_apply"] = False
        manifest["applied_at"] = _now_utc()
        write_copy_out_manifest(manifest_path, manifest)
        metadata["applied_at"] = manifest["applied_at"]
        return CopyOutApplyResult(
            success=True,
            status="APPLIED",
            manifest_path=manifest_path,
            applied=True,
            artifact_count=len(artifacts),
            applied_count=applied,
            metadata=metadata,
        )

    def _load_manifest(self, manifest_path: Path) -> tuple[Dict[str, Any], List[str]]:
        if not manifest_path.exists():
            return {}, [f"missing copy-out manifest: {manifest_path}"]
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return {}, [f"invalid copy-out manifest JSON: {exc}"]
        if not isinstance(data, dict):
            return {}, ["copy-out manifest must be a JSON object"]
        return data, []

    def _validate_manifest(
        self,
        project_dir: Path,
        manifest_path: Path,
        manifest: Dict[str, Any],
    ) -> List[str]:
        errors: List[str] = []
        if manifest.get("schema_version") != COPY_OUT_MANIFEST_SCHEMA_VERSION:
            errors.append(f"schema_version must be {COPY_OUT_MANIFEST_SCHEMA_VERSION}")
        if str(manifest.get("status", "")).lower() != COPY_OUT_PENDING_STATUS:
            errors.append(f"manifest status must be {COPY_OUT_PENDING_STATUS}")
        self._require_under_project(manifest_path, project_dir, "manifest_path", errors)
        artifacts = manifest.get("artifacts")
        if not isinstance(artifacts, list):
            errors.append("artifacts must be list")
            return errors
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                errors.append(f"artifacts[{index}] must be object")
                continue
            src_value = artifact.get("workspace_artifact")
            target_value = artifact.get("target_path")
            if not src_value:
                errors.append(f"artifacts[{index}] missing workspace_artifact")
                continue
            if not target_value:
                errors.append(f"artifacts[{index}] missing target_path")
                continue
            src = Path(str(src_value)).resolve()
            dst = Path(str(target_value)).resolve()
            if not src.exists() or not src.is_file():
                errors.append(f"artifacts[{index}] workspace artifact does not exist: {src}")
                continue
            self._require_under_project(src, project_dir, f"artifacts[{index}].workspace_artifact", errors)
            rel_target = self._require_under_project(dst, project_dir, f"artifacts[{index}].target_path", errors)
            if rel_target and not self._is_allowed_target(rel_target):
                errors.append(f"artifacts[{index}] target path is outside allowed copy-out roots: {rel_target}")
            expected_hash = str(artifact.get("content_sha256") or "")
            if not expected_hash:
                errors.append(f"artifacts[{index}] missing content_sha256")
            elif _sha256_file(src) != expected_hash:
                errors.append(f"artifacts[{index}] workspace artifact hash mismatch")
        return errors

    @staticmethod
    def _require_under_project(
        path: Path,
        project_dir: Path,
        label: str,
        errors: List[str],
    ) -> Optional[str]:
        try:
            return path.resolve().relative_to(project_dir).as_posix()
        except ValueError:
            errors.append(f"{label} escapes project root: {path}")
            return None

    @staticmethod
    def _is_allowed_target(rel_path: str) -> bool:
        return any(
            rel_path == root.rstrip("/") or rel_path.startswith(root)
            for root in COPY_OUT_ALLOWED_TARGET_ROOTS
        )
