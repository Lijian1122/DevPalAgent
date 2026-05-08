# -*- coding: utf-8 -*-
"""
OpenSpec C/C++ 代码质量检查规则 - Phase 6

基于 C++ Core Guidelines, MISRA, 以及常见的最佳实践。
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import re

from ..diagnostic_engine import (
    DiagnosticEngine,
    DiagnosticIssue,
    DiagnosticSeverity as EngineDiagnosticSeverity,
    DiagnosticCategory,
)
from .base import FileAnalysisResult, SymbolInfo, SymbolKind, SourceLocation


@dataclass
class CppRule:
    """C/C++ 检查规则"""
    rule_id: str
    name: str
    description: str
    category: str
    severity: str  # critical, high, medium, low, info
    check_function: Callable[[FileAnalysisResult, str], List[DiagnosticIssue]]

    def run(self, result: FileAnalysisResult, content: str) -> List[DiagnosticIssue]:
        """运行检查"""
        return self.check_function(result, content)


def _make_issue(
    rule_id: str,
    message: str,
    file_path: str,
    line: int = 0,
    column: int = 0,
    severity: str = "medium",
    suggestion: Optional[str] = None
) -> DiagnosticIssue:
    """创建诊断问题"""
    sev_map = {
        "critical": EngineDiagnosticSeverity.CRITICAL,
        "high": EngineDiagnosticSeverity.HIGH,
        "medium": EngineDiagnosticSeverity.MEDIUM,
        "low": EngineDiagnosticSeverity.LOW,
        "info": EngineDiagnosticSeverity.INFO,
    }
    return DiagnosticIssue(
        issue_id=rule_id,
        category=DiagnosticCategory.MAINTAINABILITY,
        severity=sev_map.get(severity, EngineDiagnosticSeverity.MEDIUM),
        message=message,
        file_path=file_path,
        line_number=line,
        suggestion=suggestion,
        auto_fixable=False,
    )


# ============================================
# 规则 1: 避免使用 C 风格的强制类型转换
# ============================================
def check_cstyle_cast(result: FileAnalysisResult, content: str) -> List[DiagnosticIssue]:
    """检查 C 风格的强制类型转换"""
    issues = []

    # 匹配 C 风格类型转换: (Type)expr
    pattern = re.compile(r'\(\s*(?:const\s+)?(?:unsigned\s+)?\w+\s*\**?\s*\)\s*\w')

    for match in pattern.finditer(content):
        line_num = content[:match.start()].count('\n') + 1
        col = match.start() - content[:match.start()].rfind('\n')

        issues.append(_make_issue(
            "CPP001",
            "避免使用 C 风格的强制类型转换",
            str(result.file_path),
            line_num,
            col,
            "medium",
            "建议使用 static_cast, dynamic_cast, const_cast 或 reinterpret_cast"
        ))

    return issues


# ============================================
# 规则 2: 检查裸指针
# ============================================
def check_raw_pointers(result: FileAnalysisResult, content: str) -> List[DiagnosticIssue]:
    """检查裸指针的使用"""
    issues = []

    # 匹配裸指针声明（排除函数参数和智能指针）
    smart_ptr_pattern = r'\b(?:unique|shared|weak)_ptr\s*<'
    smart_ptr_matches = set()
    for match in re.finditer(smart_ptr_pattern, content):
        smart_ptr_matches.add(content[:match.start()].count('\n') + 1)

    # 简单的裸指针检测
    pointer_pattern = re.compile(r'\b\w+\s*\*\s*\w+\s*[;=]')
    for match in pointer_pattern.finditer(content):
        line_num = content[:match.start()].count('\n') + 1
        if line_num in smart_ptr_matches:
            continue

        # 跳过一些常见的例外
        matched_text = match.group(0)
        if any(x in matched_text for x in ['main', 'argc', 'argv', 'char*', 'void*']):
            continue

        col = match.start() - content[:match.start()].rfind('\n')

        issues.append(_make_issue(
            "CPP002",
            "考虑使用智能指针替代裸指针",
            str(result.file_path),
            line_num,
            col,
            "low",
            "考虑使用 std::unique_ptr 或 std::shared_ptr 管理内存"
        ))

    return issues


# ============================================
# 规则 3: 检查魔法数字
# ============================================
def check_magic_numbers(result: FileAnalysisResult, content: str) -> List[DiagnosticIssue]:
    """检查魔法数字"""
    issues = []

    # 排除的数字: 0, 1, 2, 10, 100, 1024, 年份等
    excluded = {0, 1, 2, 10, 100, 1000, 1024, 2020, 2021, 2022, 2023, 2024, 2025}

    # 查找数字（不包含小数点）
    pattern = re.compile(r'\b(\d{3,})\b')
    for match in pattern.finditer(content):
        try:
            num = int(match.group(1))
            if num not in excluded:
                line_num = content[:match.start()].count('\n') + 1
                col = match.start() - content[:match.start()].rfind('\n')

                issues.append(_make_issue(
                    "CPP003",
                    f"魔法数字: {num}",
                    str(result.file_path),
                    line_num,
                    col,
                    "low",
                    "建议提取为具名常量或枚举"
                ))
        except ValueError:
            pass

    return issues


# ============================================
# 规则 4: 检查全局变量
# ============================================
def check_global_variables(result: FileAnalysisResult, content: str) -> List[DiagnosticIssue]:
    """检查全局变量"""
    issues = []

    # 简单的全局变量检测（在函数外的变量声明）
    lines = content.split('\n')

    brace_count = 0
    in_comment = False
    in_string = False

    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()

        # 跳过注释
        if '//' in stripped:
            stripped = stripped[:stripped.index('//')]

        # 简单的字符串和注释处理
        j = 0
        while j < len(stripped):
            c = stripped[j]
            if c == '"' and (j == 0 or stripped[j-1] != '\\'):
                in_string = not in_string
            elif not in_string and c == '/' and j + 1 < len(stripped) and stripped[j+1] == '*':
                in_comment = True
                j += 1
            elif not in_string and c == '*' and j + 1 < len(stripped) and stripped[j+1] == '/':
                in_comment = False
                j += 1
            elif not in_string and not in_comment:
                if c == '{':
                    brace_count += 1
                elif c == '}':
                    brace_count -= 1
            j += 1

        if brace_count == 0 and not in_comment:
            # 在全局作用域
            if re.match(r'^(?:static\s+)?(?:const\s+)?(?:\w+(?:\s*[*&])?)\s+\w+\s*[;=]', stripped):
                # 跳过主函数和常见例外
                if 'main(' in stripped or stripped.startswith('int main'):
                    continue
                # 跳过只声明的函数
                if '(' in stripped and ')' in stripped:
                    continue
                # 跳过类/结构体声明
                if stripped.startswith(('class ', 'struct ', 'enum ')):
                    continue

                issues.append(_make_issue(
                    "CPP004",
                    "全局变量可能引入线程安全和初始化顺序问题",
                    str(result.file_path),
                    line_num,
                    0,
                    "medium",
                    "考虑使用局部静态变量、单例模式或将其封装到类中"
                ))

    return issues


# ============================================
# 规则 5: 检查未使用的 include
# ============================================
def check_unused_includes(result: FileAnalysisResult, content: str) -> List[DiagnosticIssue]:
    """检查可能未使用的 include"""
    issues = []

    # 提取所有 include
    includes = []
    for dep in result.dependencies:
        if dep.kind == 'include' and dep.target:
            includes.append((dep.target, dep.location.line))

    # 简单检查: include 的文件名（不带扩展名）是否在代码中出现
    # 这只是一个启发式检查，不是精确的
    for include_name, line_num in includes:
        # 提取基本名称，如 <vector> -> vector, "myheader.h" -> myheader
        base_name = include_name.split('/')[-1].split('.')[0]

        # 检查是否有使用迹象
        used = False
        patterns = [
            rf'\bstd::{base_name}\b',
            rf'\b{base_name}\s*<',
            rf'\b{base_name}\s+',
        ]

        for pattern in patterns:
            if re.search(pattern, content):
                used = True
                break

        if not used and include_name not in {'iostream', 'string', 'vector', 'map', 'set'}:
            # 跳过非常常见的头文件
            issues.append(_make_issue(
                "CPP005",
                f"include '{include_name}' 可能未使用",
                str(result.file_path),
                line_num,
                0,
                "info",
                "建议删除未使用的头文件以加快编译"
            ))

    return issues


# ============================================
# 规则 6: 检查缺少 virtual 析构函数
# ============================================
def check_virtual_destructor(result: FileAnalysisResult, content: str) -> List[DiagnosticIssue]:
    """检查多态基类是否缺少 virtual 析构函数"""
    issues = []

    # 查找有 virtual 函数但没有 virtual 析构函数的类
    # 这是一个简化的检查，真实检查需要完整的 AST
    lines = content.split('\n')

    class_names = set()
    class_virtual_methods = {}
    class_has_virtual_destructor = set()

    for line_num, line in enumerate(lines, 1):
        # 查找类声明
        match = re.search(r'\bclass\s+(\w+)', line)
        if match:
            current_class = match.group(1)
            class_names.add(current_class)
            class_virtual_methods[current_class] = line_num

        # 查找 virtual 函数
        if 'virtual' in line and '~' in line:
            class_has_virtual_destructor.add(current_class if 'current_class' in locals() else None)

    for cls_name, line_num in class_virtual_methods.items():
        if cls_name not in class_has_virtual_destructor:
            issues.append(_make_issue(
                "CPP006",
                f"类 '{cls_name}' 有虚函数但没有虚析构函数",
                str(result.file_path),
                line_num,
                0,
                "high",
                "多态基类应该声明虚析构函数以防止内存泄漏"
            ))

    return issues


# ============================================
# 规则 7: 检查使用 using namespace std
# ============================================
def check_using_namespace_std(result: FileAnalysisResult, content: str) -> List[DiagnosticIssue]:
    """检查头文件中的 using namespace std"""
    issues = []

    # 只有头文件才警告
    if result.file_path.suffix not in {'.h', '.hpp', '.hxx', '.hh'}:
        return []

    pattern = re.compile(r'\busing\s+namespace\s+std\s*;')
    for match in pattern.finditer(content):
        line_num = content[:match.start()].count('\n') + 1
        col = match.start() - content[:match.start()].rfind('\n')

        issues.append(_make_issue(
            "CPP007",
            "头文件中避免使用 using namespace std",
            str(result.file_path),
            line_num,
            col,
            "medium",
            "这会导致命名空间污染，建议在 .cpp 文件中或函数作用域内使用"
        ))

    return issues


# ============================================
# 规则 8: 检查异常规范
# ============================================
def check_exception_spec(result: FileAnalysisResult, content: str) -> List[DiagnosticIssue]:
    """检查过时的异常规范 throw()"""
    issues = []

    pattern = re.compile(r'\bthrow\s*\([^)]*\)')
    for match in pattern.finditer(content):
        line_num = content[:match.start()].count('\n') + 1

        issues.append(_make_issue(
            "CPP008",
            "throw() 异常规范在 C++11 已弃用，C++17 已移除",
            str(result.file_path),
            line_num,
            0,
            "medium",
            "建议使用 noexcept 替代"
        ))

    return issues


# ============================================
# 规则 9: 检查 NULL
# ============================================
def check_null_macro(result: FileAnalysisResult, content: str) -> List[DiagnosticIssue]:
    """检查 NULL 宏的使用"""
    issues = []

    pattern = re.compile(r'\bNULL\b')
    for match in pattern.finditer(content):
        line_num = content[:match.start()].count('\n') + 1
        col = match.start() - content[:match.start()].rfind('\n')

        issues.append(_make_issue(
            "CPP009",
            "建议使用 nullptr 替代 NULL 宏",
            str(result.file_path),
            line_num,
            col,
            "low",
            "nullptr 是类型安全的空指针字面量（C++11 起）"
        ))

    return issues


# ============================================
# 规则 10: 检查 memcpy/memset 用于非 POD 类型
# ============================================
def check_memcpy_non_pod(result: FileAnalysisResult, content: str) -> List[DiagnosticIssue]:
    """检查 memcpy/memset 用于可能的非 POD 类型"""
    issues = []

    for func in ['memcpy', 'memset', 'memmove', 'memcmp']:
        pattern = re.compile(rf'\b{func}\s*\(')
        for match in pattern.finditer(content):
            line_num = content[:match.start()].count('\n') + 1

            issues.append(_make_issue(
                "CPP010",
                f"谨慎使用 {func} 处理非 POD 类型",
                str(result.file_path),
                line_num,
                0,
                "medium",
                "对于有构造/析构函数的对象，直接内存操作可能导致未定义行为"
            ))

    return issues


# ============================================
# 规则注册表
# ============================================
CPP_RULES = [
    CppRule("CPP001", "C 风格类型转换", "避免使用 C 风格的强制类型转换",
            "style", "medium", check_cstyle_cast),
    CppRule("CPP002", "裸指针使用", "考虑使用智能指针替代裸指针",
            "memory", "low", check_raw_pointers),
    CppRule("CPP003", "魔法数字", "避免在代码中直接使用魔法数字",
            "style", "low", check_magic_numbers),
    CppRule("CPP004", "全局变量", "全局变量可能引入线程安全问题",
            "concurrency", "medium", check_global_variables),
    CppRule("CPP005", "未使用的 include", "可能存在未使用的头文件",
            "style", "info", check_unused_includes),
    CppRule("CPP006", "缺少 virtual 析构函数", "多态基类需要虚析构函数",
            "oop", "high", check_virtual_destructor),
    CppRule("CPP007", "头文件 using namespace std", "头文件中避免使用 using namespace std",
            "style", "medium", check_using_namespace_std),
    CppRule("CPP008", "弃用的异常规范", "throw() 在 C++17 已移除",
            "modern", "medium", check_exception_spec),
    CppRule("CPP009", "使用 NULL", "建议用 nullptr 替代 NULL",
            "modern", "low", check_null_macro),
    CppRule("CPP010", "内存操作函数", "谨慎对非 POD 类型使用 memcpy/memset",
            "oop", "medium", check_memcpy_non_pod),
]


class CppCodeQualityChecker:
    """C/C++ 代码质量检查器"""

    def __init__(self, enabled_rules: Optional[List[str]] = None):
        self._rules = CPP_RULES
        self._enabled = set(enabled_rules) if enabled_rules else {r.rule_id for r in self._rules}

    def enable_rule(self, rule_id: str):
        """启用规则"""
        self._enabled.add(rule_id)

    def disable_rule(self, rule_id: str):
        """禁用规则"""
        self._enabled.discard(rule_id)

    def check_file(self, file_path: Path,
                  analysis_result: Optional[FileAnalysisResult] = None,
                  plugin=None) -> List[DiagnosticIssue]:
        """检查单个文件"""
        from .cpp_plugin import CppLanguagePlugin

        if analysis_result is None:
            if plugin is None:
                plugin = CppLanguagePlugin()
            analysis_result = plugin.analyze_file(file_path)

        if not analysis_result:
            return []

        content = file_path.read_text(encoding='utf-8', errors='ignore')

        all_issues = []
        for rule in self._rules:
            if rule.rule_id not in self._enabled:
                continue
            try:
                issues = rule.run(analysis_result, content)
                all_issues.extend(issues)
            except Exception:
                pass

        return all_issues

    def get_rule_info(self) -> List[Dict[str, str]]:
        """获取所有规则的信息"""
        return [
            {
                'id': r.rule_id,
                'name': r.name,
                'description': r.description,
                'category': r.category,
                'severity': r.severity,
            }
            for r in self._rules
        ]
