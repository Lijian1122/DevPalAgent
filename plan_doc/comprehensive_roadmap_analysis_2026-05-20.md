# DevPalAgent 综合规划与现状分析

**日期**：2026-05-20  
**基准**：README.md Roadmap + 项目当前状态  
**目标**：结合 README 路线图，综合分析项目现状，制定后续发展规划

---

## 1. 执行摘要

DevPalAgent 已从"C++ 专用代码生成工具"演进为"Spec-first Agentic SDLC Runtime"。当前处于 **M1（语言感知闭环稳定版）已完成** 阶段，后续发展应聚焦于：

1. **M2：OpenSpec Change MVP** - 补齐 OpenSpec 核心变更管理模型
2. **M3：Archive + Traceability** - 完善需求生命周期闭环
3. **M4：AI-agnostic 协作模式** - 服务更广泛的 AI 编码工具生态
4. **Skill 系统接入** - 提升任务级能力编排

核心判断：
- ✅ 已具备端到端自动生成、质量门禁、测试执行、自愈能力
- ✅ 多语言基础（C++/Python/Shell/installer）已稳定
- ⚠️ 与 OpenSpec 规范协作框架仍有 40-50% 差距
- 🎯 下一阶段重点：OpenSpec Change 生命周期 > 多语言细节优化

---

## 2. 当前能力矩阵

### 2.1 核心架构（已完成）

| 组件 | 状态 | 说明 |
|---|:---:|---|
| Plan-Act-Reflect 架构 | ✅ | Planner → Executor → Reflector 链路完整 |
| OpenSpec 11 阶段流水线 | ✅ | Phase 1-11 已实现并稳定 |
| Enhanced Scheduler | ✅ | timeout/retry/checkpoint/resume/progress |
| OpenSpecContext | ✅ | 共享状态总线，支持阶段间数据传递 |
| ToolRegistry | ✅ | 文件/Git/测试/审查/自改进工具完整 |
| Memory 系统 | ✅ | 短期/长期/错误记忆三层架构 |

### 2.2 Spec-first 能力（部分完成）

| 能力 | 状态 | 完成度 | 说明 |
|---|:---:|:---:|---|
| Structured Requirements | ✅ | 90% | 已解析 id/title/description/scenarios/priority/status |
| Delta JSON | ✅ | 60% | 有 `.spec/delta.json`，但不是 OpenSpec markdown delta |
| ArtifactGraph | ✅ | 70% | 可追踪需求→代码/测试/报告，缺 change-id 关联 |
| ValidationEngine | ✅ | 80% | 四层验证已接入 Phase 9 |
| OpenSpec Changes | ❌ | 0% | 缺少 `openspec/changes/<id>/` 目录模型 |
| Archive 机制 | ❌ | 0% | 无法合并 delta 到 main spec |
| Requirement Coverage | ⚠️ | 30% | 有基础追踪，缺场景级覆盖矩阵 |

### 2.3 多语言支持（已完成 M1）

| 语言/项目类型 | Phase 2 | Phase 4 | Phase 9 | Phase 10 | Phase 11 |
|---|:---:|:---:|:---:|:---:|:---:|
| C++ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Python | ✅ | ✅ | ✅ | ✅ | ✅ |
| Shell | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ |
| Installer/Tooling | ✅ | ✅ | ✅ | ✅ (skip) | ✅ |

说明：
- ✅ = 已语言感知并稳定
- ⚠️ = 基础支持，但未完全主流程化
- Phase 2：目录结构语言感知
- Phase 4：Prompt Engine + 语言特征
- Phase 9：按语言选择质量检查器
- Phase 10：C++ 编译/Python pytest/installer skip
- Phase 11：CLAUDE.md 语言感知

### 2.4 质量保障（已完成）

| 能力 | 状态 | 说明 |
|---|:---:|---|
| Phase 9 Quality Gate | ✅ | FORMAT/SEMANTIC/PARSER/BUSINESS 四层验证 |
| Phase 10 Test Execution | ✅ | C++ 编译测试 + Python pytest |
| Skipped 语义 | ✅ | installer 项目正确跳过不适用阶段 |
| Test Counters | ✅ | passed/failed/skipped 统计准确 |
| Quality Gate Report | ✅ | 输出验证详情和问题列表 |
| Final Report | ✅ | 包含 ArtifactGraph、测试摘要、CLAUDE.md |
| Self-healing 入口 | ✅ | Phase 9/10 已预留自愈接口 |

