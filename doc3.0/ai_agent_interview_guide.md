# AI Agent 系统面试指南

> 本文档整理了 AI Agent 系统设计与工程实践中的核心面试问题，涵盖架构设计、核心组件、记忆系统、Function Calling、RAG 和工程稳定性等六大领域。

---

## 一、AI Agent 系统架构

### 1.1 入口层（Entry Layer）

**面试问题：请描述 AI Agent 系统的入口层职责和设计要点。**

**参考答案：**

入口层是用户与 Agent 系统交互的第一道关口，主要职责包括：

1. **请求接收与路由**
   - 接收来自多渠道的用户请求（Web、API、CLI、IDE 插件等）
   - 根据请求类型路由到对应的处理流程
   - 支持同步/异步请求模式

2. **身份认证与鉴权**
   - 用户身份验证（Token、OAuth、API Key）
   - 权限校验（RBAC、ABAC）
   - 请求频率限制（Rate Limiting）

3. **请求预处理**
   - 参数校验与标准化
   - 多模态输入处理（文本、图片、文件）
   - 上下文初始化

4. **协议适配**
   - HTTP/HTTPS、WebSocket、gRPC
   - 流式响应支持（SSE、WebSocket）

**设计要点：**
- 高可用：多实例部署 + 负载均衡
- 安全性：输入校验、防注入、敏感信息过滤
- 可观测：请求日志、链路追踪（Trace ID）

---

### 1.2 编排层（Orchestration Layer）

**面试问题：编排层在 Agent 系统中扮演什么角色？如何设计一个高效的编排引擎？**

**参考答案：**

编排层是 Agent 的"大脑"，负责任务分解、执行调度和流程控制。

**核心职责：**

1. **任务规划与分解**
   - 将复杂任务拆解为可执行的子任务
   - 构建任务依赖图（DAG）
   - 动态调整执行计划

2. **执行调度**
   - 任务队列管理
   - 并行/串行执行控制
   - 资源分配与负载均衡

3. **流程控制**
   - 条件分支（if-else）
   - 循环执行（while、for）
   - 异常处理与重试

4. **状态管理**
   - 任务状态追踪（pending、running、completed、failed）
   - 执行上下文传递
   - 检查点（Checkpoint）机制

**设计模式：**
- **工作流引擎**：基于 DAG 的任务编排（类似 Airflow）
- **状态机**：有限状态机（FSM）控制执行流程
- **事件驱动**：基于事件的异步编排

**DevPalAgent 实现：**
```python
# devpal/core/openspec_phases/ - 11 阶段工作流
Phase 1: 需求解析 → Phase 2: 架构设计 → ... → Phase 11: 最终报告
```

---

### 1.3 模型层（Model Layer）

**面试问题：如何设计一个支持多模型的 Agent 系统？**

**参考答案：**

模型层负责与 LLM 交互，需要考虑多模型支持、成本优化和可靠性。

**核心设计：**

1. **模型抽象接口**
   - 统一的 LLM 调用接口（支持 OpenAI、Claude、GLM 等）
   - 模型能力注册（支持 Function Calling、Vision、长上下文等）
   - 参数标准化（temperature、max_tokens、stop_sequences）

2. **模型路由策略**
   - 基于任务类型选择模型（简单任务用 Haiku，复杂任务用 Opus）
   - 成本优化（优先使用便宜模型，失败后升级）
   - 负载均衡（多实例、多区域部署）

3. **Prompt 管理**
   - Prompt 模板库
   - 版本控制与 A/B 测试
   - Prompt 缓存（减少重复计算）

4. **可靠性保障**
   - 重试机制（指数退避）
   - 超时控制
   - 降级策略（模型不可用时的备选方案）

**成本优化技巧：**
- 使用 Prompt Caching 减少重复 token 消耗
- 短上下文任务优先使用小模型
- 批量请求合并（Batch API）

---

### 1.4 工具层（Tool Layer）

**面试问题：如何设计一个可扩展的工具系统？**

**参考答案：**

工具层为 Agent 提供与外部系统交互的能力。

**核心设计：**

1. **工具注册与发现**
   - 工具元数据（name、description、parameters schema）
   - 动态工具加载
   - 工具分类（文件操作、网络请求、数据库查询等）

2. **工具执行引擎**
   - 参数校验与类型转换
   - 沙箱隔离（安全执行）
   - 超时控制与资源限制

3. **工具编排**
   - 工具链（Tool Chain）：多个工具串联执行
   - 并行工具调用
   - 条件工具选择

**DevPalAgent 工具示例：**
```python
# devpal/tools/
- file_tools.py: Read, Write, Edit
- search_tools.py: Glob, Grep
- bash_tools.py: Bash 命令执行
- web_tools.py: WebFetch, WebSearch
```


---

### 1.5 记忆层（Memory Layer）

**面试问题：请设计一个多层次的 Agent 记忆系统。**

**参考答案：**

记忆层是 Agent 的"大脑存储"，需要支持短期、长期和结构化记忆。

**三层记忆架构：**

1. **短期记忆（Short-term Memory）**
   - 当前会话上下文（滑动窗口）
   - 最近 N 轮对话
   - 存储：内存（Redis）

2. **中期记忆（Session Memory）**
   - 会话摘要（Summary）
   - 关键决策记录
   - 存储：Redis + 文件系统

3. **长期记忆（Long-term Memory）**
   - 用户画像（偏好、习惯）
   - 业务知识库
   - 历史交互记录
   - 存储：向量数据库 + 关系数据库

**DevPalAgent 记忆实现：**
```python
# devpal/memory/
- short_term.py: 当前上下文管理
- long_term.py: 持久化记忆
- error_memory.py: 错误记录与学习
```

---

### 1.6 观测层（Observability Layer）

**面试问题：如何设计 Agent 系统的可观测性？**

**参考答案：**

观测层提供系统运行状态的全面监控。
**核心指标：**

1. **日志（Logging）**
   - 结构化日志（JSON 格式）
   - 日志级别（DEBUG、INFO、WARN、ERROR）
   - 链路追踪（Trace ID）

2. **指标（Metrics）**
   - 请求量（QPS）
   - 延迟（P50、P95、P99）
   - 错误率
   - Token 消耗
   - 工具调用成功率

3. **追踪（Tracing）**
   - 分布式追踪（OpenTelemetry）
   - 调用链可视化
   - 性能瓶颈分析

4. **告警（Alerting）**
   - 错误率阈值告警
   - 延迟异常告警
   - 成本超支告警

**工具栈：**
- 日志：ELK（Elasticsearch + Logstash + Kibana）
- 指标：Prometheus + Grafana
- 追踪：Jaeger / Zipkin



---

## 二、Agent 核心组件

### 2.1 Planner（规划器）

**面试问题：请设计一个 Agent 的任务规划器，并说明如何处理复杂任务分解。**

**参考答案：**

Planner 负责将用户意图转化为可执行的任务计划。

**核心功能：**

1. **意图理解**
   - 用户需求解析
   - 目标提取
   - 约束条件识别

2. **任务分解**
   - 递归分解（大任务 → 子任务）
   - 依赖关系分析
   - 并行机会识别

3. **计划生成**
   - 生成任务 DAG
   - 资源估算（时间、成本）
   - 风险评估

**算法选择：**
- **ReAct**：Reasoning + Acting（推理与行动交替）
- **Chain-of-Thought**：思维链提示
- **Tree-of-Thoughts**：树状思维搜索

