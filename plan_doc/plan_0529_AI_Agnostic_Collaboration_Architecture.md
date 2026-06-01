# AI-agnostic Spec-first 协作模式架构设计

**日期**：2026-05-29  
**目标**：让 DevPalAgent 不只服务自身 CLI，也能服务 Claude Code、Cursor、Cline 等外部 AI coding 工具，形成 AI-agnostic 的 Spec-first 协作模式  
**预期工期**：5-7 天 MVP  
**优先级**：P1  
**关联路线图**：`plan_doc/plan_0528_priority_roadmap.md`

---

## 1. 背景与目标

### 1.1 当前状态

**已完成能力**：
- ✅ OpenSpec 11 阶段主流程
- ✅ proposal/spec/tasks/design artifacts 生成
- ✅ ToolRegistry + Skills 编排
- ✅ Phase 4 代码生成和 Phase 9/10/11 验证闭环
- ✅ CLAUDE.md 生成能力
- ✅ 多 LLM Provider 支持
- ✅ EventBus 和 final_report 可观测

### 1.2 当前缺口

**缺口 1：DevPalAgent 仍偏自闭环执行**
- 当前 `run_ai_flow.py` 默认从 requirements 直接跑完整 11 阶段。
- 外部 AI coding 工具难以只接收 spec artifacts 后独立实现。
- 人审或 Cursor/Cline/Claude Code 接手前缺少清晰边界。

**缺口 2：缺少 propose-only / apply-only 模式**
- propose-only：只生成 proposal/spec/tasks/design，不改代码。
- apply-only：读取已有 change artifacts，执行实现、验证、报告。
- 当前没有稳定 CLI 参数和调度策略表达这两种模式。

**缺口 3：外部工具规则模板不完整**
- CLAUDE.md 已能生成项目说明，但没有专门面向外部 AI 的 spec-first 协作规则。
- 缺少 `.cursorrules` / Cline rules 模板。
- 缺少外部工具如何读取 changes、如何保持 traceability 的指导。

### 1.3 设计目标

**目标 1：Propose-only 模式**
- `python run_ai_flow.py -r requirements/simple_login.md --propose-only`
- 只运行需求解析、OpenSpec Change、技术设计相关阶段。
- 不生成业务代码，不运行测试，不修改 src/tests。

**目标 2：Apply-only 模式**
- `python run_ai_flow.py --apply-change <change-id>`
- 读取已有 `openspec/changes/<change-id>/`。
- 基于 change artifacts 执行代码生成、质量门禁、测试和报告。

**目标 3：AI-agnostic Rule Pack**
- 生成 CLAUDE.md / `.cursorrules` / `cline-rules.md`。
- 告诉外部 AI：读取哪个 change、修改哪些文件、如何写 traceability、何时调用 validate/archive。

**目标 4：外部协作命令语义**
- `/opsx:propose`
- `/opsx:apply`
- `/opsx:validate`
- `/opsx:archive`

这些命令可以先作为文档化协议，后续再接入 Claude Code skills 或 shell CLI。

---

## 2. 协作模式设计

### 2.1 三种运行模式

```text
Mode A: full-run
requirements → propose → design → generate → validate → report

Mode B: propose-only
requirements → proposal/spec/tasks/design → stop

Mode C: apply-only
existing change → generate/apply → validate → report
```

### 2.2 Propose-only 流程

```text
requirements/*.md
  ↓
Phase 1 Parse Requirements
  ↓
OpenSpec Change Builder
  ├─ proposal.md
  ├─ specs/spec.md
  ├─ tasks.md
  ├─ design.md
  └─ metadata.json(status=PROPOSED)
  ↓
Rule Pack Generation
  ├─ CLAUDE.md section
  ├─ .cursorrules
  └─ cline-rules.md
  ↓
Stop before Phase 4 code generation
```

适用场景：
- 面试展示 spec-first 设计能力。
- 人类先审 proposal/design。
- 外部 AI 工具接手实现。

