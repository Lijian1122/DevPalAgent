# -*- coding: utf-8 -*-
"""Tests for Phase 9 Quality Gate"""

from pathlib import Path

import pytest

from devpal.core.openspec_phases.base import OpenSpecContext
from devpal.core.openspec_phases.phase9_quality_gate import Phase9QualityGate


class _DummyRegistry:
    """Dummy tool registry for testing"""

    pass


class _FakeUsage:
    """Fake usage object to match LLMClient.usage interface"""

    def __init__(self):
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.cache_read_tokens = 0
        self.cache_creation_tokens = 0


class _FakeLLMClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.usage = _FakeUsage()

    def generate(self, system, user_message, **kwargs):
        self.calls.append(
            {
                "system": system,
                "user_message": user_message,
                "kwargs": kwargs,
            }
        )
        if not self.responses:
            raise AssertionError("No fake LLM response left")
        response = self.responses.pop(0)
        self.usage.calls += 1
        self.usage.input_tokens += 100
        self.usage.output_tokens += 50
        return response


class _FakeUsage:
    """Fake usage object to match LLMClient.usage interface"""

    def __init__(self):
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.cache_read_tokens = 0
        self.cache_creation_tokens = 0


@pytest.fixture
def tool_registry():
    """Create a dummy tool registry"""
    return _DummyRegistry()


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure"""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create basic structure
    (project_dir / "src").mkdir()
    (project_dir / "include").mkdir()
    (project_dir / "tests").mkdir()
    (project_dir / "docs").mkdir()

    return project_dir


@pytest.fixture
def context(temp_project):
    """Create a test context"""
    ctx = OpenSpecContext(
        project_dir=temp_project,
        requirements_file=Path("requirements.md"),
        project_name="test_project",
    )
    ctx.test_total = 5
    ctx.test_passed = 5
    ctx.test_failed = 0
    return ctx


def test_quality_gate_passes_with_all_checks_ok(context, temp_project, tool_registry):
    """Test that quality gate passes when all checks are OK"""
    # Create all required files
    (temp_project / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.10)")

    (temp_project / "src" / "main.cpp").write_text("""
#include <iostream>
int main() {
    std::cout << "Hello" << std::endl;
    return 0;
}
""")

    (temp_project / "tests" / "test_base.h").write_text("""
#ifndef TEST_BASE_H
#define TEST_BASE_H

#define ASSERT_TRUE(cond) if (!(cond)) return false
#define ASSERT_EQ(a, b) if ((a) != (b)) return false
#define RUN_TEST(test_func) if (!test_func()) return 1
#define TEST_MAIN_BEGIN() int main() {
#define TEST_MAIN_END() return 0; }

#endif
""")
    (temp_project / "tests" / "test_main.cpp").write_text("int main() { return 0; }")

    phase = Phase9QualityGate(context, tool_registry)
    result = phase.execute()

    assert result.success is True
    assert "Quality Gate passed" in result.message
    assert result.data.get("violations") == 0


def test_quality_gate_fails_missing_cmake(context, temp_project, tool_registry):
    """Test that quality gate fails when CMakeLists.txt is missing"""
    # Create other required files but not CMakeLists.txt
    (temp_project / "src" / "main.cpp").write_text("int main() { return 0; }")
    (temp_project / "tests" / "test_base.h").write_text("#define ASSERT_TRUE(x) x")

    phase = Phase9QualityGate(context, tool_registry)
    result = phase.execute()

    assert result.success is False
    assert "CMakeLists.txt not found" in result.errors


def test_quality_gate_fails_missing_main_cpp(context, temp_project, tool_registry):
    """Test that quality gate fails when src/main.cpp is missing"""
    (temp_project / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.10)")
    (temp_project / "tests" / "test_base.h").write_text("#define ASSERT_TRUE(x) x")

    phase = Phase9QualityGate(context, tool_registry)
    result = phase.execute()

    assert result.success is False
    assert any("src/main.cpp" in err for err in result.errors)


def test_quality_gate_fails_main_cpp_no_main_function(
    context, temp_project, tool_registry
):
    """Test that quality gate fails when main.cpp has no main() function"""
    (temp_project / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.10)")
    (temp_project / "src" / "main.cpp").write_text("void foo() {}")
    (temp_project / "tests" / "test_base.h").write_text("#define ASSERT_TRUE(x) x")

    phase = Phase9QualityGate(context, tool_registry)
    result = phase.execute()

    assert result.success is False
    assert any("main()" in err for err in result.errors)


def test_quality_gate_fails_missing_test_base_h(context, temp_project, tool_registry):
    """Test that quality gate fails when test_base.h is missing"""
    (temp_project / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.10)")
    (temp_project / "src" / "main.cpp").write_text("int main() { return 0; }")

    phase = Phase9QualityGate(context, tool_registry)
    result = phase.execute()

    assert result.success is False
    assert any("test_base.h" in err for err in result.errors)


def test_quality_gate_fails_test_base_missing_macros(
    context, temp_project, tool_registry
):
    """Test that quality gate fails when test_base.h is missing required macros"""
    (temp_project / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.10)")
    (temp_project / "src" / "main.cpp").write_text("int main() { return 0; }")

    # test_base.h with incomplete macros
    (temp_project / "tests" / "test_base.h").write_text("""
