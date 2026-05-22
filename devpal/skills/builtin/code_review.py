"""
CodeReviewSkill - 代码审查 Skill

审查代码质量，生成报告。
"""

import re
from pathlib import Path
from typing import Optional
from datetime import datetime

from devpal.skills.base import BaseSkill, SkillContext, SkillResult
from devpal.tools.code_review import CodeReviewTool


class CodeReviewSkill(BaseSkill):
    """代码审查 Skill"""

    name = "code_review_skill"
    description = "审查代码质量，生成报告"
    triggers = ["代码审查", "review", "检查代码", "code review", "审查"]
    required_tools = []

    def __init__(self):
        self.reviewer = CodeReviewTool()

    def can_handle(self, context: SkillContext) -> float:
        """判断是否能处理"""
        base_confidence = super().can_handle(context)

        # 检查是否提到文件路径或文件扩展名
        file_extensions = [".py", ".cpp", ".java", ".ts", ".js", ".go", ".rs"]
        query_lower = context.user_query.lower()
        for ext in file_extensions:
            if ext in query_lower:
                return min(base_confidence + 0.1, 1.0)

        return base_confidence

    def execute(self, context: SkillContext) -> SkillResult:
        """执行代码审查"""
        # 1. 识别文件或目录
        target = self._extract_target(context.user_query, context.workspace_path)

        if not target:
            return SkillResult(
                success=False,
                content="无法从查询中提取文件路径或目录",
                metadata={"query": context.user_query}
            )

        # 2. 执行审查
        try:
            if target.is_file():
                params = self.reviewer.Parameters(file_path=str(target))
                review_result = self.reviewer.execute(params)
            elif target.is_dir():
                params = self.reviewer.Parameters(directory=str(target))
                review_result = self.reviewer.execute(params)
            else:
                return SkillResult(
                    success=False,
                    content=f"目标不存在: {target}",
                    metadata={"target": str(target)}
                )
        except Exception as e:
            return SkillResult(
                success=False,
                content=f"代码审查失败: {str(e)}",
                metadata={"target": str(target), "error": str(e)}
            )

        # 3. 生成报告
        report_path = context.workspace_path / "docs" / "code_review_report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)

        report_content = self._format_report(review_result, target)
        report_path.write_text(report_content, encoding='utf-8')

        # 4. 返回结果
        issue_count = self._count_issues(review_result)
        return SkillResult(
            success=review_result.success,
            content=f"代码审查完成: {issue_count} 个问题",
            artifacts=[str(report_path)],
            metadata={
                "target": str(target),
                "issues": issue_count,
                "report": str(report_path)
            }
        )

    def _extract_target(self, query: str, workspace: Path) -> Optional[Path]:
        """从查询中提取文件路径或目录"""
        # 尝试匹配文件路径模式
        # 1. 匹配带扩展名的文件路径
        file_pattern = r'[\w/\\.-]+\.\w+'
        match = re.search(file_pattern, query)
        if match:
            path = workspace / match.group(0)
            if path.exists():
                return path

        # 2. 匹配目录路径
        dir_pattern = r'[\w/\\.-]+'
        match = re.search(dir_pattern, query)
        if match:
            path = workspace / match.group(0)
            if path.exists() and path.is_dir():
                return path

        # 3. 默认审查当前目录
        return workspace

    def _format_report(self, review_result, target: Path) -> str:
        """格式化审查报告"""
        report = f"""# 代码审查报告

## 审查目标
- 路径: {target}
- 时间: {self._get_timestamp()}

## 审查结果
"""
        if review_result.success:
            report += f"\n{review_result.content}\n"
        else:
            report += f"\n**错误**: {review_result.content}\n"

        report += "\n---\n生成工具: DevPalAgent CodeReviewSkill\n"
        return report

    def _count_issues(self, review_result) -> int:
        """统计问题数量"""
        if not review_result.success:
            return 0

        # 简单统计：计算包含 "问题" 或 "issue" 的行数
        content = review_result.content.lower()
        return content.count("问题") + content.count("issue")

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")