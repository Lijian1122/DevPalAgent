# -*- coding: utf-8 -*-
"""
OpenSpec 架构核心模块 - DevPal Agent v2.0

包含:
- validation_engine: 四层验证引擎 (Format → Semantic → Parser → Business)
- delta_spec: Delta 增量变更机制 (ADDED/MODIFIED/REMOVED/RENAMED)
- artifact_graph: 工件依赖图 (代码/测试/文档/需求 关联追踪)
- workflow: Schema 声明式工作流 (YAML定义 + 拓扑排序执行)
- requirements: 文件化需求管理 (MD/FrontMatter + 验收标准)
- diagnostic_engine: 智能诊断引擎 (Phase 5)
- config_policy: 配置驱动策略 (Phase 5)
- rollout_engine: 渐进式发布引擎 (Phase 5)
- error_manager: 统一错误处理 (Phase 5)
- languages: 多语言插件系统 (Phase 6)
- compile_db: 编译数据库支持 (Phase 6)
"""

from .validation_engine import ValidationEngine, ValidationResult, ValidationLevel, ValidationSeverity
from .delta_spec import DeltaSpec, DeltaOperation, DeltaResult, DeltaHunk
from .artifact_graph import ArtifactGraph, ArtifactNode, DependencyType, ArtifactType
from .workflow import (
    WorkflowEngine,
    WorkflowSchema,
    WorkflowStepResult,
    WorkflowExecutionSnapshot,
    ExecutionMode,
    StepStatus,
)
from .requirements import RequirementManager, RequirementDocument, RequirementItem, AcceptanceCriteria
from .spec import (
    SpecStatus,
    SpecRequirement,
    SpecDelta,
    SpecSnapshot,
    SpecEngine,
    DeltaType,
    ChangeSeverity,
    SpecArtifactRef,
    SpecContext,
)
from .event_bus import (
    EventBus,
    Event,
    EventFilter,
    EventSubscription,
    EventBusAdapter,
    EventPriority,
    EventScope,
    FileChangedEvent,
    StepExecutedEvent,
    ValidationCompletedEvent,
    ArtifactDiscoveredEvent,
    RequirementChangedEvent,
    DeltaAppliedEvent,
    WorkflowCompletedEvent,
    ImpactAnalysisEvent,
    get_global_event_bus,
    set_global_event_bus,
)

# Phase 5: 深化与体验
from .diagnostic_engine import (
    DiagnosticEngine,
    DiagnosticResult,
    DiagnosticIssue,
    HealthScore,
    DiagnosticSeverity,
    DiagnosticCategory,
)
from .config_policy import (
    PolicyConfig,
    PolicyRule,
    QualityGate,
    ChangeStrategy,
    RolloutStrategy,
    PolicyType,
    EnforcementLevel,
)
from .rollout_engine import (
    RolloutEngine,
    RolloutResult,
    RolloutStatus,
    RolloutType,
    RolloutStage,
    RolloutTarget,
    RolloutMetric,
)
from .error_manager import (
    ErrorManager,
    OpenSpecError,
    ErrorContext,
    ErrorCategory,
    ErrorSeverity,
    RecoveryStrategy,
    RecoveryAction,
)

# Phase 6: 多语言支持
from .languages import (
    LanguagePlugin,
    LanguagePluginManager,
    ASTNode,
    SymbolInfo,
    TypeInfo,
    DependencyInfo,
    FileAnalysisResult,
    CppLanguagePlugin,
)
from .compile_db import (
    CompilationDatabase,
    CompileCommand,
    BuildSystemDetector,
)
from .languages.cpp_rules import (
    CppCodeQualityChecker,
    CPP_RULES,
)

__all__ = [
    # Validation Engine
    'ValidationEngine',
    'ValidationResult',
    'ValidationLevel',
    'ValidationSeverity',

    # Delta Spec
    'DeltaSpec',
    'DeltaOperation',
    'DeltaResult',
    'DeltaHunk',

    # Artifact Graph
    'ArtifactGraph',
    'ArtifactNode',
    'DependencyType',
    'ArtifactType',

    # Workflow Engine
    'WorkflowEngine',
    'WorkflowSchema',
    'WorkflowStepResult',
    'WorkflowExecutionSnapshot',
    'ExecutionMode',
    'StepStatus',

    # Requirements Management
    'RequirementManager',
    'RequirementDocument',
    'RequirementItem',
    'AcceptanceCriteria',

    # Spec-First Core (Phase 1)
    'SpecStatus',
    'SpecRequirement',
    'SpecDelta',
    'SpecSnapshot',
    'SpecEngine',
    'DeltaType',
    'ChangeSeverity',
    'SpecArtifactRef',

    # Unified Context
    'SpecContext',

    # Event Bus (Phase 3)
    'EventBus',
    'Event',
    'EventFilter',
    'EventSubscription',
    'EventBusAdapter',
    'EventPriority',
    'EventScope',
    'FileChangedEvent',
    'StepExecutedEvent',
    'ValidationCompletedEvent',
    'ArtifactDiscoveredEvent',
    'RequirementChangedEvent',
    'DeltaAppliedEvent',
    'WorkflowCompletedEvent',
    'ImpactAnalysisEvent',
    'get_global_event_bus',
    'set_global_event_bus',

    # Phase 5: 智能诊断引擎
    'DiagnosticEngine',
    'DiagnosticResult',
    'DiagnosticIssue',
    'HealthScore',
    'DiagnosticSeverity',
    'DiagnosticCategory',

    # Phase 5: 配置驱动策略
    'PolicyConfig',
    'PolicyRule',
    'QualityGate',
    'ChangeStrategy',
    'RolloutStrategy',
    'PolicyType',
    'EnforcementLevel',

    # Phase 5: 渐进式发布引擎
    'RolloutEngine',
    'RolloutResult',
    'RolloutStatus',
    'RolloutType',
    'RolloutStage',
    'RolloutTarget',
    'RolloutMetric',

    # Phase 5: 统一错误处理
    'ErrorManager',
    'OpenSpecError',
    'ErrorContext',
    'ErrorCategory',
    'ErrorSeverity',
    'RecoveryStrategy',
    'RecoveryAction',

    # Phase 6: 语言插件系统
    'LanguagePlugin',
    'LanguagePluginManager',
    'ASTNode',
    'SymbolInfo',
    'TypeInfo',
    'DependencyInfo',
    'FileAnalysisResult',
    'CppLanguagePlugin',

    # Phase 6: 编译数据库支持
    'CompilationDatabase',
    'CompileCommand',
    'BuildSystemDetector',

    # Phase 6: C/C++ 代码质量检查
    'CppCodeQualityChecker',
    'CPP_RULES',
]
