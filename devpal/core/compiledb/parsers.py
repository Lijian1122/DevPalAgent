# -*- coding: utf-8 -*-
"""
代码解析器 - Python 和 C++ 基础实现
"""

import re
from typing import List
from .core import SymbolInfo, SymbolType


class BaseParser:
    """代码解析器基类"""

    def parse(self, content: str, file_path: str) -> List[SymbolInfo]:
        """
        解析代码内容，提取符号

        Args:
            content: 代码内容
            file_path: 文件路径

        Returns:
            符号列表
        """
        raise NotImplementedError


class PythonParser(BaseParser):
    """Python 代码解析器"""

    CLASS_PATTERN = re.compile(r'^class\s+(\w+)\s*(\([^)]+\))?:', re.MULTILINE)
    DEF_PATTERN = re.compile(r'^def\s+(\w+)\s*\(', re.MULTILINE)
    ASSIGN_PATTERN = re.compile(r'^(\w+)\s*=', re.MULTILINE)

    def parse(self, content: str, file_path: str) -> List[SymbolInfo]:
        symbols = []
        lines = content.splitlines()

        # 查找类定义
        for i, line in enumerate(lines, 1):
            class_match = self.CLASS_PATTERN.match(line.strip())
            if class_match:
                class_name = class_match.group(1)
                # 估算类结束位置（下一个非缩进行或文件结束）
                end_line = self._find_class_end(lines, i)
                symbols.append(SymbolInfo(
                    name=class_name,
                    type=SymbolType.CLASS,
                    file_path=file_path,
                    line_start=i,
                    line_end=end_line
                ))

        # 查找函数定义
        for i, line in enumerate(lines, 1):
            def_match = self.DEF_PATTERN.match(line.strip())
            if def_match:
                func_name = def_match.group(1)
                # 判断是否是方法（有缩进）
                is_method = line.startswith('    ') or line.startswith('\t')
                end_line = self._find_function_end(lines, i)

                symbol_type = SymbolType.METHOD if is_method else SymbolType.FUNCTION
                symbols.append(SymbolInfo(
                    name=func_name,
                    type=symbol_type,
                    file_path=file_path,
                    line_start=i,
                    line_end=end_line
                ))

        return symbols

    def _find_class_end(self, lines: List[str], start_line: int) -> int:
        """查找类结束行"""
        base_indent = None
        for i in range(start_line, len(lines)):
            line = lines[i]
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            indent = len(line) - len(line.lstrip())
            if base_indent is None:
                base_indent = indent
            elif indent <= base_indent and stripped:
                return i
        return len(lines)

    def _find_function_end(self, lines: List[str], start_line: int) -> int:
        """查找函数结束行"""
        return self._find_class_end(lines, start_line)


class CppParser(BaseParser):
    """C++ 代码解析器"""

    # 简化的正则表达式
    CLASS_PATTERN = re.compile(r'^\s*(class|struct)\s+(\w+)', re.MULTILINE)
    FUNC_PATTERN = re.compile(
        r'^\s*(\w[\w\s\*&:<>,]*?)\s+(\w+)\s*\([^)]*\)\s*(const)?\s*[;{]?',
        re.MULTILINE
    )
    INCLUDE_PATTERN = re.compile(r'#include\s*["<]([^">]+)[">]')

    def parse(self, content: str, file_path: str) -> List[SymbolInfo]:
        symbols = []
        lines = content.splitlines()

        # 查找类/结构体定义
        for i, line in enumerate(lines, 1):
            class_match = self.CLASS_PATTERN.match(line)
            if class_match:
                keyword = class_match.group(1)
                class_name = class_match.group(2)
                symbol_type = SymbolType.STRUCT if keyword == 'struct' else SymbolType.CLASS

                end_line = self._find_brace_end(lines, i)
                symbols.append(SymbolInfo(
                    name=class_name,
                    type=symbol_type,
                    file_path=file_path,
                    line_start=i,
                    line_end=end_line
                ))

        # 查找函数/方法声明（简化）
        for i, line in enumerate(lines, 1):
            line = line.strip()
            # 简单的函数模式：返回类型 + 函数名 + (参数)
            if '(' in line and ')' in line and not line.startswith('#'):
                # 提取函数名（简化）
                match = re.search(r'(\w+)\s*\(', line)
                if match:
                    func_name = match.group(1)
                    # 排除关键字
                    if func_name not in ['if', 'for', 'while', 'switch', 'catch']:
                        # 判断是否是方法（在类内部）
                        is_method = self._is_inside_class(i, symbols)
                        symbol_type = SymbolType.METHOD if is_method else SymbolType.FUNCTION

                        symbols.append(SymbolInfo(
                            name=func_name,
                            type=symbol_type,
                            file_path=file_path,
                            line_start=i
                        ))

        return symbols

    def _find_brace_end(self, lines: List[str], start_line: int) -> int:
        """查找大括号配对结束行"""
        brace_count = 0
        found_open = False

        for i in range(start_line - 1, len(lines)):
            line = lines[i]
            for char in line:
                if char == '{':
                    brace_count += 1
                    found_open = True
                elif char == '}':
                    brace_count -= 1
                    if found_open and brace_count == 0:
                        return i + 1

        return len(lines)

    def _is_inside_class(self, line_num: int, symbols: List[SymbolInfo]) -> bool:
        """判断行是否在类内部"""
        for symbol in symbols:
            if symbol.type in [SymbolType.CLASS, SymbolType.STRUCT]:
                if symbol.line_start <= line_num <= symbol.line_end:
                    return True
        return False
