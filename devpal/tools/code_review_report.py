# -*- coding: utf-8 -*-
"""
代码审查报告生成工具
生成详细的代码审查文档，包含问题统计、分类、详细信息
"""
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult


class CodeReviewReportTool(BaseTool):
    """代码审查报告生成工具 - 生成详细的审查结果文档"""

    name = "code_review_report"
    description = "生成详细的代码审查报告文档，包含问题统计、分类、详细信息"

    class Parameters(BaseModel):
        file_path: str = Field(
            description="被审查的源代码文件路径"
        )
        issues: List[Dict[str, Any]] = Field(
            default=None,
            description="代码审查发现的问题列表（如果不提供则自动运行代码审查）"
        )
        output_dir: Optional[str] = Field(
            default=None,
            description="输出目录（默认使用项目名目录）"
        )
        project_name: Optional[str] = Field(
            default=None,
            description="项目名称（默认使用文件名作为项目名）"
        )

    def _execute(self, params: Parameters) -> ToolResult:
        file_path = Path(params.file_path)
        if not file_path.exists():
            return ToolResult.error(f"源文件不存在: {params.file_path}")

        # 确定项目名
        project_name = params.project_name or file_path.stem

        # 确定输出目录
        if params.output_dir:
            output_dir = Path(params.output_dir)
        else:
            output_dir = Path(project_name)

        output_dir.mkdir(parents=True, exist_ok=True)

        # 获取问题列表
        issues = params.issues
        if issues is None:
            # 自动运行代码审查
            from .registry import registry as global_registry
            review_result = global_registry.execute_tool('code_review', {
                'file_path': str(file_path)
            })
            issues = review_result.metadata.get('issues', [])

        # 生成报告
        report_file = output_dir / f"{file_path.stem}_code_review.md"
        self._generate_report(report_file, file_path, issues, project_name)

        return ToolResult.ok(
            f"代码审查报告已生成: {report_file}",
            source_file=str(file_path),
            report_file=str(report_file),
            output_dir=str(output_dir),
            project_name=project_name,
            issues_count=len(issues),
            error_count=sum(1 for i in issues if i.get('severity') == 'error'),
            warning_count=sum(1 for i in issues if i.get('severity') == 'warning'),
            info_count=sum(1 for i in issues if i.get('severity') == 'info')
        )

    def _generate_report(self, report_file: Path, source_file: Path,
                         issues: List[Dict[str, Any]], project_name: str):
        """生成详细的代码审查报告"""

        # 统计分类
        errors = [i for i in issues if i.get('severity') == 'error']
        warnings = [i for i in issues if i.get('severity') == 'warning']
        infos = [i for i in issues if i.get('severity') == 'info']

        # 按类别分类
        categories = {}
        for issue in issues:
            category = issue.get('category', 'other')
            if category not in categories:
                categories[category] = []
            categories[category].append(issue)

        content = f"""# 代码审查报告 - {project_name}

> 审查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> 源文件: `{source_file.name}`
> 文件路径: `{source_file.absolute()}`

## 审查概览

| 统计项 | 数量 |
|--------|------|
| 总问题数 | {len(issues)} |
| 🔴 错误 | {len(errors)} |
| 🟡 警告 | {len(warnings)} |
| ™️  信息 | {len(infos)} |

### 问题分类统计

| 类别 | 数量 |
|------|------|
"""

        for category, items in sorted(categories.items()):
            category_name = {
                'bug': 'Bug/缺陷',
                'security': '安全问题',
                'performance': '性能问题',
                'style': '代码风格',
                'todo': '待办事项',
                'debug': '调试代码',
                'other': '其他问题'
            }.get(category, category.capitalize())
            content += f"| {category_name} | {len(items)} |\n"

        content += """
## 详细问题列表

### 🔴 错误（必须修复）

"""
        if errors:
            for i, issue in enumerate(errors, 1):
                content += self._format_issue(i, issue)
        else:
            content += "✅ 无错误\n"

        content += """
### 🟡 警告（建议修复）

"""
        if warnings:
            for i, issue in enumerate(warnings, 1):
                content += self._format_issue(i, issue)
        else:
            content += "✅ 无警告\n"

        content += """
### ™️ 信息（可选优化）

"""
        if infos:
            for i, issue in enumerate(infos, 1):
                content += self._format_issue(i, issue)
        else:
            content += "✅ 无信息提示\n"

        content += """
## 按类别查看问题

"""
        for category, items in sorted(categories.items()):
            category_name = {
                'bug': 'Bug/缺陷',
                'security': '安全问题',
                'performance': '性能问题',
                'style': '代码风格',
                'todo': '待办事项',
                'debug': '调试代码',
                'other': '其他问题'
            }.get(category, category.capitalize())

            content += f"""
### {category_name} ({len(items)}个)

| 序号 | 文件 | 行号 | 问题描述 | 修复建议 |
|------|------|------|----------|----------|
"""
            for i, issue in enumerate(items, 1):
                content += f"| {i} | {issue.get('file', '-')} | {issue.get('line', '-')} | {issue.get('message', '-')} | {issue.get('suggestion', '-')} |\n"

        content += f"""
## 修复建议优先级

### 高优先级（立即修复）
- 所有 🔴 错误类问题
- 安全漏洞、内存泄漏、潜在崩溃问题

### 中优先级（近期修复）
- 大部分 🟡 警告类问题
- 性能瓶颈、逻辑缺陷

### 低优先级（后续优化）
- 代码风格问题
- 建议性优化

---
*本报告由 DevPalAgent CodeReviewReportTool 自动生成*
"""

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(content)

    def _format_issue(self, index: int, issue: Dict[str, Any]) -> str:
        """格式化单个问题"""
        severity = issue.get('severity', 'unknown')
        file = issue.get('file', '-')
        line = issue.get('line', '-')
        message = issue.get('message', '-')
        suggestion = issue.get('suggestion', '-')
        category = issue.get('category', 'other')

        category_name = {
            'bug': 'Bug',
            'security': '安全',
            'performance': '性能',
            'style': '风格',
            'todo': '待办',
            'debug': '调试',
            'other': '其他'
        }.get(category, category.capitalize())

        return f"""**{index}. [{category_name}] {message}**
- 文件: `{file}`
- 行号: {line}
- 严重程度: {severity}
- 修复建议: {suggestion}

"""
