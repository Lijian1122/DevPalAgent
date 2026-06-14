# DevPalAgent

> Spec-first Agentic SDLC Runtime：把需求、实现、验证、归档放进一条可审计、可恢复、可追踪的软件交付流水线。

DevPalAgent 不是普通聊天机器人，也不是一次性代码生成脚本。它的核心目标是把 LLM 代码生成放进确定性的工程流程里：先把需求解析为结构化 spec，再通过阶段化 workflow、多 Agent 本地 sandbox、质量门禁、测试执行、归档追溯和 final report，降低 AI 生成代码在真实工程落地中的不可控性。

当前项目定位：

```text
DevPalAgent =
  Spec-first workflow
  + phase-level parallel execution
  + local auditable multi-agent sandbox
  + explicit merge gate
  + quality gate / test runner
  + archive / traceability lifecycle
  + AI-agnostic collaboration CLI
```

截至 2026-06-13，项目已经具备一个本地可审计的 Agentic SDLC Runtime MVP。当前重点不再是补齐基础功能，而是继续增强真实 golden run、向量检索质量、traceability 精度、sandbox 隔离强度和演示资产。

---

## 1. 项目解决什么问题

LLM 写代码真正难的不是“生成几段代码”，而是把生成行为放进工程系统里控制。

| 常见问题 | DevPalAgent 的解决方式 |
| --- | --- |
| LLM 直接改代码不可控 | 使用 OpenSpec 11 阶段 workflow 包裹生成行为 |
| 需求、代码、测试难追踪 | 使用 structured requirements、ArtifactGraph、coverage matrix、archive manifest |
| 多 Agent 并发容易污染主仓库 | 每个 Agent 写入 sandbox workspace，通过 manifest 和 merge gate 显式合并 |
| 生成结果缺少验收证据 | Phase 9 Quality Gate、Phase 10 Test Runner、Phase 11 Final Report |
| 长流程失败难恢复 | Enhanced Scheduler 支持 timeout、retry、checkpoint、resume |
| 外部 AI 工具难协同 | 提供 propose-only / apply-only / validate-only 协作模式 |
| demo 写得漂亮但不可复现 | 提供 golden flow runner、parallel benchmark、vector retrieval eval 脚本 |

项目更偏向 Agent Infra / Agent Workflow / AI DevTools / Coding Agent 方向，而不是模型训练或算法研究。

---

## 2. 当前能力状态

### 2.1 已完成能力矩阵

| 能力域 | 当前状态 | 说明 |
| --- | --- | --- |
| OpenSpec 11 阶段流水线 | 已完成 | Phase 1-11 覆盖需求解析、结构创建、设计、代码、测试、质量门禁、最终报告 |
| Enhanced Scheduler | 已完成 | 支持 timeout、retry、checkpoint、resume、progress 和 critical phase 策略 |
| Phase 4/5 并行执行 | 已完成 | 使用 `PhaseParallelExecutor` 做文件级任务拆分和并发聚合 |
| 本地多 Agent 执行 | MVP 已完成 | Phase 4/9/10 可选 CodegenAgent、ReviewAgent、TestAgent |
| Sandbox workspace | MVP 已完成 | 支持 staging workspace、路径策略、命令策略、policy violation 记录 |
| Production merge gate | 已完成 | production sandbox 生成 `merge_pending` manifest，通过 CLI 显式合并 |
| Archive lifecycle | 已完成 | `archive` CLI 合并 spec、更新 metadata、生成 archive manifest 和 coverage matrix |
| Traceability | 已完成基础闭环 | ArtifactGraph 记录 requirement/source/test/report 关系，后续继续增强精确度 |
| EventBus integration | 已完成基础闭环 | 覆盖 workflow、fallback、archive、sandbox、vector 等事件类型 |
| Semantic retrieval | MVP 已完成 | 默认 mock/local provider，支持 ChromaDB 可选持久化，质量基线仍需增强 |
| AI-agnostic collaboration | 已完成基础模式 | 支持 propose-only、apply-change、validate-change 三种运行模式 |
| Golden flow runner | 已完成脚本和测试 | 覆盖 propose/apply/validate/archive，可 dry-run 或执行真实流程 |
| 面试/demo 文档 | 已完成基础包 | `doc3.0/interview_demo_scripts.md` 和 `docs/interview_qa/` 提供讲解材料 |

