# DevPalAgent OpenSpec 踩坑记录与解决思路

日期：2026-05-15

## 1. 背景

本文整理 DevPalAgent 在 OpenSpec 自动化开发流程中遇到的主要问题、根本原因、解决方式和后续预防方案。

信息来源包括：

- 最近 Git 提交记录。
- OpenSpec 11 阶段流程实际运行日志。
- `cpp_simple_login` 项目端到端测试过程。
- 最近围绕 Phase 4、Phase 10、断点续传、测试框架、自愈机制的调试上下文。

相关近期提交：

```text
2497192 fix: stabilize OpenSpec workflow execution
077704a feat: complete Phase 10 self-healing and CMake-based compilation
ce2f0be refactor: [by AI] unify OpenSpec pipeline and template system
b7a52c2 feat:可自动化完成整个登录需求里程碑
d2e00e1 fix: resolve persistent OpenSpec C++ compilation failures and improve workflow
```

## 2. 总体结论

OpenSpec 当前已经能跑通从需求文档到项目生成、代码生成、编译测试、自愈和最终报告的端到端流程。但在真实运行过程中暴露出一类典型 Agent 工程问题：

```text
LLM 生成能力本身不是最大问题，真正的问题是流程状态、工具协议、Prompt 契约、模板一致性、编译反馈和失败判定。
```

也就是说，Coding Agent 的关键不是“让模型写代码”，而是：

- 如何让模型在正确上下文中写代码。
- 如何让生成代码符合模板和工具协议。
- 如何用编译器和测试验证结果。
- 如何避免假成功。
- 如何把失败信息反馈给模型进行修复。
- 如何把踩坑沉淀为自动化回归测试。

## 3. 坑 1：断点续传只保存阶段编号，导致上下文丢失

### 现象

运行中出现：

```text
[RESUME] Phase 4
[ERROR] 失败原因: tech_design_content is empty - did Phase 3 succeed?
```

### 根本原因

增强调度器的 checkpoint 只保存了：

```json
{
  "last_phase": 3,
  "completed_phases": [1, 2, 3]
}
```

第二次运行时从 Phase 4 恢复，但 Phase 1-3 被跳过，导致内存中的 `OpenSpecContext` 没有恢复：

- `requirements_content`
- `tech_design_content`
- `project_name`
- `project_dir`
- `generated_files`
- `test_docs`

因此 Phase 4 缺少技术设计内容，直接失败。

### 已采取修复

短期修复：禁用断点续传。

入口处调用：

```python
scheduler.run_all_phases(resume=False)
```

并在 `EnhancedOpenSpecScheduler.run_all_phases()` 中增加：

```python
if self.checkpoint and not resume:
    self.checkpoint.clear()
```

确保 `resume=False` 时不会继续根据旧 checkpoint 跳过阶段。

### 后续彻底方案

实现完整上下文持久化。

checkpoint 应保存：

- phase results
- requirements content
- parsed requirements
- project name
- project dir
- technical design
- generated files
- test docs
- llm usage
- artifact graph snapshot

建议保存为：

```text
.spec/checkpoints/latest.json
.spec/context.json
.spec/artifact_graph.json
```

### 预防测试

应增加：

- `test_resume_false_clears_checkpoint`
- `test_resume_phase4_restores_tech_design_content`
- `test_checkpoint_contains_required_context_fields`

## 4. 坑 2：resume=False 仍然跳过 Phase 1-9

### 现象

执行完整流程时出现：

```text
[SKIP] Phase 1
[SKIP] Phase 2
[SKIP] Phase 3
...
[SKIP] Phase 9
Phase 10: no test files found
Phase 11: tests 0/0 passed
```

### 根本原因

虽然入口传了 `resume=False`，但 `EnhancedOpenSpecScheduler._run_phases_with_enhancements()` 内部仍然无条件检查：

```python
if self.checkpoint and self.checkpoint.is_phase_completed(i):
    print(f"[SKIP] Phase {i}")
    continue
```

因此只要 checkpoint 里记录了 completed phases，就会跳过阶段。

### 已采取修复

在 `resume=False` 时先清空 checkpoint：

```python
if self.checkpoint and not resume:
    self.checkpoint.clear()
```

这样后续 `is_phase_completed()` 不会命中旧状态。

### 预防测试

应增加：

- 构造已有 checkpoint。
- 调用 `run_all_phases(resume=False)`。
- 断言 Phase 1 没有被跳过。

## 5. 坑 3：没有测试文件时返回成功，导致 0/0 passed 假阳性