### 2.3 Apply-only 流程

```text
openspec/changes/<change-id>/
  ↓
Load proposal/spec/tasks/design
  ↓
Phase 4 Generate or verify implementation
  ↓
Phase 5 Test docs
  ↓
Phase 9 Quality Gate
  ↓
Phase 9.5 Critique
  ↓
Phase 10 Compile/Test/Self-Healing
  ↓
Phase 11 Final Report
```

适用场景：
- Cursor/Cline/Claude Code 已经改过代码，DevPalAgent 只做验收。
- DevPalAgent 根据已有 change artifacts 继续实现。
- CI 中对指定 change 执行验证。

---

## 3. 模块结构

```text
devpal/collaboration/
├── __init__.py
├── modes.py              # RunMode / mode policy
├── change_loader.py      # load existing change artifacts
├── rule_pack.py          # generate CLAUDE.md/.cursorrules/Cline rules
├── external_commands.py  # opsx command contract
└── templates/
    ├── claude_code.md
    ├── cursorrules.txt
    └── cline_rules.md
```

### 3.1 RunMode

```python
class RunMode(str, Enum):
    FULL = "full"
    PROPOSE_ONLY = "propose_only"
    APPLY_ONLY = "apply_only"
    VALIDATE_ONLY = "validate_only"
```

### 3.2 ModePolicy

```python
@dataclass
class ModePolicy:
    start_phase: int
    stop_after_phase: int | None
    require_existing_change: bool
    allow_code_writes: bool
    allow_archive: bool
```

示例：
```python
PROPOSE_ONLY = ModePolicy(
    start_phase=1,
    stop_after_phase=3,
    require_existing_change=False,
    allow_code_writes=False,
    allow_archive=False,
)
```

---

## 4. Rule Pack 设计

### 4.1 CLAUDE.md 增强

新增章节：
```markdown
## Spec-first Collaboration Rules

1. Always read `openspec/changes/<change-id>/proposal.md` first.
2. Implement only tasks listed in `tasks.md`.
3. Preserve requirement IDs in comments, tests, or artifact metadata when available.
4. Do not archive manually; run `python -m devpal.openspec archive <change-id>` after validation.
5. Run `python run_ai_flow.py --apply-change <change-id>` for verification.
```

### 4.2 `.cursorrules`

```text
You are working in a DevPalAgent Spec-first project.
Read openspec/changes/<change-id>/ before editing code.
Keep changes aligned with tasks.md.
Do not introduce unrelated refactors.
After implementation, run DevPalAgent apply/validate flow.
```

### 4.3 Cline rules

```markdown
# Cline Spec-first Rules

- Treat OpenSpec change artifacts as the source of truth.
- Make minimal code changes required by tasks.md.
- Preserve traceability between requirements, source files, and tests.
- Ask before modifying files outside the change scope.
```

---

## 5. CLI 与命令设计

### 5.1 run_ai_flow 参数

```bash
python run_ai_flow.py -r requirements/simple_login.md --propose-only
python run_ai_flow.py --apply-change add-login-service
python run_ai_flow.py --validate-change add-login-service
```

### 5.2 opsx 命令语义

这些命令先作为跨工具协议，后续可映射到 Claude Code skill、Cursor command 或 shell script。

```text
/opsx:propose <requirements-file>
  生成 OpenSpec Change，不改代码

/opsx:apply <change-id>
  基于 change artifacts 实现或继续实现

/opsx:validate <change-id>
  验证代码、测试、traceability 和 final_report

/opsx:archive <change-id>
  归档 change，合并 spec delta
```

---

## 6. 与 OpenSpec 11 阶段集成

### 6.1 propose-only phase policy

建议执行：
- Phase 1：Parse requirements
- Phase 2：Create project structure / OpenSpec directories
- Phase 3：Generate technical design
- OpenSpec Change artifact generation
- Rule Pack generation

