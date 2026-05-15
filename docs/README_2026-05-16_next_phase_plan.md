# DevPalAgent OpenSpec 下一阶段执行计划

日期：2026-05-16

## 1. 背景

当前 `simple_login` golden case 第一版已经完成并通过，系统已经具备一条可重复验证的 OpenSpec 11 阶段完整链路。

目前已经完成的基础能力包括：

- `run_ai_flow.py` 使用 `EnhancedOpenSpecScheduler`。
- `tests/golden/test_simple_login_golden.py` 可以验证完整链路。
- 默认轻量测试覆盖 Prompt / 模板 / Phase 10 / checkpoint 等关键回归点。
- Golden summary 可以打印到控制台，并写入 `final_report.md`。
- Phase 4 / Phase 10 已加入最小成功策略，避免虚假成功。
- 调度器头部输出已修复为可读配置项。

下一阶段目标不是继续增加更多 Phase，而是把当前“能跑通的流水线”升级为：

```text
入口一致、状态清晰、产物可追踪、需求可验收的 Spec-First 自动化开发系统。
```

## 2. 当前已完成能力

| 能力 | 状态 | 说明 |
|---|---|---|
| Golden E2E | 已完成 | `simple_login` 可验证完整 11 阶段链路 |
| 轻量回归测试 | 已完成 | 默认不调用 LLM，快速验证关键契约 |
| Prompt 契约测试 | 已完成 | Phase 4 `.format()`、测试宏、STL include 规则 |
| 测试模板契约 | 已完成 | `test_base.h` 与 Phase 4 生成规则一致 |
| Phase 10 失败策略 | 已完成 | 无测试、无编译器、0/0 不再算成功 |
| 编译错误摘要 | 已完成 | Phase 10 编译失败时主日志能看到关键错误 |
| Golden Summary | 已完成 | 控制台 + `final_report.md` 可观测输出 |
| 生成策略保护 | 已完成 | `run_ai_flow.py` 默认复用已有代码，其他入口默认重生成 |
| 调度器可观测性 | 已完成 | Timeout / Retry / Checkpoint / Force regenerate 状态可见 |
| 最小成功策略 | 已完成 | Phase 4 / Phase 10 过宽成功会被拦截 |

## 3. 下一阶段总路线

建议分 3 个迭代推进：

```text
阶段 A：统一 OpenSpec 主入口
阶段 B：Spec-First 最小闭环
阶段 C：可靠断点续传
```

推荐顺序：

1. 先统一入口。
2. 再接入 Requirement Model + ArtifactGraph + Acceptance Matrix。
3. 最后做完整 context checkpoint / resume。

原因：

- 入口不统一时，后续能力会重复接入多条链路。
- Requirement Model 和 ArtifactGraph 是 checkpoint、DeltaSpec、selective test 的基础。
- 断点续传最终应该保存结构化 context，而不是只保存 phase 编号。

## 4. 阶段 A：统一 OpenSpec 主入口

### 4.1 目标

消除当前 OpenSpec 执行路径分叉，建立唯一推荐入口。

当前存在多个入口或流程实现：

- `run_ai_flow.py`
- `devpal/core/agent_engine.py`
- `devpal/core/openspec_workflow.py`
- `devpal/core/openspec_phases/scheduler.py`
- `devpal/core/openspec_phases/enhanced_scheduler.py`

风险：

- 不同入口可能有不同默认行为。
- 修 bug 容易只修一个入口。
- 后续接入 Requirement Model / ArtifactGraph 时需要重复接入。
- Golden test 只能覆盖 `run_ai_flow.py`，无法保证交互入口一致。

### 4.2 推荐方案

新增或整理统一 facade：

```text
devpal/core/openspec_executor.py
```

建议接口：

```python
class OpenSpecWorkflowExecutor:
    def __init__(self, tool_registry):
        ...

    def run(
        self,
        requirements_file: str,
        *,
        abort_on_critical_failure: bool = True,
        enable_timeout: bool = True,
        enable_retry: bool = True,
        enable_checkpoint: bool = True,
        enable_progress: bool = True,
        resume: bool = False,
        force_regenerate_code: bool = True,
    ) -> dict:
        ...
```

内部统一委托：

```python
EnhancedOpenSpecScheduler(...).run_all_phases(resume=resume)
```

### 4.3 关键文件

