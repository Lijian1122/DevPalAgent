# DevPalAgent

> Spec-first Agentic SDLC Runtime：把需求文档转成可验证、可追踪、可自愈的软件项目。

DevPalAgent 不是普通聊天机器人，也不是一次性代码生成脚本。它把 LLM 放进一个确定性的工程流水线中：需求先被解析成结构化规范，然后经过阶段化设计、代码生成、质量门禁、测试执行、报告归档和 checkpoint 恢复，最终形成一个可审查的软件交付包。

当前项目重点方向：**OpenSpec-inspired Spec-Driven Development + Agent Workflow + 自动化验证闭环**。

---

## 1. 项目定位

DevPalAgent 面向 AI Coding / Agentic Engineering 场景，目标是解决 LLM 写代码时常见的几个问题：

| 问题 | DevPalAgent 的解决方式 |
|---|---|
| LLM 直接写代码不可控 | 使用 11 阶段 OpenSpec workflow 包裹 LLM 输出 |
| 需求、代码、测试难追踪 | 使用 structured requirements、ArtifactGraph、final report |
| 生成结果无法验证 | Phase 9 Quality Gate + Phase 10 测试执行 |
| 长流程失败难恢复 | checkpoint/resume + phase result 持久化 |
| 多语言上下文错配 | language-aware Phase 2/9/10/11 + Prompt Engine |
| skipped 与 passed 混淆 | 明确记录 skipped/test_skipped/test_summary |
| 生成错误需要人工修 | 自愈与 fallback model 机制逐步接入 |

一句话概括：

```text
DevPalAgent = Spec-first workflow + Agent tool loop + Quality gate + Test/self-heal + Traceable reports
```

---

## 2. 架构总览

DevPalAgent 不是单一的“问答式 Agent”，而是由两条互补执行链组成：

1. **经典 Agent 链路**：面向交互式开发任务，采用 `Planner → Executor → Reflector` 的 Plan-Act-Reflect 模式。
2. **OpenSpec Runtime 链路**：面向从需求到项目交付的端到端生成，采用 `WorkflowExecutor → Scheduler → Context → Phase 1-11` 的确定性流水线。

### 2.1 总体分层

```text
┌────────────────────────────────────────────────────────────────────┐
│                           User / CLI / Web                          │
│        chat request / requirements.md / explicit command             │
└───────────────────────────────┬────────────────────────────────────┘
                                │
        ┌───────────────────────┴────────────────────────┐
        │                                                │
        ▼                                                ▼
┌──────────────────────┐                         ┌──────────────────────┐
│ AgentEngine           │                         │ OpenSpecWorkflow      │
│ interactive agent     │                         │ spec-first runtime    │
└──────────┬───────────┘                         └──────────┬───────────┘
           │                                                │
           ▼                                                ▼
┌──────────────────────┐                         ┌──────────────────────┐
│ Planner              │                         │ OpenSpecExecutor      │
│ task planning        │                         │ workflow facade       │
└──────────┬───────────┘                         └──────────┬───────────┘
           │                                                │
           ▼                                                ▼
┌──────────────────────┐                         ┌──────────────────────┐
│ Executor             │                         │ EnhancedScheduler     │
│ tool execution       │                         │ retry/checkpoint      │
└──────────┬───────────┘                         └──────────┬───────────┘
           │                                                │
           ▼                                                ▼
┌──────────────────────┐                         ┌──────────────────────┐
│ ToolRegistry         │                         │ OpenSpecContext       │
│ file/git/test/etc.   │                         │ shared phase state    │
└──────────┬───────────┘                         └──────────┬───────────┘
           │                                                │
           ▼                                                ▼
┌──────────────────────┐                         ┌──────────────────────┐
│ Reflector            │                         │ Phase 1-11            │
│ verify & improve     │                         │ spec→code→test→report│
└──────────┬───────────┘                         └──────────┬───────────┘
           │                                                │
           └───────────────────────┬────────────────────────┘
                                   ▼
┌────────────────────────────────────────────────────────────────────┐
│ Core engines: ValidationEngine / DeltaSpec / ArtifactGraph / EventBus│
│ LLM client / PromptEngine / Templates / Language plugins / Memory    │
└────────────────────────────────────────────────────────────────────┘
```

