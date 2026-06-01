# DevPalAgent Interview Pitch (2026-05-25)

> 面向 Agent Engineer / AI Coding / Developer Tools 岗位的项目讲解稿。  
> **更新日期**：2026-05-25  
> **项目版本**：v2.0  
> **核心亮点**：Multi-Agent Skills + Self-Healing RCA + LLM-as-a-Judge + Prompt Caching

---

## 1. 30 秒版本（最新）

DevPalAgent 是一个 Spec-first Agentic SDLC Runtime。它把需求文档通过 11 阶段 Agent workflow 转成可验证的软件项目。系统包含 **Multi-Agent Skills**（意图识别 + 自动路由）、**Self-Healing RCA**（三层智能根因分析）、**LLM-as-a-Judge**（5 维度代码质量评审）、**Prompt Caching**（成本降低 60.7%）。最近 8 天完成了 6 个重大功能，包括 OpenSpec Change、Skills 系统、根因分析等。量化成果：52K 行代码，135 测试，95.7% 通过率。


---

## 2. 2 分钟版本（最新）

LLM 写代码最大的问题不是”能不能生成”，而是生成结果不可控、不可验证、不可追踪。DevPalAgent 的思路是把 LLM 放进一个确定性的工程流水线里。

**系统分三层**：
1. **Plan-Act-Reflect Agent 链路**：Skills Router → Planner → Executor → Reflector
2. **OpenSpec Runtime 链路**：11 阶段工作流（需求解析 → 代码生成 → 质量门禁 → 测试执行 → 最终报告）
3. **Skills 系统**：5 个内置 Skills（意图识别准确率 100%）

**核心创新点**（8 天内完成）：

1. **Self-Healing RCA**：三层智能根因分析
   - 错误分类（SYNTAX/LOGIC/DEPENDENCY/RUNTIME/TIMEOUT）
   - 追溯链路（代码 → Phase → Prompt → 需求）
   - 影响范围（通过 ArtifactGraph 分析）
   - 策略选择（regenerate/fix_code/adjust_prompt/rollback）
   - 全局学习（跨项目错误模式库）

2. **LLM-as-a-Judge (Phase 9.5)**：5 维度代码质量评审
   - Readability (25%) / Architecture (25%) / Security (20%)
   - Performance (15%) / Maintainability (15%)
   - Overall Score: 86.6/100 + 10 条改进建议
   - 非阻塞设计（不影响 Phase 10）

3. **Prompt Caching 优化**：
   - Cache Hit Rate: 80.5%
   - Cost Reduction: -60.7%
   - Response Time: -55%
   - ROI: 270%（单次运行即回本）

4. **Multi-Agent Skills 系统**：
   - 意图识别准确率：100% (5/5 测试)
   - 自动路由：高置信度直接执行，低置信度 fallback
   - LLM 感知：Planner 可推荐 Skills

5. **OpenSpec Change 完整实现**：
   - proposal/specs/tasks/design 完整目录
   - ADDED/MODIFIED/REMOVED 格式
   - 变更隔离 + 追踪

6. **Skills LLM Awareness**：
   - LLM 可感知并推荐 Skills
   - 系统 prompt 包含 Skills 信息
   - Planner 智能路由
**量化成果**：
- 代码量：52,397 行 Python
- 测试：135 个用例，95.7% 通过率
- 工具：30+ 注册工具
- 开发效率：8 天完成 6 个重大功能（5.75 次提交/天）

**真实工程问题解决**：
1. checkpoint 恢复导致跳过逻辑失效
2. skipped phase 被误显示为 `0/0 passed`
3. Python/installer 项目被误跑 C++ 质量检查
4. checkpoint 早期语言判断导致生成 `cpp_test_phase_skip`
5. CLAUDE.md 中多语言上下文不一致

最后我把流程稳定成语言感知闭环：C++、Python、installer 有不同目录结构、质量检查、测试语义和报告输出，并用 e2e 测试覆盖。


---

## 3. 项目一句话定位（最新）

```text
DevPalAgent = Spec-first workflow + Multi-Agent Skills + Self-Healing RCA + LLM-as-a-Judge + Prompt Caching + Traceable reports
```

或者：

> 一个面向 AI Coding 的 Agentic SDLC Runtime，用确定性工程流水线约束 LLM 代码生成，通过 Multi-Agent 编排、智能自愈和成本优化实现可靠的代码交付。

**核心价值主张**：
- 🎯 **可控**：11 阶段确定性流水线
- ✅ **可验证**：4 层质量门禁 + LLM-as-a-Judge
- 📊 **可追踪**：ArtifactGraph + OpenSpec Change
- 🔧 **可自愈**：Self-Healing RCA + 策略选择
- 💰 **成本优化**：Prompt Caching（-60.7%）

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
