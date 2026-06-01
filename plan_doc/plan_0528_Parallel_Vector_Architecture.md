# 并行执行与向量检索架构设计

**日期**：2026-05-28  
**目标**：设计 Phase 4/5 并行执行与向量检索能力，提升单 Agent 主流程性能、上下文召回质量和 Self-Healing 经验复用能力  
**预期工期**：5 天 MVP（并行执行 1-2 天，向量检索 2-3 天）  
**优先级**：P0  
**关联路线图**：`plan_doc/plan_0528_priority_roadmap.md`

---

## 1. 背景与目标

### 1.1 当前状态

**已完成能力**：
- ✅ OpenSpec 11 阶段长流程编排
- ✅ ToolRegistry 原子工具层
- ✅ Skills 任务编排层
- ✅ Prompt Caching 成本优化（80.5% hit rate，-60.7% cost）
- ✅ LLM-as-a-Judge 质量评审（Phase 9.5）
- ✅ Self-Healing RCA 根因分析
- ✅ EventBus 全链路事件追踪
- ✅ LanguagePlugin 多语言扩展架构
- ✅ Anthropic / OpenAI / Fallback 多 Provider 支持

**已修复问题**：
- ✅ Phase 4 tool loop 文件跳过循环问题已修复
- ✅ EventBus `unknown_project` 项目名称问题已修复

### 1.2 当前缺口

**缺口 1：Phase 4/5 仍以串行为主**
- Phase 4 通过单一 LLM tool loop 生成业务代码和测试文件。
- Phase 5 对测试文件逐个执行 `test_doc_generator`。
- 文件级任务之间存在大量独立工作，但当前没有利用并行能力。

**缺口 2：缺少语义检索能力**
- 当前代码检索主要依赖文件扫描、字符串匹配和关键词重叠。
- 缺少对 requirements、design、spec、code、test、error memory 的统一语义索引。
- Phase 4/9/9.5 和 Self-Healing 无法稳定召回最相关上下文。

**缺口 3：性能优化缺少可观测闭环**
- EventBus 已具备 workflow/phase 级事件能力。
- 但并行任务需要更细粒度的 file task 事件和 final_report 统计。

### 1.3 设计目标

**目标 1：并行执行性能提升**
- Phase 4/5 支持文件级并行任务。
- 支持 `max_concurrency` 控制并发度。
- 支持单任务失败重试，不拖垮整个 phase。
- 保留串行 fallback。
- 目标：Phase 4/5 相比串行耗时下降 30%+。

**目标 2：向量检索与上下文注入**
- 建立 source/test/design/spec/change/error artifacts 的语义索引。
- 支持自然语言检索相关代码、测试、规范和错误历史。
- Phase 4/9/9.5 可注入 top-k 相关上下文。
- Self-Healing 可召回相似错误和历史修复策略。

**目标 3：保持单 Agent 架构优势**
- 不引入完整多 Agent / AgentPool 复杂度。
- 不破坏现有 OpenSpec 11 阶段主流程。
- 保留 Prompt Caching、统一上下文和可调试性优势。

### 1.4 架构原则

```text
单 Agent 主流程不变
  ↓
Phase 内部引入可控并行
  ↓
Vector Store 提供语义上下文
  ↓
EventBus + final_report 提供可观测闭环
```

**原则**：
1. **先局部并行，不做全局分布式重构**：只在 Phase 4/5 内部拆 file task。
2. **先 ChromaDB MVP，不引入重型向量平台**：先验证价值，再考虑 Qdrant/Weaviate。
3. **所有优化必须可回退**：并行失败时可以串行执行。
4. **所有优化必须可度量**：EventBus 和 final_report 记录性能、失败、重试和召回效果。
5. **不把规划能力写成已完成能力**：本文档是 P0 技术设计和实施计划。

### 1.5 面试价值

**展示点**：
1. **性能工程能力**：不是盲目堆 Agent，而是定位 Phase 4/5 串行瓶颈并做可控并行。
2. **上下文工程能力**：用向量检索解决 LLM 长上下文选择和历史经验复用问题。
3. **架构权衡能力**：评估过多 Agent，但选择复杂度更低、收益更确定的并行工具调用。
4. **可观测性意识**：通过 EventBus 和 final_report 让性能优化可验证、可复盘。

---

## 2. 当前实现分析

### 2.1 Phase 4 代码生成现状

**关键文件**：`devpal/core/openspec_phases/phase4_generate_code.py`