### 2.2 Plan-Act-Reflect 架构模式

经典 Agent 链路用于普通代码任务、测试编排、自我改进、代码审查等交互场景。它的核心不是一次性调用工具，而是把任务拆成“规划、执行、反思”的闭环。

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

### 2.3 OpenSpec Runtime 架构模式

OpenSpec 链路用于“需求文档 → 软件项目”的完整交付。它把 LLM 生成放进可恢复、可验证、可追踪的工程流程，而不是让模型直接写一堆文件。

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
   ▼
Phase 1-11
   │  parse → structure → design → code → tests → build → docs
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
| Intelligence Layer | `llm_client.py`、`prompt_engine.py`、`templates/` | LLM 调用、动态 Prompt、语言/项目模板 |
| Verification Layer | `validation_engine.py`、`phase9_quality_gate.py`、`phase10_run_tests.py` | 四层质量门禁、测试执行、编译/pytest/shell 检查 |
| Traceability Layer | `artifact_graph.py`、`delta_spec.py`、`requirements.py` | 需求、代码、测试、报告之间的关系追踪 |
| Reporting Layer | `phase11_final_report.py` | final report、ArtifactGraph、CLAUDE.md、测试摘要 |

### 2.4 核心数据流

```text
输入需求
  │
  ├─ Phase 1: requirements_content / structured_requirements / delta.json
  │
  ├─ Phase 2: project structure / .spec/requirements.json
  │
  ├─ Phase 3-8: design / code / tests / build config / docs / README
  │
  ├─ Phase 9: quality_gate_report + validation issues
  │
  ├─ Phase 10: test_result / test_summary / passed-failed-skipped counters
  │
  └─ Phase 11: final_report / artifact_graph / CLAUDE.md
```

这条数据流里，`OpenSpecContext` 是所有阶段的状态总线，`ArtifactGraph` 负责记录工件关系，`ValidationEngine` 负责质量判断，`PhaseResult` 负责把每个阶段的成功、失败、跳过原因持久化。

更详细的架构说明见：

- [doc3.0/agent_architecture.md](doc3.0/agent_architecture.md)
- [doc3.0/e2e_demo.md](doc3.0/e2e_demo.md)
- [doc3.0/interview_pitch.md](doc3.0/interview_pitch.md)

---

## 3. 核心模块

### 3.1 Agent 主引擎与 Plan-Act-Reflect

| 文件 | 说明 |
|---|---|
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

### 3.3 OpenSpec 11 阶段实现

| Phase | 文件 | 核心职责 |
|---:|---|---|
| 1 | `phase1_parse_requirements.py` | 解析需求文本，提取 structured requirements、project_type、language、features，输出 `.spec/delta.json` |
| 2 | `phase2_create_structure.py` | 创建语言感知目录结构，写入 `.spec/requirements.json` |
| 3 | `phase3_technical_design.py` | 生成技术设计，可根据 installer/tooling 等项目类型跳过 |
| 4 | `phase4_generate_code.py` | 通过 Prompt Engine、模板和 AI tool loop 生成核心代码 |
| 5 | `phase5_generate_tests.py` | 生成测试代码或测试说明，可按项目类型跳过 |
| 6 | `phase6_cmake_config.py` | 生成 CMake/build 配置，非 C++ 项目可跳过 |
| 7 | `phase7_test_docs.py` | 生成或补充测试文档 |
| 8 | `phase8_readme.py` | 生成目标项目 README |
| 9 | `phase9_quality_gate.py` | 执行语言感知四层质量门禁，输出 quality gate report |
| 9b | `phase9_code_review.py` | 代码审查型质量检查扩展 |
| 10 | `phase10_run_tests.py` | 执行 C++/Python/Shell 测试，维护 canonical test counters 和 skipped 语义 |
| 11 | `phase11_final_report.py` | 生成 final report、ArtifactGraph、CLAUDE.md 和最终交付摘要 |

