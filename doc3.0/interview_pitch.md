# DevPalAgent Interview Pitch

> 面向 Agent Engineer / AI Coding / Developer Tools 岗位的项目讲解稿。

---

## 1. 30 秒版本

DevPalAgent 是一个 Spec-first Agentic SDLC Runtime。它不是简单的代码生成器，而是把需求文档通过 11 阶段 Agent workflow 转成可验证的软件项目。系统包含需求解析、技术设计、代码生成、质量门禁、测试执行、ArtifactGraph 追踪、checkpoint 恢复和自愈机制。最近我把它从 C++ 专用流程扩展到 Python/installer 场景，并修复了 skipped phase、checkpoint、质量报告和语言上下文错配问题。

---

## 2. 2 分钟版本

LLM 写代码最大的问题不是“能不能生成”，而是生成结果不可控、不可验证、不可追踪。DevPalAgent 的思路是把 LLM 放进一个确定性的工程流水线里。

用户输入一个需求文档，系统会先解析成结构化 requirements，然后通过 11 个阶段执行：创建项目结构、生成技术设计、生成代码、质量门禁、测试执行、最终报告。每个阶段都有明确输入输出，结果写入 OpenSpecContext，并通过 PhaseResult 记录成功、失败或 skipped。

在 Phase 4，LLM 不直接输出一大段代码，而是通过 tool loop 调用 write_file 工具写文件。Phase 9 会运行四层 ValidationEngine，Phase 10 会运行 C++ 或 Python 测试，Phase 11 会生成 final_report、ArtifactGraph 和 CLAUDE.md。

这个项目里我重点解决了几个真实 Agent 工程问题：

1. checkpoint 恢复导致跳过逻辑失效。
2. skipped phase 被误显示为 `0/0 passed`。
3. Python/installer 项目被误跑 C++ 质量检查。
4. checkpoint 早期语言判断导致生成 `cpp_test_phase_skip`。
5. CLAUDE.md 中多语言上下文不一致。

最后我把流程稳定成语言感知闭环：C++、Python、installer 有不同目录结构、质量检查、测试语义和报告输出，并用 e2e 测试覆盖。

---

## 3. 项目一句话定位

```text
DevPalAgent = Spec-first workflow + Agent tool loop + Quality gate + Test/self-heal + Traceable reports
```

或者：

> 一个面向 AI Coding 的 Agentic SDLC Runtime，用确定性工程流水线约束 LLM 代码生成。

---

## 4. 面试官最可能问的问题

### Q1：这个项目和普通 ChatGPT 代码生成有什么区别？

普通 ChatGPT 是一次性生成文本。DevPalAgent 是完整 workflow：

- 有阶段状态。
- 有上下文对象。
- 有工具调用。
- 有 checkpoint。
- 有质量门禁。
- 有测试执行。
- 有 final report。
- 有 ArtifactGraph。

LLM 只是 Phase 3/4 的一部分，不是整个系统。

### Q2：Agent 在哪里？

Agent 体现在：

1. 输入需求后自动规划执行 11 阶段。
2. Phase 4 使用 tool loop 写文件。
3. Phase 9/10 根据结果决定通过、失败、跳过或自愈。
4. Scheduler 维护状态、恢复和重试。
5. Final report 将执行链变成可审查结果。

### Q3：如何保证生成结果可靠？

四层策略：

1. **结构约束**：Phase 固定输入输出。
2. **工具约束**：LLM 必须通过 write_file 写文件。
3. **质量验证**：Phase 9 ValidationEngine。
4. **测试闭环**：Phase 10 编译/pytest。
5. **报告审计**：Phase 11 final_report + CLAUDE.md。

### Q4：遇到过什么真实 bug？

可以讲 4 个：

#### Bug 1：checkpoint 导致 skip 不生效

之前测试从 Phase 3 resume，Phase 1 没执行，所以 `context.features/project_type` 为空，installer skip rule 不生效。

修复：

- `resume=False` 重新从 Phase 1 开始。
- enhanced scheduler 作为默认入口。
- checkpoint path 修正。

#### Bug 2：skipped 测试显示 0/0 passed

installer 项目跳过 Phase 10，但 final report 直接读 `test_passed/test_total`，显示 `0/0 passed`。

修复：

- skipped phase 记录 `skipped=True`。
- Phase 10 skipped 记录 `test_skipped/test_status/test_summary`。
- Phase 11 和 chat summary 使用 `test_summary`。

#### Bug 3：Python 项目误跑 C++ Quality Gate

Phase 9 四层校验固定检查 CMake/main.cpp/test_base.h，导致 installer/Python 误报。

修复：

- Phase 9 按 language/project_type 注册 validator。
- Python 检查 main.py 和 pytest 文件。
- C++ 保留 CMake/main.cpp/test_base.h。

#### Bug 4：生成 cpp_test_phase_skip

checkpoint path 在 Phase 1 识别 installer 前根据默认 `is_cpp=True` 加了 `cpp_` 前缀。

修复：

