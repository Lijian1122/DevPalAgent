# -*- coding: utf-8 -*-
"""
Phase 5: 生成测试代码

已重构为：标记测试生成完成（Phase4 通用模板系统已生成测试文件）
保持 phase 存在是为了兼容现有流水线架构
"""

from pathlib import Path
from .base import PhaseInterface, PhaseResult, OpenSpecContext


class Phase5GenerateTests(PhaseInterface):
    """Phase 5: 生成测试代码 - 已重构使用通用模板系统"""

    def __init__(self, context: OpenSpecContext, tool_registry):
        super().__init__(context)
        self.phase_number = 5
        self.phase_name = "生成测试代码"
        self.tool_registry = tool_registry

    def execute(self) -> PhaseResult:
        """执行 Phase 5

        注意：测试文件已由 Phase4 通用模板系统生成（cpp_auth_test）
        本 phase 仅做验证和状态记录
        """
        self.log("开始生成测试代码 (通用模板系统)...")

        test_file = self.context.project_dir / 'tests' / 'test_auth.cpp'

        if test_file.exists():
            self.log("  [OK] test_auth.cpp 已生成")
            return PhaseResult.ok(
                "测试代码生成成功",
                file_path=str(test_file),
                content_length=test_file.stat().st_size
            )
        else:
            self.log("  [WARN] test_auth.cpp 未生成，可能模板未匹配")
            return PhaseResult.fail(
                "测试代码未生成",
                errors=["测试文件未在预期位置找到"]
            )
