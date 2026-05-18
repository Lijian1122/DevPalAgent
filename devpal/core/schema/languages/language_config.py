# -*- coding: utf-8 -*-
"""
语言特征配置系统
提供编程语言的元数据和特征定义
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict


class ProgrammingLanguage(Enum):
    """编程语言枚举"""
    CPP = "cpp"
    PYTHON = "python"
    SHELL = "shell"
    RUST = "rust"
    GO = "go"
    JAVASCRIPT = "javascript"


@dataclass
class LanguageFeatures:
    """语言特征配置"""
    language_id: str
    language_name: str
    role_description: str  # "C++ architect", "Python developer"
    extensions: List[str]
    naming_conventions: Dict[str, str]
    package_manager: str
    test_framework: str
    build_system: str
    project_structure: Dict[str, str]
    best_practices: List[str]
    standard_library: str
    version: str = "latest"

    # Prompt 生成相关
    file_naming_pattern: str = ""  # "snake_case", "camelCase"
    class_naming_pattern: str = ""  # "PascalCase"

    def get_file_structure_description(self) -> str:
        """生成项目结构描述"""
        lines = []
        for dir_name, description in self.project_structure.items():
            lines.append(f"- {dir_name}/: {description}")
        return "\n".join(lines)

    def get_naming_conventions_description(self) -> str:
        """生成命名约定描述"""
        lines = []
        for element, convention in self.naming_conventions.items():
            lines.append(f"- {element}: {convention}")
        return "\n".join(lines)

    def get_best_practices_description(self) -> str:
        """生成最佳实践描述"""
        return "\n".join(f"- {practice}" for practice in self.best_practices)


# 语言特征数据库
LANGUAGE_FEATURES_DB: Dict[ProgrammingLanguage, LanguageFeatures] = {
    ProgrammingLanguage.CPP: LanguageFeatures(
        language_id="cpp",
        language_name="C++",
        role_description="senior C++ architect",
        extensions=[".cpp", ".h", ".hpp", ".cxx", ".cc", ".hxx", ".hh", ".inl"],
        naming_conventions={
            "class": "PascalCase",
         "function": "camelCase or snake_case",
         "variable": "snake_case",
          "constant": "UPPER_SNAKE_CASE",
            "file": "snake_case",
            "namespace": "snake_case",
        },
        package_manager="CMake",
        test_framework="gtest / custom test_base.h",
        build_system="CMake",
        project_structure={
            "include": "Header files (.h, .hpp)",
            "src": "Source files (.cpp)",
         "tests": "Test files (test_*.cpp)",
            "docs": "Documentation",
        },
        best_practices=[
            "Use C++17 standard features",
            "Use RAII for resource management",
            "Prefer const references for parameters",
        "Use smart pointers (unique_ptr, shared_ptr)",
            "Use STL containers and algorithms",
        "Include proper headers for all STL types",
            "Provide both default and parameterized constructors",
            "Use include guards: #ifndef FILENAME_H",
     ],
        standard_library="STL (C++17)",
        version="C++17",
        file_naming_pattern="snake_case",
        class_naming_pattern="PascalCase",
    ),

    ProgrammingLanguage.PYTHON: LanguageFeatures(
        language_id="python",
        language_name="Python",
        role_description="senior Python architect",
        extensions=[".py", ".pyi", ".pyw"],
        naming_conventions={
            "class": "PascalCase",
            "function": "snake_case",
            "variable": "snake_case",
            "constant": "UPPER_SNAKE_CASE",
            "file": "snake_case",
          "module": "snake_case",
        },
        package_manager="pip",
        test_framework="pytest",
        build_system="setuptools / poetry",
        project_structure={
            "src": "Source code (.py files)",
            "tests": "Test files (test_*.py)",
            "docs": "Documentation",
            "data": "Data files",
        },
        best_practices=[
        "Follow PEP 8 style guide",
         "Use type hints for function parameters and returns",
            "Use context managers (with statement) for resource management",
            "Prefer list comprehensions over loops when appropriate",
            "Use virtual environments for dependency isolation",
            "Include docstrings for modules, classes, and functions",
          "Use pytest for testing",
            "Handle exceptions properly with try/except",
        ],
        standard_library="Python Standard Library",
        version="Python 3.8+",
        file_naming_pattern="snake_case",
        class_naming_pattern="PascalCase",
    ),

    ProgrammingLanguage.SHELL: LanguageFeatures(
        language_id="shell",
        language_name="Shell Script",
        role_description="senior Shell script developer",
        extensions=[".sh", ".bash", ".bat", ".cmd", ".ps1"],
        naming_conventions={
            "function": "snake_case",
            "variable": "UPPER_SNAKE_CASE or snake_case",
            "file": "snake_case",
        },
        package_manager="N/A",
        test_framework="bats (Bash Automated Testing System)",
        build_system="N/A",
        project_structure={
            "scripts": "Shell scripts",
            "tests": "Test scripts",
            "lib": "Library scripts",
            "docs": "Documentation",
        },
        best_practices=[
            "Use set -euo pipefail for safety",
            "Quote variables to prevent word splitting",
            "Use functions for code organization",
      "Include error handling and logging",
            "Use shellcheck for linting",
            "Provide clear usage documentation",
            "Test on both bash and sh",
        ],
        standard_library="Bash built-ins",
        version="Bash 4.0+",
        file_naming_pattern="snake_case",
        class_naming_pattern="N/A",
    ),
}


def get_language_features(language: str) -> LanguageFeatures:
    """获取语言特征配置

    Args:
        language: 语言ID (cpp, python, shell等)

    Returns:
      LanguageFeatures: 语言特征配置对象
    """
    try:
        lang_enum = ProgrammingLanguage(language)
        return LANGUAGE_FEATURES_DB[lang_enum]
    except (ValueError, KeyError):
        # 默认返回 C++ 配置
        return LANGUAGE_FEATURES_DB[ProgrammingLanguage.CPP]