### 2.2 当前边界

这些边界需要在文档、面试和 demo 中主动讲清楚：

| 能力 | 当前边界 |
| --- | --- |
| 多 Agent | 当前是本地线程后端和本地 sandbox，不是分布式 Agent 平台 |
| Sandbox | 当前是路径/命令/manifest 级策略隔离，不是 OS/container/VM 强隔离 |
| Vector retrieval | 默认 deterministic mock/local proof，真实 embedding provider 和质量指标仍是后续重点 |
| Golden flow | runner 已完成，但仍建议沉淀一次稳定 non-dry-run golden report 作为发布级证据 |
| 性能收益 | 不固定承诺倍数，实际以 benchmark 和 final report 的 parallel summary 为准 |

---

## 3. 架构总览

DevPalAgent 由两条互补链路组成：

1. 交互式 Agent 链路：`Planner -> Executor -> Reflector`，用于普通开发任务、测试编排、自我修复和工具调用。
2. OpenSpec Runtime 链路：`WorkflowExecutor -> Scheduler -> Context -> Phase 1-11`，用于从需求到交付的确定性软件生成流程。

```text
User / CLI / requirements.md
        |
        +-------------------------+
        |                         |
        v                         v
  AgentEngine              OpenSpecWorkflowExecutor
        |                         |
        v                         v
 Planner / Executor        EnhancedOpenSpecScheduler
 / Reflector                      |
        |                         v
        |                  OpenSpecContext
        |                         |
        |                         v
        |                  Phase 1-11 Runtime
        |                         |
        |       +-----------------+-----------------+
        |       |                                   |
        |       v                                   v
        |  Sequential phases              Parallel / multi-agent phases
        |                              Phase 4 / Phase 5 / Phase 9 / Phase 10
        |                                   |
        |                                   v
        |                         MultiAgentCoordinator
        |                                   |
        |                                   v
        |                         LocalThreadBackend
        |                                   |
        |                                   v
        |                 CodegenAgent / ReviewAgent / TestAgent
        |                                   |
        |                                   v
        |                         SandboxSession
        |                                   |
        +-------------------------+---------+
                                  v
             ValidationEngine / ArtifactGraph / EventBus / Final Report
```

核心思想：

- OpenSpecContext 是跨阶段状态总线。
- PhaseResult 记录每个阶段的成功、失败、跳过原因和产物。
- ArtifactGraph 记录需求、代码、测试、文档、报告之间的关系。
- EventBus 记录 workflow、fallback、sandbox、archive、vector 等运行时事实。
- Sandbox manifest 记录 Agent 输出、违规、待合并文件和审计信息。

---

## 4. OpenSpec 11 阶段工作流

```text
Phase 1   Parse Requirements
Phase 2   Create Project Structure
Phase 3   Generate Technical Design
Phase 4   Generate Code
Phase 5   Generate Tests / Test Docs
Phase 6   Configure Build System
Phase 7   Generate Test Documentation
Phase 8   Generate README
Phase 9   Quality Gate
Phase 10  Run Tests
Phase 11  Final Report
```

| Phase | 核心职责 | 主要输出 | 并行/Agent 支持 |
| ---: | --- | --- | --- |
| 1 | 解析需求 | structured requirements、project type、language、delta spec | 无 |
| 2 | 创建项目结构 | 语言感知目录、`.spec/requirements.json` | 无 |
| 3 | 技术设计 | design 文档、实现约束、架构建议 | 无 |
| 4 | 代码生成 | source files、业务代码、模板代码 | 文件级并行，可选 CodegenAgent |
| 5 | 测试生成 | tests、test docs、测试说明 | 文件级并行 |
| 6 | 构建配置 | CMake 或语言相关构建文件 | 可按语言跳过 |
| 7 | 测试文档 | 测试说明、执行指引 | 可跳过 |
| 8 | README | 目标项目 README | 无 |
| 9 | 质量门禁 | quality gate report、validation issues | 可选 ReviewAgent |
| 10 | 运行测试 | test result、passed/failed/skipped counters | 可选 TestAgent |
| 11 | 最终报告 | final report、ArtifactGraph、CLAUDE.md、summary | 汇总 sandbox/vector/archive/fallback |

