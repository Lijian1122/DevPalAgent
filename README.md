
# DevPalAgent

> Spec-first Agentic SDLC Runtime：把需求文档转成可验证、可追踪、可自愈的软件项目。

DevPalAgent 不是普通聊天机器人，也不是一次性代码生成脚本。它把 LLM 放进一个确定性的工程流水线中：需求先被解析成结构化规范，然后经过阶段化设计、**多智能体并行代码生成**、质量门禁、测试执行、报告归档和 checkpoint 恢复，最终形成一个可审查的软件交付包。

当前项目重点方向：**OpenSpec-inspired Spec-Driven Development + Multi-Agent Workflow + 自动化验证闭环**。
---

## 1. 项目定位

DevPalAgent 面向 AI Coding / Agentic Engineering 场景，目标是解决 LLM 写代码时常见的几个问题：

| 问题 | DevPalAgent 的解决方式 |
|---|---|
| LLM 直接写代码不可控 | 使用 11 阶段 OpenSpec workflow 包裹 LLM 输出 |
| 顺序生成效率低下 | Phase 4/5 支持文件级并行，Phase 4/9/10 可选本地多 Agent 执行 |
| 需求、代码、测试难追踪 | 使用 structured requirements、ArtifactGraph、coverage matrix、final report |
| 生成结果无法验证 | Phase 9 Quality Gate + Phase 10 测试执行 |
| 长流程失败难恢复 | checkpoint/resume + phase result 持久化 |
| 多语言上下文错配 | language-aware Phase 2/9/10/11 + Prompt Engine |
| skipped 与 passed 混淆 | 明确记录 skipped/test_skipped/test_summary |
| 生成错误需要人工修 | 自愈与 fallback model 机制逐步接入 |
| 大项目生成慢 | 文件计划拆分 + 并发控制 + 可审计 sandbox manifest |

一句话概括：

```text
DevPalAgent = Spec-first workflow + phase parallelism + optional sandboxed multi-agent execution + Quality gate + Traceable reports
```

---

## 2. 架构总览

DevPalAgent 不是单一的"问答式 Agent"，而是由两条互补执行链组成：

1. **经典 Agent 链路**：面向交互式开发任务，采用 `Planner → Executor → Reflector` 的 Plan-Act-Reflect 模式。
2. **OpenSpec Runtime 链路**：面向从需求到项目交付的端到端生成，采用 `WorkflowExecutor → Scheduler → Context → Phase 1-11` 的确定性流水线，**其中 Phase 4/5 支持多智能体并行执行**。

### 2.1 总体分层

```text
┌───────────────────────────────────────────────────┐
│          User / CLI / Web              │
│        chat request / requirements.md / explicit command             │
└────────────────────────┬─────────────────────┘
                   │
        ┌────────────────────┴──────────────────┐
        │                              │
     ▼                                 ▼
┌────────────────┐                  ┌────────────┐
│ AgentEngine           │                    │ OpenSpecWorkflow      │
│ interactive agent     │                │ spec-first runtime    │
└──────────┬───────────┘                    └──────────┬───────────┘
           │                                      │
           ▼                                ▼
┌─────────────────┐              ┌────────────────┐
│ Planner              │               │ OpenSpecExecutor      │
│ task planning        │                         │ workflow facade       │
└────────┬────────┘                 └──────────┬───────────┘
           │                        │
           ▼                                             ▼
┌──────────────────────┐                 ┌────────────────────┐
│ Executor             │                     │ EnhancedScheduler     │
│ tool execution       │               │ retry/checkpoint    │
└──────┬───────────┘                       └──────────┬───────────┘
           │                                        │
           ▼                          ▼
┌────────────────┐                       ┌──────────────┐
│ ToolRegistry         │                   │ OpenSpecContext       │
│ file/git/test/etc.   │              │ shared phase state    │
└──────────┬───────────┘             └──────────┬───────────┘
           │                                   │
        ▼                                         ▼
┌───────────────────┐                       ┌──────────────────────┐
│ Reflector            │                     │ Phase 1-11            │
│ verify & improve     │                 │ spec→code→test→report│
└──────────┬───────────┘                   └──────────┬───────────┘
           │                                      │
           │                          ┌───────────┴───────────┐
           │                        │                   │
           │                                  ▼                       ▼
           │                     ┌──────────────────┐   ┌──────────────────┐
           │               │ Phase 4/5        │   │ Other Phases     │
      │                    │ Multi-Agent Pool │   │ Sequential       │
           │                      └──────────────────┘   └──────────────────┘
           │                      │
           └──────────────────┬──────────┘
                       ▼
┌───────────────────────────────────────────┐
│ Core engines: ValidationEngine / DeltaSpec / ArtifactGraph / EventBus│
│ LLM client / PromptEngine / Templates / Language plugins / Memory    │
│ Multi-Agent: Coordinator / LocalThreadBackend / SandboxSession        │
└───────────────────────────────────────────────────┘
```

