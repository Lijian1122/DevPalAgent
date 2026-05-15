# DevPalAgent OpenSpec 踩坑与解决方案表格版

日期：2026-05-15

## 1. 核心问题总览

| 序号 | 问题 | 影响阶段 | 严重程度 | 当前状态 | 核心结论 |
|---:|---|---|---|---|---|
| 1 | 断点续传只保存阶段编号，未保存上下文 | Phase 4 | 高 | 临时修复 | checkpoint 不能只保存 phase，需要保存完整 context |
| 2 | `resume=False` 仍跳过 Phase 1-9 | Scheduler | 高 | 已修复 | 禁用恢复时必须清空旧 checkpoint |
| 3 | 无测试文件时返回成功，出现 `0/0 passed` | Phase 10/11 | 高 | 已修复 | `0/0` 不是成功，应视为验证失败 |
| 4 | Phase 4 提示词要求测试宏，但模板未提供 | Phase 4/10 | 高 | 已修复 | Prompt 要求的 API 必须真实存在于模板中 |
| 5 | C++ 示例 `{}` 被 Python `.format()` 误解析 | Phase 4 | 高 | 已修复 | Prompt 中的代码示例需要格式化安全测试 |
| 6 | AI 看到已有文件后拒绝生成代码 | Phase 4 | 高 | 已修复 | Prompt 和 tool handler 的覆盖策略必须一致 |
| 7 | 主程序编译被测试编译失败误导 | Phase 10 | 中 | 已修复 | main build 和 test build 需要分离 |
| 8 | AI 自愈输出格式不稳定 | Phase 10 | 中 | 已缓解 | 自愈输出应优先使用纯代码格式 |
| 9 | 阶段成功条件不一致，最终报告可能假成功 | Scheduler/Phase 11 | 中 | 部分修复 | 每个 Phase 应有明确输入、输出、成功条件 |
| 10 | README 宣称能力和主链路接入不完全一致 | 项目架构 | 中 | 待优化 | 应区分已接入、已实现未接入、规划能力 |

## 2. 详细问题表

| 序号 | 现象 | 根本原因 | 已采取修复 | 后续彻底方案 | 建议回归测试 |
|---:|---|---|---|---|---|
| 1 | `[RESUME] Phase 4` 后报 `tech_design_content is empty` | checkpoint 只保存 `last_phase` 和 `completed_phases`，没有保存 `OpenSpecContext` | 入口调用 `run_all_phases(resume=False)`，禁用断点续传 | 持久化完整 context：requirements、design、project_dir、generated_files、phase_results、artifact graph | `test_resume_phase4_restores_tech_design_content` |
| 2 | 重新执行完整流程时直接 `[SKIP] Phase 1` 到 `[SKIP] Phase 9` | `_run_phases_with_enhancements()` 无条件根据 checkpoint 跳过 completed phases | `resume=False` 时执行 `checkpoint.clear()` | scheduler 内部区分 fresh run 和 resume run，避免状态串扰 | `test_resume_false_clears_checkpoint` |
| 3 | 最终显示 `测试结果: 0/0 通过` | Phase 10 在无测试目录或无测试文件时返回 OK | 无测试文件、无编译器时改为 `PhaseResult.fail()` | Phase 11 再次验证 `test_total > 0` | `test_phase10_no_tests_is_failure` |
| 4 | 测试文件用了 `RUN_TEST`，但 `test_base.h` 没有该宏，编译失败 | Phase 4 Prompt 和 C++ 模板 API 不一致 | 在 `cpp_templates.py` 的 `_TEST_BASE_H` 中补齐 `RUN_TEST`、`TEST_MAIN_BEGIN`、`TEST_MAIN_END` | 建立 Prompt-Template 契约测试 | `test_cpp_test_base_contains_required_macros` |
| 5 | Phase 4 抛 `KeyError`，内容是 `TEST_MAIN_BEGIN...` | `_AI_SYSTEM_PROMPT.format(namespace=...)` 把 C++ `{}` 当占位符 | 将示例中的 `{}` 改成 `{{}}` | 所有 Prompt 增加 format-safe 测试 | `test_phase4_prompt_format_safe` |
| 6 | Phase 4 失败：`AI produced no code files`，AI 回复“文件已存在不需要生成” | Prompt 写了 `do not regenerate`，tool handler 也跳过所有已有文件 | Prompt 改为重新生成业务文件；tool handler 只跳过基础设施文件，业务文件允许覆盖 | 支持 explicit overwrite policy / dry-run diff | `test_phase4_overwrites_existing_business_files` |
| 7 | 日志显示 main program build failed，但实际可能是测试目标失败 | `cmake --build` 默认构建 all target，包括测试 | 主程序编译指定 `${project}_app` target | Build report 区分 app build、test build、test run | `test_compile_main_uses_app_target` |
| 8 | 自愈失败：`Fixed code too short` / `AI did not return valid code` | Prompt 要求 Markdown 代码块，解析器又排斥 Markdown/解释文本 | 自愈 Prompt 改为返回纯 C++ 代码，解析器兼容纯代码和 code block | 自愈输出 schema 化，支持写入前 dry-run compile | `test_self_healer_extracts_plain_cpp_code` |
| 9 | 某些阶段失败但最终仍可能输出成功感知 | Phase 成功条件分散，缺少统一质量门禁 | Phase 10 的无测试/无编译器改成失败，关键阶段包含 Phase 10 | 引入 `PhaseSuccessPolicy` | `test_phase11_rejects_zero_total_tests` |
| 10 | README 写了 DeltaSpec、ArtifactGraph、ValidationEngine，但主流程未充分接入 | 架构模块有实现，但主 11 阶段仍以流水线为主 | 已在架构分析中标记该断层 | README 分层标注“已接入 / 已实现未接入 / 规划中” | `test_main_workflow_uses_spec_model` |

