# -*- coding: utf-8 -*-
"""
System Prompt 动态生成引擎
基于语言特征配置动态生成 AI System Prompt
"""

from typing import Optional, List
from devpal.core.schema.languages.language_config import (
    get_language_features,
    LanguageFeatures,
)


class PromptTemplateEngine:
    """动态 System Prompt 生成引擎"""  # 修复点1: 三引号闭合 (原代码缺少开头引号)

    def generate_design_prompt(
        self,
        language: str,
        features: Optional[List[str]] = None,
    ) -> str:  # 修复点2: 缩进对齐 (原代码缩进不一致)
        """
        生成 Phase 3 技术设计的 System Prompt

        Args:
            language: 编程语言 (cpp, python, shell等)
            features: 项目特性列表 (install, auth, database等)

        Returns:
            完整的 System Prompt 字符串
        """
        lang_features = get_language_features(language)

        # 基础模板
        prompt = f"""You are a {lang_features.role_description}. Given a software requirements document, produce a structured technical design in Markdown.

CRITICAL RULES:
1. Your FIRST character must be '#' (the start of the Markdown heading)
2. DO NOT output ANY thinking process, analysis, or preamble
3. DO NOT use <thinking> tags or any XML tags
4. Start DIRECTLY with: # 技术设计文档

The design MUST include the following sections in this order:
1. 系统架构概览 (modules, layering, dataflow)
2. 核心模块清单 (one bullet per module: name, responsibility, key functions/classes)
3. 关键 API 定义 (function signatures with parameter/return types)
4. 数据结构与持久化
5. 安全与并发设计
6. 文件组织 (which files map to which modules)
7. 测试策略

Constraints:
- {lang_features.language_name} {lang_features.version}
- Use {lang_features.standard_library}
- Package manager: {lang_features.package_manager}
- Test framework: {lang_features.test_framework}
- Build system: {lang_features.build_system}

Project Structure:
{lang_features.get_file_structure_description()}

Naming Conventions:
{lang_features.get_naming_conventions_description()}

Best Practices:
{lang_features.get_best_practices_description()}

- Be concrete: name actual modules, functions, file paths. No placeholders.
- Keep total length under 1200 words. For small requirements, prefer concise concrete decisions over exhaustive explanation.
"""

        return prompt

    def generate_code_gen_prompt(
        self,
        language: str,
        features: Optional[List[str]] = None,
    ) -> str:  # 修复点3: 缩进对齐 (原代码缩进不一致)
        """
        生成 Phase 4 代码生成的 System Prompt

        Args:
            language: 编程语言 (cpp, python, shell等)
            features: 项目特性列表 (install, auth, database等)

        Returns:
            完整的 System Prompt 字符串
        """
        lang_features = get_language_features(language)

        # 根据语言生成文件要求描述
        if language == 'cpp':
            required_files = """REQUIRED FILES (you MUST generate ALL of these):
1. For each class: include/<name>.h AND src/<name>.cpp (both header and implementation)
2. src/main.cpp - a working main program that demonstrates the core functionality
3. At least one tests/test_<class>.cpp for each non-trivial class

Output rules:
- path is relative to project root (include/user.h, src/user.cpp, src/main.cpp, tests/test_user.cpp)
- Each class lives in its own pair of include/<name>.h plus src/<name>.cpp (snake_case file, PascalCase class)
- Include guards use the uppercase filename (e.g. #ifndef USER_H)
- Use only C++17 STL unless the design mandates otherwise
- src/main.cpp must include a working main() function that exercises the primary workflow
- For every non-trivial class, emit at least one tests/test_<class>.cpp that includes "test_base.h"
- Test files may ONLY use macros defined in tests/test_base.h: ASSERT_TRUE, ASSERT_EQ, TEST_MAIN_BEGIN, RUN_TEST, TEST_MAIN_END.
- Do NOT use ASSERT_THROW, ASSERT_NE, EXPECT_*, GoogleTest, Catch2, or any external test framework macro.
- To test exceptions, write explicit try/catch code and assert a boolean with ASSERT_TRUE.
- Tests must only call public methods that are declared in the generated header for the class.
- Do NOT regenerate CMakeLists.txt, README.md, include/<project>.h, or tests/test_base.h - they already exist

C++ Standard Library Headers (CRITICAL):
- ALWAYS use correct STL header names: <mutex>, <thread>, <vector>, <string>, <map>, etc.
- NEVER use non-existent headers like <lock_guard>, <unique_lock>, <shared_ptr>, etc.
- Common mistakes to avoid:
  * std::lock_guard → #include <mutex> (NOT <lock_guard>)
  * std::unique_lock → #include <mutex> (NOT <unique_lock>)
  * std::shared_ptr → #include <memory> (NOT <shared_ptr>)
  * std::vector → #include <vector> (correct)
  * std::string → #include <string> (correct)
- When in doubt, check C++17 standard library documentation

C++ Constructor Requirements:
- ALWAYS provide a default constructor (no parameters) for every class
- Also provide parameterized constructors as needed
- Initialize all member variables in constructors (use member initializer lists)
- Example: class User should have both User() and User(const std::string& username, ...)
- This ensures classes can be used in STL containers and avoid "no suitable default constructor" errors"""

        elif language == 'python':
            required_files = """REQUIRED FILES (you MUST generate ALL of these):
1. For each module/class: src/<name>.py (implementation)
2. src/main.py - a working main program that demonstrates the core functionality
3. At least one tests/test_<module>.py for each non-trivial module

Output rules:
- path is relative to project root (src/auth.py, src/main.py, tests/test_auth.py)
- Each module lives in its own src/<name>.py file (snake_case)
- Use type hints for function signatures
- Use pytest for tests
- Each test file should have at least 2 test functions
- Add proper error handling
- Do NOT regenerate README.md if it already exists"""

        elif language == 'shell':
            required_files = """REQUIRED FILES (you MUST generate ALL of these):
1. For each script: scripts/<name>.sh (implementation)
2. scripts/main.sh - a working main script that demonstrates the core functionality
3. At least one tests/test_<script>.sh for each non-trivial script

Output rules:
- path is relative to project root (scripts/install.sh, scripts/main.sh, tests/test_install.sh)
- Each script lives in its own scripts/<name>.sh file (snake_case)
- Use set -euo pipefail for safety
- Quote variables to prevent word splitting
- Use functions for code organization
- Include error handling and logging
- Use shellcheck for linting
- Do NOT regenerate README.md if it already exists"""

        else:
            # 默认通用模板
            required_files = """REQUIRED FILES (you MUST generate ALL of these):
1. For each module: appropriate source files based on language conventions
2. A working main program that demonstrates the core functionality
3. At least one test file for each non-trivial module"""

        # 基础模板
        prompt = f"""You are a {lang_features.role_description}. Given a software requirements document and a technical design document, write concrete, working {lang_features.language_name} code.

CRITICAL RULES:
- You MUST use the write_file tool for EVERY file. Do NOT write code in prose.
- Call write_file once per file immediately. No planning, no discussion first.
- Start with your first write_file call right away.
- **CRITICAL**: Write COMPLETE file content, NOT diffs or patches.
- **NEVER** start with diff markers like: ---, +++, @@, or + prefix on lines.
- **NEVER** use unified diff format, patch format, or any incremental change format.
- Always write the FULL, COMPLETE file content from the first line to the last.
- If you find yourself writing "---" or "+++" at the start, STOP and write the complete file instead.

{required_files}

Naming Conventions:
{lang_features.get_naming_conventions_description()}

Best Practices:
{lang_features.get_best_practices_description()}

- After all files are written, respond with a one-line summary and stop.
"""

        return prompt


# 全局单例
_prompt_engine_instance: Optional[PromptTemplateEngine] = None


def get_prompt_engine() -> PromptTemplateEngine:
    """获取 Prompt 引擎单例"""  # 修复点4: 三引号闭合 (原代码结尾引号数量不足)
    global _prompt_engine_instance
    if _prompt_engine_instance is None:
        _prompt_engine_instance = PromptTemplateEngine()
    return _prompt_engine_instance
