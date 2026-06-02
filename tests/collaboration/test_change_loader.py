# -*- coding: utf-8 -*-
"""Tests for collaboration.change_loader module."""

import json
import pytest
from pathlib import Path
from devpal.collaboration.change_loader import ChangeLoader


def test_change_loader_init(tmp_path):
    """Test ChangeLoader initialization."""
    loader = ChangeLoader(tmp_path)

    assert loader.project_dir == tmp_path
    assert loader.changes_dir == tmp_path / "openspec" / "changes"


def test_load_change_success(tmp_path):
    """Test loading a valid change."""
    # Create change structure
    change_id = "test-change-001"
    change_dir = tmp_path / "openspec" / "changes" / change_id
    change_dir.mkdir(parents=True)

    # Create metadata
    metadata = {
        "change_id": change_id,
        "status": "PROPOSED",
        "project_type": "python",
        "language": "python",
    }
    (change_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    # Create artifacts
    (change_dir / "proposal.md").write_text("# Proposal\nTest proposal", encoding="utf-8")
    (change_dir / "tasks.md").write_text("- [ ] Task 1\n- [ ] Task 2", encoding="utf-8")
    (change_dir / "design.md").write_text("# Design\nTest design", encoding="utf-8")
    (change_dir / "specs").mkdir()
    (change_dir / "specs" / "spec.md").write_text("# Spec\nTest spec", encoding="utf-8")

    # Load change
    loader = ChangeLoader(tmp_path)
    artifacts = loader.load_change(change_id)

    assert artifacts["change_id"] == change_id
    assert artifacts["metadata"]["status"] == "PROPOSED"
    assert "Test proposal" in artifacts["proposal"]
    assert "Task 1" in artifacts["tasks"]
    assert "Test design" in artifacts["design"]
    assert "Test spec" in artifacts["spec"]


def test_load_change_not_found(tmp_path):
    """Test loading non-existent change."""
    loader = ChangeLoader(tmp_path)

    with pytest.raises(FileNotFoundError, match="Change not found"):
        loader.load_change("non-existent")


def test_load_change_missing_metadata(tmp_path):
    """Test loading change without metadata."""
    change_id = "test-change-002"
    change_dir = tmp_path / "openspec" / "changes" / change_id
    change_dir.mkdir(parents=True)

    loader = ChangeLoader(tmp_path)

    with pytest.raises(FileNotFoundError, match="metadata.json not found"):
        loader.load_change(change_id)


def test_list_changes(tmp_path):
    """Test listing changes."""
    changes_dir = tmp_path / "openspec" / "changes"
    changes_dir.mkdir(parents=True)

    # Create multiple changes
    for i, status in enumerate(["PROPOSED", "IMPLEMENTED", "ARCHIVED"]):
        change_id = f"change-{i}"
        change_dir = changes_dir / change_id
        change_dir.mkdir()

        metadata = {"change_id": change_id, "status": status}
        (change_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    loader = ChangeLoader(tmp_path)

    # List all changes
    all_changes = loader.list_changes()
    assert len(all_changes) == 3
    assert "change-0" in all_changes

    # List by status
    proposed = loader.list_changes(status="PROPOSED")
    assert len(proposed) == 1
    assert "change-0" in proposed

    implemented = loader.list_changes(status="IMPLEMENTED")
    assert len(implemented) == 1
    assert "change-1" in implemented


def test_change_exists(tmp_path):
    """Test change_exists method."""
    change_id = "test-change-003"
    change_dir = tmp_path / "openspec" / "changes" / change_id
    change_dir.mkdir(parents=True)

    loader = ChangeLoader(tmp_path)

    # Change dir exists but no metadata
    assert not loader.change_exists(change_id)

    # Create metadata
    metadata = {"change_id": change_id}
    (change_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    # Now it exists
    assert loader.change_exists(change_id)

    # Non-existent change
    assert not loader.change_exists("non-existent")