### 2.2 多智能体架构（当前实现）

OpenSpec Runtime 在确定性 11 阶段主流程内提供**可选的本地多 Agent 执行路径**，当前重点接入 Phase 4/9/10：

```text
Phase 4/9/10
    ↓
MultiAgentCoordinator
    ↓
LocalThreadBackend / PhaseParallelExecutor
    ↓
CodegenAgent / ReviewAgent / TestAgent
    ↓
SandboxSession(path + command policy)
    ↓
workspace artifact / manifest → merge / report
```

**当前已落地能力**:
- **文件级并发**: Phase 4/5 使用 `PhaseParallelExecutor` 拆分文件任务并聚合结果。
- **可选多 Agent**: `--enable-multi-agent` 后，Phase 4 可用 CodegenAgent，Phase 9 可用 ReviewAgent，Phase 10 可用 TestAgent。
- **沙箱策略**: `SandboxSession` 限制写入根目录、精确 allowed paths、命令 argv/cwd/CMake 路径，并拒绝 shell/network/destructive 命令。
- **审计产物**: 每个 sandbox task 可写入 `.spec/sandboxes/<sandbox_id>/manifest.json`，Phase 11 汇总 sandbox id、manifest 和 policy violation。
- **Production merge**: `--sandbox-level production` 下不会自动写主工作区，而是生成 `merge_pending` manifest；使用 `python -m devpal.openspec merge-sandbox <manifest> --apply` 显式合并。
- **Fallback**: 多 Agent 或并行任务失败时回退到现有 phase-local 执行路径。

性能收益依赖文件数量、LLM 延迟和依赖图形状；README 不固定承诺倍数，实际以 final report 的 parallel summary 和 benchmark 为准。

详细设计见：
- [plan_doc/plan_0525_Phase4_5_MultiAgent_Architecture.md](plan_doc/plan_0525_Phase4_5_MultiAgent_Architecture.md)
- [plan_doc/plan_0525_MultiAgent_Benefits_Details.md](plan_doc/plan_0525_MultiAgent_Benefits_Details.md)
- [plan_doc/plan_0525_MultiAgent_Impact_Analysis.md](plan_doc/plan_0525_MultiAgent_Impact_Analysis.md)

### 2.3 Plan-Act-Reflect 架构模式

经典 Agent 链路用于普通代码任务、测试编排、自我改进、代码审查等交互场景。它的核心不是一次性调用工具，而是把任务拆成"规划、执行、反思"的闭环。

```text
User request
   │
   ▼
Planner
   ├─ 解析用户意图
   ├─ 判断任务类型：开发 / 测试 / 审查 / 自改进 / OpenSpec
   ├─ 拆解步骤和工具依赖
   └─ 输出执行计划
   │
   ▼
Executor
   ├─ 路由到 ToolRegistry 或 TestOrchestrator
   ├─ 准备工具参数
   ├─ 执行文件、命令、Git、测试、编译、审查等工具
   └─ 收集结构化结果
   │
   ▼
Reflector
   ├─ 判断结果是否满足目标
   ├─ 识别失败原因和下一步动作
   ├─ 必要时触发重新规划或修复
   └─ 写入经验/错误记忆
```

三个核心角色的职责：

| 角色 | 位置 | 职责 |
|---|---|---|
| Planner | `devpal/core/planner.py` | 任务分类、步骤拆解、可行性检查、工具选择建议 |
| Executor | `devpal/core/agent_engine.py` | 执行计划、调用工具、汇总结果、处理异常 |
| Reflector | `devpal/core/reflector.py` | 验证执行结果、分析失败、给出修复或重试建议 |
| ToolRegistry | `devpal/tools/registry.py` | 注册并分发所有工具能力 |
| Memory | `devpal/memory/` | 保存短期上下文、长期偏好、错误模式 |