## 3. 按模块归类的问题

| 模块 | 已暴露问题 | 影响 | 建议优化 |
|---|---|---|---|
| `EnhancedOpenSpecScheduler` | checkpoint 跳过逻辑与 `resume=False` 冲突 | 导致流程从中间阶段错误开始 | 明确 fresh/resume 两种运行模式 |
| `CheckpointManager` | 保存状态过少 | 恢复后 context 丢失 | 保存完整 `OpenSpecContext` 快照 |
| `Phase4GenerateCode` | Prompt 与模板、tool handler 不一致 | 代码不生成或生成代码无法编译 | 建立 Prompt 契约测试 |
| `cpp_templates.py` | 测试模板 API 不完整 | 测试文件编译失败 | 模板 API 版本化，并传给模型 |
| `Phase10RunTests` | 无测试时假成功；主程序构建目标不精确 | 最终报告误导 | Phase 10 作为硬质量门禁 |
| `TestSelfHealer` | 输出解析不稳定 | 修复失败率高 | 纯代码输出 + schema 输出 + 编译前校验 |
| `Phase11FinalReport` | 汇总时缺少二次验证 | 可能展示假成功 | 验证 `test_total > 0` 和关键产物存在 |
| README / 文档 | 宣称能力和主流程接入程度不一致 | 面试/展示时容易被追问 | 明确能力成熟度分级 |

## 4. Agent 工程原则总结表

| 原则 | 说明 | 对应踩坑 |
|---|---|---|
| 不相信模型输出，必须工具验证 | 代码生成完成不代表任务完成，必须编译和测试 | 0/0 假成功、测试编译失败 |
| Prompt 是接口，不是文案 | Prompt 中出现的宏、函数、文件名、格式都必须和代码一致 | `RUN_TEST` 宏缺失、`.format()` 报错 |
| 状态恢复必须恢复完整上下文 | 只保存 phase 编号无法恢复复杂流程 | `tech_design_content` 丢失 |
| 0/0 不是成功 | 没有测试运行就是验证失败 | Phase 10 无测试返回 OK |
| 错误归因要精确 | main build、test build、test run、自愈失败要分开记录 | 主程序编译误判 |
| 自愈前应有快照 | AI 修复可能破坏代码，失败要能回滚 | Phase 10 自愈 |
| 每次事故都应变成回归测试 | 真实运行发现的问题要沉淀为自动化测试 | 所有本轮问题 |
| Prompt 和工具层策略必须一致 | Prompt 说覆盖，工具层不能跳过 | AI 不生成已有文件 |
| 模板 API 要版本化 | 模型生成代码依赖模板提供的真实 API | `test_base.h` 宏问题 |
| 最终报告不能只汇总数字 | Phase 11 应重新校验关键成功条件 | 0/0 最终成功 |

## 5. 建议新增回归测试表

