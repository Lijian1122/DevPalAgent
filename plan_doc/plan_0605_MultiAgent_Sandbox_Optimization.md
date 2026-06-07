# 多 Agent 架构升级与沙箱环境限制优化技术方案

**文档版本**: 1.0  
**创建日期**: 2026-06-05  
**参考文档**: `plan_doc/plan_0525_MultiAgent_Benefits_Details.md`  
**适用项目**: DevPalAgent / OpenSpec 11 阶段运行时

---

## 1. 背景与目标

当前 DevPalAgent 已具备 Plan-Act-Reflect 主循环、OpenSpec 11 阶段工作流、EventBus、Checkpoint、Phase 4/5 并行执行、工具安全白名单与 Delta 写入能力。但现有 `MultiAgentSkill` 仍偏面试演示：Agent A/B/C 串行传递结果，没有独立 Agent 生命周期、任务队列、隔离工作区、权限策略、资源预算和可审计沙箱。

后续升级目标不是简单增加并发线程，而是把 DevPalAgent 从“单 Agent 调用工具”演进为“Coordinator 统一调度多个受限 Agent，在沙箱中执行可追踪任务”的架构。

核心目标：

1. 将多 Agent 能力嵌入 OpenSpec 主流程，而不是仅作为 Skill Demo。
2. 为每个 Agent 提供独立上下文、工作区、权限、资源预算和事件轨迹。
3. 使用沙箱限制文件、命令、网络、依赖安装、进程和敏感信息访问。
4. 复用现有 EventBus、Checkpoint、ParallelTask、ArtifactGraph、ValidationEngine 和 DeltaSpec。
5. 优先支持本地单机多 Agent，保留未来多进程/分布式扩展口。

---

## 2. 当前能力评估

### 2.1 已具备基础

| 能力 | 当前位置 | 可复用点 |
|---|---|---|
| OpenSpec 统一入口 | `devpal/core/openspec_executor.py` | `OpenSpecRunOptions.max_concurrency` 可作为 Agent 池规模入口 |
| 11 阶段调度 | `devpal/core/openspec_phases/enhanced_scheduler.py` | Phase 级别启停、重试、Checkpoint、EventBus 发事件 |
| 并行任务模型 | `devpal/core/openspec_phases/parallel_executor.py` | `ParallelTask` / `ParallelTaskResult` / 依赖分层执行 |
| EventBus | `devpal/core/schema/event_bus.py` | 事件发布、持久化、查询、重放 |
| 工具安全检查 | `devpal/tools/base.py` | 命令白名单、危险命令黑名单、敏感路径过滤 |
| 文件写入约束 | `devpal/tools/file_writer.py` | Delta 模式、路径检查、Diff 预览 |
| Phase 4/5 并发 | `phase4_generate_code.py`, `phase5_generate_tests.py` | 文件级任务并行、结果聚合、事件上报 |

### 2.2 主要缺口

1. `MultiAgentSkill` 是串行演示，没有 AgentPool、任务队列和调度器。
2. `PhaseParallelExecutor` 是线程池任务执行器，不理解 Agent 角色、权限和沙箱。
3. `ToolSecurity` 只有命令/路径粗粒度检查，没有按 Agent、Phase、工具、目录进行策略隔离。
4. `execute_command` 使用 `shell=True`，适合受控命令演示，但不适合作为多 Agent 沙箱边界。
5. 目前工作区共享，多个任务并发写文件时依赖路径检查和跳过逻辑，缺少临时 worktree/staging 区域与合并策略。
6. EventBus 已存在，但缺少 Agent 生命周期事件、沙箱事件、权限拒绝事件和资源超限事件。

---

## 3. 目标架构

```text
User / CLI
   |
AgentEngine
   |
OpenSpecWorkflowExecutor
   |
EnhancedOpenSpecScheduler
   |
MultiAgentCoordinator
   |---------------- EventBus ----------------|
   |                                          |
AgentPoolManager                         AuditStore
   |
   |-- AgentWorker(requirements) -- SandboxSession -- ToolProxy
   |-- AgentWorker(codegen) ------ SandboxSession -- ToolProxy
   |-- AgentWorker(test) --------- SandboxSession -- ToolProxy
   |-- AgentWorker(review) ------- SandboxSession -- ToolProxy
   |
ResultMerger / ArtifactGraph / ValidationEngine / DeltaSpec
```

