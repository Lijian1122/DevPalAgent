# DevPalAgent Interview Demo Scripts

## 目标

用一套命令把 DevPalAgent 讲成一个可验证的 Spec-first Agentic SDLC Runtime，而不是零散功能集合。

主线：

```text
requirements -> OpenSpec change -> apply/validate -> archive -> final report -> sandbox/vector/traceability evidence
```

---

## 3 分钟版本

### 讲法

> DevPalAgent 把 LLM 代码生成放进确定性 OpenSpec 流水线：先生成 change artifacts，再执行代码生成、质量门禁、测试、归档和报告。多 Agent 只在文件级任务上启用，并受 SandboxSession、AgentPolicy 和 manifest 约束。

### 命令

```bash
python scripts/run_golden_openspec_flow.py --dry-run
python scripts/benchmark_parallel_executor.py --json
python scripts/evaluate_vector_retrieval.py --json
```

### 展示点

- golden flow 命令序列可复现。
- benchmark 只证明本地并行执行器能力，不夸大真实 LLM 加速。
- vector smoke 使用 mock embedding，证明检索链路和评估格式稳定。

---

## 10 分钟版本

### 1. Golden lifecycle

```bash
python scripts/run_golden_openspec_flow.py --requirements requirements/simple_login.md
```

如果没有 LLM 凭证：

```bash
python scripts/run_golden_openspec_flow.py --dry-run
```

看点：

- `--propose-only` 生成 OpenSpec change 和规则包。
- `--apply-change <change-id>` 从 change artifacts 恢复上下文。
- `--validate-change <change-id>` 只跑验证阶段。
- `python -m devpal.openspec archive` 生成 archive manifest 和 coverage matrix。

### 2. Multi-agent sandbox evidence

```bash
python run_ai_flow.py -r requirements/simple_login.md --enable-multi-agent --sandbox-level strict --max-concurrency 3
```

检查：

```bash
ls cpp_simple_login/.spec/sandboxes/*/manifest.json
grep -n "Multi-Agent Sandbox Summary\|manifest.json" cpp_simple_login/docs/final_report.md
```

讲法：

> 当前 sandbox 是本地工程边界，不是容器。它提供路径/命令策略、workspace artifact、manifest、EventBus lifecycle 和 final report 汇总。

### 3. Traceability / Archive

```bash
grep -n "Coverage Matrix\|REQ-" cpp_simple_login/.spec/coverage_matrix.md
ls cpp_simple_login/.spec/archive/
```

讲法：

> Archive 不只是移动文件，而是把 change 合并到长期 spec，写 archive manifest，并用 ArtifactGraph/metadata 构建 requirement 到 code/test/report 的覆盖矩阵。

### 4. Vector retrieval

```bash
python scripts/evaluate_vector_retrieval.py --json
python run_ai_flow.py -r requirements/simple_login.md --vector-retrieval
```

讲法：

> 向量检索默认 mock provider，保证离线可测；Chroma 是可选持久化后端。Phase 4 会把 top-k 相关上下文注入生成 prompt，Phase 11 输出检索统计。

---

## 30 分钟深挖版本

### 架构顺序

1. OpenSpec 11 阶段流水线：`OpenSpecWorkflowExecutor -> EnhancedOpenSpecScheduler -> Phase 1-11`
2. AI-agnostic 协作：`RunMode.PROPOSE_ONLY / APPLY_ONLY / VALIDATE_ONLY`
3. 多 Agent 边界：`MultiAgentCoordinator + LocalThreadBackend + SandboxSession`
4. 质量闭环：Phase 9 quality gate、Phase 10 tests、Phase 11 final report
5. 归档追踪：`ArchiveChangeService + CoverageMatrixBuilder + ArtifactGraph`
6. 语义检索：`SemanticSearchService + ProjectArtifactIndexer`

### 可打开的文件

- `run_ai_flow.py`
- `devpal/core/openspec_phases/enhanced_scheduler.py`
- `devpal/core/multi_agent/coordinator.py`
- `devpal/core/multi_agent/sandbox.py`
- `devpal/openspec/archive.py`
- `devpal/openspec/coverage.py`
- `devpal/vector_store/semantic_search.py`
- `devpal/core/openspec_phases/phase11_final_report.py`

### 常见追问回答

**Q: 这是完整分布式多 Agent 吗？**

不是。当前是本地线程后端 + 可审计 sandbox MVP。重点是把多 Agent 限制在文件级任务和受控合并边界内，而不是追求分布式复杂度。

**Q: sandbox 是容器级安全吗？**

不是。当前提供路径、命令、workspace、manifest 和 EventBus 审计。容器/worktree/进程隔离是未来扩展，不在当前 MVP 承诺里。

**Q: vector retrieval 是否已经有真实语义质量？**

当前默认 mock embedding，强调链路稳定和测试可重复；Chroma 是持久化后端。真实 embedding provider 和召回质量 benchmark 是下一阶段增强。

**Q: 性能提升怎么证明？**

用 `scripts/benchmark_parallel_executor.py` 证明本地并行执行器的可复现收益；真实 LLM 端到端性能需要独立 benchmark，不把目标数字说成已测结果。

---

## 演示失败时 fallback 话术

- LLM 凭证缺失：切换 `--dry-run` 展示生命周期命令和测试覆盖。
- 编译器缺失：展示 Phase 10 跳过/失败报告和 self-healing 入口，而不是手动绕过。
- ChromaDB 未安装：说明系统会回退到 in-memory/mock provider，保证 demo 可运行。
- Multi-agent 某个任务失败：展示 fallback、manifest 和 final report 中的 policy/merge 记录。
