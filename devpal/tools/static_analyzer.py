# -*- coding: utf-8 -*-
"""
静态分析工具
集成 clang-tidy、cppcheck 等静态分析工具
"""
import os
import re
from typing import Dict, Any, Optional, List
from pathlib import Path
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult


class StaticAnalyzer(BaseTool):
    """C/C++ 代码静态分析工具"""

    name = "static_analyzer"
    description = "C/C++ 代码静态分析工具，支持 clang-tidy、cppcheck，可发现代码质量问题、性能优化点、潜在 Bug"

    class Parameters(BaseModel):
        action: str = Field(
            default="analyze",
            description="操作类型: analyze, list_checks, list_supported"
        )
        file_path: Optional[str] = Field(
            default=None,
            description="要分析的源文件路径（可选，不指定则分析整个项目）"
        )
        checks: Optional[str] = Field(
            default=None,
            description="启用的检查规则，如 '*' 或 'readability-*,performance-*'"
        )
        tool: str = Field(
            default="clang-tidy",
            description="使用的分析工具: clang-tidy, cppcheck"
        )
        fix: bool = Field(
            default=False,
            description="是否自动修复可修复的问题"
        )
        extra_args: Optional[str] = Field(
            default=None,
            description="额外的编译参数"
        )

    def _execute(self, params: Parameters) -> ToolResult:
        if params.action == 'list_checks':
            return self._list_available_checks(params.tool)
        elif params.action == 'list_supported':
            return self._list_supported_tools()
        elif params.action == 'analyze':
            return self._analyze_code(params)
        else:
            return ToolResult.error(f"不支持的操作: {params.action}")

    def _check_tools(self) -> Dict[str, bool]:
        """检查可用的静态分析工具"""
        tools = {}

        try:
            result = os.popen("clang-tidy --version").read()
            tools['clang-tidy'] = "LLVM" in result or "clang-tidy" in result.lower()
        except Exception:
            tools['clang-tidy'] = False

        try:
            result = os.popen("cppcheck --version").read()
            tools['cppcheck'] = "Cppcheck" in result or "cppcheck" in result.lower()
        except Exception:
            tools['cppcheck'] = False

        return tools

    def _list_supported_tools(self) -> ToolResult:
        """列出支持的工具"""
        tools = self._check_tools()
        lines = ["可用的静态分析工具:\n"]
        for name, available in tools.items():
            status = "✅ 可用" if available else "❌ 未安装"
            lines.append(f"- {name}: {status}")

        return ToolResult.ok(
            "\n".join(lines),
            total_tools=len(tools),
            available_tools=sum(tools.values())
        )

    def _list_available_checks(self, tool: str) -> ToolResult:
        """列出可用的检查规则"""
        if tool == 'clang-tidy':
            stdout = os.popen("clang-tidy --list-checks").read()
            return ToolResult.ok(f"clang-tidy 可用检查规则:\n{stdout}")
        elif tool == 'cppcheck':
            stdout = os.popen("cppcheck --errorlist").read()
            return ToolResult.ok(f"cppcheck 可用检查规则:\n{stdout}")
        else:
            return ToolResult.error(f"不支持的工具: {tool}")

    def _analyze_code(self, params: Parameters) -> ToolResult:
        """分析代码"""
        file_path = params.file_path
        tool = params.tool
        checks = params.checks or '*'
        fix = params.fix
        extra_args = params.extra_args or ''

        if not file_path:
            source_files = self._find_source_files()
            if not source_files:
                return ToolResult.error("未找到源文件，请指定 file_path 参数")
        else:
            source_files = [file_path]

        all_issues = []

        for src_file in source_files:
            if tool == 'clang-tidy':
                issues = self._run_clang_tidy(src_file, checks, fix, extra_args)
            elif tool == 'cppcheck':
                issues = self._run_cppcheck(src_file, extra_args)
            else:
                issues = []
            all_issues.extend(issues)

        summary = {
            'total_issues': len(all_issues),
            'by_severity': self._group_by_severity(all_issues),
            'by_rule': self._group_by_rule(all_issues),
            'files_analyzed': len(source_files)
        }

        content = self._generate_summary_content(all_issues, summary, tool)

        return ToolResult.ok(content, summary=summary)

    def _find_source_files(self) -> List[str]:
        """查找项目中的所有源文件"""
        source_extensions = {'.cpp', '.cxx', '.cc', '.c', '.h', '.hpp', '.hxx'}
        source_files = []

        for root, dirs, files in os.walk('.'):
            for file in files:
                if Path(file).suffix in source_extensions:
                    full_path = Path(root) / file
                    source_files.append(str(full_path))

        return source_files[:10]  # 限制最多 10 个文件

    def _run_clang_tidy(
        self,
        file_path: str,
        checks: str,
        fix: bool,
        extra_args: str
    ) -> List[Dict[str, Any]]:
        """运行 clang-tidy 分析"""
        import subprocess

        cmd_parts = ["clang-tidy"]

        if checks:
            cmd_parts.append(f"--checks={checks}")

        if fix:
            cmd_parts.append("--fix")
            cmd_parts.append("--format-style=file")

        cmd_parts.append(file_path)

        if extra_args:
            cmd_parts.append("--")
            cmd_parts.append(extra_args)

        try:
            result = subprocess.run(
                ' '.join(cmd_parts),
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )

            output = result.stdout + result.stderr
            return self._parse_clang_tidy_output(output)

        except Exception:
            return []

    def _parse_clang_tidy_output(self, output: str) -> List[Dict[str, Any]]:
        """解析 clang-tidy 输出"""
        issues = []

        pattern = re.compile(
            r'^([^:]+):(\d+):(\d+):\s*(\w+):\s*(.+?)\s*\[([\w\-,]+)\]$',
            re.MULTILINE
        )

        for match in pattern.finditer(output):
            file, line, col, severity, message, rule = match.groups()
            issues.append({
                'file': file,
                'line': int(line),
                'column': int(col),
                'severity': severity,
                'rule': rule,
                'message': message
            })

        return issues

    def _run_cppcheck(self, file_path: str, extra_args: str) -> List[Dict[str, Any]]:
        """运行 cppcheck 分析"""
        import subprocess

        cmd = f"cppcheck --enable=all --quiet {extra_args} {file_path}"

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )

            output = result.stdout + result.stderr
            return self._parse_cppcheck_output(output)

        except Exception:
            return []

    def _parse_cppcheck_output(self, output: str) -> List[Dict[str, Any]]:
        """解析 cppcheck 输出"""
        issues = []

        pattern = re.compile(
            r'^\[([^\]]+):(\d+)\]:\s*\((\w+)\)\s*(.+)$',
            re.MULTILINE
        )

        for match in pattern.finditer(output):
            file, line, severity, message = match.groups()
            issues.append({
                'file': file,
                'line': int(line),
                'column': 0,
                'severity': severity,
                'rule': 'cppcheck',
                'message': message
            })

        return issues

    def _group_by_severity(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """按严重程度分组统计"""
        result = {}
        for issue in issues:
            sev = issue['severity']
            result[sev] = result.get(sev, 0) + 1
        return result

    def _group_by_rule(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """按规则分组统计"""
        result = {}
        for issue in issues:
            rule = issue['rule']
            result[rule] = result.get(rule, 0) + 1
        return result

    def _generate_summary_content(
        self,
        issues: List[Dict[str, Any]],
        summary: Dict[str, Any],
        tool: str
    ) -> str:
        """生成分析摘要内容"""
        if not issues:
            return "✅ 分析完成，没有发现问题！"

        lines = [
            f"📊 {tool} 静态分析结果",
            "=" * 50,
            f"总计发现 {summary['total_issues']} 个问题",
            f"分析了 {summary['files_analyzed']} 个文件",
            "",
            "按严重程度统计:"
        ]

        for sev, count in sorted(summary['by_severity'].items()):
            icon = {"error": "🔴", "warning": "🟡", "note": "🔵", "performance": "⚡", "style": "💅"}.get(sev, "ℹ️")
            lines.append(f"  {icon} {sev}: {count}")

        lines.extend(["", "前 10 个问题:"])

        for i, issue in enumerate(issues[:10], 1):
            icon = {"error": "🔴", "warning": "🟡"}.get(issue['severity'], "ℹ️")
            lines.append(
                f"  {i}. {icon} {issue['file']}:{issue['line']} [{issue['rule']}] {issue['message'][:80]}"
            )

        if len(issues) > 10:
            lines.append(f"  ... 还有 {len(issues) - 10} 个问题")

        return "\n".join(lines)
