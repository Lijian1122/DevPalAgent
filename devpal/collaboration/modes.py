# -*- coding: utf-8 -*-
"""Run modes and policies for OpenSpec workflow."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class RunMode(str, Enum):
    """OpenSpec workflow run modes."""

    FULL = "full"                    # Complete Phase 1-11
    PROPOSE_ONLY = "propose_only"    # Phase 1-3 + Change generation
    APPLY_ONLY = "apply_only"        # Phase 4-11 from existing change
    VALIDATE_ONLY = "validate_only"  # Phase 9-11 validation only


@dataclass
class ModePolicy:
    """Policy defining phase execution for each run mode."""

    start_phase: int
    stop_after_phase: Optional[int]
    require_existing_change: bool
    allow_code_writes: bool
    allow_test_writes: bool
    allow_archive: bool
    generate_rule_pack: bool

    def should_run_phase(self, phase_num: int) -> bool:
        """Check if a phase should run under this policy.

        Args:
            phase_num: Phase number to check

        Returns:
            True if phase should run, False otherwise
        """
        if phase_num < self.start_phase:
            return False
        if self.stop_after_phase and phase_num > self.stop_after_phase:
     return False
        return True


# Mode policies mapping
MODE_POLICIES = {
    RunMode.FULL: ModePolicy(
        start_phase=1,
        stop_after_phase=None,
        require_existing_change=False,
        allow_code_writes=True,
        allow_test_writes=True,
        allow_archive=True,
        generate_rule_pack=False,
  ),
    RunMode.PROPOSE_ONLY: ModePolicy(
        start_phase=1,
        stop_after_phase=3,
        require_existing_change=False,
        allow_code_writes=False,
      allow_test_writes=False,
        allow_archive=False,
        generate_rule_pack=True,
    ),
    RunMode.APPLY_ONLY: ModePolicy(
        start_phase=4,
        stop_after_phase=None,
    require_existing_change=True,
        allow_code_writes=True,
        allow_test_writes=True,
        allow_archive=True,
        generate_rule_pack=False,
  ),
    RunMode.VALIDATE_ONLY: ModePolicy(
        start_phase=9,
        stop_after_phase=11,
        require_existing_change=True,
        allow_code_writes=False,
        allow_test_writes=False,
        allow_archive=False,
        generate_rule_pack=False,
    ),
}


def get_mode_policy(mode: RunMode) -> ModePolicy:
    """Get the policy for a given run mode.

    Args:
        mode: The run mode

    Returns:
        The corresponding ModePolicy

    Raises:
        KeyError: If mode is not recognized
    """
    return MODE_POLICIES[mode]
