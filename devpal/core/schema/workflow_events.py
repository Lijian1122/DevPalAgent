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

    # Phase 内部任务级别
    FILE_TASK_STARTED = "file_task.started"
    FILE_TASK_COMPLETED = "file_task.completed"
    FILE_TASK_FAILED = "file_task.failed"
    FILE_TASK_RETRYING = "file_task.retrying"
    PHASE_PARALLEL_SUMMARY = "phase.parallel_summary"

    # Multi-agent / sandbox 级别
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_MERGE_COMPLETED = "agent.merge_completed"
    AGENT_FALLBACK_USED = "agent.fallback_used"
    SANDBOX_VIOLATION = "sandbox.violation"

    # 向量检索级别
    VECTOR_INDEX_STARTED = "vector.index_started"
    VECTOR_INDEX_COMPLETED = "vector.index_completed"
    VECTOR_SEARCH_STARTED = "vector.search_started"
    VECTOR_SEARCH_COMPLETED = "vector.search_completed"

    # Archive 生命周期级别
    ARCHIVE_STARTED = "archive.started"
    ARCHIVE_PREFLIGHT_COMPLETED = "archive.preflight_completed"
    ARCHIVE_SPEC_MERGED = "archive.spec_merged"
    ARCHIVE_COVERAGE_GENERATED = "archive.coverage_generated"
    ARCHIVE_COMPLETED = "archive.completed"
    ARCHIVE_FAILED = "archive.failed"

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
class FileTaskStartedEvent(Event):
    """Phase 内部文件任务开始事件"""

    workflow_id: str = ""
    phase_num: int = 0
    task_id: str = ""
    task_type: str = ""
    path: str = ""
    retry_count: int = 0

    def __post_init__(self):
        self.event_type = WorkflowEventType.FILE_TASK_STARTED.value
        if not self.source:
            self.source = f"phase{self.phase_num}"


@dataclass
class FileTaskCompletedEvent(Event):
    """Phase 内部文件任务完成事件"""

    workflow_id: str = ""
    phase_num: int = 0
    task_id: str = ""
    task_type: str = ""
    path: str = ""
    duration_ms: int = 0
    retry_count: int = 0
    success: bool = True

    def __post_init__(self):
        self.event_type = WorkflowEventType.FILE_TASK_COMPLETED.value
        if not self.source:
            self.source = f"phase{self.phase_num}"


@dataclass
class FileTaskFailedEvent(Event):
    """Phase 内部文件任务失败事件"""

    workflow_id: str = ""
    phase_num: int = 0
    task_id: str = ""
    task_type: str = ""
    path: str = ""
    duration_ms: int = 0
    retry_count: int = 0
    error: str = ""

    def __post_init__(self):
        self.event_type = WorkflowEventType.FILE_TASK_FAILED.value
        if not self.source:
            self.source = f"phase{self.phase_num}"


@dataclass
class FileTaskRetryingEvent(Event):
    """Phase 内部文件任务重试事件"""

    workflow_id: str = ""
    phase_num: int = 0
    task_id: str = ""
    task_type: str = ""
    path: str = ""
    retry_count: int = 0
    error: str = ""

    def __post_init__(self):
        self.event_type = WorkflowEventType.FILE_TASK_RETRYING.value
        if not self.source:
            self.source = f"phase{self.phase_num}"


@dataclass
class PhaseParallelSummaryEvent(Event):
    """Phase 并行任务汇总事件"""

    workflow_id: str = ""
    phase_num: int = 0
    total_tasks: int = 0
    success_count: int = 0
    failed_count: int = 0
    retry_count: int = 0
    max_concurrency: int = 1
    total_task_duration_ms: int = 0

    def __post_init__(self):
        self.event_type = WorkflowEventType.PHASE_PARALLEL_SUMMARY.value
        if not self.source:
            self.source = f"phase{self.phase_num}"


