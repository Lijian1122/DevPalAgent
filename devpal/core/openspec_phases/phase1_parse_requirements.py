# -*- coding: utf-8 -*-
"""
Phase 1: 解析需求文档
"""

from .base import PhaseInterface, PhaseResult, OpenSpecContext


class Phase1ParseRequirements(PhaseInterface):
    """Phase 1: 解析需求文档"""

    def __init__(self, context: OpenSpecContext, tool_registry):
        super().__init__(context)
        self.phase_number = 1
        self.phase_name = "解析需求文档"
        self.tool_registry = tool_registry

    def execute(self) -> PhaseResult:
        """执行 Phase 1"""
        self.log("开始解析需求文档...")

        result = self.tool_registry.execute_tool(
            'file_reader',
            {'path': str(self.context.requirements_file)}
        )

        if not result.success:
            self.log(f"[FAIL] {result.error_message}")
            return PhaseResult.fail(
                f"读取需求文档失败: {result.error_message}",
                errors=[result.error_message]
            )

        self.context.requirements_content = result.content
        self.log(f"[OK] 需求文档已读取 ({len(result.content)} 字符)")

        return PhaseResult.ok(
            "需求文档解析成功",
            content_length=len(result.content),
            file_path=str(self.context.requirements_file)
        )
