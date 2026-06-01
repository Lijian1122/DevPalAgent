# Phase 4/5 并行实现原理分析

日期：2026-05-29

## 结论摘要

当前 OpenSpec 的 Phase 4/5 并行不是“阶段级并行”，而是“阶段内部的文件级任务并行”。

也就是说，调度器仍然按顺序执行：

```text
Phase 4 Generate Code -> Phase 5 Generate Test Documentation
```

不会同时启动 Phase 4 和 Phase 5。真正的并行发生在各自 Phase 内部：

- Phase 4：尝试把代码生成拆成多个单文件 LLM 任务。
- Phase 5：把每个测试文件的文档生成拆成独立任务。

通用并行能力由 `devpal/core/openspec_phases/parallel_executor.py` 提供。

## 1. 调度层：Phase 4/5 仍然串行

增强调度器在 `enhanced_scheduler.py` 中创建 11 个 Phase，并按列表顺序循环执行。

关键顺序如下：

```python
phases = [
    Phase1ParseRequirements(...),
    Phase2CreateStructure(...),
    Phase3TechnicalDesign(...),
    Phase4GenerateCode(...),
    Phase5GenerateTests(...),
    Phase6CMakeConfig(...),
    ...
]
```

之后通过 `for i in range(start_phase, len(phases) + 1)` 逐个执行。

因此，Phase 4 和 Phase 5 之间不存在并发关系。Phase 5 必须等待 Phase 4 完成，因为 Phase 5 依赖 Phase 4 生成的 `tests/` 文件。

## 2. 通用并行执行器

核心文件：`devpal/core/openspec_phases/parallel_executor.py`

核心数据结构：

- `ParallelTask`：一个可并行执行的任务。
- `ParallelTaskResult`：一个任务的执行结果。
- `PhaseParallelExecutor`：统一的有界并行执行器。

`ParallelTask` 包含：

```python
task_id: str
phase_number: int
task_type: str
input_payload: Dict[str, Any]
dependencies: List[str]
retry_count: int
metadata: Dict[str, Any]
```

执行器的主要逻辑：

1. 没有任务则直接返回。
2. 如果 `max_concurrency == 1` 或只有一个任务，则串行执行。
3. 如果任务有依赖，则按依赖分层执行。
4. 如果任务无依赖，则用 `ThreadPoolExecutor` 并行执行。

无依赖任务的并行实现：

```python
with ThreadPoolExecutor(max_workers=min(self.max_concurrency, len(tasks))) as executor:
    futures = {executor.submit(self._run_one, task, handler): task for task in tasks}
    for future in as_completed(futures):
        task = futures[future]
        results_by_id[task.task_id] = future.result()
```

每个任务都会通过 `_run_one()` 包装执行，统一记录：

- 线程 ID
- 线程名
- 执行耗时
- retry 次数
- 错误信息
- metadata

所以当前并行模型可以概括为：

```text
Phase 生成任务列表
    -> PhaseParallelExecutor 控制并发数
        -> ThreadPoolExecutor 提交多个任务
            -> 每个任务独立执行 handler
        -> 聚合 ParallelTaskResult
    -> PhaseResult 写入 parallel_summary
```

## 3. Phase 4：代码生成的并行实现

核心文件：`devpal/core/openspec_phases/phase4_generate_code.py`

Phase 4 的目标是生成基础模板和业务代码。它的并行只作用在“业务代码文件生成”这一部分。

### 3.1 Phase 4 主流程

Phase 4 的主流程大致是：

1. 生成基础模板文件，例如 CMake、README、测试基础设施。
2. 检查是否可以跳过 AI 生成。
3. 构建文件生成计划 `file_plan`。
4. 构建 system prompt、user message 和 cached context。
5. 判断是否允许并行。
6. 如果允许，进入 `_try_generate_files_parallel()`。
7. 如果并行失败或不安全，则回退到原来的串行 LLM tool loop。

### 3.2 文件计划来源

文件计划由 `devpal/core/openspec_phases/phase4_file_plan.py` 生成。

C++ 项目默认计划通常包含：

```text
include/<namespace>_service.h
src/<namespace>_service.cpp
tests/test_<namespace>_service.cpp
src/main.cpp，可选
```

Python 项目默认计划通常包含：

```text
src/<module>.py
tests/test_<module>.py
```

Shell 项目默认计划通常包含：

```text
scripts/<script>.sh
tests/test_<script>.sh
```

### 3.3 并行开关与安全判断

