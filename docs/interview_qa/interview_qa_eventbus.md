# Interview Q&A: EventBus Architecture
## 面试专题：事件驱动架构与可观测性

---

## Q1: DevPalAgent 的 EventBus 是什么？为什么需要它？

**核心回答**:
EventBus 是 DevPalAgent 的事件驱动通信总线，实现了**解耦**、**可观测**、**可扩展**的架构。它采用 Publish-Subscribe 模式，让各个组件通过事件进行通信，而不是直接依赖。

**为什么需要**:
1. **解耦**: Phase 之间、Agent 之间、Tool 之间松耦合
2. **可观测性**: 统一的事件日志，完整追踪执行流程
3. **可扩展**: 新增功能只需订阅事件，无需修改核心代码
4. **监控告警**: 实时监控性能、错误、进度

**对标**:
- Kafka/RabbitMQ: 生产级消息队列（但 DevPalAgent 是内存版，更轻量）
- EventEmitter (Node.js): 类似概念，但 DevPalAgent 支持结构化事件

---

## Q2: EventBus 的核心设计是什么？

**架构**:
```python
# devpal/core/schema/event_bus.py
class EventBus:
    """事件总线"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._event_log: List[Event] = []
        self._logger = logging.getLogger("EventBus")
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """订阅事件"""
        self._subscribers[event_type].append(handler)
        self._logger.info(f"[Subscribe] {event_type} → {handler.__name__}")
    
    def publish(self, event: Event) -> None:
      """发布事件"""
        # 1. 记录事件
        self._event_log.append(event)
        
        # 2. 持久化事件（写入 JSONL）
        self._persist_event(event)
        
       # 3. 通知订阅者
        for handler in self._subscribers.get(event.event_type, []):
            try:
             handler(event)
            except Exception as e:
        self._logger.error(f"[Handler Error] {handler.__name__}: {e}")
    
   def _persist_event(self, event: Event) -> None:
        """持久化事件到 JSONL"""
      event_log_file = self._get_event_log_path()
        with open(event_log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event.to_dict()) + '\n')
    
    def query_events(self, event_type: Optional[str] = None,
                  time_range: Optional[Tuple[datetime, datetime]] = None) -> List[Event]:
        """查询事件"""
        results = self._event_log
        
        if event_type:
          results = [e for e in results if e.event_type == event_type]
        
        if time_range:
            start, end = time_range
            results = [e for e in results if start <= e.timestamp <= end]
        
        return results
```

**Event 数据结构**:
```python
# devpal/core/schema/events.py
@dataclass
class Event:
    """事件基类"""
    event_type: str
    timestamp: datetime
    workflow_id: str
    payload: dict
    
    def to_dict(self) -> dict:
      return {
            "event_type": self.event_type,
          "timestamp": self.timestamp.isoformat(),
            "workflow_id": self.workflow_id,
            "payload": self.payload
        }

# 具体事件类型
class WorkflowStartedEvent(Event):
    def __init__(self, workflow_id, requirements_file, language):
        super().__init__(
         event_type="workflow.started",
          timestamp=datetime.now(),
            workflow_id=workflow_id,
            payload={
           "requirements_file": requirements_file,
                "language": language
            }
        )

class PhaseStartedEvent(Event):
    def __init__(self, workflow_id, phase_num, phase_name):
        super().__init__(
          event_type="phase.started",
            timestamp=datetime.now(),
            workflow_id=workflow_id,
         payload={
                "phase_num": phase_num,
                "phase_name": phase_name
          }
      )

class PhaseCompletedEvent(Event):
    def __init__(self, workflow_id, phase_num, success, duration):
        super().__init__(
            event_type="phase.completed",
            timestamp=datetime.now(),
      workflow_id=workflow_id,
            payload={
                "phase_num": phase_num,
                "success": success,
                "duration": duration
            }
        )
```

---

## Q3: EventBus 如何集成到 OpenSpec Workflow？

