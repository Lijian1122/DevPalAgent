"""
修复策略选择器

根据根因分析结果选择合适的修复策略，支持历史学习。
"""

import logging
from typing import TYPE_CHECKING, Dict, List, Optional

from .models import HealingStrategy, RootCause, StrategyType

if TYPE_CHECKING:
    from .healing_history import HealingHistory


class HealingStrategySelector:
    """修复策略选择器"""

    def __init__(
        self, healing_history: "HealingHistory", logger: Optional[logging.Logger] = None
    ):
        self.healing_history = healing_history
        self.logger = logger or logging.getLogger(__name__)

        # 策略映射表
        self.strategy_map = self._build_strategy_map()

    def select_strategy(self, root_cause: RootCause) -> List[HealingStrategy]:
        """
        选择修复策略

        Args:
            root_cause: 根因分析结果

        Returns:
          List[HealingStrategy]: 按优先级排序的策略列表
        """
        self.logger.info(f"[Strategy] 选择修复策略: {root_cause.root_cause_type}")

        # Step 1: 从历史中查找相似错误的成功策略
        historical_strategies = self._find_historical_strategies(root_cause)

        # Step 2: 基于根因类型生成默认策略
        default_strategies = self._generate_default_strategies(root_cause)

        # Step 3: 合并并去重
        all_strategies = self._merge_strategies(
            historical_strategies, default_strategies
        )

        # Step 4: 评分和排序
        scored_strategies = self._score_and_sort(all_strategies, root_cause)

        self.logger.info(f"[Strategy] 生成 {len(scored_strategies)} 个策略")
        return scored_strategies

    def _find_historical_strategies(
        self, root_cause: RootCause
    ) -> List[HealingStrategy]:
        """从历史中查找成功策略"""
        strategies = []

        # 查询相似错误的成功修复记录
        similar_records = self.healing_history.find_similar_errors(
            root_cause.error_context, similarity_threshold=0.7
        )

        for record in similar_records:
            if record.success:
                # 复制成功的策略，提高置信度
                strategy = HealingStrategy(
                    strategy_type=record.strategy.strategy_type,
                    description=f"[历史学习] {record.strategy.description}",
                    confidence=min(record.strategy.confidence + 0.1, 1.0),
                    estimated_time=record.execution_time,
                    root_cause=root_cause,
                    parameters=record.strategy.parameters.copy(),
                )
                strategies.append(strategy)

        return strategies

    def _generate_default_strategies(
        self, root_cause: RootCause
    ) -> List[HealingStrategy]:
        """生成默认策略"""
        strategies = []
        root_cause_type = root_cause.root_cause_type

        # 从策略映射表获取
        if root_cause_type in self.strategy_map:
            strategy_configs = self.strategy_map[root_cause_type]

            for config in strategy_configs:
                strategy = HealingStrategy(
                    strategy_type=config["type"],
                    description=config["description"],
                    confidence=config["confidence"],
                    estimated_time=config["estimated_time"],
                    root_cause=root_cause,
                    parameters=self._build_parameters(root_cause, config),
                )
            strategies.append(strategy)

        return strategies

    def _merge_strategies(
        self, historical: List[HealingStrategy], default: List[HealingStrategy]
    ) -> List[HealingStrategy]:
        """合并策略并去重"""
        # 优先使用历史策略
        merged = historical.copy()

        # 添加不重复的默认策略
        existing_types = {s.strategy_type for s in historical}
        for strategy in default:
            if strategy.strategy_type not in existing_types:
                merged.append(strategy)

        return merged

    def _score_and_sort(
        self, strategies: List[HealingStrategy], root_cause: RootCause
    ) -> List[HealingStrategy]:
        """评分和排序"""
        # 综合评分：置信度 * 0.7 + (1 - 归一化时间) * 0.3
        max_time = max((s.estimated_time for s in strategies), default=100.0)

        for strategy in strategies:
            time_score = 1.0 - (strategy.estimated_time / max_time)
        strategy.metadata["score"] = strategy.confidence * 0.7 + time_score * 0.3

        # 按评分降序排序
        strategies.sort(key=lambda s: s.metadata["score"], reverse=True)
        return strategies

    def _build_parameters(self, root_cause: RootCause, config: Dict) -> Dict:
        """构建策略参数"""
        params = config.get("base_parameters", {}).copy()

        # 从根因中提取参数
        if root_cause.error_context.file_path:
            params["file_path"] = str(root_cause.error_context.file_path)

        # 从建议修复中提取参数
        if root_cause.suggested_fixes:
            params["suggested_fixes"] = root_cause.suggested_fixes

        return params

    def _build_strategy_map(self) -> Dict:
        """构建策略映射表"""
        return {
            "code_generation_error": [
                {
                    "type": StrategyType.REGENERATE_CODE,
                    "description": "重新生成代码文件",
                    "confidence": 0.8,
                    "estimated_time": 60.0,
                    "base_parameters": {},
                }
            ],
            "dependency_missing": [
                {
                    "type": StrategyType.INSTALL_DEPENDENCY,
                    "description": "安装缺失的依赖",
                    "confidence": 0.9,
                    "estimated_time": 30.0,
                    "base_parameters": {},
                }
            ],
            "requirement_misunderstanding": [
                {
                    "type": StrategyType.REGENERATE_CODE,
                    "description": "基于更新的需求理解重新生成代码",
                    "confidence": 0.7,
                    "estimated_time": 80.0,
                    "base_parameters": {},
                },
                {
                    "type": StrategyType.UPDATE_TEST,
                    "description": "更新测试用例以匹配实际需求",
                    "confidence": 0.6,
                    "estimated_time": 40.0,
                    "base_parameters": {},
                },
            ],
            "configuration_error": [
                {
                    "type": StrategyType.FIX_CONFIGURATION,
                    "description": "修复环境配置",
                    "confidence": 0.75,
                    "estimated_time": 20.0,
                    "base_parameters": {},
                }
            ],
            "test_case_error": [
                {
                    "type": StrategyType.UPDATE_TEST,
                    "description": "修复测试用例",
                    "confidence": 0.85,
                    "estimated_time": 30.0,
                    "base_parameters": {},
                }
            ],
        }
