# DevPalAgent 下一阶段优先级规划（2026-05-28）

**基准日期**：2026-05-28  
**基准文档**：
- [plan_0522_priority_roadmap.md](plan_0522_priority_roadmap.md)
- [roadmap_status_2026-05-26.md](roadmap_status_2026-05-26.md)
- [interview_pitch_0525.md](../doc3.0/interview_pitch_0525.md)

**核心目标**：先补齐单Agent核心架构能力（并行执行、向量检索、Archive、AI-agnostic 协作），再输出最终版文档、架构图和面试材料

---

## 执行摘要

**🎉 重大里程碑：Archive + Traceability 生命周期闭环完成！**

### 已完成成果（2026-05-22 至 2026-06-01）

| 任务 | 优先级 | 状态 | 完成时间 | 实际工期 |
|------|:------:|:----:|---------|-----|
| 多LLM Provider 支持 | P0 | ✅ | 2026-05-22 | 2 天 |
| Prompt Caching 优化 | P0 | ✅ | 2026-05-22 | 1 天 |
| Multi-Agent Skills 系统 | P0 | ✅ | 2026-05-23 | 2 天 |
| LLM-as-a-Judge Critique | P1 | ✅ | 2026-05-23 | 1 天 |
| OpenSpec Change 集成 | P1 | ✅ | 2026-05-24 | 1 天 |
| Self-Healing 根因分析 | P2 | ✅ | 2026-05-25 | 1 天 |
| LanguagePlugin 主流程化 | P2 | ✅ | 2026-05-26 | 2 天 |
| EventBus 主流程接入 | P3 | ✅ | 2026-05-26 | 2 天 |
| Phase 4 tool loop 修复 | P0 | ✅ | 2026-05-28 | 0.5 天 |
| EventBus 项目名称修复 | P2 | ✅ | 2026-05-28 | 0.5 天 |
| 并行工具调用优化 | P0 | ✅ | 2026-05-30 | 2 天 |
| 向量数据库集成 | P0 | ✅ | 2026-05-31 | 2 天 |
| Archive + Traceability | P1 | ✅ | 2026-06-01 | 1 天 |

**总工期**：15 天（计划 12-19 天，提前完成）

### 核心技术指标

| 指标 | 目标 | 实际达成 | 超出比例 |
|------|------|---------|---------|
| Cache Hit Rate | >60% | 80.5% | +34% |
| API Cost Reduction | -40% | -60.7% | +52% |
| 响应时间降低 | -30% | -55% | +83% |
| Skills 路由准确率 | >80% | 100% | +25% |
| 根因分析准确率 | >80% | >85% | +6% |
| 面试能力矩阵 | 8/10 | 10/10 | 100% |

**所有指标均达标或超标！**

---

## 1. 当前状态快照

### 1.1 核心能力完成度

| 能力域 | 状态 | 说明 |
|---|:---:|---|
| OpenSpec 11 阶段流水线 | ✅ | Phase 1-11 完整实现 |
| Multi-Agent Skills 系统 | ✅ | 5 个 Skills，100% 准确率 |
| LLM-as-a-Judge Critique | ✅ | Phase 9.5，5 维度评审 |
| Prompt Caching 优化 | ✅ | 80.5% hit rate, -60.7% cost |
| Self-Healing 根因分析 | ✅ | 三层分析 + 全局学习 |
| OpenSpec Change 管理 | ✅ | 完整 change 目录生成 |
| LanguagePlugin 架构 | ✅ | Phase 2/4/9/10 统一插件 |
| EventBus 事件驱动 | ✅ | 完整事件追踪 + 监控 |
| 多LLM Provider 支持 | ✅ | Anthropic + OpenAI + Fallback |
| Quality Gate 验证 | ✅ | 四层验证 + 语言感知 |

**完成度**：10/10（100%）

### 1.2 面试能力矩阵

| 面试考察点 | 状态 | 演示方式 |
|--------|:----:|---------|
| Agent Workflow Orchestration | ✅ | 11 阶段状态机 + Skills 层 |
| Tool Use | ✅ | Phase 4 tool loop |
| State Management | ✅ | OpenSpecContext + checkpoint |
| Prompt Engineering | ✅ | PromptEngine + Caching (80.5% hit) |
| Multi-Agent Collaboration | ✅ | Skills 系统 + multi_agent_skill |
| Evaluation | ✅ | Phase 9/10/11 + Phase 9.5 Critique |
| Memory System | ✅ | 三层架构 |
| Reliability | ✅ | retry/checkpoint + 根因分析 |
| Change Management | ✅ | OpenSpec Changes |
| Traceability | ✅ | ArtifactGraph + change-id + EventBus |

**完成度**：10/10（100%）

### 1.3 已知问题和限制

| 问题 | 影响 | 优先级 | 状态 |
|---|---|:---:|:---:|
| ~~Phase 4 文件跳过循环~~ | ~~高 - 导致测试无法完成~~ | ~~P0~~ | ✅ **已修复** (2dba89d) |
| ~~EventBus 项目名称为 unknown_project~~ | ~~低 - 事件日志位置不正确~~ | ~~P2~~ | ✅ **已修复** (2026-05-28) |
| ~~缺少并行工具调用~~ | ~~中 - Phase 4/5 性能仍是串行瓶颈~~ | ~~P0~~ | ✅ **已完成** (2026-05-30) |
| ~~缺少向量数据库能力~~ | ~~中 - 代码语义检索和历史修复召回不足~~ | ~~P0~~ | ✅ **已完成** (2026-05-31) |
| ~~缺少 Archive 机制~~ | ~~中 - OpenSpec Change 生命周期未闭环~~ | ~~P1~~ | ✅ **已完成** (2026-06-01) |
| 缺少 AI-agnostic 协作 | 中 - 尚不能很好服务 Cursor/Cline/Claude Code 协作流 | P1 | 🔄 待实现 |
| 缺少完整演示脚本 | 中 - 影响面试准备 | P2 | 🔄 待完成 |
| 文档需要更新 | 中 - README/架构图过时 | P2 | 🔄 等架构能力补齐后更新 |
| 缺少端到端测试验证 | 中 - 演示场景未验证 | P2 | 🔄 待验证 |

**最新修复**（2026-05-28）：
- ✅ **Phase 4 tool loop 修复** (commit `2dba89d`): 修复了 Anthropic provider 的多轮 tool loop 处理问题，解决了文件跳过循环和无限重试的问题。现在 tool loop 能够正确保持 assistant 响应历史、收集 tool 结果，并在没有 tool 调用时干净退出。
- ✅ **EventBus 项目名称修复** (2026-05-28): 修复了 EventBus 项目名称为 unknown_project 的问题，现在事件日志能够正确写入项目目录（如 `cpp_simple_login/.spec/events.jsonl`）。