**DevPalAgent 实现：**
```python
# devpal/core/planner.py
class Planner:
    def plan(self, user_request: str) -> Plan:
        # 1. 理解需求
        intent = self.parse_intent(user_request)
      
        # 2. 分解任务
        tasks = self.decompose(intent)
        
        # 3. 构建 DAG
        dag = self.build_dag(tasks)
        
        return Plan(dag=dag, tasks=tasks)
```

---

### 2.2 Executor（执行器）

**面试问题：如何设计一个高效的任务执行器？**

**参考答案：**

Executor 负责执行 Planner 生成的任务计划。

**核心功能：**

1. **任务调度**
   - 按 DAG 顺序执行
   - 并行任务调度
   - 资源分配

2. **工具调用**
   - 参数准备
   - 工具执行
   - 结果解析

3. **状态管理**
   - 任务状态更新
   - 上下文传递
   - 中间结果缓存

4. **异常处理**
   - 重试机制
   - 降级策略
   - 回滚操作

**执行模式：**
- **同步执行**：等待任务完成
- **异步执行**：后台任务 + 回调
- **流式执行**：实时返回中间结果



---

### 2.3 Reflector（反思器）

**面试问题：为什么需要 Reflector？如何设计一个有效的反思机制？**

**参考答案：**

Reflector 负责评估执行结果，发现问题并优化后续行动。

**核心功能：**

1. **结果评估**
   - 任务完成度检查
   - 质量评分
   - 目标达成度分析

2. **问题诊断**
   - 错误根因分析
   - 性能瓶颈识别
   - 改进机会发现

3. **策略调整**
   - 计划修正
   - 参数优化
   - 工具选择调整

4. **知识沉淀**
   - 成功经验记录
   - 失败案例归档
   - 最佳实践提取

**反思触发时机：**
- 任务执行失败
- 结果不符合预期
- 性能低于阈值
- 定期反思（每 N 个任务）

**DevPalAgent 实现：**
```python
# devpal/core/reflector.py
class Reflector:
    def reflect(self, execution_result: ExecutionResult) -> Reflection:
        # 1. 评估结果
        score = self.evaluate(execution_result)
        
        # 2. 诊断问题
        issues = self.diagnose(execution_result)
        
        # 3. 生成改进建议
        suggestions = self.suggest_improvements(issues)
        
        return Reflection(score=score, issues=issues, suggestions=suggestions)
```

---

### 2.4 规划-执行-反思闭环（Plan-Execute-Reflect Loop）

**面试问题：请描述 Plan-Execute-Reflect 循环的工作原理和优势。**

**参考答案：**

Plan-Execute-Reflect 是 Agent 的核心工作模式，形成自我改进的闭环。

**工作流程：**

```
1. Plan（规划）
   ↓
2. Execute（执行）
   ↓
3. Reflect（反思）
   ↓
4. Re-Plan（重新规划）→ 回到步骤 1
```

**优势：**
- **自适应**：根据执行结果动态调整计划
- **容错性**：失败后可以重新规划
- **持续优化**：通过反思不断改进

**实现要点：**
- 设置最大循环次数（防止无限循环）
- 记录每次循环的状态（便于调试）
- 提前终止条件（目标达成或无法继续）

**DevPalAgent 实现：**
```python
# devpal/core/agent_engine.py
class AgentEngine:
    def run(self, user_request: str):
        max_iterations = 10
    for i in range(max_iterations):
            # 1. Plan
        plan = self.planner.plan(user_request)
       
            # 2. Execute
          result = self.executor.execute(plan)
            
            # 3. Reflect
            reflection = self.reflector.reflect(result)
            
            # 4. Check if done
            if reflection.is_success():
          return result
         
            # 5. Re-plan based on reflection
            user_request = reflection.generate_next_request()
```



---

### 2.5 状态机（State Machine）

**面试问题：如何使用状态机管理 Agent 的执行流程？**

**参考答案：**

状态机提供清晰的状态转换逻辑，便于流程控制和调试。

**核心概念：**

1. **状态（State）**
   - IDLE：空闲
   - PLANNING：规划中
   - EXECUTING：执行中
   - REFLECTING：反思中
   - COMPLETED：已完成
   - FAILED：失败

2. **转换（Transition）**
   - 触发条件
   - 转换动作
   - 状态切换

3. **事件（Event）**
   - USER_REQUEST：用户请求
   - PLAN_READY：计划就绪
   - EXECUTION_DONE：执行完成
   - ERROR_OCCURRED：发生错误

**状态转换图：**
```
IDLE → [USER_REQUEST] → PLANNING
PLANNING → [PLAN_READY] → EXECUTING
EXECUTING → [EXECUTION_DONE] → REFLECTING
REFLECTING → [SUCCESS] → COMPLETED
REFLECTING → [NEED_REPLAN] → PLANNING
REFLECTING → [UNRECOVERABLE_ERROR] → FAILED
```

**实现示例：**
```python
from enum import Enum

class AgentState(Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    COMPLETED = "completed"
    FAILED = "failed"

class AgentStateMachine:
    def __init__(self):
      self.state = AgentState.IDLE
     self.transitions = {
            (AgentState.IDLE, "user_request"): AgentState.PLANNING,
      (AgentState.PLANNING, "plan_ready"): AgentState.EXECUTING,
            (AgentState.EXECUTING, "execution_done"): AgentState.REFLECTING,
            (AgentState.REFLECTING, "success"): AgentState.COMPLETED,
            (AgentState.REFLECTING, "need_replan"): AgentState.PLANNING,
            (AgentState.REFLECTING, "error"): AgentState.FAILED,
        }
    
    def transition(self, event: str):
        key = (self.state, event)
        if key in self.transitions:
       self.state = self.transitions[key]
            self.log_transition(event)
        else:
            raise ValueError(f"Invalid transition: {self.state} + {event}")
```



---

## 三、记忆系统

### 3.1 短期上下文（Short-term Context）

**面试问题：如何管理 Agent 的短期上下文？如何处理上下文窗口限制？**

**参考答案：**

短期上下文是当前会话的工作记忆，需要高效管理以应对 token 限制。

**核心挑战：**
- 上下文窗口有限（如 200K tokens）
- 长对话会超出窗口
- 需要保留关键信息

**管理策略：**

1. **滑动窗口（Sliding Window）**
   - 保留最近 N 轮对话
   - 丢弃过早的历史
   - 适用于短会话

2. **上下文压缩（Context Compression）**
   - 摘要历史对话
   - 提取关键信息
   - 保留重要决策

3. **分层存储**
   - 热数据：最近 5 轮（全量）
   - 温数据：5-20 轮（摘要）
   - 冷数据：20+ 轮（归档）

4. **智能裁剪**
   - 保留系统提示词
   - 保留用户最新请求
   - 裁剪中间冗余内容

**实现示例：**
```python
class ContextManager:
    def __init__(self, max_tokens=2000):
        self.max_tokens = max_tokens
        self.messages = []
    
    def add_message(self, message):
        self.messages.append(message)
        
        # 检查是否超出限制
        if self.estimate_tokens() > self.max_tokens:
            self.compress()
    
    def compress(self):
        # 保留系统提示和最近 5 轮
        system_msgs = [m for m in self.messages if m['role'] == 'system']
      recent_msgs = self.messages[-10:]  # 最近 5 轮（user + assistant）
        
        # 中间部分生成摘要
        middle_msgs = self.messages[len(system_msgs):-10]
        summary = self.summarize(middle_msgs)
        
        self.messages = system_msgs + [summary] + recent_msgs
```

---

