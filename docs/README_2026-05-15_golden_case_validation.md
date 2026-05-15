# OpenSpec Golden Case 验证说明

日期：2026-05-15

## 1. 目的

Golden Case 用于验证 OpenSpec 核心链路是否完整可用。它不是简单地跑一次流程，而是把“什么才算成功”固定成自动断言，防止历史问题回归。

当前 golden case 使用：

```text
requirements/simple_login.md
```

验证链路：

```text
需求文档 -> Phase 1-11 -> 代码生成 -> CMake 编译 -> 测试运行 -> 最终报告
```

## 2. 稳定入口

Golden case 使用稳定脚本入口：

```bash
python run_ai_flow.py -r requirements/simple_login.md
```

该入口会调用增强版调度器 `EnhancedOpenSpecScheduler`，并使用 `resume=False`，避免旧 checkpoint 导致 Phase 被错误跳过。

不建议使用自然语言交互入口作为 golden case，因为 planner 和关键词匹配会引入额外不确定性。

## 3. 快速轻量回归测试

轻量测试不调用 LLM，不跑 CMake，只验证关键契约：

```bash
pytest tests/openspec
```

覆盖内容：

- Phase 4 prompt 可以安全 `.format()`。
- Phase 4 prompt 要求的测试宏存在。
- C++ `test_base.h` 模板包含所需宏。
- Phase 10 无测试时必须失败。
- checkpoint clear 后不会继续跳过旧 completed phases。

## 4. 完整 Golden E2E 测试

完整 golden case 默认跳过，需要显式开启：

```bash
pytest tests/golden/test_simple_login_golden.py --run-golden
```

也可以直接运行：

```bash
python run_ai_flow.py -r requirements/simple_login.md
```

## 5. 前置条件

完整 E2E 需要：

- `ANTHROPIC_AUTH_TOKEN` 或 `ANTHROPIC_API_KEY`
- CMake
- MSVC 或 g++
- Python 依赖已安装

如果缺少 API key、编译器或 CMake，golden E2E 可能失败，这是预期行为。

## 6. 成功标准

Golden E2E 必须满足：

1. 进程退出码为 `0`。
2. 输出包含 `[SUCCESS] 流程成功完成`。
3. 不出现 `[SKIP] Phase 1` 到 `[SKIP] Phase 9`。
4. 不出现 `0/0 passed` 或 `0/0 通过`。
5. 生成 `cpp_simple_login/` 本地项目目录。
6. 生成 `cpp_simple_login/docs/final_report.md`。
7. 生成 `cpp_simple_login_*.log` 日志。
8. 日志包含 Phase 1、Phase 4、Phase 10、Phase 11。
9. 至少生成一个 `build_test/**/test_*.exe` 测试可执行文件。

## 7. 产物策略

`cpp_simple_login/` 是本地生成物，已加入 `.gitignore`，不应提交。

默认运行 golden E2E 时不会删除整个 `cpp_simple_login/`，只清理以下构建目录：

```text
cpp_simple_login/build/
cpp_simple_login/build_test/
cpp_simple_login/build_verify/
```

如果需要强制全量重建，可以设置：

```bash
DEVPAL_GOLDEN_CLEAN=1 pytest tests/golden/test_simple_login_golden.py --run-golden
```

## 8. 常见失败排查

| 现象 | 可能原因 | 处理方式 |
|---|---|---|
| Phase 1-9 被 `[SKIP]` | 旧 checkpoint 影响流程 | 确认入口使用 `resume=False`，并清理 `.spec/checkpoint.json` |
| Phase 4 无代码生成 | AI 认为文件已存在或 Prompt/tool handler 不一致 | 检查 Phase 4 prompt 和 write_file 覆盖策略 |
| Phase 4 `KeyError` | Prompt 中 C++ `{}` 未转义 | 运行 `pytest tests/openspec/test_phase4_prompt_contract.py` |
| Phase 10 `No tests to run` | 没有生成 `tests/test_*.cpp` | 检查 Phase 4 生成结果 |
| `0/0 passed` | 测试未实际运行但被误判成功 | Phase 10/11 必须将其视为失败 |
| 编译器找不到 | MSVC/g++ 环境缺失 | 安装 VS Build Tools 或 g++，确认 CMake 可用 |
| 自愈失败 | AI 输出不是可写入的 C++ 代码 | 检查 `test_self_healer.py` 输出解析 |

## 9. 使用建议

- 日常开发：运行 `pytest tests/openspec`。
- 修改 Phase 4 Prompt、模板、Phase 10、scheduler 后：运行 golden E2E。
- 提交前：至少运行轻量回归测试。
- 发版前：运行完整 golden E2E。

## 10. 后续扩展

未来可以增加更多 golden case：

- `todo_cli`
- `file_parser`
- `calculator_cpp`
- `python_package`

每个 golden case 应包含：

- 固定需求文件。
- 固定入口。
- 产物清单。
- 测试通过标准。
- 日志断言。
- 最终报告断言。
