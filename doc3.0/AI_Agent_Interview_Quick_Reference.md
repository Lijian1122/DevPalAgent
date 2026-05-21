# AI Agent 面试快速参考卡

**字节、腾讯、阿里核心考点速查**  
**日期**: 2026-05-20

---

## 🎯 三家公司一句话总结

| 公司 | 核心考察 | 一句话 |
|---|---|---|
| **字节** | 技术深度 | 不考概念，专挖工程细节，必须有生产级经验 |
| **腾讯** | 协议生态 | 侧重 Workflow vs Agent、MCP、Memory 系统设计 |
| **阿里** | 全面架构 | 必画 Multi-Agent 三层架构，追问落地瓶颈 |

---

## 字节跳动核心考点

### 1. ReAct 消息格式
```python
# ✅ 正确：tool_response 用 user 角色
{"role": "user", "content": "tool_response: ..."}  # 外部反馈

# ❌ 错误：tool_response 用 assistant 角色
# 会导致模型混淆
```

### 2. Agent 训练三阶段
| 阶段 | 目的 | 方法 |
|---|---|---|
| Instruct Tuning | 基础指令遵循 | SFT |
| SFT | Agent 特定能力 | 工具调用数据 |
| RL | 优化决策质量 | PPO/DPO |

### 3. 死循环检测
```python
# 方法 1: 迭代次数限制（最简单）
max_iterations = 10

# 方法 2: 模式检测（连续 3 次相同调用）
if recent_calls[-3:] == [same_call] * 3:
    terminate()

# 方法 3: 状态检测（回到之前的状态）
if current_state in history[-5:]:
    terminate()
```

### 4. 工具调用优化
- Memory 记录已调用结果
- Tool Cache 缓存结果
- System Prompt 明确避免重复
- Few-shot Examples

---

## 腾讯核心考点

### 1. Workflow vs Agent

| 维度 | Workflow | Agent |
|---|---|---|
| 控制流 | 固定有向图 | 自主决策 |
| 灵活性 | 低 | 高 |
| 成本 | 低 | 高 |
| 适用 | 流程固定 | 任务复杂 |

**最佳实践**: 组合使用
- 简单任务 → Workflow（快速可靠）
- 复杂任务 → Agent（灵活智能）

### 2. MCP 协议

**解决的问题**:
- 工具集成混乱
- 重复开发
- 维护困难

**架构**:
```
LLM App → MCP Client → MCP Server → Tools
```

### 3. A2A 通信

| 模式 | 适用场景 |
|---|---|
| 直接通信 | 简单协作 |
| 消息队列 | 解耦、高并发 |
| 共享内存 | 需要共享上下文 |
| 协调器 | 复杂协作 |

### 4. Memory 系统

**三层架构**:
- Short-term: 对话上下文（8K tokens）
- Long-term: 持久化记忆（按需检索）
- Error Memory: 错误记忆（警告提示）

**上下文超限**:
- 滑动窗口（主策略）⭐⭐⭐⭐⭐
- LLM 摘要（成本高）⭐⭐⭐
- 向量检索（需要向量库）⭐⭐⭐⭐

---

## 阿里巴巴核心考点

### 1. Tools / Workflow / Agent 区别

| 维度 | Tools | Workflow | Agent |
|---|---|---|---|
| 定义 | 单个函数 | 固定流程 | 自主决策 |
| 复杂度 | 低 | 中 | 高 |
| 灵活性 | 无 | 低 | 高 |
| 成本 | 极低 | 低 | 高 |

### 2. Multi-Agent 三层架构

```
┌─────────┐
│  路由层      │ 意图识别、任务分发
└──────┬──────┘
┌──────┴──────┐
│  管理层      │ 任务分解、协调、聚合
└──────┬──────┘
┌──────┴──────┐
│  执行层      │ Planner / Executor / Reflector
└───────────┘
```

### 3. 防死锁策略

```python
# 1. 超时机制
timeout = 30  # 30 秒超时

# 2. 资源锁
resource_locks = {}

# 3. 循环依赖检测
detect_cycle()  # 拓扑排序
```

### 4. 结果聚合

| 方法 | 说明 |
|---|---|
| 投票 | 选择多数结果 |
| 仲裁 | 高优先级决定 |
| 合并 | 组合所有结果 |
| 加权 | 按可信度加权 |

---

## 通用必备知识

### Agent 核心组件
```
Agent = Perception + Planning + Action + Memory + Reflection
```

### Agent 设计模式