### 3.2 会话摘要（Session Summary）

**面试问题：如何设计会话摘要机制？**

**参考答案：**

会话摘要将长对话压缩为精简的关键信息。

**摘要内容：**
1. **用户意图**：用户想要完成什么
2. **关键决策**：做了哪些重要选择
3. **执行结果**：完成了什么任务
4. **待办事项**：还有什么未完成
5. **上下文信息**：重要的背景知识

**摘要时机：**
- 上下文即将满时
- 会话结束时
- 用户明确请求时
**摘要策略：**
- **增量摘要**：每 N 轮生成一次，逐步累积
- **分层摘要**：先摘要小段，再摘要大段
- **结构化摘要**：使用固定格式（JSON/Markdown）

**实现示例：**
```python
def generate_summary(messages: List[Message]) -> str:
    prompt = f"""
    请总结以下对话的关键信息：
    
    {format_messages(messages)}
    
    请按以下格式输出：
    ## 用户意图
    - ...
    
    ## 关键决策
    - ...
    
    ## 执行结果
    - ...
    
    ## 待办事项
    - ...
    """
    
    return llm.generate(prompt)
```

---

### 3.3 长期用户画像（Long-term User Profile）

**面试问题：如何构建和维护用户画像？**

**参考答案：**

用户画像记录用户的长期偏好、习惯和背景信息。

**画像维度：**

1. **基本信息**
   - 角色（开发者、产品经理、学生等）
   - 技能水平（初级、中级、高级）
   - 领域专长（前端、后端、AI 等）

2. **偏好设置**
   - 代码风格偏好
   - 沟通风格（详细/简洁）
   - 工具偏好

3. **行为模式**
   - 常用功能
   - 工作习惯
   - 时间分布

4. **历史记录**
   - 项目历史
   - 常见问题
   - 成功案例

**更新策略：**
- **显式更新**：用户明确告知偏好
- **隐式学习**：从行为中推断
- **定期校准**：避免过时信息

**存储方案：**
```json
{
  "user_id": "user_123",
  "profile": {
    "role": "senior_backend_engineer",
    "skills": ["Python", "Go", "Kubernetes"],
    "preferences": {
      "code_style": "clean_code",
      "communication": "concise",
      "testing": "prefer_integration_tests"
    },
    "history": {
      "projects": ["project_a", "project_b"],
      "common_tasks": ["debugging", "code_review"]
    }
  },
  "updated_at": "2026-05-21T10:00:00Z"
}
```



---

### 3.4 业务知识库（Business Knowledge Base）

**面试问题：如何构建 Agent 的业务知识库？**

**参考答案：**

业务知识库存储领域特定的知识，帮助 Agent 理解业务上下文。

**知识类型：**

1. **文档知识**
   - API 文档
   - 技术规范
   - 最佳实践

2. **代码知识**
   - 代码库结构
   - 常用模式
   - 历史变更

3. **业务规则**
   - 业务流程
   - 约束条件
   - 决策规则

4. **FAQ 知识**
   - 常见问题
   - 解决方案
   - 故障排查

**构建方法：**
- **文档解析**：从 Markdown/PDF 提取
- **代码分析**：静态分析 + AST 解析
- **人工标注**：专家知识录入
- **自动学习**：从历史对话中提取

**检索优化：**
- 关键词索引（Elasticsearch）
- 向量检索（语义相似度）
- 混合检索（关键词 + 向量）

---

### 3.5 Redis 缓存

**面试问题：Redis 在 Agent 系统中的应用场景有哪些？**

**参考答案：**

Redis 提供高性能的缓存和临时存储。

**应用场景：**

1. **会话缓存**
   - 当前对话上下文
   - 临时状态存储
   - TTL：30 分钟

2. **结果缓存**
   - LLM 响应缓存（相同输入返回缓存结果）
   - 工具调用结果缓存
   - TTL：1 小时

3. **限流控制**
   - 用户请求计数
   - 滑动窗口限流
   - TTL：1 分钟

4. **分布式锁**
   - 防止并发执行
   - 资源互斥访问
**数据结构选择：**
```python
# 1. String - 简单缓存
redis.set(f"session:{session_id}", json.dumps(context), ex=1800)

# 2. Hash - 结构化数据
redis.hset(f"user:{user_id}", mapping={"name": "Alice", "role": "engineer"})

# 3. List - 消息队列
redis.lpush(f"queue:{task_type}", task_data)

# 4. Sorted Set - 排行榜/优先级队列
redis.zadd("task_priority", {task_id: priority})

# 5. Bitmap - 用户行为追踪
redis.setbit(f"active_users:{date}", user_id, 1)
```

**缓存策略：**
- **Cache-Aside**：先查缓存，未命中再查数据库
- **Write-Through**：写入时同时更新缓存和数据库
- **Write-Behind**：异步写入数据库

---

### 3.6 向量记忆（Vector Memory）

**面试问题：什么是向量记忆？如何实现语义检索？**

**参考答案：**

向量记忆将文本转换为向量，支持语义相似度检索。

**核心概念：**

1. **Embedding（嵌入）**
   - 将文本转换为高维向量（如 1536 维）
   - 语义相似的文本向量距离近
   - 模型：OpenAI text-embedding-3、BGE、M3E

2. **向量检索**
   - 计算查询向量与库中向量的相似度
   - 返回 Top-K 最相似结果
   - 相似度度量：余弦相似度、欧氏距离

**工作流程：**
```
1. 文本 → Embedding 模型 → 向量
2. 向量存储到向量数据库
3. 查询时：查询文本 → 向量 → 相似度检索 → Top-K 结果
```

**应用场景：**
- 知识库检索
- 历史对话检索
- 代码片段检索
- 相似问题推荐

**实现示例：**
```python
from openai import OpenAI

client = OpenAI()

# 1. 生成 Embedding
def get_embedding(text: str) -> List[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

# 2. 存储到向量数据库
embedding = get_embedding("如何设计 Agent 系统？")
vector_db.insert(id="doc_1", vector=embedding, metadata={"text": "..."})

# 3. 语义检索
query_embedding = get_embedding("Agent 架构设计")
results = vector_db.search(query_embedding, top_k=5)
```

---

### 3.7 向量数据库对比

**面试问题：请对比 Milvus、Pinecone、Chroma 三种向量数据库。**

**参考答案：**

| 特性 | Milvus | Pinecone | Chroma |
|------|--------|-------|--------|
| **类型** | 开源 | 商业 SaaS | 开源 |
| **部署** | 自托管/云 | 云托管 | 本地/云 |
| **性能** | 高（十亿级） | 高 | 中（百万级） |
| **索引算法** | IVF、HNSW、DiskANN | 专有算法 | HNSW |
| **过滤能力** | 强（标量过滤） | 强 | 中 |
| **成本** | 免费（自托管） | 按量付费 | 免费 |
| **易用性** | 中（需运维） | 高（托管） | 高（轻量） |
| **适用场景** | 大规模生产 | 快速上线 | 原型/小规模 |

**Milvus 特点：**
- 支持多种索引（IVF_FLAT、HNSW、DiskANN）
- 分布式架构，水平扩展
- 支持 GPU 加速
- 适合大规模生产环境

**Pinecone 特点：**
- 完全托管，无需运维
- 自动扩展
- 低延迟（P95 < 100ms）
- 按查询量和存储量计费

**Chroma 特点：**
- 轻量级，易于集成
- 支持本地运行（SQLite）
- 内置 Embedding 生成
- 适合快速原型和小规模应用