### 3.4 Spec、验证与可追踪核心模型

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
| RolloutEngine | `devpal/core/schema/rollout_engine.py` | 渐进式发布/策略执行能力基础 |
| ErrorManager | `devpal/core/schema/error_manager.py` | 错误分类、错误上下文和错误管理 |
| ConfigPolicy | `devpal/core/schema/config_policy.py` | 配置策略和规则管理 |
| CompileDB | `devpal/core/schema/compile_db.py`、`devpal/core/compiledb/` | 编译数据库解析与编译上下文支持 |

四层验证模型：

| 层级 | 关注点 | 示例 |
|---|---|---|
| L1 Format | 基础格式和语法 | Python AST、Shell 语法、C++ 文件结构 |
| L2 Semantic | 语义一致性 | 依赖完整性、明显逻辑矛盾、死代码 |
| L3 Parser | 可解析与接口匹配 | 函数签名、导入、调用关系 |
| L4 Business | 业务和安全规则 | 命名约束、敏感信息、注入风险、项目特定规则 |

### 3.5 Tool 系统

Tool 系统是 Executor 的执行层，也是 OpenSpec Phase 4/9/10 能调用底层能力的基础。

| 类别 | 文件 | 说明 |
|---|---|---|
| Tool 基础 | `devpal/tools/base.py` | 工具基类、输入输出约定、执行结果结构 |
| Function Call 抽象 | `devpal/tools/function_call_base.py` | 面向 LLM function/tool calling 的抽象层 |
| 工具注册 | `devpal/tools/registry.py` | 注册、查询、分发工具 |
| 文件工具 | `file_reader.py`、`file_writer.py`、`code_search.py` | 读取、写入、搜索代码 |
| 命令工具 | `command_executor.py` | 执行 shell/系统命令 |
| Git 工具 | `git_tool.py` | Git 状态、diff、提交相关操作能力 |
| 编译/静态分析 | `compiler_analyzer.py`、`static_analyzer.py`、`msvc_asan_compiler.py`、`cmake_build_tool.py` | 编译诊断、静态分析、MSVC/ASAN、CMake build |
| 代码审查 | `code_review.py`、`code_review_report.py` | 审查代码并生成审查报告 |
| 自动修复 | `auto_fixer.py`、`code_normalizer.py` | 自动修复和代码规范化 |
| 测试编排 | `test_orchestrator.py`、`test_doc_generator.py`、`test_generator.py`、`test_runner.py`、`test_result_updater.py` | 从审查到测试文档、测试代码、测试执行、结果回填的闭环 |
| 自我改进 | `self_source_reader.py`、`self_improve.py`、`compilation_reflector.py` | 读取自身源码、分析问题、反思编译结果并改进 |
| OpenSpec 工具 | `project_generator.py`、`spec_tool.py` | 项目生成和 Spec CLI 能力 |
| 插件/安全辅助 | `plugin_system.py`、`hallucination_detector.py` | 动态插件和幻觉检测 |

测试编排链路：

```text
TestOrchestrator
   ├─ CodeReview → issues
   ├─ CodeReviewReport → code_review.md
   ├─ AutoFixer → fixed source + backup
   ├─ TestDocGenerator → test documentation
   ├─ TestGenerator → test code
   └─ TestRunner → test result + pass/fail/skipped summary
```

### 3.6 LLM、Prompt、模板与多语言

