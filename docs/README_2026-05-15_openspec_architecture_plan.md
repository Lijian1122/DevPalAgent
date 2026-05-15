# DevPalAgent OpenSpec 架构分析与后续优化计划

日期：2026-05-15

## 1. 当前整体判断

DevPalAgent 当前已经从“工具集合”进化成一个 Agent + OpenSpec 流水线型代码生成系统。主流程已经可以从需求文档出发，生成 C++ 项目、CMake 配置、测试、文档，并完成编译测试闭环。

但对标成熟的开源 OpenSpec / spec-driven development 工具，目前系统更接近“需求文档驱动的项目生成流水线”，还不是严格意义上的“规范对象驱动的可追踪、可增量、可验证工程系统”。

当前核心结论：

- OpenSpec 的流程已经跑通。
- 代码生成、编译、测试、自愈链路已经具备实用价值。
- Spec-First 的底层模块已经有雏形，但尚未深度接入主流程。
- 后续重点不应继续堆叠 Phase，而应把 Requirement Model、ArtifactGraph、DeltaSpec、Validation Gate 接入主 11 阶段。

## 2. 当前主执行链路

当前主要执行链路如下：

1. 用户输入自然语言任务。
2. `devpal/core/agent_engine.py` 接收任务。
3. `devpal/core/planner.py` 判断为 `project_generator` 类型任务。
4. 进入 `devpal/core/openspec_phases/enhanced_scheduler.py`。
5. 执行 11 个 OpenSpec Phase。

11 个阶段包括：

1. Phase 1：解析需求文档。
2. Phase 2：创建项目结构。
3. Phase 3：AI 生成技术设计。
4. Phase 4：模板 + AI 生成核心代码。
5. Phase 5：扫描测试并生成测试文档。
6. Phase 6：生成或验证 CMake 配置。
7. Phase 7：生成测试文档。
8. Phase 8：生成 README 文档。
9. Phase 9：代码审查。
10. Phase 10：编译、运行测试、自愈。
11. Phase 11：生成最终报告。

## 3. 当前架构优点

### 3.1 主流程已经闭环

当前系统已经可以完成：

- 读取需求文档。
- 生成技术设计。
- 生成 C++ 业务代码。
- 生成 CMake 项目。
- 生成测试代码。
- 编译主程序和测试程序。
- 运行测试。
- 失败时尝试 AI 自愈。
- 输出最终报告。

这说明系统已经具备基本的端到端自动化能力。

### 3.2 增强调度器方向正确

`EnhancedOpenSpecScheduler` 已经加入：

- 分阶段超时。
- 自动重试。
- 进度显示。
- 关键阶段失败终止。
- 检查点机制。

这些能力是后续产品化所必需的。

### 3.3 模板与 AI 组合合理

当前 Phase 4 的思路是：

- 基础设施文件由模板生成。
- 业务代码由 AI 根据需求和技术设计生成。

这是合理方向，因为 CMake、test_base、README 骨架等稳定文件更适合模板生成，业务逻辑更适合 AI 生成。

### 3.4 Phase 10 价值高

Phase 10 当前已经承担了自动化质量验证的核心职责：

- 检测 MSVC / g++ 编译器。
- 使用 CMake 编译主程序。
- 编译并运行测试。
- 解析测试结果。
- 失败时调用 AI 自愈。
- 将测试结果写入文档。

这是整个系统中最接近“质量门禁”的部分。

## 4. 当前主要架构问题

### 4.1 README 宣称的 Spec-First 能力和主流程接入不一致

README 中提到的能力包括：

- 四层验证引擎。
- Delta 增量变更。
- ArtifactGraph 工件依赖图。
- EventBus 事件总线。
- RolloutEngine。
- 多语言插件系统。

相关模块确实存在，例如：

- `devpal/core/schema/validation_engine.py`
- `devpal/core/schema/delta_spec.py`
- `devpal/core/schema/artifact_graph.py`
- `devpal/core/schema/event_bus.py`
- `devpal/core/schema/rollout_engine.py`

