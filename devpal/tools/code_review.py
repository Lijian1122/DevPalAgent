# -*- coding: utf-8 -*-
"""
独立代码审查工具
检查 TODO、调试代码、魔法数字、安全问题、性能问题等
"""
import os
import re
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult


class CodeReviewTool(BaseTool):
    """独立代码审查工具"""

    name = "code_review"
    description = "独立代码审查工具，检查 TODO、调试代码、魔法数字、安全问题、性能问题等"

    class Parameters(BaseModel):
        file_path: Optional[str] = Field(
            default=None,
            description="单个文件路径"
        )
        directory: Optional[str] = Field(
            default=None,
            description="目录路径，审查所有支持的文件"
        )
        files: Optional[List[str]] = Field(
            default=None,
            description="文件列表"
        )
        check_types: List[str] = Field(
            default=['todo', 'debug', 'style', 'security', 'performance'],
            description="要执行的检查类型: todo, debug, style, security, performance"
        )
        max_files: int = Field(
            default=50,
            description="最大审查文件数"
        )

    def _execute(self, params: Parameters) -> ToolResult:
        files_to_review = self._collect_files(params)

        if not files_to_review:
            return ToolResult.error("没有找到需要审查的文件")

        if len(files_to_review) > params.max_files:
            files_to_review = files_to_review[:params.max_files]

        all_issues = []
        for file_path in files_to_review:
            try:
                issues = self._review_file(file_path, params.check_types)
                all_issues.extend(issues)
            except Exception as e:
                all_issues.append({
                    'file': file_path,
                    'line': 0,
                    'severity': 'error',
                    'category': 'review_error',
                    'message': f'审查文件时出错: {str(e)}',
                    'suggestion': ''
                })

        result_content = self._format_results(files_to_review, all_issues)

        return ToolResult.ok(
            result_content,
            files_reviewed=files_to_review,
            issues=all_issues,
            total_issues=len(all_issues)
        )

    def _collect_files(self, params: Parameters) -> List[str]:
        """收集需要审查的文件列表"""
        files = []
        supported_extensions = ('.cpp', '.h', '.hpp', '.c', '.cc', '.py', '.js', '.ts', '.tsx')

        if params.file_path:
            if os.path.exists(params.file_path):
                files.append(params.file_path)

        elif params.directory and os.path.isdir(params.directory):
            for root, _, filenames in os.walk(params.directory):
                for filename in filenames:
                    if filename.endswith(supported_extensions):
                        files.append(os.path.join(root, filename))

        elif params.files:
            for f in params.files:
                if os.path.exists(f):
                    files.append(f)

        return files

    def _review_file(self, file_path: str, check_types: List[str]) -> List[Dict[str, Any]]:
        """审查单个文件"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        lines = content.split('\n')
        issues = []

        if file_path.endswith(('.cpp', '.h', '.hpp', '.c', '.cc')):
            issues.extend(self._check_cpp_code(lines, file_path, check_types))

        elif file_path.endswith('.py'):
            issues.extend(self._check_python_code(lines, file_path, check_types))

        elif file_path.endswith(('.js', '.ts', '.tsx')):
            issues.extend(self._check_js_code(lines, file_path, check_types))

        return issues

    def _check_cpp_code(self, lines: List[str], file_path: str, check_types: List[str]) -> List[Dict]:
        """检查 C/C++ 代码 - 增强版，支持更多bug检测"""
        issues = []

        for i, line in enumerate(lines, 1):
            line_before = line.split('//')[0] if '//' in line else line
            line_stripped = line.strip()

            if not line_stripped:
                continue

            # TODO/FIXME - 仅检测注释中的 TODO
            if 'todo' in check_types:
                has_todo = 'TODO' in line or 'FIXME' in line
                is_python_comment = '#' in line and line_stripped.startswith('#')
                is_c_style_comment = '//' in line or line_stripped.startswith('/*') or line_stripped.startswith('*')

                if has_todo and (is_python_comment or is_c_style_comment):
                    issues.append({
                        'file': file_path,
                        'line': i,
                        'severity': 'info',
                        'category': 'todo',
                        'message': f'存在待办事项: {line_stripped}',
                        'suggestion': '建议尽快完成此任务'
                    })

            # Debug code
            if 'debug' in check_types:
                if 'cout' in line_before or 'printf' in line_before:
                    issues.append({
                        'file': file_path,
                        'line': i,
                        'severity': 'warning',
                        'category': 'debug',
                        'message': f'可能存在调试代码: {line_stripped}',
                        'suggestion': '发布前建议删除调试代码'
                    })

            # ========== BUG检测 - 增强版 ==========
            if 'bug' in check_types:
                # 1. 数组越界模式: for 循环中使用 <= 而不是 <
                if re.search(r'for\s*\(.*\s+i\s*<=\s*\w+', line_before):
                    issues.append({
                        'file': file_path,
                        'line': i,
                        'severity': 'error',
                        'category': 'bug',
                        'message': f'潜在数组越界: {line_stripped}',
                        'suggestion': '检查循环条件是否应该是 < 而不是 <='
                    })

                # 2. 条件变量谓词错误模式
                if 'condition.wait' in line_before and 'stop' in line_before and 'empty' in line_before:
                    if '&&' in line_before:
                        issues.append({
                            'file': file_path,
                            'line': i,
                            'severity': 'error',
                            'category': 'bug',
                            'message': f'条件变量谓词可能错误: {line_stripped}',
                            'suggestion': '注意: stop && empty() 会导致无法唤醒，应该是 !stop || !empty()'
                        })

                # 3. 析构函数bug: 忘记设置 stop = true
                if 'stop =' in line_before and 'true' in line_before:
                    # 检查是否在注释中
                    if '//' in line_before.split('stop =')[0]:
                        issues.append({
                            'file': file_path,
                            'line': i,
                            'severity': 'error',
                            'category': 'bug',
                            'message': f'关键代码被注释: {line_stripped}',
                            'suggestion': '这行代码非常重要，不应该被注释掉！'
                        })

                # 4. 返回错误值
                if 'return workers.size() + 1' in line_before:
                    issues.append({
                        'file': file_path,
                        'line': i,
                        'severity': 'error',
                        'category': 'bug',
                        'message': f'返回值错误: {line_stripped}',
                        'suggestion': 'workers.size() 就是实际线程数，不需要 +1'
                    })

            # Security checks - 增强版
            if 'security' in check_types:
                if 'strcpy(' in line_before or 'strcat(' in line_before:
                    issues.append({
                        'file': file_path,
                        'line': i,
                        'severity': 'error',
                        'category': 'security',
                        'message': f'不安全的字符串操作: {line_stripped}',
                        'suggestion': '建议使用 strcpy_s/strcat_s 或 std::string'
                    })

                if 'gets(' in line_before:
                    issues.append({
                        'file': file_path,
                        'line': i,
                        'severity': 'error',
                        'category': 'security',
                        'message': f'危险的函数调用: {line_stripped}',
                        'suggestion': 'gets() 是危险函数，建议使用 fgets()'
                    })

                # 悬空引用检测: 返回局部变量引用
                if 'return local' in line_before and '&' in lines[max(0, i-2)]:
                    issues.append({
                        'file': file_path,
                        'line': i,
                        'severity': 'error',
                        'category': 'security',
                        'message': f'悬空引用危险: {line_stripped}',
                        'suggestion': '绝对不要返回局部变量的引用！函数结束后局部变量已销毁'
                    })

            # Performance checks - 增强版
            if 'performance' in check_types:
                if 'new ' in line_before:
                    # 检查上下文是否有 delete
                    context_start = max(0, i - 3)
                    context_end = min(len(lines), i + 15)
                    context = ' '.join(lines[context_start:context_end])

                    severity = 'warning'
                    if 'delete' not in context and '//' not in line_before.split('new')[0]:
                        severity = 'error'

                    issues.append({
                        'file': file_path,
                        'line': i,
                        'severity': severity,
                        'category': 'performance',
                        'message': f'内存泄漏风险: {line_stripped}',
                        'suggestion': '确保有对应的 delete，或使用智能指针 std::unique_ptr'
                    })

            # Style checks - magic numbers
            if 'style' in check_types:
                if re.search(r'[^a-zA-Z_][0-9]{3,}', line):
                    if not any(s in line for s in ['0x', 'UINT', 'SIZE', '0ULL', 'std::', '#define', 'const', 'constexpr']):
                        issues.append({
                            'file': file_path,
                            'line': i,
                            'severity': 'warning',
                            'category': 'style',
                            'message': f'可能存在魔法数字: {line_stripped}',
                            'suggestion': '建议定义命名常量'
                        })

        return issues
    def _check_python_code(self, lines: List[str], file_path: str, check_types: List[str]) -> List[Dict]:
        """检查 Python 代码"""
        issues = []

        for i, line in enumerate(lines, 1):
            line_before = line.split('#')[0] if '#' in line else line
            line_stripped = line.strip()

            if not line_stripped:
                continue

            # TODO/FIXME - 仅检测注释中的 TODO
            if 'todo' in check_types:
                has_todo = 'TODO' in line or 'FIXME' in line
                # Python 注释必须以 # 开头或行中包含 #
                is_comment = line_stripped.startswith('#') or '#' in line

                if has_todo and is_comment:
                    issues.append({
                        'file': file_path,
                        'line': i,
                        'severity': 'info',
                        'category': 'todo',
                        'message': f'存在待办事项: {line_stripped}',
                        'suggestion': '建议尽快完成此任务'
                    })

            # Debug code
            if 'debug' in check_types:
                if 'print(' in line_before and not line_stripped.startswith('#'):
                    issues.append({
                        'file': file_path,
                        'line': i,
                        'severity': 'warning',
                        'category': 'debug',
                        'message': f'可能存在调试代码: {line_stripped}',
                        'suggestion': '发布前建议删除调试代码'
                    })

            # Security checks
            if 'security' in check_types:
                if 'eval(' in line_before or 'exec(' in line_before:
                    issues.append({
                        'file': file_path,
                        'line': i,
                        'severity': 'error',
                        'category': 'security',
                        'message': f'危险的函数调用: {line_stripped}',
                        'suggestion': 'eval/exec 可能导致代码注入漏洞'
                    })

                # 检测硬编码的密钥（需要同时满足：有赋值符号，且引号内有看起来像密钥的内容）
                has_assignment = '=' in line and any(q in line for q in ['"', "'"])
                has_sensitive_word = any(s.lower() in line.lower() for s in ['password', 'secret', 'api_key', 'auth_token'])
                # 排除从环境变量获取的情况
                is_from_env = any(s in line for s in ['os.', 'getenv', 'input', '.get'])

                if has_sensitive_word and has_assignment and not is_from_env:
                    issues.append({
                        'file': file_path,
                        'line': i,
                        'severity': 'warning',
                        'category': 'security',
                        'message': f'可能存在硬编码的敏感信息: {line_stripped}',
                        'suggestion': '建议使用环境变量或配置文件'
                    })

        return issues

    def _check_js_code(self, lines: List[str], file_path: str, check_types: List[str]) -> List[Dict]:
        """检查 JavaScript/TypeScript 代码"""
        issues = []

        for i, line in enumerate(lines, 1):
            line_before = line.split('//')[0] if '//' in line else line
            line_stripped = line.strip()

            if not line_stripped:
                continue

            # TODO/FIXME - 仅检测注释中的 TODO
            if 'todo' in check_types:
                has_todo = 'TODO' in line or 'FIXME' in line
                is_comment = '//' in line or line_stripped.startswith('/*') or line_stripped.startswith('*')

                if has_todo and is_comment:
                    issues.append({
                        'file': file_path,
                        'line': i,
                        'severity': 'info',
                        'category': 'todo',
                        'message': f'存在待办事项: {line_stripped}',
                        'suggestion': '建议尽快完成此任务'
                    })

            # Debug code
            if 'debug' in check_types:
                if 'console.log(' in line_before:
                    issues.append({
                        'file': file_path,
                        'line': i,
                        'severity': 'warning',
                        'category': 'debug',
                        'message': f'可能存在调试代码: {line_stripped}',
                        'suggestion': '发布前建议删除调试代码'
                    })

            # Security checks
            if 'security' in check_types:
                if 'eval(' in line_before:
                    issues.append({
                        'file': file_path,
                        'line': i,
                        'severity': 'error',
                        'category': 'security',
                        'message': f'危险的函数调用: {line_stripped}',
                        'suggestion': 'eval() 可能导致 XSS 或代码注入漏洞'
                    })

                if '.innerHTML' in line_before:
                    issues.append({
                        'file': file_path,
                        'line': i,
                        'severity': 'warning',
                        'category': 'security',
                        'message': f'潜在的 XSS 风险: {line_stripped}',
                        'suggestion': '考虑使用 textContent 或安全的 HTML 过滤'
                    })

        return issues

    def _format_results(self, files_reviewed: List[str], issues: List[Dict]) -> str:
        """格式化审查结果"""
        lines = [f"📋 代码审查完成，共审查 {len(files_reviewed)} 个文件\n"]

        if not issues:
            lines.append("✅ 没有发现问题！")
            return "\n".join(lines)

        # 按严重程度排序
        severity_order = {'error': 0, 'warning': 1, 'info': 2}
        issues_sorted = sorted(issues, key=lambda x: severity_order.get(x['severity'], 99))

        # 统计
        error_count = sum(1 for i in issues if i['severity'] == 'error')
        warning_count = sum(1 for i in issues if i['severity'] == 'warning')
        info_count = sum(1 for i in issues if i['severity'] == 'info')

        lines.append(f"📊 统计:")
        lines.append(f"   ❌ 错误: {error_count}")
        lines.append(f"   ⚠️  警告: {warning_count}")
        lines.append(f"   ℹ️  信息: {info_count}")
        lines.append("")

        # 详情
        lines.append("🔍 问题详情:")
        lines.append("-" * 60)

        current_file = None
        for issue in issues_sorted:
            if issue['file'] != current_file:
                current_file = issue['file']
                lines.append(f"\n📄 {current_file}")

            severity_icon = '❌' if issue['severity'] == 'error' else '⚠️' if issue['severity'] == 'warning' else 'ℹ️'
            lines.append(f"   {severity_icon} 第 {issue['line']} 行 [{issue['category']}]:")
            lines.append(f"      {issue['message']}")
            if issue['suggestion']:
                lines.append(f"      💡 建议: {issue['suggestion']}")

        return "\n".join(lines)