@dataclass
class AgentStartedEvent(Event):
    """Multi-agent task started event"""

    workflow_id: str = ""
    phase_num: int = 0
    task_id: str = ""
    role: str = ""
    task_type: str = ""
    sandbox_id: str = ""

    def __post_init__(self):
        self.event_type = WorkflowEventType.AGENT_STARTED.value
        if not self.source:
            self.source = f"phase{self.phase_num}.{self.role or 'agent'}"


@dataclass
class AgentCompletedEvent(Event):
    """Multi-agent task completed event"""

    workflow_id: str = ""
    phase_num: int = 0
    task_id: str = ""
    role: str = ""
    task_type: str = ""
    sandbox_id: str = ""
    success: bool = True
    duration_ms: int = 0
    error: str = ""

    def __post_init__(self):
        self.event_type = WorkflowEventType.AGENT_COMPLETED.value
        if not self.source:
            self.source = f"phase{self.phase_num}.{self.role or 'agent'}"


@dataclass
class AgentMergeCompletedEvent(Event):
    """Multi-agent merge completed event"""

    workflow_id: str = ""
    phase_num: int = 0
    task_id: str = ""
    sandbox_id: str = ""
    artifact_path: str = ""
    success: bool = True
    error: str = ""

    def __post_init__(self):
        self.event_type = WorkflowEventType.AGENT_MERGE_COMPLETED.value
        if not self.source:
            self.source = f"phase{self.phase_num}.merge"


@dataclass
class AgentFallbackUsedEvent(Event):
    """Multi-agent fallback used event"""

    workflow_id: str = ""
    phase_num: int = 0
    reason: str = ""
    fallback: str = ""

    def __post_init__(self):
        self.event_type = WorkflowEventType.AGENT_FALLBACK_USED.value
        if not self.source:
            self.source = f"phase{self.phase_num}.agent"


@dataclass
class SandboxViolationEvent(Event):
    """Sandbox policy violation event"""

    workflow_id: str = ""
    phase_num: int = 0
    task_id: str = ""
    sandbox_id: str = ""
    reason: str = ""
    path: str = ""
    command: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.event_type = WorkflowEventType.SANDBOX_VIOLATION.value
        if not self.source:
            self.source = f"phase{self.phase_num}.sandbox"


@dataclass
class ArchiveLifecycleEvent(Event):
    """OpenSpec archive lifecycle event"""

    workflow_id: str = ""
    change_id: str = ""
    archive_event: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        event_type = f"archive.{self.archive_event}" if self.archive_event else WorkflowEventType.ARCHIVE_STARTED.value
        self.event_type = event_type
        if not self.source:
            self.source = "archive"


@dataclass
class VectorIndexStartedEvent(Event):
    """向量索引开始事件"""

    workflow_id: str = ""
    project_name: str = ""
    artifact_types: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.event_type = WorkflowEventType.VECTOR_INDEX_STARTED.value
        if not self.source:
            self.source = "vector_store"


@dataclass
class VectorIndexCompletedEvent(Event):
    """向量索引完成事件"""

    workflow_id: str = ""
    project_name: str = ""
    indexed_documents: int = 0
    duration_ms: int = 0

    def __post_init__(self):
        self.event_type = WorkflowEventType.VECTOR_INDEX_COMPLETED.value
        if not self.source:
            self.source = "vector_store"


@dataclass
class VectorSearchStartedEvent(Event):
    """向量检索开始事件"""

    workflow_id: str = ""
    project_name: str = ""
    top_k: int = 5
    artifact_types: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.event_type = WorkflowEventType.VECTOR_SEARCH_STARTED.value
        if not self.source:
            self.source = "vector_store"


@dataclass
class VectorSearchCompletedEvent(Event):
    """向量检索完成事件"""

    workflow_id: str = ""
    project_name: str = ""
    top_k: int = 5
    result_count: int = 0
    retrieval_latency_ms: int = 0
    fallback: bool = False

    def __post_init__(self):
        self.event_type = WorkflowEventType.VECTOR_SEARCH_COMPLETED.value
        if not self.source:
            self.source = "vector_store"


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