**当前流程**：
1. `Phase4GenerateCode.execute()` 应用基础模板。
2. 初始化 LLM client。
3. 通过 `client.generate_with_tool_loop(...)` 发起一次主生成会话。
4. LLM 通过 `write_file` tool call 写入业务代码、测试文件和入口文件。
5. `tool_handler()` 每次处理一个文件写入。
6. 汇总 `ai_files`，更新 `context.generated_files` / `context.ai_generated_files`。
7. 更新 ArtifactGraph 并执行 CompileDB 索引。

**当前瓶颈**：
- 所有业务文件生成绑定在一个串行 LLM tool loop 中。
- 文件之间即使相互独立，也不能并发生成。
- 文件级失败、重试和耗时统计不够清晰。

**需要保留的能力**：
- 增量生成逻辑
- selective regeneration
- `write_file` 工具协议
- ArtifactGraph 更新
- CompileDB 索引
- EventBus phase 级事件

### 2.2 Phase 5 测试文档生成现状

**关键文件**：`devpal/core/openspec_phases/phase5_generate_tests.py`

**当前流程**：
1. 扫描 `tests/` 目录。
2. 按语言查找 `test_*.cpp` / `test_*.py` / `test_*.sh`。
3. 对每个测试文件查找对应 source file。
4. 串行调用 `tool_registry.execute_tool('test_doc_generator', ...)`。
5. 收集 `test_docs_generated` 和 `errors`。
6. 写入 `context.test_docs`。

**当前瓶颈**：
- 每个 test doc 生成任务相互独立，但当前串行执行。
- Phase 5 是最适合作为并行 MVP 的阶段。
- 并行后只需要聚合结果，不需要改动 OpenSpec 主流程。

### 2.3 现有并发能力

**可复用思路**：

1. `devpal/core/schema/workflow.py`
   - `WorkflowEngine._execute_parallel()` 已具备 dependency-aware 并行 step 执行思想。
   - 可借鉴 max parallel steps、依赖解析、结果汇总模式。

2. `devpal/core/schema/validation_engine.py`
   - `ValidationPipeline._run_parallel()` 使用 `ThreadPoolExecutor` 执行独立 validation stage。
   - 可借鉴 stage-level 并发、异常收集和结果聚合。

3. `devpal/workflows/code_generation_workflow.yaml`
   - 已存在 `parallel` / `max_parallel_steps` 配置概念。
   - 新设计应尽量复用配置语义，避免再造一套命名。

**当前缺口**：
- 没有专门面向 Phase 内部 file task 的 executor。
- 没有统一的 LLM 并发控制、重试、限流和串行 fallback。
- EventBus 尚未稳定记录 file task 级并行事件。

### 2.4 当前检索能力

**关键文件**：
- `devpal/tools/code_search.py`
- `devpal/memory/long_term.py`
- `devpal/memory/short_term.py`

**当前能力**：
- 基于文件扫描的 code search。
- 基于关键词重叠的 memory retrieval。
- 基于 recency / importance 的简单记忆排序。

**当前缺口**：
- 无 embedding provider。
- 无 vector store adapter。
- 无统一 chunking/indexing pipeline。
- 无 hybrid retrieval。
- 无 Phase 4/9/9.5 prompt top-k context injection。
- 无 Self-Healing 相似错误向量召回。

---

## 3. 并行执行架构设计

### 3.1 设计理念

并行执行的目标不是把 DevPalAgent 改成完整多 Agent，而是在 OpenSpec 11 阶段主流程不变的前提下，让 Phase 内部的独立文件任务并发执行。

```text
OpenSpec Scheduler
  ↓
Phase 4 / Phase 5
  ↓
PhaseParallelExecutor
  ├─ ParallelTask(file A)
  ├─ ParallelTask(file B)
  ├─ ParallelTask(file C)
  └─ ParallelTask(file D)
  ↓
Result Aggregator
  ↓
OpenSpecContext / ArtifactGraph / EventBus / final_report
```

**核心收益**：
- 提升长流程中最耗时阶段的吞吐。
- 避免完整多 Agent 带来的调度和状态同步复杂度。
- 保持单 Agent 的 Prompt Caching 和统一上下文优势。

### 3.2 核心抽象

#### ParallelTask

**职责**：描述一个可以独立执行的 phase 内部任务。

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

@dataclass
class ParallelTask:
    task_id: str
    phase_number: int
    task_type: str              # code_file / test_doc / index_chunk
    input_payload: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
