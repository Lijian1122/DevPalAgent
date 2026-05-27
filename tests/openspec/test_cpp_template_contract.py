# -*- coding: utf-8 -*-

from devpal.core.templates.cpp_templates import _TEST_BASE_H


def test_cpp_test_base_contains_phase4_required_macros():
    for macro in ["ASSERT_TRUE", "ASSERT_EQ", "RUN_TEST", "TEST_MAIN_BEGIN", "TEST_MAIN_END"]:
        assert macro in _TEST_BASE_H


def test_cpp_test_base_outputs_parseable_results_summary():
    assert "Results: " in _TEST_BASE_H
    assert " passed" in _TEST_BASE_H
    assert "[PASS]" in _TEST_BASE_H
    assert "[FAIL]" in _TEST_BASE_H


def test_cpp_test_base_wraps_test_macros_in_main_function():
    assert "#define TEST_MAIN_BEGIN int main() {" in _TEST_BASE_H
    assert "#define TEST_MAIN_END test_run_summary(passed, failed); return failed == 0 ? 0 : 1; }" in _TEST_BASE_H