**选型建议：**
- **原型阶段**：Chroma（快速验证）
- **中小规模**：Pinecone（省运维成本）
- **大规模生产**：Milvus（性能 + 成本优化）



---

## 四、Function Calling（函数调用）

### 4.1 Function Calling 可靠性

**面试问题：如何提高 Function Calling 的可靠性？**

**参考答案：**

Function Calling 是 Agent 与外部工具交互的核心机制，可靠性至关重要。

**常见问题：**
1. **参数错误**：LLM 生成的参数不符合 schema
2. **幻觉调用**：调用不存在的函数
3. **参数缺失**：必需参数未提供
4. **类型错误**：参数类型不匹配

**可靠性保障措施：**

1. **Schema 校验**（见 4.2）
2. **参数补全**（见 4.3）
3. **重试机制**
   - 参数错误时重新生成
   - 最多重试 3 次
   - 指数退避

4. **降级策略**
   - 工具不可用时使用备选方案
   - 返回友好错误信息

5. **执行沙箱**
   - 隔离执行环境
   - 资源限制（CPU、内存、时间）
   - 防止恶意代码

6. **结果验证**
   - 检查返回值格式
   - 验证业务逻辑
   - 异常检测

**实现示例：**
```python
class FunctionCaller:
    def call_function(self, function_name: str, arguments: dict, max_retries=3):
        for attempt in range(max_retries):
        try:
                # 1. 校验函数存在
                if function_name not in self.registry:
                    raise FunctionNotFoundError(function_name)
              
              # 2. Schema 校验
                self.validate_schema(function_name, arguments)
              
        # 3. 参数补全
            arguments = self.complete_arguments(function_name, arguments)
                
          # 4. 执行函数
                result = self.execute(function_name, arguments)
              
                # 5. 结果验证
                self.validate_result(result)
                
                return result
                
            except ValidationError as e:
              if attempt < max_retries - 1:
                 # 重新生成参数
             arguments = self.regenerate_arguments(function_name, e)
             else:
            raise
```

---

### 4.2 Schema 校验

**面试问题：如何设计 Function Calling 的 Schema 校验机制？**

**参考答案：**

Schema 定义了函数的参数规范，校验确保参数符合预期。

**Schema 定义（JSON Schema）：**
```json
{
  "name": "search_code",
  "description": "在代码库中搜索指定模式",
  "parameters": {
    "type": "object",
    "properties": {
      "pattern": {
        "type": "string",
    "description": "搜索模式（正则表达式）"
      },
      "file_type": {
        "type": "string",
        "enum": ["py", "js", "go"],
      "description": "文件类型"
      },
      "max_results": {
        "type": "integer",
        "minimum": 1,
        "maximum": 100,
        "default": 10
      }
    },
    "required": ["pattern"]
  }
}
```

**校验内容：**

1. **类型校验**
   - string、integer、boolean、array、object
   - 类型不匹配时尝试转换

2. **必需参数**
   - 检查 required 字段是否存在
   - 缺失时报错或补全

3. **值约束**
   - enum：枚举值
   - minimum/maximum：数值范围
   - minLength/maxLength：字符串长度
   - pattern：正则匹配

4. **嵌套对象**
   - 递归校验子对象
   - 数组元素校验

**实现示例：**
```python
from jsonschema import validate, ValidationError

def validate_function_call(function_name: str, arguments: dict):
    schema = get_function_schema(function_name)
    
    try:
        validate(instance=arguments, schema=schema["parameters"])
    except ValidationError as e:
        raise FunctionCallError(
            f"参数校验失败: {e.message}\n"
          f"路径: {'.'.join(str(p) for p in e.path)}\n"
            f"期望: {e.schema}"
        )
```

**错误处理：**
- 提供清晰的错误信息
- 指出具体哪个参数有问题
- 给出修正建议

---

### 4.3 参数补全

**面试问题：如何实现智能参数补全？**

**参考答案：**

参数补全自动填充缺失或不完整的参数。
**补全策略：**

1. **默认值补全**
   - Schema 中定义的 default 值
   - 常用默认值（如 limit=10）

2. **上下文推断**
   - 从对话历史中提取
   - 从当前环境中获取（如当前目录）

3. **智能推荐**
   - 基于历史调用记录
   - 基于用户偏好

4. **交互式补全**
   - 缺失关键参数时询问用户
   - 提供候选值供选择

**实现示例：**
```python
def complete_arguments(function_name: str, arguments: dict, context: dict) -> dict:
    schema = get_function_schema(function_name)
    completed = arguments.copy()
    
    for param_name, param_schema in schema["parameters"]["properties"].items():
        # 1. 参数已提供，跳过
        if param_name in completed:
            continue
        
        # 2. 使用默认值
        if "default" in param_schema:
            completed[param_name] = param_schema["default"]
            continue
        
        # 3. 从上下文推断
        if param_name == "file_path" and "current_file" in context:
            completed[param_name] = context["current_file"]
            continue
        
        # 4. 从历史记录推断
        historical_value = get_historical_value(function_name, param_name)
        if historical_value:
         completed[param_name] = historical_value
            continue
        
        # 5. 必需参数缺失，报错
      if param_name in schema["parameters"].get("required", []):
            raise MissingParameterError(f"缺少必需参数: {param_name}")
    
    return completed
```

---

### 4.4 幂等控制

**面试问题：为什么需要幂等控制？如何实现？**

**参考答案：**

幂等性确保相同的操作执行多次与执行一次效果相同，避免重复执行带来的副作用。

**需要幂等的场景：**
- 网络重试（请求超时后重试）
- 分布式系统（消息重复消费）
- 用户误操作（重复点击）

**幂等实现方法：**

1. **幂等键（Idempotency Key）**
   - 客户端生成唯一 ID
   - 服务端记录已执行的操作
   - 重复请求返回缓存结果

2. **状态检查**
   - 执行前检查当前状态
   - 已完成则直接返回

3. **乐观锁**
   - 使用版本号
   - 更新时检查版本

4. **唯一约束**
   - 数据库唯一索引
   - 防止重复插入

**实现示例：**
```python
import hashlib
import json

class IdempotentExecutor:
    def __init__(self):
        self.executed = {}  # {idempotency_key: result}
    
    def execute(self, function_name: str, arguments: dict) -> any:
        # 1. 生成幂等键
        idempotency_key = self.generate_key(function_name, arguments)
        
        # 2. 检查是否已执行
        if idempotency_key in self.executed:
            return self.executed[idempotency_key]
        
        # 3. 执行函数
        result = self.call_function(function_name, arguments)
        
      # 4. 缓存结果
      self.executed[idempotency_key] = result
     
        return result
    
    def generate_key(self, function_name: str, arguments: dict) -> str:
        # 基于函数名和参数生成唯一键
        content = json.dumps({"function": function_name, "args": arguments}, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
```

**注意事项：**
- 只对写操作（有副作用）启用幂等控制
- 读操作通常天然幂等
- 幂等键需要合理设计（包含关键参数）



---

### 4.5 工具描述（Tool Description）

**面试问题：如何编写高质量的工具描述？**

**参考答案：**

工具描述是 LLM 理解工具用途的关键，直接影响 Function Calling 的准确性。

**描述原则：**

1. **清晰明确**
   - 说明工具的功能
   - 避免歧义
   - 使用简单语言

2. **包含关键信息**
   - 输入参数说明
   - 输出格式说明
   - 使用场景

3. **提供示例**
   - 典型用法
   - 边界情况

4. **注明限制**
   - 性能限制
   - 权限要求
   - 副作用警告