Phase 9 的四层验证模型：

| 层级 | 关注点 | 示例 |
| --- | --- | --- |
| L1 Format | 基础格式和语法 | Python AST、Shell 语法、C++ 文件结构 |
| L2 Semantic | 语义一致性 | 依赖完整性、明显逻辑矛盾、死代码 |
| L3 Parser | 可解析与接口匹配 | 函数签名、导入、调用关系 |
| L4 Business | 业务和安全规则 | 命名约束、敏感信息、注入风险、项目特定规则 |

---

## 5. 核心模块

### 5.1 Agent 主引擎

| 模块 | 说明 |
| --- | --- |
| `devpal/core/agent_engine.py` | 交互式 Agent 主引擎，组织 Planner/Executor/Reflector |
| `devpal/core/planner.py` | 解析意图、识别任务类型、拆分步骤、选择工具 |
| `devpal/core/reflector.py` | 检查执行结果、分析失败、决定是否重试或调整计划 |
| `devpal/tools/registry.py` | 工具注册与分发入口 |
| `devpal/memory/` | 短期记忆、长期记忆、错误记忆 |

### 5.2 OpenSpec Runtime

| 模块 | 说明 |
| --- | --- |
| `devpal/core/openspec_executor.py` | OpenSpec workflow facade，提供统一执行入口 |
| `devpal/core/openspec_workflow.py` | 连接 Agent 链路和 11 阶段 OpenSpec runtime |
| `devpal/core/openspec_phases/enhanced_scheduler.py` | timeout、retry、checkpoint、resume、phase 调度 |
| `devpal/core/openspec_phases/base.py` | OpenSpecContext、PhaseResult、阶段基类 |
| `devpal/core/openspec_phases/phase*.py` | 11 阶段具体实现 |

### 5.3 多 Agent 与 Sandbox

| 模块 | 说明 |
| --- | --- |
| `devpal/core/multi_agent/coordinator.py` | Phase 级多 Agent 协调器 |
| `devpal/core/multi_agent/backend.py` | 本地线程后端，复用 PhaseParallelExecutor |
| `devpal/core/multi_agent/models.py` | AgentTask、AgentResult、AgentPolicy、命令模型 |
| `devpal/core/multi_agent/sandbox.py` | sandbox workspace、路径/命令策略、manifest、sandbox level |
| `devpal/core/multi_agent/codegen_agent.py` | Phase 4 代码生成 Agent |
| `devpal/core/multi_agent/review_agent.py` | Phase 9 代码审查 Agent |
| `devpal/core/multi_agent/test_agent.py` | Phase 10 测试执行 Agent |
| `devpal/openspec/sandbox_merge.py` | sandbox manifest 显式合并服务 |

### 5.4 Spec、验证与追溯

| 模块 | 说明 |
| --- | --- |
| `devpal/core/schema/validation_engine.py` | 四层质量验证模型 |
| `devpal/core/schema/delta_spec.py` | 增量变更模型和 spec delta |
| `devpal/core/schema/artifact_graph.py` | 需求、代码、测试、文档、报告关系图 |
| `devpal/core/schema/event_bus.py` | 发布订阅事件总线 |
| `devpal/core/schema/workflow_events.py` | workflow、sandbox、archive、fallback 等事件模型 |
| `devpal/openspec/archive.py` | OpenSpec change 归档服务 |
| `devpal/openspec/coverage.py` | archive coverage matrix 生成 |

### 5.5 Vector Store

