# OpenSpec 与开源差距分析及后续规划

> **⚠️ 本文档已过期**  
> **最新版本**：[gap_analysis_vs_openspec_2026-05-24.md](gap_analysis_vs_openspec_2026-05-24.md)  
> **更新日期**：2026-05-24

**日期**：2026-05-16  
**参考**：`docs/README_2026-05-15_openspec_architecture_plan.md`  
**对标**：[OpenSpec (Fission-AI)](https://github.com/Fission-AI/OpenSpec) — YC 支持，27k+ GitHub Stars

---

## 一、开源 OpenSpec 是什么

OpenSpec 是一个 **Spec-Driven Development (SDD)** 框架，核心理念是：**先写规范，再写代码**。它不是代码生成工具，而是一个让 AI 编码助手（Cursor、Claude Code、Cline、Copilot）在写代码前先对齐需求的**协作框架**。

### 核心工作流（10 阶段）

```
Initialize → Create Change → Explore → Propose → Spec → Design → Tasks → Apply → Verify → Archive
```

### 文件结构

每个功能变更都有独立目录：

```
openspec/
└── changes/
    └── add-dark-mode/
        ├── proposal.md     # Why（为什么做）+ What（做什么）+ Impact（影响范围）
        ├── specs/
        │   └── spec.md     # Delta 规范：## ADDED / ## MODIFIED / ## REMOVED
        │                   # 每条需求下有 Given/When/Then 验收场景
      ├── design.md       # 技术设计（架构决策、接口定义）
        └── tasks.md        # 实现清单（编号任务列表）
```

### CLI 命令

| 命令 | 作用 |
|------|------|
| `openspec init` | 初始化项目 |
| `openspec propose <name>` | 创建变更目录，生成 proposal.md |
| `openspec explore` | 探索阶段，思考方案 |
| `openspec apply` | 让 AI 按 tasks.md 实现代码 |
| `openspec archive` | 归档完成的变更，合并 delta 到主规范 |
| `openspec list` | 列出所有变更 |
| `/opsx:propose` | AI 助手内联命令 |

### Spec Delta 机制

每个 `spec.md` 描述的是**相对于现有规范的变更**，而非全量规范：

```markdown
## ADDED Requirements
- REQ-NEW-001: 用户可以切换深色模式
  - Given: 用户在设置页面
  - When: 点击主题切换按钮
  - Then: 界面切换为深色主题并持久化

## MODIFIED Requirements
- REQ-001: 登录页面（原：白色背景 → 改：支持主题色）

## REMOVED Requirements
- REQ-OLD-005: 强制浅色模式（已废弃）
```

### 关键设计原则

1. **依赖图强制顺序**：proposal → specs → design → tasks，不能跳过
2. **Repo-native**：所有规范文件存在代码仓库中，随代码一起版本控制
3. **AI-agnostic**：不依赖特定 AI 工具，任何 AI 助手都能读取 Markdown
4. **变更隔离**：每个功能变更独立目录，互不干扰
5. **Archive 归档**：完成后 delta 合并到主规范，形成活文档

---

## 二、DevPalAgent 当前状态（截至 2026-05-16）

### 已完成的核心功能

| 功能 | 状态 | 说明 |
|------|------|------|
| 11 阶段流水线 | ✅ | Phase 1-11 全部实现 |
| ArtifactGraph 集成 | ✅ | Phase 4/10/11 使用 |
| DeltaSpec 增量检测 | ✅ 部分 | Phase 1 检测变更，Phase 4 选择性重生成 |
| Phase 9 质量门禁 | ✅ | is_critical=True，5 项强制检查 |
| 选择性测试执行 | ✅ | Phase 10 基于 ArtifactGraph |
| --verbose/--debug | ✅ | 接入 Logger |
| --dry-run | ✅ | 预览执行计划 |
| --health-check | ✅ | 系统配置检查 |
| 42 个单元测试 | ✅ | 100% 通过 |

### Schema 模块实现状态

| 模块 | 代码量 | 集成状态 | 说明 |
|------|--------|----------|------|
| `artifact_graph.py` | 1087 LOC | ✅ Phase 4/10/11 | 唯一真正接入的模块 |
| `delta_spec.py` | 614 LOC | ❌ 零使用 | 文件级 diff，未接入主流程 |
| `validation_engine.py` | 719 LOC | ❌ 零使用 | 四层验证，未接入主流程 |
| `event_bus.py` | 696 LOC | ❌ 零使用 | 发布订阅，未接入主流程 |
| `rollout_engine.py` | 503 LOC | ❌ 零使用 | 渐进发布，未接入主流程 |

---

## 三、与开源 OpenSpec 的差距分析

### 差距 1：定位不同（最根本差距）

| 维度 | 开源 OpenSpec | DevPalAgent |
|----|--------------|-------------|
| **定位** | 规范协作框架（人 + AI 对齐） | 自动化代码生成流水线 |
| **用户角色** | 开发者主导，AI 辅助 | AI 主导，开发者审查 |
| **输入** | 人工编写的 proposal/spec | Markdown 需求文档 |
| **输出** | 规范文件 + AI 实现代码 | 完整 C++ 项目（代码+测试+文档） |
| **语言** | 语言无关 | 当前仅 C++ |
| **AI 依赖** | 可选（规范是 Markdown） | 强依赖（Phase 3/4 必须调用 LLM） |

**结论**：两者不是同类工具。开源 OpenSpec 是"规范管理框架"，DevPalAgent 是"需求驱动的全自动代码生成系统"。DevPalAgent 的定位更激进，但也更脆弱。

---

### 差距 2：Spec Delta 机制

**开源 OpenSpec**：
- 每个变更有独立 `spec.md`，明确标注 ADDED/MODIFIED/REMOVED
- Delta 是**需求级别**的变更描述，包含 Given/When/Then 验收场景
- Archive 后 delta 合并到主规范，形成活文档
- 完整的变更历史可追溯

**DevPalAgent 当前**：
- Phase 1 比较 `requirements.json` 检测 added/modified/removed 需求 ID
- 没有 Given/When/Then 验收场景格式
- 没有 delta 归档机制
- `delta_spec.py` 实现的是文件级 diff，不是需求级 delta

**差距**：需求变更的语义表达能力弱，缺少验收场景，缺少归档机制。

---

### 差距 3：需求对象化深度

**开源 OpenSpec**：
```markdown
## ADDED Requirements
- REQ-001: 用户登录
  - Given: 用户在登录页
  - When: 输入正确的用户名和密码
  - Then: 跳转到首页，显示欢迎信息
  - Priority: P0
  - Status: PROPOSED
```

**DevPalAgent 当前**：
```json
{
  "id": "REQ-001",
  "title": "用户登录",
  "description": "...",
  "acceptance_criteria": ["criterion1"]
}
```

**缺失字段**：`priority`、`status`、`linked_design`、`linked_code`、`linked_tests`、`tags`、`Given/When/Then` 场景格式

---

### 差距 4：Traceability（可追溯性）

**开源 OpenSpec**：
- 每个 spec delta 明确关联到变更目录
- Archive 后形成完整的需求演进历史
- 可以回答"这个需求是在哪个变更中引入的"

**DevPalAgent 当前**：
- ArtifactGraph 可以回答"REQ-001 由哪些文件实现"✅
- ArtifactGraph 可以回答"REQ-001 被哪些测试覆盖"✅
- **不能**回答"REQ-001 是在哪次变更中引入的"❌
- **不能**回答"REQ-001 的验收场景是什么"❌
- **不能**回答"哪些需求没有 Given/When/Then 场景"❌

---

### 差距 5：变更隔离与归档

**开源 OpenSpec**：
- 每个功能变更独立目录，互不干扰
- `openspec archive` 将 delta 合并到主规范
- 完成的变更有明确的生命周期（PROPOSED → IN_PROGRESS → ARCHIVED）

**DevPalAgent 当前**：
- 没有变更目录概念
- 没有归档机制
- Checkpoint 只保存执行状态，不保存需求演进历史

---

### 差距 6：AI 工具集成方式

**开源 OpenSpec**：
- 通过 CLAUDE.md / .cursorrules 注入规范上下文
- AI 助手读取 `openspec/changes/` 目录中的规范文件
- `/opsx:propose`、`/opsx:apply` 等内联命令
- 不需要 API key，AI 工具自己调用

**DevPalAgent 当前**：
- 直接调用 Anthropic API（强依赖）
- 没有 CLAUDE.md 集成
- 没有内联命令支持
- 不能与 Cursor/Cline 等工具协作

---

### 差距 7：质量验证

**开源 OpenSpec**：
- `openspec verify` 命令（验证实现是否符合规范）
- 验收场景（Given/When/Then）作为测试依据
- 人工 Review 是流程的一部分

**DevPalAgent 当前**：
- Phase 9 质量门禁（文件存在性检查）✅
- Phase 10 编译+测试执行 ✅
- **缺少**：验收场景驱动的测试生成
- **缺少**：`validation_engine.py` 的四层验证（已实现但未接入）

---

### 差距 8：多语言支持

**开源 OpenSpec**：语言无关（规范是 Markdown，代码由 AI 生成）

**DevPalAgent 当前**：仅支持 C++（`is_cpp` 标志，CMake 配置，test_base.h 等都是 C++ 专用）

---

## 四、综合差距评分

| 维度 | 开源 OpenSpec | DevPalAgent | 差距 |
|------|:---:|:---:|:---:|
| 规范管理（Spec Management） | ⭐⭐⭐⭐⭐ | ⭐⭐ | 大 |
| 需求对象化深度 | ⭐⭐⭐⭐ | ⭐⭐ | 大 |
| Spec Delta 机制 | ⭐⭐⭐⭐⭐ | ⭐⭐ | 大 |
| 变更隔离与归档 | ⭐⭐⭐⭐⭐ | ⭐ | 很大 |
| Traceability | ⭐⭐⭐ | ⭐⭐⭐ | 中 |
| 质量门禁 | ⭐⭐⭐ | ⭐⭐⭐ | 中 |
| 自动化代码生成 | ⭐⭐ | ⭐⭐⭐⭐⭐ | DevPalAgent 领先 |
| 编译+测试闭环 | ⭐ | ⭐⭐⭐⭐⭐ | DevPalAgent 领先 |
| AI 自愈能力 | ⭐ | ⭐⭐⭐⭐ | DevPalAgent 领先 |
| 多语言支持 | ⭐⭐⭐⭐⭐ | ⭐ | 很大 |
| AI 工具集成 | ⭐⭐⭐⭐⭐ | ⭐⭐ | 大 |

---

## 五、后续规划（基于差距分析）

### 阶段一：补齐 Spec Delta 机制（P1，2-3天）

**目标**：让需求变更有完整的语义表达，对标开源 OpenSpec 的 delta spec 格式。

**任务**：

1. **Phase 1 输出 Given/When/Then 验收场景**
   - 修改 `phase1_parse_requirements.py` 的 `_parse_structured_requirements()`
   - 从需求文档中提取 Given/When/Then 格式的验收场景
   - 输出到 `requirements.json` 的 `scenarios` 字段
   - 关键文件：`devpal/core/openspec_phases/phase1_parse_requirements.py`

2. **需求对象增加 priority 和 status 字段**
   - Phase 1 解析时提取优先级标记（P0/P1/P2 或 高/中/低）
   - 初始 status 设为 `PROPOSED`，Phase 10 通过后更新为 `VERIFIED`
   - 关键文件：`devpal/core/openspec_phases/phase1_parse_requirements.py`、`devpal/core/openspec_phases/base.py`

3. **生成 `.spec/delta.json`**
   - Phase 1 完成后将 delta（added/modified/removed）写入 `.spec/delta.json`
   - 格式对标开源 OpenSpec 的 spec delta
   - 关键文件：`devpal/core/openspec_phases/phase1_parse_requirements.py`

**验收标准**：
```bash
# requirements.json 包含 scenarios 字段
cat cpp_simple_login/.spec/requirements.json | python -c "import json,sys; r=json.load(sys.stdin); print(r[0].get('scenarios'))"
# .spec/delta.json 存在且格式正确
cat cpp_simple_login/.spec/delta.json
```

---

### 阶段二：接入 ValidationEngine（P2，1-2天）

**目标**：把已有的 `validation_engine.py`（719 LOC，四层验证）真正接入 Phase 9。

**任务**：

1. **Phase 9 使用 ValidationEngine 做四层验证**
   - SYNTAX：文件存在性、编码正确性（当前已有）
   - SEMANTIC：API 契约一致性（test_base.h 宏、函数签名）
   - STRUCTURAL：类三元组完整性（include/src/test）
   - BUSINESS：需求覆盖率（每个 REQ 都有对应测试）
   - 关键文件：`devpal/core/openspec_phases/phase9_quality_gate.py`、`devpal/core/schema/validation_engine.py`

2. **验证结果写入 ArtifactGraph**
   - 每个验证结果作为节点元数据存入图
   - 关键文件：`devpal/core/openspec_phases/phase9_quality_gate.py`

**验收标准**：
```bash
python -m pytest tests/openspec/test_phase9_quality_gate.py -v
# Phase 9 报告包含四层验证结果
```

---

### 阶段三：接入 EventBus（P3，1天）

**目标**：把已有的 `event_bus.py`（696 LOC）接入主流程，实现 Phase 间事件通信。

**任务**：

1. **Phase 4 生成代码后发布 `FileChangedEvent`**
2. **Phase 10 测试完成后发布 `ValidationCompletedEvent`**
3. **Phase 1 需求变更时发布 `RequirementChangedEvent`**
4. **事件日志写入 `.spec/events.json`**

**关键文件**：
- `devpal/core/schema/event_bus.py`
- `devpal/core/openspec_phases/phase4_generate_code.py`
- `devpal/core/openspec_phases/phase10_run_tests.py`
- `devpal/core/openspec_phases/base.py`（context 增加 event_bus 字段）

---

### 阶段四：自愈模型切换（P1，30分钟）

**目标**：修复 `test_self_healer.py` 中 `use_fallback` 参数有声明但实际未切换模型的 Bug。

**问题**：
```python
# 当前：use_fallback 参数存在但未使用
def heal_compile_error(self, test_file, error_output, use_fallback=False):
    # ... 无论 use_fallback 是否为 True，都用同一个 llm_client
    response = self.llm_client.generate(...)  # 没有切换模型
```

**修复方案**：
```python
def heal_compile_error(self, test_file, error_output, use_fallback=False):
    if use_fallback:
        from ..llm_client import get_llm_client
        client = get_llm_client(model=self.fallback_model)  # claude-opus-4-7
    else:
        client = self.llm_client
    response = client.generate(...)
```

**关键文件**：`devpal/core/openspec_phases/test_self_healer.py`

---

### 阶段五：多语言支持框架（P3，1周）

**目标**：从 C++ 专用扩展到支持 Python，对标开源 OpenSpec 的语言无关性。

**任务**：
1. 抽象 `LanguagePlugin` 接口（编译命令、测试框架、文件结构）
2. 实现 `CppPlugin`（现有逻辑迁移）
3. 实现 `PythonPlugin`（pytest、setup.py/pyproject.toml）
4. Phase 2 根据需求文档自动检测语言

**关键文件**：
- 新增 `devpal/core/language_plugins/base.py`
- 新增 `devpal/core/language_plugins/cpp_plugin.py`
- 新增 `devpal/core/language_plugins/python_plugin.py`
- `devpal/core/openspec_phases/phase2_create_structure.py`

---

### 阶段六：CLAUDE.md 集成（P2，1天）

**目标**：生成 `CLAUDE.md` 文件，让 Claude Code 等 AI 工具能直接读取项目规范。

**任务**：
1. Phase 11 生成 `CLAUDE.md`，包含：
   - 项目概述
   - 需求列表（带 ID 和验收场景）
   - 技术设计摘要
   - 文件结构说明
   - 编码规范
2. 格式对标开源 OpenSpec 的 CLAUDE.md 约定

**关键文件**：`devpal/core/openspec_phases/phase11_final_report.py`

---

## 六、优先级总览

| 优先级 | 任务 | 预计时间 | 价值 |
|--------|------|----------|------|
| **P0** | 修复自愈模型切换 Bug | 30分钟 | 提升自愈成功率 |
| **P1** | Phase 1 输出 Given/When/Then 场景 | 2小时 | 对标开源核心能力 |
| **P1** | 需求增加 priority/status 字段 | 1小时 | 需求对象化 |
| **P1** | 生成 `.spec/delta.json` | 1小时 | 变更追踪 |
| **P2** | ValidationEngine 接入 Phase 9 | 1天 | 四层验证 |
| **P2** | 生成 CLAUDE.md | 1天 | AI 工具集成 |
| **P3** | EventBus 接入主流程 | 1天 | 事件驱动架构 |
| **P3** | 多语言支持框架 | 1周 | 扩展性 |

---

## 七、DevPalAgent 的差异化优势（不应放弃）

开源 OpenSpec 是"规范框架"，DevPalAgent 是"全自动生成系统"。以下是 DevPalAgent 独有的能力，应继续强化：

1. **端到端自动化**：从需求文档到可编译运行的项目，全程无需人工干预
2. **AI 自愈闭环**：编译失败自动修复，开源 OpenSpec 没有这个能力
3. **编译+测试验证**：Phase 10 的编译测试闭环是核心竞争力
4. **ArtifactGraph 追踪**：需求→代码→测试的完整依赖图
5. **Checkpoint 恢复**：长流程可以从中断点恢复

**建议**：不要试图完全复制开源 OpenSpec 的定位，而是在 DevPalAgent 的自动化优势基础上，补齐规范管理能力（Given/When/Then、delta 归档、CLAUDE.md 集成），形成差异化的"全自动 Spec-First 开发系统"。

---

## 参考资料

- [OpenSpec GitHub (Fission-AI)](https://github.com/Fission-AI/OpenSpec) — 27k+ Stars
- [OpenSpec YC Launch](https://www.ycombinator.com/launches/Pdc-openspec-the-spec-framework-for-coding-agents)
- [OpenSpec Workflow](https://thedocs.io/openspec/concepts/workflow/)
- [Delta Specs Explained](https://www.mintlify.com/Gentleman-Programming/agent-teams-lite/guides/delta-specs)
- [OpenSpec vs Spec Kit](https://www.bighatgroup.com/blog/openspec-vs-speckit-spec-driven-ai-development/)
- [架构规格文档](docs/README_2026-05-15_openspec_architecture_plan.md)