---

## 2. 优先级规划（下一阶段）

### ~~P0：Phase 4 文件跳过循环修复（0.5-1 天）~~ ✅ **已完成**

#### 2.1 修复状态

**提交记录**：`2dba89d` - fix(anthropic): repair multi-turn tool loop handling

**修复内容**：
- 修复了 Anthropic provider 的多轮 tool loop 处理问题
- 正确保持 assistant 响应在消息历史中
- 正确收集跨轮次的 tool 结果
- 在没有 tool 调用返回时干净退出
- 恢复了稳定的迭代 tool-use 行为

**验证状态**：
- ✅ Tool loop 逻辑修复
- ✅ 消息历史正确维护
- ✅ 退出条件正确
- 🔄 端到端测试待验证（在演示脚本准备阶段验证）

**影响**：
- 解决了 Phase 4 文件跳过循环问题
- 解决了无限重试同一文件的问题
- Phase 4 现在可以正常完成

---

### P0：并行工具调用优化（1-2 天）🔥 **当前最优先**

#### 2.4 目标

在不引入完整多Agent复杂度的前提下，让 Phase 4/5 支持并行文件生成，提升单Agent主流程性能。

#### 2.5 为什么优先做

1. **直接提升可用性**：Phase 4/5 是长流程中最耗时的部分，并行化能显著改善用户体验。
2. **保持单Agent优势**：不需要独立 Agent 池，不破坏 Prompt Caching 和统一上下文。
3. **实现风险低**：使用 asyncio 或并发任务队列即可完成，不改变 OpenSpec 11 阶段主架构。
4. **面试价值明确**：能说明“评估过多Agent，但选择了更低复杂度的并行工具调用”。

#### 2.6 实施范围

**Phase 4：代码生成并行化**
- 将待生成文件拆成独立 file tasks
- 并发调用单文件生成逻辑
- 汇总生成结果、失败列表和 retry 信息
- 保持 ArtifactGraph / EventBus 事件记录

**Phase 5：测试生成并行化**
- 按功能模块或源文件并行生成测试
- 将测试生成结果写回统一上下文
- 保证 Phase 9/10 仍按统一项目状态验证

**并发控制**
- 设置 max_concurrency，避免 API 并发过高
- 保留串行 fallback
- 失败任务单独 retry，不拖垮整个 Phase

#### 2.7 验收标准

```bash
python run_ai_flow.py -r requirements/simple_login.md

# 验证：
# 1. Phase 4/5 可正常完成
# 2. EventBus 记录每个 file.generated/test.generated 事件
# 3. final_report 显示并行任务统计
# 4. 相比串行版本耗时下降 30%+
```

---

### P0：向量数据库集成（2-3 天）🧠 **第二优先**

#### 2.8 目标

为 DevPalAgent 增加代码语义检索、需求到代码映射、历史错误召回和 LLM Context 精准裁剪能力，提升单Agent智能化水平。

#### 2.9 核心能力

1. **代码库语义索引**
   - 对生成代码、测试、设计文档、OpenSpec Change artifacts 建立向量索引
   - 支持按自然语言查询相关文件和代码片段

2. **需求到代码映射增强**
   - requirements / spec item → code chunks
   - 增强 ArtifactGraph 的 introduced_by / related_requirements 信息

3. **Self-Healing 历史召回**
   - 将错误模式、root cause、fix strategy 向量化
   - 相似错误出现时优先召回历史成功修复策略

4. **LLM Context 优化**
   - Phase 4/9/9.5 只注入相关代码片段
   - 减少无关上下文，提高生成和评审质量

#### 2.10 推荐技术方案

**优先选型：ChromaDB**
- Python 集成简单
- 适合本地开发和面试演示
- 不需要额外服务即可跑通 MVP

**模块结构建议**：
```text
devpal/vector_store/
├── embeddings.py       # embedding provider 封装
├── vector_db.py        # ChromaDB adapter
├── code_indexer.py     # 代码/文档索引
└── semantic_search.py  # 语义检索 API
```

#### 2.11 验收标准

```bash
python -m devpal.vector_store.index_project cpp_simple_login
python -m devpal.vector_store.search "用户登录密码校验逻辑"

# 验证：
# 1. 能检索到相关 source/test/design/spec 文件
# 2. Self-Healing 可召回相似错误历史
# 3. Phase 4/9 prompt 中能注入 top-k 相关上下文
```

---

### P1：Archive + Traceability 生命周期闭环（3-4 天）✅ **已完成**

#### 2.12 完成状态

**完成时间**：2026-06-01

**实现内容**：
- ✅ `archive_change(change_id)` 命令完整实现
- ✅ Delta merge 到 `openspec/specs/main.md`
- ✅ Change 状态流转：PROPOSED → IN_PROGRESS → IMPLEMENTED → ARCHIVED
- ✅ ArtifactGraph 扩展：introduced_by / archived_at / change_id / requirement_ids
- ✅ Coverage matrix：Requirement → Code → Test → Report
- ✅ Phase 11 集成：Archive Summary 自动生成
- ✅ EventBus 集成：archive 事件完整记录
- ✅ CLI 命令：`python -m devpal.openspec archive <change-id>`
- ✅ 幂等性保证：重复 archive 安全
- ✅ 完整测试覆盖：单元测试 + 端到端测试

**验证结果**：
```bash
# 单元测试
python -m pytest tests/openspec/test_archive_lifecycle.py -v
# 4 passed

# 端到端测试
python -m pytest tests/e2e/test_archive_e2e.py -v
# 1 passed

# 总计：5 个测试全部通过
```

**文档**：
- ✅ [doc3.0/archive_lifecycle.md](../doc3.0/archive_lifecycle.md) - 完整架构和使用指南
- ✅ README.md 已更新 Archive 章节

**影响**：
- OpenSpec Change 生命周期完整闭环
- Requirement → Code → Test → Report 完整追踪
- 支持长期项目演进和审计

---

### P1：AI-agnostic 协作模式（5-7 天）

#### 2.15 目标

让 DevPalAgent 不只服务自身 CLI，也能服务 Claude Code / Cursor / Cline 等外部 AI coding 工具，形成 AI-agnostic 的 spec-first 协作模式。

#### 2.16 核心能力

1. **propose-only 模式**
   - 只生成 proposal/spec/tasks/design，不直接改代码
   - 适合人审和外部 AI 工具接手

2. **apply-only 模式**
   - 读取已有 change artifacts 执行代码生成、验证、测试
   - 适合 Cursor/Cline/Claude Code 修改后由 DevPalAgent 验收