Phase 4 通过以下配置判断是否尝试并行：

```python
parallel_enabled = bool(getattr(self.context, "phase4_parallel_enabled", True))
parallel_safe = self._is_parallel_file_plan_safe(file_plan)
```

当前安全判断非常保守：

```python
def _is_parallel_file_plan_safe(self, file_plan) -> bool:
    return bool(file_plan) and not any(item.dependencies for item in file_plan)
```

这意味着：只要任意文件任务存在依赖，Phase 4 就不会进入并行生成，而是回退到串行 tool loop。

### 3.4 单文件任务模型

Phase 4 并行时，会把每个 `file_plan` item 包装成一个 `ParallelTask`：

```python
ParallelTask(
    task_id=f"phase4:{item.path}",
    phase_number=4,
    task_type="code_file",
    input_payload={
        "plan_item": item,
        "project_dir": project_dir,
        "system_prompt": system_prompt,
        "base_user_message": base_user_message,
        "cached_context": cached_context,
    },
    dependencies=[f"phase4:{dep}" for dep in item.dependencies],
)
```

每个任务只允许生成一个文件。`_generate_single_file_task()` 内部的 tool handler 会校验写入路径：

```python
if rel.replace("\\", "/") != item.path:
    return "[error] this task may only write {}".format(item.path)
```

因此 Phase 4 的并行不是“一个 LLM 一次生成全部文件”，而是：

```text
一个目标文件 = 一个独立 LLM tool loop = 一个并行任务
```

### 3.5 独立 LLM client

每个并行任务都会创建自己的 LLM client：

```python
task_client = self._create_parallel_llm_client()
```

这样做的好处是：

- 避免多个线程共享同一个 client 状态。
- 避免 usage 统计互相污染。
- 让每个单文件生成任务彼此隔离。

### 3.6 快照与回滚

Phase 4 在并行生成前会对目标文件做快照：

```python
snapshots = self._snapshot_parallel_targets(file_plan, project_dir)
```

如果并行失败，会恢复快照：

```python
self._restore_parallel_targets(snapshots)
```

这解决了一个关键问题：并行生成可能出现部分文件成功、部分文件失败。如果不回滚，项目会处于半更新状态。

### 3.7 Phase 4 当前限制

虽然 Phase 4 已经实现了并行框架，但当前默认场景下经常不会真正并行。

原因是默认 file plan 通常带有依赖：

- C++：cpp 依赖 header，test/main 依赖 cpp。
- Python：test 依赖 src module。
- Shell：test 依赖 script。

而 Phase 4 当前的 `_is_parallel_file_plan_safe()` 要求所有任务都没有依赖。

所以当前实际效果是：

```text
file plan 无依赖 -> 进入 Phase 4 并行
file plan 有依赖 -> 禁用 Phase 4 并行，回退串行 tool loop
```

值得注意的是，`PhaseParallelExecutor` 本身已经支持依赖分层执行，但 Phase 4 当前没有利用这个能力，而是在进入 executor 前就把带依赖的计划拦掉了。

## 4. Phase 5：测试文档生成的并行实现

核心文件：`devpal/core/openspec_phases/phase5_generate_tests.py`

Phase 5 的并行更直接，也更容易真正生效。

### 4.1 Phase 5 主流程

Phase 5 的流程是：

1. 扫描 `tests/` 目录。
2. 根据语言查找测试文件。
3. 为每个测试文件构建一个测试文档任务。
4. 使用 `PhaseParallelExecutor` 并行执行。
5. 聚合结果，写入 `parallel_summary`。

测试文件匹配规则：

```text
C++    -> tests/test_*.cpp
Python -> tests/test_*.py
Shell  -> tests/test_*.sh
```

### 4.2 任务拆分方式

每个测试文件会生成一个 `ParallelTask`：

```python
ParallelTask(
    task_id=f"phase5:{test_file.name}",
    phase_number=5,
    task_type="test_doc",
    input_payload={
        "test_file": test_file,
        "source_file": source_file,
        "doc_file": doc_file,
    },
)
```

输出文档路径类似：

```text
docs/test_<test_file_stem>_doc.md
```

### 4.3 默认并发数

Phase 5 默认并发数是 3：

```python
max_concurrency = getattr(self.context, "phase5_max_concurrency", 3)
```

然后创建执行器：

```python
executor = PhaseParallelExecutor(
    max_concurrency=max_concurrency,
    retry_limit=1,
    serial_fallback=True,
    log=self.log,
)
```

