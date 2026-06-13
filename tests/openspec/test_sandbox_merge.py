# -*- coding: utf-8 -*-

import hashlib
import json
import subprocess
import sys

from devpal.openspec import SandboxMergeService


def _make_pending_manifest(project, content="print('hello')\n", target_path=None):
    workspace_artifact = project / ".spec" / "sandboxes" / "phase4-codegen-demo" / "workspace" / "src" / "app.py"
    workspace_artifact.parent.mkdir(parents=True, exist_ok=True)
    workspace_artifact.write_text(content, encoding="utf-8")
    manifest_path = workspace_artifact.parents[2] / "manifest.json"
    manifest = {
        "sandbox_id": "phase4-codegen-demo",
        "task_id": "phase4:src/app.py",
        "phase_number": 4,
        "role": "merge",
        "sandbox_level": "production",
        "status": "merge_pending",
        "requires_manual_merge": True,
        "workspace_artifact": str(workspace_artifact),
        "target_path": str(target_path or (project / "src" / "app.py")),
        "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path, workspace_artifact


def test_sandbox_merge_preview_does_not_write_target(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    manifest_path, _ = _make_pending_manifest(project)

    result = SandboxMergeService().merge_manifest(project, manifest_path, apply=False)

    assert result.success is True
    assert result.status == "PREVIEW"
    assert result.applied is False
    assert result.diff_path and result.diff_path.exists()
    assert not (project / "src" / "app.py").exists()


def test_sandbox_merge_apply_writes_target_and_updates_manifest(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    manifest_path, workspace_artifact = _make_pending_manifest(project, content="value = 42\n")

    result = SandboxMergeService().merge_manifest(project, manifest_path, apply=True)

    assert result.success is True
    assert result.status == "MERGED"
    assert result.applied is True
    assert (project / "src" / "app.py").read_text(encoding="utf-8") == workspace_artifact.read_text(encoding="utf-8")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "merged"
    assert manifest["requires_manual_merge"] is False
    assert manifest["applied"] is True
    assert "merged_at" in manifest


def test_sandbox_merge_rejects_hash_mismatch(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    manifest_path, workspace_artifact = _make_pending_manifest(project)
    workspace_artifact.write_text("tampered\n", encoding="utf-8")

    result = SandboxMergeService().merge_manifest(project, manifest_path, apply=True)

    assert result.success is False
    assert "hash mismatch" in " ".join(result.errors)
    assert not (project / "src" / "app.py").exists()


def test_sandbox_merge_rejects_target_outside_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside.py"
    manifest_path, _ = _make_pending_manifest(project, target_path=outside)

    result = SandboxMergeService().merge_manifest(project, manifest_path, apply=True)

    assert result.success is False
    assert "target_path escapes project root" in " ".join(result.errors)
    assert not outside.exists()


def test_sandbox_merge_cli_applies_manifest(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    manifest_path, _ = _make_pending_manifest(project, content="name = 'cli'\n")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "devpal.openspec",
            "merge-sandbox",
            str(manifest_path),
            "--project-dir",
            str(project),
            "--apply",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )

    assert completed.returncode == 0, completed.stderr
    data = json.loads(completed.stdout)
    assert data["success"] is True
    assert data["status"] == "MERGED"
    assert (project / "src" / "app.py").read_text(encoding="utf-8") == "name = 'cli'\n"
