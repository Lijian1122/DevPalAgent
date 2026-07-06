# -*- coding: utf-8 -*-

import json
from pathlib import Path

from devpal.core.sandbox.runner_schema import validate_runner_request, validate_runner_result


def test_runner_request_schema_rejects_missing_command():
    errors = validate_runner_request(
        {
            "schema_version": "devpal.sandbox.runner_request.v1",
            "sandbox_id": "s1",
            "execution_id": "e1",
            "project_dir": "project",
            "sandbox_dir": "project/.spec/sandboxes/s1",
            "workspace_dir": "project/.spec/sandboxes/s1/workspace",
            "result_path": "project/.spec/sandboxes/s1/runner_result.json",
        }
    )

    assert "missing required field: command" in errors


def test_runner_request_schema_rejects_result_path_escape(tmp_path):
    sandbox_dir = tmp_path / "sandbox"
    errors = validate_runner_request(
        {
            "schema_version": "devpal.sandbox.runner_request.v1",
            "sandbox_id": "s1",
            "execution_id": "e1",
            "project_dir": str(tmp_path),
            "sandbox_dir": str(sandbox_dir),
            "workspace_dir": str(sandbox_dir / "workspace"),
            "result_path": str(tmp_path / "outside.json"),
            "command": {"argv": ["python"], "timeout_seconds": 1, "env": {}},
        }
    )

    assert "result_path escapes sandbox_dir" in errors


def test_runner_request_schema_validates_isolation_flags(tmp_path):
    sandbox_dir = tmp_path / "sandbox"
    errors = validate_runner_request(
        {
            "schema_version": "devpal.sandbox.runner_request.v1",
            "sandbox_id": "s1",
            "execution_id": "e1",
            "project_dir": str(tmp_path),
            "sandbox_dir": str(sandbox_dir),
            "workspace_dir": str(sandbox_dir / "workspace"),
            "result_path": str(sandbox_dir / "runner_result.json"),
            "command": {"argv": ["python"], "timeout_seconds": 1, "env": {}},
            "isolation": {"low_integrity": "yes", "restricted_token": "yes"},
        }
    )

    assert "isolation.low_integrity must be bool" in errors
    assert "isolation.restricted_token must be bool" in errors


def test_runner_request_schema_validates_resource_limits(tmp_path):
    sandbox_dir = tmp_path / "sandbox"
    errors = validate_runner_request(
        {
            "schema_version": "devpal.sandbox.runner_request.v1",
            "sandbox_id": "s1",
            "execution_id": "e1",
            "project_dir": str(tmp_path),
            "sandbox_dir": str(sandbox_dir),
            "workspace_dir": str(sandbox_dir / "workspace"),
            "result_path": str(sandbox_dir / "runner_result.json"),
            "command": {"argv": ["python"], "timeout_seconds": 1, "env": {}},
            "policy": {"max_memory_mb": "64"},
        }
    )

    assert "policy.max_memory_mb must be positive int" in errors


def test_runner_result_schema_accepts_error_code():
    errors = validate_runner_result(
        {
            "schema_version": "devpal.sandbox.runner_result.v1",
            "sandbox_id": "s1",
            "execution_id": "e1",
            "status": "failed",
            "success": False,
            "argv": ["missing.exe"],
            "cwd": "project",
            "exit_code": -1,
            "stdout": "",
            "stderr": "",
            "duration_ms": 1,
            "timed_out": False,
            "cleanup_status": "best_effort",
            "error": "start failed",
            "error_code": "PROCESS_START_FAILED",
        }
    )

    assert errors == []


def test_runner_result_schema_validates_isolation_report():
    errors = validate_runner_result(
        {
            "schema_version": "devpal.sandbox.runner_result.v1",
            "sandbox_id": "s1",
            "execution_id": "e1",
            "status": "failed",
            "success": False,
            "argv": ["python"],
            "cwd": "project",
            "exit_code": -1,
            "stdout": "",
            "stderr": "",
            "duration_ms": 1,
            "timed_out": False,
            "cleanup_status": "not_started",
            "isolation": {
                "low_integrity_requested": "yes",
                "restricted_token_requested": "yes",
                "workspace_acl_path": 123,
            },
        }
    )

    assert "isolation.low_integrity_requested must be bool" in errors
    assert "isolation.restricted_token_requested must be bool" in errors
    assert "isolation.workspace_acl_path must be string" in errors


def test_runner_json_schema_assets_match_schema_versions():
    schema_dir = Path("devpal/core/sandbox/schemas")
    request_schema = json.loads((schema_dir / "runner_request.schema.json").read_text(encoding="utf-8"))
    result_schema = json.loads((schema_dir / "runner_result.schema.json").read_text(encoding="utf-8"))

    assert request_schema["properties"]["schema_version"]["const"] == "devpal.sandbox.runner_request.v1"
    assert result_schema["properties"]["schema_version"]["const"] == "devpal.sandbox.runner_result.v1"
    assert "isolation" in request_schema["properties"]
    assert "isolation" in result_schema["properties"]
    assert "workspace_acl_path" in result_schema["properties"]["isolation"]["properties"]
    assert "restricted_token" in request_schema["properties"]["isolation"]["properties"]
    assert "restricted_token_applied" in result_schema["properties"]["isolation"]["properties"]
    assert "max_memory_mb" in request_schema["properties"]["policy"]["properties"]
    assert "job_memory_limit_mb" in result_schema["properties"]