### 2.5 可追踪性（部分完成）

| 能力 | 状态 | 完成度 | 说明 |
|---|:---:|:---:|---|
| Requirements → Code | ✅ | 80% | ArtifactGraph 可追踪 |
| Requirements → Tests | ✅ | 80% | ArtifactGraph 可追踪 |
| Requirements → Docs | ✅ | 80% | ArtifactGraph 可追踪 |
| Change → Requirements | ❌ | 0% | 缺 change-id 关联 |
| Scenario → Test Coverage | ⚠️ | 30% | 缺场景级覆盖矩阵 |
| Validation → Requirements | ⚠️ | 40% | 缺需求级验证结果关联 |
| Archive History | ❌ | 0% | 无变更归档历史 |

---

## 3. README Roadmap 解读

### M1：语言感知闭环稳定版 ✅

**状态**：已完成

**已交付**：
- Phase 2 语言感知目录结构
- Phase 9 语言感知质量门禁
- Phase 10 Python pytest canonical result
- Phase 11 / CLAUDE.md 语言感知
- installer e2e 覆盖

**验证命令**：
```bash
python -m pytest tests/openspec/test_spec_first_artifacts.py \
               tests/openspec/test_phase10_run_tests.py \
             tests/openspec/test_phase9_quality_gate.py \
                 tests/e2e/test_installer_flow.py
```

**最近测试结果**：22 passed, 2 warnings

### M2：OpenSpec Change MVP 🎯

**状态**：下一阶段重点

**目标**：补齐 OpenSpec 核心 changes/proposal/spec/tasks 模型

**计划输出**：
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
**核心任务**：
1. 新增 `OpenSpecChange` 数据模型
2. change-id 生成规则（建议：`<type>-<feature>-<timestamp>`）
3. Phase 1 从 requirements 生成 proposal/spec/tasks 草案
4. Phase 3 design 输出到 change 目录
5. Phase 4 读取 change artifacts 进行实现
6. Phase 11 final report 引用 change-id

**优先文件**：
- `devpal/core/schema/spec.py`
- `devpal/core/schema/workflow.py`
- `devpal/core/schema/requirements.py`
- `devpal/core/openspec_phases/phase1_parse_requirements.py`
- `devpal/core/openspec_phases/phase3_technical_design.py`
- `devpal/core/openspec_phases/phase4_generate_code.py`
- `devpal/core/openspec_phases/phase11_final_report.py`

**验收标准**：
- ✅ 每次运行生成稳定 change-id
- ✅ `openspec/changes/<id>/proposal.md` 存在
- ✅ `openspec/changes/<id>/specs/spec.md` 存在（ADDED/MODIFIED/REMOVED 格式）
- ✅ `openspec/changes/<id>/tasks.md` 存在
- ✅ final report 显示 change-id 和 artifacts

**预估工期**：2-3 天

### M3：Archive + Traceability

**状态**：M2 后续

**目标**：需求生命周期闭环

**核心能力**：
- `archive_change(change_id)` 命令
- spec delta 合并到 main spec
- ArtifactGraph 增加 introduced_by/modified_by/archived_at
- final report 输出 requirement coverage matrix

**关键任务**：
1. 实现 archive 命令
2. Delta merge 逻辑
3. ArtifactGraph 扩展字段
4. Scenario → Test 覆盖追踪
5. Validation → Requirement 关联
6. Coverage matrix 生成

**验收标准**：
```bash
python -m devpal openspec archive <change-id>
# 验证：
# - changes/<id>/metadata.json status=ARCHIVED
# - specs/main.md 包含合并内容
# - ArtifactGraph 记录归档信息
# - final report 显示覆盖矩阵
```

**预估工期**：3-4 天

### M4：AI-agnostic 协作模式

**状态**：长期目标

**目标**：DevPalAgent 不仅自己调用 LLM，也能服务 Claude Code / Cursor / Cline

**核心能力**：
- 完整 CLAUDE.md 生成
- changes 目录文档化
- propose-only / apply-only 模式
- AI 助手可直接读取的规范上下文
- 不依赖 API key 的 dry-run 模式

**关键任务**：
1. CLAUDE.md 模板完善
2. changes 目录 README 生成
3. `/opsx:propose` 风格命令
4. `/opsx:apply` 风格命令
5. dry-run 模式实现
6. Cursor/Cline 集成文档

