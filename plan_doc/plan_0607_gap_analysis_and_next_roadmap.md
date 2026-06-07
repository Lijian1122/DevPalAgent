# DevPalAgent 当前实现差距分析与后续 Roadmap（2026-06-07）

**对照基准**：[plan_0528_priority_roadmap.md](plan_0528_priority_roadmap.md)  
**当前基准**：`master` 最新实现，已包含 OpenSpec 并行执行、向量检索、Archive/Traceability、AI-agnostic 协作模式，以及 2026-06-07 新增的多 Agent 沙箱执行能力。  
**结论**：0528 roadmap 的主线能力已经从“待实现”进入“已落地但需产品化验收”阶段。当前最大差距不再是缺功能，而是：端到端 golden flow、真实隔离语义、指标实测、文档准确性和面试演示闭环。

---

## 1. 总体判断

| 能力域 | 0528 目标 | 当前状态 | 差距等级 | 判断 |
|---|---|:---:|:---:|---|
| Phase 4/5 并行工具调用 | 文件级并行、失败隔离、EventBus 统计 | ✅ 已实现 | 低 | Phase 4/5 已接入 `PhaseParallelExecutor`，Phase 4 还有多 Agent 分支。缺少稳定性能基准。 |
| 向量数据库集成 | 代码/需求/变更语义检索，Phase 4/9/9.5 注入 | ✅ 已实现 | 中 | `SemanticSearchService` 已落地，但默认 mock embedding，缺少真实 embedding 质量评估。 |
| Archive + Traceability | change 生命周期闭环、覆盖矩阵 | ✅ 已实现 | 中 | CLI 和 E2E 已有；coverage matrix 仍偏粗粒度，未精确到 requirement → file/test 边。 |
| AI-agnostic 协作 | propose/apply/validate，规则包 | ✅ 基础实现 | 中 | CLI mode policy 和 rule pack 有落点；缺少完整外部工具协作 golden case。 |
| 多 Agent 架构 | 0528 暂缓完整多 Agent | ✅ 已超前实现 | 中高 | 已有 Coordinator/Codegen/Test/Review/Sandbox，但沙箱更像路径/命令策略校验，尚非完整独立 workspace。 |
| 演示脚本 | 8 个可运行 demo | 🔄 部分完成 | 高 | 有 Q&A 和图，但缺少统一 demo 脚本、录屏级命令和预期输出。 |
| 文档和架构图 | README/架构文档/面试稿同步 | 🔄 部分完成 | 高 | README 已更新，但存在“AgentPool/MessageBus/3-4x”等未完全可证实表述。 |
| 端到端验证 | simple_login golden flow | 🔄 不充分 | 高 | 单测覆盖较好，缺少一条从 requirements 到 archive 的完整回归脚本。 |

---

## 2. 与 0528 Roadmap 的逐项差距

### 2.1 P0：并行工具调用优化

**已实现证据**：
- Phase 4 文件计划和并行生成：`devpal/core/openspec_phases/phase4_generate_code.py`
- Phase 5 测试文档并行生成：`devpal/core/openspec_phases/phase5_generate_tests.py`
- 通用并行执行器：`devpal/core/openspec_phases/parallel_executor.py`
- 统计写入 final report：`devpal/core/openspec_phases/phase11_final_report.py`
- 测试覆盖：`tests/openspec/test_phase4_multi_agent.py`、`tests/openspec/test_phase5_generate_tests.py`

**剩余差距**：
1. 缺少串行 vs 并行的固定 benchmark 数据，0528 文档里的“耗时下降 30%+”尚未形成可复现实测。
2. Phase 4 并行和 multi-agent 分支都有 fallback，但缺少对 fallback 频率、失败原因、收益/成本的汇总报告。
3. Phase 5 当前是并行测试文档生成，不是完整 TestAgent 多智能体生成测试。

**建议状态**：从“功能开发”转为“性能验收 + 报告可信化”。

---

