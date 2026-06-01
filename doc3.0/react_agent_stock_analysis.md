# React Agent 股票分析系统技术文档

> **项目名称**: React Agent Stock Analysis System  
> **版本**: v1.0  
> **日期**: 2026-05-25  
> **作者**: DevPalAgent Team

---

## 目录

1. [系统概述](#1-系统概述)
2. [核心概念](#2-核心概念)
3. [架构设计](#3-架构设计)
4. [技术实现](#4-技术实现)
5. [工具系统](#5-工具系统)
6. [React循环机制](#6-react循环机制)
7. [代码实现](#7-代码实现)
8. [使用示例](#8-使用示例)
9. [性能优化](#9-性能优化)
10. [扩展方向](#10-扩展方向)

---

## 1. 系统概述

### 1.1 项目背景

传统的股票分析系统存在以下问题：
- **单次推理局限**：LLM一次性输出，无法获取实时数据
- **信息孤岛**：无法调用外部工具和API
- **推理链断裂**：缺乏迭代推理能力
- **结果不可靠**：基于训练数据，无法获取最新信息

### 1.2 解决方案

**React Agent** = **Reasoning（推理）** + **Acting（行动）**

核心思想：
```
传统AI流程：
输入 → 推理 → 输出

React Agent流程：
输入 → 推理 → 行动 → 观察 → 推理 → 行动 → ... → 输出
     ↑______________________↓
         循环迭代
```

### 1.3 系统特点

| 特性 | 说明 |
|------|------|
| **迭代推理** | 多轮思考-行动-观察循环 |
| **工具调用** | 集成5+股票分析工具 |
| **实时数据** | 获取最新市场信息 |
| **可解释性** | 完整的推理链路追踪 |
| **可扩展性** | 工具注册机制，易于扩展 |

---

## 2. 核心概念

### 2.1 React模式

**React = Reasoning + Acting**

#### Reasoning（推理）
```
Thought: 我需要分析股票2600001明天的涨跌
         首先需要获取这只股票的基本信息
```

#### Acting（行动）
```
Action: get_stock_info
Action Input: {"stock_code": "2600001"}
```

#### Observation（观察）
```
Observation: {
  "code": "2600001",
  "name": "中国太保",
  "current_price": 28.50,
  "industry": "保险"
}
```

#### 循环迭代
```
Thought → Action → Observation → Thought → Action → ...
```

### 2.2 工作流程

```
┌───────────────────────────────────┐
│       用户输入                      │
│         "分析2600001股票明天涨跌"                    │
└────────────────┬────────────────────────────────┘
               │
                 ▼
┌────────────────────────────────────────┐
│          Step 1: Thought             │
│   "需要获取股票基本信息"                        │
└────────────────┬─────────────────────────┘
                 │
               ▼
┌────────────────────────────────────────┐
│              Step 1: Action                 │
│   调用: get_stock_info("2600001")          │
└─────────────┬──────────────────────────┘
          │
            ▼
┌──────────────────────────────────┐
│            Step 1: Observation                     │
│   "股票名称：中国太保，价格：28.50元"                │
└────────────────┬──────────────────────────────────┘
                 │
          ▼
┌─────────────────────────────────────┐
│              Step 2: Thought                         │
│   "需要获取历史数据分析趋势"                     │
└────────────────┬───────────────────────┘
                 │
            ▼
┌────────────────────────────────┐
│            Step 2: Action                   │
│   调用: get_historical_data("2600001", 30)           │
└────────────────┬─────────────────────┘
              │
         ▼
                ...
                 │
                 ▼
┌──────────────────────────────────────────┐
│              Final Answer                  │
│   "明天上涨概率65%，理由：..."                       │
└──────────────────────────────┘
```

---

## 3. 架构设计

### 3.1 系统架构

```
┌────────────────────────────────────────┐
│                   用户层                           │
│              (User Interface)                     │
└──────────────┬────────────────────────┘
               │
                 ▼
┌───────────────────────────────────────────┐
│              Agent层                      │
│        (ReactAgent)                 │
│  ┌─────────────────────────────────────────┐  │
│  │  - 推理引擎 (Reasoning Engine)            │  │
│  │  - 行动解析器 (Action Parser)                │  │
│  │  - 循环控制器 (Loop Controller)              │  │
│  │  - 对话管理器 (Conversation Manager)         │  │
│  └─────────────────────────────┘  │
└──────────────┬─────────────────┘
             │
                 ▼
┌───────────────────────────────────────────┐
│                 工具层               │
│              (Tool Layer)                            │
│  ┌───────────────────────────────────┐  │
│  │  - 工具注册表 (Tool Registry)          │  │
│  │  - 工具执行器 (Tool Executor)                │  │
│  │  - 参数验证器 (Parameter Validator)          │  │
│  └──────────────────────────────┘  │
└─────────────┬──────────────────────┘
                 │
              ▼
┌─────────────────────────────┐
│                数据层                       │
│              (Data Layer)          │
│  ┌───────────────────────────────────┐  │
│  │  - 股票API (Stock API)                       │  │
│  │  - 新闻API (News API)                        │  │
│  │  - 技术指标计算 (Technical Indicators)       │  │
│  └──────────────────────────┘  │
└────────────────────────────────────┘
```

### 3.2 核心模块

#### 3.2.1 ReactAgent（核心引擎）
**职责**：
- 管理React循环
- 调用LLM进行推理
- 解析Action并执行工具
- 维护对话历史
**关键方法**：
```python
class ReactAgent:
    def __init__(self, api_key, max_iterations)
    def run(self, query, verbose) -> str
    def _build_system_prompt(self) -> str
    def _parse_action(self, response) -> Dict
    def _execute_tool(self, action, action_input) -> str
    def _is_final_answer(self, response) -> bool
```

#### 3.2.2 StockTools（工具集）

**职责**：
- 提供股票分析工具
- 封装外部API调用
- 数据格式化和验证

**工具列表**：
```python
class StockTools:
    @staticmethod
    def get_stock_info(stock_code) -> Dict
    
    @staticmethod
    def get_historical_data(stock_code, days) -> Dict
    
    @staticmethod
    def get_technical_indicators(stock_code) -> Dict
    
    @staticmethod
    def get_latest_news(stock_code) -> List[Dict]
    
    @staticmethod
    def get_market_sentiment(stock_code) -> Dict
```

#### 3.2.3 Tool Registry（工具注册表）

**职责**：
- 工具元数据管理
- 工具描述和参数定义
- 工具发现和调用

**数据结构**：
```python
TOOLS = {
    "tool_name": {
        "function": callable,
    "description": str,
     "parameters": Dict[str, str]
    }
}
```

---

## 4. 技术实现

### 4.1 技术栈

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| **LLM** | Claude 3.5 Sonnet | 推理能力强，支持长上下文 |
| **语言** | Python 3.10+ | 生态丰富，AI库完善 |
| **API客户端** | anthropic SDK | 官方SDK，稳定可靠 |
| **数据处理** | json, typing | 标准库，无额外依赖 |

### 4.2 核心算法

#### 4.2.1 React循环算法

```python
def react_loop(query, max_iterations):
    conversation_history = [{"role": "user", "content": query}]
    
    for iteration in range(max_iterations):
        # 1. 调用LLM推理
        response = llm.generate(
         system=system_prompt,
            messages=conversation_history
    )
        
        # 2. 检查是否是最终答案
     if is_final_answer(response):
            return extract_final_answer(response)
      
        # 3. 解析Action
        action_info = parse_action(response)
        if not action_info:
         continue
        
     # 4. 执行工具
        observation = execute_tool(
            action_info["action"],
            action_info["action_input"]
        )
        
        # 5. 更新对话历史
        conversation_history.append({
            "role": "assistant",
            "content": response
        })
        conversation_history.append({
            "role": "user",
            "content": f"Observation: {observation}"
        })
    
    return "达到最大迭代次数"
```

#### 4.2.2 Action解析算法

```python
def parse_action(response: str) -> Optional[Dict]:
  """
    解析格式：
    Action: tool_name
    Action Input: {"param": "value"}
    """
    lines = response.strip().split('\n')
    
    action_name = None
    action_input = None
    
    for line in lines:
        if line.startswith('Action:'):
         action_name = line.replace('Action:', '').strip()
        elif line.startswith('Action Input:'):
        json_str = line.replace('Action Input:', '').strip()
            action_input = json.loads(json_str)
    
    if action_name and action_input:
        return {
            "action": action_name,
          "action_input": action_input
        }
    
    return None
```

### 4.3 Prompt工程

#### 4.3.1 System Prompt结构

```
你是一个专业的股票分析Agent，使用React模式工作。

【可用工具】
- tool1: description
- tool2: description
...

【工作流程】
1. Thought: 思考下一步
2. Action: 选择工具
3. Observation: 观察结果
4. 重复1-3
5. Final Answer: 最终结论

【输出格式】
Thought: [思考过程]
Action: [工具名称]
Action Input: {"参数": "值"}

或：
Thought: 可以给出最终答案了
Final Answer: [分析结论]

【重要规则】
- 每次只调用一个工具
- 必须先思考再行动
- 综合多维度分析
- 给出明确概率和理由
```

#### 4.3.2 Few-shot示例

```python
few_shot_examples = """
示例1：
User: 分析000001股票
Thought: 首先需要获取股票基本信息
Action: get_stock_info
Action Input: {"stock_code": "000001"}

Observation: {"name": "平安银行", "price": 12.50}

Thought: 现在需要查看技术指标
Action: get_technical_indicators
Action Input: {"stock_code": "000001"}

Observation: {"MACD": "金叉", "RSI": 65}

Thought: 可以给出结论了
Final Answer: 明天上涨概率60%，理由：MACD金叉...
"""
```

---

## 5. 工具系统

### 5.1 工具设计原则

1. **单一职责**：每个工具只做一件事
2. **幂等性**：多次调用结果一致
3. **错误处理**：优雅处理异常
4. **类型安全**：使用类型注解
5. **文档完善**：清晰的描述和参数说明

### 5.2 工具实现

#### 5.2.1 get_stock_info（基本信息）

**功能**：获取股票基本信息

**输入**：
```python
{
    "stock_code": str  # 股票代码，如"2600001"
}
```

**输出**：
```python
{
    "code": str,           # 股票代码
    "name": str,           # 股票名称
    "current_price": float,# 当前价格
    "industry": str,       # 所属行业
    "market_cap": str      # 市值
}
```

**实现**：
```python
@staticmethod
def get_stock_info(stock_code: str) -> Dict[str, Any]:
    """获取股票基本信息"""
    try:
        # 实际应调用真实API
        # response = requests.get(f"https://api.stock.com/info/{stock_code}")
        # return response.json()
        
        # 模拟数据
        return {
            "code": stock_code,
            "name": "中国太保",
         "current_price": 28.50,
            "industry": "保险",
         "market_cap": "2580亿"
        }
    except Exception as e:
        return {"error": str(e)}
```

#### 5.2.2 get_historical_data（历史数据）

**功能**：获取历史价格数据和趋势

**输入**：
```python
{
    "stock_code": str,  # 股票代码
    "days": int         # 天数，默认30
}
```

**输出**：
```python
{
    "period": str,      # 时间周期
    "high": float,      # 最高价
    "low": float,       # 最低价
    "avg": float,       # 平均价
    "trend": str,       # 趋势描述
    "volatility": str   # 波动性
}
```

#### 5.2.3 get_technical_indicators（技术指标）

**功能**：计算技术指标

**输入**：
```python
{
    "stock_code": str  # 股票代码
}
```

**输出**：
```python
{
    "MACD": {
        "signal": str,  # 金叉/死叉
        "value": float
    },
    "KDJ": {
        "K": float,
        "D": float,
        "J": float,
      "status": str   # 超买/超卖/正常
    },
    "RSI": {
        "value": float,
        "status": str   # 偏高/偏低/正常
    },
    "volume": {
        "status": str,  # 放量/缩量
        "ratio": float
    }
}
```

#### 5.2.4 get_latest_news（最新新闻）

**功能**：获取股票相关新闻

**输入**：
```python
{
    "stock_code": str  # 股票代码
}
```

**输出**：
```python
[
    {
        "title": str,      # 新闻标题
        "sentiment": str,  # positive/negative/neutral
        "date": str        # 日期
    },
    ...
]
```

#### 5.2.5 get_market_sentiment（市场情绪）

**功能**：获取市场情绪和机构评级

**输入**：
```python
{
    "stock_code": str  # 股票代码
}
```

**输出**：
```python
{
    "bull_ratio": float,        # 看涨比例 0-1
    "bear_ratio": float,        # 看跌比例 0-1
    "hot_rank": int,            # 热度排名
    "institution_rating": str   # 机构评级
}
```

### 5.3 工具注册机制

```python
# 工具注册表
TOOLS = {
    "get_stock_info": {
        "function": StockTools.get_stock_info,
        "description": "获取股票基本信息，包括名称、价格、行业等",
      "parameters": {
            "stock_code": "股票代码（字符串）"
        }
    },
    # ... 其他工具
}

# 动态注册新工具
def register_tool(name: str, function: callable, 
               description: str, parameters: Dict):
    TOOLS[name] = {
        "function": function,
      "description": description,
        "parameters": parameters
    }
```

---

## 6. React循环机制

### 6.1 循环流程

```
┌─────────────────────┐
│         初始化对话历史                   │
│  conversation_history = [user_query]   │
└───────────┬─────────────────┘
         │
              ▼
┌───────────────────────────────┐
│      iteration < max_iterations?         │
└──────┬────────────────────────┘
         │ Yes
         ▼
┌──────────────────────────────────┐
│         调用LLM生成响应                  │
│  response = llm.generate(messages)       │
└────────────────┬─────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│      是否包含Final Answer?               │
└────┬──────────────────────────────┬───┘
     │ Yes                  │ No
     ▼                             ▼
┌─────────────────┐      ┌──────────────────────────┐
│  提取最终答案    │      │     解析Action            │
│  return answer   │      │  action_info = parse()    │
└─────────────┘      └────────────┬─────────────┘
                        │
                         ▼
                    ┌──────────────────────┐
                         │     执行工具              │
                         │  obs = execute_tool()   │
             └──────┬─────────────┘
                     │
                  ▼
                    ┌───────────────────┐
                  │   更新对话历史            │
                 │  history.append(response) │
                 │  history.append(obs)      │
                         └───────┬─────────────┘
                         │
                             ▼
                    ┌────────────────┐
                   │   继续下一轮循环          │
                      └──────────────────────┘
```

### 6.2 对话历史管理

```python
# 对话历史结构
conversation_history = [
    {
        "role": "user",
        "content": "分析2600001股票明天涨跌"
    },
    {
      "role": "assistant",
        "content": "Thought: 需要获取基本信息\nAction: get_stock_info\n..."
    },
    {
        "role": "user",
        "content": "Observation: {\"name\": \"中国太保\", ...}"
    },
    # ... 更多轮次
]
```

### 6.3 终止条件

1. **正常终止**：LLM输出Final Answer
2. **超时终止**：达到max_iterations
3. **错误终止**：工具执行失败且无法恢复

---

## 7. 代码实现

### 7.1 完整代码

详见附录A：完整代码实现

### 7.2 关键代码片段

#### 7.2.1 System Prompt构建

```python
def _build_system_prompt(self) -> str:
    """构建系统提示词"""
    tools_desc = "\n".join([
        f"- {name}: {info['description']}\n  参数: {info['parameters']}"
        for name, info in self.tools.items()
    ])
    
    return f"""你是一个专业的股票分析Agent，使用React（Reasoning + Acting）模式工作。

可用工具：
{tools_desc}

工作流程：
1. Thought: 思考下一步需要做什么
2. Action: 选择一个工具并指定参数
3. Observation: 观察工具返回的结果
4. 重复1-3，直到有足够信息做出判断
5. Final Answer: 给出最终分析结论

输出格式：
Thought: [你的思考过程]
Action: [工具名称]
Action Input: {{"参数名": "参数值"}}

或者当你准备给出最终答案时：
Thought: 我现在可以给出最终答案了
Final Answer: [你的分析结论]

重要规则：
- 每次只能调用一个工具
- 必须先思考再行动
- 基于观察结果继续推理
- 综合多个维度分析（技术面、基本面、消息面）
- 给出明确的涨跌概率和理由
"""
```

#### 7.2.2 Action解析

```python
def _parse_action(self, response: str) -> Optional[Dict[str, Any]]:
    """解析LLM返回的Action"""
    lines = response.strip().split('\n')
    
    action_name = None
    action_input = None
    
    for i, line in enumerate(lines):
        if line.startswith('Action:'):
      action_name = line.replace('Action:', '').strip()
    elif line.startswith('Action Input:'):
            json_str = line.replace('Action Input:', '').strip()
            try:
            action_input = json.loads(json_str)
            except json.JSONDecodeError:
              action_input = {"stock_code": json_str.strip('"')}
    
    if action_name and action_input:
        return {
            "action": action_name,
            "action_input": action_input
      }
    
    return None
```

#### 7.2.3 工具执行

```python
def _execute_tool(self, action: str, action_input: Dict[str, Any]) -> str:
    """执行工具调用"""
    if action not in self.tools:
        return f"错误：工具 {action} 不存在"
    
    try:
        tool_func = self.tools[action]["function"]
        result = tool_func(**action_input)
        return json.dumps(result, ensure_ascii=False, indent=2)
  except Exception as e:
        return f"错误：工具执行失败 - {str(e)}"
```

---

## 8. 使用示例

### 8.1 基本使用

```python
from react_agent import ReactAgent

# 初始化Agent
agent = ReactAgent(
    api_key="your-claude-api-key",
    max_iterations=10
)

# 运行分析
result = agent.run(
    query="分析2600001股票明天的涨跌情况",
    verbose=True  # 打印详细过程
)

print(f"分析结果:\n{result}")
```

### 8.2 运行输出示例

```
===============================================
Iteration 1
=====================================