| 文件 | 需要做什么 |
|---|---|
| `devpal/core/openspec_executor.py` | 新增统一执行 facade |
| `run_ai_flow.py` | 改为调用 executor |
| `devpal/core/agent_engine.py` | 交互入口改为调用 executor |
| `devpal/core/openspec_workflow.py` | 标记 legacy 或委托 executor |
| `devpal/core/openspec_phases/enhanced_scheduler.py` | 保留为内部调度器 |
| `tests/openspec/` | 增加入口策略测试 |

### 4.4 保留的特殊策略

`run_ai_flow.py` 是 golden / 手动验证入口，为了节省 token：

```text
默认 force_regenerate_code=False
```

其他入口默认：

```text
force_regenerate_code=True
```

原因：

- `run_ai_flow.py` 常用于重复验证已生成项目，默认复用代码更省 token。
- 交互模式 / 其他入口应默认重新生成，避免旧代码掩盖问题。

### 4.5 验收标准

- `run_ai_flow.py` 和 `agent_engine.py` 都调用 `OpenSpecWorkflowExecutor`。
- `EnhancedOpenSpecScheduler` 不再到处被直接 new。
- 旧 `openspec_workflow.py` 不再作为推荐主流程。
- 轻量测试通过。
- Golden test 继续通过。
- 入口策略测试通过：
  - `run_ai_flow.py` 默认不强制重生成。
  - executor 默认强制重生成。

### 4.6 推荐测试

新增：

```text
tests/openspec/test_openspec_executor.py
```

覆盖：

- executor 默认 `force_regenerate_code=True`。
- executor 可以显式传 `force_regenerate_code=False`。
- `run_ai_flow.py` 调用 executor 时默认传 False。

## 5. 阶段 B：Spec-First 最小闭环

### 5.1 目标

把当前链路从：

```text
Markdown 需求 -> LLM 设计 -> LLM 写代码 -> 编译测试
```

升级为：

```text
结构化 Requirement -> 技术设计 -> 代码 -> 测试 -> 验收矩阵
```

这是对标开源 OpenSpec / spec-driven 工具的核心能力。

### 5.2 最小实现范围

第一版只做最小闭环，不引入复杂 DeltaSpec。

需要产出：

```text
cpp_simple_login/.spec/requirements.json
cpp_simple_login/.spec/artifact_graph.json
final_report.md 中的 Acceptance Matrix
```

### 5.3 Requirement Model

Phase 1 从 Markdown 中解析：

```json
{
  "requirements": [
    {
      "id": "REQ-001",
      "title": "用户登录",
      "description": "...",
      "acceptance_criteria": ["...", "..."]
    }
  ]
}
```

如果需求文档没有显式 `REQ-001`，则自动生成：

```text
REQ-001, REQ-002, ...
```

### 5.4 ArtifactGraph 最小版

第一版可以先用 JSON，不必完整接入复杂图引擎。

示例：

```json
{
  "nodes": [
    {"id": "REQ-001", "type": "requirement", "label": "用户登录"},
    {"id": "src/login_service.cpp", "type": "source"},
    {"id": "tests/test_login_service.cpp", "type": "test"}
  ],
  "edges": [
    {"from": "REQ-001", "to": "src/login_service.cpp", "relation": "implemented_by"},
    {"from": "REQ-001", "to": "tests/test_login_service.cpp", "relation": "verified_by"}
  ]
}
```

### 5.5 Phase 11 Acceptance Matrix

`final_report.md` 中新增：

```markdown
## Acceptance Matrix

| Requirement | Implementation | Tests | Status |
|-------------|----------------|-------|--------|
| REQ-001 用户登录 | src/login_service.cpp | tests/test_login_service.cpp | Passed |
```

### 5.6 关键文件

| 文件 | 需要做什么 |
|---|---|
| `devpal/core/schema/requirements.py` | 复用或扩展 Requirement Model |
| `devpal/core/schema/artifact_graph.py` | 复用或做最小 JSON 输出 |
| `devpal/core/openspec_phases/base.py` | context 增加 structured requirements / artifact graph 字段 |
| `devpal/core/openspec_phases/phase1_parse_requirements.py` | 解析结构化需求 |
| `devpal/core/openspec_phases/phase4_generate_code.py` | 记录文件与需求关联 |
| `devpal/core/openspec_phases/phase10_run_tests.py` | 记录测试结果与测试文件关联 |
| `devpal/core/openspec_phases/phase11_final_report.py` | 输出 Acceptance Matrix |
| `tests/golden/test_simple_login_golden.py` | 增加结构化产物断言 |

### 5.7 验收标准

Golden test 增加断言：