**EventBusIntegration**:
```python
# devpal/core/schema/eventbus_integration.py
class EventBusIntegration:
    """EventBus 与 OpenSpec 的集成层"""
    
    def __init__(self, requirements_file: str, project_name: str):
        self.event_bus = EventBus()
        self.workflow_id = self._generate_workflow_id()
       self.project_name = project_name
        
        # 注册监控器
       self._register_monitors()
    
    def _register_monitors(self):
        """注册事件监控器"""
        # 进度监控
        self.progress_monitor = ProgressMonitor()
        self.event_bus.subscribe("phase.*", self.progress_monitor.handle_event)
        
        # 性能分析
        self.performance_analyzer = PerformanceAnalyzer()
        self.event_bus.subscribe("phase.completed", self.performance_analyzer.handle_event)
        
        # 错误追踪
        self.error_tracker = ErrorTracker()
        self.event_bus.subscribe("phase.failed", self.error_tracker.handle_event)
    
    def emit_workflow_started(self, context):
        """发出 workflow 开始事件"
        self.event_bus.publish(WorkflowStartedEvent(
            workflow_id=self.workflow_id,
            requirements_file=context.requirements_file,
            language=context.language
        ))
    
    def emit_phase_started(self, phase_num, phase_name):
        """发出 phase 开始事件"""
        self.event_bus.publish(PhaseStartedEvent(
         workflow_id=self.workflow_id,
          phase_num=phase_num,
            phase_name=phase_name
        ))
    
    def emit_phase_completed(self, phase_num, success, duration):
        """发出 phase 完成事件"""
        self.event_bus.publish(PhaseCompletedEvent(
        workflow_id=self.workflow_id,
       phase_num=phase_num,
            success=success,
            duration=duration
        ))
```

**EnhancedScheduler 集成**:
```python
# devpal/core/openspec_phases/enhanced_scheduler.py
class EnhancedOpenSpecScheduler:
    def __init__(self, ...):
        # 初始化 EventBus 集成
        self.event_integration = EventBusIntegration(
            requirements_file=requirements_file,
       project_name=initial_project_name
      )
        self.context.event_integration = self.event_integration
    
    def run(self, phases: List[Phase]) -> Dict:
        # 发出 workflow 开始事件
        self.event_integration.emit_workflow_started(self.context)
        
        for i, phase in enumerate(phases):
            # 发出 phase 开始事件
            self.event_integration.emit_phase_started(i+1, phase.phase_name)
            
            start_time = time.time()
          result = phase.execute(self.context)
         duration = time.time() - start_time
            
            # 发出 phase 完成事件
            self.event_integration.emit_phase_completed(
                i+1, result.success, duration
            )
        
        # 发出 workflow 完成事件
        self.event_integration.emit_workflow_completed(success=True)
```

---

## Q4: EventBus 的监控器（Monitors）如何工作？

**ProgressMonitor (进度监控)**:
```python
# devpal/core/schema/progress_monitor.py
class ProgressMonitor:
    """进度监控器"""
    
    def __init__(self):
        self.total_phases = 11
     self.completed_phases = 0
      self.current_phase = None
        self.start_time = None
    
    def handle_event(self, event: Event):
        """处理事件"""
        if event.event_type == "workflow.started":
       self.start_time = event.timestamp
            print(f"[ProgressMonitor] Workflow started: {event.payload['workflow_id']}")
        elif event.event_type == "phase.started":
         self.current_phase = event.payload["phase_num"]
          phase_name = event.payload["phase_name"]
     progress = (self.current_phase / self.total_phases) * 100
            print(f"[Progress] {progress:.1f}% - Phase {self.current_phase}: {phase_name}")
        
        elif event.event_type == "phase.completed":
          self.completed_phases += 1
            # 计算预计剩余时间
            remaining_time = self._estimate_remaining_time()
            print(f"[Progress] Estimated remaining time: {remaining_time:.1f}s")
        
        elif event.event_type == "workflow.completed":
           total_duration = (event.timestamp - self.start_time).total_seconds()
          print(f"[ProgressMonitor] Workflow completed in {total_duration:.1f}s")
```

