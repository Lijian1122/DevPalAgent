# -*- coding: utf-8 -*-
"""
OpenSpec 工作流事件定义

扩展 EventBus 以支持 OpenSpec 11 阶段工作流的全链路事件追踪
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .event_bus import Event


class WorkflowEventType(Enum):
    """工作流事件类型"""

    # 工作流级别
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    WORKFLOW_RESUMED = "workflow.resumed"

    # 阶段级别
    PHASE_STARTED = "phase.started"
    PHASE_EXECUTING = "phase.executing"
    PHASE_COMPLETED = "phase.completed"
    PHASE_FAILED = "phase.failed"
    PHASE_SKIPPED = "phase.skipped"

    # 工具级别
    TOOL_CALLED = "tool.called"
    TOOL_STARTED = "tool.started"
    TOOL_COMPLETED = "tool.completed"
    TOOL_FAILED = "tool.failed"

    # 验证级别
    VALIDATION_STARTED = "validation.started"
    VALIDATION_COMPLETED = "validation.completed"
    VALIDATION_ISSUE_FOUND = "validation.issue_found"

    # Checkpoint 级别
    CHECKPOINT_CREATED = "checkpoint.created"
    CHECKPOINT_LOADED = "checkpoint.loaded"

    # 文件级别
    FILE_GENERATED = "file.generated"
    FILE_MODIFIED = "file.modified"
    FILE_DELETED = "file.deleted"

    # LLM 级别
    LLM_REQUEST_STARTED = "llm.request_started"
    LLM_REQUEST_COMPLETED = "llm.request_completed"
    LLM_CACHE_HIT = "llm.cache_hit"
    LLM_CACHE_MISS = "llm.cache_miss"


# ============================
# 工作流级别事件
# ============================


@dataclass
class WorkflowStartedEvent(Event):
    """工作流开始事件"""

    workflow_id: str = ""
    requirements_file: str = ""
    project_name: str = ""
    language: str = ""
    project_type: str = ""

    def __post_init__(self):
        self.event_type = WorkflowEventType.WORKFLOW_STARTED.value
        if not self.source:
            self.source = "scheduler"


@dataclass
class WorkflowCompletedEvent(Event):
    """工作流完成事件"""

    workflow_id: str = ""
    success: bool = True
    total_duration_ms: int = 0
    phases_completed: int = 0
    phases_failed: int = 0
    phases_skipped: int = 0
    statistics: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.event_type = WorkflowEventType.WORKFLOW_COMPLETED.value
        if not self.source:
            self.source = "scheduler"


@dataclass
class WorkflowFailedEvent(Event):
    """工作流失败事件"""

    workflow_id: str = ""
    error: str = ""
    failed_phase: Optional[int] = None
    stack_trace: Optional[str] = None

    def __post_init__(self):
        self.event_type = WorkflowEventType.WORKFLOW_FAILED.value
        if not self.source:
            self.source = "scheduler"


@dataclass
class WorkflowResumedEvent(Event):
    """工作流恢复事件"""

    workflow_id: str = ""
    checkpoint_file: str = ""
    resume_from_phase: int = 0

    def __post_init__(self):
        self.event_type = WorkflowEventType.WORKFLOW_RESUMED.value
        if not self.source:
            self.source = "scheduler"


# =================================
# 阶段级别事件
# =====================================


@dataclass
class PhaseStartedEvent(Event):
    """阶段开始事件"""

    workflow_id: str = ""
    phase_num: int = 0
    phase_name: str = ""
    estimated_duration_seconds: Optional[int] = None

    def __post_init__(self):
        self.event_type = WorkflowEventType.PHASE_STARTED.value
        if not self.source:
            self.source = f"phase{self.phase_num}"


@dataclass
class PhaseExecutingEvent(Event):
    """阶段执行中事件"""

    workflow_id: str = ""
    phase_num: int = 0
    phase_name: str = ""
    progress_percent: float = 0.0
    current_step: str = ""

    def __post_init__(self):
        self.event_type = WorkflowEventType.PHASE_EXECUTING.value
        if not self.source:
            self.source = f"phase{self.phase_num}"


@dataclass
class PhaseCompletedEvent(Event):
    """阶段完成事件"""

    workflow_id: str = ""
    phase_num: int = 0
    phase_name: str = ""
    success: bool = True
    duration_ms: int = 0
    result_summary: str = ""
    artifacts: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.event_type = WorkflowEventType.PHASE_COMPLETED.value
        if not self.source:
            self.source = f"phase{self.phase_num}"


@dataclass
class PhaseFailedEvent(Event):
    """阶段失败事件"""

    workflow_id: str = ""
    phase_num: int = 0
    phase_name: str = ""
    error: str = ""
    stack_trace: Optional[str] = None

    def __post_init__(self):
        self.event_type = WorkflowEventType.PHASE_FAILED.value
        if not self.source:
            self.source = f"phase{self.phase_num}"


@dataclass
class PhaseSkippedEvent(Event):
    """阶段跳过事件"""

    workflow_id: str = ""
    phase_num: int = 0
    phase_name: str = ""
    skip_reason: str = ""

    def __post_init__(self):
        self.event_type = WorkflowEventType.PHASE_SKIPPED.value
        if not self.source:
            self.source = f"phase{self.phase_num}"


# ====================================
# 工具级别事件
# ===============================


@dataclass
class ToolCalledEvent(Event):
    """工具调用事件"""

    workflow_id: str = ""
    tool_name: str = ""
    tool_params: Dict[str, Any] = field(default_factory=dict)
    caller: str = "# 调用者（phase4/phase9/etc"

    def __post_init__(self):
        self.event_type = WorkflowEventType.TOOL_CALLED.value
        if not self.source:
            self.source = self.caller


@dataclass
class ToolStartedEvent(Event):
    """工具开始执行事件"""

    workflow_id: str = ""
    tool_name: str = ""

    def __post_init__(self):
        self.event_type = WorkflowEventType.TOOL_STARTED.value


@dataclass
class ToolCompletedEvent(Event):
    """工具完成事件"""

    workflow_id: str = ""
    tool_name: str = ""
    success: bool = True
    duration_ms: int = 0
    result_summary: str = ""

    def __post_init__(self):
        self.event_type = WorkflowEventType.TOOL_COMPLETED.value


@dataclass
class ToolFailedEvent(Event):
    """工具失败事件"""

    workflow_id: str = ""
    tool_name: str = ""
    error: str = ""

    def __post_init__(self):
        self.event_type = WorkflowEventType.TOOL_FAILED.value


# ===========================
# 验证级别事件
# ================


@dataclass
class ValidationStartedEvent(Event):
    """验证开始事件"""

    workflow_id: str = ""
    phase_num: int = 9
    validation_layers: List[str] = field(default_factory=list)
    files_to_validate: int = 0

    def __post_init__(self):
        self.event_type = WorkflowEventType.VALIDATION_STARTED.value
        if not self.source:
            self.source = "phase9"


@dataclass
class ValidationCompletedEvent(Event):
    """验证完成事件"""

    workflow_id: str = ""
    phase_num: int = 9
    total_issues: int = 0
    issues_by_layer: Dict[str, int] = field(default_factory=dict)
    passed: bool = True

    def __post_init__(self):
        self.event_type = WorkflowEventType.VALIDATION_COMPLETED.value
        if not self.source:
            self.source = "phase9"


@dataclass
class ValidationIssueFoundEvent(Event):
    """验证问题发现事件"""

    workflow_id: str = ""
    phase_num: int = 9
    layer: str = ""  # FORMAT/SEMANTIC/PARSER/BUSINESS
    severity: str = ""  # error/warning/info
    file_path: str = ""
    line_number: Optional[int] = None
    message: str = ""

    def __post_init__(self):
        self.event_type = WorkflowEventType.VALIDATION_ISSUE_FOUND.value
        if not self.source:
            self.source = "phase9"


# ====================================
# Checkpoint 级别事件
# ================


@dataclass
class CheckpointCreatedEvent(Event):
    """Checkpoint 创建事件"""

    workflow_id: str = ""
    checkpoint_file: str = ""
    phase_num: int = 0

    def __post_init__(self):
        self.event_type = WorkflowEventType.CHECKPOINT_CREATED.value
        if not self.source:
            self.source = "scheduler"


@dataclass
class CheckpointLoadedEvent(Event):
    """Checkpoint 加载事件"""

    workflow_id: str = ""
    checkpoint_file: str = ""
    resume_from_phase: int = 0

    def __post_init__(self):
        self.event_type = WorkflowEventType.CHECKPOINT_LOADED.value
        if not self.source:
            self.source = "scheduler"


# ================================
# 文件级别事件
# ===================================


@dataclass
class FileGeneratedEvent(Event):
    """文件生成事件"""

    workflow_id: str = ""
    phase_num: int = 0
    file_path: str = ""
    file_type: str = ""  # source/test/doc/config
    lines_of_code: int = 0
    language: str = ""
    generated_by: str = ""  # phase4/template/tool

    def __post_init__(self):
        self.event_type = WorkflowEventType.FILE_GENERATED.value
        if not self.source:
            self.source = self.generated_by


@dataclass
class FileModifiedEvent(Event):
    """文件修改事件"""

    workflow_id: str = ""
    phase_num: int = 0
    file_path: str = ""
    modified_by: str = ""

    def __post_init__(self):
        self.event_type = WorkflowEventType.FILE_MODIFIED.value
        if not self.source:
            self.source = self.modified_by


@dataclass
class FileDeletedEvent(Event):
    """文件删除事件"""

    workflow_id: str = ""
    phase_num: int = 0
    file_path: str = ""
    deleted_by: str = ""

    def __post_init__(self):
        self.event_type = WorkflowEventType.FILE_DELETED.value
        if not self.source:
            self.source = self.deleted_by


# ===================================
# LLM 级别事件
# =====================================


@dataclass
class LLMRequestStartedEvent(Event):
    """LLM 请求开始事件"""

    workflow_id: str = ""
    model: str = ""
    prompt_length: int = 0

    def __post_init__(self):
        self.event_type = WorkflowEventType.LLM_REQUEST_STARTED.value
        if not self.source:
            self.source = "llm_client"


@dataclass
class LLMRequestCompletedEvent(Event):
    """LLM 请求完成事件"""

    workflow_id: str = ""
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    duration_ms: int = 0
    cache_hit: bool = False
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0

    def __post_init__(self):
        self.event_type = WorkflowEventType.LLM_REQUEST_COMPLETED.value
        if not self.source:
            self.source = "llm_client"


@dataclass
class LLMCacheHitEvent(Event):
    """LLM 缓存命中事件"""

    workflow_id: str = ""
    model: str = ""
    cache_read_tokens: int = 0

    def __post_init__(self):
        self.event_type = WorkflowEventType.LLM_CACHE_HIT.value
        if not self.source:
            self.source = "llm_client"


@dataclass
class LLMCacheMissEvent(Event):
    """LLM 缓存未命中事件"""

    workflow_id: str = ""
    model: str = ""

    def __post_init__(self):
        self.event_type = WorkflowEventType.LLM_CACHE_MISS.value
        if not self.source:
            self.source = "llm_client"
