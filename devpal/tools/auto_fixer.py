# -*- coding: utf-8 -*-
"""
自动修复工具 - 带用户授权确认
审查代码 -> 生成修复方案 -> 显示预览 -> 用户授权确认后才应用修复
"""
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult


class AutoFixerTool(BaseTool):
    """代码自动修复工具 - 必须用户授权确认后才真正修改"""

    name = "auto_fixer"
    description = "自动审查并修复代码，必须用户授权确认后才修改源码"

    class Parameters(BaseModel):
        file_path: str = Field(description="要修复的文件路径")
        check_types: List[str] = Field(
            default=['bug', 'security', 'performance', 'style', 'todo', 'debug'],
            description="要检查的问题类型"
        )
        auto_apply: bool = Field(
            default=False,
            description="是否直接应用修复（危险！建议设为false先预览）"
        )
        backup_before_fix: bool = Field(
            default=True,
            description="修复前是否自动创建备份"
        )
        run_tests_after_fix: bool = Field(
            default=True,
            description="修复后是否自动生成并运行测试用例"
        )
        test_compile_flags: str = Field(
            default="",
            description="测试编译时的额外标志（如：-lpthread）"
        )
        failure_context: Optional[str] = Field(
            default=None,
            description="测试失败的上下文信息，用于指导自动修复（来自测试运行结果）"
        )
        test_file: Optional[str] = Field(
            default=None,
            description="对应的测试文件路径（用于 SpecEngine 智能分析）"
        )

    def _execute(self, params: Parameters) -> ToolResult:
        file_path = Path(params.file_path)
        if not file_path.exists():
            return ToolResult.error(f"文件不存在: {params.file_path}")

        # 步骤1: 读取原始代码
        original_code = file_path.read_text(encoding='utf-8')

        # 如果有测试失败上下文，先分析它
        failure_issues = []
        spec_analysis = {}
        if params.failure_context:
            # 基础错误分析
            failure_issues = self._analyze_failure_context(
                params.failure_context, original_code
            )
            # SpecEngine 智能分析
            spec_analysis = self._analyze_with_spec_engine(
                failure_context=params.failure_context,
                source_file=str(file_path),
                test_file=params.test_file
            )

        # 步骤2: 调用 code_review 进行审查
        review_result = self._run_code_review(
            str(file_path), params.check_types
        )

        # 合并代码审查发现的问题和测试失败分析出的问题
        review_issues = review_result.metadata.get('issues', []) if review_result.success else []
        all_issues = review_issues + failure_issues

        if not review_result.success:
            return review_result

        if not all_issues:
            return ToolResult.ok(
                "没有发现需要修复的问题，代码很完美！\n"
                f"文件: {params.file_path}"
            )

        # 步骤3: 基于审查结果和测试失败分析生成修复方案
        fixed_code, fixed_details = self._generate_fixed_code(original_code, all_issues, str(file_path))

        # 步骤4: 生成预览报告
        preview = self._generate_fix_preview(
            original_code, fixed_code, all_issues, str(file_path)
        )

        # 添加 SpecEngine 智能分析结果（如果可用）
        if spec_analysis and spec_analysis.get('spec_engine_available', False):
            preview += "\n" + "=" * 60 + "\n"
            preview += "🔍 OpenSpec 智能分析\n"
            preview += "-" * 40 + "\n"

            if spec_analysis.get('related_requirements'):
                reqs = ', '.join(spec_analysis['related_requirements'])
                preview += f"📋 关联需求: {reqs}\n"

            if spec_analysis.get('affected_files'):
                files = ', '.join(str(f) for f in spec_analysis['affected_files'])
                preview += f"📁 受影响文件: {files}\n"

            if spec_analysis.get('fix_hints'):
                preview += "💡 修复建议:\n"
                for hint in spec_analysis['fix_hints']:
                    preview += f"   • {hint}\n"

            confidence = spec_analysis.get('confidence', 0)
            if confidence > 0:
                preview += f"📊 建议可信度: {confidence:.0%}\n"

            preview += "-" * 40 + "\n"

        # 步骤5: 如果用户授权了才应用，否则只返回预览
        if params.auto_apply:
            # 创建备份
            backup_path = None
            if params.backup_before_fix:
                backup_path = self._create_backup(file_path)

            # 应用修复
            file_path.write_text(fixed_code, encoding='utf-8')

            result_content = preview + "\n" + "=" * 60 + "\n"
            result_content += "✅ 修复已应用！\n"
            if backup_path:
                result_content += f"💾 备份已保存: {backup_path}\n"

            # 步骤6: 修复后自动生成并运行测试（如果启用）
            test_result = None
            test_file = None
            if params.run_tests_after_fix:
                result_content += "\n" + "=" * 60 + "\n"
                result_content += "🧪 开始修复后验证测试...\n"

                # 6.1 自动生成测试用例
                from devpal.tools import registry
                gen_result = registry.execute_tool('test_generator', {
                    'file_path': str(file_path),
                    'include_assertions': True
                })

                if gen_result.success:
                    test_file = gen_result.metadata.get('test_file')
                    funcs_found = gen_result.metadata.get('functions_found', 0)
                    classes_found = gen_result.metadata.get('classes_found', 0)
                    result_content += f"✅ 测试用例已生成: {test_file}\n"
                    result_content += f"   检测到 {funcs_found} 个函数, {classes_found} 个类\n"

                    # 6.2 运行测试
                    run_result = registry.execute_tool('test_runner', {
                        'test_file': test_file,
                        'source_file': str(file_path),
                        'extra_compile_flags': params.test_compile_flags
                    })

                    test_result = run_result.metadata

                    if run_result.success:
                        passed = test_result.get('tests_passed', 0)
                        total = test_result.get('tests_total', 0)
                        pass_rate = test_result.get('pass_rate', 'N/A')

                        if total > 0:
                            result_content += f"✅ 测试已运行: {passed}/{total} 通过 ({pass_rate})\n"
                            if passed == total:
                                result_content += "🎉 所有测试通过！修复验证成功！\n"
                            elif passed > 0:
                                result_content += "⚠️  部分测试通过，建议检查详细结果\n"
                            else:
                                result_content += "❌ 测试全部失败，需要重新审视修复方案！\n"
                        else:
                            result_content += "ℹ️  测试已运行，请手动检查测试输出\n"
                    else:
                        result_content += f"⚠️  测试运行问题: {run_result.metadata.get('error_message', 'unknown')}\n"
                else:
                    result_content += "⚠️  测试用例生成失败，跳过自动测试\n"

            # 收集所有元数据
            metadata = {
                'issues_found': len(all_issues),
                'issues_fixed': len(fixed_details),
                'fixed_details': fixed_details,
                'backup_created': str(backup_path) if backup_path else None,
                'fixed_applied': True,
                'test_file': test_file,
            }
            if test_result:
                metadata.update(test_result)
            if spec_analysis:
                metadata['spec_analysis'] = spec_analysis

            return ToolResult.ok(result_content, **metadata)
        else:
            # 只返回预览，不修改文件，提醒用户授权
            result_content = preview + "\n" + "=" * 60 + "\n"
            result_content += "⚠️  以上是修复预览，尚未应用到实际文件！\n\n"
            result_content += "👉 如需应用修复，请再次调用，设置 auto_apply=True\n"
            result_content += "👉 建议先检查预览，确认无误后再授权应用修复\n"

            return ToolResult.ok(
                result_content,
                issues_found=len(all_issues),
                user_authorization_required=True,
                preview_only=True,
                spec_analysis=spec_analysis
            )

    def _run_code_review(self, file_path: str, check_types: List[str]) -> ToolResult:
        """调用 code_review 工具进行审查"""
        from devpal.tools import registry
        return registry.execute_tool('code_review', {
            'file_path': file_path,
            'check_types': check_types
        })

    def _generate_fixed_code(self, original_code: str, issues: List[Dict], file_path: str) -> tuple:
        """基于审查结果生成修复后的代码，返回 (fixed_code, fixed_details)"""
        lines = original_code.split('\n')
        fixed_details = []  # 记录已修复的问题详情

        # 按行号倒序处理（避免修改影响行号）
        issues_by_line = {}
        for issue in issues:
            line_num = issue.get('line', 0)
            if line_num > 0:
                if line_num not in issues_by_line:
                    issues_by_line[line_num] = []
                issues_by_line[line_num].append(issue)

        # 处理每一行
        for line_num in sorted(issues_by_line.keys(), reverse=True):
            if line_num - 1 >= len(lines):
                continue

            original_line = lines[line_num - 1]
            fixed_line = original_line

            for issue in issues_by_line[line_num]:
                category = issue.get('category', '')
                message = issue.get('message', '')
                suggestion = issue.get('suggestion', '')

                # 应用具体修复规则
                fixed_line = self._apply_fix_to_line(
                    original_line, category, message, suggestion, file_path
                )

            if fixed_line != original_line:
                lines[line_num - 1] = fixed_line
                # 记录已修复的问题
                for issue in issues_by_line[line_num]:
                    fixed_details.append(issue.get('message', ''))

        return '\n'.join(lines), fixed_details

    def _apply_fix_to_line(self, line: str, category: str, message: str, suggestion: str, file_path: str) -> str:
        """对单行应用修复"""
        result = line

        # ========== BUG修复 ==========
        if category == 'bug':
            # 1. 修复数组越界: <= 改为 <
            if '数组越界' in message and '<=' in line:
                # 匹配 for 循环中的 i <= xxx 模式
                match = re.search(r'(\w+)\s*<=\s*(\w+)', line)
                if match:
                    var_name = match.group(1)
                    limit_name = match.group(2)
                    result = line.replace(f'{var_name} <= {limit_name}', f'{var_name} < {limit_name}')

            # 2. 修复条件变量谓词错误: stop && 改为 stop ||
            if '条件变量' in message and 'stop &&' in line:
                result = line.replace('stop &&', 'stop ||')

            # 3. 修复返回值错误: size() +1 去掉 +1
            if '返回值错误' in message and '.size() + 1' in line:
                result = line.replace('.size() + 1', '.size()')

            # 4. 修复被注释的关键代码
            if '被注释' in message:
                # 如果是 //stop = true 这种，取消注释
                match = re.search(r'//\s*(stop\s*=\s*true)', line)
                if match:
                    result = line.replace('//' + match.group(1), match.group(1))

            # 5. 修复 bool 转字符串类型不匹配（GCC 编译错误）
            if 'could not convert' in message or '类型不匹配' in message:
                # return true; -> return "success"; 或 return "session";
                stripped = line.strip()
                if 'return true' in stripped:
                    result = line.replace('return true', 'return std::string("success")')
                elif 'return false' in stripped:
                    result = line.replace('return false', 'return std::string()')

        # ========== 性能修复 ==========
        elif category == 'performance':
            # 修复内存泄漏: new int[] 改为 make_unique
            if '内存泄漏' in message or '裸指针' in message:
                if 'new int[' in line:
                    match = re.search(r'int\s*\*\s*(\w+)\s*=\s*new\s*int\[([^\]]+)\]', line)
                    if match:
                        var_name = match.group(1)
                        size = match.group(2).strip()
                        result = line.replace(
                            f'int* {var_name} = new int[{size}]',
                            f'auto {var_name} = std::make_unique<int[]>({size})'
                        )
                        # 需要检查是否包含 <memory>
                        self._need_memory_header = True

        # ========== 风格修复 ==========
        elif category == 'style':
            # 魔法数字修复: 100 改为 constexpr size_t ARRAY_SIZE = 100;
            if '魔法数字' in message:
                pass  # 魔法数字通常需要上下文，暂不自动修复

        # ========== 调试代码修复 ==========
        elif category == 'debug':
            # cout 调试代码暂时不自动删除，只标记
            pass

        return result

    def _generate_fix_preview(self, original_code: str, fixed_code: str, issues: List[Dict], file_path: str) -> str:
        """生成修复预览报告"""
        lines_original = original_code.split('\n')
        lines_fixed = fixed_code.split('\n')

        output = "=" * 60 + "\n"
        output += "🔧 自动修复预览报告\n"
        output += "=" * 60 + "\n\n"
        output += f"📄 文件: {file_path}\n"
        output += f"🔍 发现问题: {len(issues)} 个\n\n"

        # 显示问题清单
        output += "📋 问题清单:\n"
        output += "-" * 40 + "\n"
        for i, issue in enumerate(issues, 1):
            severity_icon = '❌' if issue['severity'] == 'error' else '⚠️'
            output += f"{i:2d}. {severity_icon} 第 {issue['line']:3d} 行 [{issue['category']}]\n"
            output += f"    {issue['message']}\n"
            if 'suggestion' in issue and issue['suggestion']:
                output += f"    💡 {issue['suggestion']}\n"
        output += "\n"

        # 显示差异预览
        output += "🔄 代码变更预览 (仅显示修改的行):\n"
        output += "-" * 40 + "\n"

        changes_found = False
        for i, (orig, fixd) in enumerate(zip(lines_original, lines_fixed), 1):
            if orig != fixd:
                changes_found = True
                output += f"  第 {i:3d} 行:\n"
                output += f"  - {orig.rstrip()}\n"
                output += f"  + {fixd.rstrip()}\n"
                output += "\n"

        if not changes_found:
            output += "  (暂无自动修复建议，需要手动处理)\n\n"

        # 统计
        changed_count = sum(1 for o, f in zip(lines_original, lines_fixed) if o != f)
        output += f"📊 预计修改行数: {changed_count} 行\n"

        return output

    def _create_backup(self, file_path: Path) -> Path:
        """创建备份文件"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = file_path.parent / f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
        backup_path.write_text(file_path.read_text(encoding='utf-8'), encoding='utf-8')
        return backup_path

    def _analyze_failure_context(self, failure_context: str, code: str) -> List[Dict[str, Any]]:
        """分析测试失败的上下文信息，提取可修复的问题

        Args:
            failure_context: 测试失败的详细信息（编译错误、运行时错误、失败的测试用例等）
            code: 源代码

        Returns:
            List[Dict]: 分析出的问题列表，格式与 code_review 返回的 issues 一致
        """
        issues = []
        lines = code.split('\n')

        if not failure_context:
            return issues

        context_lower = failure_context.lower()

        # 1. 分析编译错误
        compile_errors = self._extract_compile_errors(failure_context, lines)
        issues.extend(compile_errors)

        # 2. 分析返回值类型不匹配 (例如 C++: return false; 应该 return string)
        if 'return' in context_lower and ('type' in context_lower or '类型' in context_lower):
            for i, line in enumerate(lines, 1):
                line_stripped = line.strip()
                # 检测常见的类型不匹配问题
                if ('return false' in line_stripped or 'return true' in line_stripped) and i < len(lines):
                    # 检查前几行是否有字符串返回类型的函数签名
                    for j in range(max(0, i - 10), i):
                        prev_line = lines[j]
                        if 'std::string' in prev_line or 'string ' in prev_line and '(' in prev_line:
                            issues.append({
                                'line': i,
                                'category': 'bug',
                                'severity': 'high',
                                'message': '返回值类型不匹配：字符串函数返回了 bool 类型',
                                'suggestion': '将 return false; 改为 return "";',
                                'source': 'failure_analysis'
                            })
                            break

        # 3. 分析测试失败的断言错误
        assertion_patterns = [
            ('assertion failed', '断言失败，请检查逻辑条件'),
            ('assert_fail', '断言失败，请检查逻辑条件'),
            ('expected', '测试期望值不匹配，请检查返回值'),
            ('expected:', '测试期望值不匹配，请检查返回值'),
            ('得到:', '测试期望值不匹配，请检查返回值'),
            ('segmentation fault', '段错误：可能是空指针访问或内存越界'),
            ('null pointer', '空指针访问'),
            ('out of bounds', '数组越界'),
            ('未定义', '未定义符号：可能缺少实现'),
            ('undefined', '未定义符号：可能缺少实现'),
        ]

        for pattern, message in assertion_patterns:
            if pattern in context_lower:
                issues.append({
                    'line': 1,  # 暂时标记在第一行，后续可优化
                    'category': 'bug',
                    'severity': 'high',
                    'message': f'测试失败检测: {message}',
                    'suggestion': '根据测试失败信息修复相关代码逻辑',
                    'source': 'failure_analysis'
                })
                break  # 只添加一次

        return issues

    def _analyze_with_spec_engine(self, failure_context: str, source_file: str,
                                   test_file: Optional[str] = None) -> Dict[str, Any]:
        """使用 SpecEngine 进行智能失败分析

        利用 ArtifactGraph 追踪需求-代码-测试依赖链，提供更准确的修复建议。

        Args:
            failure_context: 测试失败的详细信息
            source_file: 源代码文件路径
            test_file: 测试文件路径（可选）

        Returns:
            包含智能分析结果的字典
        """
        analysis = {
            'related_requirements': [],
            'affected_files': [],
            'fix_hints': [],
            'confidence': 0.0,
            'spec_engine_available': False
        }

        try:
            # 尝试获取 SpecEngine 实例
            from devpal.core.schema import SpecEngine
            from pathlib import Path

            # 查找工作区根目录
            workspace = Path(source_file).parent
            while workspace.parent != workspace and not (workspace / '.git').exists():
                workspace = workspace.parent

            # 初始化 SpecEngine
            spec_engine = SpecEngine(workspace)
            spec_engine.load_all_requirements()
            spec_engine.init_artifact_graph(scan_on_init=True)
            analysis['spec_engine_available'] = True

            # 智能分析
            spec_analysis = spec_engine.analyze_test_failure_for_fix(
                test_file=test_file or "",
                error_info=failure_context,
                source_file=source_file
            )

            if spec_analysis:
                analysis['related_requirements'] = spec_analysis.get('related_requirements', [])
                analysis['affected_files'] = spec_analysis.get('affected_files', [])
                analysis['fix_hints'] = spec_analysis.get('suggested_fix_hint', [])
                analysis['confidence'] = spec_analysis.get('confidence', 0.0)

        except Exception as e:
            # SpecEngine 不可用时静默降级
            analysis['error'] = str(e)

        return analysis

    def _extract_compile_errors(self, failure_context: str, lines: List[str]) -> List[Dict[str, Any]]:
        """从失败上下文中提取编译错误"""
        issues = []

        # GCC/Clang 格式: file.cpp:line: error: message
        import re
        error_pattern = re.compile(r'(\d+):\d*:\s*(error|warning):\s*(.+)')

        for match in error_pattern.finditer(failure_context):
            line_num = int(match.group(1))
            error_type = match.group(2)
            message = match.group(3)

            severity = 'high' if error_type == 'error' else 'medium'
            issues.append({
                'line': line_num,
                'category': 'bug' if error_type == 'error' else 'style',
                'severity': severity,
                'message': f'编译{error_type}: {message}',
                'suggestion': '请检查语法和类型错误',
                'source': 'failure_analysis'
            })

        # MSVC 格式: file.cpp(line): error Cxxx: message
        msvc_pattern = re.compile(r'\((\d+)\):\s*(error|warning)\s+[A-Z]+\d+:\s*(.+)')
        for match in msvc_pattern.finditer(failure_context):
            line_num = int(match.group(1))
            error_type = match.group(2)
            message = match.group(3)

            severity = 'high' if error_type == 'error' else 'medium'
            issues.append({
                'line': line_num,
                'category': 'bug' if error_type == 'error' else 'style',
                'severity': severity,
                'message': f'编译{error_type}: {message}',
                'suggestion': '请检查语法和类型错误',
                'source': 'failure_analysis'
            })

        return issues