```

**示例**：
```python
ParallelTask(
    task_id="phase5:test_login_service.cpp",
    phase_number=5,
    task_type="test_doc",
    input_payload={
        "test_file": "tests/test_login_service.cpp",
        "source_file": "src/login_service.cpp",
        "output_doc": "docs/test_test_login_service_doc.md",
    },
)
```

#### ParallelTaskResult

**职责**：封装单个并行任务的执行结果。

```python
@dataclass
class ParallelTaskResult:
    task_id: str
    success: bool
    artifact_path: Optional[Path] = None
    duration_ms: int = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

#### PhaseParallelExecutor

**职责**：统一处理 phase 内部任务并发、重试、聚合和回退。

```python
class PhaseParallelExecutor:
    def __init__(self, max_concurrency: int = 3, retry_limit: int = 1, serial_fallback: bool = True):
        self.max_concurrency = max_concurrency
        self.retry_limit = retry_limit
        self.serial_fallback = serial_fallback

    def execute(self, tasks: List[ParallelTask]) -> List[ParallelTaskResult]:
        """Execute independent phase tasks with bounded concurrency."""
        pass

    def aggregate(self, results: List[ParallelTaskResult]) -> Dict[str, Any]:
        """Build phase-level summary for PhaseResult/final_report."""
        pass
```

**设计约束**：
- 默认 `max_concurrency=3`，避免 API 并发过高。
- 每个 task 独立计时、独立失败、独立 retry。
- 输出结果排序必须稳定，避免 final_report 和 context 状态不可预测。

### 3.3 Phase 5 并行 MVP

Phase 5 是最适合作为 MVP 的阶段。

**原因**：
1. 每个测试文档生成任务天然独立。
2. 不涉及 LLM 多轮 tool loop 拆分。
3. 只需要并发执行 `test_doc_generator` 并聚合结果。
4. 容易对比串行和并行耗时。

**改造前**：
```python
for test_file in test_files:
    result = self.tool_registry.execute_tool('test_doc_generator', {...})
```

**改造后**：
```text
test_files
  ↓
build ParallelTask[]
  ↓
PhaseParallelExecutor.execute(tasks)
  ↓
aggregate test_docs_generated / errors
  ↓
context.test_docs = sorted_successful_docs
```

**MVP 验收**：
- 输出文档数量与串行版本一致。
- 单个 test doc 失败不会阻塞其他 test doc。
- final_report 能看到 Phase 5 并行任务统计。
- Phase 5 耗时在多测试文件场景下降明显。

### 3.4 Phase 4 文件级并行

Phase 4 比 Phase 5 更复杂，因为当前业务文件由一个 LLM tool loop 统一生成。

**推荐分两步推进**：

#### Step 1：文件计划生成

先让 LLM 或 deterministic planner 产出待生成文件计划：

```text
requirements + design + spec
  ↓
file generation plan
  ├─ include/user.h
  ├─ src/user.cpp
  ├─ include/login_service.h
  ├─ src/login_service.cpp
  └─ tests/test_login_service.cpp
```

每个文件计划包含：
- path
- purpose
- related_requirements
- dependencies
- generation_prompt_hint

#### Step 2：单文件并行生成

```text
file generation plan
  ↓
ParallelTask(code_file)[]
  ↓
bounded concurrent LLM calls
  ↓
write_file / validate / aggregate
```

**注意点**：
- 共享上下文应尽量只读：requirements、design、spec、top-k retrieved context。
- 每个文件生成任务只负责一个文件，降低互相覆盖风险。
- 对 header/source/test 这类有依赖关系的文件，可用 dependency stage 分批并行。
- 如果 file plan 不可靠，回退到当前串行 tool loop。

**推荐并行策略**：
```text
Stage 1: headers / interfaces
  ↓
Stage 2: implementations
  ↓
Stage 3: tests / main
```

每个 stage 内部并行，stage 之间保持顺序。

### 3.5 EventBus 与 final_report 观测

并行执行必须可观测，否则性能收益无法证明，失败也难排查。

**建议新增事件**：
- `file_task.started`
- `file_task.completed`
- `file_task.failed`
- `file_task.retrying`
- `phase.parallel_summary`

**事件字段**：
```json
{
  "event_type": "file_task.completed",
  "workflow_id": "...",
  "phase_num": 4,
  "task_id": "phase4:src/login_service.cpp",
  "task_type": "code_file",
  "path": "src/login_service.cpp",
  "duration_ms": 18432,
  "retry_count": 0,
  "success": true
}
```

**final_report 并行统计**：
```text
Parallel Execution Summary
- Phase: 4
- Total Tasks: 8
- Success: 8
- Failed: 0
- Retry: 1
- Max Concurrency: 3
- Parallel Duration: 62s
- Serial Baseline: 94s
- Speedup: 34.0%
```

### 3.6 失败处理与串行回退

