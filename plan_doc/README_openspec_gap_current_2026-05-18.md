# DevPalAgent vs OpenSpec 当前差距评估与后续规划

**日期**：2026-05-18  
**基准文档**：[gap_analysis_vs_openspec_2026-05-16.md](gap_analysis_vs_openspec_2026-05-16.md)  
**当前基线**：截至最近提交 `a5630f2 docs: expand README architecture overview`  
**评估对象**：当前 README、OpenSpec 11 阶段实现、Phase 2/9/10/11、installer e2e、schema/tooling 代码现状

---

## 1. 结论摘要

相比 2026-05-16 的 gap 分析，DevPalAgent 已经从“C++ 专用自动代码生成流水线”推进到“语言感知、Spec-first、可验证、可报告的 Agentic SDLC Runtime”。当前最重要的变化是：**M1：语言感知闭环稳定版已经基本完成**，后续重点应从多语言基础收敛转向 **M2：OpenSpec Change MVP**。

当前判断：

1. **README 已补齐系统架构表达**
   - README 已把架构章节提前到能力状态之前。
   - 已明确 `Planner → Executor → Reflector` 的 Plan-Act-Reflect 模式。
   - 已明确 `OpenSpecWorkflowExecutor → EnhancedScheduler → OpenSpecContext → Phase 1-11` 的 Runtime 架构。
   - 已补充 Agent 主引擎、ToolRegistry、ValidationEngine、DeltaSpec、ArtifactGraph、EventBus、PromptEngine、LanguagePlugin、TestRunner 等核心模块。

2. **M1 语言感知闭环已完成**
   - Phase 2 已根据 `language/project_type` 创建目录，installer 不再生成 C++ `include/` 遗留目录。
   - Phase 9 已按语言/项目类型运行质量门禁，installer/Python 不再误报 C++ 文件缺失。
   - Phase 10 已支持 Python pytest；installer/tooling 场景通过 skip rules 正确跳过。
   - Phase 11 / `CLAUDE.md` 已语言感知，installer 的 coding section 不再出现 `.cpp`、`test_base.h`、`CMake` 等 C++ 遗留内容。
   - `tests/e2e/test_installer_flow.py` 已覆盖 installer flow 的 skipped phase、quality gate、final report、CLAUDE.md 语义。

3. **ValidationEngine 已从“未接入”变成“主流程部分接入”**
   - Phase 9 已运行 FORMAT / SEMANTIC / PARSER / BUSINESS 四层校验。
   - 当前仍偏文件结构、语言语法、基础规则校验。
   - 尚未形成 OpenSpec 式“需求场景 → 实现 → 测试”的需求级语义验证。

4. **Spec Delta 与需求对象化仍处于半成品阶段**
   - Phase 1 已解析 structured requirements、scenarios、priority、status，并输出 `.spec/delta.json`。
   - 但仍缺 `openspec/changes/<change-id>/proposal.md/spec.md/tasks.md`。
   - 仍缺 OpenSpec 风格 `ADDED/MODIFIED/REMOVED Requirements` markdown delta。
   - 仍缺 archive 合并到 main spec 的生命周期闭环。

5. **DevPalAgent 的差异化优势更清晰**
   - OpenSpec 强在规范协作、变更隔离、归档和 AI-agnostic 上下文。
   - DevPalAgent 强在端到端自动生成、质量门禁、测试执行、自愈、checkpoint 和 final report。
   - 后续不建议重写 11 阶段流水线，而应在现有 runtime 外围补齐 OpenSpec change/archive/traceability 层。

---

## 2. 当前与 2026-05-16 文档的差异