**好的描述示例：**
```json
{
  "name": "search_code",
  "description": "在代码库中搜索匹配指定正则表达式的代码片段。支持按文件类型过滤。适用于查找函数定义、变量引用等场景。注意：大型代码库搜索可能需要 5-10 秒。",
  "parameters": {
    "type": "object",
    "properties": {
      "pattern": {
      "type": "string",
        "description": "正则表达式搜索模式。例如：'def\\s+\\w+' 匹配 Python 函数定义"
      },
      "file_type": {
        "type": "string",
        "enum": ["py", "js", "go", "java"],
        "description": "文件类型过滤。留空则搜索所有文件"
      },
      "max_results": {
        "type": "integer",
        "description": "最多返回结果数（1-100），默认 10"
      }
    },
    "required": ["pattern"]
  }
}
```

**差的描述示例：**
```json
{
  "name": "search",
  "description": "搜索",  // ❌ 太简略
  "parameters": {
    "pattern": {
      "type": "string",
      "description": "模式"  // ❌ 不清楚是什么模式
    }
  }
}
```

**描述优化技巧：**
- 使用动词开头（"搜索"、"创建"、"更新"）
- 说明适用场景（"适用于..."）
- 提供具体示例（"例如：..."）
- 注明性能特征（"大文件可能需要..."）
- 警告副作用（"注意：此操作会..."）

---

## 五、RAG（检索增强生成）

### 5.1 RAG Chunk 大小（文本分块）

**面试问题：如何确定 RAG 系统的最佳 Chunk 大小？**

**参考答案：**

Chunk 大小直接影响检索精度和生成质量。

**Chunk 大小权衡：**

| Chunk 大小 | 优点 | 缺点 | 适用场景 |
|-----------|------|------|---------|
| **小（100-200 tokens）** | 检索精准、噪音少 | 上下文不足、需要多次检索 | FAQ、短文档 |
| **中（300-500 tokens）** | 平衡精度和上下文 | 通用性好 | 技术文档、博客 |
| **大（800-1000 tokens）** | 上下文丰富 | 检索不精准、噪音多 | 长文章、书籍 |

**影响因素：**

1. **文档类型**
   - 结构化文档（API 文档）：小 Chunk
   - 叙事性文档（教程）：大 Chunk

2. **查询类型**
   - 精确查询（"函数签名"）：小 Chunk
   - 概念查询（"如何设计"）：大 Chunk

3. **模型上下文窗口**
   - 小窗口模型（4K）：小 Chunk
   - 大窗口模型（128K）：大 Chunk

**分块策略：**

1. **固定大小分块**
   - 按 token 数切分
   - 简单但可能切断语义

2. **语义分块**
   - 按段落、章节切分
   - 保持语义完整性

3. **滑动窗口**
   - Chunk 之间有重叠（如 50 tokens）
   - 避免边界信息丢失

4. **层次分块**
   - 大 Chunk（章节）+ 小 Chunk（段落）
   - 先粗检索再精检索

**实现示例：**
```python
def chunk_text(text: str, chunk_size=500, overlap=50) -> List[str]:
    tokens = tokenize(text)
    chunks = []
    
    for i in range(0, len(tokens), chunk_size - overlap):
        chunk_tokens = tokens[i:i + chunk_size]
        chunks.append(detokenize(chunk_tokens))
    
    return chunks

# 语义分块
def semantic_chunk(text: str) -> List[str]:
    # 按段落分割
    paragraphs = text.split('\n\n')
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for para in paragraphs:
        para_size = count_tokens(para)
        
        if current_size + para_size > 500:
       # 当前 chunk 已满，开始新 chunk
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = [para]
            current_size = para_size
        else:
            current_chunk.append(para)
     current_size += para_size
    
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return chunks
```

**最佳实践：**
- 起始值：300-500 tokens
- A/B 测试不同大小
- 监控检索质量指标（MRR、NDCG）
- 根据业务场景调整

---

### 5.2 召回优化

**面试问题：如何优化 RAG 系统的召回率？**

**参考答案：**

召回率是 RAG 的第一道关卡，决定了后续生成的质量上限。

**召回优化策略：**

1. **混合检索（Hybrid Search）**
   - 向量检索（语义相似度）
   - 关键词检索（BM25）
   - 加权融合（如 0.7 * 向量 + 0.3 * 关键词）

2. **查询扩展**
   - 同义词扩展
   - 相关词扩展
   - 查询改写（见 5.3）

3. **多向量检索**
   - 使用多个 Embedding 模型
   - 融合不同模型的结果

4. **元数据过滤**
   - 先用元数据筛选（如时间、类型）
   - 再进行向量检索

5. **负样本挖掘**
   - 训练时加入难负样本
   - 提高模型区分能力

**实现示例：**
```python
def hybrid_search(query: str, top_k=10) -> List[Document]:
    # 1. 向量检索
    query_embedding = get_embedding(query)
    vector_results = vector_db.search(query_embedding, top_k=top_k*2)
    
    # 2. 关键词检索（BM25）
    bm25_results = bm25_index.search(query, top_k=top_k*2)
    
    # 3. 融合结果（RRF - Reciprocal Rank Fusion）
    combined_scores = {}
    
    for rank, doc in enumerate(vector_results):
        combined_scores[doc.id] = combined_scores.get(doc.id, 0) + 1 / (rank + 60)
    
    for rank, doc in enumerate(bm25_results):
     combined_scores[doc.id] = combined_scores.get(doc.id, 0) + 1 / (rank + 60)
    
    # 4. 排序并返回 Top-K
    sorted_docs = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
    return [get_document(doc_id) for doc_id, _ in sorted_docs[:top_k]]
```

**评估指标：**
- **Recall@K**：Top-K 结果中包含相关文档的比例
- **MRR（Mean Reciprocal Rank）**：第一个相关结果的排名倒数
- **NDCG（Normalized Discounted Cumulative Gain）**：考虑排序质量的指标



---

### 5.3 Query 改写（查询改写）

**面试问题：为什么需要查询改写？如何实现？**

**参考答案：**

用户查询往往不够精确或完整，查询改写可以提高检索效果。

**改写场景：**

1. **口语化 → 规范化**
   - 原始："咋搞 Agent 啊？"
   - 改写："如何设计 AI Agent 系统？"

2. **模糊 → 具体**
   - 原始："内存问题"
   - 改写："Agent 系统内存管理策略"

3. **单一 → 多角度**
   - 原始："Function Calling"
   - 改写：["Function Calling 实现", "工具调用机制", "函数调用可靠性"]

4. **补充上下文**
   - 原始："这个怎么用？"
   - 改写："Redis 缓存在 Agent 系统中如何使用？"

**改写方法：**

1. **基于 LLM 的改写**
   ```python
   def rewrite_query(query: str, context: str = "") -> List[str]:
       prompt = f"""
       用户查询：{query}
       对话上下文：{context}
       
       请生成 3 个改写版本，使其更适合检索：
       1. 补充完整上下文
       2. 使用专业术语
       3. 从不同角度表达
       
       输出格式：
       1. ...
       2. ...
       3. ...
    """
       
       response = llm.generate(prompt)
       return parse_rewrites(response)
   ```

2. **基于模板的改写**
   ```python
   templates = [
       "{query} 是什么",
       "{query} 如何实现",
       "{query} 最佳实践",
       "{query} 常见问题"
   ]
   
   rewrites = [t.format(query=query) for t in templates]
   ```

