# -*- coding: utf-8 -*-
"""Archive OpenSpec changes into the long-lived project spec."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .coverage import CoverageMatrixBuilder, CoverageMatrixResult
from .spec_merge import SpecMerger, SpecMergeResult


@dataclass
class ArchiveResult:
    change_id: str
    success: bool
    status: str
    archived_at: str = ""
    merged_spec_path: Optional[Path] = None
    coverage_matrix_path: Optional[Path] = None
    manifest_path: Optional[Path] = None
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "change_id": self.change_id,
            "success": self.success,
            "status": self.status,
            "archived_at": self.archived_at,
            "merged_spec_path": self.merged_spec_path.as_posix() if self.merged_spec_path else None,
            "coverage_matrix_path": self.coverage_matrix_path.as_posix() if self.coverage_matrix_path else None,
            "manifest_path": self.manifest_path.as_posix() if self.manifest_path else None,
            "errors": list(self.errors),
            "metadata": dict(self.metadata),
        }


class ArchiveChangeService:
    def __init__(self, spec_merger: Optional[SpecMerger] = None, coverage_builder: Optional[CoverageMatrixBuilder] = None, event_integration=None):
        self.spec_merger = spec_merger or SpecMerger()
        self.coverage_builder = coverage_builder or CoverageMatrixBuilder()
        self.event_integration = event_integration

    def archive_change(self, project_dir: Path, change_id: str) -> ArchiveResult:
        project_dir = Path(project_dir)
        change_root = self._resolve_change_root(project_dir, change_id)
        archived_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        self._emit("started", change_id=change_id)
        errors = self._preflight(project_dir, change_id, change_root)
        self._emit("preflight_completed", change_id=change_id, success=not errors, errors=errors)
        if errors:
            result = ArchiveResult(change_id=change_id, success=False, status="FAILED", archived_at=archived_at, errors=errors)
            self._emit("failed", **result.to_dict())
            return result

        metadata_path = self._metadata_path(change_root, change_id)
        metadata = self._read_json(metadata_path)
        merge_result = self.spec_merger.merge_change_spec(project_dir, change_id, change_root=change_root)
        self._emit("spec_merged", change_id=change_id, path=merge_result.target_path.as_posix(), merged=merge_result.merged)

        metadata.update({
            "change_id": metadata.get("change_id") or change_id,
            "status": "ARCHIVED",
            "archived_at": archived_at,
            "merged_into": merge_result.target_path.relative_to(project_dir).as_posix(),
        })
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

        coverage = self.coverage_builder.build(project_dir, change_id, metadata)
        self._emit("coverage_generated", change_id=change_id, path=coverage.path.as_posix(), coverage_percent=coverage.coverage_percent)
        self._update_artifact_graph(project_dir, change_id, archived_at, metadata)
        manifest_path = self._write_manifest(project_dir, change_id, archived_at, metadata, merge_result, coverage)

        result = ArchiveResult(
            change_id=change_id,
            success=True,
            status="ARCHIVED",
            archived_at=archived_at,
            merged_spec_path=merge_result.target_path,
            coverage_matrix_path=coverage.path,
            manifest_path=manifest_path,
            metadata={
                "merged": merge_result.merged,
                "coverage_percent": coverage.coverage_percent,
                "total_requirements": coverage.total_requirements,
                "covered_requirements": coverage.covered_requirements,
            },
        )
        self._emit("completed", **result.to_dict())
        return result

    def _preflight(self, project_dir: Path, change_id: str, change_root: Path) -> List[str]:
        errors = []
        change_dir = change_root / "openspec" / "changes" / change_id
        required = [
            change_dir,
            change_dir / "metadata.json",
            change_dir / "proposal.md",
            change_dir / "tasks.md",
            change_dir / "design.md",
            change_dir / "specs" / "spec.md",
        ]
        for path in required:
            if not path.exists():
                errors.append(f"missing required archive input: {path}")
        return errors

    def _update_artifact_graph(self, project_dir: Path, change_id: str, archived_at: str, metadata: Dict[str, Any]) -> None:
        graph_path = project_dir / ".spec" / "artifact_graph.json"
        if not graph_path.exists():
            return
        try:
            data = json.loads(graph_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        requirement_ids = metadata.get("requirements") or metadata.get("requirement_ids") or []
        if isinstance(requirement_ids, str):
            requirement_ids = [requirement_ids]
        for node in data.get("nodes", []):
            node_type = node.get("type")
            if node_type in {"code", "test", "doc", "source"} or str(node.get("id", "")).startswith("file:"):
                node_metadata = node.setdefault("metadata", {})
                node_metadata["change_id"] = change_id
                node_metadata["introduced_by"] = f"openspec/changes/{change_id}"
                node_metadata["archived_at"] = archived_at
                if requirement_ids:
                    node_metadata["requirement_ids"] = requirement_ids
        data.setdefault("archive", {})[change_id] = {
            "status": "ARCHIVED",
            "archived_at": archived_at,
            "introduced_by": f"openspec/changes/{change_id}",
        }
        graph_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _write_manifest(self, project_dir: Path, change_id: str, archived_at: str, metadata: Dict[str, Any], merge_result: SpecMergeResult, coverage: CoverageMatrixResult) -> Path:
        manifest_dir = project_dir / ".spec" / "archive"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / f"{change_id}.json"
        manifest = {
            "change_id": change_id,
            "status": "ARCHIVED",
            "archived_at": archived_at,
            "metadata": metadata,
            "merged_spec_path": merge_result.target_path.relative_to(project_dir).as_posix(),
            "spec_merged": merge_result.merged,
            "coverage": coverage.to_dict(),
        }
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return manifest_path

    def _metadata_path(self, change_root: Path, change_id: str) -> Path:
        return change_root / "openspec" / "changes" / change_id / "metadata.json"

    def _resolve_change_root(self, project_dir: Path, change_id: str) -> Path:
        if (project_dir / "openspec" / "changes" / change_id).exists():
            return project_dir
        parent = project_dir.parent
        if (parent / "openspec" / "changes" / change_id).exists():
            return parent
        return project_dir

    def _read_json(self, path: Path) -> Dict[str, Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _emit(self, event_name: str, **payload) -> None:
        if self.event_integration and hasattr(self.event_integration, "emit_archive_event"):
            self.event_integration.emit_archive_event(event_name, payload)
