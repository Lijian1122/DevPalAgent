# DevPalAgent 当前差距分析与后续 Roadmap（2026-06-13）

> 对照基准：`plan_doc/plan_0607_gap_analysis_and_next_roadmap.md`  
> 当前基准：`master` 当前实现，最近主线提交为 `d4bec53 feat: harden openspec sandbox roadmap`

## 1. 总体结论

相比 2026-06-07 的 gap analysis，本项目已经从“核心能力基本实现，但验收闭环和 sandbox 产品化不足”，推进到“Spec-first Agentic SDLC Runtime 的本地可审计 MVP 已基本成型”。

当前最重要的变化是：多 Agent sandbox、golden flow、归档追溯、EventBus 观测、演示脚本和 README 事实校准已经形成闭环。剩余差距主要不再是“功能有没有”，而是“证据是否足够硬、真实场景是否足够完整、隔离和向量质量是否达到生产级”。

一句话定位：

> DevPalAgent 是一个以 OpenSpec 为中心的确定性 SDLC workflow runtime，支持阶段级并行执行、本地可审计多 Agent sandbox、变更归档追溯，以及 AI-agnostic 的外部协作 CLI。

需要继续避免把当前能力描述成“分布式多 Agent 平台”或“强隔离执行环境”。更准确的说法是：**本地多 Agent sandbox MVP + 显式 merge gate + 可追溯 workflow 证据链**。

## 2. 与 0607 Roadmap 的当前差距

| 能力域 | 0607 判断 | 0613 当前状态 | 剩余差距 |
| --- | --- | --- | --- |
| Phase 4/5 并行执行 | 低差距，需补 benchmark | 已有并行 executor proof script 与测试覆盖 | 仍缺真实 LLM/真实任务端到端性能数据 |
| Golden OpenSpec Flow | 高差距 | 已有 `scripts/run_golden_openspec_flow.py`，覆盖 propose/apply/validate/archive 与输出检查 | 仍需一次稳定的 non-dry-run golden run 作为 CI/发布级证据 |
| 多 Agent Sandbox | 中高差距 | 已有 staging workspace、manifest、strict/production level、显式 merge CLI | 目前是本地策略隔离，不是 OS/container/git worktree 强隔离 |
| EventBus 与可观测性 | 中差距 | 已覆盖 agent lifecycle、sandbox violation、merge、fallback、vector、archive 等事件 | token/resource/cooldown 等预算事件还不够完整 |
| Archive + Traceability | 中差距 | archive CLI、ArtifactGraph、final report coverage 已串起来 | requirement -> file/test 的精确度还需在真实生成流里加强 |
| Vector Retrieval | 中差距 | 已有 smoke/eval 脚本和 final report fallback 说明 | 默认仍偏 mock/local proof，缺真实 embedding provider 的质量基线 |
| AI-agnostic 协作 | 中差距 | CLI 和 golden runner 已支持外部 propose/apply/validate/archive 式协作 | 需要一条真实外部 AI/人工编辑变更流演示 |
| Demo/Docs | 高差距 | README 已校准，新增 interview demo scripts | 还需截图/录屏/面试 Q&A 统一包，以及旧文档措辞清理 |

## 3. 已经完成的关键能力

### 3.1 Golden Flow 验收闭环

已新增并强化 `scripts/run_golden_openspec_flow.py`：

- 覆盖 OpenSpec 生命周期：`propose -> apply -> validate -> archive`。
- 提供 dry-run 与真实项目路径模式。
- 输出 `GoldenFlowReport`，包含步骤状态、检查项、产物路径和失败原因。
- 对关键输出做结构化校验，而不是只依赖命令返回码。
- 已有测试覆盖 golden runner 的正向与失败路径。

这基本完成了 0607 roadmap 中“用一条可复现 golden path 证明当前系统能跑通”的要求。剩余是把 non-dry-run 结果固定成 CI 或发布报告资产。

### 3.2 Roadmap Proof Scripts

已补齐用于证明 0607 roadmap 重点能力的轻量脚本：

