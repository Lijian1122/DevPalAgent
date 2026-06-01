# EventBus 主流程接入实施计划

**日期**：2026-05-25  
**目标**：将 EventBus 接入 OpenSpec 主流程，实现全链路事件追踪和可观测性  
**预期工期**：3-4 天  
**优先级**：P3（可选优化）

---

## 1. 背景与目标

### 1.1 当前状态

**已完成能力**：
- ✅ EventBus 核心实现（`devpal/core/schema/event_bus.py`）
- ✅ 发布-订阅模式
- ✅ 事件类型定义
- ✅ 同步/异步事件处理
- ✅ 事件过滤和优先级

**当前限制**：
- ❌ EventBus 未接入 OpenSpec 主流程
- ❌ Phase 执行无事件发出
- ❌ 工具调用无事件追踪
- ❌ 缺少统一的事件日志
- ❌ 可观测性不足

**影响**：
- 难以追踪 Phase 执行细节
- 无法实时监控工作流状态
- 调试困难，缺少事件时间线
- 无法构建事件驱动的扩展

### 1.2 设计目标

**核心理念**：
> EventBus 是 OpenSpec Runtime 的神经系统，所有关键操作都应发出事件，实现全链路可观测。

**分层架构**：
```text
OpenSpec Workflow
  ↓ 发出事件
EventBus (中央事件总线)
  ↓ 订阅
┌─────────┬─────────┬─────────┬─────────┐
│ Logger  │ Monitor │ Tracer  │ Plugins │
└─────────┴─────────┴─────────┴─────────┘
```

**与现有架构关系**：
```text
EnhancedOpenSpecScheduler
  ├─ execute_phase() → 发出 PhaseStarted/PhaseCompleted 事件
  ├─ checkpoint() → 发出 CheckpointCreated 事件
  └─ resume() → 发出 WorkflowResumed 事件

Phase 1-11
  ├─ execute() → 发出 PhaseExecuting 事件
  ├─ tool_call() → 发出 ToolCalled 事件
  └─ validation() → 发出 ValidationCompleted 事件

ToolRegistry
  └─ execute_tool() → 发出 ToolStarted/ToolCompleted 事件
```

### 1.3 面试价值

**展示点**：
1. **Event-Driven Architecture**：解耦组件，通过事件通信
2. **Observability**：全链路事件追踪，可视化工作流
3. **Extensibility**：插件化监控、日志、追踪
4. **Debugging**：事件时间线重放，快速定位问题
5. **Multi-Agent Integration**：为多智能体通信提供基础设施

---

## 2. 核心抽象设计

### 2.1 事件类型体系

#### 2.1.1 工作流级别事件

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional

class EventType(Enum):
    """事件类型枚举"""
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

@dataclass
class BaseEvent:
    """事件基类"""
    event_id: str                    # 事件唯一 ID
    event_type: EventType            # 事件类型
    timestamp: datetime              # 时间戳
    source: str                      # 事件来源（phase/tool/scheduler）
    workflow_id: Optional[str] = None  # 工作流 ID
    phase_num: Optional[int] = None    # 阶段编号
    metadata: Dict[str, Any] = None    # 元数据
    
    def __post_init__(self):
        if self.metadata is None:
        self.metadata = {}
```

#### 2.1.2 具体事件定义

```python
@dataclass
class WorkflowStartedEvent(BaseEvent):
    """工作流开始事件"""
    requirements_file: str
    project_name: str
    language: str
    project_type: str
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = EventType.WORKFLOW_STARTED
        self.source = "scheduler"

@dataclass
class PhaseStartedEvent(BaseEvent):
    """阶段开始事件"""
    phase_name: str
    phase_num: int
    estimated_duration_seconds: Optional[int] = None
    
    def __post_init__(self):
    super().__post_init__()
        self.event_type = EventType.PHASE_STARTED
        self.source = f"phase{self.phase_num}"

@dataclass
class PhaseCompletedEvent(BaseEvent):
    """阶段完成事件"""
    phase_name: str
    phase_num: int
    success: bool
    duration_ms: int
    result_summary: str
    artifacts: list = None
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = EventType.PHASE_COMPLETED
        self.source = f"phase{self.phase_num}"
        if self.artifacts is None:
            self.artifacts = []