### 2.4 OpenSpec Runtime 架构模式

OpenSpec 链路用于"需求文档 → 软件项目"的完整交付。它把 LLM 生成放进可恢复、可验证、可追踪的工程流程，而不是让模型直接写一堆文件。

```text
requirements.md
   │
   ▼
OpenSpecWorkflowExecutor
   │  创建运行上下文和调度器
   ▼
EnhancedOpenSpecScheduler
   │  timeout / retry / checkpoint / resume / progress / success policy
   ▼
OpenSpecContext
   │  requirements / structured_requirements / language / project_type
   │  phase_results / generated_files / artifact_graph / test counters
   │  agent_pool_config / agent_pool_stats (新增)
   ▼
Phase 1-11
   │  parse → structure → design → **multi-agent code** → tests → build → docs
   │  → quality gate → run tests → final report
   ▼
Deliverables
   │  source files / tests / README / quality report / final report / CLAUDE.md
```

运行时分层：

| 层级 | 代表模块 | 作用 |
|---|---|---|
| Workflow Facade | `openspec_executor.py`、`openspec_workflow.py` | 对外提供统一的 OpenSpec 执行入口 |
| Scheduler | `enhanced_scheduler.py`、`scheduler.py` | 阶段调度、重试、超时、checkpoint、恢复 |
| Shared State | `base.py`、`openspec_context.py` | `OpenSpecContext`、`PhaseResult`、成功策略、阶段产物 |
| Phase Layer | `openspec_phases/phase*.py` | 11 阶段需求解析、生成、验证、测试、报告 |
| **Multi-Agent Layer** | `multi_agent/coordinator.py`、`backend.py`、`sandbox.py` | Phase 4/9/10 的可选本地多 Agent 执行与审计 |
| Intelligence Layer | `llm_client.py`、`prompt_engine.py`、`templates/` | LLM 调用、动态 Prompt、语言/项目模板 |
| Verification Layer | `validation_engine.py`、`phase9_quality_gate.py`、`phase10_run_tests.py` | 四层质量门禁、测试执行、编译/pytest/shell 检查 |
| Traceability Layer | `artifact_graph.py`、`delta_spec.py`、`requirements.py` | 需求、代码、测试、报告之间的关系追踪 |
| Reporting Layer | `phase11_final_report.py` | final report、ArtifactGraph、CLAUDE.md、测试摘要 |

### 2.5 核心数据流

```text
输入需求
  │
  ├─ Phase 1: requirements_content / structured_requirements / delta.json
  │
  ├─ Phase 2: project structure / .spec/requirements.json
  │
  ├─ Phase 3: design
  │
  ├─ Phase 4: **文件级并行 / 可选多 Agent 代码生成**
  │     ├─ 依赖解析 → 分阶段
  │     ├─ LocalThreadBackend / PhaseParallelExecutor 执行
  │     └─ 结果聚合
  │
  ├─ Phase 5: **并行测试/文档生成**
  │
  ├─ Phase 6-8: build config / test docs / README
  │
  ├─ Phase 9: quality_gate_report + validation issues
  │
  ├─ Phase 10: test_result / test_summary / passed-failed-skipped counters
  │
  └─ Phase 11: final_report / artifact_graph / CLAUDE.md
```

这条数据流里，`OpenSpecContext` 是所有阶段的状态总线，`ArtifactGraph` 负责记录工件关系，`ValidationEngine` 负责质量判断，`PhaseResult` 负责把每个阶段的成功、失败、跳过原因持久化。当前多 Agent 路径由 `MultiAgentCoordinator`、`LocalThreadBackend`、`CodegenAgent`、`ReviewAgent`、`TestAgent` 和 `SandboxSession` 组成；性能收益以 benchmark 和 final report 为准，不固定承诺倍数。

更详细的架构说明见：

- [doc3.0/agent_architecture.md](doc3.0/agent_architecture.md)
- [doc3.0/e2e_demo.md](doc3.0/e2e_demo.md)
- [doc3.0/interview_pitch.md](doc3.0/interview_pitch.md)

---

## 3. 核心模块

### 3.1 Agent 主引擎与 Plan-Act-Reflect

