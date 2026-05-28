# -*- coding: utf-8 -*-
"""
OpenSpec 事件总线系统

事件驱动架构，用于:
- 组件间的松耦合通信
- 事件溯源和审计
- 跨组件状态同步
- 插件扩展机制

事件类型:
- FileChangedEvent: 文件内容变更
- StepExecutedEvent: 工作流步骤执行
- ValidationCompletedEvent: 验证完成
- ArtifactDiscoveredEvent: 发现新工件
- RequirementChangedEvent: 需求变更
- DeltaAppliedEvent: Delta 变更应用
"""

from typing import Any, Dict, List, Optional, Callable, TypeVar, Generic, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime
import uuid
import json
from collections import defaultdict


class EventPriority(Enum):
    """事件优先级"""
    HIGH = "high"      # 高优先级，立即处理
    NORMAL = "normal"  # 普通优先级，按顺序处理
    LOW = "low"        # 低优先级，延迟处理


class EventScope(Enum):
    """事件作用域"""
    LOCAL = "local"       # 仅当前会话
    PROJECT = "project"   # 项目范围
    GLOBAL = "global"     # 全局范围


@dataclass
class Event:
    """事件基类"""
    event_type: str = "generic"
    source: str = ""  # 事件来源组件名称
    priority: EventPriority = EventPriority.NORMAL
    scope: EventScope = EventScope.PROJECT
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        event_dict = {
            "event_id": self.event_id,
            "source": self.source,
        }
        if hasattr(self, "phase_name"):
            event_dict["phase_name"] = getattr(self, "phase_name")
        event_dict.update(
            {
                "event_type": self.event_type,
                "timestamp": self.timestamp.isoformat(),
                "priority": self.priority.value,
                "scope": self.scope.value,
                "metadata": self.metadata,
            }
        )
        return event_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        return cls(
            event_type=data['event_type'],
            source=data['source'],
            priority=EventPriority(data['priority']),
            scope=EventScope(data['scope']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            event_id=data['event_id'],
            metadata=data.get('metadata', {}),
        )


# ============================================
# 具体事件类型
# ============================================

@dataclass
class FileChangedEvent(Event):
    """文件变更事件"""
    file_path: str = ""
    change_type: str = ""  # created, modified, deleted
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    delta_count: int = 0

    def __post_init__(self):
        self.event_type = "file_changed"


@dataclass
class StepExecutedEvent(Event):
    """工作流步骤执行事件"""
    workflow_name: str = ""
    step_id: str = ""
    status: str = ""  # success, failed, skipped
    duration: float = 0.0
    tool_name: Optional[str] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        self.event_type = "step_executed"


@dataclass
class ValidationCompletedEvent(Event):
    """验证完成事件"""
    file_path: Optional[str] = None
    validation_level: str = ""
    passed: bool = True
    issue_count: int = 0
    issues: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        self.event_type = "validation_completed"


@dataclass
class ArtifactDiscoveredEvent(Event):
    """发现新工件事件"""
    artifact_id: str = ""
    artifact_type: str = ""
    artifact_path: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.event_type = "artifact_discovered"


@dataclass
class RequirementChangedEvent(Event):
    """需求变更事件"""
    requirement_id: str = ""
    change_type: str = ""  # created, modified, deleted
    old_status: Optional[str] = None
    new_status: Optional[str] = None

    def __post_init__(self):
        self.event_type = "requirement_changed"


@dataclass
class DeltaAppliedEvent(Event):
    """Delta 变更应用事件"""
    target_file: str = ""
    delta_count: int = 0
    conflict_count: int = 0
    diff_preview: Optional[str] = None

    def __post_init__(self):
        self.event_type = "delta_applied"


@dataclass
class WorkflowCompletedEvent(Event):
    """工作流完成事件"""
    workflow_name: str = ""
    success: bool = True
    duration: float = 0.0
    total_steps: int = 0
    success_steps: int = 0
    failed_steps: int = 0

    def __post_init__(self):
        self.event_type = "workflow_completed"


@dataclass
class ImpactAnalysisEvent(Event):
    """影响分析事件"""
    changed_item: str = ""
    change_type: str = ""  # requirement, code, test
    affected_artifacts: List[str] = field(default_factory=list)
    impact_score: float = 0.0  # 0.0 - 1.0

    def __post_init__(self):
        self.event_type = "impact_analysis"


# ============================================
# 事件处理器类型
# ============================================

EventHandler = Callable[[Event], None]
T = TypeVar('T', bound=Event)


class EventFilter:
    """事件过滤器"""

    def __init__(self,
                 event_types: Optional[List[str]] = None,
                 sources: Optional[List[str]] = None,
                 min_priority: Optional[EventPriority] = None,
                 scope: Optional[EventScope] = None):
        self.event_types = event_types
        self.sources = sources
        self.min_priority = min_priority
        self.scope = scope

    def matches(self, event: Event) -> bool:
        """检查事件是否匹配过滤条件"""
        if self.event_types and event.event_type not in self.event_types:
            return False
        if self.sources and event.source not in self.sources:
            return False
        if self.min_priority:
            priority_order = [EventPriority.LOW, EventPriority.NORMAL, EventPriority.HIGH]
            event_level = priority_order.index(event.priority)
            min_level = priority_order.index(self.min_priority)
            if event_level < min_level:
                return False
        if self.scope and event.scope != self.scope:
            return False
        return True


class EventSubscription(Generic[T]):
    """事件订阅"""

    def __init__(self,
                 handler: Callable[[T], None],
                 filter: Optional[EventFilter] = None,
                 once: bool = False,
                 async_handler: bool = False):
        self.handler = handler
        self.filter = filter
        self.once = once
        self.async_handler = async_handler
        self.triggered_count = 0

    def should_handle(self, event: Event) -> bool:
        """是否应该处理该事件"""
        if self.once and self.triggered_count > 0:
            return False
        if self.filter and not self.filter.matches(event):
            return False
        return True

    def handle(self, event: T):
        """处理事件"""
        try:
            self.handler(event)
        finally:
            self.triggered_count += 1


# ============================================
# 事件总线
# ============================================

class EventBus:
    """OpenSpec 事件总线

    核心功能:
    - 事件发布/订阅
    - 事件过滤
    - 同步/异步处理
    - 事件持久化
    - 事件溯源查询
    """

    def __init__(self, event_store_path: Optional[Union[str, Path]] = None):
        self._subscriptions: Dict[str, List[EventSubscription]] = defaultdict(list)
        self._global_subscriptions: List[EventSubscription] = []
        self._event_store: List[Event] = []
        self._event_store_path = Path(event_store_path) if event_store_path else None
        self._async_queue: List[Event] = []
        self._processing = False

        # 事件统计
        self._stats: Dict[str, int] = defaultdict(int)

    def subscribe(self,
                 event_type: str,
                 handler: Callable[[Event], None],
                 filter: Optional[EventFilter] = None,
                 once: bool = False,
                 async_handler: bool = False) -> str:
        """订阅特定类型的事件

        Args:
            event_type: 事件类型
            handler: 处理函数
            filter: 事件过滤器
            once: 是否只触发一次
            async_handler: 是否异步处理

        Returns:
            subscription_id: 订阅ID
        """
        subscription_id = str(uuid.uuid4())[:8]
        subscription = EventSubscription(
            handler=handler,
            filter=filter,
            once=once,
            async_handler=async_handler
        )
        self._subscriptions[event_type].append(subscription)
        return subscription_id

    def subscribe_all(self,
                     handler: Callable[[Event], None],
                     filter: Optional[EventFilter] = None,
                     async_handler: bool = False) -> str:
        """订阅所有事件

        Args:
            handler: 处理函数
            filter: 事件过滤器
            async_handler: 是否异步处理

        Returns:
            subscription_id: 订阅ID
        """
        subscription_id = str(uuid.uuid4())[:8]
        subscription = EventSubscription(
            handler=handler,
            filter=filter,
            once=False,
            async_handler=async_handler
        )
        self._global_subscriptions.append(subscription)
        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅

        Returns:
            是否成功取消
        """
        # 检查类型订阅
        for event_type, subs in self._subscriptions.items():
            for sub in subs:
                if id(sub) == id(subscription_id):  # TODO: 使用更好的标识方式
                    subs.remove(sub)
                    return True

        # 检查全局订阅
        for sub in self._global_subscriptions:
            if id(sub) == id(subscription_id):
                self._global_subscriptions.remove(sub)
                return True

        return False

    def publish(self, event: Event, immediate: bool = True) -> str:
        """发布事件

        Args:
            event: 事件对象
            immediate: 是否立即处理（False 表示加入队列）

        Returns:
            event_id: 事件ID
        """
        self._event_store.append(event)
        self._stats[event.event_type] += 1

        # 持久化
        if self._event_store_path:
            self._append_to_store(event)

        if immediate:
            self._dispatch_event(event)
        else:
            self._async_queue.append(event)

        return event.event_id

    def _dispatch_event(self, event: Event):
        """分发事件到订阅者"""
        # 分发到类型订阅
        for subscription in self._subscriptions.get(event.event_type, []):
            if subscription.should_handle(event):
                if subscription.async_handler:
                    # TODO: 真正的异步处理
                    import threading
                    threading.Thread(
                        target=subscription.handle,
                        args=(event,),
                        daemon=True
                    ).start()
                else:
                    subscription.handle(event)

        # 分发到全局订阅
        for subscription in self._global_subscriptions:
            if subscription.should_handle(event):
                if subscription.async_handler:
                    import threading
                    threading.Thread(
                        target=subscription.handle,
                        args=(event,),
                        daemon=True
                    ).start()
                else:
                    subscription.handle(event)

    def process_queue(self) -> int:
        """处理异步事件队列

        Returns:
            处理的事件数量
        """
        count = len(self._async_queue)
        for event in self._async_queue:
            self._dispatch_event(event)
        self._async_queue.clear()
        return count

    def _append_to_store(self, event: Event):
        """追加事件到持久化存储"""
        if not self._event_store_path:
            return

        self._event_store_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self._event_store_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event.to_dict(), ensure_ascii=False) + '\n')
        except Exception:
            pass

    def query_events(self,
                    event_type: Optional[str] = None,
                    source: Optional[str] = None,
                    start_time: Optional[datetime] = None,
                    end_time: Optional[datetime] = None,
                    limit: int = 100) -> List[Event]:
        """查询历史事件

        Args:
            event_type: 事件类型过滤
            source: 来源过滤
            start_time: 开始时间
            end_time: 结束时间
            limit: 最大返回数量

        Returns:
            匹配的事件列表（按时间倒序）
        """
        results = []
        for event in reversed(self._event_store):
            if event_type and event.event_type != event_type:
                continue
            if source and event.source != source:
                continue
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue

            results.append(event)
            if len(results) >= limit:
                break

        return results

    def get_event_stats(self) -> Dict[str, Any]:
        """获取事件统计信息"""
        return {
            'total_events': len(self._event_store),
            'by_type': dict(self._stats),
            'queue_size': len(self._async_queue),
            'subscriptions': {
                'by_type': {k: len(v) for k, v in self._subscriptions.items()},
                'global': len(self._global_subscriptions),
            }
        }

    def replay_events(self,
                     start_time: Optional[datetime] = None,
                     end_time: Optional[datetime] = None,
                     event_types: Optional[List[str]] = None) -> int:
        """重放事件

        用于:
        - 系统状态重建
        - 新组件初始化同步
        - 调试和测试

        Returns:
            重放的事件数量
        """
        count = 0
        for event in self._event_store:
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue
            if event_types and event.event_type not in event_types:
                continue

            self._dispatch_event(event)
            count += 1

        return count

    def clear_history(self, before: Optional[datetime] = None) -> int:
        """清理历史事件

        Args:
            before: 只清理此时间之前的事件，None 表示清理全部

        Returns:
            清理的事件数量
        """
        if before is None:
            count = len(self._event_store)
            self._event_store.clear()
            return count

        original_count = len(self._event_store)
        self._event_store = [e for e in self._event_store if e.timestamp >= before]
        return original_count - len(self._event_store)


# ============================================
# 事件总线适配器 - 用于集成到各个组件
# ============================================

class EventBusAdapter:
    """事件总线适配器

    方便各个组件发布事件的便捷包装类
    """

    def __init__(self, event_bus: EventBus, component_name: str):
        self._event_bus = event_bus
        self._component_name = component_name

    def publish_file_changed(self,
                            file_path: str,
                            change_type: str,
                            old_content: Optional[str] = None,
                            new_content: Optional[str] = None,
                            delta_count: int = 0,
                            **metadata):
        """发布文件变更事件"""
        event = FileChangedEvent(
            source=self._component_name,
            file_path=file_path,
            change_type=change_type,
            old_content=old_content,
            new_content=new_content,
            delta_count=delta_count,
            metadata=metadata,
        )
        return self._event_bus.publish(event)

    def publish_step_executed(self,
                             workflow_name: str,
                             step_id: str,
                             status: str,
                             duration: float = 0.0,
                             tool_name: Optional[str] = None,
                             error_message: Optional[str] = None,
                             **metadata):
        """发布步骤执行事件"""
        event = StepExecutedEvent(
            source=self._component_name,
            workflow_name=workflow_name,
            step_id=step_id,
            status=status,
            duration=duration,
            tool_name=tool_name,
            error_message=error_message,
            metadata=metadata,
        )
        return self._event_bus.publish(event)

    def publish_validation_completed(self,
                                    passed: bool,
                                    issue_count: int,
                                    file_path: Optional[str] = None,
                                    validation_level: str = "format",
                                    issues: Optional[List[Dict]] = None,
                                    **metadata):
        """发布验证完成事件"""
        event = ValidationCompletedEvent(
            source=self._component_name,
            passed=passed,
            issue_count=issue_count,
            file_path=file_path,
            validation_level=validation_level,
            issues=issues or [],
            metadata=metadata,
        )
        return self._event_bus.publish(event)

    def publish_artifact_discovered(self,
                                   artifact_id: str,
                                   artifact_type: str,
                                   artifact_path: Optional[str] = None,
                                   dependencies: Optional[List[str]] = None,
                                   **metadata):
        """发布工件发现事件"""
        event = ArtifactDiscoveredEvent(
            source=self._component_name,
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            artifact_path=artifact_path,
            dependencies=dependencies or [],
            metadata=metadata,
        )
        return self._event_bus.publish(event)

    def publish_delta_applied(self,
                             target_file: str,
                             delta_count: int,
                             conflict_count: int = 0,
                             diff_preview: Optional[str] = None,
                             **metadata):
        """发布 Delta 应用事件"""
        event = DeltaAppliedEvent(
            source=self._component_name,
            target_file=target_file,
            delta_count=delta_count,
            conflict_count=conflict_count,
            diff_preview=diff_preview,
            metadata=metadata,
        )
        return self._event_bus.publish(event)

    def publish_workflow_completed(self,
                                  workflow_name: str,
                                  success: bool,
                                  duration: float,
                                  total_steps: int,
                                  success_steps: int,
                                  failed_steps: int,
                                  **metadata):
        """发布工作流完成事件"""
        event = WorkflowCompletedEvent(
            source=self._component_name,
            workflow_name=workflow_name,
            success=success,
            duration=duration,
            total_steps=total_steps,
            success_steps=success_steps,
            failed_steps=failed_steps,
            metadata=metadata,
        )
        return self._event_bus.publish(event)

    def publish_impact_analysis(self,
                               changed_item: str,
                               change_type: str,
                               affected_artifacts: List[str],
                               impact_score: float = 0.0,
                               **metadata):
        """发布影响分析事件"""
        event = ImpactAnalysisEvent(
            source=self._component_name,
            changed_item=changed_item,
            change_type=change_type,
            affected_artifacts=affected_artifacts,
            impact_score=impact_score,
            metadata=metadata,
        )
        return self._event_bus.publish(event)

    def subscribe(self, event_type: str, handler: Callable, **kwargs):
        """订阅事件"""
        return self._event_bus.subscribe(event_type, handler, **kwargs)

    def subscribe_all(self, handler: Callable, **kwargs):
        """订阅所有事件"""
        return self._event_bus.subscribe_all(handler, **kwargs)


# ============================================
# 全局事件总线实例
# ============================================

_global_event_bus: Optional[EventBus] = None


def get_global_event_bus(event_store_path: Optional[Union[str, Path]] = None) -> EventBus:
    """获取全局事件总线实例"""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus(event_store_path)
    return _global_event_bus


def set_global_event_bus(bus: EventBus):
    """设置全局事件总线实例"""
    global _global_event_bus
    _global_event_bus = bus
