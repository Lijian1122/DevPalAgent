# -*- coding: utf-8 -*-

import json

from devpal.core.sandbox.copy_out import (
    COPY_OUT_APPLIED_STATUS,
    COPY_OUT_PENDING_STATUS,
    SandboxCopyOutService,
    create_copy_out_manifest,
)
from devpal.core.sandbox.models import SandboxArtifact


def test_copy_out_gate_previews_and_applies_hash_checked_artifacts(tmp_path):
    project = tmp_path / "project"
    workspace = project / ".spec" / "sandboxes" / "phase10-workspace-execution" / "workspace"
    artifact_path = workspace / "build" / "result.bin"
    artifact_path.parent.mkdir(parents=True)
    artifact_path.write_bytes(b"artifact")
    manifest_path = workspace.parent / "copy_out_manifest.json"

    manifest = create_copy_out_manifest(
        project_dir=project,
        workspace_dir=workspace,
        manifest_path=manifest_path,
        artifacts=[
            SandboxArtifact(
                workspace_artifact=artifact_path,
                target_path="build/result.bin",
                content_sha256="",
            )
        ],
    )

    assert manifest["status"] == COPY_OUT_PENDING_STATUS
    assert manifest["artifact_count"] == 1
    target = project / "build" / "result.bin"
    assert not target.exists()

    preview = SandboxCopyOutService().apply_manifest(project, manifest_path)

    assert preview.success is True
    assert preview.status == "PREVIEW"
    assert preview.applied is False
    assert not target.exists()

    applied = SandboxCopyOutService().apply_manifest(project, manifest_path, apply=True)
    updated = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert applied.success is True
    assert applied.status == "APPLIED"
    assert target.read_bytes() == b"artifact"
    assert updated["status"] == COPY_OUT_APPLIED_STATUS
    assert updated["artifacts"][0]["applied"] is True


def test_copy_out_gate_rejects_hash_tampering(tmp_path):
    project = tmp_path / "project"
    workspace = project / ".spec" / "sandboxes" / "phase10-workspace-execution" / "workspace"
    artifact_path = workspace / "build" / "result.bin"
    artifact_path.parent.mkdir(parents=True)
    artifact_path.write_bytes(b"artifact")
    manifest_path = workspace.parent / "copy_out_manifest.json"
    create_copy_out_manifest(
        project_dir=project,
        workspace_dir=workspace,
        manifest_path=manifest_path,
        artifacts=[
            SandboxArtifact(
                workspace_artifact=artifact_path,
                target_path="build/result.bin",
                content_sha256="",
            )
        ],
    )
    artifact_path.write_bytes(b"tampered")

    result = SandboxCopyOutService().apply_manifest(project, manifest_path, apply=True)

    assert result.success is False
    assert "hash mismatch" in " ".join(result.errors)
    assert not (project / "build" / "result.bin").exists()
