"""
根因分析报告生成器

生成详细的根因分析报告，包含错误概览、详细分析和统计信息。
"""

from datetime import datetime
from pathlib import Path
from typing import List

from .healing_history import HealingHistory
from .models import HealingRecord


class RootCauseReportGenerator:
    """根因分析报告生成器"""

    def __init__(self, healing_history: HealingHistory, output_path: Path):
        self.healing_history = healing_history
        self.output_path = output_path

    def generate_report(self, records: List[HealingRecord]) -> Path:
        """生成根因分析报告"""
        report_lines = []

        # 标题和元数据
        report_lines.extend(self._generate_header(records))

        # 错误概览
        report_lines.extend(self._generate_overview(records))

        # 详细分析
        report_lines.extend(self._generate_detailed_analysis(records))

        # 统计分析
        report_lines.extend(self._generate_statistics(records))

        # 建议和改进
        report_lines.extend(self._generate_recommendations(records))

        # 写入文件
        report_path = self.output_path / "root_cause_analysis.md"
        report_path.write_text("\n".join(report_lines), encoding="utf-8")

        return report_path

    def _generate_header(self, records: List[HealingRecord]) -> List[str]:
        """生成报告头部"""
        return [
            "# 根因分析报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**错误总数**: {len(records)}",
            "",
            "---",
            "",
        ]

    def _generate_overview(self, records: List[HealingRecord]) -> List[str]:
        """生成错误概览"""
        lines = [
            "## 1. 错误概览",
            "",
            "| 错误ID | 错误类型 | 严重程度 | 根因类型 | 修复状态 |",
            "|--------|----------|----------|----------|----------|",
        ]

        for record in records:
            status = "✅ 已修复" if record.success else "❌ 修复失败"
            lines.append(
                f"| {record.record_id} | "
                f"{record.error_context.error_type.value} | "
                f"{record.error_context.severity.value} | "
                f"{record.root_cause.root_cause_type} | "
                f"{status} |"
            )

        lines.extend(["", "---", ""])
        return lines

    def _generate_detailed_analysis(self, records: List[HealingRecord]) -> List[str]:
        """生成详细分析"""
        lines = ["## 2. 详细分析", ""]

        for i, record in enumerate(records, 1):
            lines.extend(
                [
                    f"### 2.{i} 错误 #{i}: {record.record_id}",
                    "",
                    f"**错误消息**: {record.error_context.error_message[:100]}...",
                    "",
                    f"**错误分类**: {record.error_context.error_type.value}",
                    "",
                    f"**根因类型**: {record.root_cause.root_cause_type}",
                    "",
                    f"**根因描述**: {record.root_cause.root_cause_description}",
                    "",
                    f"**置信度**: {record.root_cause.confidence:.2f}",
                    "",
                ]
            )

            # 追溯链路
            if record.root_cause.trace_chain:
                lines.append("**追溯链路**:")
            for j, node in enumerate(record.root_cause.trace_chain, 1):
                lines.append(
                    f"{j}. {node.node_type}: {node.node_id} - "
                    f"{node.content} (置信度: {node.confidence:.1f})"
                )
                lines.append("")

            # 修复信息
            status = "✅ 成功" if record.success else "❌ 失败"
            lines.extend(
                [
                    f"**修复策略**: {record.strategy.strategy_type.value}",
                    "",
                    f"**修复描述**: {record.strategy.description}",
                    "",
                    f"**修复结果**: {status} (耗时: {record.execution_time:.1f}s)",
                    "",
                    "---",
                    "",
                ]
            )

        return lines

    def _generate_statistics(self, records: List[HealingRecord]) -> List[str]:
        """生成统计分析"""
        stats = self.healing_history.get_statistics()

        lines = [
            "## 3. 统计分析",
            "",
            "### 3.1 总体统计",
            "",
            f"- 总修复记录: {stats['total_records']}",
            f"- 修复成功率: {stats['success_rate']:.1%}",
            f"- 平均修复时间: {stats['avg_execution_time']:.1f}s",
            "",
            "### 3.2 按错误类型统计",
            "",
            "| 错误类型 | 总数 | 成功数 | 成功率 |",
            "|--------|------|--------|--------|",
        ]

        for error_type, data in stats["by_error_type"].items():
            success_rate = data["success"] / data["total"] if data["total"] > 0 else 0
            lines.append(
                f"| {error_type} | {data['total']} | "
                f"{data['success']} | {success_rate:.1%} |"
            )

        lines.extend(
            [
                "",
                "### 3.3 按策略类型统计",
                "",
                "| 策略类型 | 总数 | 成功数 | 成功率 |",
                "|-------|--------|--------|",
            ]
        )

        for strategy_type, data in stats["by_strategy_type"].items():
            success_rate = data["success"] / data["total"] if data["total"] > 0 else 0
            lines.append(
                f"| {strategy_type} | {data['total']} | "
                f"{data['success']} | {success_rate:.1%} |"
            )

        lines.extend(["", "---", ""])
        return lines

    def _generate_recommendations(self, records: List[HealingRecord]) -> List[str]:
        """生成建议和改进"""
        return [
            "## 4. 建议和改进",
            "",
            "### 4.1 高频错误类型",
            "",
            "基于历史数据分析，建议重点关注以下错误类型的预防。",
            "",
            "### 4.2 策略优化",
            "",
            "建议优化低成功率的修复策略，或增加新的策略类型。",
            "",
            "---",
            "",
            "*报告由 DevPalAgent Self-Healing 系统自动生成*",
        ]
