# DevPalAgent Agent Architecture

> 面向 Agent 工程岗位的架构说明：DevPalAgent 如何把 LLM 代码生成封装成可靠、可验证、可恢复的 Agentic SDLC Runtime。

---

## 1. 架构目标

DevPalAgent 的核心目标不是“让 LLM 直接写代码”，而是构建一个确定性的 Agent Workflow：

```text
Spec → Plan/Design → Generate → Validate → Test → Report → Recover
```

系统设计原则：

1. **Spec-first**：所有生成从需求文档开始。
2. **Phase-based orchestration**：复杂开发任务拆成固定阶段。
3. **Tool-loop execution**：LLM 通过工具写文件，而不是只输出文本。
4. **Verification-first**：生成后必须进入质量门禁和测试。
5. **Traceability**：需求、代码、测试、文档可追踪。
6. **Recoverability**：长流程可 checkpoint/resume。
7. **Language awareness**：C++/Python/installer 使用不同目录、测试、报告语义。

---

## 2. 高层架构

```text
┌──────────────────────────────────────────────────────────────┐
│                        User / CLI                             │
│ requirements.md / chat command / smoke script                 │
└───────────────────────────────┬──────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────┐
│                 OpenSpecWorkflowExecutor                      │
│ creates scheduler with options: timeout/retry/checkpoint      │
└───────────────────────────────┬──────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────┐
│                EnhancedOpenSpecScheduler                      │
│ phase loop / skip rules / checkpoint / progress / policy      │
└───────────────────────────────┬──────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────┐
│                     OpenSpecContext                           │
│ requirements, language, project_type, generated files,         │
│ artifact graph, phase results, test counters, LLM usage        │
└───────────────────────────────┬──────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────┐
│                         Phase 1-11                            │
│ parse → structure → design → generate → quality → test → docs │
└───────────────────────────────┬──────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────┐
│ Tools / Templates / PromptEngine / ValidationEngine / Graph   │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. 核心运行时对象

### 3.1 OpenSpecContext

`OpenSpecContext` 是 workflow 的共享状态容器。

关键字段：

| 字段 | 作用 |
|---|---|
| `requirements_file` | 输入需求文件 |
| `requirements_content` | 原始需求文本 |
| `structured_requirements` | 结构化需求对象 |
| `requirements_delta` | added/modified/removed 变更 |
| `language` / `is_cpp` | 当前项目语言 |
| `project_type` / `features` | installer/tooling/auth/database 等特征 |
| `phase_results` | 每个 Phase 的结果 |
| `generated_files` | 生成的文件列表 |
| `artifact_graph` | 需求-代码-测试-文档关系图 |
| `test_passed/test_failed/test_total` | 测试统计 |
| `llm_*` | LLM 调用统计 |

### 3.2 PhaseResult

每个阶段返回 `PhaseResult`：

```python
PhaseResult(
    success=True,
    message="...",
    data={...},
    errors=[],
    warnings=[],
)
```

关键约定：

- skipped phase 仍可 `success=True`，但必须带 `data["skipped"] = True`。
- Phase 10 skipped 必须带：
  - `test_skipped=True`
  - `test_status="skipped"`
  - `test_summary="skipped (...)"`
- skipped 不等于 passed，不显示 `0/0 passed`。

---

## 4. 11 阶段 Agent Workflow

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

### 4.1 Phase 1：需求解析

职责：

- 读取 requirements markdown。
- 提取 requirement id/title/description/acceptance criteria。
- 提取 scenarios、priority、status。
- 检测 features/project_type。
- 根据 installer/tooling 设置 `language="python"`、`is_cpp=False`。
- 写 `.spec/delta.json`。

### 4.2 Phase 2：语言感知目录结构

职责：

- C++ 创建 C++ 项目结构。
- Python 创建 Python 项目结构。
- installer/tooling 创建精简结构，避免 `include` 和 CMake 假设。

### 4.3 Phase 3：技术设计

职责：

- 对普通项目生成技术设计。
- 对 installer/tooling 可跳过。

### 4.4 Phase 4：代码生成

职责：

- 先应用基础模板。
- 通过 PromptEngine 生成语言感知 system prompt。
- 通过 LLM tool loop 调用 `write_file` 写业务代码。
- 更新 ArtifactGraph 和 CompileDB。

### 4.5 Phase 9：质量门禁

职责：

- 四层验证：FORMAT / SEMANTIC / PARSER / BUSINESS。
- 按语言选择检查器。
- Python/installer 不再跑 C++ 检查。
- 代码审查和自愈入口。

### 4.6 Phase 10：测试执行

职责：

- C++：编译并运行测试。
- Python：运行 pytest，并写 canonical test counts。
- installer/tooling：按 skip rules 跳过。

### 4.7 Phase 11：最终报告

输出：

- `docs/final_report.md`
- `.spec/artifact_graph.json`
- `CLAUDE.md`

职责：

- 汇总 phase 状态。
- 汇总测试状态。
- 输出 ArtifactGraph。
- 输出语言感知 CLAUDE.md。

---

## 5. Agent Reliability 设计

### 5.1 Checkpoint / Resume

长流程可能因为 LLM、测试或环境失败中断，因此 enhanced scheduler 支持 checkpoint。

关键修复：

- checkpoint 路径不再基于初始 `is_cpp=True` 预加 `cpp_`。
- installer 项目不会再生成 `cpp_test_phase_skip`。
- `resume=False` 可强制从 Phase 1 重新执行。

### 5.2 Skip Semantics

Agent workflow 中 skipped 是重要状态，不能混同为 passed。

示例：installer 项目跳过 Phase 10。

正确报告：

```text
tests: skipped (安装脚本项目不需要编译和运行测试)
```

错误报告：

```text
tests: 0/0 passed
```

### 5.3 Success Policy

`validate_phase_success()` 用于防止弱成功：

- Phase 4 成功但没有 AI 代码且未显式 skipped → fail。
- Phase 10 成功但 `test_total <= 0` 且未 skipped → fail。
- Phase 10 有失败测试 → fail。

### 5.4 Quality Gate

Phase 9 让 Agent 生成结果进入确定性检查：

```text
FORMAT   → 文件结构/入口点
SEMANTIC → API/测试框架契约
PARSER   → 解析兼容性
BUSINESS → 业务规则/测试存在性
```

---

## 6. Traceability

当前追踪能力：

```text
Requirement → Generated code
Requirement → Test files
Generated files → final report
Phase result → report summary
```

关键产物：

- `.spec/requirements.json`
- `.spec/delta.json`
- `.spec/artifact_graph.json`
- `docs/final_report.md`

后续计划：

- change-id
- introduced_by / modified_by
- archive metadata
- scenario coverage matrix

---

## 7. 多语言设计

当前已具备：

- `language_config.py`：语言特征数据库。
- Python/Shell plugin 雏形。
- PromptEngine 按语言生成 prompt。
- Phase 2/9/10/11 语言感知。

仍需改进：

- LanguagePlugin 尚未完全接入所有 Phase。
- Phase 2/4/9/10/11 仍存在各自 helper，后续应统一到 plugin interface。

目标接口：

```python
class LanguagePlugin:
    def project_structure(self) -> dict: ...
    def source_patterns(self) -> list[str]: ...
    def test_patterns(self) -> list[str]: ...
    def build_command(self) -> list[str]: ...
    def test_command(self) -> list[str]: ...
    def quality_checks(self) -> list: ...
    def prompt_features(self) -> LanguageFeatures: ...
```

---

## 8. 当前架构边界

DevPalAgent 当前不是 OpenSpec 的完整复刻。它更偏向：

```text
OpenSpec-inspired spec workflow + automated code generation + validation/self-heal runtime
```

仍未完成：

- `openspec/changes/<change-id>/proposal.md`
- `openspec/changes/<change-id>/specs/spec.md`
- `tasks.md`
- archive merge
- AI-agnostic propose/apply 模式

这些是 M2/M3/M4 的重点。
