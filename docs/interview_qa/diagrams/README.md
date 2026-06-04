# Architecture Diagrams Index

## DevPalAgent 架构图索引

本目录包含 DevPalAgent 的 5 个核心架构图，采用 Mermaid 格式，可在 GitHub、支持 Mermaid 的 Markdown 编辑器或面试演示中直接渲染。

---

## 架构图列表

### 1. [System Architecture](./01_system_architecture.md)
**系统整体架构图**

**内容**:
- 8 层架构设计（UI → Agent → OpenSpec → Phase → Multi-Agent → Services → Memory → Storage）
- 双链路：Agent 链路（Plan-Act-Reflect）+ OpenSpec 链路（11-Phase Pipeline）
- 核心组件：Scheduler、Multi-Agent Coordinator、EventBus、Memory System
- 数据流：User Request → Planner → Executor → OpenSpec → Multi-Agent → Quality Gate → Final Report

**适用场景**:
- 整体架构讲解
- 系统设计面试
- 技术选型说明

---

### 2. [OpenSpec 11-Phase Pipeline](./02_openspec_pipeline.md)
**OpenSpec 11 阶段流程图**

**内容**:
- 11 个阶段完整流程：Parse → Structure → Design → Code → Test → Validate → Report
- Phase Skip Rules：installer/tooling/python 项目智能跳过
- Multi-Agent 并行：Phase 4/5 支持 4-16 agents
- Checkpoint & Resume：3 个关键断点
- Self-Healing 流程：Quality Gate 失败 → Root Cause Analysis → Auto-Fix

**适用场景**:
- 工作流设计讲解
- 确定性流程说明
- 容错机制演示

---

### 3. [Multi-Agent Architecture](./03_multi_agent.md)
**多智能体并行执行架构图**

**内容**:
- 依赖分析 → 拓扑排序 → 分阶段执行
- Agent Pool Manager：4-16 agents 动态分配
- Message Bus：Command Queue + Result Queue
- Shared Resources：Prompt Cache 共享
- Fault Tolerance：Retry Policy + Circuit Breaker
- 性能对比：顺序 vs 并行，3.3x 加速

**适用场景**:
- 并行计算讲解
- 性能优化说明
- 分布式协调演示

---

### 4. [Quality Gate Validation](./04_quality_gate.md)
**Quality Gate 四层验证流程图**

**内容**:
- L1: FORMAT → L2: SEMANTIC → L3: PARSER → L4: BUSINESS
- 早失败机制：L1 失败直接终止
- Self-Healing 集成：CRITICAL 问题触发自动修复
- Critique Phase 集成：LLM 深度审查
- Quality Report 示例：PASS / FAIL 报告格式

**适用场景**:
- 质量保障体系讲解
- 静态分析说明
- 验证流程演示

---

### 5. [EventBus Architecture](./05_eventbus.md)
**EventBus 事件驱动架构图**

**内容**:
- Pub-Sub 模式：Publishers → EventBus → Subscribers
- 事件类型：Workflow Events, Phase Events, Agent Events, Tool Events
- 监控器：Progress Monitor, Performance Analyzer, Error Tracker
- 外部集成：Datadog, Slack, Prometheus
- 事件存储：JSONL 持久化 + Query API

**适用场景**:
- 事件驱动架构讲解
- 可观测性设计说明
- 监控告警演示

---

## 使用指南

### 在线查看

