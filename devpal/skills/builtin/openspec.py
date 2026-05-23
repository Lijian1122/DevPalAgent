"""
OpenSpecSkill - OpenSpec 完整项目生成 Skill

执行完整的 OpenSpec 11-phase 工作流，从需求到代码生成。
"""

from pathlib import Path
from typing import Optional
from devpal.skills.base import BaseSkill, SkillContext, SkillResult


class OpenSpecSkill(BaseSkill):
    """OpenSpec Skill - 执行完整的 11-phase 工作流"""
    
    name = "openspec_skill"
    description = "执行完整的 OpenSpec 11-phase 工作流：从需求分析到代码生成、测试、文档"
    triggers = [
        "完整项目", "端到端", "openspec", "full project", 
        "11-phase", "全流程", "需求到代码"
    ]
    required_tools = []  # 直接使用 openspec_executor

    def can_handle(self, context: SkillContext) -> float:
        """判断是否能处理当前查询"""
        base_confidence = super().can_handle(context)
        query_lower = context.user_query.lower()

        # 检查流程关键词匹配度
        workflow_keywords = [
            "完整", "端到端", "全流程", "需求", 
            "requirement", "spec", "e2e", "end-to-end"
        ]
        keyword_count = sum(1 for keyword in workflow_keywords if keyword in query_lower)

        return min(base_confidence + 0.15 * (keyword_count >= 2), 1.0)

    def execute(self, context: SkillContext) -> SkillResult:
        """执行 OpenSpec 工作流"""
        # 1. 检查执行器初始化状态
        if not context.openspec_executor:
            return SkillResult(
                success=False,
                content="openspec_executor 未初始化，无法执行 OpenSpec 工作流",
                metadata={"error": "missing_openspec_executor"}
            )

        # 2. 提取需求文件路径
        requirement_file = self._extract_requirement_file(context)
        if not requirement_file:
            return SkillResult(
                success=False,
                content="未能从查询中提取需求文件路径，请明确指定需求文档（如 requirements/xxx.md）",
                metadata={"error": "missing_requirement_file"}
            )

        # 3. 验证文件存在性
        full_path = context.workspace_path / requirement_file
        if not full_path.exists():
            return SkillResult(
                success=False,
                content=f"需求文件不存在: {requirement_file}",
                metadata={
                    "error": "file_not_found",
                    "requirement_file": str(requirement_file)
                }
            )

        # 4. 执行 11-phase 工作流
        try:
            result = context.openspec_executor.run(
                requirement_file=str(full_path),
                workspace_path=context.workspace_path
            )

            if result.get('success', False):
                # 收集工件
                artifacts = [
                    artifact 
                    for phase in result.get('phases_completed', [])
                    for artifact in phase.get('artifacts', [])
                ]

                return SkillResult(
                    success=True,
                    content=self._format_openspec_result(result),
                    artifacts=artifacts,
                    metadata={
                        "requirement_file": str(requirement_file),
                        "phases_completed": len(result.get('phases_completed', [])),
                        "total_phases": 11,
                        "artifacts_generated": len(artifacts),
                        "execution_time": result.get('execution_time', 0)
                    }
                )
            
            # 工作流执行失败
            error_message = result.get('error', 'Unknown error')
            return SkillResult(
                success=False,
                content=f"OpenSpec 工作流执行失败\n\n错误: {error_message}",
                metadata={
                    "error": "workflow_failed",
                    "error_message": error_message
                }
            )

        except Exception as e:
            return SkillResult(
                success=False,
                content=f"OpenSpec 工作流执行过程出错: {str(e)}",
                metadata={
                    "error": "exception",
                    "exception_message": str(e)
                }
            )

    def _extract_requirement_file(self, context: SkillContext) -> Optional[str]:
        """从查询中提取需求文件路径"""
        import re

        patterns = [
            r'(?:需求|requirement|spec|文档)\s*[:：]?\s*[`"]?([^\s`"]+\.md)[`"]?',
            r'[`"]([^\s`"]+\.md)[`"]',
            r'(requirements?/[\w/]+\.md)',
            r'(req_[\w]+\.md)'
        ]

        # 1. 正则匹配用户查询
        for pattern in patterns:
            if match := re.search(pattern, context.user_query, re.IGNORECASE):
                return match.group(1)

        # 2. 检查上下文元数据
        if 'requirement_file' in context.metadata:
            return context.metadata['requirement_file']

        # 3. 默认查找 requirements 目录
        requirements_dir = context.workspace_path / "requirements"
        if requirements_dir.is_dir():
            if md_files := list(requirements_dir.glob("*.md")):
                return str(md_files[0].relative_to(context.workspace_path))

        return None

    def _format_openspec_result(self, result: dict) -> str:
        """格式化 OpenSpec 执行结果"""
        phases = result.get('phases_completed', [])
        completed = len(phases)
        total = 11

        # 标题部分
        output = [
            "OpenSpec 11-Phase 工作流执行成功",
            "",
            f"执行时间: {result.get('execution_time', 0):.2f}s",
            f"完成阶段: {completed}/{total}",
            "",
            "各阶段执行情况:"
        ]

        # 阶段详情
        for i, phase in enumerate(phases, 1):
            status_icon = "✅" if phase.get('status') == "success" else "❌"
            phase_time = phase.get('execution_time', 0)
            
            output.append(
                f"  {status_icon} Phase {i}: {phase.get('name', f'阶段 {i}')} "
                f"({phase_time:.2f}s)"
            )

            # 工件展示（最多显示3个）
            artifacts = phase.get('artifacts', [])
            if artifacts:
                output.append(f"     生成工件: {len(artifacts)} 个")
                for artifact in artifacts[:3]:
                    output.append(f"       - {artifact}")
                if len(artifacts) > 3:
                    output.append(f"       - ... 还有 {len(artifacts) - 3} 个")

        # 结束提示
        output.extend(["", "工作流完成，所有工件已生成到项目目录"])
        
        return "\n".join(output)