设计原则：

1. Coordinator 是唯一调度中心，Agent 之间不直接通信。
2. Agent 不直接调用工具，必须通过 ToolProxy 做权限检查和审计。
3. Agent 不直接写主工作区，默认写 sandbox workspace 或 staging patch。
4. 所有任务、工具调用、拒绝、超时、重试、合并都写入 EventBus。
5. Phase 4/5 先落地文件级多 Agent，Phase 9/10 再引入 Review/Test Agent。

---

## 4. Agent 角色设计

| Agent 类型 | 职责 | 默认可用工具 | 写入范围 |
|---|---|---|---|
| RequirementAgent | 拆分需求、生成任务图、识别依赖 | file_reader, spec_tool | `.spec/`, `openspec/changes/` |
| DesignAgent | 生成技术设计、接口草案、依赖图 | file_reader, code_search | `docs/`, `openspec/changes/` |
| CodegenAgent | 按文件生成源码和头文件 | file_reader, file_writer | `src/`, `include/`, `tests/` staging |
| TestAgent | 生成测试、运行最小测试集 | test_generator, test_runner, execute_command | `tests/`, `docs/test_*` |
| ReviewAgent | 静态审查、质量门禁、风险标注 | code_review, static_analyzer | 只读，输出 report |
| FixAgent | 基于失败结果做局部修复 | auto_fixer, file_writer | 仅失败关联文件 |
| MergeAgent | 合并 patch、冲突检测、更新 ArtifactGraph | file_writer, spec_tool | 主工作区受控写入 |

首期不要一次性实现全部角色。建议先落地：CodegenAgent、TestAgent、ReviewAgent、MergeAgent。

---

## 5. 核心模块设计

### 5.1 MultiAgentCoordinator

职责：

1. 接收 Phase 传入的 `ParallelTask` 或 `AgentTask`。
2. 按任务类型选择 Agent 角色。
3. 向 AgentPool 申请 AgentWorker。
4. 创建 SandboxSession。
5. 收集 AgentResult 并交给 ResultMerger。
6. 将关键状态写入 Checkpoint。

建议接口：

```python
class MultiAgentCoordinator:
    def execute(self, tasks: list[AgentTask], policy: AgentPolicy) -> list[AgentResult]:
        ...
```

### 5.2 AgentPoolManager

职责：

1. 管理 AgentWorker 生命周期：idle、running、failed、cooldown。
2. 支持 `max_concurrency`、每角色并发上限和全局 LLM 调用预算。
3. 支持失败隔离：单个 Agent 崩溃只影响当前任务。
4. 支持后续扩展到多进程或远程 Worker。

首期可基于 `ThreadPoolExecutor` 实现，但接口不要绑定线程，方便未来替换为进程池或远程队列。

### 5.3 AgentTask / AgentResult

`AgentTask` 应扩展现有 `ParallelTask`：

```python
@dataclass
class AgentTask:
    task_id: str
    phase_number: int
    role: str
    task_type: str
    input_payload: dict
    dependencies: list[str]
    allowed_paths: list[str]
    allowed_tools: list[str]
    timeout_seconds: int
    token_budget: int | None
```

`AgentResult` 应保留产物、patch、事件、资源消耗和审计摘要：

```python
@dataclass
class AgentResult:
    task_id: str
    success: bool
    artifacts: list[Path]
    patch: str | None
    events: list[str]
    duration_ms: int
    error: str | None
    sandbox_id: str
    policy_violations: list[dict]
```

---

## 6. 沙箱限制设计

### 6.1 文件系统沙箱

建议采用三层目录：

```text
project_root/
  .spec/sandboxes/
    phase4_codegen_task_user_service/
      workspace/        # Agent 可写副本
      patches/          # 生成 patch
      logs/             # 工具调用和事件日志
      manifest.json     # 输入、输出、权限、哈希
```

限制规则：

