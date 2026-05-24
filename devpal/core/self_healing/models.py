"""
Self-Healing 核心数据模型
定义错误上下文、根因分析、修复策略和历史记录的数据结构。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional


class ErrorType(Enum):
    """错误类型"""

    SYNTAX = "syntax"  # 语法错误（编译错误、import 错误）
    LOGIC = "logic"  # 逻辑错误（测试失败、断言错误）
    ENVIRONMENT = "environment"  # 环境错误（依赖缺失、配置错误）
    UNKNOWN = "unknown"  # 未知错误


class ErrorSeverity(Enum):
    """错误严重程度"""

    CRITICAL = "critical"  # 阻塞性错误（编译失败）
    HIGH = "high"  # 高优先级（多个测试失败）
    MEDIUM = "medium"  # 中优先级（单个测试失败）
    LOW = "low"  # 低优先级（警告）


class StrategyType(Enum):
    """修复策略类型"""

    REGENERATE_CODE = "regenerate_code"  # 重新生成代码
    FIX_SYNTAX = "fix_syntax"  # 修复语法错误
    UPDATE_TEST = "update_test"  # 更新测试用例
    INSTALL_DEPENDENCY = "install_dependency"  # 安装依赖
    FIX_CONFIGURATION = "fix_configuration"  # 修复配置
    MANUAL_INTERVENTION = "manual_intervention"  # 需要人工介入


# 根因类型定义
ROOT_CAUSE_TYPES = {
    "code_generation_error": "代码生成错误（LLM 生成的代码有问题）",
    "requirement_misunderstanding": "需求理解错误（需求解析不正确）",
    "prompt_issue": "Prompt 问题（Prompt 不够清晰或有误）",
    "dependency_missing": "依赖缺失（缺少必要的库或工具）",
    "configuration_error": "配置错误（环境配置不正确）",
    "test_case_error": "测试用例错误（测试本身有问题）",
    "integration_error": "集成错误（多个模块集成问题）",
    "unknown": "未知根因",
}


@dataclass
class ErrorContext:
    """错误上下文"""

    error_message: str  # 错误消息
    error_type: ErrorType  # 错误类型
    severity: ErrorSeverity  # 严重程度
    file_path: Optional[Path] = None  # 错误文件路径
    line_number: Optional[int] = None  # 错误行号
    stack_trace: str = ""  # 堆栈跟踪
    phase: Optional[str] = None  # 发生错误的 Phase
    timestamp: str = ""  # 错误时间戳
    metadata: Dict = field(default_factory=dict)  # 额外元数据


@dataclass
class TraceNode:
    """追溯链路节点"""

    node_type: str  # 节点类型：requirement/prompt/phase/code/test
    node_id: str  # 节点 ID
    content: str  # 节点内容摘要
    confidence: float  # 置信度 0.0-1.0


@dataclass
class RootCause:
    """根因分析结果"""

    error_context: ErrorContext  # 错误上下文
    root_cause_type: str  # 根因类型
    root_cause_description: str  # 根因描述
    trace_chain: List[TraceNode] = field(default_factory=list)  # 追溯链路
    affected_files: List[Path] = field(default_factory=list)  # 影响的文件
    confidence: float = 0.0  # 根因分析置信度
    suggested_fixes: List[str] = field(default_factory=list)  # 建议修复方案
    metadata: Dict = field(default_factory=dict)  # 元数据


@dataclass
class HealingStrategy:
    """修复策略"""

    strategy_type: StrategyType  # 策略类型
    description: str  # 策略描述
    confidence: float  # 策略置信度 0.0-1.0
    estimated_time: float  # 预计修复时间（秒）
    root_cause: RootCause  # 关联的根因
    fix_function: Optional[Callable] = None  # 修复函数
    parameters: Dict = field(default_factory=dict)  # 修复参数
    metadata: Dict = field(default_factory=dict)  # 元数据


@dataclass
class HealingRecord:
    """修复历史记录"""

    record_id: str  # 记录 ID
    error_context: ErrorContext  # 错误上下文
    root_cause: RootCause  # 根因分析
    strategy: HealingStrategy  # 修复策略
    success: bool  # 是否成功
    execution_time: float  # 执行时间（秒）
    timestamp: datetime = field(default_factory=datetime.now)  # 时间戳
    retry_count: int = 0  # 重试次数
    final_error: Optional[str] = None  # 最终错误（如果失败）
    metadata: Dict = field(default_factory=dict)  # 元数据