| 模块 | 说明 |
| --- | --- |
| `devpal/vector_store/index_project.py` | 索引项目 artifacts |
| `devpal/vector_store/search.py` | 语义检索 CLI |
| `scripts/evaluate_vector_retrieval.py` | deterministic vector retrieval smoke/eval |

---

## 6. 多 Agent Sandbox 与显式合并

当前多 Agent 路径的重点不是“让 Agent 自由改仓库”，而是把每个 Agent 的输出放进可审计边界。

```text
Phase 4 / 9 / 10
    |
    v
MultiAgentCoordinator
    |
    v
LocalThreadBackend
    |
    v
AgentTask
    |
    v
SandboxSession
    |
    +--> write to sandbox workspace
    +--> record manifest.json
    +--> record policy violations
    +--> production mode creates merge_pending entries
```

Sandbox level：

| Level | 适用场景 | 行为 |
| --- | --- | --- |
| `staging` | 本地开发、快速实验 | 使用 sandbox workspace 和基础策略 |
| `strict` | 更严格本地验证 | 强化路径和命令限制，记录违规 |
| `production` | 需要人工确认的协作流 | 不直接写主项目，生成 `merge_pending` manifest |

显式合并命令：

```bash
python -m devpal.openspec merge-sandbox <manifest> --project-dir <project>
python -m devpal.openspec merge-sandbox <manifest> --project-dir <project> --apply
```

不带 `--apply` 时用于预览；带 `--apply` 时才会写入目标项目文件。

---

## 7. Archive + Traceability Lifecycle

OpenSpec change 完成后，可以通过 archive 命令将变更合入主 spec 并固化证据链。

```bash
python -m devpal.openspec archive <change-id> --project-dir <project-dir>
```

Archive 会做几件事：

1. 将 `openspec/changes/<change-id>/specs/spec.md` 合并到 `openspec/specs/main.md`。
2. 更新 change metadata，将状态标记为 archived。
3. 生成 coverage matrix，表达 Requirement -> Code -> Test -> Report 的关系。
4. 更新 ArtifactGraph 的 archive metadata。
5. 写入 `.spec/archive/<change-id>.json` manifest。
6. 发出 archive lifecycle 事件，供 EventBus 和 final report 使用。

追溯链路示例：

```text
Requirement REQ-001
    -> implements
Source src/auth.py
    -> tests
Test tests/test_auth.py
    -> documents
Report docs/final_report.md
```

完整说明见 `doc3.0/archive_lifecycle.md`。

---

## 8. AI-agnostic 协作模式

DevPalAgent 可以和 Claude Code、Cursor、Cline 或人工编辑协作。它不要求所有代码都由自己生成，而是提供 spec、验证和归档的工程边界。

| 模式 | Phase 范围 | 用途 |
| --- | --- | --- |
| `--propose-only` | Phase 1-3 | 生成 proposal、tasks、design、spec 和外部工具规则 |
| `--apply-change <id>` | Phase 4-11 | 基于已有 change 执行实现、验证和报告 |
| `--validate-change <id>` | Phase 9-11 | 只验证外部 AI 或人工已经完成的代码变更 |

典型流程：

```bash
# 1. 生成 OpenSpec Change，不改业务代码
python run_ai_flow.py -r requirements/simple_login.md --propose-only

# 2. 外部 AI 工具或人工根据 openspec/changes/<change-id>/ 修改代码

# 3. 由 DevPalAgent 负责质量门禁、测试和最终报告
python run_ai_flow.py -r requirements/simple_login.md --validate-change <change-id>

# 4. 变更完成后归档
python -m devpal.openspec archive <change-id> --project-dir <project-dir>
```

这个模式适合面试或实际团队协作中强调一句话：

```text
外部 AI 可以负责生成，DevPalAgent 负责把生成行为纳入 spec、验证、追溯和归档。
```

---

## 9. Semantic Retrieval / Vector Store

DevPalAgent 支持对 requirements、OpenSpec change artifacts、source、tests、docs 和 error memory 建立语义索引，并在 Phase 4、fallback、自愈和 Phase 11 报告中使用检索上下文。

