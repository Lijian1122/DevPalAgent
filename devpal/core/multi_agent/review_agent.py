# -*- coding: utf-8 -*-
"""Deterministic review agent for Phase 9 quality gate."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, List

from .models import AgentPolicy, AgentResult, AgentTask
from .sandbox import SandboxSession

ReviewChecker = Callable[[Path, List[str]], List[dict]]


class ReviewAgent:
    def __init__(self, policy: AgentPolicy, checker: ReviewChecker):
        self.policy = policy
        self.checker = checker

    def execute(self, task: AgentTask) -> AgentResult:
        start = time.time()
        project_dir = Path(task.input_payload["project_dir"])
        file_path = Path(task.input_payload["file_path"])
        check_types = list(task.input_payload.get("check_types") or [])
        sandbox = SandboxSession(
            project_dir=project_dir,
            task_id=task.task_id,
            phase_number=task.phase_number,
            role=task.role,
            sandbox_level=self.policy.sandbox_level,
        )
        try:
            target = file_path.resolve()
            target.relative_to(project_dir.resolve())
        except ValueError as exc:
            manifest_path = sandbox.write_manifest(
                [],
                status="policy_violation",
                policy_violations=[{"reason": str(exc), "path": str(file_path)}],
            )
            return AgentResult(
                task_id=task.task_id,
                success=False,
                duration_ms=int((time.time() - start) * 1000),
                error=f"review path escapes project root: {file_path}",
                sandbox_id=sandbox.sandbox_id,
                policy_violations=[{"reason": str(exc), "path": str(file_path)}],
                metadata={"file_path": str(file_path), "issues": [], "manifest_path": str(manifest_path), "sandbox": sandbox.manifest()},
            )

        try:
            issues = self.checker(target, check_types)
        except Exception as exc:
            manifest_path = sandbox.write_manifest(
                [target],
                status="failed",
                error=str(exc),
                reviewed_file=str(target),
            )
            return AgentResult(
                task_id=task.task_id,
                success=False,
                duration_ms=int((time.time() - start) * 1000),
                error=str(exc),
                sandbox_id=sandbox.sandbox_id,
                metadata={"file_path": str(file_path), "issues": [], "manifest_path": str(manifest_path), "sandbox": sandbox.manifest([target])},
            )

        manifest_path = sandbox.write_manifest(
            [target],
            status="completed",
            reviewed_file=str(target),
            issue_count=len(issues),
        )
        return AgentResult(
            task_id=task.task_id,
            success=True,
            duration_ms=int((time.time() - start) * 1000),
            sandbox_id=sandbox.sandbox_id,
            metadata={
                "file_path": str(file_path),
                "issues": issues,
                "manifest_path": str(manifest_path),
                "sandbox": sandbox.manifest([target]),
            },
        )