1. Agent 默认只能读 project root 中允许的路径。
2. Agent 默认只能写自己的 sandbox workspace。
3. 写主项目必须通过 MergeAgent + DeltaSpec。
4. 禁止访问 `.env`、密钥、SSH、证书、系统目录和仓库外路径。
5. 所有输出文件必须记录 SHA256、来源 Agent、任务 ID 和 Phase。

### 6.2 命令沙箱

现有 `ToolSecurity.check_command_safety` 需要升级为策略化检查：

```yaml
sandbox_policy:
  command:
    shell: false
    allow:
      - python -m pytest
      - cmake --build
      - ctest
      - git diff
    deny_patterns:
      - rm -rf
      - curl
      - wget
      - ssh
      - scp
      - pip install
    timeout_seconds: 60
    max_output_kb: 512
```

优化点：

1. 避免 `shell=True`，优先使用参数数组执行。
2. 命令按 Phase 和 Agent role 白名单控制。
3. 禁止网络类命令，除非用户显式开启。
4. 对安装依赖、删除文件、修改 git 状态等高风险命令设置审批点。
5. stdout/stderr 截断并落盘，避免上下文污染。

### 6.3 网络沙箱

默认策略：多 Agent 执行阶段禁止网络访问。允许网络的场景必须显式声明，例如下载依赖、查询远程 API、调用外部 LLM Provider。

建议分级：

| 等级 | 网络能力 | 适用场景 |
|---|---|---|
| `none` | 禁止外部网络 | 默认代码生成、测试、审查 |
| `llm_only` | 仅允许 LLM API | 多 Agent 推理 |
| `allowlist` | 仅允许配置域名 | 依赖源、内部服务 |
| `open` | 不建议默认启用 | 人工确认后的特殊任务 |

### 6.4 资源沙箱

每个 AgentTask 应有资源预算：

1. wall time：默认 120 秒，测试任务可提高到 300 秒。
2. token budget：防止单任务无限生成。
3. retry limit：默认 1 次，LLM 瞬时失败可 2 次。
4. output size：单文件最大字节数、单任务最大产物数。
5. process count：禁止 Agent 启动长期后台进程。

---

## 7. 与 OpenSpec 阶段集成路线

### 阶段 A：抽象不破坏现有流程

1. 新增 `devpal/core/multi_agent/` 模块。
2. 定义 `AgentTask`、`AgentResult`、`AgentPolicy`、`SandboxSession`。
3. 保持 `PhaseParallelExecutor` 不变，先实现适配器：`ParallelTask -> AgentTask`。
4. `OpenSpecRunOptions` 增加 `enable_multi_agent`、`sandbox_level`、`agent_pool_size`。

### 阶段 B：Phase 4 文件级 CodegenAgent

1. 将 Phase 4 的 file plan 转换为多个 CodegenAgent 任务。
2. 每个任务生成单文件或强关联文件组。
3. Agent 输出 patch 到 sandbox。
4. MergeAgent 顺序合并 patch，使用 DeltaSpec 检查冲突。
5. ArtifactGraph 记录需求 ID 到文件的映射。

### 阶段 C：Phase 5/10 TestAgent

1. Phase 5 用 TestAgent 生成测试文档和测试文件。
2. Phase 10 用 TestAgent 在命令沙箱中运行 pytest/ctest。
3. 失败结果转为 FixAgent 的输入。
4. 测试命令必须绑定 timeout、cwd、输出限制和白名单。

### 阶段 D：Phase 9 ReviewAgent + LLM-as-Judge

1. ReviewAgent 并行检查 correctness、security、maintainability、traceability。
2. LLM-as-Judge 对冲突结论做裁决。
3. 高风险问题进入 FixAgent，低风险问题进入最终报告。
4. 质量门禁只读取合并后的主工作区，不读取未合并 sandbox。

### 阶段 E：分布式预留

1. 将 AgentPoolManager 接口从线程池抽象为 WorkerBackend。
2. 支持 local_thread、local_process、remote_queue 三种后端。
3. EventBus 后端从内存扩展到 Redis/RabbitMQ 时不影响 Phase API。

---

## 8. EventBus 事件扩展

新增事件类型：

