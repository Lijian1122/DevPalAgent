"""
Self-Healing 根因分析模块

提供智能错误分析、修复策略选择和历史学习能力。
"""

from .models import (
    ErrorType,
    ErrorSeverity,
    ErrorContext,
    TraceNode,
    RootCause,
    StrategyType,
    HealingStrategy,
    HealingRecord,
    ROOT_CAUSE_TYPES
)

from .root_cause_analyzer import RootCauseAnalyzer
from .strategy_selector import HealingStrategySelector
from .healing_history import HealingHistory
from .report_generator import RootCauseReportGenerator

__all__ = [
    # Enums
    "ErrorType",
    "ErrorSeverity",
    "StrategyType",

    # Data Models
    "ErrorContext",
    "TraceNode",
    "RootCause",
    "HealingStrategy",
    "HealingRecord",

    # Constants
    "ROOT_CAUSE_TYPES",

    # Core Classes
    "RootCauseAnalyzer",
    "HealingStrategySelector",
    "HealingHistory",
    "RootCauseReportGenerator",
]