1. **GitHub**: 直接在 GitHub 仓库中查看，Mermaid 自动渲染
2. **VS Code**: 安装 [Markdown Preview Mermaid Support](https://marketplace.visualstudio.com/items?itemName=bierner.markdown-mermaid) 插件
3. **在线编辑器**: 
   - [Mermaid Live Editor](https://mermaid.live/)
   - [StackEdit](https://stackedit.io/)

### 导出图片（面试演示用）

使用 Mermaid CLI 导出 PNG/SVG：

```bash
# 安装 mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# 导出 PNG
mmdc -i 01_system_architecture.md -o system_architecture.png

# 导出 SVG
mmdc -i 02_openspec_pipeline.md -o openspec_pipeline.svg

# 批量导出
for f in *.md; do
    mmdc -i "$f" -o "${f%.md}.png"
done
```

### 嵌入演示文稿

1. **导出为图片**: 使用上述命令导出 PNG
2. **插入 PPT**: 将 PNG 插入 PowerPoint/Keynote
3. **在线演示**: 上传到 GitHub 并分享链接

---

## 架构图特点

### 设计原则

1. **分层清晰**: 每个架构图都有明确的分层结构
2. **颜色编码**: 不同组件类型使用不同颜色
3. **数据流**: 箭头明确标注数据流向
4. **注释完整**: 关键节点有详细说明

### 技术亮点

每个架构图都突出 DevPalAgent 的核心亮点：
- **01_system_architecture**: 双链路架构、8层设计
- **02_openspec_pipeline**: 确定性流程、Checkpoint/Resume
- **03_multi_agent**: 3.3x 并行加速、12x 综合效率提升
- **04_quality_gate**: 四层验证、Self-Healing 集成
- **05_eventbus**: Pub-Sub 解耦、完整可观测性

---

## 面试使用建议

### 15 分钟面试

**推荐组合**: 01 + 02
- 先展示整体架构（01）：3 分钟
- 再展示核心流程（02）：7 分钟
- 留 5 分钟答疑

### 30 分钟面试

**推荐组合**: 01 + 02 + 03
- 整体架构（01）：5 分钟
- OpenSpec 流程（02）：10 分钟
- Multi-Agent 并行（03）：10 分钟
- 答疑：5 分钟

### 45 分钟+ 面试

**推荐组合**: 全部 5 个
- 整体架构（01）：8 分钟
- OpenSpec 流程（02）：10 分钟
- Multi-Agent 并行（03）：10 分钟
- Quality Gate（04）：8 分钟
- EventBus（05）：7 分钟
- 答疑：2 分钟

### 演示顺序

**推荐顺序**: 01 → 02 → 03 → 04 → 05

**逻辑线**:
1. 整体架构（全景）
2. OpenSpec 流程（核心）
3. Multi-Agent 并行（性能）
4. Quality Gate（质量）
5. EventBus（可观测）

**故事线**:
"DevPalAgent 采用双链路架构（01），核心是 OpenSpec 11-Phase 流程（02），其中 Phase 4/5 支持多智能体并行执行（03），生成的代码通过 Quality Gate 四层验证（04），整个过程通过 EventBus 实现完整可观测（05）。"

---

## 配套文档

每个架构图都有对应的详细 Q&A 文档：

| 架构图 | 对应 Q&A 文档 |
|-------|----------|
| 01_system_architecture | [interview_qa_architecture.md](../interview_qa_architecture.md) |
| 02_openspec_pipeline | [interview_qa_11phase_pipeline.md](../interview_qa_11phase_pipeline.md) |
| 03_multi_agent | *包含在 interview_qa_architecture.md 中* |
| 04_quality_gate | [interview_qa_quality_gate.md](../interview_qa_quality_gate.md) |
| 05_eventbus | [interview_qa_eventbus.md](../interview_qa_eventbus.md) |

**建议**: 先看架构图理解整体结构，再读 Q&A 文档深入技术细节。

---

## 文件清单

```
docs/interview_qa/diagrams/
├── README.md               # 本文件
├── 01_system_architecture.md      # 系统整体架构图
├── 02_openspec_pipeline.md        # OpenSpec 11-Phase 流程图
├── 03_multi_agent.md           # 多智能体并行架构图
├── 04_quality_gate.md               # Quality Gate 验证流程图
└── 05_eventbus.md             # EventBus 事件驱动架构图
```

**总大小**: ~60KB Markdown + Mermaid

---

**创建日期**: 2026-06-04  
**最后更新**: 2026-06-04  
**版本**: v1.0  
**维护者**: DevPalAgent Team