| 能力项 | 2026-05-16 状态 | 2026-05-18 当前状态 | 变化 |
|---|---|---|---|
| 11 阶段流水线 | 已实现 | 已实现，enhanced scheduler 成为稳定入口 | 稳定 |
| README 架构表达 | 旧 README 很细但新版缺 Planner/Reflector/Executor 细节 | 已补齐架构模式和核心模块说明 | 明显提升 |
| Phase 跳过逻辑 | 未体现 | installer 项目稳定跳过 Phase 3/5/6/7/10 | 新增并稳定 |
| Checkpoint | 有，但曾误生成 `cpp_` 目录 | checkpoint/project path 已按语言与项目类型修正 | 修复 |
| Phase 1 需求解析 | 基础结构化 | 已含 features/project_type/scenarios/priority/status/delta.json | 提升 |
| Spec Delta | 部分 | 仍为部分，有 `.spec/delta.json`，无 markdown delta | 小幅提升 |
| ValidationEngine | 文档称未接入 | Phase 9 已接入四层校验 | 明显提升 |
| Phase 9 质量门禁 | C++ 检查为主 | 按 language/project_type 选择检查 | 提升 |
| Phase 2 目录结构 | C++ 默认结构为主 | C++/Python/Shell/installer 目录结构语言感知 | 明显提升 |
| Python 支持 | 基本无 | Python skeleton、pytest、Python prompt、Python quality checks | 明显提升 |
| installer 支持 | 无 | installer flow smoke/e2e 已覆盖 skipped/report/quality gate | 明显提升 |
| Prompt 系统 | 静态 C++ prompt | PromptTemplateEngine + LanguageFeatures 已接入 Phase 4 | 新增 |
| CLAUDE.md | 文档称缺失 | Phase 11 已生成，且已语言感知 | 明显提升 |
| 测试统计 | 默认 `0/0 passed` | skipped 场景显示 skipped/not applicable | 修复 |
| OpenSpec changes | 缺失 | 仍缺失 | 未变 |
| Archive | 缺失 | 仍缺失 | 未变 |
| EventBus 主流程化 | 未主流程化 | 仍未主流程化 | 未变 |

---

## 3. 综合差距评分（当前版）

评分以开源 OpenSpec 的规范协作能力为 5 分满分，同时保留 DevPalAgent 在自动化生成和验证闭环上的差异化优势。

| 维度 | OpenSpec | DevPalAgent 当前 | 2026-05-16 估计 | 当前差距 | 说明 |
|---|:---:|:---:|:---:|---|---|
| 规范管理 Spec Management | 5 | 2.5 | 2 | 大 | 有需求解析、delta.json、报告，但没有 changes/proposal/tasks/archive 体系 |
| 需求对象化深度 | 4 | 3 | 2 | 中 | 已有 scenarios/priority/status，但 linked_design/code/tests/tags 仍弱 |
| Spec Delta 机制 | 5 | 2.5 | 2 | 大 | 有 JSON delta，不是 OpenSpec markdown delta + archive |
| 变更隔离与归档 | 5 | 1.5 | 1 | 很大 | 缺少 `openspec/changes/<change-id>` 生命周期 |
| Traceability | 3 | 3.5 | 3 | 中偏小 | ArtifactGraph 较强，但缺 change-id 和变更历史追溯 |
| 质量门禁 | 3 | 4 | 3 | 小 | Phase 9 + ValidationEngine + 语言感知已较强 |
| 自动化代码生成 | 2 | 5 | 5 | DevPalAgent 领先 | 仍是核心优势 |
| 编译/测试闭环 | 1 | 4.5 | 5 | DevPalAgent 领先 | C++/Python/installer skip 语义已稳定；需求级覆盖仍需加强 |
| AI 自愈能力 | 1 | 4 | 4 | DevPalAgent 领先 | 已有 Phase 9/10 自愈入口和 test self-healer，但可观测性需加强 |
| 多语言支持 | 5 | 3 | 1 | 中到大 | Phase 2/4/9/10/11 已语言感知，但 LanguagePlugin 未完全主流程化 |
| AI 工具集成 | 5 | 3 | 2 | 中到大 | README/CLAUDE.md 已改善，但缺 changes 目录和 AI-agnostic 命令体系 |

**总体判断**：  
距离 OpenSpec 的“规范协作框架”仍有 **约 40%～50% 差距**；但在“自动生成 + 质量门禁 + 测试执行 + 自愈 + checkpoint/report”方向，DevPalAgent 仍明显领先。当前最大缺口已经不是多语言基础，而是 **OpenSpec Change 生命周期**。

---