3. **CLAUDE.md / .cursorrules / Cline rules 模板**
   - 注入 spec-first 工作流规则
   - 告诉外部 AI 如何读取 changes 目录、如何保持 traceability

4. **外部工具协作命令**
   - `/opsx:propose`
   - `/opsx:apply`
   - `/opsx:archive`
   - `/opsx:validate`

#### 2.17 验收标准

```bash
python run_ai_flow.py -r requirements/simple_login.md --propose-only
python run_ai_flow.py --apply-change <change-id>

# 验证：
# 1. propose-only 不生成代码，只生成 change artifacts
# 2. apply-only 能基于 change artifacts 完成代码/测试/报告
# 3. CLAUDE.md 明确说明外部 AI 协作流程
```

---

### P2：面试演示脚本准备（1-2 天）

#### 2.18 目标

在并行、向量库、Archive、AI-agnostic 协作的架构能力补齐后，再统一整理最终演示脚本，确保演示内容和最终架构一致。

#### 2.5 演示清单

**Demo 1: 端到端生成**（3 分钟）
- 展示 11 阶段流程
- OpenSpec Change 生成
- Quality Gate 报告
- Final Report + ArtifactGraph

**Demo 2: Phase 9.5 Critique**（2 分钟）
- 展示 LLM 评审
- 5 维度评分
- 改进建议

**Demo 3: Self-Healing 根因分析**（2 分钟）
- 展示错误分类
- 追溯链路
- 修复历史学习

**Demo 4: Skills 系统**（2 分钟）
- 展示意图识别
- 自动路由
- installer_skill 演示

**Demo 5: Prompt Caching**（2 分钟）
- 第一次运行（创建缓存）
- 第二次运行（命中缓存）
- 成本降低 60.7%

**Demo 6: 多LLM Provider**（2 分钟）
- Anthropic Provider
- OpenAI Provider
- Fallback 机制

**Demo 7: Quality Gate**（2 分钟）
- 四层验证
- 语言感知
- 自愈能力

**Demo 8: EventBus 事件追踪**（2 分钟）
- 事件日志查看
- 事件统计分析
- 全链路可观测性

**总演示时间**：17 分钟

#### 2.6 实施计划

**Task 1: 创建演示脚本文件**（0.5 天）
- 新增 `doc3.0/interview_demo_scripts.md`
- 包含 8 个演示场景
- 每个场景包含：命令、预期输出、面试话术

**Task 2: 验证所有演示**（0.5 天）
- 运行所有 8 个演示
- 记录实际输出
- 修复发现的问题

**Task 3: 准备演示数据**（0.3 天）
- 准备演示用的 requirements 文件
- 准备演示用的项目目录
- 确保演示环境干净

**Task 4: 录制演示视频（可选）**（0.2 天）
- 录制关键演示场景
- 用于面试前复习

#### 2.7 验收标准

- 8 个演示脚本全部可运行
- 每个演示有清晰的面试话术
- 演示时间控制在 2-3 分钟内
- 所有演示输出符合预期

---

### P2：面试 Q&A 文档完善（1 天）

#### 2.19 目标

在核心架构能力落地后，统一补充面试问题回答，覆盖新加入的并行执行、向量数据库、Archive、AI-agnostic 协作等技术点。

#### 2.9 Q&A 清单

**已有文档**：
- `doc3.0/interview_pitch_0525.md` - 项目讲解稿

**待创建文档**：
- `doc3.0/interview_qa_caching.md` - Prompt Caching Q&A
- `doc3.0/interview_qa_skills.md` - Skills 系统 Q&A
- `doc3.0/interview_qa_critique.md` - Critique Phase Q&A
- `doc3.0/interview_qa_root_cause.md` - 根因分析 Q&A
- `doc3.0/interview_qa_openspec_change.md` - OpenSpec Change Q&A
- `doc3.0/interview_qa_eventbus.md` - EventBus Q&A

**核心问题**（12 个）：
1. 如何设计 Agent workflow？
2. 如何处理 Tool Use？
3. 如何管理 Agent 状态？
4. 如何优化 Prompt？
5. 如何实现多 Agent 协作？
6. 如何评估生成质量？
7. 如何处理多语言？
8. 如何追踪需求？
9. 如何实现自愈？
10. 如何降低成本？
11. 如何保证可观测性？
12. 遇到过什么真实 bug？

#### 2.10 实施计划

**Task 1: 创建 Q&A 文档**（0.5 天）
- 创建 6 个 Q&A 文档
- 每个文档包含 5-10 个问题
- 每个问题包含：问题、回答、技术细节、面试话术

**Task 2: 完善技术细节**（0.3 天）
- 补充技术实现细节
- 添加代码示例
- 添加架构图

**Task 3: 准备 STAR 讲法**（0.2 天）
- Situation - 问题背景
- Task - 任务目标
- Action - 具体行动
- Result - 量化成果

#### 2.11 验收标准

- 6 个 Q&A 文档完整
- 每个文档包含 5-10 个问题
- 所有问题有清晰的回答和面试话术
- 技术细节准确无误

---

### P2：最终文档和架构图更新（1-2 天）

#### 2.20 目标

等并行执行、向量数据库、Archive、AI-agnostic 协作这些关键架构能力完成后，再更新 README、架构文档、面试稿和架构图，避免文档反复返工。

#### 2.13 文档清单

**需要更新的文档**：
1. `README.md` - 项目总览
2. `doc3.0/agent_architecture.md` - 架构详解
3. `doc3.0/interview_pitch_0525.md` - 面试讲解稿
4. `CLAUDE.md` - 项目指南

**需要创建的架构图**：
1. 系统架构图（三层编排）
2. Skills 系统架构图
3. EventBus 架构图
4. Phase 流程图
5. 数据流图

#### 2.14 实施计划

**Task 1: 更新 README.md**（0.3 天）
- 更新项目简介
- 更新核心特性
- 更新架构图
- 更新快速开始

**Task 2: 更新架构文档**（0.3 天）
- 更新 `doc3.0/agent_architecture.md`
- 添加 Skills 系统章节
- 添加 EventBus 章节
- 添加 Critique Phase 章节

**Task 3: 创建架构图**（0.3 天）
- 使用 Mermaid 创建架构图
- 系统架构图
- Skills 系统架构图
- EventBus 架构图

**Task 4: 更新面试讲解稿**（0.1 天）
- 更新 `doc3.0/interview_pitch_0525.md`
- 添加最新成果
- 更新量化指标

#### 2.15 验收标准

- README.md 与最新实现一致
- 架构文档完整准确
- 5 个架构图清晰易懂
- 面试讲解稿更新完整