| 文件 | 说明 |
|---|
| `devpal/core/agent_engine.py` | 交互式 Agent 主引擎，负责接收用户任务、组织 Planner/Executor/Reflector 链路 |
| `devpal/core/planner.py` | 规划器：解析意图、识别任务类型、拆分步骤、选择候选工具 |
| `devpal/core/reflector.py` | 反思器：检查执行结果、分析错误、判断是否需要重试或调整计划 |
| `devpal/memory/memory_manager.py` | 记忆管理入口，协调短期记忆、长期记忆、错误记忆 |
| `devpal/memory/short_term.py` | 对话级上下文和近期任务状态 |
| `devpal/memory/long_term.py` | 用户偏好、历史经验、稳定知识 |
| `devpal/memory/error_memory.py` | 错误模式和修正经验，服务 Reflector 的复盘过程 |

### 3.2 OpenSpec Workflow / Scheduler / Context

| 文件 | 说明 |
|---|---|
| `devpal/core/openspec_executor.py` | OpenSpec workflow facade，对外提供统一执行入口 |
| `devpal/core/openspec_workflow.py` | OpenSpec 工作流封装，连接 Agent 与 11 阶段流水线 |
| `devpal/core/openspec_phases/enhanced_scheduler.py` | 增强调度器，负责 checkpoint、resume、retry、timeout、progress |
| `devpal/core/openspec_phases/scheduler.py` | 基础调度器实现 |
| `devpal/core/openspec_phases/base.py` | `OpenSpecContext`、`PhaseResult`、阶段基类、success policy |
| `devpal/core/openspec_context.py` | 旧版/兼容 OpenSpec 上下文管理能力 |
| `devpal/core/openspec_phases/phase_skip_rules.py` | 按语言和项目类型判断阶段是否应该跳过 |
| `devpal/core/openspec_phases/logger.py` | 工作流日志输出和阶段状态记录 |

### 3.3 多智能体核心模块（新增）

| 文件 | 说明 |
|---|---|
| `devpal/core/multi_agent/coordinator.py` | Phase 协调器基类，负责多智能体执行编排 |
| `devpal/core/multi_agent/backend.py` | 本地线程后端，复用 `PhaseParallelExecutor` |
| `devpal/core/multi_agent/models.py` | `AgentTask`、`AgentResult`、`AgentPolicy`、命令模型 |
| `devpal/core/multi_agent/sandbox.py` | 路径/命令策略、workspace、manifest 和 sandbox level |
| `devpal/core/multi_agent/codegen_agent.py` | 代码生成智能体（Phase 4） |
| `devpal/core/multi_agent/review_agent.py` | 代码审查智能体（Phase 9） |
| `devpal/core/multi_agent/test_agent.py` | 测试执行智能体（Phase 10） |
| `devpal/core/multi_agent/adapters.py` | Phase parallel task 与 Agent task/result 的适配 |
| `devpal/core/multi_agent/content_sanitizer.py` | 生成内容清洗与安全检查 |

**配置文件**:
- CLI 参数：`--enable-multi-agent`、`--agent-pool-size`、`--sandbox-level`
- 当前后端：`local`，主要通过 `AgentPolicy` 和 `OpenSpecContext` 传递运行策略

### 3.4 OpenSpec 11 阶段实现

| Phase | 文件 | 核心职责 |
|---:|---|---|
| 1 | `phase1_parse_requirements.py` | 解析需求文本，提取 structured requirements、project_type、language、features，输出 `.spec/delta.json` |
| 2 | `phase2_create_structure.py` | 创建语言感知目录结构，写入 `.spec/requirements.json` |
| 3 | `phase3_technical_design.py` | 生成技术设计，可根据 installer/tooling 等项目类型跳过 |
| 4 | `phase4_generate_code.py` | 文件级并行 / 可选 CodegenAgent 生成核心代码 |
| 5 | `phase5_generate_tests.py` | 并行生成测试文件和测试文档 |
| 6 | `phase6_cmake_config.py` | 生成 CMake/build 配置，非 C++ 项目可跳过 |
| 7 | `phase7_test_docs.py` | 生成或补充测试文档 |
| 8 | `phase8_readme.py` | 生成目标项目 README |
| 9 | `phase9_quality_gate.py` | 执行语言感知四层质量门禁，输出 quality gate report |
| 9b | `phase9_code_review.py` | 代码审查型质量检查扩展 |
| 10 | `phase10_run_tests.py` | 执行 C++/Python/Shell 测试，维护 canonical test counters 和 skipped 语义 |
| 11 | `phase11_final_report.py` | 生成 final report、ArtifactGraph、CLAUDE.md 和最终交付摘要 |