```bash
# 在 OpenSpec 流程中启用检索上下文注入
python run_ai_flow.py -r requirements/simple_login.md --vector-retrieval --vector-top-k 5

# 单独索引项目 artifacts
python -m devpal.vector_store.index_project <project-dir>

# 查询相关代码/文档，必要时先索引
python -m devpal.vector_store.search "用户登录密码校验逻辑" --project-dir <project-dir> --index-first
```

当前默认使用 deterministic `MockEmbeddingProvider`，便于本地测试和离线 demo。安装并配置 ChromaDB 后可使用持久化向量库。后续重点是补真实 embedding provider、固定 query set、top-k/hit-rate/fallback-rate 等质量指标。

---

## 10. Golden Flow 与 Proof Scripts

为了避免 README 只停留在叙事层，项目提供了几类可执行 proof。

### 10.1 Golden OpenSpec Lifecycle

```bash
# 只输出计划，不执行真实流程
python scripts/run_golden_openspec_flow.py --dry-run

# 指定需求和输出目录
python scripts/run_golden_openspec_flow.py --requirements requirements/simple_login.md --output-dir .spec/golden_flow
```

Golden flow 覆盖：

```text
propose -> apply -> validate -> archive
```

输出包括步骤状态、命令、产物检查、失败原因和 JSON/Markdown 报告。

### 10.2 Parallel Executor Benchmark

```bash
python scripts/benchmark_parallel_executor.py --json
python scripts/benchmark_parallel_executor.py --tasks 12 --delay-ms 50 --max-concurrency 4 --output .spec/parallel_benchmark.md
```

该脚本用于证明 Phase parallel execution 的基础收益，但不等同于真实 LLM 端到端性能。

### 10.3 Vector Retrieval Evaluation

```bash
python scripts/evaluate_vector_retrieval.py --json
```

该脚本用于 deterministic vector retrieval smoke/eval，后续可扩展为真实 embedding provider 的质量基线。

---

## 11. 快速开始

### 11.1 环境要求

- Python 3.10+
- pytest
- pyyaml
- 可选：anthropic，用于真实 LLM 调用
- 可选：ChromaDB，用于持久化向量库
- 可选：CMake / C++ compiler，用于 C++ 项目验收

当前仓库没有固定 `requirements.txt`，最小本地验证可以先安装：

```bash
python -m pip install pytest pyyaml
```

如果要跑真实 AI 生成流程：

```bash
python -m pip install anthropic pyyaml pytest
```

PowerShell 设置 Anthropic key 示例：

```powershell
$env:ANTHROPIC_API_KEY="your_key_here"
```

### 11.2 健康检查

```bash
python run_ai_flow.py --health-check
```

健康检查会检查 API key、CMake、C++ 编译器、Python 包和 `requirements/` 目录。

### 11.3 Dry-run 预览

```bash
python run_ai_flow.py -r requirements/simple_login.md --dry-run
```

Dry-run 只打印 OpenSpec 11 阶段计划，不写入业务文件。

### 11.4 运行完整 OpenSpec 流程

```bash
python run_ai_flow.py -r requirements/simple_login.md --verbose
```

常用参数：

| 参数 | 说明 |
| --- | --- |
| `--resume` | 从 `.spec/checkpoint.json` 恢复 |
| `--no-abort` | 关键阶段失败时继续后续阶段 |
| `--force-regenerate-code` | 强制重新生成业务代码 |
| `--max-concurrency 4` | 控制 phase 内部文件任务并发 |
| `--vector-retrieval` | 启用语义检索上下文注入 |
| `--enable-multi-agent` | 启用本地多 Agent 路径 |
| `--sandbox-level strict` | 设置 sandbox level |

### 11.5 多 Agent 示例

```bash
python run_ai_flow.py -r requirements/simple_login.md --enable-multi-agent --agent-pool-size 3 --sandbox-level strict --max-concurrency 3
```

Production merge gate 示例：

```bash
python run_ai_flow.py -r requirements/simple_login.md --enable-multi-agent --sandbox-level production
python -m devpal.openspec merge-sandbox <manifest> --project-dir <project-dir>
python -m devpal.openspec merge-sandbox <manifest> --project-dir <project-dir> --apply
```