## 4. 当前已完成能力清单

### 4.1 Spec-first Runtime

- 11 阶段 OpenSpec workflow 已实现。
- Enhanced scheduler 支持 timeout / retry / checkpoint / progress。
- `OpenSpecPhaseScheduler` 已指向 enhanced scheduler。
- `resume=False` 可禁用 checkpoint，从 Phase 1 重新开始。
- PhaseResult 已能表达 success/fail/skipped，并在 final report 中保留 skipped 语义。

### 4.2 Agent 架构表达

- README 已明确两条主链路：
  - 经典 Agent：`Planner → Executor → Reflector`。
  - OpenSpec Runtime：`WorkflowExecutor → Scheduler → Context → Phase 1-11`。
- README 已补充核心模块：
  - `agent_engine.py`
  - `planner.py`
  - `reflector.py`
  - `tools/registry.py`
  - `validation_engine.py`
  - `delta_spec.py`
  - `artifact_graph.py`
  - `event_bus.py`
  - `prompt_engine.py`
  - `language_config.py`
  - Phase 1-11 实现文件

### 4.3 Installer / Python / Shell 语言感知

- Phase 1 可识别 installer/tooling 类项目。
- installer 项目会设置：
  - `context.is_cpp = False`
  - `context.language = "python"`
  - `context.features` 包含 install 语义
  - `context.project_type = "installer"`
- Phase 2 目录结构语言感知：
  - installer/tooling/cli_tool：`src`、`tests`、`docs`、`.spec`
  - Python：来自 `LanguageFeatures.project_structure`
  - 非 C++ 项目不会生成 `include/`
- Phase 4 使用 PromptTemplateEngine 和语言特征生成动态 prompt。
- Phase 9 按语言/项目类型选择检查器。
- Phase 10 对 Python 项目使用 pytest。
- Phase 11 / CLAUDE.md 已按语言和项目类型输出文件结构、命名规范、测试结果。

### 4.4 Installer 跳过规则与 e2e

installer/tooling 项目会跳过：

- Phase 3：不生成 AI 技术设计。
- Phase 5：不生成测试代码/测试文档。
- Phase 6：不生成 CMake。
- Phase 7：不生成测试文档。
- Phase 10：不编译运行测试。

已由 `tests/e2e/test_installer_flow.py` 覆盖：

- Phase 3/5/6/7/10 success + skipped。
- 不生成 `cpp_test_phase_skip`。
- final report 不出现 `0/0 passed`。
- quality gate 不出现 C++ 缺失误报。
- CLAUDE.md coding section 不出现 `.cpp`、`test_base.h`、`CMake`。

### 4.5 报告与统计修复

- skipped phase 会记录：
  - `skipped=True`
  - `skip_reason`
- skipped Phase 10 会记录：
  - `test_skipped=True`
  - `test_status="skipped"`
  - `test_summary="skipped (...)"`
- Phase 11 与 chat summary 不再显示 `0/0 passed`。
- Phase 状态表显示 skipped，不再误导成 OK/passed。

### 4.6 Phase 9 ValidationEngine 接入

- Phase 9 已运行四层校验：
  - FORMAT
  - SEMANTIC
  - PARSER
  - BUSINESS
- 校验按语言/项目类型选择：
  - C++：CMake/main.cpp/test_base/test_*.cpp 等。
  - Python：main.py/__main__.py + pytest 文件等。
  - installer/tooling：跳过不适用 C++ 检查。
- quality gate report 已输出 validation details。

### 4.7 Prompt、模板与安装脚本能力

- 新增 `PromptTemplateEngine`。
- 新增 `LanguageFeatures` 配置：C++、Python、Shell。
- Python 模板已从固定 auth 业务模板改为 skeleton/readme 基础模板，业务逻辑交给 AI 生成。
- 新增安装脚本生成器。
- 支持 i18n message collection。
- bash installer 会检测 `claude` 是否已安装，已安装时打印 `install.already_installed` 并退出。
- 新增 installer CLI 命令雏形。

---

## 5. 仍存在的主要差距

### 5.1 缺少 OpenSpec changes 目录模型

当前仍没有类似：