3. **基于同义词的扩展**
   ```python
   synonyms = {
       "Agent": ["智能体", "代理", "AI Agent"],
       "Memory": ["记忆", "存储", "缓存"]
   }
   
   def expand_query(query: str) -> List[str]:
       expanded = [query]
       for term, syns in synonyms.items():
        if term in query:
               for syn in syns:
                   expanded.append(query.replace(term, syn))
       return expanded
   ```

**多查询融合：**
```python
def multi_query_retrieval(original_query: str, top_k=10) -> List[Document]:
    # 1. 生成多个改写版本
    queries = rewrite_query(original_query)
    queries.insert(0, original_query)  # 包含原始查询
    
    # 2. 每个查询独立检索
    all_results = {}
    for query in queries:
        results = vector_search(query, top_k=top_k*2)
        for rank, doc in enumerate(results):
      score = 1 / (rank + 1)
            all_results[doc.id] = all_results.get(doc.id, 0) + score
    
    # 3. 融合排序
    sorted_docs = sorted(all_results.items(), key=lambda x: x[1], reverse=True)
    return [get_document(doc_id) for doc_id, _ in sorted_docs[:top_k]]
```

---

### 5.4 多路召回

**面试问题：什么是多路召回？如何设计多路召回策略？**
**参考答案：**

多路召回通过多种检索策略并行召回，提高覆盖率和准确性。

**召回路径：**

1. **向量召回**
   - 语义相似度检索
   - 适合概念性查询

2. **关键词召回**
   - BM25、TF-IDF
   - 适合精确匹配

3. **标签召回**
   - 基于文档标签/分类
   - 适合分类查询

4. **热门召回**
   - 高频访问文档
   - 适合通用查询

5. **个性化召回**
   - 基于用户历史
   - 适合推荐场景

6. **图召回**
   - 基于知识图谱
   - 适合关系查询

**架构设计：**
```
用户查询
    ↓
┌───┴───┬───────┬───────┬───────┐
│向量召回│关键词召回│标签召回│热门召回│个性化召回│
└───┬───┴───────┴───────┴───────┘
    ↓
  融合排序（Rerank）
    ↓
  Top-K 结果
```

**实现示例：**
```python
from concurrent.futures import ThreadPoolExecutor

class MultiPathRetrieval:
    def __init__(self):
        self.retrievers = {
            "vector": VectorRetriever(),
            "bm25": BM25Retriever(),
       "tag": TagRetriever(),
        "popular": PopularRetriever(),
        }
    
    def retrieve(self, query: str, top_k=10) -> List[Document]:
        # 1. 并行召回
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                name: executor.submit(retriever.search, query, top_k=top_k*2)
                for name, retriever in self.retrievers.items()
            }
            
    results = {
              name: future.result()
                for name, future in futures.items()
            }
        
        # 2. 融合结果
      combined = self.merge_results(results)
        
        # 3. Rerank
        reranked = self.rerank(query, combined)
      
        return reranked[:top_k]
    
    def merge_results(self, results: Dict[str, List[Document]]) -> List[Document]:
        # 使用 RRF（Reciprocal Rank Fusion）
        scores = {}
        
        for path_name, docs in results.items():
            weight = self.get_path_weight(path_name)
            
            for rank, doc in enumerate(docs):
                score = weight / (rank + 60)
            scores[doc.id] = scores.get(doc.id, 0) + score
      
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [get_document(doc_id) for doc_id, _ in sorted_docs]
    
    def get_path_weight(self, path_name: str) -> float:
        # 不同召回路径的权重
        weights = {
         "vector": 0.4,
        "bm25": 0.3,
            "tag": 0.2,
         "popular": 0.1,
        }
        return weights.get(path_name, 0.25)
```

**路径权重调优：**
- A/B 测试不同权重组合
- 根据查询类型动态调整
- 监控各路径的贡献度

---

### 5.5 Rerank 重排

**面试问题：为什么需要 Rerank？如何实现高效的重排序？**

**参考答案：**

Rerank 在召回结果基础上进行精排，提高 Top-K 结果的质量。

**为什么需要 Rerank：**
1. **召回阶段追求覆盖率**：宁可多召回，不能漏掉相关文档
2. **排序阶段追求精准度**：从候选中挑选最相关的
3. **两阶段分工**：召回快速粗筛，重排精细打分

**Rerank 方法：**

1. **Cross-Encoder 模型**
   - 将查询和文档拼接输入模型
   - 输出相关性分数
   - 精度高但速度慢

2. **LLM 打分**
   - 让 LLM 评估相关性
   - 灵活但成本高

3. **多因子打分**
   - 语义相似度
   - 关键词匹配度
   - 文档质量分
   - 时效性分
   - 用户偏好分

**实现示例：**
```python
from sentence_transformers import CrossEncoder

class Reranker:
    def __init__(self):
        # 使用 Cross-Encoder 模型
        self.model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    
    def rerank(self, query: str, documents: List[Document], top_k=10) -> List[Document]:
        # 1. 准备输入对
        pairs = [(query, doc.content) for doc in documents]
        
        # 2. 批量打分
        scores = self.model.predict(pairs)
        
        # 3. 排序
        doc_scores = list(zip(documents, scores))
        doc_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [doc for doc, _ in doc_scores[:top_k]]

# 多因子打分
class MultiFactorReranker:
    def rerank(self, query: str, documents: List[Document], top_k=10) -> List[Document]:
        scored_docs = []
        
        for doc in documents:
            # 计算多个因子分数
         semantic_score = self.semantic_similarity(query, doc)
            keyword_score = self.keyword_match(query, doc)
            quality_score = doc.quality_score
            freshness_score = self.freshness(doc)
            
        # 加权融合
            final_score = (
                0.4 * semantic_score +
                0.3 * keyword_score +
                0.2 * quality_score +
                0.1 * freshness_score
            )
          
            scored_docs.append((doc, final_score))
        
        # 排序
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in scored_docs[:top_k]]
```

**性能优化：**
- 只对 Top-100 候选进行 Rerank（不是全量）
- 使用轻量级 Rerank 模型
- 批量推理提高吞吐
- 缓存常见查询的 Rerank 结果

**效果评估：**
- **NDCG@K**：考虑排序质量
- **MRR**：第一个相关结果的位置
- **用户点击率**：实际业务指标



---

## 六、工程性能与稳定性

### 6.1 P95 延迟

**面试问题：什么是 P95 延迟？如何优化 Agent 系统的 P95 延迟？**

**参考答案：**

P95 延迟是指 95% 的请求响应时间低于该值，是衡量系统性能的关键指标。

**为什么关注 P95 而非平均值：**
- 平均值会被极端值拉高/拉低
- P95 更能反映大多数用户体验
- 长尾延迟影响用户满意度

**Agent 系统延迟构成：**
```
总延迟 = 网络延迟 + 模型推理延迟 + 工具执行延迟 + 排队延迟
```

**优化策略：**

1. **模型推理优化**
   - 使用更快的模型（Haiku vs Opus）
   - Prompt 缓存（减少重复计算）
   - 批量推理（Batch API）
   - 流式输出（降低首 token 延迟）

2. **工具执行优化**
   - 并行工具调用（见 6.2）
   - 工具结果缓存
   - 超时控制（避免慢工具拖累整体）

3. **网络优化**
   - CDN 加速
   - 区域就近部署
   - HTTP/2、gRPC

4. **排队优化**
   - 优先级队列
   - 限流（见 6.4）
   - 弹性扩容（见 6.3）