### 3.5 Spec、验证与可追踪核心模型

| 模块 | 文件 | 说明 |
|---|---|---|
| ValidationEngine | `devpal/core/schema/validation_engine.py` | 四层验证：格式、语义、解析、业务规则；Phase 9 的核心质量模型 |
| DeltaSpec | `devpal/core/schema/delta_spec.py` | 增量变更模型，负责描述变更、冲突检测、原子应用能力基础 |
| ArtifactGraph | `devpal/core/schema/artifact_graph.py` | 工件依赖图，追踪 requirements、source、tests、docs、reports 的关系 |
| EventBus | `devpal/core/schema/event_bus.py` | 发布-订阅事件总线，用于解耦工具、验证、工件变化和工作流事件 |
| Requirements | `devpal/core/schema/requirements.py` | 需求结构模型和需求文档管理能力 |
| Workflow Schema | `devpal/core/schema/workflow.py` | 声明式 workflow/schema 能力 |
| Spec Engine | `devpal/core/schema/spec.py` | Spec 核心抽象，支撑规范优先开发模型 |
| DiagnosticEngine | `devpal/core/schema/diagnostic_engine.py` | 诊断引擎，用于结构化分析错误和运行状态 |
| CompileDB | `devpal/core/schema/compile_db.py`、`devpal/core/compiledb/` | 编译数据库解析与编译上下文支持 |

四层验证模型：

| 层级 | 关注点 | 示例 |
|---|---|---|
| L1 Format | 基础格式和语法 | Python AST、Shell 语法、C++ 文件结构 |
| L2 Semantic | 语义一致性 | 依赖完整性、明显逻辑矛盾、死代码 |
| L3 Parser | 可解析与接口匹配 | 函数签名、导入、调用关系 |
| L4 Business | 业务和安全规则 | 命名约束、敏感信息、注入风险、项目特定规则 |

---

## 4. 当前能力状态

### 4.1 已完成能力

| 能力 | 状态 | 说明 |
|---|---:|---|
| OpenSpec 11 阶段流水线 | ✅ | Phase 1-11 已实现 |
| **多智能体并行执行** | ✅ MVP | Phase 4 可选 CodegenAgent，Phase 9/10 可选 Review/Test Agent；并发度由 CLI 控制 |
| **依赖解析与调度** | ✅ | 文件计划支持依赖分阶段执行，底层使用 `PhaseParallelExecutor` |
| **故障隔离与恢复** | ✅ MVP | sandbox manifest、路径/命令策略、fallback 事件和 final report 汇总；非容器级隔离 |
| Enhanced Scheduler | ✅ | timeout / retry / checkpoint / progress |
| Structured Requirements | ✅ | 解析 id/title/description/acceptance/scenarios/priority/status |
| Delta JSON | ✅ | Phase 1 输出 `.spec/delta.json` |
| ArtifactGraph | ✅ | 需求、代码、测试、报告关系追踪 |
| Prompt Engine | ✅ | 按语言动态生成 Phase 3/4 prompt |
| 多语言基础能力 | ✅ | C++ / Python / Shell 配置与插件雏形 |
| Phase Skip Rules | ✅ | installer/tooling 跳过不适用阶段 |
| Phase 9 Quality Gate | ✅ | 四层验证，按语言选择检查器 |
| Phase 10 Test Runner | ✅ | C++ 测试、Python pytest、skipped 语义 |
| Phase 11 Final Report | ✅ | 生成 final_report、artifact_graph、CLAUDE.md |
| CLAUDE.md 输出 | ✅ | 当前已语言感知 |

### 4.2 当前阶段

项目已完成 `M1：语言感知闭环稳定版` + `M2：多智能体并行执行`：

- Phase 2 目录结构语言感知
- Phase 4/5 多智能体并行执行（可配置开关）
- Phase 9 Python/installer 不再跑 C++ 检查
- Phase 10 Python pytest 写入 canonical test counts
- Phase 11 / CLAUDE.md 语言感知
- installer 项目不再显示 `0/0 passed`
- **多智能体架构完整设计文档**

---

## 5. OpenSpec 11 阶段工作流

DevPalAgent 的核心执行流：

