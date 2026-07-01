# -*- coding: utf-8 -*-

import hashlib

import pytest

from devpal.core.sandbox import (
    SANDBOX_MANIFEST_SCHEMA_VERSION,
    ManifestValidationError,
    SandboxArtifact,
    SandboxRequest,
    build_manifest_v2,
    read_manifest_v2,
    validate_manifest_v2,
    write_manifest_v2,
)


def test_manifest_v2_roundtrip(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    workspace_artifact = project / ".spec" / "sandboxes" / "demo" / "workspace" / "src" / "app.py"
    workspace_artifact.parent.mkdir(parents=True, exist_ok=True)
    content = "print('hello')\n"
    workspace_artifact.write_text(content, encoding="utf-8")
    request = SandboxRequest.from_legacy(
        project,
        task_id="phase4:src/app.py",
        phase_number=4,
        role="codegen",
        sandbox_level="strict",
        allowed_paths=["src/app.py"],
        execution_id="exec-demo",
        trace_id="trace-demo",
    )
    manifest_path = project / ".spec" / "sandboxes" / "demo" / "manifest.v2.json"

    manifest = build_manifest_v2(
        request,
        sandbox_id="demo",
        sandbox_dir=manifest_path.parent,
        workspace_dir=workspace_artifact.parents[1],
        manifest_path=manifest_path,
        status="generated",
        artifacts=[
            SandboxArtifact(
                workspace_artifact=workspace_artifact,
                target_path=project / "src" / "app.py",
                content_sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
            )
        ],
    )
    written = write_manifest_v2(manifest_path, manifest)
    loaded = read_manifest_v2(written)

    assert loaded["schema_version"] == SANDBOX_MANIFEST_SCHEMA_VERSION
    assert loaded["sandbox_id"] == "demo"
    assert loaded["execution_id"] == "exec-demo"
    assert loaded["policy"]["sandbox_level"] == "strict"
    assert loaded["policy"]["allowed_paths"] == ["src/app.py"]
    assert loaded["artifacts"][0]["content_sha256"]
    assert validate_manifest_v2(loaded) == []


def test_manifest_v2_validation_reports_schema_errors():
    errors = validate_manifest_v2(
        {
            "schema_version": "wrong",
            "sandbox_id": "demo",
        }
    )

    assert "schema_version must be" in " ".join(errors)
    assert "missing required field: execution_id" in errors
    assert "missing required field: policy" in errors


def test_read_manifest_v2_rejects_invalid_schema(tmp_path):
    manifest_path = tmp_path / "manifest.v2.json"
    manifest_path.write_text('{"schema_version": "wrong"}', encoding="utf-8")

    with pytest.raises(ManifestValidationError):
        read_manifest_v2(manifest_path)