**失败处理策略**：
1. 单任务失败后先 retry。
2. retry 仍失败则记录错误，但不立即终止其他任务。
3. 聚合阶段判断失败是否超过阈值。
4. 若失败过多，触发 serial fallback。

**串行回退触发条件**：
- 并行执行初始化失败。
- LLM provider 返回 rate limit 或并发限制错误。
- 文件依赖关系无法稳定解析。
- 失败任务比例超过阈值。

**回退原则**：
- 回退不能丢失已成功生成的文件。
- 回退结果必须在 final_report 中说明。
- 回退后仍需保持 ArtifactGraph 和 EventBus 一致。

---

## 4. 向量检索架构设计

### 4.1 设计理念

向量检索的目标不是替代现有 code search，而是补足语义召回能力，让单 Agent 在生成、评审和自愈时能找到真正相关的上下文。

```text
Project Artifacts
  ├─ requirements/*.md
  ├─ openspec changes
  ├─ design docs
  ├─ source files
  ├─ test files
  ├─ final reports
  └─ error memory / fix strategy
        ↓
CodeIndexer / ArtifactIndexer
        ↓
EmbeddingProvider
        ↓
VectorStore(ChromaDB)
        ↓
SemanticSearchService
        ↓
Phase 4 / Phase 9 / Phase 9.5 / Self-Healing
```

**核心收益**：
- Phase 4：生成代码前召回相关规范、设计和已有代码。
- Phase 9：质量检查时召回相关测试和需求。
- Phase 9.5：LLM-as-a-Judge 注入更精准上下文。
- Self-Healing：相似错误出现时召回历史 root cause 和 fix strategy。

### 4.2 模块结构

推荐 MVP 使用 ChromaDB，本地即可运行，适合快速验证和面试演示。

```text
devpal/vector_store/
├── __init__.py
├── embeddings.py       # EmbeddingProvider 封装
├── vector_db.py        # ChromaDB adapter
├── code_indexer.py     # code/doc/change/error artifacts 索引
├── semantic_search.py  # 语义检索与上下文构建 API
└── cli.py              # index/search 命令入口（可选）
```

**为什么先选 ChromaDB**：
- Python 集成简单。
- 本地开发不需要额外服务。
- 足够支撑 source/test/spec/error memory 的 MVP 检索。
- 后续可通过 adapter 切换到 Qdrant / Weaviate。

### 4.3 核心抽象

#### EmbeddingProvider

**职责**：封装 embedding 模型调用，避免业务层直接绑定具体 Provider。

```python
class EmbeddingProvider:
    def embed_text(self, text: str) -> list[float]:
        pass

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        pass
```

**设计要求**：
- 支持 batch embedding。
- 支持本地 mock embedding，便于测试。
- metadata 中记录 embedding model，便于后续迁移。

#### VectorDocument

**职责**：统一表示可索引 artifact chunk。

```python
from dataclasses import dataclass, field
from typing import Any, Dict

@dataclass
class VectorDocument:
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
```

#### VectorStore

**职责**：封装 ChromaDB 的 upsert/search/delete 操作。

```python
class VectorStore:
    def upsert(self, documents: list[VectorDocument]) -> None:
        pass

    def search(self, query: str, top_k: int = 5, filters: dict | None = None) -> list[VectorDocument]:
        pass

    def delete_by_project(self, project_name: str) -> None:
        pass
```

#### CodeIndexer

**职责**：把项目文件和 OpenSpec artifacts 切分为可检索 chunk。

```python
class CodeIndexer:
    def index_project(self, project_dir: Path) -> int:
        pass

    def index_file(self, path: Path) -> list[VectorDocument]:
        pass

    def index_change_artifacts(self, change_dir: Path) -> int:
        pass

    def index_error_memory(self, error_record: dict) -> str:
        pass
```

#### SemanticSearchService

**职责**：给 Phase 和 Self-Healing 提供稳定 API。

```python
class SemanticSearchService:
    def search_code(self, query: str, top_k: int = 5) -> list[VectorDocument]:
        pass

    def search_specs(self, query: str, top_k: int = 5) -> list[VectorDocument]:
        pass

    def search_similar_errors(self, error_message: str, top_k: int = 3) -> list[VectorDocument]:
        pass

    def build_context(self, query: str, top_k: int = 5) -> str:
        pass
```

### 4.4 索引对象与 metadata schema

#### 索引对象

**MVP 必须索引**：
1. `requirements/*.md`
2. OpenSpec Change artifacts
   - `proposal.md`
   - `specs/spec.md`
   - `tasks.md`
   - `design.md`
   - `metadata.json`