### 2.2 P0：向量数据库集成

**已实现证据**：
- 向量服务：`devpal/vector_store/semantic_search.py`
- 索引器和 CLI：`devpal/vector_store/indexer.py`、`devpal/vector_store/index_project.py`、`devpal/vector_store/search.py`
- Phase 4/9/self-healing 检索接入测试：`tests/openspec/test_phase4_prompt_contract.py`、`tests/openspec/test_self_healer_vector.py`
- 入口参数：`run_ai_flow.py` 的 `--vector-retrieval`、`--vector-top-k`、`--vector-persist-dir`

**剩余差距**：
1. 默认使用 `MockEmbeddingProvider`，可演示检索链路，但不能代表真实语义检索质量。
2. 缺少 top-k 召回率、噪声率、上下文注入对生成质量影响的评估。
3. Self-Healing 历史错误召回已有测试入口，但还没有“重复错误 golden case”证明实际修复效率提升。

**建议状态**：实现完成，下一步补“真实 embedding provider + 检索质量评测”。

---

### 2.3 P1：Archive + Traceability 生命周期闭环

**已实现证据**：
- Archive 服务：`devpal/openspec/archive.py`
- 覆盖矩阵：`devpal/openspec/coverage.py`
- CLI E2E：`tests/e2e/test_archive_e2e.py`
- 生命周期单测：`tests/openspec/test_archive_lifecycle.py`

**剩余差距**：
1. `CoverageMatrixBuilder` 当前按项目中是否存在 code/test/report 文件判断 `VERIFIED`，粒度偏粗。
2. ArtifactGraph 更新会批量给文件节点打 `change_id`，但没有精确证明某个 requirement 由哪个文件/测试覆盖。
3. Archive 与完整 OpenSpec 11 阶段的联动验收还不够：应验证 full/apply 流程结束后自动或手动 archive 的一致性。

**建议状态**：生命周期已闭环，但 traceability 需要从“存在性矩阵”升级为“精确关系矩阵”。

---

### 2.4 P1：AI-agnostic 协作模式

**已实现证据**：
- RunMode 和 ModePolicy：`devpal/collaboration/modes.py`
- Change 读取：`devpal/collaboration/change_loader.py`
- 规则包生成：`devpal/collaboration/rule_pack_generator.py`
- CLI 参数：`run_ai_flow.py` 的 `--propose-only`、`--apply-change`、`--validate-change`
- 单测：`tests/collaboration/test_modes.py`
- 架构文档：`doc3.0/ai_agnostic_collaboration_architecture.md`、`doc3.0/ai_agnostic_code_flow.md`

**剩余差距**：
1. 0528 文档提到 `/opsx:propose`、`/opsx:apply`、`/opsx:archive`、`/opsx:validate`，当前主要是 CLI 参数，不是实际 slash command 系统。
2. 缺少外部工具真实协作流程验证：propose-only 生成规则包 → 外部 AI 修改 → validate-change 验收 → archive。
3. 规则包容易重复写入或和项目级 `CLAUDE.md` 冲突，后续需要幂等和差异化测试。

**建议状态**：基础模式完成，下一步做“外部工具协作 golden case”。

---

### 2.5 新增超前项：多 Agent 沙箱执行

**已实现证据**：
- Coordinator：`devpal/core/multi_agent/coordinator.py`
- Agent 模型/后端/适配器：`devpal/core/multi_agent/models.py`、`backend.py`、`adapters.py`
- Codegen/Test/Review Agent：`codegen_agent.py`、`test_agent.py`、`review_agent.py`
- 沙箱策略：`devpal/core/multi_agent/sandbox.py`
- Phase 接入：Phase 4、Phase 9、Phase 10
- 测试覆盖：`tests/openspec/test_multi_agent_*.py`