| 文件 | 说明 |
|---|---|
| `devpal/core/llm_client.py` | LLM 调用封装，供代码生成、审查、设计等模块使用 |
| `devpal/core/prompts/prompt_engine.py` | 动态 Prompt Template Engine，根据语言、项目类型和 Phase 生成提示词 |
| `devpal/core/templates/base.py` | 模板基类 |
| `devpal/core/templates/registry.py` | 模板注册表 |
| `devpal/core/templates/cpp_templates.py` | C++ 项目模板 |
| `devpal/core/templates/python_templates.py` | Python skeleton、README、测试模板 |
| `devpal/core/templates/install_script_generator.py` | Claude CLI installer 脚本生成器 |
| `devpal/core/templates/requirements_parser.py` | 需求解析模板和辅助逻辑 |
| `devpal/core/schema/languages/language_config.py` | C++ / Python / Shell 的语言特征配置 |
| `devpal/core/schema/languages/base.py` | 语言插件基类 |
| `devpal/core/schema/languages/cpp_plugin.py`、`cpp_rules.py` | C++ 插件与规则 |
| `devpal/core/schema/languages/python_plugin.py` | Python 插件雏形 |
| `devpal/core/schema/languages/shell_plugin.py` | Shell 插件雏形 |

### 3.7 编译、测试与运行结果解析

| 文件 | 说明 |
|---|---|
| `devpal/core/compiler_detector.py` | 编译器检测，尤其是 Windows/MSVC 环境识别 |
| `devpal/core/test_result_parser.py` | 测试结果解析，统一 passed/failed/skipped 语义 |
| `devpal/core/compiledb/core.py` | compile database 核心处理 |
| `devpal/core/compiledb/parsers.py` | compile commands 等编译数据库解析器 |

---

## 4. 当前能力状态

### 4.1 已完成能力

| 能力 | 状态 | 说明 |
|---|---:|---|
| OpenSpec 11 阶段流水线 | ✅ | Phase 1-11 已实现 |
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
| Installer flow smoke/e2e | ✅ | 覆盖 skipped phase、report、quality gate |
| Checkpoint 路径修正 | ✅ | 不再误生成 `cpp_*` checkpoint 目录 |

### 4.2 当前阶段

项目已完成 `M1：语言感知闭环稳定版`：

- Phase 2 目录结构语言感知。
- Phase 9 Python/installer 不再跑 C++ 检查。
- Phase 10 Python pytest 写入 canonical test counts。
- Phase 11 / CLAUDE.md 语言感知。
- installer 项目不再显示 `0/0 passed`。
- installer e2e 验证通过。

---

## 5. OpenSpec 11 阶段工作流

DevPalAgent 的核心执行流：

```text
Phase 1  Parse Requirements
Phase 2  Create Project Structure
Phase 3  Generate Technical Design
Phase 4  Generate Core Code
Phase 5  Generate Tests / Test Docs
Phase 6  Configure Build System
Phase 7  Generate Test Documentation
Phase 8  Generate README
Phase 9  Quality Gate
Phase 10 Run Tests / Compile / Update Docs
Phase 11 Final Report
```

### 5.1 阶段职责

| Phase | 名称 | 主要输出 |
|---:|---|---|
| 1 | Parse Requirements | `requirements_content`、`structured_requirements`、`requirements_delta`、`.spec/delta.json` |
| 2 | Create Structure | 项目目录、`.spec/requirements.json` |
| 3 | Technical Design | `tech_design_content`，可按项目类型跳过 |
| 4 | Code Generation | infra templates + AI business code |
| 5 | Test Generation | 测试文档/测试代码，可按项目类型跳过 |
| 6 | Build Config | CMake 等构建配置，可按语言跳过 |
| 7 | Test Docs | 测试文档补充，可跳过 |
| 8 | README | 项目 README |
| 9 | Quality Gate | 四层验证 + 代码审查 + 自愈入口 |
| 10 | Run Tests | C++/Python/Shell 测试执行或 skipped |
| 11 | Final Report | final report、ArtifactGraph、CLAUDE.md |

### 5.2 Installer 项目跳过规则

Installer/tooling 项目不需要 C++ 技术设计、CMake、编译测试，因此会跳过：