```text
Phase 1  Parse Requirements
Phase 2  Create Project Structure
Phase 3  Generate Technical Design
Phase 4  **Multi-Agent Code Generation** (并行)
Phase 5  **Multi-Agent Code Review** (并行)
Phase 6  Configure Build System
Phase 7  Generate Test Documentation
Phase 8  Generate README
Phase 9  Quality Gate
Phase 10 Run Tests / Compile / Update Docs
Phase 11 Final Report
```

### 5.1 阶段职责

| Phase | 名称 | 主要输出 | 并行支持 |
|---:|---|---|---|
| 1 | Parse Requirements | `requirements_content`、`structured_requirements`、`requirements_delta`、`.spec/delta.json` | - |
| 2 | Create Structure | 项目目录、`.spec/requirements.json` | - |
| 3 | Technical Design | `tech_design_content`，可按项目类型跳过 | - |
| 4 | Code Generation | infra templates + AI business code | **✅ 多智能体** |
| 5 | Test Generation | 测试文档/测试代码，可按项目类型跳过 | **✅ 多智能体** |
| 6 | Build Config | CMake 等构建配置，可按语言跳过 | - |
| 7 | Test Docs | 测试文档补充，可跳过 | - |
| 8 | README | 项目 README | - |
| 9 | Quality Gate | 四层验证 + 代码审查 + 自愈入口 | - |
| 10 | Run Tests | C++/Python/Shell 测试执行或 skipped | - |
| 11 | Final Report | final report、ArtifactGraph、CLAUDE.md | - |

### 5.2 多智能体执行流程

**Phase 4 代码生成**:
```text
1. 依赖解析 → 分阶段 (models → services → api)
2. 每个阶段内并行执行
3. 智能体池动态分配
4. 实时进度追踪
5. 结果聚合与验证
```

**配置示例**:
```yaml
# config/agent_pool.yaml
phase4_code_generation:
  pool_size: 4  # 4 个并行智能体
  timeout_seconds: 300
  retry_policy:
    max_retries: 3
    backoff_multiplier: 2
```

---

## 5.5 Archive + Traceability Lifecycle

After OpenSpec execution completes, you can archive the change to maintain long-term traceability:
```bash
# Archive a change
python -m devpal.openspec archive <change-id> --project-dir <path>
```

**What archiving does:**
1. Merges change spec into `openspec/specs/main.md`
2. Updates change status to `ARCHIVED`
3. Generates coverage matrix (Requirement → Code → Test → Report)
4. Updates ArtifactGraph with archive metadata
5. Creates archive manifest in `.spec/archive/<change-id>.json`

**Traceability chain:**
```
Requirement (REQ-001)
    ↓ implements
Code (src/feature.cpp)
    ↓ tests
Test (tests/test_feature.cpp)
    ↓ documents
Report (docs/final_report.md)
```

All connections are preserved in ArtifactGraph and coverage matrix.

**See:** [doc3.0/archive_lifecycle.md](doc3.0/archive_lifecycle.md) for complete documentation.

---

## 5.6 AI-agnostic 协作模式

DevPalAgent 支持与外部 AI coding 工具（Claude Code, Cursor, Cline）进行 Spec-first 协作，实现多工具协同开发。

### 三种协作模式

| 模式 | Phase 范围 | 用途 | 输出 |
|----|------|------|------|
| **PROPOSE_ONLY** | 1-3 | 生成 OpenSpec Change artifacts，不修改代码 | proposal, tasks, design, spec + Rule Pack |
| **APPLY_ONLY** | 4-11 | 基于已有 Change 执行代码实现 | 完整的代码、测试、报告 |
| **VALIDATE_ONLY** | 9-11 | 仅对已有实现进行质量验证 | 质量报告、测试结果 |

### 使用示例

## 模式1: Propose-only（规划模式）
生成 OpenSpec Change，供外部 AI 工具使用：

```bash
python run_ai_flow.py -r requirements/feature.md --propose-only
```

**输出**：
- `openspec/changes/<change-id>/` 目录包含：
  - `proposal.md` - 功能提案
  - `tasks.md` - 任务清单
  - `design.md` - 技术设计
  - `specs/spec.md` - 详细规格
  - `metadata.json` - Change 元数据
- **Rule Pack 文件**：
  - `CLAUDE.md` - Claude Code 协作规则（更新 Spec-first 章节）
  - `.cursorrules` - Cursor 集成规则
  - `cline-rules.md` - Cline 集成规则

#### 模式2: Apply-only（实施模式）
基于已有 Change 执行代码生成和验证：