**与 0605 目标相比的差距**：
1. 当前 `SandboxSession` 主要做路径和命令校验，尚未创建 `.spec/sandboxes/<task>/workspace` 独立工作区。
2. `MultiAgentCoordinator.merge_successful_results()` 仍直接写主项目目标文件，缺少 patch/staging/merge conflict 流程。
3. 没有独立 `AgentPoolManager` 生命周期状态，也没有 role-level 并发上限、token budget、cooldown。
4. EventBus 中缺少完整的 agent lifecycle、sandbox policy violation、resource budget events。
5. `sandbox_level` 目前只有配置传递和报告展示，缺少 `staging/strict/production` 的差异化策略。

**建议状态**：这是当前最有面试价值的新主线，但必须从“可运行 MVP”推进到“可审计安全边界”。

---

## 3. 后续 Roadmap（建议 10 天）

### Phase A：验收基线与文档纠偏（Day 1-2，P0）

**目标**：把“已经实现”变成“可证明实现”，并修正文档中过度承诺或过期表述。

任务：
1. 新增 `scripts/run_golden_openspec_flow.py` 或等价测试脚本，固定跑：full → propose-only → apply-change → validate-change → archive。
2. 建立 simple_login golden case 输出清单：change artifacts、generated files、quality report、final report、coverage matrix、archive manifest。
3. 更新 README 和核心架构文档，把“AgentPoolManager/MessageBus/3-4x”改成当前真实实现：`MultiAgentCoordinator + LocalThreadBackend + SandboxSession`。
4. 在 final report 中增加 fallback 使用情况、multi-agent task summary、sandbox violation summary。

验收命令：
```bash
python -m pytest tests/openspec/ tests/collaboration/ tests/e2e/test_archive_e2e.py
python run_ai_flow.py -r requirements/simple_login.md --max-concurrency 3 --vector-retrieval
python run_ai_flow.py -r requirements/simple_login.md --propose-only
python run_ai_flow.py -r requirements/simple_login.md --apply-change <change-id>
python run_ai_flow.py -r requirements/simple_login.md --validate-change <change-id>
python -m devpal.openspec archive <change-id> --project-dir <project-dir>
```

交付物：
- Golden flow 测试报告
- README/架构文档修订
- 当前能力状态表

---

### Phase B：多 Agent 沙箱产品化（Day 3-6，P0/P1）

**目标**：把 0605 多 Agent 沙箱从 MVP 提升为可解释、可审计、可控风险的架构亮点。

任务：
1. 为每个 AgentTask 创建 `.spec/sandboxes/<sandbox_id>/workspace`，Agent 输出先落 staging，再由 merge 阶段写主工作区。
2. 引入 patch/result manifest：记录 task_id、role、allowed_paths、artifacts、policy_violations、duration、merge_status。
3. 将 `sandbox_level` 做成真实策略：
   - `staging`：允许写 staging workspace；
   - `strict`：只允许 allowed_paths 和只读上下文；
   - `production`：禁止自动写主工作区，必须走 manifest/merge。
4. 增加 EventBus 事件：agent.started、agent.completed、sandbox.violation、agent.merge_completed、agent.fallback_used。
5. 增加 role-level 并发上限和预算字段，先在 `AgentPolicy` 中保留并报告，不必一次接入真实 token 计费。

验收标准：
- Phase 4 multi-agent 输出先写 sandbox/staging，再 merge。
- 任一 Agent 写越权路径会失败且记录 violation。
- final report 可列出每个 sandbox manifest。
- 现有 `tests/openspec/test_multi_agent_*.py` 扩展覆盖 staging workspace 和 violation events。

---

### Phase C：Traceability 与向量检索质量升级（Day 7-8，P1）

**目标**：把“能检索/能归档”升级为“关系可信、检索有质量指标”。

任务：
1. CoverageMatrixBuilder 从“所有文件覆盖所有需求”升级为基于 ArtifactGraph metadata 的 requirement → code/test/report 映射。
2. Phase 4 写入 generated file 时补充 requirement_ids / change_id / plan_item metadata。
3. 向量检索增加真实 embedding provider 配置入口，并保留 mock 作为测试 fallback。
4. 增加检索评估样例：给定 5 个查询，断言 top-k 包含目标文件或目标 artifact。
5. Self-Healing 增加重复错误 golden case，验证相似错误召回进入修复 prompt 或报告。

