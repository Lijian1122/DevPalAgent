# -*- coding: utf-8 -*-
"""Integration tests for AI-agnostic collaboration modes."""

import json

from devpal.core.openspec_context import OpenSpecContext
from devpal.core.openspec_phases.enhanced_scheduler import EnhancedOpenSpecScheduler

from devpal.collaboration.change_loader import ChangeLoader
from devpal.collaboration.context_restorer import ContextRestorer
from devpal.collaboration.modes import RunMode, get_mode_policy


class _DummyRegistry:
    pass


def _write_change(project_dir, change_id="test-change-001", status="PROPOSED"):
    change_dir = project_dir / "openspec" / "changes" / change_id
    specs_dir = change_dir / "specs"
    specs_dir.mkdir(parents=True)
    metadata = {
        "change_id": change_id,
        "status": status,
        "project_type": "python",
        "language": "python",
        "project_name": "restored_project",
        "features": ["feature1", "feature2"],
        "requirements": [{"id": "REQ-001", "description": "Restored requirement"}],
    }
    (change_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    (change_dir / "proposal.md").write_text("# Proposal\nRestored proposal", encoding="utf-8")
    (change_dir / "tasks.md").write_text("- [ ] Restore task", encoding="utf-8")
    (change_dir / "design.md").write_text("# Design\nRestored design", encoding="utf-8")
    (specs_dir / "spec.md").write_text("# Spec\nRestored spec", encoding="utf-8")
    return change_dir


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
        change_id = "test-integration-001"
        _write_change(tmp_path, change_id=change_id)

        loader = ChangeLoader(tmp_path)
        artifacts = loader.load_change(change_id)

        assert artifacts["change_id"] == change_id
        assert artifacts["metadata"]["status"] == "PROPOSED"
        assert "Restored proposal" in artifacts["proposal"]
        assert "Restore task" in artifacts["tasks"]

        restorer = ContextRestorer()
        tasks = restorer._parse_tasks(artifacts["tasks"])
        assert len(tasks) == 1
        assert "Restore task" in tasks[0]

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

    def test_apply_only_restores_change_context_without_resume(self, tmp_path, monkeypatch):
        change_id = "apply-change-001"
        requirements = tmp_path / "requirements.md"
        requirements.write_text("# Requirements\n", encoding="utf-8")
        _write_change(tmp_path, change_id=change_id, status="IMPLEMENTED")

        scheduler = EnhancedOpenSpecScheduler(
            str(requirements),
            _DummyRegistry(),
            enable_checkpoint=True,
            enable_progress=False,
            run_mode=RunMode.APPLY_ONLY,
            change_id=change_id,
        )
        scheduler.context.project_dir = tmp_path

        def fake_run(start_phase):
            return {
                "success": True,
                "start_phase": start_phase,
                "change_id": scheduler.context.current_change_id,
                "project_name": scheduler.context.project_name,
                "requirements": scheduler.context.structured_requirements,
            }

        monkeypatch.setattr(scheduler, "_run_phases_with_enhancements", fake_run)

        result = scheduler.run_all_phases(resume=False)

        assert result["success"] is True
        assert result["start_phase"] == 1
        assert result["change_id"] == change_id
        assert result["project_name"] == "restored_project"
        assert result["requirements"][0]["id"] == "REQ-001"

    def test_validate_only_restores_change_context_without_resume(self, tmp_path, monkeypatch):
        change_id = "validate-change-001"
        requirements = tmp_path / "requirements.md"
        requirements.write_text("# Requirements\n", encoding="utf-8")
        _write_change(tmp_path, change_id=change_id, status="IMPLEMENTED")

        scheduler = EnhancedOpenSpecScheduler(
            str(requirements),
            _DummyRegistry(),
            enable_checkpoint=True,
            enable_progress=False,
            run_mode=RunMode.VALIDATE_ONLY,
            change_id=change_id,
        )
        scheduler.context.project_dir = tmp_path

        monkeypatch.setattr(
            scheduler,
            "_run_phases_with_enhancements",
            lambda start_phase: {
                "success": True,
                "start_phase": start_phase,
                "change_id": scheduler.context.current_change_id,
                "spec_content": scheduler.context.spec_content,
            },
        )

        result = scheduler.run_all_phases(resume=False)

        assert result["success"] is True
        assert result["start_phase"] == 1
        assert result["change_id"] == change_id
        assert "Restored spec" in result["spec_content"]

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