**ReAct**:
```
while not done:
    Thought → Action → Observation
```

**Plan-and-Execute**:
```
Plan → Execute → (Re-plan if failed)
```

**Reflexion**:
```
Attempt → Reflect → Refine
```

### Agent 评估指标

| 指标 | 说明 |
|---|---|
| Success Rate | 任务成功率 |
| Efficiency | 平均步数 |
| Cost | Token 消耗 |
| Reliability | 1 - 错误率 |
| Latency | 响应时间 |

---

## DevPalAgent 项目介绍模板

```
DevPalAgent 是一个 Spec-first Agentic SDLC Runtime。

核心特点：
1. 三层 Agent 架构：Planner → Executor → Reflector
2. 11 阶段 OpenSpec Workflow
3. 三层 Memory 系统：Short/Long/Error
4. 自愈能力：错误检测 → 自动修复

技术栈：
- LLM: Claude Opus 4.7
- 工具: MCP 协议
- 测试: pytest

实战成果：
- 成功生成 10+ 完整项目
- 代码质量评分 8.5/10
- 自愈成功率 85%
```

---

## 高频问题 30 秒回答

### Q: "tool_response 为什么用 user 角色？"
**A**: Tool response 是外部系统的反馈，不是 Agent 自己生成的。用 user 角色表示"来自外部的输入"，避免模型混淆自己的输出和外部反馈。

### Q: "如何检测 Agent 死循环？"
**A**: 三种方法：1) 迭代次数限制（最简单）；2) 模式检测（连续 3 次相同调用）；3) 状态检测（回到之前的状态）。DevPalAgent 采用组合策略。

### Q: "Workflow 和 Agent 有什么区别？"
**A**: Workflow 是固定控制流，适合流程明确的任务；Agent 是自主决策，适合复杂任务。最佳实践是组合使用：简单任务用 Workflow，复杂任务用 Agent。

### Q: "上下文超限怎么办？"
**A**: 不用 LLM 压缩（成本高、延迟大）。采用滑动窗口截断 Short-term，Long-term 按需检索 top-k。简单高效，零成本。

### Q: "如何防止 Multi-Agent 死锁？"
**A**: 三层防护：1) 超时机制（30 秒）；2) 资源锁管理；3) 循环依赖检测（拓扑排序）。

### Q: "Agent 如何聚合多个结果？"
**A**: 四种方法：1) 投票（选多数）；2) 仲裁（高优先级）；3) 合并（组合所有）；4) 加权（按可信度）。根据任务类型选择。

### Q: "如何保证代码质量？"
**A**: 五层保障：1) 多阶段验证（生成→审查→测试）；2) 静态分析（pylint/bandit）；3) 动态测试（pytest，覆盖率 > 80%）；4) 人工审核（关键代码）；5) 持续改进（Error Memory）。

### Q: "项目落地最大挑战是什么？"
**A**: 三个挑战：1) LLM 成本高（解决：缓存 + 小模型，降低 60%）；2) 工具调用不稳定（解决：Schema 验证 + 重试）；3) 结果不可控（解决：输出验证 + 人工审核）。

---

## 面试技巧

### STAR 法则
- **S**ituation: 项目背景
- **T**ask: 你的任务
- **A**ction: 你的行动
- **R**esult: 最终结果（带数据）
### 主动引导
回答时主动提到准备好的内容：
"这个问题让我想到 DevPalAgent 项目中的一个案例..."

### 展示思考
不只给答案，要展示思考过程：
"我会从三个维度分析：成本、延迟、质量..."

---

## 准备清单

### 字节跳动
- [ ] ReAct 代码示例
- [ ] 训练流程图
- [ ] 死循环检测案例
- [ ] 工具优化数据对比

### 腾讯
- [ ] Workflow vs Agent 对比表
- [ ] MCP 架构图
- [ ] A2A 通信代码
- [ ] Memory 三层架构图

### 阿里巴巴
- [ ] Tools/Workflow/Agent 对比表
- [ ] Multi-Agent 三层架构图
- [ ] 防死锁代码示例
- [ ] 项目落地案例

### 通用
- [ ] 项目经验整理（STAR 格式）
- [ ] 5 张必备架构图
- [ ] 5 段核心代码（能手写）
- [ ] 8 个高频问题 30 秒回答

---

**准备人**: Claude Opus 4.7  
**准备日期**: 2026-05-20  
**打印建议**: 双面打印，面试前快速复习

祝你面试顺利！🎉
