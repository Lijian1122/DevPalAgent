# -*- coding: utf-8 -*-
"""File-level code generation agent for OpenSpec Phase 4."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable, Dict, List

from .content_sanitizer import (
    cpp_header_public_incomplete_type_errors,
    has_unified_diff_markers,
    missing_local_includes,
    sanitize_generated_content,
)
from .models import AgentPolicy, AgentResult, AgentTask
from .sandbox import SandboxSession


_WRITE_FILE_TOOL: Dict[str, Any] = {
    "name": "write_file",
    "description": "Write the single file assigned to this codegen task.",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Project-relative path"},
            "content": {"type": "string", "description": "Full file content"},
            "description": {"type": "string", "description": "Optional description"},
        },
        "required": ["path", "content"],
    },
}


class CodegenAgent:
    def __init__(self, client_factory: Callable[[], Any], policy: AgentPolicy):
        self.client_factory = client_factory
        self.policy = policy

    def execute(self, task: AgentTask) -> AgentResult:
        start = time.time()
        item = task.input_payload["plan_item"]
        project_dir = Path(task.input_payload["project_dir"])
        sandbox = SandboxSession(
            project_dir=project_dir,
            task_id=task.task_id,
            phase_number=task.phase_number,
            role=task.role,
            sandbox_level=self.policy.sandbox_level,
            allowed_paths=task.allowed_paths or [item.path],
        )
        try:
            target = sandbox.resolve_target(item.path)
        except ValueError as exc:
            return self._failure(task, sandbox, start, str(exc), item.path)

        generated_content: List[str] = []

        def tool_handler(tool_name, tool_input):
            if tool_name != "write_file":
                return f"[error] unknown tool {tool_name}"
            rel = (tool_input.get("path") or "").strip()
            content = tool_input.get("content") or ""
            try:
                normalized = sandbox.normalize_relative_path(rel)
            except ValueError as exc:
                return f"[error] {exc}"
            if normalized != item.path:
                return f"[error] this task may only write {item.path}"
            if not content:
                return "[error] content is required"
            if has_unified_diff_markers(content):
                return "[error] content must be the complete file body, not a diff or patch"
            content, _ = sanitize_generated_content(content)
            if not content.strip():
                return "[error] content is empty"
            missing_includes = missing_local_includes(
                content,
                normalized,
                project_dir,
                task.input_payload.get("planned_paths", []),
            )
            if missing_includes:
                return (
                    "[error] local include(s) are not generated or planned: "
                    + ", ".join(missing_includes)
                )
            incomplete_errors = cpp_header_public_incomplete_type_errors(content)
            if incomplete_errors:
                return "[error] " + "; ".join(incomplete_errors)
            generated_content.append(content)
            return f"accepted {normalized}"

        user_message = (
            task.input_payload["base_user_message"]
            + "\n\n=== SINGLE FILE TASK OVERRIDE ===\n"
            + f"Generate exactly one file: {item.path}\n"
            + f"Purpose: {item.purpose}\n"
            + f"Stage: {item.stage}\n"
            + "For this agent task, ignore any earlier instruction to generate multiple files.\n"
            + "Call write_file exactly once for this path and do not write any other file.\n"
            + "The content must be the complete file content, not a diff or patch.\n"
        )

        try:
            client = self.client_factory()
            result = client.generate_with_tool_loop(
                system=task.input_payload["system_prompt"],
                user_message=user_message,
                tools=[_WRITE_FILE_TOOL],
                tool_handler=tool_handler,
                cached_context=task.input_payload["cached_context"],
                max_turns=5,
                max_tokens=4096,
            )
        except Exception as exc:
            return self._failure(task, sandbox, start, str(exc), item.path)

        if not generated_content:
            stop_reason = getattr(result, "stop_reason", "unknown")
            return self._failure(
                task,
                sandbox,
                start,
                f"LLM did not produce {item.path}: stop_reason={stop_reason}",
                item.path,
                {"turns": getattr(result, "turns", 0)},
            )

        usage = getattr(client, "usage", None)
        workspace_target = sandbox.resolve_workspace_target(item.path)
        workspace_target.parent.mkdir(parents=True, exist_ok=True)
        workspace_target.write_text(generated_content[-1], encoding="utf-8")
        manifest_path = sandbox.write_manifest(
            [workspace_target],
            target_path=str(target),
            workspace_artifact=str(workspace_target),
            status="generated",
        )
        metadata = {
            "path": item.path,
            "content": generated_content[-1],
            "workspace_artifact": str(workspace_target),
            "manifest_path": str(manifest_path),
            "turns": getattr(result, "turns", 0),
            "llm_calls": getattr(usage, "calls", 0),
            "llm_input_tokens": getattr(usage, "input_tokens", 0),
            "llm_output_tokens": getattr(usage, "output_tokens", 0),
            "llm_cache_read_tokens": getattr(usage, "cache_read_tokens", 0),
            "llm_cache_creation_tokens": getattr(usage, "cache_creation_tokens", 0),
            "sandbox": sandbox.manifest([workspace_target]),
        }
        return AgentResult(
            task_id=task.task_id,
            success=True,
            artifacts=[workspace_target],
            artifact_path=workspace_target,
            duration_ms=int((time.time() - start) * 1000),
            sandbox_id=sandbox.sandbox_id,
            metadata=metadata,
        )

    def _failure(
        self,
        task: AgentTask,
        sandbox: SandboxSession,
        start: float,
        error: str,
        path: str,
        metadata: Dict[str, Any] | None = None,
    ) -> AgentResult:
        details = {"path": path}
        if metadata:
            details.update(metadata)
        try:
            manifest_path = sandbox.write_manifest(
                [],
                status="failed",
                error=error,
                target_path=path,
            )
            details["manifest_path"] = str(manifest_path)
            details["sandbox"] = sandbox.manifest()
        except Exception:
            pass
        return AgentResult(
            task_id=task.task_id,
            success=False,
            duration_ms=int((time.time() - start) * 1000),
            error=error,
            sandbox_id=sandbox.sandbox_id,
            metadata=details,
        )