| 事件 | 触发时机 | 关键字段 |
|---|---|---|
| `agent.started` | AgentWorker 启动 | agent_id, role, sandbox_id |
| `agent.task.assigned` | 任务分配 | task_id, phase, role |
| `agent.tool.requested` | 调用工具前 | tool, args_hash, policy_id |
| `agent.tool.denied` | 权限拒绝 | reason, rule_id, severity |
| `agent.sandbox.violation` | 越权访问 | path/command/network, action |
| `agent.task.completed` | 任务成功 | artifacts, duration, token_usage |
| `agent.task.failed` | 任务失败 | error, retry_count, recoverable |
| `agent.patch.merged` | patch 合并 | files_changed, conflicts |

这些事件应进入现有 EventBus 持久化日志，最终由 Phase 11 汇总到 final report。

---

## 9. 策略配置建议

新增配置文件可放在 `.spec/agent_policy.yaml` 或项目配置中：

```yaml
multi_agent:
  enabled: true
  pool_size: 4
  backend: local_thread
  sandbox_level: strict

roles:
  codegen:
    allowed_tools: [file_reader, file_writer]
    allowed_write_paths: [src/, include/, tests/]
    command_access: false
  test:
    allowed_tools: [file_reader, test_runner, execute_command]
    allowed_commands: [python -m pytest, ctest]
    timeout_seconds: 300
  review:
    allowed_tools: [file_reader, code_review, static_analyzer]
    write_access: false

merge:
  strategy: delta_spec
  require_validation: true
  conflict_policy: fail_fast
```

默认建议使用 `strict`：禁止网络、禁止 shell、禁止写仓库外路径、禁止直接改 git 状态。

---

## 10. 风险与优化策略

| 风险 | 表现 | 优化策略 |
|---|---|---|
| 并发写冲突 | 多个 Agent 修改同一文件 | sandbox patch + MergeAgent 串行合并 |
| 上下文不一致 | Agent 对需求理解不同 | RequirementAgent 先生成统一任务图和共享摘要 |
| 成本失控 | 多 Agent 重复调用 LLM | token budget、prompt caching、共享只读上下文 |
| 安全绕过 | Agent 构造危险命令 | ToolProxy 策略检查、禁用 shell、命令参数化 |
| 事件噪音 | 日志过多难分析 | 事件分级、Phase 11 摘要、原始日志落盘 |
| 调试复杂 | 失败来源不清 | sandbox manifest + task_id + event replay |

---

## 11. 验收指标

首期落地应满足：

1. Phase 4 在 10 个文件以上项目中执行时间降低 30% 以上。
2. 所有 Agent 写入都能追溯到 task_id、sandbox_id、phase_number。
3. 禁止路径逃逸：`../`、绝对路径、敏感文件访问全部被拒绝并记录事件。
4. 禁止危险命令：网络、删除、SSH、格式化、后台进程默认拒绝。
5. 单个 Agent 失败不导致整个 Phase 崩溃，除非关键任务无法恢复。
6. Checkpoint 恢复后不会重复合并已成功 patch。
7. Phase 11 能输出并发摘要、沙箱摘要、拒绝事件摘要和 Agent 成功率。

---

## 12. 推荐实施顺序

1. 先做接口层：`AgentTask`、`AgentResult`、`AgentPolicy`、`SandboxSession`。
2. 再做 ToolProxy：把工具调用统一纳入权限检查和审计。
3. 改造 Phase 4：用 CodegenAgent 替换直接线程任务执行。
4. 引入 MergeAgent：所有写主工作区的动作走 DeltaSpec 合并。
5. 改造命令执行：去掉默认 `shell=True` 路线，按 allowlist 参数化执行。
6. 扩展 EventBus：补齐 Agent、Sandbox、Policy、Merge 事件。
7. 最后推广到 Phase 5、Phase 9、Phase 10。

结论：DevPalAgent 已经有 EventBus、Checkpoint、ParallelTask 和 OpenSpec 11 阶段这些关键地基，后续多 Agent 优化的重点不是重写工作流，而是在现有并行执行之上增加 Agent 语义、沙箱边界、权限策略、审计事件和安全合并机制。这样既能保留当前 OpenSpec 稳定性，也能把项目叙事升级为“可治理的多 Agent SDLC Runtime”。