3. generated source files
4. generated test files
5. Phase 9 / Phase 9.5 / final reports
6. Self-Healing error memory
   - error message
   - root cause
   - fix strategy
   - successful patch summary

#### metadata schema

```json
{
  "project_name": "cpp_simple_login",
  "artifact_type": "source",
  "path": "src/login_service.cpp",
  "language": "cpp",
  "symbol": "LoginService::login",
  "phase_number": 4,
  "change_id": "add-login-service",
  "requirement_id": "REQ-001",
  "hash": "sha256:...",
  "mtime": "2026-05-28T10:30:00",
  "chunk_index": 0,
  "embedding_model": "text-embedding-..."
}
```

**metadata 用途**：
- 按项目隔离检索结果。
- 按 artifact_type 限定检索范围。
- 支持增量更新：hash / mtime 变化才重建索引。
- 支持 traceability：requirement_id / change_id 连接需求、代码、测试和报告。

### 4.5 检索策略

#### MVP：向量 top-k 检索

```text
query
  ↓
embed query
  ↓
ChromaDB similarity search
  ↓
top-k chunks
  ↓
build prompt context
```

适用场景：
- “用户登录密码校验逻辑在哪里？”
- “和 token 过期相关的测试有哪些？”
- “之前类似编译错误怎么修的？”

#### 增强：Hybrid Search

后续增强为关键词 + 向量混合检索：

```text
keyword search results
       +
vector search results
       ↓
RRF fusion / score merge
       ↓
rerank
       ↓
top-k context
```

**为什么需要 hybrid**：
- 文件名、函数名、错误码适合关键词检索。
- 需求语义、错误原因、设计意图适合向量检索。
- 混合检索可以减少纯向量误召回。

#### 未来增强

- Query rewrite：把用户问题改写成多个检索 query。
- Multi-query retrieval：从 requirement、code、error 三个角度召回。
- RRF fusion：融合关键词和向量结果。
- Rerank：用轻量 LLM 或规则对 top-k 重新排序。
- Metrics：Recall@K、MRR、NDCG。

### 4.6 集成点

#### Phase 4：代码生成

```text
requirements + design + file task
  ↓
SemanticSearchService.build_context(...)
  ↓
LLM prompt
  ↓
write_file
```

**注入内容**：
- 相关 requirements/spec/design chunk。
- 同模块已有代码。
- 相关测试样例。
- 历史相似修复策略。

#### Phase 9：质量门禁

**用途**：
- 检索与当前文件相关的 requirements 和 tests。
- 检查实现是否覆盖需求。
- 辅助生成更准确的质量报告。

#### Phase 9.5：LLM-as-a-Judge

**用途**：
- 给 Judge 注入相关架构文档和代码上下文。
- 避免 Judge 只基于单文件做片面评价。
- 提升 Architecture / Maintainability 评分准确性。

#### Self-Healing RCA

**用途**：
- 将失败日志、root cause、fix strategy 写入向量库。
- 新错误发生时检索相似历史错误。
- 优先尝试历史成功修复策略。

```text
new error
  ↓
search_similar_errors(error_message)
  ↓
root cause candidates + fix strategies
  ↓
Self-Healing repair prompt
```

#### EventBus 与 final_report

**建议新增统计**：
- vector.index_started
- vector.index_completed
- vector.search_started
- vector.search_completed
- retrieved_context_count
- top_k
- retrieval_latency_ms
- injected_context_tokens

---

## 5. 分阶段实施路线

### Day 1：Phase 5 并行 MVP

**目标**：先在风险最低的 Phase 5 验证并行执行收益。

**任务**：
1. 设计 `ParallelTask` / `ParallelTaskResult` / `PhaseParallelExecutor`。
2. 将 Phase 5 的 test doc 生成拆成独立 task。
3. 支持 `max_concurrency`。
4. 聚合 `test_docs_generated` 和 `errors`。
5. 输出 Phase 5 并行 summary。

**验收**：
- Phase 5 输出文档与串行版本一致。
- 多个 test doc 可以并发生成。
- 单个 test doc 失败不会阻塞其他任务。

---

### Day 2：Phase 4 文件级并行设计与接入

**目标**：将 Phase 4 从单一大 tool loop 逐步拆成文件级任务。

**任务**：
1. 增加 file generation plan 设计。
2. 将 header/source/test/main 拆成可并行 task。
3. 支持 stage-level dependency：headers → implementations → tests。
4. 接入 EventBus file task 事件。
5. final_report 输出并行统计。
6. 保留当前串行 tool loop fallback。