- `scripts/benchmark_parallel_executor.py`：并行执行基准 proof。
- `scripts/evaluate_vector_retrieval.py`：向量检索 smoke/eval proof。
- `tests/openspec/test_roadmap_proof_scripts.py`：确保 proof scripts 可执行、可解析、不会变成“文档里写了但代码跑不动”的漂浮资产。

这让 Phase 4/5 并行和 vector retrieval 至少都有可执行证据入口。

### 3.3 多 Agent Sandbox 产品化推进

当前 sandbox 能力已经从“概念性并行 Agent”推进为“可审计、本地隔离、显式合并”的执行机制：

- 支持 per-agent staging workspace。
- 支持 sandbox manifest 记录产物、违规、冲突和 merge_pending。
- 支持 `strict` / `production` 等 sandbox level。
- production merge 不再默认直接写入主项目，而是生成待合并清单。
- 新增 `SandboxMergeService` 与 CLI：

```bash
python -m devpal.openspec merge-sandbox <manifest> --project-dir <project> --apply
```

这已经覆盖 0607 roadmap 中 Phase B 的核心目标：Agent 输出必须经过显式 gate，主工作区不应被静默污染。

### 3.4 EventBus、Fallback 与最终报告

当前 workflow 已经能把更多运行时事实写入事件与报告：

- Agent 生命周期事件。
- sandbox violation / merge 相关事件。
- vector fallback 事件。
- archive 生命周期事件。
- final report 中的 Semantic Retrieval、Parallel Execution、Fallback Events、Multi-Agent Sandbox Summary、Archive Summary。

这使报告不再只是“执行成功/失败”，而是能解释用了哪些 fallback、哪些 sandbox 产物被合并、哪些能力实际生效。

### 3.5 文档与演示材料

已完成的文档性改进包括：

- README 中当前能力描述更接近真实模块名和实现边界。
- 新增 `doc3.0/interview_demo_scripts.md`，覆盖 3 分钟、10 分钟、30 分钟演示口径。
- 演示文档明确说明 sandbox 是本地边界，不是容器强隔离；vector 默认是 mock/local proof，不夸大成生产级语义检索。

这解决了 0607 roadmap 里“文档声称和代码事实不完全一致”的核心风险。

## 4. 当前仍然存在的主要缺口

### 4.1 缺少稳定的真实 Golden Run 资产

现在有 golden runner，但还需要一次稳定的 non-dry-run 项目样例，把完整报告、生成文件、archive 结果沉淀下来。否则验收证据仍偏“脚本可跑”，还不是“真实项目可复现”。

建议不要把临时生成目录直接散落在根目录，而是统一输出到 `.spec/golden_flow/` 或 `docs/generated/golden_flow/`，并明确哪些提交、哪些忽略。

### 4.2 Vector Retrieval 还没有生产级质量基线

当前已有 smoke eval，但默认仍更像 mock/local proof。下一步需要：

- 明确 embedding provider 配置入口。
- 准备固定 query set。
- 输出 top-k、hit rate、fallback rate。
- 在 final report 中区分 mock、local、real provider。

这样才能把“支持语义检索”升级为“可评估的语义检索质量”。

### 4.3 Traceability 精度还需要增强

Archive 和 ArtifactGraph 已经能串起来，但 requirement -> generated file -> test -> validation evidence 的映射还需要更细。

下一步应该让 Phase 4 生成产物携带更明确的 requirement id / artifact id，并在 Phase 11 coverage matrix 中用这些 id 建立稳定引用，减少启发式匹配。

### 4.4 Sandbox 仍是本地策略隔离

当前 sandbox 已经足以支撑“本地可审计多 Agent 协作”，但不能描述成强安全边界。

后续如果要进入更强生产场景，应考虑：

- git worktree 或临时项目副本隔离。
- 每个 agent 独立 dependency/cache 目录。
- 更细粒度 allowlist/denylist。
- merge conflict 可视化与人工确认。
- 可选 container/remote runner。

### 4.5 预算、资源和降级治理还不完整

0607 roadmap 提到的 budget/cooldown/resource 事件，目前还没有形成完整治理闭环。现状可以解释 fallback，但对 token、成本、并发资源、agent timeout 的策略化报告仍不足。

### 4.6 文档仍需一次全面扫尾