---

### ~~P2：EventBus 项目名称修复（0.5 天）~~ ✅ **已完成**

#### 2.16 修复状态

**完成时间**：2026-05-28

**问题描述**：
- 事件日志在 `unknown_project/.spec/events.jsonl`
- 而不是 `cpp_simple_login/.spec/events.jsonl`

**修复方案**：
- 从 requirements_file 推断项目名称
- 在 EventBusIntegration 初始化时正确设置项目名称

**验证结果**：
- ✅ 事件日志现在写入正确的项目目录
- ✅ 不再有 unknown_project 目录
- ✅ 项目名称正确识别

**影响**：
- 解决了事件日志位置不正确的问题
- EventBus 功能完全正常

---

### P3：后续低优先级能力扩展（按需）

> 注：并行工具调用、向量数据库、Archive、AI-agnostic 协作已经提升为 P0/P1 架构能力，不再放在 P3 可选项。P3 只保留锦上添花或探索性能力。

#### 2.21 多维度质量评分系统（2-3 天）⭐⭐⭐

**目标**：在 Phase 9.5 Critique 的基础上沉淀长期质量趋势。

**评分维度**：
- Correctness（功能正确性）：0-100
- Readability（代码可读性）：0-100
- Maintainability（可维护性）：0-100
- Performance（性能）：0-100
- Security（安全性）：0-100
- Test Coverage（测试覆盖率）：0-100

**输出**：
- Quality Scorecard（质量记分卡）
- 趋势分析（多次运行的质量变化）
- 对标基准（与行业标准对比）

**优先级**：P3（可选，Phase 9.5 已有基础评分能力）

---

#### 2.22 Skills 生态扩展（2-3 天）⭐⭐

**目标**：按实际需求补充专业 Skill，而不是为了“多Agent感”提前扩张。

**候选 Skill**：
1. **RefactorSkill**：代码重构
2. **SecuritySkill**：安全审查
3. **PerformanceSkill**：性能优化
4. **DocumentationSkill**：文档生成

**优先级**：P3（低于并行、向量库、Archive、AI-agnostic；当前 5 个 Skills 已覆盖核心场景）

---

#### 2.23 混合架构探索（暂不实施）⭐⭐

**结论**：当前不重构为多Agent，也不急于引入独立 AgentPool。

**原因**：
- 多Agent必要性评估仅 3/10
- 会增加成本和调试复杂度
- 当前更应该强化单Agent主流程的并行执行、语义检索和协作协议

**保留场景**：未来出现批量长任务或持续监控任务时，再评估是否将部分 Skill 升级为独立 Agent。

---

## 3. 实施时间线

### Phase A（Day 1-2）：并行工具调用优化 ⚡

**目标**：先解决单Agent主流程性能瓶颈。

- Day 1：设计并实现 Phase 4 file task 拆分、asyncio 并发执行、max_concurrency 控制
- Day 2：接入 Phase 5 测试生成并行化，补充 EventBus 事件和 final_report 并行统计

**验收**：Phase 4/5 正常完成，耗时较串行下降 30%+。

---

### Phase B（Day 3-5）：向量数据库集成 🧠

**目标**：给单Agent补上语义检索和历史召回能力。

- Day 3：集成 ChromaDB，建立 `devpal/vector_store/` 基础模块
- Day 4：实现代码、测试、design、OpenSpec artifacts 索引和语义搜索 API
- Day 5：接入 Phase 4/9/9.5 和 Self-Healing，支持 top-k 相关上下文注入和相似错误召回

**验收**：可以用自然语言检索相关代码；Self-Healing 能召回相似历史错误；Phase 4/9 prompt 可使用向量检索上下文。

---

### Phase C（Day 6-9）：Archive + Traceability 生命周期闭环 📚

**目标**：补齐 OpenSpec Change 从生成到归档的闭环。

- Day 6-7：实现 `archive_change(change_id)` 命令和 Change 状态流转
- Day 8：实现 delta merge 到 `openspec/specs/main.md`
- Day 9：扩展 ArtifactGraph 和 coverage matrix，接入 final_report

**验收**：Change 可从 PROPOSED/IMPLEMENTED 归档到 ARCHIVED，主规范和 traceability 均保留记录。

---

### Phase D（Day 10-16）：AI-agnostic 协作模式 🤝

**目标**：让 DevPalAgent 可以服务 Claude Code / Cursor / Cline 等外部 AI coding 工具。

- Day 10-11：实现 propose-only 模式，只生成 change artifacts
- Day 12-13：实现 apply-only 模式，基于已有 change artifacts 执行生成/验证/测试
- Day 14：完善 CLAUDE.md / .cursorrules / Cline rules 模板
- Day 15-16：补充 `/opsx:propose`、`/opsx:apply`、`/opsx:archive`、`/opsx:validate` 协作说明和测试

**验收**：外部 AI 可以读取 change artifacts 协作修改，DevPalAgent 可负责 apply/validate/archive。

---

### Phase E（Day 17-19）：最终文档、架构图和面试材料 📝

**目标**：等架构能力稳定后，再一次性更新最终材料，避免反复返工。

- Day 17：更新 README、`doc3.0/agent_architecture.md`、`interview_pitch_0525.md`
- Day 18：补齐架构图：系统总览、并行执行、向量检索、Archive 生命周期、AI-agnostic 协作
- Day 19：整理演示脚本、Q&A、端到端验证记录

**验收**：最终文档与真实系统一致，演示脚本覆盖新增架构能力。

---

### 总体优先级结论

1. **先做并行工具调用**：提升单Agent可用性和性能。
2. **再做向量数据库**：提升单Agent语义检索、上下文选择和自愈召回能力。
3. **再做 Archive + Traceability**：补齐 OpenSpec 生命周期闭环。
4. **再做 AI-agnostic 协作**：扩展到 Claude Code / Cursor / Cline 等工具。
5. **最后做文档和架构图**：等系统能力定型后统一更新。

**总工期**：约 19 天（3.5-4 周）

**预计架构能力完成**：2026-06-16  
**预计最终文档和面试材料完成**：2026-06-19

---

## 4. 验收标准

### 4.1 ~~Phase 4 循环修复~~ ✅ **已完成**

- ✅ Tool loop 逻辑修复（commit 2dba89d）
- ✅ 消息历史正确维护
- ✅ 退出条件正确

### 4.2 ~~EventBus 项目名称修复~~ ✅ **已完成**

- ✅ 事件日志在正确位置
- ✅ 不再有 unknown_project 目录
- ✅ 项目名称正确识别

### 4.3 并行工具调用优化

