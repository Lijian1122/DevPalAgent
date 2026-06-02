# -*- coding: utf-8 -*-
"""Tests for collaboration.modes module."""

import pytest
from devpal.collaboration.modes import RunMode, ModePolicy, MODE_POLICIES, get_mode_policy


def test_run_mode_values():
    """Test RunMode enum values."""
    assert RunMode.FULL == "full"
    assert RunMode.PROPOSE_ONLY == "propose_only"
    assert RunMode.APPLY_ONLY == "apply_only"
    assert RunMode.VALIDATE_ONLY == "validate_only"


def test_mode_policy_full():
    """Test FULL mode policy."""
    policy = MODE_POLICIES[RunMode.FULL]

  assert policy.start_phase == 1
    assert policy.stop_after_phase is None
    assert policy.require_existing_change is False
    assert policy.allow_code_writes is True
    assert policy.allow_test_writes is True
    assert policy.allow_archive is True
    assert policy.generate_rule_pack is False

    # Should run all phases
    assert policy.should_run_phase(1)
  assert policy.should_run_phase(5)
    assert policy.should_run_phase(11)


def test_mode_policy_propose_only():
    """Test PROPOSE_ONLY mode policy."""
    policy = MODE_POLICIES[RunMode.PROPOSE_ONLY]

    assert policy.start_phase == 1
    assert policy.stop_after_phase == 3
    assert policy.require_existing_change is False
    assert policy.allow_code_writes is False
    assert policy.allow_test_writes is False
    assert policy.allow_archive is False
    assert policy.generate_rule_pack is True

  # Should run phases 1-3 only
    assert policy.should_run_phase(1)
    assert policy.should_run_phase(2)
    assert policy.should_run_phase(3)
    assert not policy.should_run_phase(4)
    assert not policy.should_run_phase(11)


def test_mode_policy_apply_only():
    """Test APPLY_ONLY mode policy."""
    policy = MODE_POLICIES[RunMode.APPLY_ONLY]

    assert policy.start_phase == 4
    assert policy.stop_after_phase is None
    assert policy.require_existing_change is True
    assert policy.allow_code_writes is True
    assert policy.allow_test_writes is True
    assert policy.allow_archive is True
    assert policy.generate_rule_pack is False

    # Should run phases 4-11 only
    assert not policy.should_run_phase(1)
    assert not policy.should_run_phase(3)
    assert policy.should_run_phase(4)
    assert policy.should_run_phase(11)


def test_mode_policy_validate_only():
    """Test VALIDATE_ONLY mode policy."""
    policy = MODE_POLICIES[RunMode.VALIDATE_ONLY]

    assert policy.start_phase == 9
   assert policy.stop_after_phase == 11
    assert policy.require_existing_change is True
    assert policy.allow_code_writes is False
    assert policy.allow_test_writes is False
    assert policy.allow_archive is False
    assert policy.generate_rule_pack is False

    # Should run phases 9-11 only
    assert not policy.should_run_phase(1)
    assert not policy.should_run_phase(8)
    assert policy.should_run_phase(9)
    assert policy.should_run_phase(10)
    assert policy.should_run_phase(11)


def test_get_mode_policy():
    """Test get_mode_policy function."""
    policy = get_mode_policy(RunMode.FULL)
    assert policy.start_phase == 1

    policy = get_mode_policy(RunMode.PROPOSE_ONLY)
    assert policy.stop_after_phase == 3