---

## 12. 测试与验收命令

推荐先跑核心验收集：

```bash
python -m pytest tests/openspec/test_sandbox_merge.py tests/golden/test_golden_flow_runner.py tests/openspec/test_phase4_multi_agent.py tests/openspec/test_phase9_quality_gate.py tests/openspec/test_phase11_final_report.py tests/test_eventbus_integration.py tests/e2e/test_archive_e2e.py tests/openspec/test_archive_lifecycle.py
```

Roadmap proof scripts：

```bash
python scripts/run_golden_openspec_flow.py --dry-run
python scripts/benchmark_parallel_executor.py --json
python scripts/evaluate_vector_retrieval.py --json
```

更广的测试入口：

```bash
python -m pytest tests/openspec/
python -m pytest tests/golden/
python -m pytest tests/e2e/
```

注意：`pytest.ini` 中 `golden` 标记表示可能调用 LLM 或构建工具的长流程测试，日常本地验证建议优先跑 targeted tests。

---

## 13. 面试与项目讲解

如果用于 Agent 工程师、AI Infra 应用层、AI DevTools 或 Coding Agent 岗位，建议这样介绍：

```text
DevPalAgent 是一个 Spec-first Agentic SDLC Runtime。
它不是让 LLM 自由写代码，而是把需求、实现、验证、归档、多 Agent 协作
放进可审计、可恢复、可追踪的工程 workflow 中。
```

推荐讲解主线：

1. Workflow 层：OpenSpec 11 阶段，propose/apply/validate/archive 生命周期。
2. Agent 协作层：Phase 4/9/10 本地多 Agent，sandbox workspace，manifest。
3. 治理层：AgentPolicy、路径/命令限制、merge gate、fallback、EventBus。
4. 验收层：Quality Gate、Test Runner、Golden Flow、Archive、Final Report。
5. 边界意识：当前是本地可审计 MVP，不夸大为分布式 Agent 平台或强安全 sandbox。

适合强调的竞争力：

| 方向 | 亮点 |
| --- | --- |
| Agent Engineering | 多 Agent 编排、工具调用、状态管理、fallback、反思/验证 |
| AI Infra / Platform | workflow runtime、checkpoint、event bus、observability、report |
| AI DevTools | spec-first coding workflow、merge gate、archive、traceability |
| Coding Agent | 需求到代码到测试到报告的完整工程闭环 |

详细材料：

- `doc3.0/interview_demo_scripts.md`
- `doc3.0/interview_pitch.md`
- `docs/interview_qa/README.md`
- `docs/interview_qa/diagrams/README.md`

---

## 14. 技术文档地图

### 架构与设计

| 文档 | 说明 |
| --- | --- |
| `doc3.0/agent_architecture.md` | Agent 架构说明 |
| `doc3.0/e2e_demo.md` | E2E demo 命令说明 |
| `doc3.0/archive_lifecycle.md` | Archive lifecycle 说明 |
| `doc3.0/ai_agnostic_collaboration_architecture.md` | 外部 AI 协作架构 |

### 多 Agent

| 文档 | 说明 |
| --- | --- |
| `plan_doc/plan_0525_Phase4_5_MultiAgent_Architecture.md` | Phase 4/5 多 Agent 架构 |
| `plan_doc/plan_0525_MultiAgent_Benefits_Details.md` | 多 Agent 收益与技术细节 |
| `plan_doc/plan_0525_MultiAgent_Impact_Analysis.md` | 多 Agent 架构影响分析 |

### Roadmap 与差距分析

| 文档 | 说明 |
| --- | --- |
| `plan_doc/plan_0607_gap_analysis_and_next_roadmap.md` | 0607 差距分析和下一步规划 |
| `plan_doc/plan_0613_gap_analysis_roadmap.md` | 0613 当前实现总结和后续整体规划 |

### 面试资料

