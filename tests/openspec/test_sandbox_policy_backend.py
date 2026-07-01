# -*- coding: utf-8 -*-

import json

import pytest

from devpal.core.multi_agent import CommandSpec
from devpal.core.sandbox import SandboxRequest, read_manifest_v2
from devpal.core.sandbox.backends import PolicySandboxBackend


def test_policy_backend_resolves_allowed_target_like_legacy_session(tmp_path):
    request = SandboxRequest.from_legacy(
        tmp_path,
        task_id="phase4:src/example.py",
        phase_number=4,
        role="codegen",
        sandbox_level="strict",
        allowed_paths=["src/example.py"],
    )
    session = PolicySandboxBackend().create_session(request)

    assert session.resolve_target("src/example.py") == (tmp_path / "src" / "example.py").resolve()


def test_policy_backend_preserves_strict_allowed_path_requirement(tmp_path):
    request = SandboxRequest.from_legacy(
        tmp_path,
        task_id="phase4:src/example.py",
        phase_number=4,
        role="codegen",
        sandbox_level="strict",
    )
    session = PolicySandboxBackend().create_session(request)

    with pytest.raises(ValueError, match="strict sandbox requires explicit allowed_paths"):
        session.resolve_target("src/example.py")


def test_policy_backend_preserves_production_command_block(tmp_path):
    request = SandboxRequest.from_legacy(
        tmp_path,
        task_id="phase10:test",
        phase_number=10,
        role="test",
        sandbox_level="production",
        allowed_paths=["tests/test_example.py"],
    )
    session = PolicySandboxBackend().create_session(request)

    with pytest.raises(ValueError, match="production sandbox does not allow local command execution"):
        session.validate_command(CommandSpec(argv=["pytest", "tests"], cwd=tmp_path))


def test_policy_backend_writes_legacy_and_v2_manifests(tmp_path):
    request = SandboxRequest.from_legacy(
        tmp_path,
        task_id="phase4:src/example.py",
        phase_number=4,
        role="codegen",
        sandbox_level="strict",
        allowed_paths=["src/example.py"],
        execution_id="exec-policy",
    )
    session = PolicySandboxBackend().create_session(request)
    workspace_target = session.resolve_workspace_target("src/example.py")
    workspace_target.parent.mkdir(parents=True, exist_ok=True)
    workspace_target.write_text("print('ok')\n", encoding="utf-8")

    legacy_manifest = session.write_manifest([workspace_target], status="generated")
    manifest_v2 = session.write_manifest_v2([workspace_target], status="generated")

    legacy = json.loads(legacy_manifest.read_text(encoding="utf-8"))
    loaded_v2 = read_manifest_v2(manifest_v2)
    assert legacy["sandbox_id"] == session.sandbox_id
    assert legacy["status"] == "generated"
    assert loaded_v2["schema_version"] == "devpal.sandbox.manifest.v2"
    assert loaded_v2["backend"] == "policy"
    assert loaded_v2["isolation_level"] == "policy"
