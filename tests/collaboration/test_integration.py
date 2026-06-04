# -*- coding: utf-8 -*-
"""Integration tests for AI-agnostic collaboration modes."""

import json

from devpal.core.openspec_context import OpenSpecContext

from devpal.collaboration.change_loader import ChangeLoader
from devpal.collaboration.context_restorer import ContextRestorer
from devpal.collaboration.modes import RunMode, get_mode_policy


class TestCollaborationIntegration:
    """Test AI-agnostic collaboration mode integration."""

    def test_mode_policy_integration(self):
        """Test that mode policies are correctly configured."""
        # Test FULL mode
        full_policy = get_mode_policy(RunMode.FULL)
        assert full_policy.should_run_phase(1)
        assert full_policy.should_run_phase(11)
        assert not full_policy.require_existing_change
        assert full_policy.allow_code_writes

        # Test PROPOSE_ONLY mode
        propose_policy = get_mode_policy(RunMode.PROPOSE_ONLY)
        assert propose_policy.should_run_phase(1)
        assert propose_policy.should_run_phase(3)
        assert not propose_policy.should_run_phase(4)
        assert propose_policy.stop_after_phase == 3
        assert propose_policy.generate_rule_pack

        # Test APPLY_ONLY mode
        apply_policy = get_mode_policy(RunMode.APPLY_ONLY)
        assert not apply_policy.should_run_phase(1)
        assert apply_policy.should_run_phase(4)
        assert apply_policy.should_run_phase(11)
        assert apply_policy.require_existing_change

        # Test VALIDATE_ONLY mode
        validate_policy = get_mode_policy(RunMode.VALIDATE_ONLY)
        assert not validate_policy.should_run_phase(1)
        assert not validate_policy.should_run_phase(8)
        assert validate_policy.should_run_phase(9)
        assert validate_policy.should_run_phase(11)
        assert validate_policy.require_existing_change

    def test_change_loader_with_context_restorer(self, tmp_path):
        """Test loading a change and restoring context."""
        # Create mock change structure
        change_id = "test-integration-001"
        changes_dir = tmp_path / "openspec" / "changes" / change_id
        changes_dir.mkdir(parents=True)

        # Create metadata
        metadata = {
            "change_id": change_id,
            "status": "PROPOSED",
            "project_type": "python",
            "language": "python",
            "project_name": "test_project",
            "features": ["feature1", "feature2"],
        }
        (changes_dir / "metadata.json").write_text(
            json.dumps(metadata), encoding="utf-8"
        )

        # Create artifacts
        (changes_dir / "proposal.md").write_text(
            "# Proposal\nTest content", encoding="utf-8"
        )
        (changes_dir / "tasks.md").write_text(
            "- [ ] Task 1\n- [ ] Task 2\n- [ ] Task 3", encoding="utf-8"
        )
        (changes_dir / "design.md").write_text(
            "# Design\nTest design", encoding="utf-8"
        )
        (changes_dir / "specs").mkdir()
        (changes_dir / "specs" / "spec.md").write_text(
            "# Spec\nTest spec", encoding="utf-8"
        )

        # Load change
        loader = ChangeLoader(tmp_path)
        artifacts = loader.load_change(change_id)

        # Verify artifacts loaded
        assert artifacts["change_id"] == change_id
        assert artifacts["metadata"]["status"] == "PROPOSED"
        assert "Test content" in artifacts["proposal"]
        assert "Task 1" in artifacts["tasks"]

        # Verify task parsing works
        restorer = ContextRestorer()
        tasks = restorer._parse_tasks(artifacts["tasks"])
        assert len(tasks) == 3
        assert "Task 1" in tasks[0]

    def test_mode_policy_phase_filtering(self):
        """Test that phase filtering works correctly for each mode."""
        # PROPOSE_ONLY should only run phases 1-3
        propose_policy = get_mode_policy(RunMode.PROPOSE_ONLY)
        allowed_phases = [i for i in range(1, 12) if propose_policy.should_run_phase(i)]
        assert allowed_phases == [1, 2, 3]

        # APPLY_ONLY should run phases 4-11
        apply_policy = get_mode_policy(RunMode.APPLY_ONLY)
        allowed_phases = [i for i in range(1, 12) if apply_policy.should_run_phase(i)]
        assert allowed_phases == [4, 5, 6, 7, 8, 9, 10, 11]

        # VALIDATE_ONLY should run phases 9-11
        validate_policy = get_mode_policy(RunMode.VALIDATE_ONLY)
        allowed_phases = [
            i for i in range(1, 12) if validate_policy.should_run_phase(i)
        ]
        assert allowed_phases == [9, 10, 11]

    def test_change_status_retrieval(self, tmp_path):
        """Test retrieving change status from metadata."""
        change_id = "test-status-001"
        changes_dir = tmp_path / "openspec" / "changes" / change_id
        changes_dir.mkdir(parents=True)

        for status in ["PROPOSED", "IMPLEMENTED", "ARCHIVED"]:
            metadata = {"change_id": change_id, "status": status}
            (changes_dir / "metadata.json").write_text(
                json.dumps(metadata), encoding="utf-8"
            )

            loader = ChangeLoader(tmp_path)
            artifacts = loader.load_change(change_id)

            restorer = ContextRestorer()
            retrieved_status = restorer.get_change_status(artifacts["metadata"])

            assert retrieved_status == status