### 现象

流程最终输出：

```text
OpenSpec 11 阶段流程已完成
测试结果: 0/0 通过
```

但实际上没有任何测试被运行。

### 根本原因

Phase 10 在没有 `tests/` 或没有 `test_*.cpp` 文件时返回了 OK：

```python
return PhaseResult.ok("No tests to run", test_passed=0, test_total=0)
```

这导致 Phase 11 认为流程成功。

### 已采取修复

改为失败：

```python
return PhaseResult.fail("No tests to run", errors=["no test_*.cpp files found"])
```

没有编译器时也改为失败：

```python
return PhaseResult.fail("No compiler available", errors=["MSVC/g++ compiler not found"])
```

### 设计原则

对于 Coding Agent，`0/0 passed` 不是成功，而是无效验证。

成功必须满足：

```text
test_total > 0 and test_passed == test_total
```

### 预防测试

应增加：

- `test_phase10_no_tests_is_failure`
- `test_phase10_no_compiler_is_failure`
- `test_phase11_rejects_zero_total_tests`

## 6. 坑 4：Phase 4 提示词要求测试宏，但模板没有提供

### 现象

AI 生成的测试文件使用：

```cpp
TEST_MAIN_BEGIN
RUN_TEST(testFunction);
TEST_MAIN_END
```

但 `tests/test_base.h` 模板里没有这些宏，导致测试编译失败。

### 根本原因

Prompt 和模板 API 不一致。

Phase 4 提示词要求：

```text
Each test file MUST use RUN_TEST, TEST_MAIN_BEGIN, and TEST_MAIN_END macros.
```

但 `cpp_templates.py` 中的 `_TEST_BASE_H` 只提供：

```cpp
ASSERT_TRUE
ASSERT_EQ
test_pass
test_fail
test_run_summary
```

没有：

```cpp
RUN_TEST
TEST_MAIN_BEGIN
TEST_MAIN_END
```

### 已采取修复

在 C++ 测试模板中补齐宏：

```cpp
#define TEST_MAIN_BEGIN int total = 0; int passed = 0; int failed = 0; std::cout << "Running tests..." << std::endl;
#define RUN_TEST(test_func) do { ++total; try { test_func(); ++passed; test_pass(#test_func); } catch (...) { ++failed; } } while(0)
#define TEST_MAIN_END test_run_summary(passed, failed); return failed == 0 ? 0 : 1;
```

并统一测试输出为：

```text
Results: X/Y passed
```

### 设计原则

Prompt 中要求模型使用的 API，必须由模板或上下文真实提供。

不能让模型基于“想象中的测试框架”写代码。

### 预防测试

应增加：

- `test_cpp_template_contains_prompt_required_macros`
- `test_generated_test_file_compiles_with_test_base`
- `test_test_output_parser_supports_template_output`

## 7. 坑 5：Phase 4 prompt 中 C++ 大括号被 Python `.format()` 误解析

### 现象

Phase 4 执行时报错：

```text
KeyError: '\n      TEST_MAIN_BEGIN\n      RUN_TEST(testFunction1);\n      RUN_TEST(testFunction2);\n      TEST_MAIN_END\n  '
```

### 根本原因

`_AI_SYSTEM_PROMPT` 使用：

```python
_AI_SYSTEM_PROMPT.format(namespace=namespace)
```

但提示词中加入了 C++ 示例：

```cpp
int main() {
    TEST_MAIN_BEGIN
    RUN_TEST(testFunction1);
    TEST_MAIN_END
}
```

Python `.format()` 将 `{ ... }` 当成占位符解析，导致 KeyError。

### 已采取修复

将 C++ 示例中的大括号转义：

```cpp
int main() {{
    TEST_MAIN_BEGIN
    RUN_TEST(testFunction1);
    TEST_MAIN_END
}}
```

`.format()` 后实际传给模型的仍是正常 C++：

```cpp
int main() {
    TEST_MAIN_BEGIN
    RUN_TEST(testFunction1);
    TEST_MAIN_END
}
```

### 预防措施

所有包含 `.format()` 的 Prompt 必须做格式化安全测试。

### 预防测试

应增加：

- `test_phase4_system_prompt_format_safe`
- `test_all_prompts_format_without_keyerror`

## 8. 坑 6：AI 看到文件已存在后拒绝生成代码

### 现象

Phase 4 报错：

```text
AI produced no code files
text=所有文件都已存在，不需要重新生成
```

### 根本原因

之前用户提示中写了：

