# -*- coding: utf-8 -*-
"""Merge pending sandbox artifacts into a project workspace."""

from __future__ import annotations

import difflib
import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


_ALLOWED_TARGET_ROOTS = ("src/", "include/", "tests/", "scripts/")


@dataclass
class SandboxMergeResult:
    success: bool
    status: str
    manifest_path: Optional[Path] = None
    workspace_artifact: Optional[Path] = None
    target_path: Optional[Path] = None
    diff_path: Optional[Path] = None
    applied: bool = False
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "status": self.status,
            "manifest_path": self.manifest_path.as_posix() if self.manifest_path else None,
            "workspace_artifact": self.workspace_artifact.as_posix() if self.workspace_artifact else None,
            "target_path": self.target_path.as_posix() if self.target_path else None,
            "diff_path": self.diff_path.as_posix() if self.diff_path else None,
            "applied": self.applied,
            "errors": list(self.errors),
            "metadata": dict(self.metadata),
        }


class SandboxMergeService:
    def __init__(self, event_integration=None):
        self.event_integration = event_integration

    def merge_manifest(self, project_dir: Path, manifest_path: Path, apply: bool = False) -> SandboxMergeResult:
        project_dir = Path(project_dir).resolve()
        manifest_path = Path(manifest_path)
        if not manifest_path.is_absolute():
            manifest_path = (project_dir / manifest_path).resolve()
        else:
            manifest_path = manifest_path.resolve()

        manifest, errors = self._load_manifest(manifest_path)
        if errors:
            return SandboxMergeResult(
                success=False,
                status="FAILED",
                manifest_path=manifest_path,
                errors=errors,
            )

        workspace_artifact = self._resolve_manifest_path(
            manifest.get("workspace_artifact"),
            project_dir,
        )
        target_path = self._resolve_manifest_path(manifest.get("target_path"), project_dir)
        errors = self._validate(project_dir, manifest_path, manifest, workspace_artifact, target_path)
        if errors:
            self._emit_merge_completed(manifest, target_path, success=False, error="; ".join(errors))
            return SandboxMergeResult(
                success=False,
                status="FAILED",
                manifest_path=manifest_path,
                workspace_artifact=workspace_artifact,
                target_path=target_path,
                errors=errors,
            )

        assert workspace_artifact is not None
        assert target_path is not None
        new_content = workspace_artifact.read_text(encoding="utf-8")
        old_content = target_path.read_text(encoding="utf-8") if target_path.exists() else ""
        diff_text = self._build_diff(project_dir, target_path, old_content, new_content)
        diff_path = manifest_path.with_name("merge.diff")
        diff_path.write_text(diff_text, encoding="utf-8")

        metadata = {
            "sandbox_id": manifest.get("sandbox_id", ""),
            "task_id": manifest.get("task_id", ""),
            "phase_number": manifest.get("phase_number", 0),
            "diff_preview": diff_text[:8000],
            "content_sha256": hashlib.sha256(new_content.encode("utf-8")).hexdigest(),
        }

        if not apply:
            return SandboxMergeResult(
                success=True,
                status="PREVIEW",
                manifest_path=manifest_path,
                workspace_artifact=workspace_artifact,
                target_path=target_path,
                diff_path=diff_path,
                applied=False,
                metadata=metadata,
            )

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(new_content, encoding="utf-8")
        merged_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        manifest.update(
            {
                "status": "merged",
                "merge_status": "merged",
                "merged_at": merged_at,
                "applied": True,
                "requires_manual_merge": False,
                "diff_path": diff_path.as_posix(),
            }
        )
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        self._emit_merge_completed(manifest, target_path, success=True)
        metadata["merged_at"] = merged_at
        return SandboxMergeResult(
            success=True,
            status="MERGED",
            manifest_path=manifest_path,
            workspace_artifact=workspace_artifact,
            target_path=target_path,
            diff_path=diff_path,
            applied=True,
            metadata=metadata,
        )

    def _load_manifest(self, manifest_path: Path) -> tuple[Dict[str, Any], List[str]]:
        if not manifest_path.exists():
            return {}, [f"missing manifest: {manifest_path}"]
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return {}, [f"invalid manifest JSON: {exc}"]
        if not isinstance(data, dict):
            return {}, ["manifest must be a JSON object"]
        return data, []

    def _resolve_manifest_path(self, value: Any, project_dir: Path) -> Optional[Path]:
        if not value:
            return None
        path = Path(str(value))
        if not path.is_absolute():
            path = project_dir / path
        return path.resolve()

    def _validate(
        self,
        project_dir: Path,
        manifest_path: Path,
        manifest: Dict[str, Any],
        workspace_artifact: Optional[Path],
        target_path: Optional[Path],
    ) -> List[str]:
        errors: List[str] = []
        if str(manifest.get("status", "")).lower() != "merge_pending":
            errors.append("manifest status must be merge_pending")
        if workspace_artifact is None:
            errors.append("manifest missing workspace_artifact")
        elif not workspace_artifact.exists():
            errors.append(f"workspace artifact does not exist: {workspace_artifact}")
        else:
            self._require_under_project(workspace_artifact, project_dir, "workspace_artifact", errors)
            expected_hash = manifest.get("content_sha256")
            if expected_hash:
                actual_hash = hashlib.sha256(
                    workspace_artifact.read_text(encoding="utf-8").encode("utf-8")
                ).hexdigest()
                if actual_hash != expected_hash:
                    errors.append("workspace artifact hash mismatch")
        if target_path is None:
            errors.append("manifest missing target_path")
        else:
            rel = self._require_under_project(target_path, project_dir, "target_path", errors)
            if rel and not self._is_allowed_target(rel):
                errors.append(f"target path is outside allowed merge roots: {rel}")
        self._require_under_project(manifest_path, project_dir, "manifest_path", errors)
        return errors

    def _require_under_project(
        self,
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

    def _is_allowed_target(self, rel_path: str) -> bool:
        return any(
            rel_path == root.rstrip("/") or rel_path.startswith(root)
            for root in _ALLOWED_TARGET_ROOTS
        )

    def _build_diff(self, project_dir: Path, target_path: Path, old_content: str, new_content: str) -> str:
        try:
            rel = target_path.relative_to(project_dir).as_posix()
        except ValueError:
            rel = target_path.as_posix()
        return "".join(
            difflib.unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{rel}",
                tofile=f"b/{rel}",
            )
        )

    def _emit_merge_completed(
        self,
        manifest: Dict[str, Any],
        target_path: Optional[Path],
        success: bool,
        error: str = "",
    ) -> None:
        if not self.event_integration or not hasattr(self.event_integration, "emit_agent_merge_completed"):
            return
        self.event_integration.emit_agent_merge_completed(
            int(manifest.get("phase_number", 0) or 0),
            str(manifest.get("task_id", "")),
            sandbox_id=str(manifest.get("sandbox_id", "")),
            artifact_path=str(target_path or ""),
            success=success,
            error=error,
        )