@dataclass
class ToolCalledEvent(BaseEvent):
    """工具调用事件"""
    tool_name: str
    tool_params: Dict[str, Any]
    caller: str  # 调用者（phase4/phase9/etc）
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = EventType.TOOL_CALLED
        self.source = self.caller

@dataclass
class FileGeneratedEvent(BaseEvent):
    """文件生成事件"""
    file_path: str
    file_type: str  # source/test/doc/config
    lines_of_code: int
    language: str
    generated_by: str  # phase4/template/tool
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = EventType.FILE_GENERATED
      self.source = self.generated_by

@dataclass
class LLMRequestCompletedEvent(BaseEvent):
    """LLM 请求完成事件"""
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    duration_ms: int
    cache_hit: bool
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = EventType.LLM_REQUEST_COMPLETED
        self.source = "llm_client"
```

### 2.2 EventBus 增强

#### 2.2.1 事件过滤器

```python
from typing import Callable

class EventFilter:
    """事件过滤器"""
    
    def __init__(self, 
             event_types: list[EventType] = None,
            source_pattern: str = None,
                 phase_nums: list[int] = None):
        self.event_types = event_types
     self.source_pattern = source_pattern
        self.phase_nums = phase_nums
    
    def matches(self, event: BaseEvent) -> bool:
      """判断事件是否匹配过滤条件"""
        if self.event_types and event.event_type not in self.event_types:
         return False
        
        if self.source_pattern and not event.source.startswith(self.source_pattern):
            return False
        
     if self.phase_nums and event.phase_num not in self.phase_nums:
            return False
        
        return True

# 使用示例
phase4_filter = EventFilter(
    event_types=[EventType.PHASE_STARTED, EventType.PHASE_COMPLETED],
    phase_nums=[4]
)
```

#### 2.2.2 事件持久化

```python
import json
from pathlib import Path

class EventLogger:
    """事件日志记录器"""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
    self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log_event(self, event: BaseEvent):
        """记录事件到文件"""
      event_dict = {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
        "timestamp": event.timestamp.isoformat(),
        "source": event.source,
          "workflow_id": event.workflow_id,
            "phase_num": event.phase_num,
            "metadata": event.metadata,
            # 具体事件字段
            **{k: v for k, v in event.__dict__.items() 
               if k not in ['event_id', 'event_type', 'timestamp', 'source', 
                           'workflow_id', 'phase_num', 'metadata']}
        }
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event_dict, ensure_ascii=False) + '\n')
    
    def read_events(self, filter: EventFilter = None) -> list[BaseEvent]:
        """读取事件日志"""
      events = []
        if not self.log_file.exists():
            return events
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
            event_dict = json.loads(line)
                # 重建事件对象（简化版）
              event = BaseEvent(
                event_id=event_dict['event_id'],
                    event_type=EventType(event_dict['event_type']),
                    timestamp=datetime.fromisoformat(event_dict['timestamp']),
                    source=event_dict['source'],
                    workflow_id=event_dict.get('workflow_id'),
                    phase_num=event_dict.get('phase_num'),
                    metadata=event_dict.get('metadata', {})
            )
                
                if filter is None or filter.matches(event):
                events.append(event)
        
   return events
```

#### 2.2.3 事件统计

```python
from collections import defaultdict

class EventStatistics:
    """事件统计"""
    
    def __init__(self):
   self.event_counts = defaultdict(int)
        self.phase_durations = {}
        self.tool_calls = defaultdict(int)
        self.llm_tokens = {
            'prompt': 0,
            'completion': 0,
         'cache_creation': 0,
            'cache_read': 0
        }
    
    def process_event(self, event: BaseEvent):
        """处理事件并更新统计"""
        self.event_counts[event.event_type] += 1
        
        if isinstance(event, PhaseCompletedEvent):
            self.phase_durations[event.phase_num] = event.duration_ms
        
        if isinstance(event, ToolCalledEvent):
       self.tool_calls[event.tool_name] += 1
        
        if isinstance(event, LLMRequestCompletedEvent):
            self.llm_tokens['prompt'] += event.prompt_tokens
            self.llm_tokens['completion'] += event.completion_tokens
            self.llm_tokens['cache_creation'] += event.cache_creation_tokens
            self.llm_tokens['cache_read'] += event.cache_read_tokens
    
    def get_summary(self) -> dict:
        """获取统计摘要"""
        return {
            'total_events': sum(self.event_counts.values()),
            'event_counts': dict(self.event_counts),
            'phase_durations': self.phase_durations,
            'tool_calls': dict(self.tool_calls),
        'llm_tokens': self.llm_tokens,
       'total_duration_ms': sum(self.phase_durations.values())
        }