```text
EXISTING FILES (do not regenerate)
```

AI 看到项目目录里已有文件后，主动决定不再生成任何业务代码。

同时 `write_file` 工具处理器也会跳过所有已存在文件：

```python
if target.exists():
    return "[skipped] already exists"
```

这导致已存在项目无法重新生成业务文件。

### 已采取修复

Prompt 改为明确要求：

```text
Even if files exist, REGENERATE business files (*.cpp, *.h in src/ and include/).
ONLY skip infrastructure files: CMakeLists.txt, README.md, tests/test_base.h, include/<project>.h.
```

工具处理器也改为：

- 基础设施文件存在时跳过。
- 业务代码文件存在时允许覆盖。

### 设计原则

Prompt 和 tool handler 必须一致。

如果 Prompt 说可以覆盖业务文件，但工具层仍然跳过，就会形成隐性冲突。

### 预防测试

应增加：

- `test_phase4_overwrites_existing_business_files`
- `test_phase4_skips_existing_infrastructure_files`
- `test_phase4_fails_if_ai_writes_no_business_files`

## 9. 坑 7：主程序编译失败被测试编译失败误导

### 现象

日志显示：

```text
[BUILD] Compiling main program...
[FAIL] CMake build failed
```

但实际失败可能来自测试目标，而不一定是主程序。

### 根本原因

Phase 10 编译主程序时使用默认：

```bash
cmake --build build --config Release
```

这个命令会构建默认 all target，包括测试目标。如果测试编译失败，也会导致主程序构建步骤失败。

### 已采取修复

主程序编译改为指定 app target：

```bash
cmake --build build --config Release --target cpp_simple_login_app
```

代码中根据项目目录名生成 target：

```python
target_name = f"{project_dir.name}_app"
```

### 设计原则

主程序编译和测试编译应该分离，避免错误归因混乱。

### 预防测试

应增加：

- `test_compile_main_uses_app_target`
- `test_test_compile_failure_does_not_mark_main_compile_failed`

## 10. 坑 8：AI 自愈输出格式不稳定

### 现象

Phase 10 自愈时出现：

```text
[HEAL] Failed: Fixed code too short
[HEAL] Failed: AI did not return valid code
```

### 根本原因

自愈 Prompt 既要求：

```text
Return ONLY the fixed C++ code inside ```cpp code blocks
```

又要求：

```text
Do NOT include markdown text
```

模型可能返回解释、过短代码、或 Markdown 格式不符合解析器预期。

### 已采取修复

将编译错误自愈提示词改成：

```text
Return the complete fixed C++ test file as plain text code only.
Return ONLY the complete fixed C++ code, starting with #include.
Do NOT wrap the answer in markdown fences.
```

解析器同时兼容：

- Markdown code block。
- 以 `#include` 开头的纯代码。

### 设计原则

自愈场景中，模型输出应该尽量接近机器可直接写入文件的格式。

### 预防测试

应增加：

- `test_self_healer_extracts_plain_cpp_code`
- `test_self_healer_rejects_explanatory_text`
- `test_self_healer_preserves_test_base_api`

## 11. 坑 9：阶段失败和最终成功判定不够严格

### 现象

之前出现过某些非关键阶段失败但流程继续，或者 0/0 测试仍被最终报告展示为成功。

### 根本原因

不同 Phase 对成功/失败的定义不一致：

- 有些 Phase 没有产物也算成功。
- 有些 Phase 失败但只是 warning。
- Phase 11 汇总时依赖 context 中的测试数字，没有再次验证测试总数。

### 已采取修复

目前已将关键阶段包括：

```python
CRITICAL_PHASES = [1, 2, 3, 4, 10]
```

Phase 10 对无测试、无编译器、编译失败均返回失败。

### 后续建议

引入统一质量门禁：

```text
PhaseSuccessPolicy
- required_outputs
- required_context_fields
- allowed_warnings
- hard_fail_conditions
```

每个 Phase 必须声明：

- 输入依赖。
- 输出产物。
- 成功条件。
- 失败条件。

## 12. 坑 10：文档宣称能力和实际主链路能力不完全一致

### 现象

README 中描述了：

- ValidationEngine
- DeltaSpec
- ArtifactGraph
- RolloutEngine
- EventBus

但实际 OpenSpec 11 阶段主链路还没有充分使用这些模块。

### 根本原因

项目经历了多轮功能演进，部分模块已经实现，但尚未整合进当前主链路。

### 风险

面试或项目展示时容易被追问：