- Phase 4/5 支持可配置 max_concurrency
- 并行任务失败可单独 retry，不影响其他文件
- EventBus 记录每个文件/测试生成事件
- final_report 输出并行任务统计
- 相比串行执行耗时下降 30%+

### 4.4 向量数据库集成

- 能索引 source/test/design/spec/change artifacts
- 支持自然语言语义搜索相关代码和文档
- Phase 4/9/9.5 可注入 top-k 相关上下文
- Self-Healing 可召回相似错误和历史修复策略

### 4.5 Archive + Traceability

- 支持 `archive_change(change_id)` 命令
- Change 状态可流转到 ARCHIVED
- Delta 可合并到 `openspec/specs/main.md`
- ArtifactGraph 保留 change_id / introduced_by / archived_at
- final_report 输出 coverage matrix

### 4.6 AI-agnostic 协作模式

- `--propose-only` 只生成 change artifacts，不改代码
- `--apply-change <change-id>` 可基于 change artifacts 执行实现和验证
- CLAUDE.md / Cursor / Cline 协作规则清晰
- `/opsx:propose`、`/opsx:apply`、`/opsx:archive`、`/opsx:validate` 有明确说明

### 4.7 最终文档和演示材料

- README.md 与最终架构一致
- 架构文档覆盖并行执行、向量检索、Archive、AI-agnostic 协作
- 架构图包含系统总览、数据流、事件流、生命周期流
- 演示脚本覆盖新增架构能力
- Q&A 覆盖“为什么不完整多Agent”“为什么先并行+向量库”“如何 AI-agnostic 协作”

---

## 5. 核心亮点总结

### 5.1 已完成的核心亮点

1. 🌟 **LLM-as-a-Judge**：5 维度代码质量评审（皇冠明珠）✅
2. 🌟 **Prompt Caching**：80.5% hit rate, 60.7% cost reduction ✅
3. 🌟 **Multi-Agent Skills**：5 个 Skills，意图识别 100% 准确 ✅
4. 🌟 **多LLM Provider**：Anthropic + OpenAI + Fallback ✅
5. 🌟 **OpenSpec Changes**：完整的变更管理流程 ✅
6. 🌟 **根因分析**：基于 Traceability 的智能自愈 ✅
7. 🌟 **LanguagePlugin**：统一语言插件架构 ✅
8. 🌟 **EventBus**：事件驱动架构 + 全链路可观测性 ✅

### 5.2 面试展示价值

**技术深度**：
- ✅ **架构设计**: Event-Driven Architecture, Multi-Agent Orchestration
- ✅ **可观测性**: 全链路追踪, 实时监控, 性能分析
- ✅ **成本优化**: Prompt Caching, 多LLM Provider
- ✅ **质量保证**: LLM-as-a-Judge, 四层验证, 根因分析
- ✅ **扩展性**: LanguagePlugin, Skills 系统, EventBus

**量化成果**：
- 代码量：52,397 行 Python
- 测试：135 个用例，95.7% 通过率
- 工具：30+ 注册工具
- 开发效率：12 天完成 8 个重大功能（5.75 次提交/天）
- Cache Hit Rate: 80.5%
- Cost Reduction: -60.7%
- Skills 准确率: 100%

---

## 6. 面试讲法（更新）

### 6.1 30 秒版本

DevPalAgent 是一个 Spec-first Agentic SDLC Runtime。它把需求文档通过 11 阶段 Agent workflow 转成可验证的软件项目。系统包含 **Multi-Agent Skills**（意图识别 + 自动路由）、**Self-Healing RCA**（三层智能根因分析）、**LLM-as-a-Judge**（5 维度代码质量评审）、**Prompt Caching**（成本降低 60.7%）、**EventBus**（全链路可观测性）。最近 12 天完成了 8 个重大功能。量化成果：52K 行代码，135 测试，95.7% 通过率。

### 6.2 2 分钟版本

LLM 写代码最大的问题不是"能不能生成"，而是生成结果不可控、不可验证、不可追踪。DevPalAgent 的思路是把 LLM 放进一个确定性的工程流水线里。

**系统分三层**：
1. **Plan-Act-Reflect Agent 链路**：Skills Router → Planner → Executor → Reflector
2. **OpenSpec Runtime 链路**：11 阶段工作流（需求解析 → 代码生成 → 质量门禁 → 测试执行 → 最终报告）
3. **Skills 系统**：5 个内置 Skills（意图识别准确率 100%）

**核心创新点**（12 天内完成）：

1. **Self-Healing RCA**：三层智能根因分析
   - 错误分类（SYNTAX/LOGIC/DEPENDENCY/RUNTIME/TIMEOUT）
   - 追溯链路（代码 → Phase → Prompt → 需求）
   - 全局学习（跨项目错误模式库）

2. **LLM-as-a-Judge (Phase 9.5)**：5 维度代码质量评审
   - Readability / Architecture / Security / Performance / Maintainability
   - Overall Score: 86.6/100 + 10 条改进建议

3. **Prompt Caching 优化**：
   - Cache Hit Rate: 80.5%
   - Cost Reduction: -60.7%
   - ROI: 270%（单次运行即回本）

4. **Multi-Agent Skills 系统**：
   - 意图识别准确率：100%
   - 自动路由 + Fallback 机制

5. **EventBus 事件驱动**：
   - 全链路事件追踪
   - 实时进度监控
   - 性能分析

**量化成果**：
- 代码量：52,397 行 Python
- 测试：135 个用例，95.7% 通过率
- 工具：30+ 注册工具
- 开发效率：12 天完成 8 个重大功能

---

## 7. 风险与缓解

### 7.1 并行执行一致性风险

**风险**：Phase 4/5 并行后，文件生成顺序、共享上下文和失败重试可能导致结果不稳定。

**缓解**：
- 以文件级 task 为最小并行单元，保持每个 task 输入独立
- 增加 `max_concurrency` 配置，默认保守并发
- EventBus 记录 file.started / file.completed / file.failed，便于定位单文件失败
- final_report 输出并行统计和失败明细

### 7.2 向量检索质量风险

**风险**：向量数据库如果召回不准，可能给 Phase 4/9/9.5 注入噪声上下文。

**缓解**：
- 先用 ChromaDB 做 MVP，控制集成复杂度
- 对 source/test/design/spec/change artifacts 分集合索引
- top-k 默认较小，并保留关键词过滤和路径过滤
- 用固定 golden case 验证召回是否能提升代码生成和自愈效果

### 7.3 Archive 生命周期一致性风险

**风险**：Archive 如果只移动文件而不更新 traceability，会造成规范、代码、测试、报告之间断链。