但当前主 11 阶段流程基本没有强依赖这些模块。

当前实际链路更像：

```text
Markdown 需求 -> LLM 设计 -> LLM 写代码 -> 编译测试
```

理想的 Spec-First 链路应该是：

```text
需求对象 -> Spec 变更 -> ArtifactGraph 影响分析 -> Delta 应用 -> Validation Gate -> 测试选择 -> 验收闭环
```

这是当前和成熟开源 spec-driven 工具之间最大的差距。

### 4.2 存在多套 OpenSpec 流程

当前同时存在：

- `devpal/core/openspec_workflow.py`
- `devpal/core/openspec_phases/scheduler.py`
- `devpal/core/openspec_phases/enhanced_scheduler.py`

其中 `openspec_workflow.py` 更像旧版 9 阶段流程，而当前主链路使用 `enhanced_scheduler.py` 的 11 阶段流程。

风险包括：

- 维护成本高。
- 文档和实现容易不一致。
- 修 bug 容易修错入口。
- CLI、聊天模式、工具模式可能行为不一致。

建议后续统一成一个正式的 `OpenSpecWorkflowExecutor`。

### 4.3 Phase 职责有重复和空心化

当前 11 个阶段中存在职责重叠：

- Phase 5 和 Phase 7 都处理测试文档。
- Phase 6 和模板系统都处理 CMake。
- Phase 8 和模板系统都处理 README。
- Phase 9 当前更偏报告生成，还没有形成硬性质量门禁。

更合理的阶段拆分可以是：

1. Parse Requirements。
2. Normalize Spec。
3. Plan Architecture。
4. Generate Artifacts。
5. Validate Static。
6. Build。
7. Test。
8. Repair Loop。
9. Traceability Report。
10. Acceptance Verification。
11. Final Package。

### 4.4 断点续传设计还不完整

当前已经临时禁用了断点续传。根因是 checkpoint 只保存阶段编号和完成状态，没有保存完整上下文。

可靠的断点续传至少需要保存：

- requirements content。
- parsed requirements。
- project name。
- project dir。
- technical design。
- generated files。
- test docs。
- phase results。
- llm usage。
- artifact graph snapshot。

否则从中间阶段恢复时容易缺失上下文，例如 Phase 4 缺失 `tech_design_content`。

### 4.5 Prompt 和工具协议之间缺少契约测试

近期出现过几个典型问题：

- Phase 4 提示词要求使用 `RUN_TEST`，但模板没有提供该宏。
- 提示词中 C++ `{}` 没转义，导致 Python `.format()` 报错。
- 提示词要求重新生成业务文件，但工具处理器仍跳过已存在文件。
- 自愈提示词要求 Markdown 代码块，解析器处理不稳定。

这说明 Prompt 不是简单文本，而是系统接口的一部分，应该有契约测试。

建议为每个 Prompt 增加：

- 格式化安全测试。
- 输出 schema 测试。
- 与模板 API 一致性测试。
- 最小回归测试样例。

### 4.6 缺少框架级回归测试

当前主要依赖完整 E2E 流程验证。完整流程价值很高，但成本高，不适合频繁定位问题。

建议补充以下回归测试：

- `resume=False` 不跳过 Phase。
- Phase 4 prompt `.format()` 不报错。
- `test_base.h` 包含 Phase 4 要求的宏。
- 没有测试文件时 Phase 10 必须失败。
- 没有编译器时 Phase 10 必须失败。
- Windows 反斜杠路径可以正确解析。
- 已存在项目时业务代码允许覆盖，基础设施文件跳过。
- AI tool loop 输出为空时错误信息清晰。

## 5. 对标开源 OpenSpec / Spec-Driven 工具的主要差距

### 5.1 需求没有对象化到足够强

成熟工具通常会把需求转为结构化对象：

```text
Requirement
- id
- title
- description
- acceptance criteria
- priority
- status
- linked design
- linked code
- linked tests
```

当前 Phase 1 主要还是读取 Markdown 文本，后续多数阶段仍把原始文本交给 LLM。