**预估工期**：5-7 天

---

## 4. 补充规划：Skill 系统接入

### 4.1 背景
当前 DevPalAgent 有 Tool（原子能力）和 OpenSpec（长流程），但缺少中间层的任务级能力编排。

### 4.2 Skill 定位

> 面向用户意图的任务级能力包，用于编排多个 Tool、OpenSpec 工作流、模板系统和语言插件。

**分层**：
```text
User Query
  ↓
Skill (任务编排)
  ↓
Tool (原子能力) / OpenSpec (长流程) / Template (模板) / LanguagePlugin (语言分析)
```

### 4.3 核心抽象

**SkillContext**：
```python
class SkillContext(BaseModel):
    user_query: str
    workspace_path: Path
    tool_registry: ToolRegistry
    config: dict = {}
    metadata: dict = {}
```

**SkillResult**：
```python
class SkillResult(BaseModel):
    success: bool
  content: str
    artifacts: list[str] = []
    metadata: dict = {}
```

**BaseSkill**：
```python
class BaseSkill(ABC):
    name: str
    description: str
    triggers: list[str] = []
    required_tools: list[str] = []
    
    def can_handle(self, context: SkillContext) -> float:
        return 0.0
    
    @abstractmethod
    def execute(self, context: SkillContext) -> SkillResult:
        pass
```

### 4.4 内置 Skill 规划

| Skill | 优先级 | 职责 | 复用能力 |
|---|:---:|---|---|
| installer_skill | P0 | 安装脚本生成 | InstallScriptGenerator |
| code_review_skill | P1 | 代码审查编排 | code_review/static_analyzer/hallucination_detector |
| test_generation_skill | P1 | 测试生成编排 | test_generator/test_runner/test_doc_generator |
| openspec_skill | P2 | OpenSpec 入口 | OpenSpecWorkflowExecutor |

### 4.5 分阶段落地

**Phase 1：Skill 内核**（1-2 天）
- 新增 `devpal/skills/base.py`
- 新增 `devpal/skills/registry.py`
- 新增 `devpal/skills/router.py`
- 改造 `devpal/core/agent_engine.py`

**Phase 2：installer_skill**（1 天）
- 新增 `devpal/skills/builtin/installer.py`
- 复用 `InstallScriptGenerator`
- 测试自动路由

**Phase 3：code_review + test_generation**（2 天）
- 新增 `devpal/skills/builtin/code_review.py`
- 新增 `devpal/skills/builtin/test_generation.py`
- 编排现有工具

**Phase 4：openspec_skill**（1 天）
- 新增 `devpal/skills/builtin/openspec.py`
- 委托 OpenSpecWorkflowExecutor

**总预估工期**：5-6 天

---

## 5. 综合优先级排序

### P0：保持 M1 稳定性（0.5-1 天）

**任务**：
1. 增加普通 Python app smoke fixture
2. 同步 README 验证命令与测试集
3. 明确运行产物忽略策略（`.spec/`、checkpoint、生成目录）

**验收**：
```bash
python -m pytest tests/openspec/ tests/e2e/
# 全部通过
```

### P1：M2 OpenSpec Change MVP（2-3 天）

**任务**：
1. OpenSpecChange 数据模型
2. change-id 生成规则
3. Phase 1 生成 proposal/spec/tasks
4. Phase 3 design 输出到 change 目录
5. Phase 4 读取 change artifacts
6. Phase 11 引用 change-id
7. 增加 e2e 测试

**验收**：
- change 目录结构完整
- spec.md 采用 ADDED/MODIFIED/REMOVED 格式
- final report 显示 change-id

### P1：Markdown Delta Spec（1-2 天）

**任务**：
1. Delta markdown 生成逻辑
2. Given/When/Then 格式化
3. Phase 9 缺失 Given/When/Then 时 warning

**验收**：
- `openspec/changes/<id>/specs/spec.md` 可读性强
- 与 `.spec/delta.json` 一致

### P2：Skill 系统接入（5-6 天）

**任务**：
1. Skill 内核（base/registry/router）
2. installer_skill
3. code_review_skill + test_generation_skill
4. openspec_skill
5. 测试覆盖

**验收**：
- 用户请求可自动路由到 Skill
- Skill 可编排现有能力
- 不破坏现有 Plan-Act-Reflect 流程

