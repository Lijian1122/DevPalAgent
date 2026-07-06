# -*- coding: utf-8 -*-

import hashlib
import json
from pathlib import Path

import pytest

from devpal.core.multi_agent import CommandSpec, SandboxSession
from devpal.openspec.sandbox_merge import SandboxMergeService


def _sandbox(tmp_path):
    return SandboxSession(
        project_dir=tmp_path,
        task_id="phase10:redteam",
        phase_number=10,
        role="test",
        sandbox_level="strict",
        allowed_paths=["src/allowed.py"],
    )


@pytest.mark.parametrize(
    "rel_path",
    [
        "../escape.py",
        "src/../../escape.py",
    ],
)
def test_sandbox_rejects_workspace_path_escape(tmp_path, rel_path):
    sandbox = _sandbox(tmp_path)

    with pytest.raises(ValueError, match="path escapes project root|workspace path escapes sandbox"):
        sandbox.resolve_workspace_target(rel_path)


@pytest.mark.parametrize(
    "argv",
    [
        ["powershell", "-Command", "Get-ChildItem"],
        ["cmd", "/c", "dir"],
        ["curl", "https://example.com"],
    ],
)
def test_sandbox_rejects_dangerous_command_entrypoints(tmp_path, argv):
    sandbox = _sandbox(tmp_path)

    with pytest.raises(ValueError):
        sandbox.validate_command(CommandSpec(argv=argv, cwd=tmp_path))


def test_sandbox_rejects_shell_string_command(tmp_path):
    sandbox = _sandbox(tmp_path)

    with pytest.raises(ValueError, match="command argv must be a list"):
        sandbox.validate_command(CommandSpec(argv="pytest tests", cwd=tmp_path))  # type: ignore[arg-type]


def test_sandbox_rejects_command_cwd_outside_project(tmp_path):
    sandbox = _sandbox(tmp_path)

    with pytest.raises(ValueError, match="command cwd escapes project root"):
        sandbox.validate_command(CommandSpec(argv=["pytest", "tests"], cwd=tmp_path.parent))


def test_sandbox_merge_rejects_manifest_hash_tampering(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    workspace = project / ".spec" / "sandboxes" / "merge" / "workspace"
    workspace.mkdir(parents=True)
    artifact = workspace / "allowed.py"
    artifact.write_text("print('tampered')\n", encoding="utf-8")
    manifest = {
        "sandbox_id": "merge",
        "task_id": "phase4:src/allowed.py",
        "phase_number": 4,
        "role": "codegen",
        "target_path": "src/allowed.py",
        "workspace_artifact": str(artifact),
        "status": "merge_pending",
        "requires_manual_merge": True,
        "content_sha256": hashlib.sha256(b"different").hexdigest(),
    }
    manifest_path = workspace.parent / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = SandboxMergeService().merge_manifest(project, manifest_path, apply=True)

    assert result.success is False
    assert "hash mismatch" in " ".join(result.errors)