后续应升级为：

```text
Markdown -> Requirement AST -> Spec Model -> 后续阶段全部基于 Spec Model 工作
```

### 5.2 缺少需求到代码和测试的 Traceability

成熟工具应能回答：

- REQ-001 由哪些文件实现？
- REQ-001 被哪些测试覆盖？
- 哪个测试失败影响哪个需求？
- 修改某个源文件影响哪些需求？
- 哪些需求没有测试覆盖？

当前还没有形成这个闭环。

本地已有 `ArtifactGraph`，但尚未接入主流程。

### 5.3 缺少增量变更能力

当前更偏重新生成项目或覆盖业务文件。

成熟工具更强调：

- 已有项目增量修改。
- 只修改受影响文件。
- 保留用户手写代码。
- 生成 patch/diff。
- 支持回滚。
- 支持审查后应用。

本地已有 `DeltaSpec`，但主流程尚未使用。

### 5.4 缺少标准质量门禁

当前 Phase 10 是主要 gate，但还不够。

后续至少需要：

- format gate。
- compile gate。
- unit test gate。
- acceptance criteria gate。
- coverage gate。
- hallucination gate。
- generated artifact completeness gate。

例如 Phase 4 后应验证：

- CMakeLists.txt 存在。
- src/main.cpp 存在。
- 每个非平凡类都有 include/src/test。
- test_base.h API 与测试文件一致。
- 测试结果不能是 0/0。
- 所有 include 都可解析。

### 5.5 缺少稳定可复现的执行状态

建议最终形成标准 `.spec/` 目录：

```text
.spec/
  requirements.json
  design.json
  plan.json
  tasks.json
  artifacts.json
  traceability.json
  checkpoints/
  reports/
```

当前 `.spec` 已有缓存和日志，但状态结构还不够稳定。

## 6. 后续优化计划

### 6.1 第一阶段：稳定主流程，降低回归风险

目标：让当前已经跑通的流程稳定下来。

建议任务：

1. 统一 OpenSpec 入口。
   - 以 `enhanced_scheduler.py` 为唯一主流程。
   - 废弃或适配 `openspec_workflow.py` 旧流程。
   - CLI、聊天模式、工具模式都走同一个 executor。

2. 补充自动化回归测试。
   - `resume=False` 不跳过 Phase。
   - Phase 4 prompt `.format()` 安全。
   - `test_base.h` 与测试生成规则一致。
   - no-test-files 必须失败。
   - Windows 反斜杠路径提取。

3. 清理 Phase 职责。
   - 合并 Phase 5 和 Phase 7。
   - 明确 Phase 6/8 是生成还是验证。
   - Phase 9 从报告型审查升级为质量 gate。

4. 修复调度器显示。
   - 当前增强调度器仍有空标签输出。
   - 应恢复为明确文本：

```text
Timeout: Enabled
Retry: Enabled
Checkpoint: Disabled
```

### 6.2 第二阶段：把 Spec-First 模块真正接入主流程

目标：从“文档喂给 LLM”升级为“结构化 Spec 驱动”。

建议任务：

1. Phase 1 输出结构化 Requirement Model。
   - 解析需求 ID。
   - 解析验收标准。
   - 解析优先级。
   - 解析功能标签。
   - 保存到 `.spec/requirements.json`。

2. Phase 3 基于 Requirement Model 生成设计。
   - 每个设计决策关联需求 ID。
   - 技术设计输出结构化段落。
   - 保存到 `.spec/design.json`。

3. Phase 4 生成代码时带 Trace Metadata。
   - 每个文件说明覆盖哪些需求。
   - 每个测试说明验证哪些验收标准。

4. 接入 ArtifactGraph。
   - 需求 -> 设计 -> 代码 -> 测试 -> 文档。
   - 生成 `.spec/artifact_graph.json`。

5. Phase 11 输出验收矩阵。

示例：

```text
REQ-001 用户注册
  实现: src/authentication_service.cpp
  测试: tests/test_authentication.cpp::testRegister
  状态: Passed
```

