# -*- coding: utf-8 -*-
"""
DevPal Agent 核心引擎
阶段3：完整 Plan-Act-Reflect 架构
+ OpenSpec Architecture (v2.0): 验证引擎, Delta变更, 工件图, 工作流, 需求管理
+ Phase 4: OpenSpecContext - 闭环集成上下文
"""
from .agent_engine import AgentEngine, AgentConfig
from .planner import Planner, Plan, PlanStep
from .reflector import Reflector, Reflection

# Export OpenSpec schema components
try:
    from devpal.core.schema.validation_engine import ValidationEngine, ValidationResult
    from devpal.core.schema.delta_spec import DeltaSpec, DeltaOperation, DeltaResult
    from devpal.core.schema.artifact_graph import ArtifactGraph, ArtifactNode, DependencyType
    from devpal.core.schema.workflow import WorkflowEngine, WorkflowSchema, WorkflowStepResult
    from devpal.core.schema.requirements import RequirementManager, RequirementDocument
    from .openspec_context import OpenSpecContext, OpenSpecConfig

    __all__ = [
        "AgentEngine",
        "AgentConfig",
        "Planner",
        "Plan",
        "PlanStep",
        "Reflector",
        "Reflection",
        "ValidationEngine",
        "ValidationResult",
        "DeltaSpec",
        "DeltaOperation",
        "DeltaResult",
        "ArtifactGraph",
        "ArtifactNode",
        "DependencyType",
        "WorkflowEngine",
        "WorkflowSchema",
        "WorkflowStepResult",
        "RequirementManager",
        "RequirementDocument",
        "OpenSpecContext",  # Phase 4: 统一上下文
        "OpenSpecConfig",   # Phase 4: 上下文配置
    ]
except ImportError as e:
    # Fallback if schema module is not available
    __all__ = [
        "AgentEngine",
        "AgentConfig",
        "Planner",
        "Plan",
        "PlanStep",
        "Reflector",
        "Reflection",
    ]