```

---

## 3. 主流程接入方案
### 3.1 EnhancedOpenSpecScheduler 接入

#### 3.1.1 初始化 EventBus

```python
# devpal/core/openspec_phases/enhanced_scheduler.py

from devpal/core/schema/event_bus import EventBus
from devpal/core/schema/events import *
import uuid

class EnhancedOpenSpecScheduler:
    def __init__(self, ...):
        # 现有初始化代码
        ...
        
        # 新增：初始化 EventBus
        self.event_bus = EventBus.get_instance()
        self.workflow_id = str(uuid.uuid4())
        
        # 新增：初始化事件日志
        self.event_logger = EventLogger(
            Path(self.requirements_file).parent / '.spec' / 'events.jsonl'
        )
        self.event_bus.subscribe(
            event_type=None,  # 订阅所有事件
            handler=self.event_logger.log_event
      )
    
        # 新增：初始化事件统计
        self.event_stats = EventStatistics()
        self.event_bus.subscribe(
            event_type=None,
            handler=self.event_stats.process_event
        )
```

#### 3.1.2 发出工作流事件

```python
def run_all_phases(self, resume: bool = False) -> Dict[str, Any]:
    """执行所有阶段"""
    
    # 发出工作流开始事件
    self.event_bus.publish(WorkflowStartedEvent(
        event_id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        workflow_id=self.workflow_id,
        requirements_file=self.requirements_file,
        project_name=self.context.project_name,
        language=self.context.language,
        project_type=self.context.project_type
    ))
    
    try:
        # 现有执行逻辑
     for phase_num in range(1, 12):
            result = self.execute_phase(phase_num)
         ...
        
        # 发出工作流完成事件
        self.event_bus.publish(WorkflowCompletedEvent(
          event_id=str(uuid.uuid4()),
       timestamp=datetime.now(),
         workflow_id=self.workflow_id,
            source="scheduler",
            success=True,
            total_duration_ms=...,
            phases_completed=11,
       statistics=self.event_stats.get_summary()
      ))
        
      return self.context.phase_results
        
    except Exception as e:
        # 发出工作流失败事件
        self.event_bus.publish(WorkflowFailedEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            workflow_id=self.workflow_id,
          source="scheduler",
          error=str(e),
            failed_phase=...
        ))
        raise
```

#### 3.1.3 发出阶段事件

```python
def execute_phase(self, phase_num: int) -> PhaseResult:
    """执行单个阶段"""
    phase_name = self.get_phase_name(phase_num)
    
    # 发出阶段开始事件
    start_time = datetime.now()
    self.event_bus.publish(PhaseStartedEvent(
        event_id=str(uuid.uuid4()),
        timestamp=start_time,
        workflow_id=self.workflow_id,
        phase_num=phase_num,
      phase_name=phase_name,
        source=f"phase{phase_num}"
    ))
    
    try:
        # 现有执行逻辑
        result = self._execute_phase_impl(phase_num)
        
        # 发出阶段完成事件
        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        self.event_bus.publish(PhaseCompletedEvent(
            event_id=str(uuid.uuid4()),
            timestamp=end_time,
            workflow_id=self.workflow_id,
          phase_num=phase_num,
            phase_name=phase_name,
            source=f"phase{phase_num}",
         success=result.success,
            duration_ms=duration_ms,
            result_summary=result.message,
          artifacts=result.data.get('generated_files', [])
        ))
        
        return result
        
    except Exception as e:
        # 发出阶段失败事件
        self.event_bus.publish(PhaseFailedEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            workflow_id=self.workflow_id,
            phase_num=phase_num,
          phase_name=phase_name,
            source=f"phase{phase_num}",
            error=str(e)
        ))
        raise
```