**验收**：
- Phase 4 可在并行模式下完成简单项目生成。
- 并行失败时可回退到串行模式。
- ArtifactGraph / generated_files / ai_generated_files 保持一致。

---

### Day 3：ChromaDB MVP 与基础索引

**目标**：建立最小可用向量库能力。

**任务**：
1. 创建 `devpal/vector_store/` 模块。
2. 实现 `EmbeddingProvider`。
3. 实现 `VectorStore` ChromaDB adapter。
4. 实现基础 chunking。
5. 支持 requirements、source、test、design 文件索引。

**验收**：
- 可以对项目建立向量索引。
- 可以通过自然语言检索相关文件 chunk。

---

### Day 4：Artifacts Indexer 与 Semantic Search API

**目标**：把 OpenSpec artifacts 和 error memory 纳入统一检索。

**任务**：
1. 实现 `CodeIndexer.index_change_artifacts()`。
2. 实现 `CodeIndexer.index_error_memory()`。
3. 实现 `SemanticSearchService.search_code()`。
4. 实现 `SemanticSearchService.search_specs()`。
5. 实现 `SemanticSearchService.search_similar_errors()`。
6. 提供 CLI/API 验证入口。

**验收**：
- 能检索 proposal/spec/tasks/design。
- 能检索历史错误和修复策略。
- metadata 支持 project_name / artifact_type / change_id / requirement_id 过滤。

---

### Day 5：Context Injection 与端到端验证

**目标**：把向量检索接入核心 Agent 流程。

**任务**：
1. Phase 4 prompt 注入 top-k requirements/design/code context。
2. Phase 9 prompt 注入相关 requirements/tests context。
3. Phase 9.5 Judge prompt 注入相关架构和代码 context。
4. Self-Healing prompt 注入相似错误和 fix strategy。
5. EventBus 记录 vector search 事件。
6. final_report 输出 retrieval summary。

**验收**：
- 端到端流程能完成。
- prompt 中可以看到检索上下文来源。
- Self-Healing 能召回相似历史错误。

---

## 6. 测试与验收标准

### 6.1 基础回归测试

```bash
python run_ai_flow.py -r requirements/simple_login.md
python -m pytest tests/openspec/
python -m pytest tests/e2e/
```

**验证点**：
- OpenSpec 11 阶段仍可正常运行。
- Phase 4/5 可正常完成。
- Phase 9/10/11 不受并行和向量检索影响。

### 6.2 并行执行验收

**测试命令**：
```bash
python run_ai_flow.py -r requirements/simple_login.md --max-concurrency 3
```

**验收标准**：
- Phase 5 并行任务数 = test docs 数量。
- Phase 4/5 耗时相比串行下降 30%+。
- EventBus 包含 file task 级事件。
- final_report 包含并行统计。
- 失败 task 可单独 retry。
- 并行失败可串行 fallback。

### 6.3 simple_calculator 实测结果（2026-05-28）

**测试命令**：
```bash
python run_ai_flow.py -r requirements/simple_calculator.md
```

**验证结果**：
- OpenSpec 11 阶段全部成功。
- Phase 4 默认并行已启用，3 个 `phase4:*` file task 全部成功。
- Phase 5 并行生成 2 个 test doc task，全部成功。
- Phase 9 validation completed event warning 已消除。
- EventBus 初始化直接使用 `cpp_simple_calculator/.spec/events.jsonl`，不再先落到 `unknown_project`。
- Phase 10 编译和测试通过：`14/14 passed`。

**性能收益**：
| 指标 | 串行/旧路径 | 并行/新路径 | 收益 |
|------|-------------|-------------|------|
| Phase 4 耗时 | 60.13s | 39.89s | -33.7% |
| 端到端总耗时 | 169.58s | 107.47s | -36.6% |
| Self-Healing 次数 | 1 | 0 | 编译质量更稳定 |

**结论**：Phase 4/5 并行执行在 `simple_calculator` golden case 上已达到 30%+ 性能提升目标，并保持端到端验证通过。

### 6.4 Phase 3 缓存优化实测结果（2026-05-28）

**优化内容**：
- 为 Phase 3 技术设计文档增加 requirements hash 缓存。
- 当 requirements、language、project_type、features 未变化时，直接复用 `docs/技术实现文档.md`。
- 同步写入当前 OpenSpec change directory 的 `design.md`，保证 Phase 4 后续读取链路不变。

**测试命令**：
```bash
python run_ai_flow.py -r requirements/simple_calculator.md
```