**PerformanceAnalyzer (性能分析)**:
```python
# devpal/core/schema/performance_analyzer.py
class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        self.phase_durations: Dict[int, List[float]] = defaultdict(list)
        self.slowest_phase = None
    
    def handle_event(self, event: Event):
        """处理 phase.completed 事件"""
        phase_num = event.payload["phase_num"]
        duration = event.payload["duration"]
        
        self.phase_durations[phase_num].append(duration)
        
        # 更新最慢 phase
        if not self.slowest_phase or duration > self.slowest_phase[1]:
            self.slowest_phase = (phase_num, duration)
    
    def generate_report(self) -> str:
        """生成性能报告"""
        report = "Performance Analysis Report\n"
      report += "=" * 70 + "\n\n"
        
        total_duration = sum(sum(durations) for durations in self.phase_durations.values())
        
        report += f"Total Duration: {total_duration:.2f}s\n\n"
        report += "Phase Performance:\n"
        report += "-" * 70 + "\n"
        
        for phase_num in sorted(self.phase_durations.keys()):
            durations = self.phase_durations[phase_num]
            avg_duration = statistics.mean(durations)
            percentage = (avg_duration / total_duration) * 100
            
            bar = "#" * int(percentage / 3)
            report += f"  Phase {phase_num:2d}: {avg_duration:6.2f}s [{bar:<30}] {percentage:5.1f}%\n"
        
        report += "\n" + "-" * 70 + "\n"
        report += f"  Slowest Phase: Phase {self.slowest_phase[0]} ({self.slowest_phase[1]:.2f}s)\n"
        
        # 性能建议
        if self.slowest_phase[1] > 30:
          report += "\nPerformance Recommendations:\n"
            report += f"  - Phase {self.slowest_phase[0]} takes {self.slowest_phase[1]:.1f}s, consider optimization\n"
        
        return report
```

**ErrorTracker (错误追踪)**:
```python
# devpal/core/schema/error_tracker.py
class ErrorTracker:
    """错误追踪器"""
    
    def __init__(self):
        self.errors: List[dict] = []
        self.error_categories = Counter()
    
    def handle_event(self, event: Event):
        """处理 phase.failed 事件"""
        error_info = {
         "timestamp": event.timestamp,
            "phase_num": event.payload["phase_num"],
            "phase_name": event.payload["phase_name"],
            "error_message": event.payload["error_message"],
          "error_category": self._categorize_error(event.payload["error_message"])
        }
     
        self.errors.append(error_info)
        self.error_categories[error_info["error_category"]] += 1
        
        # 实时告警（如果是 CRITICAL 错误）
        if error_info["error_category"] == "CRITICAL":
            self._send_alert(error_info)
    
    def _categorize_error(self, error_message: str) -> str:
     """错误分类"""
    if "timeout" in error_message.lower():
            return "TIMEOUT"
        elif "dependency" in error_message.lower():
         return "DEPENDENCY"
        elif "syntax" in error_message.lower():
            return "SYNTAX"
     else:
            return "UNKNOWN"
    
    def get_error_summary(self) -> dict:
        """获取错误摘要"""
        return {
            "total_errors": len(self.errors),
            "by_category": dict(self.error_categories),
            "recent_errors": self.errors[-5:]  # 最近 5 个错误
        }
```

---

## Q5: EventBus 的事件日志如何持久化和查询？

**JSONL 格式存储**:
```
.spec/events/20260604_155513_9aaca4d1.jsonl
```

**日志格式**:
```jsonl
{"event_type":"workflow.started","timestamp":"2026-06-04T15:55:13","workflow_id":"9aaca4d1","payload":{"requirements_file":"requirements/simple_login.md","language":"cpp"}}
{"event_type":"phase.started","timestamp":"2026-06-04T15:55:13","workflow_id":"9aaca4d1","payload":{"phase_num":1,"phase_name":"Parse requirements"}}
{"event_type":"phase.completed","timestamp":"2026-06-04T15:55:13","workflow_id":"9aaca4d1","payload":{"phase_num":1,"success":true,"duration":0.08}}
{"event_type":"phase.started","timestamp":"2026-06-04T15:55:13","workflow_id":"9aaca4d1","payload":{"phase_num":2,"phase_name":"Create project structure"}}
...
```