- 这些模块是否真的参与当前流程？
- ArtifactGraph 是否真的驱动测试选择？
- DeltaSpec 是否真的保护用户代码？
- ValidationEngine 是否作为质量门禁？

### 建议处理

README 中区分：

- 已接入主流程能力。
- 已实现但未接入能力。
- 规划中能力。

这样更可信。

## 13. 从这些坑总结出的 Agent 工程原则

### 原则 1：不要相信模型输出，必须用工具验证

代码生成完成不等于任务完成。

必须经过：

- 文件存在性检查。
- 编译检查。
- 测试检查。
- 输出解析。
- 验收条件检查。

### 原则 2：Prompt 是接口，不是文案

Prompt 中出现的：

- 宏。
- 函数。
- 文件路径。
- target 名。
- 输出格式。

都必须和代码模板、解析器、工具处理器一致。

### 原则 3：状态恢复必须恢复完整上下文

只保存 phase 编号没有意义。

断点续传必须保存可继续执行所需的全部上下文。

### 原则 4：0/0 不是成功

没有测试被运行时，应该判定为验证失败。

### 原则 5：错误归因要精确

主程序构建、测试构建、测试运行、自愈失败应分别记录。

否则 Agent 无法把正确反馈传给模型。

### 原则 6：自愈之前要有快照

AI 自愈会修改代码，应在修改前保存 snapshot。

失败时可以回滚。

### 原则 7：把每次事故变成回归测试

每次真实运行中发现的问题，都应该沉淀为自动化测试。

## 14. 建议新增的回归测试清单

### Scheduler / Checkpoint

- `test_resume_false_clears_checkpoint`
- `test_resume_does_not_skip_required_phases_without_context`
- `test_checkpoint_persists_required_context`

### Phase 4 / Prompt

- `test_phase4_prompt_format_safe`
- `test_phase4_prompt_mentions_existing_test_base_api`
- `test_phase4_overwrites_business_files`
- `test_phase4_skips_infrastructure_files`

### Templates

- `test_cpp_test_base_contains_required_macros`
- `test_cpp_cmake_contains_app_target`
- `test_cpp_template_test_output_is_parseable`

### Phase 10 / Build & Test

- `test_phase10_no_tests_is_failure`
- `test_phase10_no_compiler_is_failure`
- `test_phase10_compiles_main_target_only`
- `test_phase10_parse_results_x_y_passed`

### Self-Healer

- `test_self_healer_extracts_plain_cpp_code`
- `test_self_healer_rejects_markdown_explanation`
- `test_self_healer_uses_fallback_model_on_second_attempt`

### End-to-End

- `test_e2e_simple_login_generates_tests_and_passes`
- `test_e2e_existing_project_regenerates_business_code`
- `test_e2e_windows_backslash_requirements_path`

## 15. 后续优化路线

### P0：稳定性优先

1. 补回归测试。
2. 修复调度器空标签显示。
3. 统一 OpenSpec 主入口。
4. 为 Prompt 增加契约测试。
5. 为 Phase 成功条件增加统一策略。

### P1：Spec-First 主链路接入

1. Phase 1 输出结构化 Requirement Model。
2. Phase 3 设计文档绑定需求 ID。
3. Phase 4 代码和测试绑定需求 ID。
4. 接入 ArtifactGraph。
5. Phase 11 输出需求验收矩阵。

### P2：安全增量修改

1. 接入 DeltaSpec。
2. 支持 dry-run 和 diff。
3. 支持 snapshot 和 rollback。
4. 保护用户手写代码。
5. 根据影响范围选择性跑测试。

### P3：评估与产品化

1. 增加 eval cases。
2. 统计成功率、耗时、LLM 调用次数、自愈成功率。
3. 输出 JSON/JUnit 报告。
4. 支持 CI 模式。
5. 标准化 CLI：`plan/apply/test/verify/resume`。

## 16. 总结

这轮 OpenSpec 流程中遇到的问题，本质上都是 Coding Agent 工程化必经问题：

```text
状态不完整、Prompt 与工具不一致、模板契约缺失、失败判定过宽、自愈输出不稳定、质量门禁不足。
```

对应的解决方向是：

```text
完整上下文持久化 + Prompt 契约测试 + 模板 API 校验 + 编译测试硬门禁 + Traceability + 回归测试沉淀。
```

当前项目已经跑通端到端流程，下一阶段最重要的是把这些踩坑变成系统级约束，让 OpenSpec 从“能跑通”升级为“稳定、可复现、可追踪、可增量演进”。
