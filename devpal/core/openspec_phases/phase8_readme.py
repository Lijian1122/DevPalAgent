# -*- coding: utf-8 -*-
"""
Phase 8: 生成 README 文档

已重构为：标记文档生成完成（Phase4 通用模板系统已生成 README.md）
保持 phase 存在是为了兼容现有流水线架构
"""

from pathlib import Path
from .base import PhaseInterface, PhaseResult, OpenSpecContext


class Phase8Readme(PhaseInterface):
    """Phase 8: 生成 README 文档 - 已重构使用通用模板系统"""

    def __init__(self, context: OpenSpecContext, tool_registry):
        super().__init__(context)
        self.phase_number = 8
        self.phase_name = "生成 README 文档"
        self.tool_registry = tool_registry

    def execute(self) -> PhaseResult:
        """执行 Phase 8

        注意：README.md 已由 Phase4 通用模板系统生成（cpp_readme）
        本 phase 仅做验证和状态记录
        """
        self.log("开始生成 README 文档 (通用模板系统)...")

        readme_file = self.context.project_dir / 'README.md'

        if readme_file.exists():
            self.log("  [OK] README 文档已生成")
            return PhaseResult.ok(
                "README 文档生成成功",
                file_path=str(readme_file),
                content_length=readme_file.stat().st_size
            )
        else:
            self.log("  [WARN] README.md 未生成，可能模板未匹配")
            return PhaseResult.fail(
                "README 文档未生成",
                errors=["文档未在预期位置找到"]
            )