```text
openspec/
└── changes/
    └── add-feature/
        ├── proposal.md
        ├── specs/spec.md
        ├── design.md
        ├── tasks.md
        └── metadata.json
```

现有流程仍是从单个 requirements markdown 直接进入 11 阶段流水线。  
这导致：

- 无法隔离多个并行变更。
- 无法回答“某需求由哪个 change 引入”。
- 无法 archive 已完成变更。
- 无法把 delta 合并到主规范。
- 无法让 Claude Code / Cursor / Cline 直接读取 OpenSpec 风格上下文。

### 5.2 Delta 仍不是 OpenSpec 语义 Delta

当前 `.spec/delta.json` 偏执行产物，不是用户可审阅的规范文档。缺少：

```markdown
## ADDED Requirements
## MODIFIED Requirements
## REMOVED Requirements
```

也缺少 Given/When/Then 与 delta 的强绑定。

### 5.3 需求生命周期没有完整闭环

已有 `PROPOSED / IN_PROGRESS / VERIFIED / FAILED` 的基础状态，但还不完整：

- Phase 4 会标记 IN_PROGRESS。
- Phase 10/11 的 VERIFIED/FAILED 语义对 skipped/not applicable 场景仍需需求级细化。
- 没有 ARCHIVED 状态。
- 没有 requirement → design/code/test 的强元数据字段。
- 没有 requirement/scenario coverage matrix。

### 5.4 ArtifactGraph 与 Delta/Archive 未打通

ArtifactGraph 可以表达需求到代码/测试/报告的关系，但目前还不能表达：

- requirement introduced_by change-id
- requirement modified_by change-id
- requirement archived_at
- scenario covered_by test-id
- validation result linked_to requirement-id
- final report 中的 requirement coverage matrix

### 5.5 多语言支持仍未完全插件化

M1 已完成“语言感知闭环”，但还不是统一插件架构：

- Phase 2/4/9/10/11 已分别语言感知。
- `language_config.py` 和 Python/Shell plugin 已存在。
- 但 `LanguagePlugin` 还没有成为所有 phase 的统一接口。
- build/test/quality/prompt/template 仍分散在不同 phase 的条件分支中。

### 5.6 AI-agnostic 能力不足

DevPalAgent 仍强依赖 Anthropic API 和内部 runtime。与 OpenSpec 相比缺少：

- AI 工具可直接读取的 changes/proposal/tasks 目录。
- `/opsx:propose`、`/opsx:apply` 风格命令。
- Cursor/Cline/Copilot 可复用的规范上下文。
- 不依赖 API key 的 propose-only / apply-only / dry-run 模式。

### 5.7 EventBus / RolloutEngine 仍未主流程化

Schema 里已有：

- `event_bus.py`
- `rollout_engine.py`
- `diagnostic_engine.py`
- `error_manager.py`
- `config_policy.py`

但主流程仍主要是顺序调度，事件、诊断、渐进发布没有成为核心运行机制。

---

## 6. 后续规划

### P0：保持 M1 稳定性并补普通 Python app smoke（0.5～1 天）

M1 已基本完成，不建议继续扩大 scope。P0 只保留少量稳定性补强。

任务：

1. 增加普通 Python app smoke fixture。
   - 验证非 installer Python 项目不会跳过 Phase 10。
   - 验证 pytest 真执行并写入 canonical test counters。

2. 将 README 中的验证命令与当前测试集保持同步。
   - `tests/e2e/test_installer_flow.py`
   - `tests/openspec/test_phase9_quality_gate.py`
   - `tests/openspec/test_phase10_run_tests.py`
   - `tests/openspec/test_spec_first_artifacts.py`

3. 明确运行产物忽略策略。
   - `.spec/`
   - generated project dirs
   - checkpoint dirs
   - pytest/cache artifacts

验收：

```bash
python -m pytest tests/openspec/test_spec_first_artifacts.py tests/openspec/test_phase10_run_tests.py tests/openspec/test_phase9_quality_gate.py tests/e2e/test_installer_flow.py
```

---

### P1：实现 OpenSpec Change MVP（2～3 天）