```bash
python run_ai_flow.py --apply-change feature-login-20260604_120000
```

**行为**：
- 加载并恢复 Change artifacts
- 执行 Phase 4-11（代码生成、测试、验证、报告）
- 跳过 Phase 1-3（已通过 propose-only 完成）

#### 模式3: Validate-only（验证模式）
仅对外部工具修改的代码进行质量验证：

```bash
python run_ai_flow.py --validate-change feature-login-20260604_120000
```

**行为**：
- 加载 Change context
- 执行 Phase 9-11（Quality Gate、测试执行、最终报告）
- 跳过 Phase 1-8

### Rule Pack 说明

DevPalAgent 会为不同的 AI 工具生成协作规则，确保：
- 外部 AI 工具理解如何读取 `openspec/changes/<change-id>/` artifacts
- 修改代码时保持与 spec 的一致性
- 维持 traceability（change-id、requirement-id）
- 修改后可以通过 DevPalAgent 的验证流程

**协作流程**：
```
[DevPalAgent --propose-only] 
    → 生成 OpenSpec Change + Rule Pack
    → [External AI Tool reads change artifacts]
    → [External AI Tool modifies code]
    → [DevPalAgent --validate-change]
    → Quality Gate + Tests → Report
```

---

## 5.7 Semantic Retrieval / Vector Store

DevPalAgent 可以把 requirements、OpenSpec change artifacts、source、tests、docs 和 error memory 建立本地语义索引，并在 Phase 4 代码生成、自愈和 Phase 11 报告中使用检索统计。

```bash
# 在 OpenSpec 流程中启用检索上下文注入
python run_ai_flow.py -r requirements/simple_login.md --vector-retrieval --vector-top-k 5

# 单独索引项目 artifacts
python -m devpal.vector_store.index_project <project-dir>

# 查询相关代码/文档，必要时先索引
python -m devpal.vector_store.search "用户登录密码校验逻辑" --project-dir <project-dir> --index-first
```

当前默认使用 deterministic `MockEmbeddingProvider`，便于本地测试和离线 demo；安装并配置 ChromaDB 后可使用持久化向量库。真实 embedding provider 和召回质量 benchmark 是后续优化项。

---

## 6. 快速开始

### 6.1 环境要求

- Python 3.10+
- pytest
- 可选：C++ 编译器 / MSVC / CMake
- 可选：Anthropic API key，用于真实 AI 代码生成

### 6.2 安装依赖

```bash
pip install -r requirements.txt
```

### 6.3 配置多智能体（可选）

```bash
# 启用多智能体并行执行
cp config/agent_pool.yaml.example config/agent_pool.yaml
# 编辑配置文件，设置池大小和超时
```

### 6.4 运行示例

```bash
# 基础示例（顺序执行）
python test_simple.py

# 多智能体示例（并行执行）
python test_simple.py --multi-agent --pool-size 4
```

### 6.5 运行测试

```bash
# OpenSpec 核心测试
python -m pytest tests/openspec/

# 多智能体测试
python -m pytest tests/openspec/test_phase4_multi_agent.py
python -m pytest tests/openspec/test_phase5_multi_agent.py

# 端到端测试
python -m pytest tests/e2e/test_multi_agent_flow.py
```

---

## 7. 面试 / 项目讲解亮点

如果用这个项目面试 Agent 工程岗位，推荐这样定位：

> DevPalAgent 是一个 Spec-first Agentic SDLC Runtime，支持多智能体并行执行。它把 LLM 代码生成放进确定性的工程流水线，通过需求解析、阶段化调度、**多智能体并行生成**、工具调用、质量门禁、测试执行、checkpoint 恢复和 final report，解决 AI 代码生成不可控、不可验证、不可追踪、**效率低下**的问题。

重点亮点：

1. **Multi-Agent Orchestration**：Phase 4/9/10 提供可选本地多 Agent 路径，并通过 sandbox manifest 审计
2. **Intelligent Scheduling**：依赖解析、拓扑排序、分阶段执行
3. **Fault Isolation**：sandbox path/command policy、staging workspace、fallback event 和报告汇总
4. **Message-driven Architecture**：事件总线、命令/事件分离、异步通信
5. **Agent workflow orchestration**：不是单 prompt，而是 11 阶段状态机
6. **Tool use**：Phase 4 通过 tool loop 写文件
7. **State management**：OpenSpecContext + checkpoint/resume
8. **Reliability**：success policy、skipped 语义、quality gate、checkpoint/resume
9. **Evaluation**：Phase 9/10/11 把生成结果变成可验证报告
10. **Multi-language awareness**：C++/Python/installer 分支已稳定
11. **Traceability**：ArtifactGraph 追踪需求到代码/测试/文档
12. **Scalability**：Phase 级并行 + 本地多 Agent MVP，保留未来远程/分布式扩展口