- checkpoint path 不再预加 `cpp_`。
- e2e 断言无 `cpp_test_phase_skip`。

### Q5：你怎么做多语言？

当前做法：

- Phase 1 识别语言/project_type。
- language_config 提供语言特征。
- PromptEngine 按语言生成 prompt。
- Phase 2 按语言建目录。
- Phase 9 按语言做质量检查。
- Phase 10 按语言跑测试。
- Phase 11 按语言生成 CLAUDE.md 和 report。

后续会统一成 LanguagePlugin。

### Q6：项目和 OpenSpec 的关系？

OpenSpec 是规范协作框架，DevPalAgent 是自动化 Agentic SDLC Runtime。

DevPalAgent 借鉴 OpenSpec：

- spec-first
- requirements lifecycle
- delta
- archive roadmap
- CLAUDE.md integration

但 DevPalAgent 更强调：

- 自动代码生成
- 编译/测试闭环
- 自愈
- checkpoint
- ArtifactGraph

---

## 5. STAR 讲法

### Situation

LLM 可以生成代码，但实际工程中经常出现不可控、不可验证、上下文错配、失败后无法恢复的问题。

### Task

我希望构建一个 Agentic SDLC Runtime，让 LLM 代码生成符合规范、能被验证、能追踪，并支持失败恢复。

### Action

我设计了 11 阶段 OpenSpec workflow，引入 OpenSpecContext、PhaseResult、EnhancedScheduler、PromptEngine、ValidationEngine、ArtifactGraph 和 Phase 10 测试闭环。最近我完成了语言感知稳定版，修复 installer/Python 项目的 C++ 误报、skipped 统计错误和 checkpoint 目录错误。

### Result

现在 installer flow 可以完整跑通：Phase 3/5/6/7/10 正确 skipped，Phase 9 四层 0 issue，Phase 11 输出 skipped 测试摘要，CLAUDE.md 不再有 C++ 编码规范残留，并且有 e2e 测试覆盖。

---

## 6. 适合投递的岗位

### 高匹配

- Agent Engineer
- AI Engineer
- AI Coding Engineer
- Developer Tools Engineer
- LLM Application Engineer
- Workflow/Automation Engineer

### 中高匹配

- Agent Platform Engineer
- AI Infrastructure Engineer
- Prompt/Tool-use Engineer
- Test Automation + AI Engineer

### 需要补强后再投

- Research Scientist
- Multi-agent Research Engineer
- Evaluation Scientist
- Infra-level Agent Runtime Engineer

---

## 7. 通过率评估

| 岗位类型 | 当前通过率估计 | 补 README/demo 后 |
|---|---:|---:|
| Agent 应用工程师 | 75%～85% | 80%+ |
| AI Coding / Developer Tools | 70%～80% | 80%+ |
| Agent Infra / Runtime | 60%～75% | 70%+ |
| 高级 Research / Platform | 45%～65% | 60%+ |

项目优势已经够，但要赢面试，需要稳定 demo、清晰 README、架构图和 failure case 讲法。

---

## 8. 3 分钟 Demo 讲解词

1. 这是一个需求文件：`requirements/test_phase_skip.md`。
2. 我运行 `python test_simple.py`。
3. 系统从 Phase 1 开始解析需求，识别为 installer 项目。
4. 因为 installer 不需要 C++ 技术设计、CMake 和编译测试，所以 Phase 3/5/6/7/10 自动 skipped。
5. Phase 4 仍会基于需求生成 Python installer 项目。
6. Phase 9 做 Python/installer 质量门禁，四层都是 0 issue。
7. Phase 11 生成 final_report 和 CLAUDE.md。
8. 报告里显示 `tests: skipped (...)`，而不是错误的 `0/0 passed`。
9. 这展示了 Agent workflow 的可靠性：它不只是生成代码，还知道什么阶段不适用、如何报告、如何验证。

---

## 9. 当前项目短板的诚实回答

如果面试官问限制，可以这样答：

当前 DevPalAgent 已经有稳定的阶段化 Agent workflow，但还不是完整 OpenSpec 复刻。缺口主要在：

1. 还没有完整 `openspec/changes/<change-id>` 目录模型。
2. Delta 还是 `.spec/delta.json`，不是 OpenSpec Markdown delta spec。
3. Archive 机制还没实现。
4. LanguagePlugin 还没完全主流程化。
5. EventBus 存在但还没接入主执行链。

下一阶段我会优先做 OpenSpec Change MVP 和 Archive + Traceability。

---

## 10. 面试时要避免的说法

不要说：

- “这是一个自动写代码工具。”
- “就是套了一层 prompt。”
- “支持所有语言。”
- “完全实现 OpenSpec。”

建议说：

- “这是一个 Spec-first Agentic SDLC Runtime。”
- “LLM 被放在确定性 workflow 里。”
- “当前稳定支持 C++ 和 Python/installer 的核心闭环，多语言正在插件化。”
- “OpenSpec changes/archive 是下一阶段路线图。”
