# -*- coding: utf-8 -*-
"""Cleanup stale sandbox workspaces from manifest v2 records."""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Set


STALE_STATUSES = {"timeout", "failed", "running", "created"}


@dataclass
class ReaperEntry:
    manifest_path: Path
    sandbox_dir: Path
    status: str
    age_seconds: int
    action: str
    workflow_id: str = ""
    task_id: str = ""
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "manifest_path": self.manifest_path.as_posix(),
            "sandbox_dir": self.sandbox_dir.as_posix(),
            "status": self.status,
            "age_seconds": self.age_seconds,
            "action": self.action,
            "workflow_id": self.workflow_id,
            "task_id": self.task_id,
            "error": self.error,
        }


@dataclass
class ReaperReport:
    project_dir: Path
    dry_run: bool
    entries: List[ReaperEntry] = field(default_factory=list)

    @property
    def cleaned_count(self) -> int:
        return sum(1 for entry in self.entries if entry.action == "cleaned")

    @property
    def candidate_count(self) -> int:
        return sum(1 for entry in self.entries if entry.action in {"would_clean", "cleaned"})

    def to_dict(self) -> dict:
        return {
            "project_dir": self.project_dir.as_posix(),
            "dry_run": self.dry_run,
            "candidate_count": self.candidate_count,
            "cleaned_count": self.cleaned_count,
            "entries": [entry.to_dict() for entry in self.entries],
        }


class SandboxReaper:
    def __init__(
        self,
        project_dir: Path | str,
        stale_after_seconds: int = 3600,
        statuses: Iterable[str] | None = None,
        workflow_id: str = "",
        task_id: str = "",
    ):
        self.project_dir = Path(project_dir).resolve()
        self.sandbox_root = self.project_dir / ".spec" / "sandboxes"
        self.stale_after = timedelta(seconds=max(0, int(stale_after_seconds)))
        self.statuses: Set[str] = {
            str(status).lower() for status in (statuses or STALE_STATUSES)
        }
        self.workflow_id = workflow_id
        self.task_id = task_id

    def reap(self, *, dry_run: bool = True) -> ReaperReport:
        report = ReaperReport(project_dir=self.project_dir, dry_run=dry_run)
        if not self.sandbox_root.exists():
            return report
        for manifest_path in self.sandbox_root.rglob("manifest.v2.json"):
            entry = self._inspect_manifest(manifest_path, dry_run=dry_run)
            if entry:
                report.entries.append(entry)
        return report

    def _inspect_manifest(self, manifest_path: Path, *, dry_run: bool) -> ReaperEntry | None:
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            status = str(data.get("status", "")).lower()
            workflow_id = str(data.get("workflow_id", "") or "")
            task_id = str(data.get("task_id", "") or "")
            sandbox_dir = Path(data.get("workspace", {}).get("sandbox_dir") or manifest_path.parent).resolve()
            sandbox_dir.relative_to(self.sandbox_root.resolve())
            age_seconds = self._age_seconds(manifest_path)
            if status not in self.statuses or timedelta(seconds=age_seconds) < self.stale_after:
                return None
            if self.workflow_id and workflow_id != self.workflow_id:
                return None
            if self.task_id and task_id != self.task_id:
                return None
            if dry_run:
                return ReaperEntry(
                    manifest_path,
                    sandbox_dir,
                    status,
                    age_seconds,
                    "would_clean",
                    workflow_id=workflow_id,
                    task_id=task_id,
                )
            shutil.rmtree(sandbox_dir)
            return ReaperEntry(
                manifest_path,
                sandbox_dir,
                status,
                age_seconds,
                "cleaned",
                workflow_id=workflow_id,
                task_id=task_id,
            )
        except Exception as exc:
            return ReaperEntry(
                manifest_path,
                manifest_path.parent,
                "unknown",
                0,
                "error",
                error=str(exc),
            )

    @staticmethod
    def _age_seconds(path: Path) -> int:
        modified = datetime.fromtimestamp(path.stat().st_mtime, UTC)
        return max(0, int((datetime.now(UTC) - modified).total_seconds()))


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reap stale DevPal sandbox workspaces")
    parser.add_argument("--project-dir", default=".", help="Project directory")
    parser.add_argument("--stale-after-seconds", type=int, default=3600)
    parser.add_argument("--status", action="append", help="Status to clean; repeatable")
    parser.add_argument("--workflow-id", default="", help="Only clean sandboxes for this workflow")
    parser.add_argument("--task-id", default="", help="Only clean sandboxes for this task")
    parser.add_argument("--apply", action="store_true", help="Actually remove candidates")
    args = parser.parse_args(list(argv) if argv is not None else None)

    report = SandboxReaper(
        args.project_dir,
        args.stale_after_seconds,
        statuses=args.status,
        workflow_id=args.workflow_id,
        task_id=args.task_id,
    ).reap(dry_run=not args.apply)
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
