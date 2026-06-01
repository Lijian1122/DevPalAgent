
### 3.2 Phase 层接入

[内容已在主文件中]

### 3.3 Tool 层接入

[内容已在主文件中]

### 3.4 LLM Client 接入

[内容已在主文件中]

---

## 4. 事件订阅者实现

[内容已在主文件中]

---

## 5. 实施计划

### 5.1 阶段 1: 核心事件定义（0.5 天）

**任务**:
1. 定义完整的事件类型枚举
2. 实现所有事件类
3. 增强 EventBus
4. 编写单元测试

**交付物**:
- `devpal/core/schema/events.py`
- `devpal/core/schema/event_bus.py`
- `tests/test_events.py`

### 5.2 阶段 2: Scheduler 接入（1 天）

**任务**:
1. EnhancedOpenSpecScheduler 初始化 EventBus
2. 发出工作流级别事件
3. 发出阶段级别事件
4. 发出 checkpoint 事件
5. 集成 EventLogger

**交付物**:
- 修改 `enhanced_scheduler.py`
- `.spec/events.jsonl` 事件日志

### 5.3-5.6 其他阶段

[详见主文档]

---

## 6. 配置与开关

```yaml
# config/features.yaml
features:
  eventbus_enabled: true
  event_logging: true
  event_monitoring: true
```

---

## 7. 使用示例

```python
# 基础使用
executor = OpenSpecWorkflowExecutor(tool_registry)
result = executor.run("requirements/login.md")
# 事件自动记录到 .spec/events.jsonl
```

---

## 8. 面试展示价值

### 8.1 技术亮点

1. **Event-Driven Architecture** - 解耦组件
2. **Observability** - 全链路追踪
3. **Extensibility** - 插件化监控
4. **Debugging** - 事件时间线
5. **Multi-Agent Foundation** - 智能体通信基础

### 8.2 演示场景

**实时进度监控**、**性能分析**、**事件时间线可视化**

---

## 9. 与多智能体架构集成

EventBus 为多智能体提供通信基础设施，支持：
- 智能体状态事件
- 工作项分配事件
- 协调器事件
- 实时监控

---

## 10. 总结

### 10.1 核心价值

1. 可观测性提升 - 全链路可追踪
2. 调试效率提升 - 快速定位问题
3. 性能优化基础 - 详细性能数据
4. 扩展性增强 - 插件化监控
5. 面试价值 - 展示架构设计能力

### 10.2 实施优先级

- **P3**: 可选优化
- **工期**: 3-4 天
- **依赖**: 无
- **风险**: 低

### 10.3 后续扩展

1. 分布式追踪 (OpenTelemetry)
2. 实时监控面板 (Web UI)
3. 告警系统
4. 事件回放
5. A/B 测试

---

**文档结束**
