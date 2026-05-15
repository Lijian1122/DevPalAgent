# -*- coding: utf-8 -*-

from devpal.core.openspec_phases.base import PhaseResult, validate_phase_success


def test_phase4_success_requires_generated_or_explicitly_skipped_code():
    result = PhaseResult.ok("phase 4", ai_count=0)

    violations = validate_phase_success(4, result)

    assert violations == [
        "Phase 4 succeeded without generated code or explicit skipped_ai_generation"
    ]


def test_phase4_success_allows_explicit_skipped_ai_generation():
    result = PhaseResult.ok("phase 4", ai_count=0, skipped_ai_generation=True)

    assert validate_phase_success(4, result) == []


def test_phase10_success_requires_nonzero_passing_tests():
    result = PhaseResult.ok("phase 10", test_total=0, test_failed=0)

    assert validate_phase_success(10, result) == ["Phase 10 succeeded with test_total <= 0"]


def test_phase10_success_rejects_failing_tests():
    result = PhaseResult.ok("phase 10", test_total=3, test_failed=1)

    assert validate_phase_success(10, result) == ["Phase 10 succeeded with failing tests"]