- `cpp_simple_login/.spec/requirements.json` 存在。
- `cpp_simple_login/.spec/artifact_graph.json` 存在。
- `final_report.md` 包含 `## Acceptance Matrix`。
- 至少一个 requirement 状态是 `Passed`。
- 至少一个 requirement 关联到测试文件。

## 6. 阶段 C：可靠断点续传

### 6.1 目标

把当前半成品 checkpoint 变成真正可用的断点续传。

### 6.2 当前问题

目前 checkpoint 只保存：

```text
last_phase
last_success
completed_phases
timestamp
```

没有保存：

```text
requirements_content
tech_design_content
project_name
project_dir
generated_files
test_docs
phase_results
requirements model
artifact graph
```

这会导致恢复时 context 丢失，例如：

```text
[RESUME] Phase 4
tech_design_content is empty
```

### 6.3 推荐方案

checkpoint 保存完整 context 摘要：

```json
{
  "last_phase": 4,
  "last_success": true,
  "completed_phases": [1, 2, 3, 4],
  "context": {
    "requirements_file": "requirements/simple_login.md",
    "project_name": "cpp_simple_login",
    "project_dir": "cpp_simple_login",
    "requirements_content": "...",
    "tech_design_content": "...",
    "generated_files": [],
    "test_docs": [],
    "test_passed": 0,
    "test_total": 0,
    "requirements": [],
    "artifact_graph": {}
  }
}
```

增加：

```python
CheckpointManager.restore_context(context)
```

### 6.4 checkpoint 位置

建议从仓库根目录：

```text
.spec/checkpoint.json
```

迁移到项目目录：

```text
cpp_simple_login/.spec/checkpoint.json
```

或未来标准 run 目录：

```text
.spec/runs/<run_id>/checkpoint.json
```

当前建议先用项目目录，避免不同项目互相污染。

### 6.5 显式 resume 参数

默认继续 fresh run：

```bash
python run_ai_flow.py -r requirements/simple_login.md
```

显式恢复：

```bash
python run_ai_flow.py -r requirements/simple_login.md --resume
```

### 6.6 验收标准

- 默认运行不读取旧 checkpoint。
- `--resume` 才启用恢复。
- 恢复到 Phase 4 时 `tech_design_content` 不为空。
- 成功完成后清理 checkpoint。
- checkpoint 不跨项目污染。
- golden test 不受旧 checkpoint 影响。

## 7. 不建议现在做的事项

| 暂不做 | 原因 |
|---|---|
| DeltaSpec 增量修改 | 依赖 Requirement Model 和 ArtifactGraph |
| dry-run / diff 模式 | 需要先统一入口和产物追踪 |
| rollback | 依赖 snapshot 和 delta |
| Web UI / dashboard | 底层结构化数据未稳定 |
| 多语言产品化 | 当前 C++ 链路仍在收敛 |
| 更多复杂 golden case | 先把 simple_login 结构化验收闭环做好 |

## 8. 推荐执行顺序

### Step 1：统一入口

```text
OpenSpecWorkflowExecutor
run_ai_flow.py -> executor
agent_engine.py -> executor
openspec_workflow.py -> legacy / delegate
```

### Step 2：结构化需求

```text
Phase 1 -> requirements.json
context.structured_requirements
```

### Step 3：ArtifactGraph 最小版

```text
requirement -> source -> test -> result
.spec/artifact_graph.json
```

### Step 4：Acceptance Matrix

```text
Phase 11 -> final_report.md
Golden test -> assert Acceptance Matrix
```

### Step 5：可靠 checkpoint

```text
checkpoint saves context
--resume restores context
```

## 9. 每步必须保留的验证

轻量测试：

```bash
pytest tests/openspec tests/golden/test_simple_login_golden.py
```

语法检查：

```bash
python -m py_compile run_ai_flow.py devpal/core/openspec_phases/enhanced_scheduler.py devpal/core/openspec_phases/phase4_generate_code.py devpal/core/openspec_phases/phase10_run_tests.py
```

完整 golden：

```bash
pytest tests/golden/test_simple_login_golden.py --run-golden -s
```

强制重新生成代码的 golden：

```bash
DEVPAL_GOLDEN_FORCE_REGENERATE=1 pytest tests/golden/test_simple_login_golden.py --run-golden -s
```

## 10. 一句话总结

完成 golden test 后，下一阶段最重要的是：

```text
先统一入口，再接入 Requirement Model + ArtifactGraph + Acceptance Matrix，最后做可靠断点续传。
```

这样 DevPalAgent 才能从“需求文档驱动的代码生成流水线”升级为真正的 “Spec-First 自动化开发系统”。
