# DevPal Agent v2.0 - 核心架构模型详解

## 目录

- [🔍 四层验证引擎 (ValidationEngine)](#-四层验证引擎-validationengine)
- [📦 Delta 增量变更引擎 (DeltaEngine)](#-delta-增量变更引擎-deltaengine)
- [🗺️ 工件依赖图 (ArtifactGraph)](#-工件依赖图-artifactgraph)
- [📢 事件总线架构 (EventBus)](#-事件总线架构-eventbus)
- [🔄 组件协同工作流程](#-组件协同工作流程)

---

## 🔍 四层验证引擎 (ValidationEngine)

**位置**: `devpal/core/schema/validation_engine.py`

四层验证引擎提供渐进式代码质量保障，每一层验证通过后才进入下一层。

### 验证流水线

```
┌─────────────────────────────────────────────────────────────────┐
│                        四层验证流水线                                │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: Format Validation (格式验证)                            │
│  ├─ JSON/YAML 语法检查                                             │
│  ├─ 代码缩进和格式规范                                              │
│  ├─ 文件编码检测 (UTF-8)                                            │
│  └─ 基础类型验证                                                    │
│                                                                   │
│  风险等级: 🟢 低 | 耗时: ~10ms                                      │
└─────────────────────────────┬───────────────────────────────────┘
                              │ PASS
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 2: Semantic Validation (语义验证)                         │
│  ├─ 逻辑矛盾检测 (if True: return False)                         │
│  ├─ 依赖完整性检查 (import 是否存在)                               │
│  ├─ 变量未定义检测                                                 │
│  └─ 死代码检测 (unreachable code)                                 │
│                                                                   │
│  风险等级: 🟡 中 | 耗时: ~50ms                                      │
└─────────────────────────────┬───────────────────────────────────┘
                              │ PASS
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 3: Parser Validation (解析验证)                           │
│  ├─ 函数签名兼容性检查                                             │
│  ├─ 方法是否存在 (obj.method())                                   │
│  ├─ 类型推断和类型检查                                             │
│  └─ API 调用合法性验证                                             │
│                                                                   │
│  风险等级: 🟡 中 | 耗时: ~100ms                                     │
└─────────────────────────────┬───────────────────────────────────┘
                              │ PASS
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 4: Business Validation (业务规则验证)                      │
│  ├─ 命名规范检查 (驼峰/下划线)                                      │
│  ├─ SQL 注入风险检测                                               │
│  ├─ XSS 跨站脚本检测                                               │
│  ├─ 敏感信息泄露检测 (密码/密钥)                                   │
│  └─ 业务逻辑一致性检查                                              │
│                                                                   │
│  风险等级: 🔴 高 | 耗时: ~200ms                                     │
└─────────────────────────────┬───────────────────────────────────┘
                              │ ALL PASS
                              ▼
                        ✅ 验证通过，允许应用变更
```

### 实际示例

```python
# Layer 2 失败示例：缺少 import
validation_result = validation_engine.pipeline.run(
    content="reset_token = secrets.token_urlsafe(32)",
    context={'file_path': 'auth_service.py'}
)
# 结果: Layer 2 FAIL - Missing import: secrets

# 自动修复后重新验证
fixed_code = "import secrets\n" + original_code
validation_result = validation_engine.pipeline.run(content=fixed_code)
# 结果: ALL PASS
```

### 优势

- ✅ 渐进式验证，快速失败 (fail-fast)
- ✅ 每层独立，易于扩展新规则
- ✅ 风险分级，高风险问题优先处理
- ✅ 自动修复建议，减少人工干预

---

## 📦 Delta 增量变更引擎 (DeltaEngine)

**位置**: `devpal/core/schema/delta_spec.py`

Delta 引擎实现增量变更而非全量覆盖，确保代码修改的原子性和可回滚性。

### Delta 变更流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                        Delta 变更流程图                            │
└─────────────────────────────────────────────────────────────────┘

原始文件 (main.cpp)
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: 加载原始内容                                             │
│  ├─ 读取文件内容                                                   │
│  ├─ 计算内容哈希 (SHA256)                                          │
│  └─ 记录原始行号映射                                                │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 2: 生成 Delta 操作序列                                       │
│  ├─ Delta 001: INSERT at line 10 (添加 #include <vector>)        │
│  ├─ Delta 002: MODIFY at line 25 (修改函数签名)                   │
│  ├─ Delta 003: DELETE at line 30 (删除废弃代码)                   │
│  └─ Delta 004: INSERT at line 45 (添加新函数)                     │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 3: 冲突检测                                                 │
│  ├─ 检查行号是否仍然有效                                           │
│  ├─ 检查上下文是否匹配                                             │
│  ├─ 检查是否有并发修改                                             │
│  └─ 生成冲突报告                                                   │
└─────────────────────────────┬───────────────────────────────────┘
                              │ NO CONFLICT
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 4: 验证 Delta                                               │
│  ├─ 运行四层验证引擎                                               │
│  ├─ 检查语法正确性                                                 │
│  ├─ 检查语义一致性                                                 │
│  └─ 检查业务规则                                                   │
└─────────────────────────────┬───────────────────────────────────┘
                              │ VALIDATION PASS
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 5: 逆序应用 Delta (关键！)                                  │
│  ├─ 从最后一个 Delta 开始应用 (Delta 004)                        │
│  ├─ 逆序应用避免行号偏移问题                                       │
│  ├─ 每个 Delta 原子应用                                            │
│  └─ 失败时自动回滚已应用的 Delta                                   │
└─────────────────────────────┬───────────────────────────────────┘
                              │ ALL APPLIED
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 6: 结果输出                                                 │
│  ├─ 写入修改后的文件                                               │
│  ├─ 计算新内容哈希                                                 │
│  ├─ 记录 Delta 应用历史                                           │
│  └─ 发布 DELTA_APPLIED 事件                                       │
└─────────────────────────────────────────────────────────────────┘
```

### 为什么逆序应用？

```cpp
// 原始文件 main.cpp (5行)
1: #include <iostream>
2: int main() {
3:     std::cout << "Hello\n";
4:     return 0;
5: }

// 需要应用两个 Delta:
// Delta 1: INSERT at line 2 → #include <vector>
// Delta 2: INSERT at line 4 → std::cout << "World\n";

// ❌ 正序应用会导致行号偏移:
// 应用 Delta 1 后，原来的 line 4 变成了 line 5
// Delta 2 的 line 4 指向错误位置

// ✅ 逆序应用避免行号偏移:
// 先应用 Delta 2 (line 4)，不影响 line 2
// 再应用 Delta 1 (line 2)，不影响已应用的 Delta 2
```

### 实际示例

```python
# 创建 Delta 规范
delta_spec = DeltaSpec("src/auth_service.py")
delta_spec.load_original()

# 生成 Delta
deltas = delta_spec.create_delta_from_diff(new_code)
# 输出: [Delta_001, Delta_002, Delta_003]

# 逆序应用
for delta in reversed(deltas):
    result = delta_spec.apply_single_delta(delta, dry_run=False)
    print(f"Applied {delta.id}: {result.status}")

# 输出:
# Applied Delta_003: SUCCESS
# Applied Delta_002: SUCCESS
# Applied Delta_001: SUCCESS
```

### 优势

- ✅ 增量变更，避免全量覆盖
- ✅ 冲突检测，防止并发修改
- ✅ 原子应用，失败自动回滚
- ✅ 逆序应用，避免行号偏移

---

## 🗺️ 工件依赖图 (ArtifactGraph)

**位置**: `devpal/core/schema/artifact_graph.py`

工件依赖图使用 NetworkX 构建代码、测试、文档、需求之间的依赖关系，支持影响范围分析。

### 依赖图架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        工件依赖图架构                              │
└─────────────────────────────────────────────────────────────────┘

需求文档 (requirements.md)
     │
     │ [需求定义]
     ▼
┌─────────────────────────────────────────────────────────────────┐
│  代码实现层                                                       │
│  ├─ src/auth_service.py                                          │
│  │   ├─ register_user()                                          │
│  │   ├─ login_user()                                             │
│  │   └─ reset_password()                                         │
│  │                                                               │
│  ├─ src/user_model.py                                            │
│  │   └─ User 类                                                  │
│  │                                                               │
│  └─ src/database.py                                              │
│      └─ Database 类                                              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              │ [实现关系]
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  测试代码层                                                       │
│  ├─ tests/test_auth.py                                           │
│  │   ├─ test_register_user()                                     │
│  │   ├─ test_login_user()                                        │
│  │   └─ test_reset_password()                                    │
│  │                                                               │
│  └─ tests/test_user_model.py                                     │
│      └─ test_user_creation()                                     │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              │ [测试覆盖]
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  文档层                                                           │
│  ├─ docs/api.md (API 文档)                                       │
│  ├─ docs/README.md (使用说明)                                     │
│  └─ docs/test_report.md (测试报告)                                │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              │ [文档描述]
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  配置层                                                           │
│  ├─ config.py (配置文件)                                          │
│  └─ .env (环境变量)                                               │
└─────────────────────────────────────────────────────────────────┘
```

### 依赖关系类型

```python
# 1. 代码依赖 (import)
artifact_graph.add_dependency(
    from_artifact="file:src/auth_service.py",
    to_artifact="file:src/user_model.py",
    dependency_type="import"
)

# 2. 测试覆盖 (test)
artifact_graph.add_dependency(
    from_artifact="file:tests/test_auth.py",
    to_artifact="file:src/auth_service.py",
    dependency_type="test"
)

# 3. 文档描述 (document)
artifact_graph.add_dependency(
    from_artifact="file:docs/api.md",
    to_artifact="file:src/auth_service.py",
    dependency_type="document"
)

# 4. 需求实现 (implement)
artifact_graph.add_dependency(
    from_artifact="file:src/auth_service.py",
    to_artifact="file:requirements.md",
    dependency_type="implement"
)
```

### 影响范围分析

```python
# 查询：修改 auth_service.py 会影响哪些文件？
affected = artifact_graph.get_affected_artifacts("file:src/auth_service.py")

# 输出:
# [
#   "file:tests/test_auth.py",        # 需要重新运行测试
#   "file:docs/api.md",                # 需要更新文档
#   "file:src/main.py"                 # 依赖此文件的代码
# ]

# 可视化依赖图
artifact_graph.visualize(output_path="dependency_graph.png")
```

### 实际示例

```python
# 场景：添加 reset_password 功能

# 1. 添加代码工件
artifact_graph.add_artifact(
    artifact_id="function:reset_password",
    artifact_type="function",
    metadata={
        'file': 'src/auth_service.py',
        'line': 45,
        'signature': 'reset_password(email: str) -> bool'
    }
)

# 2. 添加测试工件
artifact_graph.add_artifact(
    artifact_id="test:test_reset_password",
    artifact_type="test",
    metadata={
        'file': 'tests/test_auth.py',
        'line': 120
    }
)

# 3. 建立依赖关系
artifact_graph.add_dependency(
    from_artifact="test:test_reset_password",
    to_artifact="function:reset_password",
    dependency_type="test"
)

# 4. 影响分析
print(f"Total artifacts: {artifact_graph.graph.number_of_nodes()}")
print(f"Total dependencies: {artifact_graph.graph.number_of_edges()}")
```

### 优势

- ✅ 自动追踪代码、测试、文档的关联关系
- ✅ 修改代码前预测影响范围
- ✅ 确保测试覆盖完整性
- ✅ 支持依赖图可视化

---

## 📢 事件总线架构 (EventBus)

**位置**: `devpal/core/schema/event_bus.py`

事件总线实现发布-订阅模式，解耦各组件之间的通信。

### 事件总线架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        事件总线架构图                              │
└─────────────────────────────────────────────────────────────────┘

发布者 (Publishers)
     │
     ├─ DeltaEngine (发布 DELTA_APPLIED)
     ├─ ValidationEngine (发布 VALIDATION_COMPLETED)
     ├─ ToolRegistry (发布 TOOL_EXECUTED)
     └─ WorkflowExecutor (发布 WORKFLOW_PHASE_COMPLETED)
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│  EventBus 核心                                                    │
│  ├─ 事件队列 (PriorityQueue)                                      │
│  ├─ 订阅者注册表 (Dict[EventType, List[Callable]])                │
│  └─ 事件过滤器 (Filter by type/priority)                           │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  优先级队列处理                                                    │
│  ├─ Priority 1 (高): CONFLICT_DETECTED                            │
│  ├─ Priority 2 (中): VALIDATION_COMPLETED                         │
│  └─ Priority 3 (低): TOOL_EXECUTED                                 │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  事件分发 (Dispatch)                                              │
│  ├─ 查找订阅者列表                                                 │
│  ├─ 按注册顺序调用                                                 │
│  └─ 异常隔离 (一个订阅者失败不影响其他)                             │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
订阅者 (Subscribers)
     │
     ├─ Logger (记录所有事件)
     ├─ CompileDB (更新符号索引)
     ├─ ArtifactGraph (更新依赖图)
     ├─ StateManager (创建快照)
     └─ TestRunner (触发测试)
```

### 7种标准事件类型

```python
class EventType(Enum):
    TOOL_EXECUTED = "tool_executed"                  # 工具执行完成
    VALIDATION_COMPLETED = "validation_completed"      # 验证完成
    DELTA_APPLIED = "delta_applied"                 # Delta 应用完成
    ARTIFACT_CHANGED = "artifact_changed"              # 工件变更
    SNAPSHOT_CREATED = "snapshot_created"              # 快照创建
    CONFLICT_DETECTED = "conflict_detected"            # 冲突检测
    WORKFLOW_PHASE_COMPLETED = "workflow_phase_completed"  # 工作流阶段完成
```

### 实际示例

```python
# 初始化事件总线
event_bus = EventBus()

# 订阅者 1: 日志记录器
def log_handler(event: Event):
    print(f"[LOG] {event.type.value}: {event.data.get('message', '')}")
    with open("devpal.log", "a") as f:
        f.write(f"{datetime.now()} - {event.type.value}\n")

event_bus.subscribe(EventType.TOOL_EXECUTED, log_handler)
event_bus.subscribe(EventType.DELTA_APPLIED, log_handler)

# 订阅者 2: CompileDB 更新器
def compile_db_handler(event: Event):
    if event.type == EventType.DELTA_APPLIED:
        file_path = event.data.get("file_path")
        compile_db.index_file(Path(file_path))
        print(f"[CompileDB] Indexed {file_path}")

event_bus.subscribe(EventType.DELTA_APPLIED, compile_db_handler)

# 订阅者 3: 快照管理器
def snapshot_handler(event: Event):
    if event.type == EventType.WORKFLOW_PHASE_COMPLETED:
        phase = event.data.get("phase")
        if phase in ["Phase 3", "Phase 5", "Phase 9"]:
            state_manager.create_snapshot(f"after_{phase}")
            print(f"[Snapshot] Created snapshot after {phase}")

event_bus.subscribe(EventType.WORKFLOW_PHASE_COMPLETED, snapshot_handler)

# 发布事件
event_bus.publish(Event(
    type=EventType.DELTA_APPLIED,
    data={
        'file_path': 'src/auth_service.py',
        'delta_count': 3,
        'message': 'Applied 3 deltas to auth_service.py'
    }
))

# 输出:
# [LOG] delta_applied: Applied 3 deltas to auth_service.py
# [CompileDB] Indexed src/auth_service.py
```

### 优势

- ✅ 解耦组件，发布者和订阅者互不依赖
- ✅ 可扩展，新增订阅者无需修改现有代码
- ✅ 异步处理，事件可以触发多个处理器
- ✅ 优先级队列，高优先级事件优先处理
- ✅ 异常隔离，一个订阅者失败不影响其他

---

## 🔄 组件协同工作流程

### 完整示例：添加密码重置功能

```
用户请求: "Add password reset functionality"
     │
     ▼
[1] Executor.Planner 生成计划
     │
     ▼
[2] DeltaEngine 创建 Delta
     │
     ▼
[3] ValidationEngine 四层验证
     │ PASS
     ▼
[4] DeltaEngine 逆序应用 Delta
     │
     ▼
[5] EventBus 发布 DELTA_APPLIED 事件
     │
     ├─► [CompileDB] 更新符号索引
     ├─► [ArtifactGraph] 更新依赖图
     └─► [Logger] 记录日志
     │
     ▼
[6] EventBus 发布 WORKFLOW_PHASE_COMPLETED 事件
     │
     └─► [StateManager] 创建快照
     │
     ▼
[7] Executor.Reflector 自我检查
     │
     ▼
✅ 完成
```

### 数据流示例

```python
# 1. 生成代码
new_code = generate_reset_password_function()

# 2. 创建 Delta
delta_spec = DeltaSpec("src/auth_service.py")
deltas = delta_spec.create_delta_from_diff(new_code)

# 3. 四层验证
validation_result = validation_engine.pipeline.run(
    content=new_code,
    context={'file_path': 'src/auth_service.py'}
)

if not validation_result.passed:
    # 自动修复
    fixed_code = auto_fix(new_code, validation_result.issues)
    validation_result = validation_engine.pipeline.run(content=fixed_code)

# 4. 应用 Delta (逆序)
for delta in reversed(deltas):
    delta_spec.apply_single_delta(delta, dry_run=False)

# 5. 发布事件
event_bus.publish(Event(
    type=EventType.DELTA_APPLIED,
    data={'file_path': 'src/auth_service.py', 'delta_count': len(deltas)}
))

# 6. 更新依赖图
artifact_graph.add_artifact(
    artifact_id="function:reset_password",
    artifact_type="function"
)

# 7. 影响分析
affected = artifact_graph.get_affected_artifacts("file:src/auth_service.py")
print(f"Affected files: {affected}")

# 8. 创建快照
snapshot = state_manager.create_snapshot("after_password_reset")
state_manager.save_snapshot(snapshot)
```

### 协同优势

- ✅ 自动化流程，从需求到部署全自动
- ✅ 实时验证，每个步骤都有质量保证
- ✅ 可追溯性，EventBus 记录所有操作
- ✅ 可回滚性，StateManager 支持任意时间点回滚
- ✅ 影响分析，ArtifactGraph + CompileDB 预测变更影响
- ✅ 自我修复，Reflector 发现问题并自动修复

---

## 相关文档

- [Core_Engine_Implementation_Guide.md](./Core_Engine_Implementation_Guide.md) - 核心引擎实现详解
- [Anti_Hallucination_Architecture_v2.0.md](./Anti_Hallucination_Architecture_v2.0.md) - v2.0 防幻觉架构

---

**文档维护**: DevPal Agent 开发团队  
**最后更新**: 2026-05-11  
**版本**: v2.0