验收标准：
- `.spec/coverage_matrix.md` 能显示每个 requirement 对应具体 code/test/report。
- 向量检索测试同时覆盖 mock provider 和真实 provider 配置缺失时的 fallback。
- final report 中展示 retrieval stats 和 traceability coverage percent。

---

### Phase D：面试演示闭环（Day 9-10，P2）

**目标**：形成一套 10-15 分钟内可讲、可跑、可截图的最终材料。

任务：
1. 新增 `doc3.0/interview_demo_scripts.md`，每个 demo 包含命令、预期输出、失败时 fallback 话术。
2. 更新 `docs/interview_qa/README.md`，把并行、向量、Archive、AI-agnostic、多 Agent 沙箱加入主线问题。
3. 产出 5 张最终架构图：系统总览、OpenSpec 11 阶段、多 Agent 沙箱、Traceability/Archive、AI-agnostic 协作。
4. 删除或标注过时文档，避免面试时出现“文档说法和代码不一致”。

验收标准：
- 3 分钟版本、10 分钟版本、30 分钟深挖版本都能从同一套材料展开。
- 所有 demo 命令在干净环境跑通或明确说明依赖项。
- 文档中的性能数字都能追溯到 benchmark 或标注为目标值。

---

## 4. 当前最优先的 5 个任务

1. **P0：补 Golden Flow E2E**  
   一条脚本证明 full/propose/apply/validate/archive 全链路可跑。

2. **P0：修正文档事实偏差**  
   README 和架构图必须使用当前真实模块名，避免“AgentPoolManager/MessageBus”先于实现出现。

3. **P0：沙箱 staging workspace**  
   当前多 Agent 沙箱最大短板是没有真实隔离工作区，这是多 Agent 架构可信度核心。

4. **P1：Traceability 精确矩阵**  
   从存在性覆盖升级为 requirement-level 映射，是 OpenSpec-first 的关键卖点。

5. **P2：最终面试演示脚本**  
   把项目从“功能很多”压缩成“可讲清楚的一条工程闭环”。

---

## 5. 更新后的项目定位建议

0528 的定位是：**先补齐单 Agent 核心架构能力，再准备面试材料**。  
当前更准确的定位应升级为：

```text
DevPalAgent = Spec-first deterministic workflow
            + phase-level parallel execution
            + optional sandboxed multi-agent execution
            + traceable OpenSpec change lifecycle
            + AI-agnostic collaboration interface
```

面试叙事建议避免说“我做了完整分布式多 Agent 系统”，而应说：

> 我先用确定性的 OpenSpec 11 阶段保证主流程可控，再在文件级任务上引入并行和可选多 Agent。多 Agent 不是为了堆概念，而是被限制在 Coordinator、SandboxSession、AgentPolicy 和 ResultMerger 这几个边界内，确保失败隔离、路径权限和可审计事件。当前版本已完成 MVP，下一步重点是 staging workspace、EventBus lifecycle events 和 golden flow 验收。

---

## 6. 结论

`plan_0528_priority_roadmap.md` 的核心能力目标已经基本实现，且项目已经额外进入多 Agent 沙箱架构阶段。后续不建议继续横向增加新能力，而应集中做四件事：

1. 用 golden flow 证明主链路稳定；
2. 把多 Agent 沙箱从路径校验升级为真实 staging workspace；
3. 把 traceability 和向量检索做成可量化验收；
4. 把 README、架构图、Q&A 和 demo 脚本统一到当前真实实现。

完成这些后，DevPalAgent 才能从“功能丰富的原型”升级为“面试和项目展示都站得住的 Spec-first Agentic SDLC Runtime”。
