# -*- coding: utf-8 -*-
"""
OpenSpec Phase 调度器

统一管理 11 个阶段的执行流程。
"""

from pathlib import Path
from typing import Dict, List

from .base import OpenSpecContext, PhaseResult
from .phase1_parse_requirements import Phase1ParseRequirements
from .phase2_create_structure import Phase2CreateStructure
from .phase3_technical_design import Phase3TechnicalDesign
from .phase4_generate_code import Phase4GenerateCode
from .phase5_generate_tests import Phase5GenerateTests
from .phase6_cmake_config import Phase6CMakeConfig
from .phase7_test_docs import Phase7TestDocs
from .phase8_readme import Phase8Readme
from .phase9_code_review import Phase9CodeReview
from .phase10_run_tests import Phase10RunTests
from .phase11_final_report import Phase11FinalReport


class OpenSpecPhaseScheduler:
    """OpenSpec 11 阶段调度器"""

    def __init__(self, requirements_file: str, tool_registry):
        """
        初始化调度器

        Args:
            requirements_file: 需求文档路径
            tool_registry: 工具注册表实例
        """
        self.context = OpenSpecContext(
            project_dir=Path("."),
            requirements_file=Path(requirements_file)
        )
        self.tool_registry = tool_registry

        # 检测编程语言
        content = Path(requirements_file).read_text(encoding='utf-8', errors='ignore')
        self.context.is_cpp = "c++" in content.lower() or "cpp" in content.lower()
        self.context.language = "cpp" if self.context.is_cpp else "python"

    def run_all_phases(self) -> Dict[str, any]:
        """
        执行所有 11 个阶段

        Returns:
            包含执行结果的字典
        """
        print()
        print("=" * 70)
        print("  OpenSpec - Requirements-Driven Development Workflow")
        print("=" * 70)
        print(f"  需求文档: {self.context.requirements_file}")
        print(f"  目标语言: {'C++' if self.context.is_cpp else 'Python'}")
        print("=" * 70)
        print()

        # 11 个阶段按顺序执行
        phases = [
            Phase1ParseRequirements(self.context, self.tool_registry),
            Phase2CreateStructure(self.context, self.tool_registry),
            Phase3TechnicalDesign(self.context),
            Phase4GenerateCode(self.context, self.tool_registry),
            Phase5GenerateTests(self.context, self.tool_registry),
            Phase6CMakeConfig(self.context, self.tool_registry),
            Phase7TestDocs(self.context, self.tool_registry),
            Phase8Readme(self.context, self.tool_registry),
            Phase9CodeReview(self.context, self.tool_registry),
            Phase10RunTests(self.context, self.tool_registry),
            Phase11FinalReport(self.context),
        ]

        for i, phase in enumerate(phases, 1):
            result = phase.execute()
            self.context.set_phase_result(i, result)

            if not result.success and i < 11:
                print(f"\n  ⚠️ Phase {i} 执行存在问题，但继续后续阶段...")

        print()
        print("=" * 70)
        print("  OpenSpec 流程完成!")
        print(f"  项目目录: {self.context.project_dir.absolute()}")
        print(f"  测试结果: {self.context.test_passed}/{self.context.test_total} 通过")
        print("=" * 70)

        return {
            'success': True,
            'project_dir': str(self.context.project_dir),
            'test_passed': self.context.test_passed,
            'test_total': self.context.test_total,
            'phases': self.context.phase_results
        }
