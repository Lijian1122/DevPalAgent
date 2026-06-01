# React Agent 股票分析完整实现指南

> **版本**: v1.0  
> **日期**: 2026-05-25  
> **适用场景**: Python实现React Agent进行股票涨跌分析

---

## 目录

1. [核心概念](#1-核心概念)
2. [完整代码实现](#2-完整代码实现)
3. [运行示例](#3-运行示例)
4. [性能优化](#4-性能优化)
5. [扩展方向](#5-扩展方向)
6. [常见问题](#6-常见问题)

---

## 1. 核心概念

### 1.1 什么是React Agent？

**React = Reasoning（推理） + Acting（行动）**

```
传统AI：输入 → 推理 → 输出

React Agent：
输入 → 推理 → 行动 → 观察 → 推理 → 行动 → ... → 输出
     ↑______________________↓
              循环迭代
```

### 1.2 工作流程

```
Step 1: Thought（思考）
"我需要分析股票2600001，首先获取基本信息"

Step 2: Action（行动）
调用工具：get_stock_info("2600001")

Step 3: Observation（观察）
"股票名称：中国太保，价格：28.50元"

Step 4: Thought（思考）
"现在需要获取历史数据分析趋势"

Step 5: Action（行动）
调用工具：get_historical_data("2600001", 30)

... 循环迭代 ...

Final Answer: "明天上涨概率65%，理由：..."
```

---

## 2. 完整代码实现

### 2.1 工具定义

```python
# stock_tools.py

from typing import List, Dict, Any

class StockTools:
    """股票分析工具集"""
    
    @staticmethod
    def get_stock_info(stock_code: str) -> Dict[str, Any]:
        """获取股票基本信息"""
        return {
            "code": stock_code,
        "name": "中国太保",
            "current_price": 28.50,
       "industry": "保险",
     "market_cap": "2580亿"
    }
    
    @staticmethod
    def get_historical_data(stock_code: str, days: int = 30) -> Dict[str, Any]:
        """获取历史价格数据"""
        return {
            "period": f"最近{days}天",
            "high": 29.80,
            "low": 27.20,
        "avg": 28.30,
            "trend": "震荡上行",
            "volatility": "中等"
        }
  
    @staticmethod
    def get_technical_indicators(stock_code: str) -> Dict[str, Any]:
        """获取技术指标"""
        return {
          "MACD": {"signal": "金叉", "value": 0.15},
            "KDJ": {"K": 82, "D": 75, "J": 89, "status": "超买"},
          "RSI": {"value": 68, "status": "偏高"},
            "volume": {"status": "放量", "ratio": 1.5}
        }
    
    @staticmethod
    def get_latest_news(stock_code: str) -> List[Dict[str, str]]:
        """获取最新新闻"""
        return [
         {
                "title": "中国太保Q3业绩超预期",
                "sentiment": "positive",
                "date": "2024-05-24"
            },
          {
                "title": "保险行业政策利好",
        "sentiment": "positive",
                "date": "2024-05-23"
            }
        ]
    
    @staticmethod
    def get_market_sentiment(stock_code: str) -> Dict[str, Any]:
        """获取市场情绪"""
        return {
            "bull_ratio": 0.65,
          "bear_ratio": 0.35,
         "hot_rank": 15,
            "institution_rating": "买入"
        }
# 工具注册表
TOOLS = {
    "get_stock_info": {
        "function": StockTools.get_stock_info,
        "description": "获取股票基本信息，包括名称、价格、行业等",
        "parameters": {"stock_code": "股票代码（字符串）"}
    },
    "get_historical_data": {
        "function": StockTools.get_historical_data,
        "description": "获取股票历史价格数据和趋势",
        "parameters": {
          "stock_code": "股票代码（字符串）",
            "days": "天数（整数，默认30）"
        }
    },
    "get_technical_indicators": {
        "function": StockTools.get_technical_indicators,
        "description": "获取技术指标（MACD、KDJ、RSI等）",
        "parameters": {"stock_code": "股票代码（字符串）"}
    },
    "get_latest_news": {
        "function": StockTools.get_latest_news,
        "description": "获取股票最新新闻和公告",
        "parameters": {"stock_code": "股票代码（字符串）"}
    },
    "get_market_sentiment": {
        "function": StockTools.get_market_sentiment,
        "description": "获取市场情绪和机构评级",
        "parameters": {"stock_code": "股票代码（字符串）"}
    }
}
```

### 2.2 React Agent核心实现

```python
# react_agent.py

import json
from typing import List, Dict, Any, Optional
import anthropic

class ReactAgent:
    """React Agent实现"""
    
    def __init__(self, api_key: str, max_iterations: int = 10):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.max_iterations = max_iterations
        self.tools = TOOLS
        self.conversation_history = []
        
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

    def _parse_action(self, response: str) -> Optional[Dict[str, Any]]:
      """解析LLM返回的Action"""
        lines = response.strip().split('\n')
        
        action_name = None
        action_input = None
        
        for line in lines:
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
    
    def _is_final_answer(self, response: str) -> bool:
        ""判断是否是最终答案""
        return "Final Answer:" in response
    
    def _extract_final_answer(self, response: str) -> str:
      """提取最终答案"""
        if "Final Answer:" in response:
            return response.split("Final Answer:")[1].strip()
        return response
    
    def run(self, query: str, verbose: bool = True) -> str:
    """运行React Agent"""
        
        self.conversation_history = [
            {"role": "user", "content": query}
        ]
        
        iteration = 0
        
        while iteration < self.max_iterations:
       iteration += 1
            
            if verbose:
          print(f"\n{'='*60}")
          print(f"Iteration {iteration}")
                print(f"{'='*60}")
          
            # 调用LLM
            response = self.client.messages.create(
              model="claude-3-5-sonnet-20241022",
             max_tokens=2000,
                system=self._build_system_prompt(),
                messages=self.conversation_history
            )
            
            assistant_message = response.content[0].text
            
            if verbose:
                print(f"\nAssistant:\n{assistant_message}")
            
            # 检查是否是最终答案
            if self._is_final_answer(assistant_message):
                final_answer = self._extract_final_answer(assistant_message)
                if verbose:
                  print(f"\n{'='*60}")
                    print("最终答案")
                    print(f"{'='*60}")
              print(final_answer)
         return final_answer
            
         # 解析Action
            action_info = self._parse_action(assistant_message)
            
            if not action_info:
             self.conversation_history.append({
               "role": "assistant",
              "content": assistant_message
         })
                self.conversation_history.append({
               "role": "user",
                    "content": "请按照格式输出Action和Action Input"
                })
                continue
         
          # 执行工具
            action = action_info["action"]
          action_input = action_info["action_input"]
      
            if verbose:
              print(f"\n执行工具: {action}")
                print(f"参数: {action_input}")
            
      observation = self._execute_tool(action, action_input)
        
            if verbose:
             print(f"\n观察结果:\n{observation}")
          
          # 更新对话历史
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
          })
            self.conversation_history.append({
                "role": "user",
                "content": f"Observation: {observation}"
            })
        
        return "达到最大迭代次数，未能得出结论"
```

### 2.3 主程序

```python
# main.py

from react_agent import ReactAgent
from stock_tools import TOOLS

if __name__ == "__main__":
    # 初始化Agent
    agent = ReactAgent(
        api_key="your-claude-api-key",
        max_iterations=10
    )
    
    # 运行分析
    result = agent.run(
        query="分析2600001股票明天的涨跌情况",
      verbose=True
    )
    
    print(f"\n\n最终结果:\n{result}")
```

---

## 3. 运行示例

### 3.1 完整运行输出

```bash
$ python main.py

=====================================
Iteration 1
======================================