**缓解**：
- Archive 必须同时更新 Change 状态、主规范、ArtifactGraph 和 coverage matrix
- `archive_change(change_id)` 先校验 tasks/spec/report 完整性
- final_report 明确输出归档状态和 traceability 覆盖率

### 7.4 AI-agnostic 协作边界风险

**风险**：Claude Code / Cursor / Cline 等工具协作时，如果边界不清晰，可能绕过 OpenSpec 规范和验证链路。

**缓解**：
- 明确 propose-only 只生成 change artifacts，不直接改代码
- apply-only 必须基于 change artifacts 执行实现、验证和测试
- 为不同工具提供规则模板，统一输入输出契约
- `/opsx:validate` 作为外部修改后的强制校验入口

### 7.5 时间风险

**风险**：架构能力优先后，总工期从短期面试准备扩展为约 19 天。

**缓解**：
- 按 Phase A-E 分段验收，每一阶段都可独立展示
- 文档和架构图放到最后统一更新，减少返工
- 若面试提前，可先展示已完成 8 大核心能力和 Phase A/B 的阶段成果

---

## 8. 成功指标

| 指标 | 目标 | 验证方式 | 状态 |
|------|------|----------|:----:|
| ~~Phase 4 tool loop 修复~~ | ~~100%~~ | ~~Anthropic 多轮 tool loop 稳定退出~~ | ✅ **已完成** |
| ~~EventBus 项目名称修复~~ | ~~100%~~ | ~~事件日志写入正确项目目录~~ | ✅ **已完成** |
| Phase 4/5 并行执行 | 耗时下降 30%+ | 串行 vs 并行 golden case 对比 | 🔄 P0 |
| 并行任务可观测性 | 100% | EventBus + final_report 输出文件级事件和统计 | 🔄 P0 |
| 向量数据库索引覆盖 | source/test/design/spec/change artifacts | ChromaDB collection + 检索用例验证 | 🔄 P0 |
| 语义检索有效性 | top-k 可用于 Phase 4/9/9.5 | prompt 注入记录 + 生成质量对比 | 🔄 P0 |
| Self-Healing 相似错误召回 | 可召回历史错误和修复策略 | 构造重复错误 golden case | 🔄 P0 |
| Archive 生命周期闭环 | PROPOSED → IMPLEMENTED → ARCHIVED | `archive_change(change_id)` E2E 验证 | 🔄 P1 |
| Traceability 覆盖矩阵 | Requirement → Code → Test → Report | final_report coverage matrix | 🔄 P1 |
| AI-agnostic propose/apply | 外部工具可协作 | propose-only / apply-only / validate 流程验证 | 🔄 P1 |
| 最终文档和架构图 | 与真实实现一致 | README + 架构图 + 面试稿审查 | 🔄 P2 |

---

## 9. 总结

### 9.1 核心成就

- ✅ 8 个核心亮点已实现：LLM-as-a-Judge、Prompt Caching、Skills、Self-Healing RCA、EventBus、OpenSpec Changes、LanguagePlugin、多 Provider
- ✅ **Phase 4 tool loop 问题已修复**（2026-05-28，commit 2dba89d）
- ✅ **EventBus unknown_project 问题已修复**（2026-05-28）
- ✅ 多Agent架构评估已完成，明确保持单Agent + Skills，不做完整多Agent重构
- ✅ 下一阶段路线已调整为架构能力优先，而不是先写最终文档

### 9.2 最新进展（2026-05-28）

**已完成**：
- ✅ Phase 4 tool loop 修复
  - 修复 Anthropic provider 的多轮 tool loop 处理
  - 解决文件跳过循环和无限重试问题
  - 恢复稳定的迭代 tool-use 行为

- ✅ EventBus 项目名称修复
  - 事件日志现在写入正确的项目目录
  - 不再写入 `unknown_project/.spec/events.jsonl`
  - EventBus 可作为 Demo 8 的稳定观测能力

- ✅ 架构路线重新排序
  - 并行工具调用：P0
  - 向量数据库：P0
  - Archive + Traceability：P1
  - AI-agnostic 协作：P1
  - 最终文档和架构图：P2

**待完成**：
- 🔄 Phase A：Phase 4/5 并行工具调用优化（Day 1-2）
- 🔄 Phase B：向量数据库集成（Day 3-5）
- 🔄 Phase C：Archive + Traceability 生命周期闭环（Day 6-9）
- 🔄 Phase D：AI-agnostic 协作模式（Day 10-16）
- 🔄 Phase E：最终文档、架构图和面试材料（Day 17-19）

### 9.3 下一步行动

**Phase A（Day 1-2）**：
1. 设计 Phase 4/5 文件级 task 拆分
2. 实现 asyncio 并行执行和 `max_concurrency`
3. 接入 EventBus 文件级事件
4. 在 final_report 输出并行统计

**Phase B（Day 3-5）**：
1. 集成 ChromaDB MVP
2. 建立 source/test/design/spec/change artifacts 索引
3. 提供语义搜索 API
4. 接入 Phase 4/9/9.5 和 Self-Healing

**Phase C（Day 6-9）**：
1. 实现 `archive_change(change_id)`
2. 合并 delta 到 `openspec/specs/main.md`
3. 扩展 ArtifactGraph 和 coverage matrix

**Phase D（Day 10-16）**：
1. 实现 propose-only / apply-only
2. 补充 Claude Code / Cursor / Cline 协作规则
3. 完成 `/opsx:*` 协作命令说明和验证

**Phase E（Day 17-19）**：
1. 更新 README、架构文档、面试稿
2. 补齐最终架构图
3. 整理演示脚本、Q&A 和端到端验证记录

**预计架构能力完成**：2026-06-16  
**预计最终文档和面试材料完成**：2026-06-19

### 9.4 差异化优势

**vs OpenSpec**：
- OpenSpec 强在规范协作、变更隔离、AI-agnostic
- DevPalAgent 强在端到端自动生成、质量门禁、测试执行、自愈、Prompt Caching、EventBus
- 下一阶段通过 Archive + AI-agnostic 协作补齐 OpenSpec 生命周期和外部工具协作能力

**vs 其他 Agent 框架**：
- LangChain/AutoGPT：通用 Agent 框架，缺少 SDLC 专用规范、验证和归档闭环
- DevPalAgent：Spec-first + 11 阶段 + Skills + Quality Gate + Traceability + EventBus + Vector Retrieval + Archive Lifecycle

---

## 10. 架构决策记录（ADR）

### ADR-001: 单Agent + Skills vs 多Agent架构

**日期**：2026-05-28  
**状态**：已决策  
**决策**：保持单Agent + Skills架构，不重构为多Agent

**背景**：
- 评估了多Agent架构的必要性
- 分析了当前架构的优劣势
- 对比了三种架构模式