**监控与分析：**
```python
import time
from collections import defaultdict

class LatencyMonitor:
    def __init__(self):
        self.latencies = defaultdict(list)
    
    def record(self, operation: str, latency: float):
        self.latencies[operation].append(latency)
    
    def get_percentile(self, operation: str, percentile=95) -> float:
        latencies = sorted(self.latencies[operation])
        if not latencies:
            return 0
    
        index = int(len(latencies) * percentile / 100)
        return latencies[index]
    
    def report(self):
        for operation, latencies in self.latencies.items():
            p50 = self.get_percentile(operation, 50)
            p95 = self.get_percentile(operation, 95)
            p99 = self.get_percentile(operation, 99)
            
            print(f"{operation}:")
            print(f"  P50: {p50:.2f}ms")
            print(f"  P95: {p95:.2f}ms")
          print(f"  P99: {p99:.2f}ms")

# 使用示例
monitor = LatencyMonitor()

@monitor_latency("llm_call")
def call_llm(prompt: str):
    start = time.time()
    result = llm.generate(prompt)
    latency = (time.time() - start) * 1000
    monitor.record("llm_call", latency)
    return result
```

**优化目标：**
- P95 < 2s（交互式应用）
- P95 < 5s（后台任务）
- P99 < 10s（可接受上限）

---

### 6.2 并行工具

**面试问题：如何实现并行工具调用？有哪些注意事项？**

**参考答案：**

并行工具调用可以显著降低总延迟，提升用户体验。

**并行场景：**
1. **独立工具**：无依赖关系的工具可以并行
   - 示例：同时搜索代码 + 读取文档
2. **批量操作**：对多个对象执行相同操作
   - 示例：批量读取多个文件

**实现方式：**

1. **线程池（ThreadPoolExecutor）**
   ```python
   from concurrent.futures import ThreadPoolExecutor, as_completed
   
   def parallel_tool_calls(tool_calls: List[ToolCall]) -> List[ToolResult]:
    with ThreadPoolExecutor(max_workers=5) as executor:
           # 提交所有任务
        futures = {
               executor.submit(execute_tool, call): call
               for call in tool_calls
           }
       
           # 收集结果
           results = []
           for future in as_completed(futures):
               call = futures[future]
         try:
                   result = future.result(timeout=30)
                   results.append(result)
               except Exception as e:
                   results.append(ToolResult(error=str(e)))
           
           return results
   ```

2. **异步 IO（asyncio）**
   ```python
   import asyncio
   
   async def parallel_tool_calls_async(tool_calls: List[ToolCall]) -> List[ToolResult]:
       # 创建任务
       tasks = [execute_tool_async(call) for call in tool_calls]
    
       # 并行执行
       results = await asyncio.gather(*tasks, return_exceptions=True)
       
       return results
   ```

**依赖处理：**
```python
def execute_with_dependencies(tool_calls: List[ToolCall]) -> List[ToolResult]:
    # 1. 构建依赖图
    dag = build_dependency_graph(tool_calls)
    
    # 2. 拓扑排序
    execution_order = topological_sort(dag)
    
    # 3. 按层执行（同层并行）
    results = {}
    for layer in execution_order:
        # 同层工具并行执行
     layer_results = parallel_execute(layer)
        results.update(layer_results)
    
    return results
```

**注意事项：**

1. **资源限制**
   - 限制并发数（避免资源耗尽）
   - 设置超时（防止慢工具阻塞）

2. **错误处理**
   - 部分失败不影响其他工具
   - 记录失败原因

3. **顺序保证**
   - 有依赖的工具串行执行
   - 结果顺序与请求顺序一致

4. **幂等性**
   - 并行重试时避免副作用

**性能提升：**
- 3 个独立工具并行：延迟降低 ~66%
- 5 个独立工具并行：延迟降低 ~80%

---

### 6.3 弹性伸缩

**面试问题：如何设计 Agent 系统的弹性伸缩策略？**

**参考答案：**

弹性伸缩根据负载动态调整资源，平衡成本和性能。

**伸缩维度：**

1. **水平伸缩（Scale Out/In）**
   - 增加/减少实例数量
   - 适合无状态服务

2. **垂直伸缩（Scale Up/Down）**
   - 增加/减少单实例资源（CPU、内存）
   - 适合有状态服务

**伸缩指标：**

1. **基于负载**
   - CPU 使用率 > 70% → 扩容
   - 内存使用率 > 80% → 扩容
   - QPS > 阈值 → 扩容

2. **基于延迟**
   - P95 延迟 > 2s → 扩容
   - 排队时间 > 5s → 扩容

3. **基于队列长度**
   - 队列长度 > 100 → 扩容
   - 队列长度 < 10 → 缩容

4. **基于时间**
   - 工作日 9:00-18:00 → 扩容
   - 夜间 → 缩容

**实现方案：**

1. **Kubernetes HPA（Horizontal Pod Autoscaler）**
   ```yaml
   apiVersion: autoscaling/v2
   kind: HorizontalPodAutoscaler
   metadata:
     name: agent-service
   spec:
     scaleTargetRef:
       apiVersion: apps/v1
       kind: Deployment
       name: agent-service
     minReplicas: 2
     maxReplicas: 10
     metrics:
     - type: Resource
       resource:
         name: cpu
         target:
           type: Utilization
           averageUtilization: 70
     - type: Pods
       pods:
         metric:
           name: request_latency_p95
         target:
         type: AverageValue
           averageValue: "2000"  # 2s
   ```

2. **自定义伸缩逻辑**
   ```python
   class AutoScaler:
       def __init__(self, min_replicas=2, max_replicas=10):
           self.min_replicas = min_replicas
           self.max_replicas = max_replicas
           self.current_replicas = min_replicas
       
       def check_and_scale(self):
           metrics = self.collect_metrics()
           
           # 计算目标副本数
           target_replicas = self.calculate_target_replicas(metrics)
           
           # 执行伸缩
       if target_replicas > self.current_replicas:
               self.scale_out(target_replicas - self.current_replicas)
         elif target_replicas < self.current_replicas:
               self.scale_in(self.current_replicas - target_replicas)
       
       def calculate_target_replicas(self, metrics: dict) -> int:
           # 基于 CPU 使用率
           cpu_based = int(self.current_replicas * metrics['cpu_usage'] / 70)
         
           # 基于 QPS
           qps_based = int(metrics['qps'] / 100)  # 每个实例处理 100 QPS
           
           # 取最大值
           target = max(cpu_based, qps_based)
           
           # 限制范围
           return max(self.min_replicas, min(target, self.max_replicas))
   ```

**伸缩策略：**
- **快速扩容**：负载突增时快速响应
- **缓慢缩容**：避免频繁抖动（冷却期 5-10 分钟）
- **预热机制**：新实例启动后预热再接入流量

**成本优化：**
- 使用 Spot 实例（降低 70% 成本）
- 夜间自动缩容
- 按需付费 vs 预留实例



---

### 6.4 限流排队

**面试问题：如何设计 Agent 系统的限流和排队机制？**

**参考答案：**

限流保护系统不被过载，排队保证请求不丢失。

**限流算法：**

1. **固定窗口（Fixed Window）**
   - 每个时间窗口（如 1 分钟）允许 N 个请求
   - 简单但有突刺问题

2. **滑动窗口（Sliding Window）**
   - 动态计算最近 N 秒的请求数
   - 更平滑但实现复杂

3. **令牌桶（Token Bucket）**
   - 固定速率生成令牌
   - 允许短时突发
   - 适合 API 限流

