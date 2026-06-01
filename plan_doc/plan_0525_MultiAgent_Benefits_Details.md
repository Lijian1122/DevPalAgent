# 多智能体架构核心收益与技术细节

**文档版本**: 1.0  
**创建日期**: 2026-05-25  
**作者**: DevPalAgent 团队

---

## 目录

1. [核心收益详解](#1-核心收益详解)
2. [智能体间通信机制](#2-智能体间通信机制)
3. [工作流协调细节](#3-工作流协调细节)
4. [状态管理与同步](#4-状态管理与同步)
5. [错误处理与恢复](#5-错误处理与恢复)
6. [性能优化策略](#6-性能优化策略)

---

## 1. 核心收益详解

### 1.1 性能收益

#### 1.1.1 并行执行加速

**当前问题**:
```python
# 顺序执行 - 10 个文件
for file in files:  # 10 次循环
    code = llm.generate(file)  # 每次 30 秒
    write_file(file, code)
# 总耗时: 10 × 30s = 300s
```

**多智能体方案**:
```python
# 并行执行 - 10 个文件，4 个智能体
# 批次 1: file1, file2, file3, file4 (并行) - 30s
# 批次 2: file5, file6, file7, file8 (并行) - 30s
# 批次 3: file9, file10 (并行) - 30s
# 总耗时: 3 × 30s = 90s
```

**加速比计算**:
- 理论加速比 = 智能体数量 = 4x
- 实际加速比 = 300s / 90s = 3.3x
- 损耗来源: 协调开销 (5%) + 依赖等待 (15%)

**不同规模的收益**:

| 文件数 | 顺序耗时 | 4 智能体 | 8 智能体 | 16 智能体 | 最优配置 |
|-------|---------|---------|---------|----------|---------|
| 5     | 150s    | 60s     | 45s     | 45s      | 4 智能体 |
| 10    | 300s    | 90s     | 60s     | 60s    | 4 智能体 |
| 20    | 600s    | 180s    | 90s     | 75s      | 8 智能体 |
| 50    | 1500s   | 450s    | 225s    | 120s     | 16 智能体 |
| 100   | 3000s   | 900s    | 450s    | 240s     | 16 智能体 |

**关键发现**:
- 小项目 (< 10 文件): 4 智能体最优
- 中项目 (10-30 文件): 8 智能体最优
- 大项目 (> 30 文件): 16 智能体最优

#### 1.1.2 资源利用率提升

**当前状态**:
```
CPU:  ████░░░░░░░░░░░░░░░░  20% (单线程等待 LLM)
GPU:  ░░░░░░░░░░░░░░░░░   0% (未使用)
网络: ██░░░░░░░░░░░░░░░░░░  10% (单连接)
LLM:  ████░░░░░░░░░░░░░░░░  20% (顺序调用)
```

**多智能体状态**:
```
CPU:  ████████████████░░░░  80% (多线程协调)
GPU:  ░░░░░░░░░░░░░░░   0% (未使用)
网络: ████████░░░░░░░░░░░░  40% (4 并发连接)
LLM:  ████████████████░░  80% (并发调用)
```

**收益量化**:
- CPU 利用率: 20% → 80% (+300%)
- 网络利用率: 10% → 40% (+300%)
- LLM 吞吐量: 2 req/min → 8 req/min (+300%)

### 1.2 可扩展性收益

#### 1.2.1 水平扩展能力

**当前架构限制**:
```
单机顺序执行 → 无法利用多核 → 无法分布式
```

**多智能体架构**:
```
本地智能体池 → 可配置池大小 → 未来可分布式
```

**扩展路径**:

**阶段 1: 本地多智能体** (当前方案)
```yaml
agent_pool:
  type: local
  pool_size: 4
  location: same_process
```

**阶段 2: 本地多进程**
```yaml
agent_pool:
  type: multiprocess
  pool_size: 8
  location: same_machine
```

**阶段 3: 分布式智能体** (未来)
```yaml
agent_pool:
  type: distributed
  pool_size: 32
  nodes:
    - host: node1, agents: 8
    - host: node2, agents: 8
    - host: node3, agents: 8
  - host: node4, agents: 8
```

**收益**:
- 当前: 支持 4-16 智能体（单机）
- 未来: 支持 100+ 智能体（分布式）
- 架构无需重构，仅需扩展 AgentPoolManager

#### 1.2.2 弹性伸缩

**动态调整池大小**:
```python
class DynamicAgentPool:
    def auto_scale(self):
        queue_depth = self.get_queue_depth()
      current_size = self.get_pool_size()
        
        # 队列积压 > 10，扩容
      if queue_depth > 10 and current_size < self.max_size:
            self.scale_up(target=current_size + 2)
        
      # 队列空闲 > 5 分钟，缩容
     elif self.idle_time > 300 and current_size > self.min_size:
            self.scale_down(target=current_size - 2)
```

**收益**:
- 高峰期: 自动扩容到 16 智能体
- 低峰期: 自动缩容到 4 智能体
- 成本节省: 平均节省 40% 资源

### 1.3 可靠性收益

#### 1.3.1 故障隔离

**当前问题**:
```python
# 顺序执行 - 一个文件失败，整个阶段失败
for file in files:
    try:
        code = llm.generate(file)
    except Exception as e:
        # 整个 Phase 4 失败
        raise PhaseFailureError(f"Failed at {file}")
```

**多智能体方案**:
```python
# 并行执行 - 故障隔离
results = []
for agent in agent_pool:
    try:
        result = agent.execute(work_item)
        results.append(result)
    except Exception as e:
        # 仅该智能体失败，其他继续
        failed_items.append(work_item)
        # 工作项重新入队，分配给其他智能体
        work_queue.put(work_item)

# 部分成功也能继续
if len(results) >= threshold:
  return PhaseResult(success=True, partial=True)
```

**收益量化**:
- 当前: 1 个文件失败 → 整个阶段失败 (0% 容错)
- 多智能体: 1 个文件失败 → 其他 9 个成功 (90% 容错)
- 可用性提升: 95% → 99.5%

#### 1.3.2 自动重试与恢复

**智能重试策略**:
```python
class SmartRetryPolicy:
    def should_retry(self, error: Exception, attempt: int) -> bool:
        # LLM API 错误 - 重试
        if isinstance(error, LLMAPIError):
            return attempt < 3
        
        # 网络超时 - 重试
        if isinstance(error, TimeoutError):
            return attempt < 5
        
        # 语法错误 - 不重试（需要修改 prompt）
        if isinstance(error, SyntaxError):
       return False
        
        return attempt < 3
    
    def get_backoff_delay(self, attempt: int) -> float:
        # 指数退避: 1s, 2s, 4s, 8s, 16s
        return min(2 ** attempt, 30)
```

**工作项重分配**:
```python
# Agent 1 失败 3 次后，分配给 Agent 2
work_item.failed_agents = [agent1.id]
work_item.retry_count = 3

# 分配给不同的智能体
agent2 = pool.acquire_agent(exclude=work_item.failed_agents)
result = agent2.execute(work_item)
```

**收益**:
- 重试成功率: 85% (3 次重试)
- 平均恢复时间: 从 5 分钟降到 30 秒
- 人工介入减少: 80%

### 1.4 可观测性收益

#### 1.4.1 细粒度进度追踪

**当前状态**:
```
[Phase 4] 代码生成中... (无进度信息)
```

**多智能体状态**:
```
[Phase 4] 代码生成中...
  ├─ Agent-1: ✓ user.py (完成)
  ├─ Agent-2: ⟳ order.py (生成中 45%)
  ├─ Agent-3: ✓ product.py (完成)
  ├─ Agent-4: ⏳ payment.py (队列中)
  └─ 进度: 7/10 文件 (70%)
```

**实时监控**:
```python
# 实时指标
metrics = {
    "total_files": 10,
    "completed": 7,
    "in_progress": 2,
    "queued": 1,
    "failed": 0,
    "progress_percent": 70,
    "estimated_remaining": "45s",
    "agent_utilization": {
        "agent-1": "idle",
        "agent-2": "working",
        "agent-3": "idle",
        "agent-4": "working"
    }
}
```

#### 1.4.2 性能分析
**智能体性能对比**:
```python
agent_stats = {
    "agent-1": {
        "completed": 3,
        "avg_duration": 28.5,
        "success_rate": 100%,
        "quality_score": 8.5
    },
    "agent-2": {
        "completed": 2,
        "avg_duration": 35.2,
        "success_rate": 100%,
        "quality_score": 8.2
    },
    "agent-3": {
        "completed": 3,
        "avg_duration": 25.8,
     "success_rate": 66%,  # 1 次失败
        "quality_score": 7.9
    }
}
```

**优化建议**:
- Agent-3 成功率低 → 检查配置或替换
- Agent-3 速度快但质量低 → 调整 temperature
- Agent-1 表现最佳 → 作为基准配置

### 1.5 成本收益

#### 1.5.1 时间成本

**开发者时间节省**:
```
场景: 生成 20 个文件的项目

当前: 10 分钟等待 → 开发者切换任务 → 上下文切换成本
多智能体: 3 分钟等待 → 开发者保持专注 → 无上下文切换

时间节省: 7 分钟/次
迭代次数: 平均 5 次/天
每日节省: 35 分钟
每月节省: 14 小时
年度节省: 168 小时 (21 个工作日)
```

**价值量化**:
- 开发者时薪: $50/小时
- 年度节省: 168 小时 × $50 = $8,400/人
- 10 人团队: $84,000/年

#### 1.5.2 LLM API 成本

**成本对比**:
```
顺序执行:
  - 10 个文件 × 1 次调用 = 10 次调用
  - 每次 4K tokens (input) + 2K tokens (output)
  - 总计: 40K input + 20K output
  - 成本: $0.60

多智能体并行:
  - 10 个文件 × 1 次调用 = 10 次调用 (相同)
  - 每次 4K tokens (input) + 2K tokens (output)
  - 总计: 40K input + 20K output
  - 成本: $0.60 (相同)
```

**关键发现**: LLM API 成本不增加，仅执行时间减少

#### 1.5.3 基础设施成本

**额外资源需求**:
```
单智能体:
  - 内存: 500MB
  - CPU: 1 核 × 20% = 0.2 核
  - 网络: 1 Mbps

4 智能体:
  - 内存: 500MB + 4 × 100MB = 900MB
  - CPU: 1 核 × 80% = 0.8 核
  - 网络: 4 Mbps

增量成本:
  - 内存: +400MB (~$0.02/月)
  - CPU: +0.6 核 (~$5/月)
  - 网络: +3 Mbps (~$1/月)
  - 总计: ~$6/月
```

**ROI 计算**:
```
成本: $6/月
收益: $700/月 (开发者时间节省)
ROI: 11,600%
回本周期: < 1 天
```

---

## 2. 智能体间通信机制

### 2.1 通信架构

#### 2.1.1 整体架构

```
┌──────────────────────────────────────────────────┐
│                    Coordinator                          │
│  (中央协调器 - 唯一的控制点)                                │
└────────┬──────────────────────────────┬────────┘
         │                           │
         │ 命令通道                 │ 事件通道
         │ (Command Channel)             │ (Event Channel)
         ↓                 ↑
┌──────────────────────────────────────────┐
│                  Message Bus                    │
│  (消息总线 - 异步解耦)                        │
└────┬───────────┬───────────┬───────────┬────────┘
     │           │           │           │
     ↓           ↓           ↓           ↓
┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│Agent 1 │  │Agent 2 │  │Agent 3 │  │Agent 4 │
│        │  │     │  │        │        │
│ 独立状态 │  │ 独立状态 │  │ 独立状态 │  │ 独立状态 │
└────────┘  └────────┘  └────────┘  └────────┘
```

**关键设计原则**:
1. **无直接通信**: 智能体之间不直接通信
2. **中央协调**: 所有通信通过 Coordinator
3. **异步解耦**: 使用消息总线异步传递
4. **状态隔离**: 每个智能体维护独立状态

#### 2.1.2 通信层次

```
┌────────────────────────────────┐
│ Layer 4: 业务协议层                      │
│ WorkItem, WorkResult, PhaseResult                  │
└──────────────────────────────────────┘
         ↕
┌────────────────────┐
│ Layer 3: 消息协议层                        │
│ Command, Event, Request, Response                    │
└─────────────────────────────────┘
         ↕
┌──────────────────────────────────┐
│ Layer 2: 传输层                         │
│ MessageBus (内存队列 / Redis / RabbitMQ)            │
└───────────────────────────────────┘
         ↕
┌────────────────────────────────────┐
│ Layer 1: 序列化层                        │
│ JSON / Pickle / Protocol Buffers               │
└───────────────────────────────┘
```

### 2.2 消息类型

#### 2.2.1 命令消息 (Coordinator → Agent)

**ASSIGN_WORK**: 分配工作项
```python
@dataclass
class AssignWorkCommand:
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    command_type: str = "ASSIGN_WORK"
    
    # 目标智能体
    target_agent_id: str
    
    # 工作项
    work_item: WorkItem
    
    # 优先级
    priority: int = 0
    
    # 超时设置
    timeout_seconds: int = 300
    
    # 重试配置
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
```

**CANCEL_WORK**: 取消工作
```python
@dataclass
class CancelWorkCommand:
    message_id: str
    timestamp: datetime
    command_type: str = "CANCEL_WORK"
    
    target_agent_id: str
    work_item_id: str
    reason: str
```

**SHUTDOWN**: 关闭智能体
```python
@dataclass
class ShutdownCommand:
    message_id: str
    timestamp: datetime
    command_type: str = "SHUTDOWN"
    
    target_agent_id: str
    graceful: bool = True  # 优雅关闭
    timeout_seconds: int = 30
```

#### 2.2.2 事件消息 (Agent → Coordinator)

**WORK_STARTED**: 工作开始
```python
@dataclass
class WorkStartedEvent:
    message_id: str
    timestamp: datetime
    event_type: str = "WORK_STARTED"
    
    agent_id: str
    work_item_id: str
    estimated_duration_seconds: int
```
**WORK_PROGRESS**: 工作进度
```python
@dataclass
class WorkProgressEvent:
    message_id: str
    timestamp: datetime
    event_type: str = "WORK_PROGRESS"
    
    agent_id: str
    work_item_id: str
    progress_percent: float  # 0-100
  current_step: str
    message: str
```

**WORK_COMPLETED**: 工作完成
```python
@dataclass
class WorkCompletedEvent:
    message_id: str
    timestamp: datetime
    event_type: str = "WORK_COMPLETED"
    
    agent_id: str
    work_item_id: str
    result: WorkResult
    duration_ms: int
    success: bool
```

**WORK_FAILED**: 工作失败
```python
@dataclass
class WorkFailedEvent:
    message_id: str
    timestamp: datetime
    event_type: str = "WORK_FAILED"
    
    agent_id: str
    work_item_id: str
    error: str
    error_type: str
    stack_trace: str
    retry_count: int
    can_retry: bool
```

**AGENT_HEARTBEAT**: 心跳
```python
@dataclass
class AgentHeartbeatEvent:
    message_id: str
    timestamp: datetime
    event_type: str = "AGENT_HEARTBEAT"
    
    agent_id: str
    status: AgentStatus  # IDLE, WORKING, ERROR
    current_work_item_id: Optional[str]
    memory_usage_mb: float
    cpu_usage_percent: float
```

### 2.3 消息总线实现

#### 2.3.1 内存队列实现（本地单机）

```python
import asyncio
from collections import defaultdict
from typing import Dict, List, Callable

class InMemoryMessageBus:
    """基于 asyncio.Queue 的内存消息总线"""
    
    def __init__(self):
        # 命令队列: agent_id → Queue[Command]
        self.command_queues: Dict[str, asyncio.Queue] = {}
        
        # 事件队列: event_type → Queue[Event]
        self.event_queues: Dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
        
        # 订阅者: event_type → List[Callable]
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        
      # 消息历史（用于调试）
        self.message_history: List[Message] = []
        self.max_history_size = 1000
    
    async def send_command(self, agent_id: str, command: Command):
        """发送命令到指定智能体"""
        if agent_id not in self.command_queues:
            self.command_queues[agent_id] = asyncio.Queue()
        
        await self.command_queues[agent_id].put(command)
        self._record_message(command)
    
    async def receive_command(self, agent_id: str, timeout: float = None) -> Command:
        """智能体接收命令"""
        if agent_id not in self.command_queues:
            self.command_queues[agent_id] = asyncio.Queue()
        
        try:
            if timeout:
           command = await asyncio.wait_for(
                  self.command_queues[agent_id].get(),
            timeout=timeout
                )
            else:
                command = await self.command_queues[agent_id].get()
            return command
        except asyncio.TimeoutError:
          return None
    
    async def publish_event(self, event: Event):
        """发布事件"""
        event_type = event.event_type
        
        # 放入事件队列
        await self.event_queues[event_type].put(event)
        
        # 通知所有订阅者
        for callback in self.subscribers[event_type]:
            try:
         if asyncio.iscoroutinefunction(callback):
                  await callback(event)
             else:
                 callback(event)
          except Exception as e:
              print(f"Error in subscriber callback: {e}")
        
        self._record_message(event)
    
    def subscribe(self, event_type: str, callback: Callable):
        """订阅事件"""
     self.subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable):
        """取消订阅"""
        if callback in self.subscribers[event_type]:
            self.subscribers[event_type].remove(callback)
    
    def _record_message(self, message: Message):
        """记录消息历史"""
        self.message_history.append(message)
        if len(self.message_history) > self.max_history_size:
            self.message_history.pop(0)
```

#### 2.3.2 Redis 实现（分布式）

```python
import redis.asyncio as redis
import json

class RedisMessageBus:
    """基于 Redis 的分布式消息总线"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)
        self.pubsub = self.redis.pubsub()
    
    async def send_command(self, agent_id: str, command: Command):
        """发送命令到 Redis 队列"""
        queue_key = f"agent:{agent_id}:commands"
        command_json = json.dumps(asdict(command))
        await self.redis.lpush(queue_key, command_json)
    
    async def receive_command(self, agent_id: str, timeout: float = None) -> Command:
        """从 Redis 队列接收命令"""
      queue_key = f"agent:{agent_id}:commands"
        
      if timeout:
          result = await self.redis.brpop(queue_key, timeout=int(timeout))
      else:
            result = await self.redis.brpop(queue_key)
     
        if result:
            _, command_json = result
          command_dict = json.loads(command_json)
            return Command(**command_dict)
        return None
    
    async def publish_event(self, event: Event):
    """发布事件到 Redis Pub/Sub"""
        channel = f"events:{event.event_type}"
        event_json = json.dumps(asdict(event))
        await self.redis.publish(channel, event_json)
    
    async def subscribe(self, event_type: str, callback: Callable):
        """订阅 Redis Pub/Sub 频道"""
        channel = f"events:{event_type}"
    await self.pubsub.subscribe(channel)
        
        # 启动监听循环
        asyncio.create_task(self._listen_loop(callback))
    
    async def _listen_loop(self, callback: Callable):
        """监听 Redis Pub/Sub 消息"""
        async for message in self.pubsub.listen():
            if message['type'] == 'message':
           event_dict = json.loads(message['data'])
      event = Event(**event_dict)
              await callback(event)
```

### 2.4 通信流程详解

#### 2.4.1 工作分配流程

```
时间轴:
T0: Coordinator 准备工作项
T1: Coordinator 发送 ASSIGN_WORK 命令
T2: Agent 接收命令
T3: Agent 发送 WORK_STARTED 事件
T4: Agent 执行工作（定期发送 WORK_PROGRESS）
T5: Agent 发送 WORK_COMPLETED 事件
T6: Coordinator 接收结果

详细步骤:
```

```python
# T0-T1: Coordinator 分配工作
async def distribute_work(self, work_items: List[WorkItem]):
    for work_item in work_items:
        # 获取可用智能体
        agent = await self.agent_pool.acquire_agent()
        
        # 创建命令
        command = AssignWorkCommand(
            target_agent_id=agent.id,
            work_item=work_item,
            timeout_seconds=300
        )
        
        # 发送命令
        await self.message_bus.send_command(agent.id, command)
        
        # 记录分配
        self.work_assignments[work_item.id] = agent.id

# T2-T3: Agent 接收并开始工作
async def agent_main_loop(self):
    while self.running:
        # 接收命令
        command = await self.message_bus.receive_command(
            self.agent_id,
            timeout=1.0
     )
        
      if isinstance(command, AssignWorkCommand):
            # 发送开始事件
            await self.message_bus.publish_event(
              WorkStartedEvent(
                 agent_id=self.agent_id,
                    work_item_id=command.work_item.id,
              estimated_duration_seconds=30
              )
            )
            
         # 执行工作
       result = await self.execute_work(command.work_item)
            
            # 发送完成事件
        await self.message_bus.publish_event(
                WorkCompletedEvent(
                    agent_id=self.agent_id,
                    work_item_id=command.work_item.id,
                 result=result,
                  duration_ms=result.duration_ms,
                    success=result.success
           )
            )

# T4: Agent 执行工作并报告进度
async def execute_work(self, work_item: WorkItem) -> WorkResult:
    try:
        # 步骤 1: 加载上下文
        await self.report_progress(work_item.id, 10, "加载上下文")
        context = await self.load_context(work_item)
        
        # 步骤 2: 生成代码
        await self.report_progress(work_item.id, 30, "生成代码")
     code = await self.llm_client.generate(work_item.prompt)
        
        # 步骤 3: 验证语法
        await self.report_progress(work_item.id, 70, "验证语法")
        is_valid = await self.validate_syntax(code)
      
        # 步骤 4: 完成
        await self.report_progress(work_item.id, 100, "完成")
        
        return WorkResult(
            work_item_id=work_item.id,
            code=code,
            is_valid=is_valid,
            success=True
        )
    except Exception as e:
        return WorkResult(
            work_item_id=work_item.id,
            error=str(e),
            success=False
        )

async def report_progress(self, work_item_id: str, percent: float, message: str):
    await self.message_bus.publish_event(
        WorkProgressEvent(
            agent_id=self.agent_id,
         work_item_id=work_item_id,
          progress_percent=percent,
            message=message
    )
    )

# T5-T6: Coordinator 接收结果
async def collect_results(self):
    # 订阅完成事件
    self.message_bus.subscribe(
        "WORK_COMPLETED",
        self.on_work_completed
    )
    
    # 订阅失败事件
    self.message_bus.subscribe(
        "WORK_FAILED",
        self.on_work_failed
    )
    
    # 等待所有工作完成
    while len(self.completed_work) < len(self.total_work):
        await asyncio.sleep(0.1)
    
    return self.aggregate_results()

async def on_work_completed(self, event: WorkCompletedEvent):
    # 记录结果
    self.completed_work[event.work_item_id] = event.result
    
    # 释放智能体
    agent_id = self.work_assignments[event.work_item_id]
    await self.agent_pool.release_agent(agent_id)
  
    # 更新进度
    progress = len(self.completed_work) / len(self.total_work) * 100
    print(f"进度: {progress:.1f}%")
```

#### 2.4.2 心跳与健康检查

```python
class AgentHealthMonitor:
    """智能体健康监控"""
    
    def __init__(self, message_bus: MessageBus):
        self.message_bus = message_bus
        self.agent_last_heartbeat: Dict[str, datetime] = {}
        self.heartbeat_timeout = 30  # 30 秒无心跳视为异常
    
    async def start_monitoring(self):
        """启动监控"""
        # 订阅心跳事件
        self.message_bus.subscribe(
            "AGENT_HEARTBEAT",
          self.on_heartbeat
        )
        
      # 启动检查循环
     asyncio.create_task(self.check_loop())
  
    async def on_heartbeat(self, event: AgentHeartbeatEvent):
        """接收心跳""
        self.agent_last_heartbeat[event.agent_id] = event.timestamp
    
    async def check_loop(self):
        """定期检查智能体健康状态"""
        while True:
            await asyncio.sleep(10)  # 每 10 秒检查一次
         
            now = datetime.now()
        for agent_id, last_heartbeat in self.agent_last_heartbeat.items():
              elapsed = (now - last_heartbeat).total_seconds()
                
                if elapsed > self.heartbeat_timeout:
              # 智能体超时
            await self.handle_agent_timeout(agent_id)
    
    async def handle_agent_timeout(self, agent_id: str):
        ""处理智能体超时"""
     print(f"[WARNING] Agent {agent_id} timeout, restarting...")
        
        # 1. 取消当前工作
        work_item_id = self.get_current_work(agent_id)
        if work_item_id:
            await self.message_bus.send_command(
                agent_id,
             CancelWorkCommand(
             target_agent_id=agent_id,
                work_item_id=work_item_id,
                 reason="Agent timeout"
              )
        )
        
        # 2. 重启智能体
        await self.agent_pool.restart_agent(agent_id)
        
        # 3. 重新分配工作
        if work_item_id:
            await self.reassign_work(work_item_id)
```

#### 2.4.3 错误处理与重试

```python
class WorkItemRetryHandler:
    """工作项重试处理器"""
    
    def __init__(self, message_bus: MessageBus, max_retries: int = 3):
        self.message_bus = message_bus
        self.max_retries = max_retries
        self.retry_counts: Dict[str, int] = {}
        self.failed_agents: Dict[str, List[str]] = {}
    
    async def on_work_failed(self, event: WorkFailedEvent):
        """处理工作失败"""
        work_item_id = event.work_item_id
        agent_id = event.agent_id
      
        # 记录失败的智能体
        if work_item_id not in self.failed_agents:
          self.failed_agents[work_item_id] = []
        self.failed_agents[work_item_id].append(agent_id)
        
        # 增加重试计数
        self.retry_counts[work_item_id] = self.retry_counts.get(work_item_id, 0) + 1
        
        # 判断是否可以重试
      if self.retry_counts[work_item_id] < self.max_retries:
            # 重试
            await self.retry_work(work_item_id, event.can_retry)
        else:
          # 达到最大重试次数，标记为永久失败
        await self.mark_as_permanently_failed(work_item_id, event.error)
    
    async def retry_work(self, work_item_id: str, can_retry: bool):
        """重试工作项"""
        if not can_retry:
          # 不可重试的错误（如语法错误），需要人工介入
            await self.mark_as_permanently_failed(
                work_item_id,
          "Non-retryable error"
      )
          return
        
        # 获取工作项
        work_item = self.get_work_item(work_item_id)
        
        # 选择新的智能体（排除已失败的）
        failed_agents = self.failed_agents.get(work_item_id, [])
     agent = await self.agent_pool.acquire_agent(exclude=failed_agents)
        
        if agent is None:
            # 没有可用智能体
          await self.mark_as_permanently_failed(
                work_item_id,
           "No available agents"
         )
            return
        
        # 计算退避延迟
        retry_count = self.retry_counts[work_item_id]
        delay = min(2 ** retry_count, 30)  # 1s, 2s, 4s, ..., 最多 30s
        
        print(f"[RETRY] Work {work_item_id} retry {retry_count}/{self.max_retries} after {delay}s")
        
        # 延迟后重新分配
        await asyncio.sleep(delay)
        await self.message_bus.send_command(
            agent.id,
            AssignWorkCommand(
                target_agent_id=agent.id,
          work_item=work_item,
        retry_count=retry_count
            )
        )
```

### 2.5 状态同步机制

#### 2.5.1 共享状态管理

```python
class SharedStateManager:
    """共享状态管理器（用于依赖解析）"""
    
    def __init__(self):
     # 文件生成状态: file_path → status
        self.file_status: Dict[str, FileStatus] = {}
        self.file_status_lock = asyncio.Lock()
        
     # 依赖等待队列: file_path → List[work_item_id]
        self.dependency_waiters: Dict[str, List[str]] = {}
    
    async def mark_file_completed(self, file_path: str):
        """标记文件完成"""
        async with self.file_status_lock:
            self.file_status[file_path] = FileStatus.COMPLETED
            
            # 通知等待者
            if file_path in self.dependency_waiters:
      for work_item_id in self.dependency_waiters[file_path]:
            await self.notify_dependency_ready(work_item_id, file_path)
                
          # 清空等待队列
             del self.dependency_waiters[file_path]
    
    async def wait_for_dependencies(self, work_item: WorkItem) -> bool:
        """等待依赖文件完成"""
        for dep_file in work_item.dependencies:
            async with self.file_status_lock:
                status = self.file_status.get(dep_file, FileStatus.PENDING)
          
                if status == FileStatus.COMPLETED:
                    continue
           elif status == FileStatus.FAILED:
                  return False  # 依赖失败
         else:
                    # 加入等待队列
                    if dep_file not in self.dependency_waiters:
                   self.dependency_waiters[dep_file] = []
                    self.dependency_waiters[dep_file].append(work_item.id)
        
        return True
    
    async def notify_dependency_ready(self, work_item_id: str, file_path: str):
     """通知依赖就绪"""
        await self.message_bus.publish_event(
            DependencyReadyEvent(
              work_item_id=work_item_id,
                dependency_file=file_path
          )
        )
```

#### 2.5.2 分布式锁（用于关键资源）

```python
class DistributedLock:
    """分布式锁（基于 Redis）"""
    
    def __init__(self, redis_client: redis.Redis, key: str, timeout: int = 30):
        self.redis = redis_client
        self.key = f"lock:{key}"
      self.timeout = timeout
        self.lock_id = str(uuid.uuid4())
    
    async def acquire(self, blocking: bool = True, timeout: float = None) -> bool:
    """获取锁"""
        start_time = time.time()
        
        while True:
          # 尝试设置锁
        acquired = await self.redis.set(
                self.key,
                self.lock_id,
             nx=True,  # 仅当 key 不存在时设置
                ex=self.timeout  # 过期时间
            )
            
            if acquired:
             return True
       
            if not blocking:
          return False
            
            # 检查超时
       if timeout and (time.time() - start_time) > timeout:
                return False
            
            # 等待后重试
            await asyncio.sleep(0.1)
    
    async def release(self):
      """释放锁""
      # Lua 脚本确保原子性
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
     """
        await self.redis.eval(lua_script, 1, self.key, self.lock_id)
    
    async def __aenter__(self):
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.release()

# 使用示例
async def write_shared_resource(resource_id: str, data: str):
    """写入共享资源（需要加锁）"""
    lock = DistributedLock(redis_client, f"resource:{resource_id}")
    
    async with lock:
        # 临界区：只有一个智能体可以执行
        await write_file(resource_id, data)
        await update_metadata(resource_id)
```

---

## 3. 工作流协调细节

### 3.1 依赖解析算法

#### 3.1.1 拓扑排序实现

```python
class DependencyResolver:
    """依赖解析器 - 拓扑排序"""
    
    def resolve(self, work_items: List[WorkItem]) -> List[List[WorkItem]]:
      """
      将工作项按依赖关系分组为多个阶段
        
        Returns:
            List[List[WorkItem]]: 每个子列表是一个可并行执行的阶段
      """
        # 1. 构建依赖图
        graph = self.build_dependency_graph(work_items)
        
      # 2. 检测循环依赖
        if self.has_cycle(graph):
            raise DependencyError("Circular dependency detected")
        # 3. 拓扑排序
        stages = self.topological_sort(graph)
        
        return stages
    
    def build_dependency_graph(self, work_items: List[WorkItem]) -> Dict:
        """构建依赖图"""
        graph = {
            'nodes': {},  # work_item_id → WorkItem
            'edges': {},  # work_item_id → List[dependency_ids]
          'in_degree': {}  # work_item_id → 入度
        }
        
        # 添加节点
        for item in work_items:
            graph['nodes'][item.id] = item
            graph['edges'][item.id] = []
            graph['in_degree'][item.id] = 0
        
        # 添加边
        for item in work_items:
            for dep_file in item.dependencies:
      # 找到依赖的工作项
                dep_item_id = self.find_work_item_by_file(work_items, dep_file)
                if dep_item_id:
                    graph['edges'][dep_item_id].append(item.id)
                graph['in_degree'][item.id] += 1
        
        return graph
    
    def has_cycle(self, graph: Dict) -> bool:
        """检测循环依赖（DFS）"""
        visited = set()
        rec_stack = set()
        
        def dfs(node_id: str) -> bool:
          visited.add(node_id)
            rec_stack.add(node_id)
            
        for neighbor in graph['edges'][node_id]:
                if neighbor not in visited:
                  if dfs(neighbor):
                     return True
          elif neighbor in rec_stack:
               return True  # 发现环
            
            rec_stack.remove(node_id)
         return False
        
        for node_id in graph['nodes']:
            if node_id not in visited:
           if dfs(node_id):
                    return True
        
        return False
    
    def topological_sort(self, graph: Dict) -> List[List[WorkItem]]:
        """Kahn 算法拓扑排序"""
        stages = []
        in_degree = graph['in_degree'].copy()
      
        while True:
            # 找到所有入度为 0 的节点（当前阶段）
            current_stage = [
                graph['nodes'][node_id]
                for node_id, degree in in_degree.items()
             if degree == 0
       ]
            
            if not current_stage:
                break
            
            stages.append(current_stage)
            
            # 移除当前阶段的节点，更新入度
            for item in current_stage:
            del in_degree[item.id]
           for neighbor in graph['edges'][item.id]:
                    if neighbor in in_degree:
                in_degree[neighbor] -= 1
      
        # 检查是否所有节点都已处理
        if in_degree:
         raise DependencyError(f"Unresolved dependencies: {list(in_degree.keys())}")
        
        return stages
```

#### 3.1.2 依赖解析示例

```python
# 示例：10 个文件的依赖关系
work_items = [
    WorkItem(id="1", file="models/user.py", dependencies=[]),
  WorkItem(id="2", file="models/order.py", dependencies=[]),
    WorkItem(id="3", file="models/product.py", dependencies=[]),
    WorkItem(id="4", file="services/user_service.py", dependencies=["models/user.py"]),
    WorkItem(id="5", file="services/order_service.py", dependencies=["models/order.py", "models/user.py"]),
    WorkItem(id="6", file="services/product_service.py", dependencies=["models/product.py"]),
    WorkItem(id="7", file="api/user_api.py", dependencies=["services/user_service.py"]),
    WorkItem(id="8", file="api/order_api.py", dependencies=["services/order_service.py"]),
    WorkItem(id="9", file="api/product_api.py", dependencies=["services/product_service.py"]),
    WorkItem(id="10", file="main.py", dependencies=["api/user_api.py", "api/order_api.py", "api/product_api.py"]),
]

# 解析结果
resolver = DependencyResolver()
stages = resolver.resolve(work_items)

# 输出:
# Stage 0 (并行): models/user.py, models/order.py, models/product.py
# Stage 1 (并行): services/user_service.py, services/order_service.py, services/product_service.py
# Stage 2 (并行): api/user_api.py, api/order_api.py, api/product_api.py
# Stage 3 (顺序): main.py
```

**执行时间对比**:
```
顺序执行: 10 × 30s = 300s

多智能体（4 个）:
- Stage 0: 3 个文件，1 批次 = 30s
- Stage 1: 3 个文件，1 批次 = 30s
- Stage 2: 3 个文件，1 批次 = 30s
- Stage 3: 1 个文件，1 批次 = 30s
- 总计: 120s

加速比: 300s / 120s = 2.5x
```

### 3.2 工作调度策略

#### 3.2.1 调度算法对比

**1. FIFO (First In First Out) - 先进先出**
```python
class FIFOScheduler:
    def schedule(self, work_queue: Queue, agent_pool: AgentPool):
        while not work_queue.empty():
       work_item = work_queue.get()  # 按顺序取出
            agent = agent_pool.acquire_agent()  # 获取任意可用智能体
         agent.execute(work_item)
```
- 优点: 简单，公平
- 缺点: 不考虑优先级和依赖

**2. Priority-based - 基于优先级**
```python
class PriorityScheduler:
    def schedule(self, work_queue: PriorityQueue, agent_pool: AgentPool):
        while not work_queue.empty():
            work_item = work_queue.get()  # 按优先级取出
            agent = agent_pool.acquire_agent()
            agent.execute(work_item)

# 优先级定义
priority_rules = {
    "models/*": 100,      # 最高优先级
    "services/*": 50,     # 中等优先级
    "api/*": 10,          # 低优先级
    "tests/*": 5          # 最低优先级
}
```
- 优点: 关键文件优先生成
- 缺点: 可能导致低优先级任务饥饿

**3. Dependency-aware - 依赖感知**
```python
class DependencyAwareScheduler:
    def schedule(self, work_items: List[WorkItem], agent_pool: AgentPool):
        # 1. 拓扑排序
        stages = dependency_resolver.resolve(work_items)
        
        # 2. 按阶段执行
        for stage in stages:
            # 同一阶段内并行执行
            await asyncio.gather(*[
                self.assign_to_agent(item, agent_pool)
              for item in stage
            ])
```
- 优点: 保证依赖顺序，最大化并行
- 缺点: 需要预先分析依赖

**4. Work-stealing - 工作窃取**
```python
class WorkStealingScheduler:
    def __init__(self, agent_pool: AgentPool):
        # 每个智能体有自己的工作队列
        self.agent_queues = {
            agent.id: deque()
            for agent in agent_pool.agents
        }
    
    async def agent_worker(self, agent: Agent):
        while True:
            # 1. 尝试从自己的队列获取工作
        if self.agent_queues[agent.id]:
                work_item = self.agent_queues[agent.id].popleft()
            else:
             # 2. 自己的队列空了，尝试从其他智能体"窃取"工作
                work_item = self.steal_work(agent.id)
            
            if work_item:
        await agent.execute(work_item)
            else:
                await asyncio.sleep(0.1)
    
    def steal_work(self, thief_agent_id: str) -> Optional[WorkItem]:
        """从其他智能体的队列窃取工作"""
        for agent_id, queue in self.agent_queues.items():
            if agent_id != thief_agent_id and queue:
                # 从队列尾部窃取（减少竞争）
                return queue.pop()
        return None
```
- 优点: 负载均衡，无中央协调开销
- 缺点: 实现复杂，可能违反依赖顺序

**推荐方案**: Dependency-aware + Priority-based 混合
```python
class HybridScheduler:
    def schedule(self, work_items: List[WorkItem], agent_pool: AgentPool):
        # 1. 依赖解析 - 分阶段
        stages = dependency_resolver.resolve(work_items)
      
        # 2. 每个阶段内按优先级排序
        for stage in stages:
            stage.sort(key=lambda item: item.priority, reverse=True)
            
            # 3. 并行执行
      await self.execute_stage(stage, agent_pool)
```

#### 3.2 负载均衡策略

**1. Round-robin - 轮询**
```python
class RoundRobinBalancer:
    def __init__(self, agents: List[Agent]):
        self.agents = agents
        self.current_index = 0
    
    def select_agent(self) -> Agent:
        agent = self.agents[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.agents)
        return agent
```

**2. Least-loaded - 最少负载**
```python
class LeastLoadedBalancer:
    def select_agent(self, agent_pool: AgentPool) -> Agent:
        # 选择当前负载最小的智能体
        return min(
            agent_pool.agents,
            key=lambda agent: agent.current_workload
        )
```

**3. Performance-based - 基于性能**
```python
class PerformanceBasedBalancer:
    def __init__(self):
        self.agent_stats = {}  # agent_id → stats
    def select_agent(self, agent_pool: AgentPool, work_item: WorkItem) -> Agent:
        # 根据历史性能选择最佳智能体
      scores = {}
        for agent in agent_pool.available_agents:
         stats = self.agent_stats.get(agent.id, {})
            
            # 综合评分
            score = (
           stats.get('success_rate', 1.0) * 0.4 +
                (1 / stats.get('avg_duration', 30)) * 0.3 +
            stats.get('quality_score', 0.8) * 0.3
            )
            scores[agent.id] = score
        
        # 选择得分最高的
        best_agent_id = max(scores, key=scores.get)
        return agent_pool.get_agent(best_agent_id)
```

### 3.3 协调器状态机

```python
from enum import Enum

class CoordinatorState(Enum):
    IDLE = "idle"
    INITIALIZING = "initializing"
    DISTRIBUTING = "distributing"
    EXECUTING = "executing"
    COLLECTING = "collecting"
    COMPLETED = "completed"
    FAILED = "failed"

class PhaseCoordinator:
    def __init__(self):
        self.state = CoordinatorState.IDLE
        self.state_transitions = {
        CoordinatorState.IDLE: [CoordinatorState.INITIALIZING],
         CoordinatorState.INITIALIZING: [CoordinatorState.DISTRIBUTING, CoordinatorState.FAILED],
            CoordinatorState.DISTRIBUTING: [CoordinatorState.EXECUTING, CoordinatorState.FAILED],
            CoordinatorState.EXECUTING: [CoordinatorState.COLLECTING, CoordinatorState.FAILED],
            CoordinatorState.COLLECTING: [CoordinatorState.COMPLETED, CoordinatorState.FAILED],
            CoordinatorState.COMPLETED: [CoordinatorState.IDLE],
          CoordinatorState.FAILED: [CoordinatorState.IDLE],
        }
  
    def transition_to(self, new_state: CoordinatorState):
        """状态转换"""
        if new_state not in self.state_transitions[self.state]:
        raise InvalidStateTransitionError(
            f"Cannot transition from {self.state} to {new_state}"
     )
        
        old_state = self.state
        self.state = new_state
        
        # 发出状态变更事件
        self.message_bus.publish_event(
            CoordinatorStateChangedEvent(
              old_state=old_state,
                new_state=new_state,
                timestamp=datetime.now()
            )
        )
    
    async def execute(self, work_items: List[WorkItem]) -> PhaseResult:
        """执行工作流"""
        try:
            # IDLE → INITIALIZING
         self.transition_to(CoordinatorState.INITIALIZING)
            await self.initialize(work_items)
          
            # INITIALIZING → DISTRIBUTING
            self.transition_to(CoordinatorState.DISTRIBUTING)
            await self.distribute_work(work_items)
            
            # DISTRIBUTING → EXECUTING
          self.transition_to(CoordinatorState.EXECUTING)
            await self.monitor_execution()
            
            # EXECUTING → COLLECTING
            self.transition_to(CoordinatorState.COLLECTING)
            results = await self.collect_results()
            
            # COLLECTING → COMPLETED
            self.transition_to(CoordinatorState.COMPLETED)
            return PhaseResult(success=True, data=results)
          
        except Exception as e:
            # ANY → FAILED
            self.transition_to(CoordinatorState.FAILED)
            return PhaseResult(success=False, error=str(e))
        finally:
            # COMPLETED/FAILED → IDLE
            self.transition_to(CoordinatorState.IDLE)
```

---

## 4. 完整执行流程示例

### 4.1 端到端流程

```python
# ==========================================
# 场景: 生成 10 个文件，使用 4 个智能体
# ===============================================

async def phase4_multi_agent_execution():
    """Phase 4 多智能体执行完整流程"""
    
    # ========== 步骤 1: 初始化 ==========
    print("[1/6] 初始化...")
    
    # 1.1 创建消息总线
    message_bus = InMemoryMessageBus()
    
    # 1.2 创建智能体池
    agent_pool = AgentPoolManager(
        pool_size=4,
        agent_factory=CodeGeneratorAgentFactory(),
        message_bus=message_bus
    )
    await agent_pool.initialize()
    
    # 1.3 创建协调器
    coordinator = Phase4Coordinator(
        agent_pool=agent_pool,
        message_bus=message_bus,
        dependency_resolver=DependencyResolver(),
        scheduler=HybridScheduler()
    )
    
    # ========== 步骤 2: 准备工作项 ==========
    print("[2/6] 准备工作项...")
    
    work_items = [
        WorkItem(id="1", file="models/user.py", dependencies=[], priority=100),
        WorkItem(id="2", file="models/order.py", dependencies=[], priority=100),
        WorkItem(id="3", file="models/product.py", dependencies=[], priority=100),
      WorkItem(id="4", file="services/user_service.py", dependencies=["models/user.py"], priority=50),
        WorkItem(id="5", file="services/order_service.py", dependencies=["models/order.py"], priority=50),
        WorkItem(id="6", file="services/product_service.py", dependencies=["models/product.py"], priority=50),
        WorkItem(id="7", file="api/user_api.py", dependencies=["services/user_service.py"], priority=10),
        WorkItem(id="8", file="api/order_api.py", dependencies=["services/order_service.py"], priority=10),
      WorkItem(id="9", file="api/product_api.py", dependencies=["services/product_service.py"], priority=10),
        WorkItem(id="10", file="main.py", dependencies=["api/user_api.py", "api/order_api.py"], priority=5),
    ]
    
  # ========== 步骤 3: 依赖解析 ==========
    print("[3/6] 解析依赖...")
    
    stages = coordinator.dependency_resolver.resolve(work_items)
    print(f"  - 共 {len(stages)} 个阶段")
    for i, stage in enumerate(stages):
        print(f"  - Stage {i}: {len(stage)} 个文件可并行")
    
    # 输出:
    # - 共 4 个阶段
    # - Stage 0: 3 个文件可并行 (models)
    # - Stage 1: 3 个文件可并行 (services)
    # - Stage 2: 3 个文件可并行 (api)
    # - Stage 3: 1 个文件可并行 (main)
    
    # ======== 步骤 4: 分配工作 ==========
    print("[4/6] 分配工作...")
    
    for stage_num, stage in enumerate(stages):
     print(f"\n  [Stage {stage_num}] 开始执行 {len(stage)} 个文件...")
        
        # 并行分配
        tasks = []
      for work_item in stage:
          # 获取可用智能体
            agent = await agent_pool.acquire_agent()
            
            # 发送命令
            command = AssignWorkCommand(
                target_agent_id=agent.id,
           work_item=work_item,
         timeout_seconds=300
          )
            await message_bus.send_command(agent.id, command)
        
            print(f"    - {work_item.file} → Agent-{agent.id}")
        
        # ====== 步骤 5: 监控执行 ==========
        print(f"  [Stage {stage_num}] 监控执行...")
        
        # 订阅进度事件
        progress_tracker = ProgressTracker(stage)
        message_bus.subscribe("WORK_PROGRESS", progress_tracker.on_progress)
        message_bus.subscribe("WORK_COMPLETED", progress_tracker.on_completed)
        message_bus.subscribe("WORK_FAILED", progress_tracker.on_failed)
        
        # 等待阶段完成
        await progress_tracker.wait_for_completion()
        
      # 输出进度
      print(f"  [Stage {stage_num}] 完成:")
        print(f"    - 成功: {progress_tracker.completed_count}/{len(stage)}")
      print(f"    - 失败: {progress_tracker.failed_count}")
     print(f"    - 耗时: {progress_tracker.duration:.1f}s")
    
    # ========== 步骤 6: 收集结果 =====
    print("\n[6/6] 收集结果...")
    
    results = coordinator.collect_results()
    
    print(f"\n执行完成:")
    print(f"  - 总文件数: {len(work_items)}")
    print(f"  - 成功: {results.success_count}")
    print(f"  - 失败: {results.failed_count}")
    print(f"  - 总耗时: {results.total_duration:.1f}s")
    print(f"  - 加速比: {results.speedup:.1f}x")
    
    # 输出示例:
    # 执行完成:
    #   - 总文件数: 10
    #   - 成功: 10
    #   - 失败: 0
    #   - 总耗时: 120.5s
    #   - 加速比: 2.5x
    
    return results
```

### 4.2 实时输出示例

```
[1/6] 初始化...
  ✓ 消息总线已创建
  ✓ 智能体池已初始化 (4 个智能体)
  ✓ 协调器已创建

[2/6] 准备工作项...
  ✓ 10 个工作项已准备

[3/6] 解析依赖...
  - 共 4 个阶段
  - Stage 0: 3 个文件可并行 (models)
  - Stage 1: 3 个文件可并行 (services)
  - Stage 2: 3 个文件可并行 (api)
  - Stage 3: 1 个文件可并行 (main)

[4/6] 分配工作...

  [Stage 0] 开始执行 3 个文件...
    - models/user.py → Agent-1
    - models/order.py → Agent-2
    - models/product.py → Agent-3
  
  [Stage 0] 监控执行...
    Agent-1: models/user.py [████████░░] 80% - 验证语法
    Agent-2: models/order.py [██████████] 100% - 完成 ✓
    Agent-3: models/product.py [████░░░░] 60% - 生成代码
    
    Agent-1: models/user.py [██████████] 100% - 完成 ✓
    Agent-3: models/product.py [████████] 100% - 完成 ✓
  
  [Stage 0] 完成:
    - 成功: 3/3
    - 失败: 0
    - 耗时: 28.3s

  [Stage 1] 开始执行 3 个文件...
    - services/user_service.py → Agent-1
    - services/order_service.py → Agent-2
    - services/product_service.py → Agent-3
  
  [Stage 1] 监控执行...
    Agent-1: services/user_service.py [██████████] 100% - 完成 ✓
    Agent-2: services/order_service.py [██████████] 100% - 完成 ✓
    Agent-3: services/product_service.py [████████] 100% - 完成 ✓
  
  [Stage 1] 完成:
    - 成功: 3/3
    - 失败: 0
    - 耗时: 31.2s

  [Stage 2] 开始执行 3 个文件...
    - api/user_api.py → Agent-1
    - api/order_api.py → Agent-2
    - api/product_api.py → Agent-3
  
  [Stage 2] 监控执行...
    Agent-1: api/user_api.py [██████████] 100% - 完成 ✓
    Agent-2: api/order_api.py [██████████] 100% - 完成 ✓
    Agent-3: api/product_api.py [██████████] 100% - 完成 ✓
  
  [Stage 2] 完成:
    - 成功: 3/3
    - 失败: 0
    - 耗时: 29.8s

  [Stage 3] 开始执行 1 个文件...
    - main.py → Agent-1
  
  [Stage 3] 监控执行...
    Agent-1: main.py [██████████] 100% - 完成 ✓
  
  [Stage 3] 完成:
    - 成功: 1/1
    - 失败: 0
    - 耗时: 31.2s

[6/6] 收集结果...

执行完成:
  - 总文件数: 10
  - 成功: 10
  - 失败: 0
  - 总耗时: 120.5s
  - 加速比: 2.5x (vs 300s 顺序执行)
  
智能体统计:
  Agent-1: 4 个文件, 平均 29.5s, 成功率 100%
  Agent-2: 3 个文件, 平均 30.1s, 成功率 100%
  Agent-3: 3 个文件, 平均 29.8s, 成功率 100%
  Agent-4: 0 个文件 (未使用)
```

---

**文档结束**

## 总结

本文档详细阐述了多智能体架构的：

1. **核心收益**: 3-4 倍性能提升、更好的资源利用、故障隔离、细粒度监控
2. **通信机制**: 消息总线、命令/事件模型、状态同步、分布式锁
3. **工作流协调**: 依赖解析、调度策略、负载均衡、状态机
4. **完整流程**: 从初始化到结果收集的端到端执行

关键设计原则：
- 智能体间无直接通信，通过中央协调器
- 异步消息传递，解耦组件
- 依赖感知调度，最大化并行
- 故障隔离与自动恢复