**决策理由**：

1. **场景匹配**（⭐⭐⭐⭐⭐）
   - DevPalAgent 是确定性工作流（需求→代码→测试）
   - 不需要多Agent的开放式探索能力
   - 单Agent + Skills 最适合当前场景

2. **成本优化**（⭐⭐⭐⭐⭐）
   - 单Agent 可以利用 Prompt Caching（成本降低 60.7%）
   - 多Agent 会失去这个优势
   - 预计成本增加 2-3 倍

3. **架构评分**（⭐⭐⭐⭐⭐）
   - 当前架构：8.3/10
   - 多Agent架构：6.8/10
   - 当前架构优于多Agent

4. **复杂度控制**（⭐⭐⭐⭐⭐）
   - 多Agent 会引入分布式系统复杂性
   - 调试困难度增加 5-10 倍
   - 维护成本增加 5-10 倍

5. **Skills 系统已足够**（⭐⭐⭐⭐⭐）
   - 已实现意图识别、任务路由、协作编排
   - 5 个 Skills，100% 准确率
   - 满足当前所有需求

**必要性评分**：3/10（低必要性）

**后果**：
- ✅ 保持架构简单性
- ✅ 保持成本优势
- ✅ 保持可控性和可调试性
- ⚠️ 部分场景性能受限（可通过并行工具调用优化）

**替代方案**：
- 方案A：保持单Agent + 强化Skills（✅ 已选择）
- 方案B：混合架构（备选，特定场景使用）
- 方案C：完全重构为多Agent（❌ 不推荐）

**参考文档**：
- [multi_agent_architecture_assessment_2026-05-24.md](multi_agent_architecture_assessment_2026-05-24.md)
---

### ADR-002: 向量数据库选型

**日期**：2026-05-28  
**状态**：建议决策，待 POC 验证  
**决策**：优先采用 ChromaDB 作为 MVP 向量数据库

**背景**：
- 需要增强代码检索和语义搜索能力
- 需要优化 Self-Healing 错误匹配
- 需要改进 LLM Context 选择

**候选方案**：

**方案A：ChromaDB**（推荐）⭐⭐⭐⭐⭐
- 优势：轻量级、易集成、Python 原生
- 劣势：功能相对简单
- 适用场景：快速原型、中小规模

**方案B：Qdrant**⭐⭐⭐⭐
- 优势：高性能、支持过滤、Rust 实现
- 劣势：部署复杂度高
- 适用场景：大规模、高性能需求

**方案C：Weaviate**⭐⭐⭐
- 优势：功能丰富、支持多模态
- 劣势：资源占用高、学习曲线陡
- 适用场景：复杂场景、多模态需求

**评估维度**：
| 维度 | ChromaDB | Qdrant | Weaviate |
|------|--------|--------|----------|
| 易用性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| 性能 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 功能 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 资源占用 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 社区 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

**推荐**：ChromaDB（快速集成，满足当前需求）

**后续行动**：
1. 完成 POC 验证
2. 性能测试
3. 最终决策

---

### ADR-003: 并行策略选择

**日期**：2026-05-28  
**状态**：建议决策，待性能测试验证  
**决策**：优先采用 asyncio 实现 Phase 4/5 文件级并行

**背景**：
- Phase 4/5 可以并行生成文件
- 需要提升性能 2-3 倍
- 需要保持架构简单性

**候选方案**：

**方案A：asyncio 并行**（推荐）⭐⭐⭐⭐⭐
```python
async def generate_files_parallel(files: List[str]):
    tasks = [generate_file(f) for f in files]
    results = await asyncio.gather(*tasks)
    return results
```
- 优势：Python 原生、简单、易调试
- 劣势：受 GIL 限制（但 LLM 调用是 I/O 密集型）

**方案B：multiprocessing 并行**⭐⭐⭐
```python
from multiprocessing import Pool
def generate_files_parallel(files: List[str]):
    with Pool(processes=4) as pool:
        results = pool.map(generate_file, files)
    return results
```
- 优势：真正并行、不受 GIL 限制
- 劣势：进程间通信复杂、资源占用高

**方案C：ThreadPoolExecutor**⭐⭐⭐⭐
```python
from concurrent.futures import ThreadPoolExecutor
def generate_files_parallel(files: List[str]):
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(generate_file, files))
    return results
```
- 优势：简单、资源占用低
- 劣势：受 GIL 限制

**推荐**：asyncio（最适合 LLM I/O 密集型任务）

**后续行动**：
1. 实现 asyncio 版本
2. 性能测试
3. 与串行版本对比

---

## 11. 技术债务清单

### 已关闭技术债务

| 债务项 | 原影响 | 状态 | 说明 |
|--------|--------|:----:|------|
| Phase 4 文件跳过循环 | 高 - 阻塞后续阶段 | ✅ 已关闭 | Anthropic provider 多轮 tool loop 已修复 |
| EventBus 项目名称问题 | 低 - 日志位置不正确 | ✅ 已关闭 | 事件日志已写入正确项目目录 |

### 高优先级技术债务（P0）

| 债务项 | 影响 | 优先级 | 预计工期 |
|--------|------|--------|---------|
| Phase 4/5 串行执行 | 高 - 主流程性能受限，无法体现单Agent并行能力 | P0 | 1-2 天 |
| 缺少向量数据库 | 高 - 缺少语义检索、上下文选择和历史错误召回 | P0 | 2-3 天 |

### 中优先级技术债务（P1）

| 债务项 | 影响 | 优先级 | 预计工期 |
|--------|------|--------|---------|
| 缺少 Archive 机制 | 中 - OpenSpec Change 生命周期未闭环 | P1 | 3-4 天 |
| 缺少 AI-agnostic 协作 | 中 - 尚不能很好服务 Claude Code / Cursor / Cline 等外部工具 | P1 | 5-7 天 |
| 缺少端到端架构能力验证 | 中 - 新能力需要统一 golden case 验证 | P1 | 1-2 天 |

### 低优先级技术债务（P2/P3）

| 债务项 | 影响 | 优先级 | 预计工期 |
|--------|------|--------|---------|
| 文档和架构图滞后 | 中 - 需要等架构能力落地后统一更新 | P2 | 1-2 天 |
| 面试 Q&A 未覆盖新能力 | 中 - 需要补充并行、向量库、Archive、AI-agnostic 话术 | P2 | 1 天 |
| 缺少多维度质量趋势评分 | 低 - Phase 9.5 已有基础评分，趋势化可后置 | P3 | 2-3 天 |
| Skills 生态扩展不足 | 低 - 当前 5 个 Skills 已覆盖核心场景 | P3 | 2-3 天 |
| 缺少混合 AgentPool 架构 | 极低 - 当前明确不实施完整多Agent | P4 | 暂不排期 |

