# -*- coding: utf-8 -*-
"""C++ 基础设施模板集合.

仅包含与业务无关的脚手架: CMake 构建、项目骨架、测试断言头、README.
业务代码 (实体类/逻辑/主程序/具体测试用例) 由 Phase 4 的 AI 生成.
"""

from typing import List

from .base import (
    BaseTemplate,
    TemplateContext,
    GeneratedFile,
    TemplateCategory,
)
from .registry import registry


def _get_vars(context: TemplateContext) -> dict:
    """Compute common template variables from context."""
    project_name = context.project_name or "myproject"
    namespace = project_name.lower().replace("-", "_").replace(" ", "_")
    pascal = "".join(w.capitalize() for w in namespace.split("_") if w)
    return {
        "project_name": project_name,
        "namespace": namespace,
        "pascal": pascal or "Project",
    }


@registry.register
class CppProjectSkeletonTemplate(BaseTemplate):
    """仅生成空命名空间的基础头文件,业务实现由 AI 填充."""

    name = "cpp_project_skeleton"
    description = "C++ 项目骨架 (include/<project>.h 空命名空间)"
    category = TemplateCategory.CORE
    language = "cpp"
    priority = 100

    def generate(self, context: TemplateContext) -> List[GeneratedFile]:
        v = _get_vars(context)
        namespace = v["namespace"]
        guard = namespace.upper() + "_H"
        content = _SKELETON_HEADER.format(guard=guard, namespace=namespace)
        return [GeneratedFile(
            path=f"include/{namespace}.h",
            content=content,
       description="项目基础命名空间头文件",
        )]

@registry.register
class CppCMakeTemplate(BaseTemplate):
    """通用 CMakeLists, glob src/tests, 不绑定业务目标名."""

    name = "cpp_cmake"
    description = "通用 CMake 构建配置"
    category = TemplateCategory.BUILD
    language = "cpp"
    priority = 90

    def generate(self, context: TemplateContext) -> List[GeneratedFile]:
        v = _get_vars(context)
        content = _CMAKE_TEMPLATE.format(
            pascal=v["pascal"],
            namespace=v["namespace"],
        )
        return [GeneratedFile(
            path="CMakeLists.txt",
            content=content,
            description="通用 CMake 构建配置",
        )]


@registry.register
class CppTestBaseTemplate(BaseTemplate):
    """tests/test_base.h - 轻量断言/报告头, 供 AI 生成的 test_*.cpp 引用."""

    name = "cpp_test_base"
    description = "测试基础断言和报告工具"
    category = TemplateCategory.TEST
    language = "cpp"
    priority = 80

    def generate(self, context: TemplateContext) -> List[GeneratedFile]:
        return [GeneratedFile(
            path="tests/test_base.h",
       content=_TEST_BASE_H,
        description="测试断言和报告工具头",
        )]


@registry.register
class CppReadmeTemplate(BaseTemplate):
    """通用 README 模板, 不绑定具体业务."""

    name = "cpp_readme"
    description = "通用项目 README"
    category = TemplateCategory.DOCS
    language = "cpp"
    priority = 60

    def generate(self, context: TemplateContext) -> List[GeneratedFile]:
        v = _get_vars(context)
        content = _README_TEMPLATE.format(
            pascal=v["pascal"],
            namespace=v["namespace"],
        )
        return [GeneratedFile(
            path="README.md",
            content=content,
            description="通用项目 README",
        )]


# ---- Literal C++ / build content (no business coupling) ----

_SKELETON_HEADER = '#ifndef {guard}\n#define {guard}\n#pragma once\n\nnamespace {namespace} {{}}  // namespace {namespace}\n\n#endif  // {guard}\n'

_CMAKE_TEMPLATE = 'cmake_minimum_required(VERSION 3.14)\nproject({pascal} VERSION 1.0 LANGUAGES CXX)\n\nset(CMAKE_CXX_STANDARD 17)\nset(CMAKE_CXX_STANDARD_REQUIRED ON)\nset(CMAKE_CXX_EXTENSIONS OFF)\n\nif(MSVC)\n    add_compile_options(/W3 /utf-8)\nelse()\n    add_compile_options(-Wall -Wextra -Wpedantic)\nendif()\n\ninclude_directories(${{PROJECT_SOURCE_DIR}}/include)\n\n# ---- Library: everything in src/ except main.cpp ----\nfile(GLOB LIB_SOURCES src/*.cpp)\nlist(FILTER LIB_SOURCES EXCLUDE REGEX ".*/main\\\\.cpp$")\nif(LIB_SOURCES)\n    add_library({namespace}_lib STATIC ${{LIB_SOURCES}})\nendif()\n\n# ---- Main executable (if src/main.cpp exists) ----\nif(EXISTS ${{PROJECT_SOURCE_DIR}}/src/main.cpp)\n    add_executable({namespace}_app src/main.cpp)\n    if(TARGET {namespace}_lib)\n        target_link_libraries({namespace}_app PRIVATE {namespace}_lib)\n    endif()\nendif()\n\n# ---- Tests: tests/test_*.cpp ----\nenable_testing()\nfile(GLOB TEST_SOURCES tests/test_*.cpp)\nforeach(TEST_SRC ${{TEST_SOURCES}})\n    get_filename_component(TEST_NAME ${{TEST_SRC}} NAME_WE)\n    add_executable(${{TEST_NAME}} ${{TEST_SRC}})\n    if(TARGET {namespace}_lib)\n        target_link_libraries(${{TEST_NAME}} PRIVATE {namespace}_lib)\n    endif()\n    target_include_directories(${{TEST_NAME}} PRIVATE ${{PROJECT_SOURCE_DIR}}/include ${{PROJECT_SOURCE_DIR}}/tests)\n    add_test(NAME ${{TEST_NAME}} COMMAND ${{TEST_NAME}})\nendforeach()\n'

_TEST_BASE_H = '#ifndef TEST_BASE_H\n#define TEST_BASE_H\n#pragma once\n\n#include <iostream>\n#include <string>\n\ninline void test_pass(const char* name) {\n    std::cout << "  [PASS] " << name << std::endl;\n}\n\ninline void test_fail(const char* name, const char* message = "") {\n    std::cout << "  [FAIL] " << name << ": " << message << std::endl;\n}\n\ninline void test_run_summary(int passed, int failed) {\n    std::cout << "Results: " << passed << "/" << (passed + failed) << " passed" << std::endl;\n}\n\n#define ASSERT_TRUE(expr) do { if (!(expr)) { test_fail(__func__, #expr); throw 1; } } while(0)\n#define ASSERT_EQ(a, b) do { if (!((a) == (b))) { test_fail(__func__, #a " != " #b); throw 1; } } while(0)\n#define TEST_MAIN_BEGIN int total = 0; int passed = 0; int failed = 0; std::cout << "Running tests..." << std::endl;\n#define RUN_TEST(test_func) do { ++total; try { test_func(); ++passed; test_pass(#test_func); } catch (...) { ++failed; } } while(0)\n#define TEST_MAIN_END test_run_summary(passed, failed); return failed == 0 ? 0 : 1;\n\n#endif  // TEST_BASE_H\n'

_README_TEMPLATE = '# {pascal}\n\n## 构建\n\n```bash\nmkdir build && cd build\ncmake ..\ncmake --build . --config Release\n```\n## 运行测试\n\n```bash\ncd build\nctest --output-on-failure\n```\n\n## 项目结构\n\n```\n{namespace}/\n├── include/        # 头文件\n├── src/           # 源文件\n├── tests/            # 测试用例\n├── docs/             # 文档\n└── CMakeLists.txt    # 构建配置\n```\n'
