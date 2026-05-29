"""
增强的测试自愈器

集成根因分析、策略选择和历史学习功能。
"""

import hashlib
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from ..llm_client import LLMClient
from ..self_healing import (
    ErrorContext,
    ErrorSeverity,
    ErrorType,
    HealingHistory,
    HealingRecord,
    HealingStrategySelector,
    RootCauseAnalyzer,
    StrategyType,
)
from .test_self_healer import TestSelfHealer

if TYPE_CHECKING:
    from .base import OpenSpecContext
    from ..schema.artifact_graph import ArtifactGraph


class EnhancedTestSelfHealer(TestSelfHealer):
    """增强的测试自愈器，集成根因分析"""

    def __init__(
        self,
        project_dir: Path,
        llm_client: LLMClient,
        context: "OpenSpecContext",
        artifact_graph: "ArtifactGraph",
        logger=None,
        fallback_model: str = "claude-opus-4-7",
    ):
        super().__init__(project_dir, llm_client, logger, fallback_model, context=context)

        self.context = context
        self.artifact_graph = artifact_graph

        # 初始化根因分析组件
        self.root_cause_analyzer = RootCauseAnalyzer(
            artifact_graph=artifact_graph,
            context=context,
            logger=logging.getLogger(__name__),
        )

        # 初始化修复历史 - 使用全局路径，按语言分类
        # 这样可以跨项目学习，不同语言的项目共享学习经验
        language = getattr(context, 'language', 'unknown')
        global_history_path = Path.home() / ".devpal" / "healing_history" / language
        self.healing_history = HealingHistory(
            storage_path=global_history_path, logger=logging.getLogger(__name__)
        )

        # 初始化策略选择器
        self.strategy_selector = HealingStrategySelector(
            healing_history=self.healing_history, logger=logging.getLogger(__name__)
        )

        # 最大重试次数
        self.max_retries = 3

    def heal_compile_error_enhanced(
        self, test_file: Path, error_output: str, use_fallback: bool = False
    ) -> bool:
        """
        增强的编译错误修复（集成根因分析）

        Args:
            test_file: 测试文件路径
            error_output: 错误输出
            use_fallback: 是否使用备用模型

        Returns:
            bool: 是否修复成功
        """
        self.log("[Healing] 开始智能修复（集成根因分析）")

        # Step 1: 构建错误上下文
        error_context = self._build_error_context(error_output, "compile", test_file)

        # Step 2: 根因分析
        root_cause = self.root_cause_analyzer.analyze(error_context)
        self._log_root_cause(root_cause)

        # Step 3: 选择修复策略
        strategies = self.strategy_selector.select_strategy(root_cause)

        if not strategies:
            self.log("[Healing] 未找到合适的修复策略，回退到传统方法")
            return super().heal_compile_error(test_file, error_output, use_fallback)

        # Step 4: 依次尝试策略
        for i, strategy in enumerate(strategies[: self.max_retries]):
            self.log(
                f"[Healing] 尝试策略 {i + 1}/{len(strategies)}: "
                f"{strategy.strategy_type.value} (置信度: {strategy.confidence:.2f})"
            )

            start_time = datetime.now()
            success = self._execute_strategy(
                strategy, test_file, error_output, use_fallback
            )
            execution_time = (datetime.now() - start_time).total_seconds()

            # 记录修复历史
            record = HealingRecord(
                record_id=self._generate_record_id(error_context),
                error_context=error_context,
                root_cause=root_cause,
                strategy=strategy,
                success=success,
                execution_time=execution_time,
                retry_count=i,
            )
            self.healing_history.add_record(record)

        if success:
            self.log(f"[Healing] 修复成功 (耗时: {execution_time:.2f}s)")
            self.heal_success += 1
            return True

        self.log("[Healing] 所有策略均失败")
        return False

    def _build_error_context(
        self, error_output: str, error_type_str: str, file_path: Optional[Path] = None
    ) -> ErrorContext:
        """构建错误上下文"""
        # 解析错误位置
        parsed_file, line_number = self._parse_error_location(error_output)
        if not file_path and parsed_file:
            file_path = parsed_file

        # 确定严重程度
        severity = (
            ErrorSeverity.CRITICAL
            if error_type_str == "compile"
            else ErrorSeverity.HIGH
        )

        return ErrorContext(
            error_message=error_output[:500],  # 截取前500字符
            error_type=ErrorType.UNKNOWN,  # 将由分析器分类
            severity=severity,
            file_path=file_path,
            line_number=line_number,
            stack_trace=error_output,
            phase="Phase 10: Test Execution",
            timestamp=datetime.now().isoformat(),
        )

    def _execute_strategy(
        self, strategy, test_file: Path, error_output: str, use_fallback: bool
    ) -> bool:
        """执行修复策略"""
        try:
            if strategy.strategy_type == StrategyType.REGENERATE_CODE:
                return self._regenerate_code(
                    strategy, test_file, error_output, use_fallback
                )
            elif strategy.strategy_type == StrategyType.FIX_SYNTAX:
                return self._fix_syntax(strategy, test_file, error_output, use_fallback)
            elif strategy.strategy_type == StrategyType.INSTALL_DEPENDENCY:
                self.log("[Healing] 依赖安装策略暂未实现")
                return False
            else:
                self.log(f"[Healing] 未实现的策略: {strategy.strategy_type}")
                return False
        except Exception as e:
            self.log(f"[Healing] 策略执行失败: {e}")
            return False

    def _regenerate_code(
        self, strategy, test_file: Path, error_output: str, use_fallback: bool
    ) -> bool:
        """重新生成代码（使用原有的修复逻辑）"""
        return super().heal_compile_error(test_file, error_output, use_fallback)

    def _fix_syntax(
        self, strategy, test_file: Path, error_output: str, use_fallback: bool
    ) -> bool:
        """修复语法错误（使用原有的修复逻辑）"""
        return super().heal_compile_error(test_file, error_output, use_fallback)

    def _parse_error_location(self, error_output: str):
        """解析错误位置"""
        # 匹配常见的错误位置格式
        patterns = [
            r"([^\s:]+):(\d+):",  # file.cpp:42:
            r'File "([^"]+)", line (\d+)',  # Python
        ]

        for pattern in patterns:
            match = re.search(pattern, error_output)
            if match:
                file_path = Path(match.group(1))
                line_number = int(match.group(2))
                return file_path, line_number

        return None, None

    def _log_root_cause(self, root_cause) -> None:
        """记录根因分析结果"""
        self.log("[RCA] ===== 根因分析结果 =====")
        self.log(f"[RCA] 根因类型: {root_cause.root_cause_type}")
        self.log(f"[RCA] 根因描述: {root_cause.root_cause_description}")
        self.log(f"[RCA] 置信度: {root_cause.confidence:.2f}")

        if root_cause.trace_chain:
            self.log("[RCA] 追溯链路:")
            for node in root_cause.trace_chain:
                self.log(f"[RCA]   - {node.node_type}: {node.content}")

        if root_cause.suggested_fixes:
            self.log("[RCA] 建议修复:")
            for fix in root_cause.suggested_fixes:
                self.log(f"[RCA]   - {fix}")

    def _generate_record_id(self, error_context: ErrorContext) -> str:
        """生成记录 ID"""
        content = f"{error_context.error_message}{error_context.timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def get_healing_statistics(self):
        """获取修复统计信息"""
        stats = self.healing_history.get_statistics()
        stats["heal_attempts"] = self.heal_attempts
        stats["heal_success"] = self.heal_success
        stats["model_switches"] = self.model_switches
        return stats