目标：引入 OpenSpec 最核心的 changes/proposal/spec/tasks 结构，作为现有 11 阶段 runtime 的上游规范层。

新增目录建议：

```text
openspec/
├── project.md
├── specs/
│   └── main.md
└── changes/
    └── <change-id>/
        ├── proposal.md
        ├── specs/spec.md
        ├── design.md
        ├── tasks.md
        └── metadata.json
```

任务：

1. 新增 `OpenSpecChange` 数据模型。
2. 新增 change-id 生成规则。
3. Phase 1 支持从 requirements markdown 生成 proposal/spec/tasks 草案。
4. Phase 3 design 输出到 change 目录。
5. Phase 4 读取 tasks/spec/design 进行实现。
6. Phase 11 final report 引用 change-id 和 change artifacts。

优先文件：

- `devpal/core/schema/spec.py`
- `devpal/core/schema/workflow.py`
- `devpal/core/schema/requirements.py`
- `devpal/core/openspec_phases/phase1_parse_requirements.py`
- `devpal/core/openspec_phases/phase3_technical_design.py`
- `devpal/core/openspec_phases/phase4_generate_code.py`
- `devpal/core/openspec_phases/phase11_final_report.py`

验收：

- 每次运行生成稳定 `change-id`。
- `openspec/changes/<change-id>/proposal.md` 存在。
- `openspec/changes/<change-id>/specs/spec.md` 存在。
- `openspec/changes/<change-id>/tasks.md` 存在。
- final report 能显示 change-id 和 change artifacts。

---

### P1：实现 Markdown Delta Spec（1～2 天）

目标：让 delta 从 JSON 执行产物升级为可审阅规范文档。

新增输出：

```text
<project>/.spec/delta.json
openspec/changes/<change-id>/specs/spec.md
```

`spec.md` 格式：

```markdown
## ADDED Requirements
### REQ-001: xxx
- Given: ...
- When: ...
- Then: ...

## MODIFIED Requirements
...

## REMOVED Requirements
...
```

验收：

- 每次运行可生成 spec delta markdown。
- `requirements.json`、`.spec/delta.json` 与 `spec.md` 一致。
- 缺少 Given/When/Then 时 Phase 9 能提示 warning。

---

### P2：Archive 归档机制（2 天）

目标：完成 OpenSpec 生命周期闭环。

任务：

1. 新增 `archive_change(change_id)`。
2. 将 `changes/<id>/specs/spec.md` 合并到 `openspec/specs/main.md`。
3. 将 change metadata 标记为 ARCHIVED。
4. ArtifactGraph 记录 introduced_by/modified_by/archived_at。

验收：

```bash
python -m devpal openspec archive add-installer
```

---

### P2：需求级验证与场景覆盖（2～3 天）

目标：Phase 9/10 不仅检查文件存在，还检查需求是否被实现和测试覆盖。

任务：

1. 每个 requirement/scenario 生成稳定 ID。
2. Phase 4 写入 ArtifactGraph：code implements requirement。
3. Phase 5/10 写入 ArtifactGraph：test verifies scenario。
4. Phase 9 输出 coverage matrix：
   - requirement has code
   - requirement has test
   - scenario has test
   - skipped/not applicable reason

---

### P3：LanguagePlugin 主流程化（3～5 天）

目标：把当前 language_config/plugin/prompt/template 统一为单一接口。

接口建议：

```python
class LanguagePlugin:
    def project_structure(self) -> dict: ...
    def infrastructure_templates(self) -> list: ...
    def build_command(self) -> list: ...
    def test_command(self) -> list: ...
    def quality_checks(self) -> list: ...
    def prompt_features(self) -> LanguageFeatures: ...
```

迁移顺序：

1. Phase 2 目录结构。
2. Phase 4 prompt + infra templates。
3. Phase 9 validation checks。
4. Phase 10 test runner。
5. Phase 11 docs/CLAUDE.md。

---

### P3：EventBus 主流程接入（1～2 天）

目标：让流水线从“顺序脚本”升级为“事件可观测系统”。

建议事件：

