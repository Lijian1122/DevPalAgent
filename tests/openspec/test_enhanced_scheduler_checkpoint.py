# -*- coding: utf-8 -*-

import json

from devpal.core.openspec_phases.enhanced_scheduler import CheckpointManager


def test_checkpoint_clear_removes_completed_phases(tmp_path):
    checkpoint_file = tmp_path / ".spec" / "checkpoint.json"
    checkpoint_file.parent.mkdir()
    checkpoint_file.write_text(
        json.dumps({"last_phase": 9, "last_success": True, "completed_phases": list(range(1, 10))}),
        encoding="utf-8",
    )

    checkpoint = CheckpointManager(checkpoint_file)
    assert checkpoint.is_phase_completed(1)
    assert checkpoint.get_resume_phase() == 10

    checkpoint.clear()

    assert not checkpoint_file.exists()
    assert not checkpoint.is_phase_completed(1)
    assert checkpoint.get_resume_phase() == 0
