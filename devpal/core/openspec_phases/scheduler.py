# -*- coding: utf-8 -*-
"""
OpenSpec Phase 调度器

统一管理 11 个阶段的执行流程。
"""

from pathlib import Path
from typing import Dict

from .base import OpenSpecContext, PhaseResult
from .logger import OpenSpecLogger
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

    def __init__(self, requirements_file: str, tool_registry, abort_on_critical_failure: bool = True):
        """
        初始化调度器

        Args:
            requirements_file: 需求文档路径
            tool_registry: 工具注册表实例
            abort_on_critical_failure: 关键阶段失败时是否终止流程（默认 True）
        """
        self.context = OpenSpecContext(
            project_dir=Path("."),
            requirements_file=Path(requirements_file),
            abort_on_critical_failure=abort_on_critical_failure
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

        # 创建 11 个阶段
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

        # 标记关键阶段（失败必须终止）
        critical_phases = [1, 3, 4, 10]  # Phase 1, 3, 4, 10
        for i in critical_phases:
            phases[i - 1].is_critical = True

        # 执行各阶段
        for i, phase in enumerate(phases, 1):
            # Phase 2 执行后初始化日志系统
            if i == 2:
                result, duration = phase.execute_with_timing()
                self.context.set_phase_result(i, result)

                if result.success and self.context.project_dir:
                    # 初始化日志系统
                    try:
                        self.context.logger = OpenSpecLogger(
                            self.context.project_name,
                            self.context.project_dir
                        )
                        self.context.log_file = self.context.logger.log_file
                        print(f"[INFO] 日志文件: {self.context.log_file}")
                    except Exception as exc:
                        print(f"[WARN] 日志系统初始化失败: {exc}")
                continue

            # 记录阶段开始
            if self.context.logger:
                self.context.logger.phase_start(i, phase.phase_name)

            # 执行阶段
            result, duration = phase.execute_with_timing()
            self.context.set_phase_result(i, result)

            # 记录阶段结束
            if self.context.logger:
                self.context.logger.phase_end(i, result.success, duration)

            # 检查是否需要终止
            if not result.success:
                if phase.is_critical and self.context.abort_on_critical_failure:
                    # 关键阶段失败，终止流程
                    error_msg = f"关键阶段 Phase {i} ({phase.phase_name}) 失败，终止流程"
                    if self.context.logger:
                        self.context.logger.critical(error_msg)
                        self.context.logger.error(f"失败原因: {result.message}")
                        if result.errors:
                            for error in result.errors:
                                self.context.logger.error(f"  - {error}")
                    else:
                        print(f"\n[CRITICAL] {error_msg}")
                        print(f"失败原因: {result.message}")

                    return {
                        'success': False,
                        'failed_phase': i,
                        'failed_phase_name': phase.phase_name,
                        'error_message': result.message,
                        'errors': result.errors,
                        'project_dir': str(self.context.project_dir),
                        'log_file': str(self.context.log_file) if self.context.log_file else None,
                        'phases': self.context.phase_results
                    }
                else:
                    # 非关键阶段失败，继续执行
                    warning_msg = f"Phase {i} 执行存在问题，但继续后续阶段..."
                    if self.context.logger:
                        self.context.logger.warning(warning_msg)
                    else:
                        print(f"\n[WARNING] {warning_msg}")

        # 所有阶段完成
        if self.context.logger:
            self.context.logger.info("")
            self.context.logger.info("=" * 70)
            self.context.logger.info("OpenSpec 流程完成!")
            self.context.logger.info(f"项目目录: {self.context.project_dir.absolute()}")
            self.context.logger.info(f"测试结果: {self.context.test_passed}/{self.context.test_total} 通过")
            self.context.logger.info(f"日志文件: {self.context.log_file}")
            self.context.logger.info("=" * 70)

        print()
        print("=" * 70)
        print("  OpenSpec 流程完成!")
        print(f"  项目目录: {self.context.project_dir.absolute()}")
        print(f"  测试结果: {self.context.test_passed}/{self.context.test_total} 通过")
        if self.context.log_file:
            print(f"  日志文件: {self.context.log_file}")
        print("=" * 70)

        return {
            'success': True,
            'project_dir': str(self.context.project_dir),
            'test_passed': self.context.test_passed,
            'test_total': self.context.test_total,
            'log_file': str(self.context.log_file) if self.context.log_file else None,
            'phases': self.context.phase_results
        }