### P2：M3 Archive + Traceability（3-4 天）

**任务**：
1. archive 命令
2. Delta merge 到 main spec
3. ArtifactGraph 扩展
4. Coverage matrix 生成

**验收**：
```bash
python -m devpal openspec archive <change-id>
# 验证归档成功
```

### P3：LanguagePlugin 主流程化（3-5 天）

**任务**：
1. 统一 LanguagePlugin 接口
2. Phase 2/4/9/10/11 迁移到插件接口
3. 移除硬编码语言分支

**验收**：
- 新增语言只需实现 LanguagePlugin
- 不需要修改 Phase 代码

### P3：EventBus 主流程接入（1-2 天）

**任务**：
1. 定义核心事件（RequirementParsed/PhaseStarted/FileGenerated 等）
2. Phase 1-11 发布事件
3. 输出 `.spec/events.jsonl`

**验收**：
- 运行后生成事件日志
- 可观测性提升

### P4：M4 AI-agnostic 协作模式（5-7 天）

**任务**：
1. CLAUDE.md 模板完善
2. changes 目录文档化
3. propose-only / apply-only 模式
4. Cursor/Cline 集成文档

**验收**：
- Claude Code 可直接读取 changes 目录
- dry-run 模式可用

---

## 6. 推荐执行路径

### 路径 A：OpenSpec 优先（推荐）

**理由**：
- M1 已完成，多语言基础稳定
- 当前最大差距是 OpenSpec Change 生命周期
- M2 完成后可显著提升项目故事完整性

**顺序**：
```text
P0 (稳定性) → P1 (M2 Change MVP) → P1 (Markdown Delta) → P2 (M3 Archive) → P2 (Skill) → P3 (LanguagePlugin) → P3 (EventBus) → P4 (M4 AI-agnostic)
```

**总工期**：约 18-25 天

### 路径 B：Skill 优先

**理由**：
- 快速提升用户体验
- installer_skill 可立即展示价值
- 不影响 OpenSpec 主流程

**顺序**：
```text
P0 (稳定性) → P2 (Skill 内核 + installer) → P1 (M2 Change MVP) → P1 (Markdown Delta) → P2 (Skill 扩展) → P2 (M3 Archive) → P3 (LanguagePlugin) → P3 (EventBus) → P4 (M4 AI-agnostic)
```

**总工期**：约 18-25 天
### 路径 C：并行推进

**理由**：
- Skill 和 OpenSpec Change 相对独立
- 可并行开发

**顺序**：
```text
P0 (稳定性)
  ↓
并行：
  - P1 (M2 Change MVP) + P1 (Markdown Delta)
  - P2 (Skill 内核 + installer)
  ↓
并行：
  - P2 (M3 Archive)
  - P2 (Skill 扩展)
  ↓
P3 (LanguagePlugin) → P3 (EventBus) → P4 (M4 AI-agnostic)
```

**总工期**：约 12-18 天（需要并行开发能力）

---

## 7. 关键风险与缓解

### 7.1 OpenSpec Change 稳定性风险

**风险**：change-id 不稳定导致追踪失效

**缓解**：
- 采用确定性生成规则：`<type>-<feature>-<hash>`
- 早期测试 change-id 唯一性和可读性
- 提供 change-id 重命名工具

### 7.2 Skill 路由误伤风险

**风险**：SkillRouter 抢走所有请求，破坏现有流程

**缓解**：
- 设置置信度阈值（建议 0.8）
- 低置信度请求继续走 Plan-Act-Reflect
- 提供 Skill 开关配置

### 7.3 多语言插件化复杂度风险

**风险**：LanguagePlugin 主流程化改动面大，影响稳定性

**缓解**：
- 分阶段迁移（Phase 2 → 4 → 9 → 10 → 11）
- 保留现有语言分支作为 fallback
- 充分测试覆盖

### 7.4 运行产物污染风险

**风险**：`.spec/`、checkpoint、events.jsonl 进入 git

**缓解**：
- 更新 `.gitignore`
- 文档明确说明运行产物清理策略
- 提供清理命令

---

## 8. 成功指标

### M2 完成标准

- ✅ 每次运行生成 `openspec/changes/<id>/` 目录
- ✅ proposal/spec/tasks/design 文件完整
- ✅ spec.md 采用 ADDED/MODIFIED/REMOVED 格式
- ✅ final report 引用 change-id
- ✅ e2e 测试覆盖

