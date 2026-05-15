# -*- coding: utf-8 -*-

from devpal.core.openspec_phases.phase4_generate_code import _AI_SYSTEM_PROMPT


def test_phase4_system_prompt_formats_with_cpp_example_braces():
    prompt = _AI_SYSTEM_PROMPT.format(namespace="cpp_simple_login")

    assert "namespace cpp_simple_login" in prompt
    assert "int main() {" in prompt
    assert "TEST_MAIN_BEGIN" in prompt
    assert "RUN_TEST(testFunction1);" in prompt
    assert "TEST_MAIN_END" in prompt


def test_phase4_prompt_declares_test_base_contract():
    prompt = _AI_SYSTEM_PROMPT.format(namespace="cpp_simple_login")

    for macro in ["ASSERT_TRUE", "ASSERT_EQ", "RUN_TEST", "TEST_MAIN_BEGIN", "TEST_MAIN_END"]:
        assert macro in prompt

    assert "Do NOT define custom pass/fail counters" in prompt
    assert "Do NOT call throw directly" in prompt


def test_phase4_prompt_declares_cpp_stl_include_contract():
    prompt = _AI_SYSTEM_PROMPT.format(namespace="cpp_simple_login")

    assert "std::lock_guard" in prompt
    assert "#include <mutex>" in prompt
    assert "Never include <lock_guard>" in prompt
    assert "Do NOT invent non-existent standard headers" in prompt