建议跳过：
- Phase 4：代码生成
- Phase 5：测试文档
- Phase 9/9.5/10：验证和测试
- Phase 11：可生成 propose summary，但不作为完整 final_report

### 6.2 apply-only phase policy

建议执行：
- Load existing change artifacts
- Phase 4：代码生成或增量实现
- Phase 5：测试文档
- Phase 9：Quality Gate
- Phase 9.5：Critique
- Phase 10：Compile/Test/Self-Healing
- Phase 11：Final Report

建议跳过：
- Phase 1 requirements parsing，可从 change metadata 恢复。
- Phase 3 design generation，除非 change 缺少 design.md。

---

## 7. 分阶段实施路线

### Day 1：RunMode 与 scheduler policy

验收：
- `OpenSpecRunOptions` 增加 `run_mode` / `apply_change_id`。
- scheduler 能根据 mode 决定 start/stop/skip phases。
- propose-only 不写 src/tests。

### Day 2：Propose-only MVP

验收：
- `--propose-only` 生成 proposal/spec/tasks/design/metadata。
- metadata 状态为 PROPOSED。
- 终端输出 next steps：让 Claude Code/Cursor/Cline 读取 change。

### Day 3：Apply-only MVP

验收：
- `--apply-change <change-id>` 能加载已有 change artifacts。
- context 恢复 requirements/design/spec 信息。
- Phase 4-11 可完成。

### Day 4：Rule Pack Generator

验收：
- 生成或更新 CLAUDE.md spec-first section。
- 生成 `.cursorrules`。
- 生成 `cline-rules.md`。
- 不覆盖用户已有规则，使用 marker block 增量更新。

### Day 5：Validate-only 与外部命令协议

验收：
- `--validate-change <change-id>` 不生成代码，只跑质量门禁、编译测试和报告。
- 输出 `/opsx:*` 命令说明文档。

### Day 6-7：测试与演示

验收：
- propose-only / apply-only / validate-only 单测和 e2e golden case。
- Claude Code / Cursor / Cline 协作文档可用于面试演示。

---

## 8. 验收标准

```bash
python run_ai_flow.py -r requirements/simple_login.md --propose-only
python run_ai_flow.py --apply-change add-simple-login
python run_ai_flow.py --validate-change add-simple-login
```

验证点：
1. propose-only 只生成 change artifacts，不生成业务代码。
2. apply-only 能基于 change artifacts 完成代码、测试和报告。
3. validate-only 不改代码，只验证已有实现。
4. CLAUDE.md / `.cursorrules` / Cline rules 明确说明外部 AI 协作流程。
5. final_report 记录 run mode、change_id 和外部协作建议。

---

## 9. 风险与缓解

1. **外部 AI 修改范围失控**：Rule Pack 强制读取 tasks.md，只允许 change scope 内修改。
2. **propose-only 与 full-run 逻辑分叉过大**：用 ModePolicy 控制 phase skip，不复制一套 workflow。
3. **apply-only context 不完整**：ChangeLoader 必须从 metadata/proposal/spec/design 恢复 context。
4. **覆盖用户已有规则文件**：Rule Pack 使用 marker block 增量更新，不全量覆盖。
5. **工具命令碎片化**：`/opsx:*` 先作为协议，底层统一映射到 run_ai_flow/devpal.openspec CLI。

---

## 10. 面试讲法

DevPalAgent 的定位不是替代所有 AI coding 工具，而是提供 spec-first 的工程中枢。它可以 propose-only 生成可审查的 OpenSpec Change，让 Claude Code、Cursor 或 Cline 接手实现；也可以 apply-only 读取已有 change artifacts，对外部 AI 写出的代码执行质量门禁、测试、自愈和报告。这样项目从“单工具闭环”升级为 AI-agnostic 协作流，核心价值是让任何 AI 写代码都必须围绕同一套 spec、tasks 和 traceability 进行。