**验证结果**：
- Phase 3 命中缓存：`[CACHE] reused technical design`。
- Phase 3 耗时从 68.64s 降至 0.00s。
- 端到端流程成功完成，Phase 10 编译测试通过：`11/11 passed`。
- 总流程耗时降至 80.04s。

**注意**：Phase 4 对 header/source/test 这类依赖耦合 file plan 会自动禁用单文件并行，走稳定串行 tool loop，避免 header/source API 不一致。

### 6.5 向量检索验收

**测试命令**：
```bash
python -m devpal.vector_store.index_project cpp_simple_login
python -m devpal.vector_store.search "用户登录密码校验逻辑"
python -m devpal.vector_store.search "登录失败时的测试用例"
```

**验收标准**：
- 能检索到相关 source/test/design/spec 文件。
- 返回结果包含 path、artifact_type、score、chunk_index。
- 支持按 project_name 和 artifact_type 过滤。
- 增量索引不会重复写入未变化文件。

### 6.6 Context Injection 验收

**验证点**：
- Phase 4 prompt 中包含 top-k 相关 requirements/design/code chunk。
- Phase 9 prompt 中包含相关 requirements/tests chunk。
- Phase 9.5 prompt 中包含相关架构/代码 chunk。
- Self-Healing prompt 中包含相似错误和历史修复策略。

### 6.7 成功指标

| 指标 | 目标 | 验证方式 |
|------|------|----------|
| Phase 4/5 性能提升 | 30%+ | ✅ simple_calculator: Phase 4 -33.7%，端到端 -36.6% |
| Phase 3 缓存复用 | 命中后跳过 LLM | ✅ simple_calculator: 68.64s → 0.00s |
| 并行任务成功率 | 95%+ | EventBus / final_report |
| 失败任务隔离 | 100% | 构造单任务失败 |
| 串行回退可用 | 100% | 人为触发并发失败 |
| 向量索引覆盖 | source/test/design/spec/change/error | index summary |
| 语义检索可用 | top-k 命中相关文件 | golden query 验证 |
| Self-Healing 召回 | 可召回相似历史错误 | repeated error case |
| Context Injection | Phase 4/9/9.5 可注入 | prompt trace |

---

## 7. 风险与缓解

### 7.1 Phase 4 文件依赖风险

**风险**：header/source/test 之间存在依赖，如果完全并行可能生成不一致。

**缓解**：
- 使用 stage-level 并行：headers → implementations → tests。
- 先生成 file plan，再按依赖分组。
- file plan 不可靠时回退到串行 tool loop。

### 7.2 LLM Provider 并发限制风险

**风险**：并发 LLM 调用可能触发 rate limit。

**缓解**：
- 默认 `max_concurrency=3`。
- 支持配置降级到 1。
- 遇到 rate limit 自动 retry/backoff。
- 超过阈值时串行 fallback。

### 7.3 向量召回噪声风险

**风险**：不相关 chunk 被注入 prompt，影响生成质量。

**缓解**：
- top-k 默认较小。
- 使用 artifact_type / project_name / language filter。
- 后续引入 hybrid search 和 rerank。
- prompt 中标注 context 来源，便于调试。

### 7.4 索引陈旧风险

**风险**：文件变化后向量索引未更新，召回旧内容。

**缓解**：
- metadata 记录 hash 和 mtime。
- 每次索引前比较 hash。
- final_report 输出 index freshness summary。

### 7.5 架构范围膨胀风险

**风险**：并行执行和向量检索容易扩展成完整多 Agent 或复杂 RAG 平台。

**缓解**：
- MVP 只做 Phase 4/5 file task 并行。
- MVP 只做 ChromaDB 本地向量检索。
- Qdrant/Weaviate、RRF、rerank 放到后续增强。

---

## 8. 面试讲法

### 8.1 30 秒版本

DevPalAgent 当前已经有 Spec-first 11 阶段 workflow、Skills、EventBus、Self-Healing 和 LLM-as-a-Judge。下一步我没有直接重构成完整多 Agent，而是先补两个更关键的单 Agent 能力：第一是 Phase 4/5 文件级并行，把代码和测试生成从串行改成可控并发；第二是向量检索，把 requirements、design、code、test 和 error memory 建成语义索引，用于代码生成、质量评审和自愈召回。这样能提升性能和上下文质量，同时保留单 Agent 的低成本、可调试和 Prompt Caching 优势。

### 8.2 2 分钟版本

LLM coding agent 的瓶颈不只是“会不会生成代码”，还有两个工程问题：一是长流程性能，二是上下文选择。

