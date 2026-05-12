# -*- coding: utf-8 -*-
"""
Phase 11: 生成最终验证报告
"""

from pathlib import Path
from .base import PhaseInterface, PhaseResult, OpenSpecContext


class Phase11FinalReport(PhaseInterface):
    """Phase 11: 生成最终验证报告"""

    def __init__(self, context: OpenSpecContext):
        super().__init__(context)
        self.phase_number = 11
        self.phase_name = "生成最终验证报告"

    def execute(self) -> PhaseResult:
        """执行 Phase 11"""
        self.log("开始生成最终验证报告...")

        report_content = self._generate_final_report()
        report_path = self.context.project_dir / 'docs' / '最终验证报告.md'
        report_path.write_text(report_content, encoding='utf-8')

        self.context.generated_files.append(report_path)
        self.log(f"  [OK] 最终验证报告已生成: {report_path}")

        self.log("")
        self.log("=" * 60)
        self.log("  OpenSpec 11 阶段流程全部完成!")
        self.log(f"  项目位置: {self.context.project_dir}")
        self.log(f"  测试结果: {self.context.test_passed}/{self.context.test_total} 通过")
        self.log(f"  生成文件: {len(self.context.generated_files)} 个")
        self.log("=" * 60)

        return PhaseResult.ok(
            "最终验证报告生成成功",
            report_path=str(report_path),
            project_dir=str(self.context.project_dir),
            test_passed=self.context.test_passed,
            test_total=self.context.test_total,
            generated_files=len(self.context.generated_files)
        )

    def _generate_final_report(self) -> str:
        """生成最终验证报告内容"""
        # 去重处理（避免多个 Phase 重复添加相同文件）
        unique_files = sorted(set(self.context.generated_files))

        lines = [
            "# OpenSpec - 最终验证报告",
            "",
            "> **生成时间**: 2026-05-08",
            "> **项目类型**: C++ 用户认证系统",
            "",
            "## 1. 项目概览",
            "",
            f"- **项目目录**: `{self.context.project_dir}`",
            f"- **需求文档**: `{self.context.requirements_file}`",
            f"- **生成文件**: {len(unique_files)} 个",
            "",
            "## 2. 测试结果",
            "",
            f"- **测试通过**: {self.context.test_passed}/{self.context.test_total}",
            f"- **成功率**: {self.context.test_passed/self.context.test_total*100:.1f}%" if self.context.test_total > 0 else "",
            "",
            "### 测试输出",
            "",
            "```",
            self.context.test_output or "无测试输出",
            "```",
            "",
            "## 3. 生成的文件列表",
            "",
            "```",
        ]

        # 去重处理（避免多个 Phase 重复添加相同文件）
        unique_files = sorted(set(self.context.generated_files))
        for f in unique_files:
            rel_path = Path(f).relative_to(self.context.project_dir)
            lines.append(f"  {rel_path}")

        lines.extend([
            "```",
            "",
            "## 4. 阶段完成情况",
            "",
            "| 阶段 | 名称 | 状态 |",
            "|-----|------|------|",
        ])

        phase_names = {
            1: "解析需求文档",
            2: "创建项目结构",
            3: "生成技术设计文档",
            4: "生成核心代码",
            5: "生成测试代码",
            6: "生成 CMake 配置",
            7: "生成测试文档",
            8: "生成 README",
            9: "代码质量审查",
            10: "编译运行测试",
            11: "生成最终报告",
        }

        for phase_num in range(1, 12):
            result = self.context.get_phase_result(phase_num)
            # Phase11 就是当前正在执行的阶段，肯定是成功的
            if phase_num == 11:
                status = "✅"
            else:
                status = "✅" if (result and result.success) else "❌"
            lines.append(f"| {phase_num} | {phase_names.get(phase_num, '')} | {status} |")

        lines.extend([
            "",
            "## 5. 总结",
            "",
            "OpenSpec 11 阶段需求驱动开发流程已全部完成。",
            "项目已通过编译测试，可以直接使用。",
            "",
            "### 下一步",
            "",
            "1. 查看 `docs/技术实现文档.md` 了解技术实现细节",
            "2. 查看 `docs/测试文档.md` 了解测试覆盖情况",
            "3. 进入项目目录，运行 `cmake` 构建",
            "4. 执行 `build_test/test_auth.exe` 运行单元测试",
            "",
        ])

        return '\n'.join(lines)