详细面试讲法见：

- [doc3.0/interview_pitch.md](doc3.0/interview_pitch.md)
- [plan_doc/plan_0525_MultiAgent_Benefits_Details.md](plan_doc/plan_0525_MultiAgent_Benefits_Details.md)

---

## 8. 技术文档

### 8.1 架构文档
- [doc3.0/agent_architecture.md](doc3.0/agent_architecture.md) - Agent 架构说明
- [doc3.0/e2e_demo.md](doc3.0/e2e_demo.md) - E2E demo 命令说明
- [doc3.0/interview_pitch.md](doc3.0/interview_pitch.md) - 面试讲法

### 8.2 多智能体文档（新增）
- [plan_doc/plan_0525_Phase4_5_MultiAgent_Architecture.md](plan_doc/plan_0525_Phase4_5_MultiAgent_Architecture.md) - 多智能体架构技术方案
- [plan_doc/plan_0525_MultiAgent_Benefits_Details.md](plan_doc/plan_0525_MultiAgent_Benefits_Details.md) - 核心收益与技术细节
- [plan_doc/plan_0525_MultiAgent_Impact_Analysis.md](plan_doc/plan_0525_MultiAgent_Impact_Analysis.md) - 架构影响分析

---

## 9. Roadmap

### M1：语言感知闭环稳定版

状态：✅ 已完成

- Phase 2 语言感知目录结构
- Phase 9 语言感知质量门禁
- Phase 10 Python pytest canonical result
- Phase 11 / CLAUDE.md 语言感知
- installer e2e 覆盖

### M2：本地多 Agent 与并行执行

状态：✅ MVP 已完成，持续产品化

- Phase 4/5 文件级并行执行
- Phase 4 CodegenAgent 可选执行路径
- Phase 9 ReviewAgent 可选执行路径
- Phase 10 TestAgent 命令策略校验
- SandboxSession 路径/命令策略与 manifest 审计
- LocalThreadBackend 作为当前本地后端

### M3：OpenSpec Change MVP

目标：补齐 OpenSpec 核心 changes/proposal/spec/tasks 模型

计划输出：

```text
openspec/
├── project.md
├── specs/main.md
└── changes/<change-id>/
    ├── proposal.md
    ├── specs/spec.md
    ├── tasks.md
    ├── design.md
    └── metadata.json
```

### M4：Archive + Traceability

目标：需求生命周期闭环

- `archive_change(change_id)`
- spec delta 合并到 main spec
- ArtifactGraph 增加 introduced_by / modified_by / archived_at
- final report 输出 requirement coverage matrix

### M5：多 Agent 产品化与远程后端探索

目标：在本地 MVP 稳定后，再扩展更强隔离和远程执行

- 更严格的 sandbox level 策略
- Agent lifecycle / budget / cooldown 事件
- 可选多进程或远程 worker backend
- 更完整的性能 benchmark 与 fallback 报告

---

## 10. 维护约定

- 运行产物不要提交：`.spec/`、`test_phase_skip/`、`cpp_test_phase_skip/`、`__pycache__/`
- skipped 不等于 passed，报告中必须保留 skipped reason
- 新增语言时不要只改 prompt，必须同步 Phase 2/4/9/10/11
- 新增能力优先加 targeted tests，再加 e2e smoke
- OpenSpec 对标方向优先补 changes/archive/traceability
- 多智能体功能通过配置开关控制，保持向后兼容

---

## 11. 贡献指南

欢迎贡献！重点方向：

1. **多智能体优化**: 调度算法、负载均衡、性能优化
2. **语言插件**: 新增 TypeScript、Go、Rust 等语言支持
3. **OpenSpec 完善**: changes 目录、archive 机制、traceability
4. **测试覆盖**: 多智能体场景、边界情况、性能测试
5. **文档完善**: 使用指南、最佳实践、故障排查

---

**License**: MIT

**Contact**: DevPalAgent Team
