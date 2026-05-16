# -*- coding: utf-8 -*-
"""Phase 7: 测试文档（已合并到 Phase 5）

Phase 5 已承担测试文档生成职责。
本 Phase 保留为 no-op 以维持 11 阶段流水线结构。
"""

from .base import PhaseInterface, PhaseResult, OpenSpecContext


class Phase7TestDocs(PhaseInterface):
    """Phase 7: 测试文档（no-op，功能已合并到 Phase 5）"""

    def __init__(self, context: OpenSpecContext, tool_registry):
        super().__init__(context)
        self.phase_number = 7
        self.phase_name = "Test docs (merged into Phase 5)"
        self.tool_registry = tool_registry

    def execute(self) -> PhaseResult:
        self.log("Phase 7: test documentation already generated in Phase 5, skipping.")
        return PhaseResult.ok(
            "Phase 7 skipped (merged into Phase 5)",
            skipped=True,
      )