README 已经校准过关键点，但 roadmap、旧计划、面试材料和部分历史文档之间还可能存在口径差异。尤其要清理：

- 已不存在或未实现的 AgentPool/MessageBus 类表述。
- 把“未来规划”写成“当前能力”的句子。
- 对 sandbox、vector、external AI 协作的夸大说法。

## 5. 后续整体 Roadmap

### Phase 1：验收资产与 CI 硬化（1-2 天）

目标：把“能跑”变成“可复现、可提交、可验收”。

- 跑一次 non-dry-run golden flow，并产出稳定报告。
- 明确 `.spec/`、`simple_login/`、`requirements/.spec/` 等生成目录的提交或忽略策略。
- 把 golden runner、sandbox merge、parallel benchmark、vector eval 纳入最小验收命令清单。
- 在 README 或 `doc3.0/interview_demo_scripts.md` 中补一段“验收命令一键跑”的路径。

建议验收命令：

```bash
python -m pytest tests/openspec/test_sandbox_merge.py tests/golden/test_golden_flow_runner.py tests/openspec/test_phase4_multi_agent.py tests/openspec/test_phase9_quality_gate.py tests/openspec/test_phase11_final_report.py tests/test_eventbus_integration.py tests/e2e/test_archive_e2e.py tests/openspec/test_archive_lifecycle.py
python scripts/run_golden_openspec_flow.py --dry-run
python scripts/benchmark_parallel_executor.py --json
python scripts/evaluate_vector_retrieval.py --json
```

### Phase 2：Traceability 与 Vector 质量增强（2-4 天）

目标：把“报告里有覆盖率”变成“需求、代码、测试、归档证据能稳定互相指向”。

- 为生成产物补 requirement id / artifact id 元数据。
- 增强 Phase 11 coverage matrix，减少纯文本启发式匹配。
- 增加真实 embedding provider 或本地 embedding provider 配置。
- 建立固定 query set 与 top-k/hit-rate/fallback-rate 指标。
- 将 vector eval 结果汇入 final report。

### Phase 3：Sandbox 与 Agent 治理产品化（3-5 天）

目标：把本地 sandbox 从“可审计 MVP”推进到“更接近生产协作机制”。

- 支持 git worktree 或临时项目副本级隔离。
- 增加 merge conflict 检测、diff 摘要和人工确认流程。
- 将 AgentPolicy 的 timeout、max_files、allowed_paths、预算等配置写入报告。
- 补齐 token/resource/cooldown 事件。
- 对 agent 输出增加更强的 schema validation。

### Phase 4：AI-agnostic 协作与面试演示闭环（2-3 天）

目标：形成可以直接展示的“外部 AI/人工协作 + DevPal 验收归档”故事线。

- 设计一个真实小需求，例如 `simple_login` 或更小的 API feature。
- 使用外部 AI/人工编辑生成变更。
- DevPal 负责 validate、archive、traceability、final report。
- 录制或截图关键过程：proposal、sandbox manifest、merge、validate、archive report。
- 更新 `docs/interview_qa` 和 `doc3.0/interview_demo_scripts.md`，形成统一面试包。

## 6. 当前优先级建议

如果只做最有价值的 5 件事，建议顺序如下：

1. 跑通并保存一次真实 non-dry-run golden flow 报告。
2. 处理生成目录的 `.gitignore` / 提交策略，保持主线干净。
3. 为 vector retrieval 接入真实 provider 或固定本地 embedding，并输出质量指标。
4. 强化 requirement -> file/test/archive 的 traceability id 链路。
5. 整理 README、roadmap、interview docs 的一致口径，做一版可演示材料。

## 7. 阶段性判断

截至 2026-06-13，0607 roadmap 中的 P0/P1 大部分已经完成或有可运行入口。项目现在不再是“需要补齐基础模块”的状态，而是进入“证据资产、真实场景、质量指标、生产边界”的阶段。

短期内最应该追求的是：

- 一个真实 golden flow。
- 一个干净可复现的验收命令集合。
- 一个不夸大但足够有说服力的 demo narrative。

这样项目的下一阶段才会从“功能堆叠”转向“可信交付”。