- `RequirementParsed`
- `RequirementChanged`
- `PhaseStarted`
- `PhaseCompleted`
- `FileGenerated`
- `ValidationCompleted`
- `TestCompleted`
- `ChangeArchived`

输出：

```text
.spec/events.jsonl
```

注意：事件日志应作为运行产物，不建议默认提交到 git。

---

## 7. 建议里程碑

### M1：语言感知闭环稳定版

状态：已完成。

已覆盖：

- Phase 2 目录语言感知。
- Phase 4 Prompt Engine 语言感知。
- Phase 9 质量门禁语言感知。
- Phase 10 Python pytest + installer skipped 语义。
- Phase 11 / CLAUDE.md 语言感知。
- installer e2e 覆盖 skipped/report/quality gate/CLAUDE.md。

### M2：OpenSpec Change MVP

状态：下一阶段重点。

目标：具备 proposal/spec/tasks/change-id 的最小模型。

包含：

- `openspec/project.md`
- `openspec/specs/main.md`
- `openspec/changes/<change-id>/proposal.md`
- `openspec/changes/<change-id>/specs/spec.md`
- `openspec/changes/<change-id>/tasks.md`
- `metadata.json`
- Phase 4 基于 tasks/spec/design 实现
- Phase 11 引用 change artifacts

### M3：Archive + Traceability

目标：能回答“需求从哪里来、被什么实现、由什么测试覆盖、何时归档”。

包含：

- archive 命令。
- main spec 合并。
- ArtifactGraph introduced_by/modified_by/archived_at。
- Requirement/scenario coverage matrix。

### M4：AI-agnostic 协作模式

目标：DevPalAgent 不仅能自己调用 API，还能服务 Claude Code / Cursor / Cline。

包含：

- CLAUDE.md 完整化。
- changes 目录文档化。
- slash-command 风格工作流说明。
- dry-run / propose-only / apply-only 模式。

---

## 8. 下一步建议

优先做 **M2：OpenSpec Change MVP**。理由：

1. M1 已完成，继续补语言细节的边际收益下降。
2. 当前最大 OpenSpec 差距是 changes/proposal/spec/tasks/archive，而不是 Phase 执行能力。
3. DevPalAgent 已有稳定 runtime，适合在 runtime 前面加规范变更层，而不是重写调度器。
4. M2 完成后，README、CLAUDE.md、final report、ArtifactGraph 都可以围绕 change-id 形成更强的项目故事。

建议下一批任务：

1. 新增 `OpenSpecChange` 数据模型。
2. Phase 1 生成 `openspec/changes/<change-id>/proposal.md`。
3. Phase 1 同步生成 `openspec/changes/<change-id>/specs/spec.md`，采用 `ADDED Requirements` 格式。
4. Phase 1/3 生成或更新 `tasks.md`、`design.md`。
5. Phase 4 读取 change 目录，而不是只依赖内存里的 requirements。
6. Phase 11 final report 输出 change-id、proposal/spec/tasks/design 路径。
7. 增加 e2e：断言 change 目录存在、spec.md 与 requirements.json 一致。

---

## 9. 风险与注意事项

1. **不要一次性重构所有 Phase**  
   当前流程能跑通，建议先加 OpenSpec change 层，再逐步把 Phase 输入切到 change artifacts。

2. **不要把 OpenSpec 当成替代 runtime**  
   OpenSpec 应成为规范层，DevPalAgent 的核心竞争力仍是自动生成、验证、自愈、checkpoint、report。

3. **避免运行产物进入 git**  
   `.spec/events.jsonl`、checkpoint、生成项目目录、测试输出应默认忽略或清理。

4. **区分 skipped、not applicable 与 passed**  
   installer 这类项目“不适用测试”应显示 skipped/not applicable，不能显示 passed 或 `0/0`。

5. **多语言不是只改 Prompt**  
   M1 已证明真正的多语言需要 Phase 2/4/9/10/11 全链路一致；后续 LanguagePlugin 主流程化也应遵循这个原则。

6. **M2 的关键是 change-id 稳定性**  
   如果 change-id 不稳定，ArtifactGraph、archive、final report、AI 工具上下文都会难以追踪。