在 DevPalAgent 里，Phase 4/5 是最耗时的阶段。Phase 4 负责生成业务代码，Phase 5 负责测试文档生成。当前它们仍然偏串行，所以我计划引入 `PhaseParallelExecutor`，把文件级任务拆成 `ParallelTask`，通过 `max_concurrency` 控制并发，并用 EventBus 和 final_report 记录每个任务的耗时、失败和重试。这样可以在不引入完整多 Agent 复杂度的情况下，把主流程耗时降低 30% 以上。

第二个能力是向量检索。DevPalAgent 会产生大量 artifacts：requirements、OpenSpec Change、design、source、tests、final report、error memory。仅靠关键词搜索很难找到语义相关上下文。所以我计划用 ChromaDB 做 MVP，建立 `devpal/vector_store/` 模块，把这些 artifacts 建成向量索引。Phase 4 生成代码前可以召回相关设计和代码；Phase 9/9.5 做质量检查时可以召回相关需求和测试；Self-Healing 遇到错误时可以召回相似历史错误和成功修复策略。

这个设计体现的重点是架构取舍：我评估过多 Agent，但当前场景是确定性的 SDLC workflow，不需要先引入 AgentPool。更好的路线是先强化单 Agent 主链路的并行执行、语义检索和可观测性。

### 8.3 高频问题

**Q: 为什么不直接用多 Agent 并行？**

A: 因为当前瓶颈是 Phase 内部文件级任务串行，不是缺少独立 Agent。完整多 Agent 会引入调度、状态同步、成本和调试复杂度，还可能削弱 Prompt Caching 收益。文件级并行能以更低复杂度解决主要性能问题。

**Q: 为什么先做 Phase 5 并行？**

A: Phase 5 的 test doc 任务天然独立，风险最低，最适合验证并行 executor、结果聚合、失败隔离和 EventBus 统计。验证成功后再推进更复杂的 Phase 4 文件级生成。

**Q: 向量数据库为什么选 ChromaDB？**

A: ChromaDB Python 集成简单，本地即可运行，适合 MVP 和面试演示。当前目标是验证语义召回、上下文注入和 Self-Healing 历史召回价值，不需要一开始引入 Qdrant 或 Weaviate 这种更重的部署复杂度。

**Q: 如何证明并行和向量检索真的有效？**

A: 并行通过串行/并行耗时对比、任务成功率、retry 次数和 final_report 统计证明。向量检索通过 golden query、top-k 命中率、prompt 注入记录和 Self-Healing 相似错误召回来证明。

---

## 9. 总结

### 9.1 核心结论

并行执行和向量检索是 DevPalAgent 下一阶段最值得优先补齐的两个 P0 能力。

- **并行执行**解决 Phase 4/5 主流程性能瓶颈。
- **向量检索**解决长期上下文选择和历史经验复用问题。
- 两者都强化单 Agent 主链路，而不是引入完整多 Agent 复杂度。

**已验证收益（2026-05-28，simple_calculator）**：
- Phase 4 默认并行成功执行 3 个 file task。
- Phase 5 并行成功执行 2 个 test doc task。
- Phase 4 耗时从 60.13s 降至 39.89s，提升 33.7%。
- 端到端总耗时从 169.58s 降至 107.47s，提升 36.6%。
- Phase 10 编译测试通过：14/14 passed。
- EventBus 初始路径和 Phase 9 validation event warning 已同步修复。
- Phase 3 技术设计缓存命中后从 68.64s 降至 0.00s，重复运行总耗时降至 80.04s。
- Phase 4 依赖耦合 file plan 会自动走串行稳定路径，避免单文件并行造成 API 不一致。

### 9.2 推荐实施顺序

1. Phase 5 并行 MVP
2. Phase 4 文件级并行
3. ChromaDB + EmbeddingProvider
4. CodeIndexer + SemanticSearchService
5. Phase 4/9/9.5/Self-Healing context injection
6. EventBus + final_report 指标闭环

### 9.3 与整体路线图关系

本文档对应 `plan_0528_priority_roadmap.md` 中的两个 P0：

1. **P0：并行工具调用优化**
2. **P0：向量数据库集成**

完成这两个能力后，再继续推进：

1. P1：Archive + Traceability 生命周期闭环
2. P1：AI-agnostic 协作模式
3. P2：最终文档、架构图和面试材料更新

### 9.4 最终目标

让 DevPalAgent 从“能完成 Spec-first 生成流程”进一步升级为：

```text
可并行执行
  +
可语义检索
  +
可历史召回
  +
可观测复盘
  +
仍然保持单 Agent 架构简单性
```

这将显著提升系统的实际可用性、面试说服力和后续扩展空间。
