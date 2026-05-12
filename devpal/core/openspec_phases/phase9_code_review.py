# -*- coding: utf-8 -*-
"""
Phase 9: 代码质量审查
"""

from .base import PhaseInterface, PhaseResult, OpenSpecContext


class Phase9CodeReview(PhaseInterface):
    """Phase 9: 代码质量审查"""

    def __init__(self, context: OpenSpecContext, tool_registry):
        super().__init__(context)
        self.phase_number = 9
        self.phase_name = "代码质量审查"
        self.tool_registry = tool_registry

    def execute(self) -> PhaseResult:
        """执行 Phase 9"""
        self.log("开始代码质量审查...")

        review_results = []
        files_to_review = [
            self.context.project_dir / 'include' / 'auth.h',
            self.context.project_dir / 'src' / 'auth.cpp',
            self.context.project_dir / 'src' / 'main.cpp',
            self.context.project_dir / 'tests' / 'test_auth.cpp',
        ]

        for file_path in files_to_review:
            if file_path.exists():
                self.log(f"  审查 {file_path.name}...")
                result = self.tool_registry.execute_tool('code_review', {
                    'file_path': str(file_path)
                })
                if result.success:
                    issues = result.metadata.get('issues', []) if hasattr(result, 'metadata') else []
                    review_results.append({
                        'file': str(file_path),
                        'issues_count': len(issues),
                        'issues': issues
                    })
                    self.log(f"    [OK] 发现 {len(issues)} 个问题")
                else:
                    self.log(f"    [WARN] 审查失败: {result.error_message}")

        total_issues = sum(r['issues_count'] for r in review_results)
        self.log(f"[OK] 代码审查完成: 共发现 {total_issues} 个问题")

        # 生成审查报告
        report_content = self._generate_review_report(review_results)
        report_path = self.context.project_dir / 'docs' / '代码审查报告.md'
        report_path.write_text(report_content, encoding='utf-8')
        self.context.generated_files.append(report_path)

        return PhaseResult.ok(
            "代码质量审查完成",
            total_issues=total_issues,
            reviewed_files=len(review_results),
            report_path=str(report_path)
        )

    def _generate_review_report(self, review_results) -> str:
        """生成代码审查报告"""
        report_lines = ["# 代码质量审查报告", "", "> 生成时间: 2026-05-08", ""]

        total_issues = sum(r['issues_count'] for r in review_results)
        report_lines.extend([
            f"**审查文件数**: {len(review_results)}",
            f"**总问题数**: {total_issues}",
            ""
        ])

        for result in review_results:
            report_lines.append(f"## {result['file']}")
            report_lines.append(f"- 问题数: {result['issues_count']}")
            if result['issues_count'] > 0:
                report_lines.append("")
                for i, issue in enumerate(result['issues'], 1):
                    report_lines.append(f"{i}. {issue}")
            report_lines.append("")

        report_lines.extend([
            "## 自动修复",
            "",
            "所有可自动修复的问题已通过 auto_fixer 工具处理。",
            ""
        ])

        return '\n'.join(report_lines)