---

## 12. 面试准备清单（更新）

### 核心技术亮点（8 个已完成 + 4 个架构能力待补齐）

**已完成核心亮点**（8 个）：
1. ✅ LLM-as-a-Judge（5 维度评审）
2. ✅ Prompt Caching（80.5% hit rate，-60.7% cost）
3. ✅ Multi-Agent Skills（单Agent内的意图识别、路由和协作编排）
4. ✅ Self-Healing RCA（三层根因分析）
5. ✅ EventBus（全链路可观测性）
6. ✅ OpenSpec Changes（变更管理基础能力）
7. ✅ LanguagePlugin（统一多语言扩展架构）
8. ✅ 多LLM Provider（Anthropic + OpenAI + Fallback）

**下一阶段必须补齐的架构能力**（4 个）：
9. 🔄 并行工具调用（P0）：Phase 4/5 文件级并行，提升单Agent主流程性能
10. 🔄 向量数据库（P0）：语义搜索、上下文选择、历史错误召回
11. 🔄 Archive + Traceability（P1）：OpenSpec Change 生命周期闭环
12. 🔄 AI-agnostic 协作（P1）：服务 Claude Code / Cursor / Cline 等外部 AI coding 工具

### 架构决策亮点（4 个）

1. ✅ **单Agent + Skills，而不是完整多Agent**
   - 多Agent必要性：3/10
   - 当前架构评分：8.3/10
   - 完整多Agent评分：6.8/10
   - 核心理由：确定性 SDLC workflow 更适合单Agent编排，成本更低，调试更简单，Prompt Caching 收益更稳定

2. 🔄 **先并行工具调用，而不是 AgentPool**
   - 推荐：asyncio + 文件级 task + `max_concurrency`
   - 理由：瓶颈来自 LLM I/O 和文件生成串行，不需要引入完整多Agent分布式复杂度

3. 🔄 **先 ChromaDB MVP，而不是重型向量平台**
   - 候选：ChromaDB / Qdrant / Weaviate
   - 推荐：ChromaDB
   - 理由：Python 原生、轻量、适合先验证语义检索和 Self-Healing 召回价值

4. 🔄 **先补生命周期和协作协议，再做最终文档**
   - Archive 解决 OpenSpec Change 归档闭环
   - AI-agnostic 解决外部 AI coding 工具协作边界
   - 文档和架构图放到最后，确保描述真实系统而不是规划稿

### 面试话术（架构决策）

**Q: 为什么不直接改成完整多Agent架构？**

**A**：
> "我做过完整评估，结论是 DevPalAgent 当前不适合直接重构成完整多Agent。它的核心场景是 Spec-first SDLC workflow，本质是确定性的 11 阶段工程流水线，不是开放式探索任务。完整多Agent会带来调度、状态同步、成本和调试复杂度，而且会削弱 Prompt Caching 的收益。  
>  
> 所以我选择单Agent + Skills：Skills 负责意图识别、任务路由和专业能力封装；主 workflow 保持确定性和可追踪。评估结果是当前架构 8.3/10，完整多Agent 6.8/10，多Agent必要性只有 3/10。下一步不是堆 Agent 数量，而是补齐并行执行、向量检索、Archive 和 AI-agnostic 协作这些真正提升系统可用性的能力。"

**亮点**：
- ✅ 展示架构决策能力
- ✅ 展示成本意识
- ✅ 展示工程权衡思维
- ✅ 展示不是盲目追热点，而是按场景选择架构
- ✅ 展示量化评估能力（8.3/10、6.8/10、3/10）

**Q: 为什么并行工具调用优先级高于继续扩展 Skills？**

**A**：
> "当前 5 个 Skills 已经覆盖核心场景，继续扩展 Skills 属于能力丰富度提升；但 Phase 4/5 串行执行直接影响主链路性能和用户体验。并行工具调用可以在不改变单Agent架构的情况下，把文件生成和测试生成拆成独立任务并发执行，这是投入产出比最高的性能优化。  
>  
> 技术上我会优先用 asyncio，因为 LLM 调用是 I/O 密集型；同时加 `max_concurrency`、文件级 EventBus 事件和 final_report 统计，保证性能提升的同时仍然可观测、可调试。"

**Q: 向量数据库在这个系统里解决什么问题？**

**A**：
> "向量数据库不是为了追技术栈，而是补单Agent的长期上下文能力。DevPalAgent 会产生 requirements、design、spec、code、test、report、error memory 等 artifacts，仅靠关键词检索很难找到语义相关内容。  
>  
> 集成 ChromaDB 后，可以支持三类能力：第一，Phase 4 生成代码时检索相关设计和已有代码；第二，Phase 9/9.5 做质量检查时检索相关测试和规范；第三，Self-Healing 遇到错误时召回相似历史错误和修复策略。这会提升生成质量，也会让自愈更像工程经验复用。"

**Q: Archive + Traceability 为什么重要？**

**A**：
> "OpenSpec Change 不能只停留在 proposal/spec/tasks 阶段。真正工程化需要生命周期闭环：一个 change 从 PROPOSED 到 IMPLEMENTED，最后归档为 ARCHIVED，同时把 delta 合并到主规范，并保留 Requirement → Code → Test → Report 的追踪关系。  
>  
> 所以 Archive 机制不是整理文件，而是让规范、代码、测试和报告之间的证据链长期可追溯。面试里这能体现我不是只做代码生成，而是在做可审计、可演进的 Agentic SDLC Runtime。"

**Q: AI-agnostic 协作模式的价值是什么？**

**A**：
> "我不希望 DevPalAgent 绑定某一个 AI coding 工具。AI-agnostic 协作的目标是让 Claude Code、Cursor、Cline 都能围绕同一套 OpenSpec artifacts 协作。  
>  
> 具体会拆成 propose-only 和 apply-only：propose-only 只生成 change artifacts，不直接改代码；apply-only 基于已有 change artifacts 执行实现、验证、测试和归档。这样外部 AI 工具可以参与编辑，但 DevPalAgent 保留规范、验证和 traceability 的控制权。"

### 最终材料更新顺序

1. 先完成 Phase A-D 架构能力实现和验证
2. 再更新 README、`doc3.0/agent_architecture.md`、`doc3.0/interview_pitch_0525.md`
3. 最后补架构图：系统总览、并行执行、向量检索、Archive 生命周期、AI-agnostic 协作
4. 面试材料以真实实现为准，不提前把规划能力写成已完成能力

---

**文档版本**：v8.0（架构能力优先版）