| 文档 | 说明 |
| --- | --- |
| `doc3.0/interview_demo_scripts.md` | 3 分钟、10 分钟、30 分钟 demo 讲法 |
| `doc3.0/interview_pitch.md` | 项目 pitch |
| `docs/interview_qa/` | 面试问答资料 |
| `docs/interview_qa/diagrams/` | 架构图、OpenSpec pipeline、multi-agent、quality gate、EventBus 图 |

---

## 15. Roadmap

### M1：语言感知闭环稳定版

状态：已完成

- Phase 2 语言感知目录结构。
- Phase 9 语言感知质量门禁。
- Phase 10 Python pytest canonical result。
- Phase 11 / CLAUDE.md 语言感知。
- installer / tooling 类项目支持阶段跳过和 skipped reason。

### M2：本地多 Agent 与并行执行

状态：MVP 已完成，持续产品化

- Phase 4/5 文件级并行执行。
- Phase 4 CodegenAgent 可选执行路径。
- Phase 9 ReviewAgent 可选执行路径。
- Phase 10 TestAgent 命令策略校验。
- SandboxSession 路径/命令策略与 manifest 审计。
- LocalThreadBackend 作为当前本地后端。

### M3：OpenSpec Change / AI-agnostic 协作

状态：基础闭环已完成，继续增强 demo 和真实场景

- propose-only 生成 proposal、tasks、design、spec、metadata。
- apply-change 从已有 change 执行 Phase 4-11。
- validate-change 对外部 AI 或人工修改执行 Phase 9-11。
- Rule Pack 支持 Claude/Cursor/Cline 协作口径。
- 后续重点：沉淀一条真实外部 AI 协作 demo。

### M4：Archive + Traceability

状态：基础闭环已完成，继续增强精确度

- archive CLI 已可用。
- spec delta 可合并到 main spec。
- archive manifest 已可生成。
- ArtifactGraph 和 coverage matrix 已接入。
- Phase 11 final report 已包含 archive summary。
- 后续重点：强化 requirement id -> file/test/report 的稳定映射。

### M5：Sandbox 与 Agent 治理产品化

状态：进行中

- 已完成 staging/strict/production sandbox level。
- 已完成 explicit sandbox merge gate。
- 已记录 sandbox violation、merge_pending、fallback summary。
- 后续重点：git worktree 或临时副本隔离、merge conflict 可视化、budget/token/resource/cooldown 事件、远程 worker backend。

### M6：向量检索质量基线

状态：MVP 已完成，质量工程待加强

- 已有 vector index/search CLI。
- 已有 deterministic smoke/eval script。
- Phase 11 可报告 semantic retrieval/fallback 信息。
- 后续重点：真实 embedding provider、固定 query set、top-k/hit-rate/fallback-rate 指标。

---

## 16. 维护约定

- 运行产物默认不要提交：`.spec/`、`__pycache__/`、`.pytest_cache/`、临时生成项目目录。
- skipped 不等于 passed，报告中必须保留 skipped reason。
- 新增语言时不要只改 prompt，必须同步 Phase 2/4/9/10/11。
- 新增 Agent 能力时必须考虑 AgentPolicy、sandbox manifest、fallback 和 final report。
- 新增 OpenSpec lifecycle 能力时必须同步 archive、coverage matrix 和 ArtifactGraph。
- 新增 CLI 能力时优先补 targeted tests，再补 e2e smoke。
- 文档描述必须区分当前能力、MVP 能力、后续规划，避免把 roadmap 写成已完成事实。

---

## 17. 贡献方向

欢迎围绕这些方向继续完善：

1. 更强 sandbox：git worktree、临时项目副本、container/remote runner。
2. 更强 traceability：requirement id、artifact id、test id 的稳定链路。
3. 更强 vector retrieval：真实 provider、质量基线、召回评估。
4. 更多语言插件：TypeScript、Go、Rust、Java。
5. 更完整 demo：真实 non-dry-run golden flow、截图、录屏、面试材料包。
6. 更强治理：token budget、资源限制、cooldown、agent lifecycle metrics。

---

## License

MIT

## Contact

DevPalAgent Team
