# -*- coding: utf-8 -*-
"""
编译错误分析工具
"""
import re
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from .base import BaseTool, ToolResult


class CompilationAnalyzer:
    """编译错误解析器"""

    # 常见编译器错误模式
    ERROR_PATTERNS = [
        # MSVC 模式: filename(line): error CXXXX: message
        (re.compile(r'(.+?)\((\d+)\)\s*:\s*error\s+([A-Z]+\d+)\s*:\s*(.+)'), 'msvc'),
        # GCC/Clang 模式: filename:line:col: error: message
        (re.compile(r'(.+?):(\d+):(\d+):\s*error:\s*(.+)'), 'gcc'),
        # MSVC 警告
        (re.compile(r'(.+?)\((\d+)\)\s*:\s*warning\s+([A-Z]+\d+)\s*:\s*(.+)'), 'msvc_warn'),
        # GCC/Clang 警告
        (re.compile(r'(.+?):(\d+):(\d+):\s*warning:\s*(.+)'), 'gcc_warn'),
    ]

    @classmethod
    def parse_output(cls, output: str) -> List[Dict]:
        """解析编译输出"""
        errors = []

        for line in output.split('\n'):
            line = line.strip()
            if not line:
                continue

            for pattern, compiler_type in cls.ERROR_PATTERNS:
                match = pattern.match(line)
                if match:
                    if compiler_type in ['msvc', 'msvc_warn']:
                        errors.append({
                            'file': match.group(1),
                            'line': int(match.group(2)),
                            'error_code': match.group(3),
                            'message': match.group(4),
                            'type': 'warning' if 'warn' in compiler_type else 'error',
                            'compiler': 'msvc'
                        })
                    else:
                        errors.append({
                            'file': match.group(1),
                            'line': int(match.group(2)),
                            'column': int(match.group(3)),
                            'message': match.group(4),
                            'type': 'warning' if 'warn' in compiler_type else 'error',
                            'compiler': 'gcc'
                        })
                    break

        return errors

    @classmethod
    def suggest_fix(cls, error_code: str, message: str) -> str:
        """给出修复建议"""
        suggestions = []

        # 常见错误修复建议
        if 'C2065' in error_code or 'undeclared' in message.lower():
            suggestions.append("变量未声明：检查变量名拼写，或者在使用前声明")
        elif 'C2039' in error_code or 'is not a member' in message.lower():
            suggestions.append("成员不存在：检查类/结构体成员名，或检查头文件是否包含")
        elif 'C1083' in error_code or 'No such file' in message:
            suggestions.append("头文件找不到：检查 include 路径、文件名拼写")
        elif 'C2447' in error_code or 'missing function header' in message:
            suggestions.append("函数头缺失：检查大括号匹配，或函数声明语法")
        elif 'C2001' in error_code or 'newline in constant' in message:
            suggestions.append("字符串换行问题：检查引号是否正确配对")
        elif 'C3861' in error_code or 'identifier not found' in message:
            suggestions.append("标识符找不到：检查函数名拼写，或是否缺少 using namespace")
        elif 'LNK2019' in error_code or 'unresolved external' in message.lower():
            suggestions.append("链接错误：检查函数是否实现，库文件是否正确链接")
        elif 'LNK1120' in error_code or 'unresolved externals' in message.lower():
            suggestions.append("未解析的外部符号：检查所有函数是否有实现")
        elif 'undefined reference' in message.lower():
            suggestions.append("未定义引用：检查函数实现是否编译，库是否链接")
        elif 'syntax error' in message.lower():
            suggestions.append("语法错误：检查分号、大括号、括号是否匹配")

        if not suggestions:
            suggestions.append("仔细阅读错误信息，检查相关代码行的语法")

        return "\n".join(f"  - {s}" for s in suggestions)


class CompilerAnalyzerTool(BaseTool):
    """编译错误分析工具"""

    name = "compiler_analyzer"
    description = "分析编译器输出的错误和警告，解析错误位置、给出修复建议"

    class Parameters(BaseModel):
        compiler_output: str = Field(description="编译器的完整输出内容，包含所有错误和警告信息")
        show_warnings: bool = Field(default=True, description="是否显示警告信息")

    def _execute(self, params: Parameters) -> ToolResult:
        try:
            errors = CompilationAnalyzer.parse_output(params.compiler_output)

            if not errors:
                return ToolResult.ok(
                    content="未解析到编译错误，编译输出看起来正常。\n"
                           "如果确实有错误，可能是不支持的编译器格式。",
                    error_count=0
                )

            # 分离错误和警告
            actual_errors = [e for e in errors if e['type'] == 'error']
            warnings = [e for e in errors if e['type'] == 'warning']

            result_lines = []
            result_lines.append(f" 编译分析结果：")
            result_lines.append(f"   错误数: {len(actual_errors)}")
            result_lines.append(f"   警告数: {len(warnings)}")
            result_lines.append("")

            # 显示错误
            if actual_errors:
                result_lines.append(" 错误详情：")
                for i, err in enumerate(actual_errors[:10], 1):
                    result_lines.append(f"\n{i}. {err['file']}:{err['line']}")
                    result_lines.append(f"   [{err.get('error_code', 'ERROR')}] {err['message']}")
                    result_lines.append(f"    修复建议：")
                    result_lines.append(f"      {CompilationAnalyzer.suggest_fix(err.get('error_code', ''), err['message'])}")

                if len(actual_errors) > 10:
                    result_lines.append(f"\n   还有 {len(actual_errors) - 10} 个错误未显示...")

            # 显示警告
            if params.show_warnings and warnings:
                result_lines.append("\n️ 警告详情：")
                for i, warn in enumerate(warnings[:5], 1):
                    result_lines.append(f"\n{i}. {warn['file']}:{warn['line']}")
                    result_lines.append(f"   [{warn.get('error_code', 'WARNING')}] {warn['message']}")

                if len(warnings) > 5:
                    result_lines.append(f"\n   还有 {len(warnings) - 5} 个警告未显示...")

            return ToolResult.ok(
                content="\n".join(result_lines),
                error_count=len(actual_errors),
                warning_count=len(warnings)
            )

        except Exception as e:
            return ToolResult.error(f"分析编译输出失败: {str(e)}")