#define ASSERT_TRUE(x) x
// Missing ASSERT_EQ, RUN_TEST, TEST_MAIN_BEGIN, TEST_MAIN_END
""")

    phase = Phase9QualityGate(context, tool_registry)
    result = phase.execute()

    assert result.success is False
    assert any("test_base.h" in err and "macro" in err.lower() for err in result.errors)


def test_quality_gate_fails_zero_tests(context, temp_project, tool_registry):
    """Test that quality gate fails when no test files exist"""
    # Create all required files
    (temp_project / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.10)")
    (temp_project / "src" / "main.cpp").write_text("int main() { return 0; }")
    (temp_project / "tests" / "test_base.h").write_text("""
#define ASSERT_TRUE(x) x
#define ASSERT_EQ(a, b) (a) == (b)
#define RUN_TEST(f) f()
#define TEST_MAIN_BEGIN() int main() {
#define TEST_MAIN_END() return 0; }
""")

    context.test_total = 0

    phase = Phase9QualityGate(context, tool_registry)
    result = phase.execute()

    assert result.success is False
    assert any("No test files" in err for err in result.errors)


def test_quality_gate_shell_installer_does_not_run_cpp_validation(
    context, temp_project, tool_registry
):
    # 设置为 shell 项目（is_cpp 是只读属性，基于 language 字段）
    context.language = "shell"
    context.project_type = "installer"
    scripts_dir = temp_project / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    (scripts_dir / "install_claude_cli.sh").write_text(
        "#!/usr/bin/env bash\n", encoding="utf-8"
    )
    (scripts_dir / "install_claude_cli.bat").write_text("@echo off\n", encoding="utf-8")

    phase = Phase9QualityGate(context, tool_registry)
    result = phase.execute()

    assert result.success is True
    report = (temp_project / "docs" / "quality_gate_report.md").read_text(
        encoding="utf-8"
    )
    assert "CMakeLists.txt not found" not in report
    assert "src/main.cpp not found" not in report
    assert "tests/test_base.h not found" not in report
    assert "No test files found in tests/ directory" not in report
    assert "FORMAT layer: 0 error(s)" in report
    assert "BUSINESS layer: 0 error(s)" in report


def test_quality_gate_report_includes_validation_details(
    context, temp_project, tool_registry
):
    phase = Phase9QualityGate(context, tool_registry)
    result = phase.execute()

    assert result.success is False
    report = (temp_project / "docs" / "quality_gate_report.md").read_text(
        encoding="utf-8"
    )
    assert "#### Validation Details" in report
    assert "CMakeLists.txt not found" in report
    assert "src/main.cpp not found" in report


def test_quality_gate_report_generation(context, temp_project, tool_registry):
    """Test that quality gate generates a report file"""
    # Create all required files
    (temp_project / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.10)")
    (temp_project / "src" / "main.cpp").write_text("int main() { return 0; }")
    (temp_project / "tests" / "test_base.h").write_text("""
#define ASSERT_TRUE(x) x
#define ASSERT_EQ(a, b) (a) == (b)
#define RUN_TEST(f) f()
#define TEST_MAIN_BEGIN() int main() {
#define TEST_MAIN_END() return 0; }
""")

    phase = Phase9QualityGate(context, tool_registry)
    result = phase.execute()

    # Check that report was generated
    report_path = temp_project / "docs" / "quality_gate_report.md"
    assert report_path.exists()

    # Check report content
    report_content = report_path.read_text(encoding="utf-8")
    assert "Quality Gate Report" in report_content
    assert "PASSED" in report_content or "FAILED" in report_content


def _write_valid_quality_gate_project(project_dir):
    (project_dir / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.10)")
    (project_dir / "src" / "main.cpp").write_text("int main() { return 0; }")
    (project_dir / "tests" / "test_auth.cpp").write_text("int main() { return 0; }")
    (project_dir / "tests" / "test_base.h").write_text("""
