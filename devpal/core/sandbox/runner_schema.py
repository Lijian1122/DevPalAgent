# -*- coding: utf-8 -*-
"""Validation helpers for sandbox runner request/result JSON."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


RUNNER_REQUEST_SCHEMA_VERSION = "devpal.sandbox.runner_request.v1"
RUNNER_RESULT_SCHEMA_VERSION = "devpal.sandbox.runner_result.v1"


def validate_runner_request(data: Any) -> List[str]:
    errors: List[str] = []
    if not isinstance(data, dict):
        return ["runner request must be an object"]

    _require(data, "schema_version", str, errors)
    _require(data, "sandbox_id", str, errors)
    _require(data, "execution_id", str, errors)
    _require(data, "project_dir", str, errors)
    _require(data, "sandbox_dir", str, errors)
    _require(data, "workspace_dir", str, errors)
    _require(data, "result_path", str, errors)
    _require(data, "command", dict, errors)

    if data.get("schema_version") != RUNNER_REQUEST_SCHEMA_VERSION:
        errors.append(f"schema_version must be {RUNNER_REQUEST_SCHEMA_VERSION}")

    command = data.get("command")
    if isinstance(command, dict):
        argv = command.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(item, str) for item in argv):
            errors.append("command.argv must be a non-empty list of strings")
        timeout = command.get("timeout_seconds")
        if not isinstance(timeout, int) or timeout <= 0:
            errors.append("command.timeout_seconds must be a positive int")
        env = command.get("env")
        if env is not None and not isinstance(env, dict):
            errors.append("command.env must be an object")
        if env is not None and isinstance(env, dict):
            for key, value in env.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    errors.append("command.env keys and values must be strings")
                    break

    policy = data.get("policy")
    if policy is not None:
        if not isinstance(policy, dict):
            errors.append("policy must be an object")
        else:
            for key in ["max_processes", "max_memory_mb"]:
                value = policy.get(key)
                if value is not None and (not isinstance(value, int) or value <= 0):
                    errors.append(f"policy.{key} must be positive int")

    isolation = data.get("isolation")
    if isolation is not None:
        if not isinstance(isolation, dict):
            errors.append("isolation must be an object")
        else:
            for key in ["low_integrity", "harden_workspace_acl", "network_deny", "restricted_token"]:
                if key in isolation and not isinstance(isolation[key], bool):
                    errors.append(f"isolation.{key} must be bool")

    _validate_path_boundary(data, "workspace_dir", "sandbox_dir", errors)
    _validate_path_boundary(data, "result_path", "sandbox_dir", errors)
    return errors


def validate_runner_result(data: Any) -> List[str]:
    errors: List[str] = []
    if not isinstance(data, dict):
        return ["runner result must be an object"]

    _require(data, "schema_version", str, errors)
    _require(data, "sandbox_id", str, errors)
    _require(data, "execution_id", str, errors)
    _require(data, "status", str, errors)
    _require(data, "success", bool, errors)
    _require(data, "argv", list, errors)
    _require(data, "cwd", str, errors)
    _require(data, "exit_code", int, errors)
    _require(data, "stdout", str, errors)
    _require(data, "stderr", str, errors)
    _require(data, "duration_ms", int, errors)
    _require(data, "timed_out", bool, errors)
    _require(data, "cleanup_status", str, errors)

    if data.get("schema_version") != RUNNER_RESULT_SCHEMA_VERSION:
        errors.append(f"schema_version must be {RUNNER_RESULT_SCHEMA_VERSION}")
    if data.get("error_code") is not None and not isinstance(data.get("error_code"), str):
        errors.append("error_code must be string")
    if data.get("job_memory_limit_mb") is not None:
        value = data.get("job_memory_limit_mb")
        if not isinstance(value, int) or value <= 0:
            errors.append("job_memory_limit_mb must be positive int")
    isolation = data.get("isolation")
    if isolation is not None:
        if not isinstance(isolation, dict):
            errors.append("isolation must be an object")
        else:
            for key in [
                "low_integrity_requested",
                "low_integrity_applied",
                "workspace_acl_requested",
                "workspace_acl_hardened",
                "network_deny_requested",
                "network_deny_applied",
                "restricted_token_requested",
                "restricted_token_applied",
            ]:
                if key in isolation and not isinstance(isolation[key], bool):
                    errors.append(f"isolation.{key} must be bool")
            for key in [
                "low_integrity_error",
                "workspace_acl_path",
                "workspace_acl_error",
                "network_rule_name",
                "network_error",
                "restricted_token_error",
                "process_launcher",
            ]:
                if isolation.get(key) is not None and not isinstance(isolation[key], str):
                    errors.append(f"isolation.{key} must be string")
    return errors


def _require(data: Dict[str, Any], key: str, expected_type: type, errors: List[str]) -> None:
    if key not in data:
        errors.append(f"missing required field: {key}")
        return
    if not isinstance(data[key], expected_type):
        errors.append(f"{key} must be {expected_type.__name__}")


def _validate_path_boundary(data: Dict[str, Any], child_key: str, parent_key: str, errors: List[str]) -> None:
    child_value = data.get(child_key)
    parent_value = data.get(parent_key)
    if not isinstance(child_value, str) or not isinstance(parent_value, str):
        return
    try:
        child = Path(child_value).resolve()
        parent = Path(parent_value).resolve()
        child.relative_to(parent)
    except Exception:
        errors.append(f"{child_key} escapes {parent_key}")