### 4.4 每个任务的实际执行

每个任务调用 `test_doc_generator` 工具：

```python
result = self.tool_registry.execute_tool('test_doc_generator', {
    'file_path': str(source_file) if source_file else str(test_file),
    'output_doc': str(doc_file),
    'test_file': str(test_file)
})
```

因为不同测试文件的文档生成互相独立，所以 Phase 5 的任务没有 dependencies，可以直接并行。

### 4.5 Phase 5 的失败策略

Phase 5 对失败比较宽松：

- 某个测试文档生成失败，会记录到 errors。
- 已成功生成的文档仍然保留。
- PhaseResult 仍可能返回 ok，只是 message 中说明生成数量不足。

这和 Phase 4 不同。Phase 4 是核心代码生成阶段，任一并行任务失败会触发回滚并返回失败。

## 5. Phase 4 和 Phase 5 对比

| 维度 | Phase 4 | Phase 5 |
|---|---|---|
| 并行粒度 | 单个目标代码文件 | 单个测试文件的文档 |
| 主要任务类型 | `code_file` | `test_doc` |
| 默认并发数 | `phase4_max_concurrency`，默认 2 | `phase5_max_concurrency`，默认 3 |
| 是否直接调用 LLM | 是 | 通过 `test_doc_generator` 工具 |
| 是否创建独立 client | 是，每个任务独立 client | 否，由工具内部决定 |
| 是否支持回滚 | 支持快照回滚 | 不支持，也通常不需要 |
| 失败策略 | 任一失败则并行失败并回滚 | 部分失败可继续返回 ok |
| 当前是否容易真并行 | 不一定，依赖计划会禁用 | 是，多个测试文件即可并行 |

## 6. 当前实现的核心价值

当前并行实现的价值主要有三点：

1. 有界并发

通过 `max_concurrency` 限制同时运行的任务数量，避免 LLM/API/tool 调用过载。

2. 文件级可观测

每个并行任务都有独立的：

- task_id
- duration_ms
- retry_attempts
- thread_id
- thread_name
- error
- metadata

这些信息会聚合到 `parallel_summary`，方便后续诊断性能瓶颈和失败原因。

3. 为依赖分层并行打好了基础

`PhaseParallelExecutor` 已经支持 dependencies。理论上可以做到：

```text
Stage 1: headers / core source
Stage 2: implementations depending on headers
Stage 3: tests / entrypoint depending on implementation
```

只是 Phase 4 当前的安全判断没有启用这条路径。

## 7. 改进建议

### 建议 1：Phase 4 启用依赖分层并行

当前 `PhaseParallelExecutor` 已支持 `_execute_by_dependency_stage()`，Phase 4 可以取消过于保守的判断：

```python
not any(item.dependencies for item in file_plan)
```

改成允许带依赖计划进入 executor，由 executor 按依赖分层执行。

预期效果：

- 有依赖的任务不会乱序执行。
- 同一依赖层内的多个任务可以并行。
- 比完全串行更快，也比无视依赖更安全。

### 建议 2：扩展 file plan，让同层任务更多

当前 C++ 默认 plan 通常只有一个 service 链路，依赖链偏线性，能并行的空间有限。

如果 Phase 3 或 Phase 4 planner 能按模块拆分多个 service，例如：

```text
include/user_service.h
include/auth_service.h
include/token_service.h
src/user_service.cpp
src/auth_service.cpp
src/token_service.cpp
tests/test_user_service.cpp
tests/test_auth_service.cpp
tests/test_token_service.cpp
```

则同一层可以并行生成多个文件，性能收益更明显。

### 建议 3：Phase 4 保留回滚策略

Phase 4 写的是核心源码，失败影响较大。当前快照恢复机制是必要的，不建议移除。

可以进一步增强为：

- 记录哪些文件被恢复。
- 在 `parallel_summary` 中标记 rollback。
- 将失败任务和恢复任务写入最终报告。

## 8. 最终判断

当前 Phase 4/5 的并行架构已经具备基础能力：

```text
任务拆分 -> 有界线程池 -> 独立任务执行 -> 结果聚合 -> PhaseResult 记录
```

但成熟度不同：

- Phase 5 已经是比较完整的实用并行。
- Phase 4 是“框架已完成，但默认策略偏保守”，很多真实项目会因为 file dependencies 回退到串行。

下一步最值得做的是：让 Phase 4 直接使用 `PhaseParallelExecutor` 已有的依赖分层执行能力，而不是遇到依赖就禁用并行。
