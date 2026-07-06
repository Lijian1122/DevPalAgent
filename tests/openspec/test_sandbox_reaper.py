# -*- coding: utf-8 -*-

import json
import os
import time

from devpal.core.sandbox.reaper import SandboxReaper


def _write_manifest(project, sandbox_id, status, workflow_id="", task_id=""):
    sandbox_dir = project / ".spec" / "sandboxes" / sandbox_id
    sandbox_dir.mkdir(parents=True)
    manifest = {
        "status": status,
        "workflow_id": workflow_id,
        "task_id": task_id,
        "workspace": {
            "sandbox_dir": str(sandbox_dir),
        },
    }
    manifest_path = sandbox_dir / "manifest.v2.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    old = time.time() - 120
    os.utime(manifest_path, (old, old))
    return sandbox_dir, manifest_path


def test_reaper_dry_run_reports_stale_failed_sandbox(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    sandbox_dir, _ = _write_manifest(project, "failed-1", "failed")

    report = SandboxReaper(project, stale_after_seconds=1).reap(dry_run=True)

    assert report.candidate_count == 1
    assert report.cleaned_count == 0
    assert report.entries[0].sandbox_dir == sandbox_dir.resolve()
    assert report.entries[0].action == "would_clean"
    assert sandbox_dir.exists()


def test_reaper_apply_removes_stale_sandbox(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    sandbox_dir, _ = _write_manifest(project, "timeout-1", "timeout")

    report = SandboxReaper(project, stale_after_seconds=1).reap(dry_run=False)

    assert report.cleaned_count == 1
    assert not sandbox_dir.exists()


def test_reaper_ignores_completed_sandbox(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    sandbox_dir, _ = _write_manifest(project, "completed-1", "completed")

    report = SandboxReaper(project, stale_after_seconds=1).reap(dry_run=False)

    assert report.candidate_count == 0
    assert sandbox_dir.exists()


def test_reaper_filters_by_status_workflow_and_task(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    matched, _ = _write_manifest(
        project,
        "failed-match",
        "failed",
        workflow_id="wf-1",
        task_id="phase10:test",
    )
    ignored_status, _ = _write_manifest(
        project,
        "timeout-ignore",
        "timeout",
        workflow_id="wf-1",
        task_id="phase10:test",
    )
    ignored_workflow, _ = _write_manifest(
        project,
        "failed-other-wf",
        "failed",
        workflow_id="wf-2",
        task_id="phase10:test",
    )

    report = SandboxReaper(
        project,
        stale_after_seconds=1,
        statuses=["failed"],
        workflow_id="wf-1",
        task_id="phase10:test",
    ).reap(dry_run=True)

    assert report.candidate_count == 1
    assert report.entries[0].sandbox_dir == matched.resolve()
    assert report.entries[0].workflow_id == "wf-1"
    assert report.entries[0].task_id == "phase10:test"
    assert ignored_status.exists()
    assert ignored_workflow.exists()
