# -*- coding: utf-8 -*-
"""Tests for Phase 9 Quality Gate"""

from pathlib import Path
import pytest
from devpal.core.openspec_phases.phase9_quality_gate import Phase9QualityGate
from devpal.core.openspec_phases.base import OpenSpecContext


class _DummyRegistry:
    """Dummy tool registry for testing"""
    pass


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
        project_name="test_project"
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


def test_quality_gate_fails_main_cpp_no_main_function(context, temp_project, tool_registry):
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


def test_quality_gate_fails_test_base_missing_macros(context, temp_project, tool_registry):
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
    """Test that quality gate fails when test_total is 0"""
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

    # Set test_total to 0
    context.test_total = 0

    phase = Phase9QualityGate(context, tool_registry)
    result = phase.execute()

    assert result.success is False
    assert any("test" in err.lower() and "0" in err for err in result.errors)


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
    report_content = report_path.read_text(encoding='utf-8')
    assert "Quality Gate Report" in report_content
    assert "PASSED" in report_content or "FAILED" in report_content