```text
Phase 3  skipped: 安装脚本项目不需要 AI 技术设计
Phase 5  skipped: 安装脚本项目不需要生成测试代码
Phase 6  skipped: 安装脚本项目不需要 CMake 配置
Phase 7  skipped: 安装脚本项目不需要测试文档
Phase 10 skipped: 安装脚本项目不需要编译和运行测试
```

skipped 不会被当成 passed，也不会显示为 `0/0 passed`，而是记录：

```json
{
  "skipped": true,
  "test_skipped": true,
  "test_status": "skipped",
  "test_summary": "skipped (...)"
}
```

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

如果仓库没有统一 requirements，可至少安装测试依赖：

```bash
pip install pytest
```

### 6.3 运行 installer smoke flow

```bash
python test_simple.py
```

预期：

- 项目目录：`test_phase_skip/`
- Phase 3/5/6/7/10 skipped
- Phase 9 四层 0 issue
- Phase 11 显示 `tests: skipped (...)`
- 不生成 `cpp_test_phase_skip/`

运行后可查看：

```text
test_phase_skip/docs/final_report.md
test_phase_skip/docs/quality_gate_report.md
test_phase_skip/CLAUDE.md
```

### 6.4 运行 M1 目标测试

```bash
python -m pytest tests/openspec/test_spec_first_artifacts.py tests/openspec/test_phase10_run_tests.py tests/openspec/test_phase9_quality_gate.py tests/e2e/test_installer_flow.py
```

最近验证结果：

```text
22 passed, 2 warnings
```

### 6.5 运行更多测试

```bash
python -m pytest tests/openspec
python -m pytest tests/test_install_script_generator.py
```

---

## 7. E2E Demo

### 7.1 输入需求

示例文件：

```text
requirements/test_phase_skip.md
```

内容描述一个安装脚本项目：

```markdown
# 安装脚本生成器测试

这是一个安装脚本项目，用于生成 Claude Code CLI 的安装脚本。
本项目是安装脚本类型，不需要 C++ 编译、CMake 配置和测试。
```

### 7.2 执行命令

```bash
python test_simple.py
```

### 7.3 关键输出

```text
[SKIP] Phase 3 ... 安装脚本项目不需要 AI 技术设计
[SKIP] Phase 5 ... 安装脚本项目不需要生成测试代码
[SKIP] Phase 6 ... 安装脚本项目不需要 CMake 配置
[SKIP] Phase 7 ... 安装脚本项目不需要测试文档
[SKIP] Phase 10 ... 安装脚本项目不需要编译和运行测试

Phase 9:
FORMAT layer: 0 issue(s)
SEMANTIC layer: 0 issue(s)
PARSER layer: 0 issue(s)
BUSINESS layer: 0 issue(s)

Phase 11:
tests: skipped (...)
```

更多说明见：

- [doc3.0/e2e_demo.md](doc3.0/e2e_demo.md)

---

## 8. 面试 / 项目讲解亮点

如果用这个项目面试 Agent 工程岗位，推荐这样定位：

> DevPalAgent 是一个 Spec-first Agentic SDLC Runtime。它把 LLM 代码生成放进确定性的工程流水线，通过需求解析、阶段化调度、工具调用、质量门禁、测试执行、checkpoint 恢复和 final report，解决 AI 代码生成不可控、不可验证、不可追踪的问题。

重点亮点：

1. **Agent workflow orchestration**：不是单 prompt，而是 11 阶段状态机。
2. **Tool use**：Phase 4 通过 tool loop 写文件。
3. **State management**：OpenSpecContext + checkpoint/resume。
4. **Reliability**：success policy、skipped 语义、quality gate。
5. **Evaluation**：Phase 9/10/11 把生成结果变成可验证报告。
6. **Multi-language awareness**：C++/Python/installer 分支已稳定。
7. **Traceability**：ArtifactGraph 追踪需求到代码/测试/文档。
8. **Roadmap**：OpenSpec changes/archive/traceability 是下一阶段。

详细面试讲法见：

- [doc3.0/interview_pitch.md](doc3.0/interview_pitch.md)