| 优先级 | 测试名 | 覆盖问题 | 预期结果 |
|---|---|---|---|
| P0 | `test_resume_false_clears_checkpoint` | resume=False 仍跳过阶段 | fresh run 不读取旧 completed phases |
| P0 | `test_phase4_prompt_format_safe` | Prompt 中 C++ `{}` 触发 KeyError | `_AI_SYSTEM_PROMPT.format()` 不报错 |
| P0 | `test_cpp_test_base_contains_required_macros` | Prompt 要求的测试宏不存在 | 模板包含全部测试宏 |
| P0 | `test_phase10_no_tests_is_failure` | 0/0 假成功 | 无测试文件时 Phase 10 fail |
| P0 | `test_phase10_no_compiler_is_failure` | 无编译器假成功 | 无编译器时 Phase 10 fail |
| P1 | `test_phase4_overwrites_existing_business_files` | 已有项目不重新生成业务代码 | 业务文件允许覆盖 |
| P1 | `test_phase4_skips_infrastructure_files` | 基础设施文件被覆盖 | CMake/test_base/README 被跳过 |
| P1 | `test_compile_main_uses_app_target` | 主程序编译误判 | build command 指定 app target |
| P1 | `test_self_healer_extracts_plain_cpp_code` | 自愈输出解析失败 | 纯代码响应可被解析 |
| P1 | `test_phase11_rejects_zero_total_tests` | 最终报告假成功 | `test_total == 0` 时整体失败 |
| P2 | `test_e2e_simple_login_generates_tests_and_passes` | 端到端回归 | simple_login 全流程成功 |
| P2 | `test_e2e_existing_project_regenerates_business_code` | 已存在项目回归 | 业务代码重新生成并测试通过 |
| P2 | `test_e2e_windows_backslash_requirements_path` | Windows 路径兼容 | `requirements\simple_login.md` 能正确解析 |

## 6. 后续优化优先级表

| 优先级 | 优化项 | 目标 | 产出 |
|---|---|---|---|
| P0 | 补齐回归测试 | 避免同类问题反复出现 | `tests/openspec/` 测试集 |
| P0 | 修复调度器显示空标签 | 提升运行日志可读性 | 清晰的 Timeout/Retry/Checkpoint 状态 |
| P0 | 统一 OpenSpec 主入口 | 避免新旧流程分叉 | 单一 `OpenSpecWorkflowExecutor` |
| P0 | Prompt 契约测试 | 防止 Prompt 与模板/解析器不一致 | prompt test suite |
| P1 | Requirement Model 结构化 | 从文档驱动升级为 Spec 对象驱动 | `.spec/requirements.json` |
| P1 | ArtifactGraph 接入主流程 | 建立需求-代码-测试追踪关系 | `.spec/artifact_graph.json` |
| P1 | Phase 11 输出验收矩阵 | 明确每个需求是否通过 | acceptance matrix |
| P1 | checkpoint 保存完整 context | 支持真正断点续传 | `.spec/context.json` |
| P2 | DeltaSpec 增量修改 | 支持已有项目安全修改 | patch/diff workflow |
| P2 | dry-run / diff 模式 | 修改前可审查 | `devpal openspec plan/apply` |
| P2 | snapshot / rollback | 自愈失败可回滚 | snapshots 目录 |
| P2 | selective test | 只跑受影响测试 | impact-based testing |
| P3 | eval framework | 量化 Agent 成功率 | eval report JSON/JUnit |
| P3 | CI 模式 | 接入自动化流水线 | 无交互执行模式 |
| P3 | 标准 CLI | 产品化使用 | `devpal openspec plan/apply/test/verify` |

## 7. 面试展示用精简表

| 面试官关注点 | 项目中的真实案例 | 可以强调的能力 |
|---|---|---|
| Agent 如何保证生成代码可用？ | Phase 10 编译、CTest、自愈 | LLM + 编译测试反馈闭环 |
| Agent 如何处理失败？ | 超时、重试、关键阶段终止、自愈 | workflow orchestration |
| Prompt 不稳定怎么办？ | `.format()` 大括号、测试宏不一致 | prompt contract engineering |
| 状态恢复怎么做？ | checkpoint context 丢失 | state management 思考 |
| 如何避免假成功？ | 0/0 tests 改为失败 | quality gate 意识 |
| 如何减少模型幻觉？ | 模板 API、编译器反馈、自愈 | tool-grounded generation |
| 下一步怎么演进？ | ArtifactGraph、DeltaSpec、ValidationEngine 接入 | spec-first 架构规划 |

## 8. 一句话总结

本轮 OpenSpec 调试暴露的问题，本质上不是单纯代码 bug，而是 Coding Agent 工程化问题：

```text
状态要完整，Prompt 要契约化，模板要可验证，工具要给真实反馈，测试不能假成功，失败要能定位和回滚。
```

这些经验后续应沉淀为回归测试、质量门禁和 Spec-First 主流程约束。