#define ASSERT_TRUE(x) x
#define ASSERT_EQ(a, b) (a) == (b)
#define RUN_TEST(f) f()
#define TEST_MAIN_BEGIN() int main() {
#define TEST_MAIN_END() return 0; }
""")


def test_quality_gate_self_heal_fixes_critical_review_issue(
    context, temp_project, tool_registry
):
    _write_valid_quality_gate_project(temp_project)
    unsafe_file = temp_project / "src" / "unsafe.cpp"
    unsafe_file.write_text("""
#include <cstring>

void copy_user(char *buffer, const char *input) {
    strcpy(buffer, input);
}
""")
    context.ai_generated_files = [unsafe_file]
    context.config = {
        "phase9_quality_gate": {
            "code_review": {
                "fail_on_critical": True,
                "self_heal": {
                    "enabled": True,
                    "max_attempts": 1,
                    "switch_model_after": 0,
                    "create_backup": False,
                },
            }
        }
    }

    response = """
```json
{
  "analysis": {
    "root_cause": "unsafe strcpy call",
    "issue_validity": "real security issue",
    "fix_strategy": "replace with bounded copy",
    "risk_assessment": "low"
  },
  "fixes": [
    {
      "file": "src/unsafe.cpp",
      "line": 5,
      "issue_category": "security",
      "old_code": "    strcpy(buffer, input);",
      "new_code": "    std::strncpy(buffer, input, 255);\\n    buffer[255] = '\\\\0';",
      "reason": "Replace unsafe strcpy with bounded strncpy"
    }
  ]
}
```
"""
    fake_llm = _FakeLLMClient([response])

    phase = Phase9QualityGate(context, tool_registry, llm_client=fake_llm)
    result = phase.execute()

    assert result.success is True
    content = unsafe_file.read_text(encoding="utf-8")
    assert "std::strncpy" in content
    assert "strcpy(buffer, input)" not in content
    assert fake_llm.calls
    assert phase.heal_attempts == 1
    assert phase.heal_success == 1


def test_quality_gate_self_heal_uses_fallback_client_without_switch_model(
    context, temp_project, tool_registry
):
    _write_valid_quality_gate_project(temp_project)
    unsafe_file = temp_project / "src" / "unsafe.cpp"
    unsafe_file.write_text("""
#include <cstring>

void copy_user(char *buffer, const char *input) {
    strcpy(buffer, input);
}
""")
    context.ai_generated_files = [unsafe_file]
    context.config = {
        "phase9_quality_gate": {
            "code_review": {
                "fail_on_critical": True,
                "self_heal": {
                    "enabled": True,
                    "max_attempts": 2,
                    "switch_model_after": 2,
                    "fallback_model": "fallback-test-model",
                    "create_backup": False,
                },
            }
        }
    }

    primary_llm = _FakeLLMClient(['{"analysis": {}, "fixes": []}'])
    fallback_response = """
{
  "analysis": {
    "root_cause": "unsafe strcpy call",
    "issue_validity": "real security issue",
    "fix_strategy": "replace with bounded copy",
    "risk_assessment": "low"
  },
  "fixes": [
    {
      "file": "src/unsafe.cpp",
      "line": 5,
      "issue_category": "security",
      "old_code": "    strcpy(buffer, input);",
      "new_code": "    std::strncpy(buffer, input, 255);\\n    buffer[255] = '\\\\0';",
      "reason": "Replace unsafe strcpy with bounded strncpy"
    }
  ]
}
"""
    fallback_llm = _FakeLLMClient([fallback_response])
    requested_models = []

    def factory(model=None):
        requested_models.append(model)
        return fallback_llm

    phase = Phase9QualityGate(
        context,
        tool_registry,
        llm_client=primary_llm,
        llm_client_factory=factory,
    )
    result = phase.execute()

    assert result.success is True
    assert requested_models == ["fallback-test-model"]
    assert phase.model_switches == 1
    assert phase.heal_attempts == 2
    assert phase.heal_success == 1
    assert "std::strncpy" in unsafe_file.read_text(encoding="utf-8")
