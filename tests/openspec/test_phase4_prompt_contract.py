# -*- coding: utf-8 -*-

from devpal.core.prompts.prompt_engine import get_prompt_engine


def test_phase4_system_prompt_includes_cpp_requirements():
    """Test that C++ code generation prompt includes key requirements"""
    engine = get_prompt_engine()
    prompt = engine.generate_code_gen_prompt('cpp')

    # Check file structure requirements
    assert "include/<name>.h" in prompt
    assert "src/<name>.cpp" in prompt
    assert "tests/test_<class>.cpp" in prompt

    # Check constructor requirements
    assert "default constructor" in prompt
    assert "parameterized constructors" in prompt

    # Check third-party library constraint
    assert "ONLY C++17 STL" in prompt or "NO third-party libraries" in prompt


def test_phase4_prompt_includes_best_practices():
    """Test that prompt includes C++ best practices"""
    engine = get_prompt_engine()
    prompt = engine.generate_code_gen_prompt('cpp')

    # Check best practices are included
    assert "C++17" in prompt
    assert "STL" in prompt or "standard library" in prompt


def test_phase4_prompt_includes_naming_conventions():
    """Test that prompt includes naming conventions"""
    engine = get_prompt_engine()
    prompt = engine.generate_code_gen_prompt('cpp')

    # Check naming conventions
    assert "PascalCase" in prompt
    assert "snake_case" in prompt
