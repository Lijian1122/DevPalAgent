# Phase 1 验收资产闭环记录（2026-06-14）

> 目标：把 DevPalAgent 当前 MVP 的验收路径从“口头可跑”固化为“命令可复现、失败可留痕、生成目录有策略”。

## 1. 本轮完成项

### 1.1 Proof scripts 已验证

以下命令已在 `C:\code\DevPalAgent` 执行通过：

```bash
python scripts/run_golden_openspec_flow.py --dry-run
python scripts/benchmark_parallel_executor.py --json
python scripts/evaluate_vector_retrieval.py --json
```

结果摘要：

| 命令 | 结果 | 说明 |
| --- | --- | --- |
| golden dry-run | 通过 | 生成 `.spec/golden_flow/golden_flow_report.json` 与 `.md` |
| parallel benchmark | 通过 | 8 tasks、25ms delay、max concurrency 4，观测 speedup 约 3.78 |
| vector eval | 通过 | 3/3 cases hit，`recall_at_k = 1.0`，使用 deterministic smoke case |

### 1.2 核心 targeted tests 已验证

默认 pytest 临时目录在当前环境无权限，因此使用 workspace 内 `.tmp/pytest` 并禁用 pytest cache：

```bash
New-Item -ItemType Directory -Force .tmp | Out-Null
python -m pytest -p no:cacheprovider --basetemp .tmp\pytest tests/openspec/test_sandbox_merge.py tests/golden/test_golden_flow_runner.py tests/openspec/test_phase4_multi_agent.py tests/openspec/test_phase9_quality_gate.py tests/openspec/test_phase11_final_report.py tests/test_eventbus_integration.py tests/e2e/test_archive_e2e.py tests/openspec/test_archive_lifecycle.py
```

结果：

```text
49 passed, 2 warnings
```

说明：

- 初次直接运行 pytest 时，`C:\Users\72740\AppData\Local\Temp\pytest-of-72740` 权限不足导致 fixture setup 失败。
- 使用 `--basetemp .tmp\pytest` 后，测试全部通过。
- `-p no:cacheprovider` 用于避免当前 `.pytest_cache` 权限问题影响验收。

### 1.3 真实 non-dry-run golden flow 已尝试

已执行：

```bash
python scripts/run_golden_openspec_flow.py --requirements requirements/simple_login.md --timeout 300
```

执行结果：

```text
propose 阶段完成，生成 change:
feature-简化登录系统需求文档-20260614_162530

apply 阶段失败。
```

失败原因分两层：

1. sandbox 网络限制下，Anthropic API 连接失败。
2. 允许网络后，Anthropic API 返回 `403 SUBSCRIPTION_NOT_FOUND`，提示当前账号或 group 没有可用订阅。

关键错误：

```text
Anthropic API call failed: PermissionDeniedError: Error code: 403 -
{'code': 'SUBSCRIPTION_NOT_FOUND', 'message': 'No active subscription found for this group'}
```

结论：

- 当前真实 non-dry-run golden flow 的阻塞点是外部 AI provider 账号/订阅权限，不是本地 OpenSpec lifecycle、sandbox merge、archive 或 proof scripts 的单元级失败。
- 后续需要使用有效 Anthropic 订阅/API key，或增加离线 fake provider 模式，才能把 non-dry-run golden report 固化为发布级资产。

### 1.4 Golden runner 失败留痕已增强

`scripts/run_golden_openspec_flow.py` 已调整：

- 某一步失败时不再直接抛异常退出。
- 会写出 `golden_flow_report.json` 和 `golden_flow_report.md`。
- 报告中包含失败步骤、return code、stdout tail、stderr tail。
- 返回码仍为非 0，便于 CI 判断失败。

这样真实 golden flow 即使被 API、网络、编译器等外部因素阻塞，也能留下验收资产。

### 1.5 生成目录策略已更新

`.gitignore` 已补充：

```gitignore
.pytest_cache/
.ruff_cache/
.tmp/
.spec/
requirements/.spec/
simple_login/
```

目的：

- 避免 proof scripts、golden runner、pytest basetemp 和真实流程生成物污染主线。
- 保留 `plan_doc/`、`doc3.0/`、`docs/` 下的总结和 demo 文档作为可提交资产。

## 2. 当前 Phase 1 状态

| 项目 | 状态 | 说明 |
| --- | --- | --- |
| dry-run golden flow | 完成 | 可生成计划报告 |
| proof scripts | 完成 | parallel/vector smoke 均通过 |
| targeted tests | 完成 | 49 passed |
| 生成目录忽略策略 | 完成 | `.gitignore` 已更新 |
| 真实 non-dry-run golden flow | 阻塞 | Anthropic 账号/订阅返回 403 |
| 失败报告留痕 | 完成 | golden runner 已增强 |

## 3. 后续解锁真实 golden flow 的选择

### 方案 A：使用可用 Anthropic 订阅

适合验证真实 AI 生成能力。

需要：

- 确认 `ANTHROPIC_API_KEY` 或 `ANTHROPIC_AUTH_TOKEN` 对应账号有可用订阅。
- 重新执行：

```bash
python scripts/run_golden_openspec_flow.py --requirements requirements/simple_login.md --timeout 1800
```

### 方案 B：增加离线 fake provider golden mode

适合 CI 和面试 demo，可避免外部 API 不稳定。

建议：

- 在 `run_ai_flow.py` 或 LLM client 层增加 fake provider 配置。
- 使用固定 fixtures 生成 Phase 4 代码。
- 让 golden flow 在无网络环境也能完整执行 propose/apply/validate/archive。

### 方案 C：拆分真实 AI golden 与离线 acceptance golden

推荐长期方案：

- 离线 acceptance golden：CI 必跑，保证 workflow、archive、traceability 不退化。
- 真实 AI golden：人工或 nightly 跑，验证 provider、prompt 和真实生成质量。

## 4. 推荐验收入口

短期推荐将以下命令作为本地最小验收：

```bash
python scripts/run_golden_openspec_flow.py --dry-run
python scripts/benchmark_parallel_executor.py --json
python scripts/evaluate_vector_retrieval.py --json
New-Item -ItemType Directory -Force .tmp | Out-Null
python -m pytest -p no:cacheprovider --basetemp .tmp\pytest tests/openspec/test_sandbox_merge.py tests/golden/test_golden_flow_runner.py tests/openspec/test_phase4_multi_agent.py tests/openspec/test_phase9_quality_gate.py tests/openspec/test_phase11_final_report.py tests/test_eventbus_integration.py tests/e2e/test_archive_e2e.py tests/openspec/test_archive_lifecycle.py
```

Phase 1 可以视为“离线验收资产闭环完成，真实 AI golden flow 等待 provider 账号/订阅解锁”。