4. **漏桶（Leaky Bucket）**
   - 固定速率处理请求
   - 平滑流量
   - 适合消息队列
**实现示例：**

```python
import time
from collections import deque

class TokenBucketLimiter:
    def __init__(self, rate: int, capacity: int):
        """
        rate: 每秒生成的令牌数
        capacity: 桶容量
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
    
    def acquire(self) -> bool:
      now = time.time()
        
        # 补充令牌
        elapsed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now
        
        # 尝试获取令牌
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

class SlidingWindowLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
    
    def acquire(self) -> bool:
        now = time.time()
        
        # 移除过期请求
        while self.requests and self.requests[0] < now - self.window_seconds:
        self.requests.popleft()
        
        # 检查是否超限
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False
```

**分级限流：**
```python
class TieredRateLimiter:
    def __init__(self):
        self.limiters = {
            "free": TokenBucketLimiter(rate=10, capacity=20),      # 10 req/s
            "pro": TokenBucketLimiter(rate=100, capacity=200),     # 100 req/s
            "enterprise": TokenBucketLimiter(rate=1000, capacity=2000)  # 1000 req/s
        }
    
    def acquire(self, user_tier: str) -> bool:
        limiter = self.limiters.get(user_tier)
     if not limiter:
            return False
        return limiter.acquire()
```

**排队机制：**

1. **FIFO 队列**
   - 先进先出
   - 公平但不考虑优先级

2. **优先级队列**
   - 高优先级先处理
   - 适合多租户场景

3. **公平队列**
   - 每个用户轮流处理
   - 防止单用户占用资源

**实现示例：**
```python
import heapq
from queue import Queue
from threading import Thread

class PriorityQueue:
    def __init__(self, max_workers=5):
        self.queue = []
        self.counter = 0
        self.max_workers = max_workers
        self.workers = []
        
     # 启动工作线程
        for _ in range(max_workers):
            worker = Thread(target=self._worker)
            worker.daemon = True
            worker.start()
       self.workers.append(worker)
    
    def enqueue(self, task, priority=0):
        """
        priority: 数值越小优先级越高
        """
        heapq.heappush(self.queue, (priority, self.counter, task))
        self.counter += 1
    
    def _worker(self):
     while True:
            if self.queue:
            _, _, task = heapq.heappop(self.queue)
             self._execute(task)
            else:
              time.sleep(0.1)
    
    def _execute(self, task):
        try:
            task()
      except Exception as e:
            print(f"Task failed: {e}")
```

**限流响应：**
- **429 Too Many Requests**：超出限流
- **503 Service Unavailable**：队列已满
- **Retry-After**：告知客户端何时重试

**监控指标：**
- 限流触发次数
- 队列长度
- 排队时间
- 拒绝率

---

### 6.5 熔断降级

**面试问题：什么是熔断降级？如何实现？**

**参考答案：**

熔断降级是保护系统稳定性的最后一道防线。

**熔断器（Circuit Breaker）：**

**三种状态：**
1. **Closed（关闭）**：正常工作
2. **Open（打开）**：熔断，直接返回错误
3. **Half-Open（半开）**：尝试恢复

**状态转换：**
```
Closed → [错误率 > 阈值] → Open
Open → [冷却时间到] → Half-Open
Half-Open → [成功] → Closed
Half-Open → [失败] → Open
```

**实现示例：**
```python
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, 
                 failure_threshold=5,      # 失败次数阈值
             timeout=60,               # 熔断超时（秒）
                 success_threshold=2):     # 半开状态成功次数阈值
        self.failure_threshold = failure_threshold
        self.timeout = timeout
     self.success_threshold = success_threshold
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
    
    def call(self, func, *args, **kwargs):
        # 检查是否需要从 Open 转到 Half-Open
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
          self.state = CircuitState.HALF_OPEN
         self.success_count = 0
            else:
                raise CircuitBreakerOpenError("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
      return result
        except Exception as e:
         self._on_failure()
            raise e
    
    def _on_success(self):
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
         if self.success_count >= self.success_threshold:
            self.state = CircuitState.CLOSED
             self.failure_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
        elif self.failure_count >= self.failure_threshold:
          self.state = CircuitState.OPEN

# 使用示例
breaker = CircuitBreaker(failure_threshold=5, timeout=60)

def call_external_service():
    return breaker.call(external_api.request, "/endpoint")
```

**降级策略：**

1. **返回默认值**
   ```python
   def get_user_profile(user_id: str):
       try:
           return user_service.get_profile(user_id)
    except Exception:
       # 降级：返回默认画像
           return {"user_id": user_id, "name": "Guest", "tier": "free"}
   ```

2. **使用缓存**
   ```python
   def get_recommendations(user_id: str):
       try:
           return recommendation_service.get(user_id)
     except Exception:
         # 降级：返回缓存的推荐
           return cache.get(f"rec:{user_id}") or []
   ```

3. **简化功能**
   ```python
   def search(query: str):
       try:
           # 正常：向量检索 + 关键词检索 + Rerank
        return advanced_search(query)
       except Exception:
       # 降级：仅关键词检索
           return simple_keyword_search(query)
   ```

4. **跳过非核心功能**
   ```python
   def process_request(request):
       result = core_logic(request)  # 核心逻辑必须执行
     
       try:
           analytics.track(request)  # 非核心，可降级
     except Exception:
           pass  # 静默失败
       
       return result
   ```

**多级降级：**
```python
class DegradationManager:
    def __init__(self):
      self.level = 0  # 0: 正常, 1-3: 降级级别
    
    def execute(self, task):
        if self.level == 0:
            return self.full_execution(task)
        elif self.level == 1:
            return self.light_degradation(task)
        elif self.level == 2:
            return self.medium_degradation(task)
        else:
            return self.heavy_degradation(task)
    
    def full_execution(self, task):
        # 完整功能：向量检索 + Rerank + 个性化
        return full_pipeline(task)
    
    def light_degradation(self, task):
        # 轻度降级：跳过个性化
        return pipeline_without_personalization(task)
    
    def medium_degradation(self, task):
        # 中度降级：跳过 Rerank
        return simple_retrieval(task)
    
    def heavy_degradation(self, task):
        # 重度降级：返回缓存或默认结果
        return cached_or_default(task)
```

**监控与告警：**
- 熔断器状态变化告警
- 降级触发次数统计
- 降级对业务指标的影响

---

## 总结

本文档覆盖了 AI Agent 系统的六大核心领域：

1. **系统架构**：入口层、编排层、模型层、工具层、记忆层、观测层
2. **核心组件**：Planner、Executor、Reflector、Plan-Execute-Reflect 循环、状态机
3. **记忆系统**：短期上下文、会话摘要、用户画像、知识库、Redis、向量数据库
4. **Function Calling**：可靠性、Schema 校验、参数补全、幂等控制、工具描述
5. **RAG**：Chunk 大小、召回优化、Query 改写、多路召回、Rerank
6. **工程稳定性**：P95 延迟、并行工具、弹性伸缩、限流排队、熔断降级

**面试准备建议：**
- 理解每个概念的原理和应用场景
- 准备 1-2 个实际项目案例
- 能够画出架构图并解释设计决策
- 了解常见问题和解决方案
- 关注最新技术趋势（如 Prompt Caching、长上下文模型）

**DevPalAgent 项目亮点：**
- Spec-first 开发流程
- 11 阶段 OpenSpec 工作流
- Plan-Execute-Reflect 闭环
- 三层记忆系统
- 自愈能力（Phase 9）

祝面试顺利！🚀

<!-- END -->