### 6.3 第三阶段：增量开发和安全覆盖

目标：让系统可以安全修改已有项目，而不是只生成新项目。

建议任务：

1. 引入 DeltaSpec 到 Phase 4。
   - AI 不直接覆盖文件。
   - 先生成 patch/delta。
   - 通过验证后再应用。

2. 保护用户代码。
   - 区分 generated region 和 user region。
   - 不覆盖用户手写逻辑。
   - 对已有项目默认生成 diff。

3. 增加变更影响分析。
   - 修改需求时只影响相关文件。
   - 根据 ArtifactGraph 选择性重跑测试。

4. 增加回滚机制。
   - 每次 Phase 4/10 自愈前生成 snapshot。
   - 修复失败自动回滚。

### 6.4 第四阶段：提升 AI 生成质量

目标：减少依赖编译失败后的自愈。

建议任务：

1. Prompt 契约测试。
   - Phase 3 prompt 测试。
   - Phase 4 prompt 测试。
   - Self-healer prompt 测试。
   - 所有 `.format()` 安全测试。

2. 生成前提供机器可读上下文。
   - `test_base.h` API。
   - CMake target 名。
   - namespace。
   - 项目结构。
   - 文件覆盖规则。

3. 模型输出 schema 化。

示例：

```json
{
  "files": [],
  "requirements_covered": [],
  "tests_generated": [],
  "known_limitations": []
}
```

4. 自愈模型显式支持 fallback。
   - 确认 `use_fallback` 是否真的切换模型。
   - 建议 `llm_client.generate(..., model=...)` 支持显式模型参数。

### 6.5 第五阶段：产品化能力

目标：从内部脚本变成长期可维护的开发工具。

建议任务：

1. 标准 CLI。

```bash
devpal openspec init
devpal openspec plan requirements/simple_login.md
devpal openspec apply
devpal openspec test
devpal openspec verify
devpal openspec resume
```

2. 标准状态目录。

```text
.spec/
  requirements.json
  design.json
  plan.json
  tasks.json
  artifacts.json
  traceability.json
  checkpoints/
  reports/
```

3. dry-run 模式。
   - 只生成计划。
   - 不写文件。
   - 输出 diff。

4. CI 模式。
   - 无交互。
   - 固定模型。
   - 固定随机性。
   - 输出 JUnit/JSON 报告。

5. 多项目类型支持。
   - C++ CLI。
   - Python 包。
   - Web API。
   - React 前端。
   - Rust CLI。
   - Go service。

## 7. 推荐优先级

### P0：必须马上做

1. 给当前完整流程加回归测试。
2. 修复增强调度器空标签显示。
3. 统一 OpenSpec 主入口。
4. 增加 Phase 4 prompt 契约测试。
5. 增加 `test_base.h` 与测试生成规则一致性测试。

### P1：核心能力升级

1. Requirement Model 结构化。
2. ArtifactGraph 接入主流程。
3. Phase 11 输出需求验收矩阵。
4. checkpoint 保存完整 context。
5. 合并 Phase 5 和 Phase 7。

### P2：对标开源能力

1. DeltaSpec 增量修改。
2. dry-run / diff 模式。
3. selective test。
4. rollback。
5. CI 报告格式。

### P3：产品化

1. 标准 CLI。
2. 插件化语言支持。
3. Web UI 可视化流程。
4. 需求覆盖率 dashboard。
5. 模型成本和耗时统计。

## 8. 总结

当前 DevPalAgent 的方向正确，已经具备可运行的 OpenSpec 自动化闭环。但当前最核心的问题是：

```text
OpenSpec 的流程已经跑通，但 OpenSpec 的规范对象、追踪关系、增量验证、质量门禁还没有真正成为主架构。
```

下一步建议不要继续简单增加 Phase，而是把已有的 schema、ArtifactGraph、DeltaSpec、ValidationEngine 接入主流程。这样系统才能从“AI 自动生成项目工具”升级为真正的“Spec-First 自动化开发系统”。