**查询 API**:
```python
# devpal/core/schema/event_query.py
class EventQuery:
    """事件查询器"""
    
    def __init__(self, event_log_file: str):
        self.event_log_file = event_log_file
        self._events = self._load_events()
    
    def _load_events(self) -> List[Event]:
        """加载事件日志"""
        events = []
        with open(self.event_log_file, 'r', encoding='utf-8') as f:
            for line in f:
                event_data = json.loads(line)
                events.append(Event.from_dict(event_data))
        return events
    
    def filter_by_type(self, event_type: str) -> List[Event]:
        """按类型过滤"""
        return [e for e in self._events if e.event_type == event_type]
    
    def filter_by_phase(self, phase_num: int) -> List[Event]:
    """按 Phase 过滤"""
        return [e for e in self._events if e.payload.get("phase_num") == phase_num]
    
    def get_phase_duration(self, phase_num: int) -> float:
        """获取 Phase 执行时长"""
        started = next(e for e in self._events 
                    if e.event_type == "phase.started" 
                    and e.payload["phase_num"] == phase_num)
        completed = next(e for e in self._events 
                  if e.event_type == "phase.completed" 
                and e.payload["phase_num"] == phase_num)
        return (completed.timestamp - started.timestamp).total_seconds()
    
    def get_workflow_summary(self) -> dict:
        """获取 workflow 摘要"""
        workflow_started = next(e for e in self._events if e.event_type == "workflow.started")
        workflow_completed = next(e for e in self._events if e.event_type == "workflow.completed")
        
        total_duration = (workflow_completed.timestamp - workflow_started.timestamp).total_seconds()
        
        phases_completed = len([e for e in self._events if e.event_type == "phase.completed"])
        phases_failed = len([e for e in self._events if e.event_type == "phase.failed"])
      
        return {
         "workflow_id": workflow_started.workflow_id,
            "total_duration": total_duration,
            "phases_completed": phases_completed,
          "phases_failed": phases_failed,
        "success": workflow_completed.payload.get("success", False)
        }
```

**CLI 查询工具**:
```bash
# 查询最近一次 workflow 的事件
python -m devpal.eventbus query --latest

# 查询特定 workflow 的事件
python -m devpal.eventbus query --workflow-id 9aaca4d1

# 查询失败的 phases
python -m devpal.eventbus query --event-type phase.failed

# 生成性能报告
python -m devpal.eventbus analyze --workflow-id 9aaca4d1
```

---

## Q6: EventBus 的扩展性如何？

**插件式监控器**:
```python
# 用户可以自定义监控器
class CustomMetricsMonitor:
    """自定义指标监控器"""
    
    def __init__(self, metrics_backend):
        self.metrics = metrics_backend
    
    def handle_event(self, event: Event):
        """处理事件并上报指标"""
        if event.event_type == "phase.completed":
            self.metrics.record_gauge(
                "devpal.phase.duration",
                event.payload["duration"],
          tags={
                    "phase_num": event.payload["phase_num"],
                    "success": event.payload["success"]
             }
      )

# 注册到 EventBus
event_bus = EventBus()
custom_monitor = CustomMetricsMonitor(DatadogMetrics())
event_bus.subscribe("phase.completed", custom_monitor.handle_event)
```

**与外部系统集成**:
```python
# 集成 Datadog
class DatadogIntegration:
    def handle_event(self, event: Event):
        if event.event_type == "phase.failed":
            datadog.api.Event.create(
         title=f"DevPalAgent Phase Failed",
                text=f"Phase {event.payload['phase_num']} failed",
                alert_type="error"
            )

# 集成 Slack
class SlackIntegration:
    def handle_event(self, event: Event):
        if event.event_type == "workflow.completed":
        slack.send_message(
              channel="#devpal-notifications",
                text=f"✅ Workflow {event.workflow_id} completed"
            )
```

---

## 面试展示脚本

**开场**:
"EventBus 是 DevPalAgent 的神经系统，它通过事件驱动架构实现了解耦、可观测、可扩展。"

**技术深度展示**:
1. "Pub-Sub 架构：发布者与订阅者解耦，松耦合设计"
2. "三大监控器：ProgressMonitor、PerformanceAnalyzer、ErrorTracker"
3. "JSONL 持久化：完整的事件日志，支持事后分析"
4. "插件式扩展：自定义监控器，集成外部系统"

**代码展示**:
- `devpal/core/schema/event_bus.py` - EventBus 核心
- `devpal/core/schema/eventbus_integration.py` - OpenSpec 集成
- 监控器实现示例

**亮点总结**:
- 📡 **事件驱动**: Pub-Sub 解耦，松耦合架构
- 📊 **可观测性**: 完整事件日志 + 实时监控
- 🔌 **可扩展**: 插件式监控器，易于集成外部系统
- 📈 **性能分析**: 自动生成性能报告，识别瓶颈