---

## 9. 当前限制

当前仍不是完整 OpenSpec 复刻版，主要差距包括：

1. **缺少 OpenSpec changes 目录模型**
   - 尚未生成 `openspec/changes/<change-id>/proposal.md/spec.md/tasks.md`。

2. **Delta 仍偏执行产物**
   - `.spec/delta.json` 已有，但还不是 OpenSpec 风格 Markdown delta spec。

3. **Archive 机制未完成**
   - 尚不能把 delta 合并到 `openspec/specs/main.md`。

4. **Traceability 仍缺变更历史**
   - ArtifactGraph 可追踪需求到文件，但还不能回答“哪个 change 引入了这个需求”。

5. **LanguagePlugin 未完全主流程化**
   - Phase 2/4/9/10/11 已语言感知，但统一插件接口还未完全贯通。

6. **EventBus 未接入主流程**
   - 事件总线存在，但还没有成为默认 runtime event log。

---

## 10. Roadmap

### M1：语言感知闭环稳定版

状态：✅ 已完成

- Phase 2 语言感知目录结构
- Phase 9 语言感知质量门禁
- Phase 10 Python pytest canonical result
- Phase 11 / CLAUDE.md 语言感知
- installer e2e 覆盖

### M2：OpenSpec Change MVP

目标：补齐 OpenSpec 核心 changes/proposal/spec/tasks 模型。

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

### M3：Archive + Traceability

目标：需求生命周期闭环。

- `archive_change(change_id)`
- spec delta 合并到 main spec
- ArtifactGraph 增加 introduced_by / modified_by / archived_at
- final report 输出 requirement coverage matrix

### M4：AI-agnostic 协作模式

目标：DevPalAgent 不仅自己调用 LLM，也能服务 Claude Code / Cursor / Cline。

- 完整 CLAUDE.md
- changes 目录
- propose-only / apply-only 模式
- AI 助手可直接读取的规范上下文

---

## 11. 仓库文件说明

```text
devpal/
├── main.py                    # 应用入口
├── cli.py                     # CLI 命令
├── config.py                  # 配置管理
├── core/
│   ├── agent_engine.py        # Agent 主引擎，组织 Planner/Executor/Reflector
│   ├── planner.py             # Planner 规划器
│   ├── reflector.py           # Reflector 反思器
│   ├── openspec_executor.py   # OpenSpec workflow facade
│   ├── openspec_workflow.py   # OpenSpec 工作流封装
│   ├── openspec_phases/       # Phase 1-11 workflow
│   ├── schema/                # ArtifactGraph / ValidationEngine / Delta / EventBus
│   ├── prompts/               # Dynamic prompt engine
│   ├── templates/             # C++/Python/installer templates
│   ├── compiledb/             # 编译数据库解析
│   └── i18n/                  # 多语言文案
├── memory/                    # short-term / long-term / error memory
├── tools/                     # ToolRegistry 下的文件、命令、Git、审查、测试、自改进工具
├── workflows/                 # 声明式 workflow 配置
└── multimodal/                # 多模态能力

tests/
├── openspec/                  # OpenSpec phase/unit tests
├── e2e/                       # End-to-end smoke flows
└── golden/                    # Golden cases

doc3.0/
├── agent_architecture.md      # Agent 架构说明
├── interview_pitch.md         # 面试讲法
└── e2e_demo.md                # E2E demo 命令说明

README_old.md                 # 旧版 README 备份
README.md                     # 当前新版 README
```

---

## 12. 维护约定

- 运行产物不要提交：`.spec/`、`test_phase_skip/`、`cpp_test_phase_skip/`、`__pycache__/`。
- skipped 不等于 passed，报告中必须保留 skipped reason。
- 新增语言时不要只改 prompt，必须同步 Phase 2/4/9/10/11。
- 新增能力优先加 targeted tests，再加 e2e smoke。
- OpenSpec 对标方向优先补 changes/archive/traceability，不建议重写现有 11 阶段流水线。
