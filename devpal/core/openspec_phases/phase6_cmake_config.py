# -*- coding: utf-8 -*-
"""
Phase 6: 生成 CMakeLists.txt 配置

已重构为：标记配置生成完成（Phase4 通用模板系统已生成 CMakeLists.txt）
保持 phase 存在是为了兼容现有流水线架构
"""

from pathlib import Path
from .base import PhaseInterface, PhaseResult, OpenSpecContext


class Phase6CMakeConfig(PhaseInterface):
    """Phase 6: 生成 CMakeLists.txt 配置 - 已重构使用通用模板系统"""

    def __init__(self, context: OpenSpecContext, tool_registry):
        super().__init__(context)
        self.phase_number = 6
        self.phase_name = "生成 CMakeLists.txt 配置"
        self.tool_registry = tool_registry

    def execute(self) -> PhaseResult:
        """执行 Phase 6

        注意：CMakeLists.txt 已由 Phase4 通用模板系统生成（cpp_cmake）
        本 phase 仅做验证和状态记录
        """
        self.log("开始生成 CMakeLists.txt (通用模板系统)...")

        cmake_file = self.context.project_dir / 'CMakeLists.txt'

        if cmake_file.exists():
            self.log("  [OK] CMakeLists.txt 已生成")
            return PhaseResult.ok(
                "CMake 配置生成成功",
                file_path=str(cmake_file),
                content_length=cmake_file.stat().st_size
            )
        else:
            self.log("  [WARN] CMakeLists.txt 未生成，可能模板未匹配")
            return PhaseResult.fail(
                "CMake 配置未生成",
                errors=["配置文件未在预期位置找到"]
            )