### M3 完成标准

- ✅ `archive_change()` 命令可用
- ✅ main spec 包含归档内容
- ✅ ArtifactGraph 记录 introduced_by/archived_at
- ✅ final report 显示 coverage matrix

### Skill 系统完成标准

- ✅ installer_skill 可自动路由
- ✅ code_review_skill 可编排现有工具
- ✅ test_generation_skill 可编排测试工具
- ✅ openspec_skill 可委托 OpenSpecWorkflowExecutor
- ✅ 不破坏现有 Plan-Act-Reflect 流程

### M4 完成标准

- ✅ CLAUDE.md 完整化
- ✅ changes 目录可被 AI 工具读取
- ✅ propose-only / apply-only 模式可用
- ✅ Cursor/Cline 集成文档完整

---

## 9. 面试讲法建议

### 9.1 项目定位

> DevPalAgent 是一个 Spec-first Agentic SDLC Runtime。它把 LLM 代码生成放进确定性的工程流水线，通过需求解析、阶段化调度、工具调用、质量门禁、测试执行、checkpoint 恢复和 final report，解决 AI 代码生成不可控、不可验证、不可追踪的问题。

### 9.2 核心亮点

1. **Agent workflow orchestration**：不是单 prompt，而是 11 阶段状态机
2. **Tool use**：Phase 4 通过 tool loop 写文件
3. **State management**：OpenSpecContext + checkpoint/resume
4. **Reliability**：success policy、skipped 语义、quality gate
5. **Evaluation**：Phase 9/10/11 把生成结果变成可验证报告
6. **Multi-language awareness**：C++/Python/installer 分支已稳定
7. **Traceability**：ArtifactGraph 追踪需求到代码/测试/文档
8. **Roadmap**：OpenSpec changes/archive/traceability 是下一阶段

### 9.3 技术深度展示

**问题**：如何保证 LLM 生成代码的质量？

**回答**：
- Phase 9 四层验证：FORMAT/SEMANTIC/PARSER/BUSINESS
- 按语言选择检查器（C++ CMake/Python pytest/Shell syntax）
- Phase 10 实际执行测试，记录 passed/failed/skipped
- 自愈入口预留，可自动修复常见问题
- final report 输出完整质量报告和 ArtifactGraph

**问题**：如何处理多语言项目？

**回答**：
- Phase 1 识别 language/project_type
- Phase 2 按语言创建目录结构
- Phase 4 使用 PromptTemplateEngine 生成语言感知 prompt
- Phase 9/10 按语言选择验证和测试策略
- installer 项目跳过不适用阶段（Phase 3/5/6/7/10）
- 下一步：LanguagePlugin 主流程化

**问题**：如何追踪需求到代码？

**回答**：
- Phase 1 解析 structured requirements
- ArtifactGraph 记录 requirement → code/test/doc 关系
- Phase 11 生成 final report 和 CLAUDE.md
- 下一步：引入 change-id，追踪"哪个变更引入了哪个需求"
- 下一步：生成 requirement coverage matrix

---

## 10. 总结

DevPalAgent 当前已完成 M1（语言感知闭环稳定版），具备端到端自动生成、质量门禁、测试执行、自愈能力。

**下一阶段重点**：
1. **M2 OpenSpec Change MVP**（2-3 天）- 补齐 changes/proposal/spec/tasks 模型
2. **Skill 系统接入**（5-6 天）- 提升任务级能力编排
3. **M3 Archive + Traceability**（3-4 天）- 完善需求生命周期闭环

**推荐执行路径**：OpenSpec 优先（路径 A）

**总预估工期**：18-25 天（串行）或 12-18 天（并行）

**核心差异化优势**：
- OpenSpec 强在规范协作、变更隔离、归档和 AI-agnostic 上下文
- DevPalAgent 强在端到端自动生成、质量门禁、测试执行、自愈、checkpoint 和 final report
- 后续不建议重写 11 阶段流水线，而应在现有 runtime 外围补齐 OpenSpec change/archive/traceability 层

**面试建议**：
- 强调 Spec-first + Agent workflow + Quality gate + Traceability
- 展示多语言感知、skipped 语义、四层验证等技术深度
- 说明 OpenSpec changes/archive 是下一阶段重点
- 突出与 OpenSpec 的差异化优势（自动生成 + 验证闭环）
