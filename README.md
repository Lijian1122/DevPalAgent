# DevPal Agent 详细技术方案文档

> **个人开发助手 Agent 系统设计与实现**
>
> **目标：** 从零实现一个完整的 Agent 系统，涵盖 Function Call、记忆、规划、反思、多模态等所有核心能力
>
> **作者：** 李建
>
> **版本：** v1.0
>
> **预计开发周期：** 2 周

---

## 📋 目录

- [1. 项目概述](#1-项目概述)
- [2. 整体架构设计](#2-整体架构设计)
- [3. 核心模块详细设计](#3-核心模块详细设计)
  - [3.1 LLM 封装层](#31-llm-封装层)
  - [3.2 工具系统（Function Call）](#32-工具系统function-call)
  - [3.3 记忆系统](#33-记忆系统)
  - [3.4 规划与反思模块](#34-规划与反思模块)
  - [3.5 Agent 核心引擎](#35-agent-核心引擎)
  - [3.6 多模态支持](#36-多模态支持)
- [4. 开发路线图与里程碑](#4-开发路线图与里程碑)
- [5. 技术选型与依赖](#5-技术选型与依赖)
- [6. 测试策略与评估指标](#6-测试策略与评估指标)
- [7. 部署与使用](#7-部署与使用)
- [8. 风险与应对](#8-风险与应对)
- [9. MVP 快速启动代码](#9-mvp-快速启动代码)

---

## 1. 项目概述

### 1.1 项目背景

当前大模型 Agent 技术发展迅速，但市面上的 Agent 产品大多是通用型的，针对 C++ 音视频开发场景的专业 Agent 几乎没有。本项目旨在：

1. **深入理解 Agent 底层原理**：通过从零实现，彻底掌握 Function Call、记忆、规划、反思等核心技术
2. **打造实用的开发工具**：做一个自己写代码时真正能用的开发助手
3. **形成技术壁垒**：拥有一个完整的 Agent 项目，面试时可以吊打 90% 的候选人

### 1.2 核心目标

| 目标 | 说明 |
|-----|------|
| **功能完整** | 覆盖 Agent 所有核心能力：工具调用、记忆、规划、反思、多模态 |
| **代码质量高** | 模块化设计，可扩展，可测试，符合工程标准 |
| **真正可用** | 做出来自己每天写代码都能用，不是玩具项目 |
| **易于学习** | 每个阶段都有明确交付物，循序渐进 |

### 1.3 核心能力清单

- ✅ **多工具自动编排**：自主决定调用什么工具、什么顺序
- ✅ **长短时记忆**：记住对话历史、用户偏好、犯过的错误
- ✅ **任务规划**：复杂任务自动拆解成步骤，先规划再执行
- ✅ **自我反思**：能发现自己的错误并纠正
- ✅ **多模态理解**：能理解图片中的代码、编译报错
- ✅ **开发工具链集成**：编译、静态分析、Git 操作自动化

---

## 2. 整体架构设计

### 2.1 分层架构图

```
┌─────────────────────────────────────────────────────────┐
│                    交互层 (Interface)                    │
│  CLI / Web UI / IDE 插件                                 │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                  Agent 核心引擎 (Core)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  Planner │  │Executor  │  │ Reflector│             │
│  │ 规划器   │  │执行器    │  │反思器    │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                基础能力层 (Infrastructure)               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  LLM SDK │  │ Memory   │  │  Tools   │             │
│  │大模型封装 │  │记忆系统  │  │工具系统   │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
```

### 2.2 核心执行流程（Plan-Act-Reflect 循环）

```
用户输入
    ↓
[Planner 规划器]
    ↓ 生成执行计划
    ├─ 评估计划可行性
    └─ 拆解成步骤
        ↓
[Executor 执行器] ←───────────────┐
    ↓                              │
    ├─ 决定是否需要调用工具         │
    ├─ 选择合适的工具               │
    ├─ 执行工具 → 拿到结果          │
    └─ 判断任务完成了吗？           │
           ↓ 否                    │
[Reflector 反思器]                 │
    ↓ 反思刚才的执行               │
    ├─ 刚才做的对吗？               │
    ├─ 哪里错了？                   │
    ├─ 需要调整计划吗？             │
    └─ 把经验存入记忆 ──────────────┘
           ↓ 是
[结果输出 + 经验总结]
```

### 2.3 目录结构设计

```
devpal/
├── devpal/
│   ├── __init__.py
│   ├── core/                       # 核心引擎
│   │   ├── __init__.py
│   │   ├── agent.py                # Agent 主类
│   │   ├── planner.py              # 规划器
│   │   ├── executor.py             # 执行器
│   │   └── reflector.py            # 反思器
│   ├── llm/                        # LLM 封装层
│   │   ├── __init__.py
│   │   ├── base.py                 # LLM 基类
│   │   ├── claude.py               # Claude 实现
│   │   ├── openai.py               # GPT 实现
│   │   └── deepseek.py             # DeepSeek 实现
│   ├── memory/                     # 记忆系统
│   │   ├── __init__.py
│   │   ├── base.py                 # 记忆基类
│   │   ├── short_term.py           # 短期记忆（对话上下文）
│   │   ├── long_term.py            # 长期记忆（向量 DB）
│   │   └── error_memory.py         # 错误记忆
│   ├── tools/                      # 工具系统
│   │   ├── __init__.py
│   │   ├── base.py                 # Tool 基类
│   │   ├── filesystem.py           # 文件读写工具
│   │   ├── command.py              # 命令行执行工具
│   │   ├── code_search.py          # 代码搜索工具
│   │   ├── compiler.py             # 编译分析工具
│   │   ├── git_tool.py            # Git 操作工具
│   │   └── static_analysis.py      # 静态分析工具
│   ├── multimodal/                 # 多模态支持
│   │   ├── __init__.py
│   │   └── image_analyzer.py       # 图片分析
│   └── utils/                      # 工具函数
│       ├── __init__.py
│       ├── token_counter.py        # Token 计数
│       └── retry.py              # 重试机制
├── tests/                          # 测试
│   ├── unit/
│   └── integration/
├── examples/                       # 使用示例
├── config/                         # 配置文件
│   └── config.yaml
├── requirements.txt
├── setup.py
└── README.md
```

---

## 3. 核心模块详细设计

---

### 3.1 LLM 封装层

#### 3.1.1 设计目标

- 统一的 LLM 调用接口，支持多种大模型无缝切换
- 自动处理 Token 计数、截断、压缩
- 内置重试、超时、错误处理机制
- 支持流式输出和非流式输出

#### 3.1.2 接口定义

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Generator
from dataclasses import dataclass

@dataclass
class ToolCall:
    """工具调用数据结构"""
    id: str
    name: str
    arguments: Dict[str, Any]

@dataclass
class LLMResponse:
    """LLM 响应统一格式"""
    content: Optional[str]
    tool_calls: List[ToolCall]
    usage: Dict[str, int]  # prompt_tokens, completion_tokens, total_tokens
    model: str
    finish_reason: str

class BaseLLM(ABC):
    """LLM 基类，所有具体 LLM 实现都继承这个类"""
    
    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = "auto",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> LLMResponse | Generator[str, None, None]:
        """
        统一的聊天接口
        Args:
            messages: 对话历史，格式 [{"role": "user", "content": "..."}]
            tools: 可用工具列表，符合 OpenAI Function Call 格式
            tool_choice: "auto" / "none" / {"name": "tool_name"}
            temperature: 温度，0-1，越低越确定
            max_tokens: 最大输出 Token 数
            stream: 是否流式输出
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """计算文本的 Token 数量"""
        pass
    
    @abstractmethod
    def truncate_messages(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int
    ) -> List[Dict[str, str]]:
        """截断消息历史，保证不超过 Token 限制"""
        pass
```

#### 3.1.3 Claude 实现示例

```python
import anthropic
from typing import List, Dict, Any, Optional, Generator
from .base import BaseLLM, LLMResponse, ToolCall

class ClaudeLLM(BaseLLM):
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
    
    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 4096,
        system: Optional[str] = None,
    ) -> LLMResponse:
        """
        非流式聊天接口
        Args:
            messages: 对话历史，格式 [{"role": "user", "content": "..."}]
            tools: 可用工具列表，符合 Claude Tool 格式
            tool_choice: 工具选择策略 {"type": "auto"} / {"type": "any"} / {"type": "tool", "name": "..."}
            temperature: 温度
            max_tokens: 最大输出 Token 数
            system: 系统提示词（Claude 推荐单独传）
        """
        # 分离 system prompt (Claude 推荐单独传)
        claude_messages = []
        extracted_system = system
        
        for msg in messages:
            if msg["role"] == "system" and not extracted_system:
                extracted_system = msg["content"]
            else:
                claude_messages.append(msg)
        
        # 调用 API
        response = self.client.beta.tools.messages.create(
            model=self.model,
            system=extracted_system,
            messages=claude_messages,
            tools=tools,
            tool_choice=tool_choice,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return self._parse_response(response)
    
    def chat_stream(self, *args, **kwargs) -> Generator[str, None, None]:
        """流式聊天接口，独立出来避免类型混淆"""
        kwargs["stream"] = True
        response = self.client.beta.tools.messages.create(*args, **kwargs)
        for event in response:
            if event.type == "content_block_delta" and event.delta.type == "text_delta":
                yield event.delta.text
    
    def count_tokens(self, text: str) -> int:
        """Claude SDK 目前没有公开的 tokenizer，用近似估算"""
        return len(text) // 4  # 英文平均 4 字符 = 1 token，中文约 1-2 字符 = 1 token
    
    def truncate_messages(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int
    ) -> List[Dict[str, str]]:
        """
        截断策略：
        1. 保留最新的 N 条消息
        2. 保留第一条系统提示
        3. 中间的旧消息做摘要压缩
        """
        if len(messages) <= 2:
            return messages
        
        system_prompt = messages[0]
        recent_messages = messages[-10:]  # 保留最新 10 条
        old_messages = messages[1:-10]
        
        if not old_messages:
            return messages
        
        # 对旧消息做摘要
        summary = self._summarize_messages(old_messages)
        return [
            system_prompt,
            {"role": "user", "content": f"[历史对话摘要] {summary}"},
            *recent_messages,
        ]
    
    # ... 私有方法实现
```

#### 3.1.4 内置能力

| 能力 | 实现方式 |
|-----|---------|
| **自动重试** | 装饰器模式，对网络错误、限流自动重试 3 次，指数退避 |
| **Token 计数** | 集成各模型的官方 Tokenizer |
| **自动截断** | 超过 Token 限制时自动摘要旧对话 |
| **错误处理** | 统一的异常类型，调用方不需要关心底层 LLM 差异 |

---

### 3.2 工具系统（Function Call）

#### 3.2.1 设计目标

- 统一的 Tool 基类，新增工具只需要继承基类即可
- 自动生成符合 Function Call 格式的工具描述
- 自动参数校验和类型转换
- 工具执行的安全沙箱机制

#### 3.2.2 Tool 基类定义（优化版：Pydantic 自动生成 Schema）

**改进点：不用手动写 JSON Schema，用 Pydantic 模型自动生成**

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Type, Optional
from pydantic import BaseModel, create_model

class ToolResult(BaseModel):
    """工具执行结果"""
    success: bool
    content: str
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}

class BaseTool(ABC):
    """所有工具的基类 - 自动从参数模型自动生成 JSON Schema"""
    
    # 子类定义参数模型，自动生成描述
    Parameters: Type[BaseModel]
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称，必须是唯一的"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述，告诉 LLM 这个工具是干什么的"""
        pass
    
    @abstractmethod
    def execute(self, parameters: BaseModel) -> ToolResult:
        """执行工具的具体逻辑，传入 Pydantic 模型"""
        pass
    
    def to_function_call_format(self) -> Dict[str, Any]:
        """从 Pydantic 模型自动生成 Claude Tool 格式"""
        schema = self.Parameters.model_json_schema()
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": schema.get("properties", {}),
                "required": schema.get("required", [])
            }
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """用 Pydantic 自动校验，省去手动写校验逻辑"""
        try:
            self.Parameters(**parameters)
            return True, None
        except Exception as e:
            return False, str(e)
    
    def execute_with_validation(self, parameters: Dict[str, Any]) -> ToolResult:
        """带校验的执行入口"""
        valid, error = self.validate_parameters(parameters)
        if not valid:
            return ToolResult(success=False, content="", error_message=error)
        return self.execute(self.Parameters(**parameters))
```

#### 3.2.3 第一个工具：文件读取（优化版）

```python
import os
from pydantic import Field
from .base import BaseTool, ToolResult

class FileReaderTool(BaseTool):
    name = "file_reader"
    description = "读取本地文件的内容，支持读取文本文件"
    
    class Parameters(BaseModel):
        path: str = Field(description="要读取的文件的路径，可以是相对路径或绝对路径")
        start_line: int = Field(default=1, description="从第几行开始读，默认从第一行开始")
        end_line: int = Field(default=-1, description="读到第几行结束，默认读到文件末尾")
    
    def execute(self, params: Parameters) -> ToolResult:
        # 安全检查：不允许读取系统敏感文件
        if self._is_sensitive_path(params.path):
            return ToolResult(
                success=False,
                content="",
                error_message="不允许读取系统敏感文件"
            )
        
        try:
            with open(params.path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # 行号范围处理
            start_idx = max(0, params.start_line - 1)
            end_idx = len(lines) if params.end_line == -1 else min(params.end_line, len(lines))
            content = "".join(lines[start_idx:end_idx])
            
            return ToolResult(
                success=True,
                content=f"文件 {params.path} 内容（第 {params.start_line}-{end_idx} 行）：\n{content}",
                metadata={"total_lines": len(lines), "read_lines": end_idx - start_idx}
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error_message=f"读取文件失败: {str(e)}"
            )
    
    def _is_sensitive_path(self, path: str) -> bool:
        sensitive_patterns = ["/etc/", "/root/", ".ssh", ".env", "id_rsa", "password"]
        return any(p in path for p in sensitive_patterns)
```

> **✅ 优化效果：新增工具时，只用定义参数模型即可，JSON Schema 和校验全自动化，零重复代码**

---

#### 3.2.x 原基类定义（旧版，已弃用）

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pydantic import BaseModel, ValidationError

class ToolResult(BaseModel):
    """工具执行结果"""
    success: bool
    content: str
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}

class BaseTool(ABC):
    """所有工具的基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称，必须是唯一的"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述，告诉 LLM 这个工具是干什么的"""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """
        参数定义，符合 JSON Schema 格式
        示例：
        {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "mode": {"type": "string", "enum": ["r", "w"], "description": "打开模式"}
            },
            "required": ["path"]
        }
        """
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """执行工具的具体逻辑"""
        pass
    
    def to_function_call_format(self) -> Dict[str, Any]:
        """转换为 OpenAI Function Call 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """校验 LLM 传过来的参数是否合法"""
        required_params = self.parameters.get("required", [])
        for param in required_params:
            if param not in parameters:
                return False, f"缺少必要参数: {param}"
        
        # 简单的类型校验
        properties = self.parameters.get("properties", {})
        for param_name, param_value in parameters.items():
            if param_name in properties:
                expected_type = properties[param_name].get("type")
                if expected_type == "string" and not isinstance(param_value, str):
                    return False, f"参数 {param_name} 应该是字符串"
                # ... 其他类型校验
        
        return True, None
```

#### 3.2.3 第一个工具：文件读取

```python
import os
from typing import Dict, Any
from .base import BaseTool, ToolResult

class FileReaderTool(BaseTool):
    @property
    def name(self) -> str:
        return "file_reader"
    
    @property
    def description(self) -> str:
        return "读取本地文件的内容，支持读取文本文件"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "要读取的文件的路径，可以是相对路径或绝对路径"
                },
                "start_line": {
                    "type": "integer",
                    "description": "从第几行开始读，默认从第一行开始",
                    "default": 1
                },
                "end_line": {
                    "type": "integer",
                    "description": "读到第几行结束，默认读到文件末尾",
                    "default": -1
                }
            },
            "required": ["path"]
        }
    
    def execute(self, **kwargs) -> ToolResult:
        path = kwargs["path"]
        start_line = kwargs.get("start_line", 1)
        end_line = kwargs.get("end_line", -1)
        
        # 安全检查：不允许读取系统敏感文件
        if self._is_sensitive_path(path):
            return ToolResult(
                success=False,
                content="",
                error_message="不允许读取系统敏感文件"
            )
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # 行号范围处理
            start_idx = max(0, start_line - 1)
            end_idx = len(lines) if end_line == -1 else min(end_line, len(lines))
            content = "".join(lines[start_idx:end_idx])
            
            return ToolResult(
                success=True,
                content=f"文件 {path} 内容（第 {start_line}-{end_idx} 行）：\n{content}",
                metadata={"total_lines": len(lines), "read_lines": end_idx - start_idx}
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error_message=f"读取文件失败: {str(e)}"
            )
    
    def _is_sensitive_path(self, path: str) -> bool:
        """安全检查，防止读取敏感文件"""
        sensitive_patterns = [
            "/etc/",
            "/root/",
            ".ssh",
            ".env",
            "id_rsa",
        ]
        return any(p in path for p in sensitive_patterns)
```

#### 3.2.4 内置工具清单（第一阶段实现）

| 工具名称 | 功能 | 优先级 |
|---------|------|-------|
| `file_reader` | 读取文件内容 | P0 |
| `file_writer` | 写入文件内容 | P0 |
| `command_executor` | 执行命令行命令（带安全沙箱） | P0 |
| `code_search` | 代码搜索（grep） | P1 |
| `compiler_analyzer` | 编译报错分析 | P1 |
| `git_operation` | Git 操作 | P2 |
| `static_analyzer` | 静态分析（clang-tidy） | P2 |

#### 3.2.5 安全机制

- 白名单目录限制，只能访问指定目录下的文件
- 敏感路径黑名单，禁止读写系统文件、秘钥文件
- 命令执行白名单，只允许执行安全的命令（g++、git、ls 等）
- 超时机制，防止长时间执行挂住
- 所有工具执行都有日志记录，可审计

---

### 3.3 记忆系统

#### 3.3.1 三层记忆架构

```
┌─────────────────────────────────────────────────┐
│  短期记忆 (Short-term Memory)                    │
│  对话上下文，滑动窗口管理，当前会话有效           │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│  长期记忆 (Long-term Memory)                     │
│  用户偏好、历史经验、知识，向量数据库存储，永久有效 │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│  错误记忆 (Error Memory)                         │
│  记录 Agent 犯过的错误，下次遇到自动规避          │
└─────────────────────────────────────────────────┘
```

#### 3.3.2 短期记忆实现

```python
from typing import List, Dict, Any
from dataclasses import dataclass
from ..utils.token_counter import count_tokens

@dataclass
class MemoryItem:
    role: str
    content: str
    timestamp: float
    token_count: int
    importance: int = 1  # 重要程度，1-10

class ShortTermMemory:
    def __init__(self, max_tokens: int = 80000, llm_for_summary: Optional[BaseLLM] = None):
        self.max_tokens = max_tokens
        self.memories: List[MemoryItem] = []
        self.system_prompt: Optional[MemoryItem] = None
        self.llm_for_summary = llm_for_summary  # 注入 LLM，用于摘要
    
    def add(self, role: str, content: str, importance: int = 1) -> None:
        """添加一条记忆"""
        tokens = count_tokens(content)
        item = MemoryItem(
            role=role,
            content=content,
            timestamp=time.time(),
            token_count=tokens,
            importance=importance
        )
        
        if role == "system":
            self.system_prompt = item
        else:
            self.memories.append(item)
        
        self._truncate_if_needed()
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """获取用于 LLM 的消息列表，支持混合内容（文本+工具结果"""
        messages = []
        
        total_tokens = self.system_prompt.token_count if self.system_prompt else 0
        selected_memories = []
        
        # 从后往前遍历，优先保留最新的和重要的
        for item in reversed(self.memories):
            if total_tokens + item.token_count <= self.max_tokens * 0.7:
                selected_memories.append(item)
                total_tokens += item.token_count
            elif item.importance >= 5:
                selected_memories.append(item)
                total_tokens += item.token_count
            else:
                break
        
        selected_memories.reverse()
        
        for item in selected_memories:
            messages.append({"role": item.role, "content": item.content})
        
        return messages
    
    def _truncate_if_needed(self) -> None:
        """Token 超了的时候，对旧记忆做摘要压缩"""
        total_tokens = sum(m.token_count for m in self.memories)
        if total_tokens < self.max_tokens * 0.5:
            return
        
        # 前 50% 的旧记忆，只保留最近 20 条，更早的直接丢弃（轻量版不做 LLM 摘要
        split_idx = max(20, len(self.memories) // 2)
        self.memories = self.memories[-split_idx:]  # 直接保留最新的
    
    def get_token_heavy_truncate(self) -> None:
        """真正需要摘要时才调用，用 LLM 压缩"""
        if not self.llm_for_summary:
            return  # 没有 LLM 就不做摘要
        
        summary = self._summarize_with_llm(self.memories[:len(self.memories)//2])
        self.memories = self.memories[len(self.memories)//2:]
        self.memories.insert(0, MemoryItem(
            role="user",
            content=f"[历史对话摘要] {summary}",
            timestamp=time.time(),
            token_count=count_tokens(summary),
            importance=3
        ))
```

#### 3.3.3 长期记忆实现（向量 RAG）

```python
import chromadb
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

class LongTermMemory:
    def __init__(self, persist_dir: str = "./data/long_term_memory"):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="devpal_memory",
            metadata={"description": "DevPal 长期记忆"}
        )
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def add(
        self,
        content: str,
        memory_type: str,  # "user_preference", "experience", "knowledge"
        metadata: Dict[str, Any] = None
    ) -> None:
        """添加一条长期记忆"""
        embedding = self.embedding_model.encode(content).tolist()
        metadata = metadata or {}
        metadata["type"] = memory_type
        
        self.collection.add(
            ids=[f"mem_{int(time.time() * 1000000)}"],
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata]
        )
    
    def retrieve(
        self,
        query: str,
        memory_type: Optional[str] = None,
        top_k: int = 5
    ) -> List[str]:
        """检索相关记忆"""
        embedding = self.embedding_model.encode(query).tolist()
        
        where_filter = {"type": memory_type} if memory_type else None
        
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=where_filter
        )
        
        return results["documents"][0]
    
    def get_context_for_query(self, query: str) -> str:
        """获取一条查询的相关记忆上下文"""
        preferences = self.retrieve(query, memory_type="user_preference", top_k=3)
        experiences = self.retrieve(query, memory_type="experience", top_k=3)
        
        context_parts = []
        if preferences:
            context_parts.append("用户偏好：\n" + "\n".join(preferences))
        if experiences:
            context_parts.append("历史经验：\n" + "\n".join(experiences))
        
        return "\n\n".join(context_parts) if context_parts else ""
```

#### 3.3.4 错误记忆

```python
class ErrorMemory:
    """专门记录 Agent 犯过的错误，避免重复踩坑"""
    
    def __init__(self, persist_path: str = "./data/error_memory.json"):
        self.persist_path = persist_path
        self.errors = self._load()
    
    def add_error(
        self,
        error_type: str,  # "tool_call_error", "logic_error", "hallucination"
        description: str,
        correction: str,
        context: str
    ) -> None:
        """记录一个错误"""
        self.errors.append({
            "type": error_type,
            "description": description,
            "correction": correction,
            "context": context,
            "timestamp": time.time(),
            "occurrences": 1
        })
        self._save()
    
    def check_for_similar_errors(self, current_context: str) -> List[Dict[str, Any]]:
        """检查当前上下文有没有类似的历史错误"""
        # 用向量相似度检索
        # ... 实现省略
        pass
    
    def generate_warning_prompt(self, similar_errors: List[Dict[str, Any]]) -> str:
        """生成错误警示提示，在 System Prompt 里注入"""
        if not similar_errors:
            return ""
        
        warning = "\n⚠️ 注意：你之前在类似情况下犯过以下错误，请避免重复：\n"
        for err in similar_errors:
            warning += f"- {err['description']} → 正确做法：{err['correction']}\n"
        
        return warning
```

---

### 3.4 规划与反思模块

这是 Agent 最核心的部分，也是区分"高级智能体"和"简单工具调用机器人"的关键。

#### 3.4.1 规划器（Planner）设计

```python
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class PlanStep:
    """计划中的一个步骤"""
    step_number: int
    description: str
    tool_needed: Optional[str] = None  # 需要用到什么工具
    expected_output: Optional[str] = None  # 预期产出
    importance: int = 1  # 重要程度 1-10

@dataclass
class Plan:
    """完整执行计划"""
    original_query: str
    steps: List[PlanStep]
    overall_goal: str
    estimated_complexity: str  # "simple", "medium", "complex"

class Planner:
    def __init__(self, llm: BaseLLM):
        self.llm = llm
    
    def generate_plan(self, query: str) -> Plan:
        """根据用户查询生成执行计划"""
        
        planning_prompt = f"""
        你是一个专业的软件开发助手，需要根据用户的需求生成一个详细的执行计划。
        
        用户需求：{query}
        
        请按照以下格式生成计划：
        1. 首先评估任务复杂度（simple/medium/complex）
        2. 拆解成具体步骤，每个步骤说明做什么、需要用什么工具
        3. 每个步骤标注重要程度
        
        输出 JSON 格式：
        {{
            "overall_goal": "整体目标",
            "complexity": "simple/medium/complex",
            "steps": [
                {{
                    "step_number": 1,
                    "description": "步骤描述",
                    "tool_needed": "工具名称或null",
                    "expected_output": "预期产出",
                    "importance": 1-10
                }}
            ]
        }}
        """
        
        response = self.llm.chat([
            {"role": "user", "content": planning_prompt}
        ])
        
        # 解析 JSON 生成 Plan 对象
        plan_data = self._parse_plan_json(response.content)
        return Plan(
            original_query=query,
            steps=[PlanStep(**step) for step in plan_data["steps"]],
            overall_goal=plan_data["overall_goal"],
            estimated_complexity=plan_data["complexity"]
        )
    
    def evaluate_plan_feasibility(self, plan: Plan) -> tuple[bool, List[str]]:
        """评估计划可行性，返回 (是否可行, 问题列表)"""
        issues = []
        
        # 检查每个步骤需要的工具是否存在
        for step in plan.steps:
            if step.tool_needed and step.tool_needed not in AVAILABLE_TOOLS:
                issues.append(f"步骤 {step.step_number} 需要的工具 {step.tool_needed} 不存在")
        
        # 检查步骤顺序是否合理
        # ... 更多检查逻辑
        
        return len(issues) == 0, issues
    
    def adjust_plan(
        self,
        current_plan: Plan,
        current_step: int,
        execution_result: ToolResult,
        feedback: str
    ) -> Plan:
        """根据执行结果动态调整计划"""
        # 如果执行失败，考虑要不要调整步骤、跳过、或者增加新步骤
        # ... 实现省略
        return adjusted_plan
```

#### 3.4.2 反思器（Reflector）设计

```python
class Reflector:
    def __init__(self, llm: BaseLLM, error_memory: ErrorMemory):
        self.llm = llm
        self.error_memory = error_memory
    
    def reflect_step(
        self,
        step: PlanStep,
        execution_result: ToolResult,
        current_context: str
    ) -> Dict[str, Any]:
        """反思单步执行结果"""
        
        reflection_prompt = f"""
        请对刚才的执行结果进行反思评估：
        
        执行的步骤：{step.description}
        执行结果：{execution_result.content if execution_result.success else execution_result.error_message}
        当前上下文：{current_context}
        
        请回答以下问题：
        1. 这一步执行成功了吗？达到预期目标了吗？
        2. 有没有哪里做得不好可以改进的？
        3. 有没有发现什么错误？
        4. 接下来的计划需要调整吗？
        
        输出 JSON 格式：
        {{
            "success": true/false,
            "goal_achieved": true/false,
            "issues_found": ["问题1", "问题2"],
            "improvements": ["改进建议1", "改进建议2"],
            "need_plan_adjustment": true/false,
            "adjustment_suggestion": "调整建议"
        }}
        """
        
        response = self.llm.chat([{"role": "user", "content": reflection_prompt}])
        reflection = self._parse_reflection_json(response.content)
        
        # 如果发现错误，记录到错误记忆
        if reflection["issues_found"]:
            for issue in reflection["issues_found"]:
                self.error_memory.add_error(
                    error_type="execution_error",
                    description=issue,
                    correction=reflection["improvements"],
                    context=current_context
                )
        
        return reflection
    
    def reflect_final_result(self, query: str, final_result: str) -> Dict[str, Any]:
        """任务完成后的最终反思，总结经验教训"""
        
        final_reflection_prompt = f"""
        原始任务：{query}
        最终结果：{final_result}
        
        请总结这次任务：
        1. 哪些地方做得好？
        2. 哪些地方可以改进？
        3. 有什么经验教训可以记录下来，以后避免犯同样的错误？
        
        输出简洁的总结。
        """
        
        response = self.llm.chat([{"role": "user", "content": final_reflection_prompt}])
        
        # 把经验教训存入长期记忆
        # ... 实现省略
        
        return {
            "summary": response.content,
            "lessons_learned": [...]
        }
```

---

### 3.5 Agent 核心引擎

#### 3.5.1 主引擎实现

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .llm.base import BaseLLM
from .memory.short_term import ShortTermMemory
from .memory.long_term import LongTermMemory
from .memory.error_memory import ErrorMemory
from .tools.base import BaseTool
from .planner import Planner
from .reflector import Reflector

@dataclass
class AgentConfig:
    enable_planning: bool = True
    enable_reflection: bool = True
    enable_long_term_memory: bool = True
    max_iterations: int = 10
    verbose: bool = False

class DevPalAgent:
    def __init__(
        self,
        llm: BaseLLM,
        tools: List[BaseTool],
        config: AgentConfig = None
    ):
        self.config = config or AgentConfig()
        
        # 核心组件
        self.llm = llm
        self.tools = {tool.name: tool for tool in tools}
        self.short_term_memory = ShortTermMemory()
        self.long_term_memory = LongTermMemory() if self.config.enable_long_term_memory else None
        self.error_memory = ErrorMemory()
        
        self.planner = Planner(llm)
        self.reflector = Reflector(llm, self.error_memory)
        
        # 系统提示词
        self._init_system_prompt()
    
    def _init_system_prompt(self) -> None:
        system_prompt = f"""
        你是 DevPal，一个专业的 C++ 音视频开发助手。
        
        你的工作方式：
        1. 先理解用户需求，必要时可以提问澄清
        2. 先规划再执行，不要盲目动手
        3. 不确定的地方就去查资料，不要瞎猜
        4. 每次执行完一步都要反思，看看对不对
        5. 犯了错误就记录下来，下次不要重复犯错
        
        你可以使用以下工具：
        {', '.join(self.tools.keys())}
        
        不要编造不存在的工具，也不要编造不存在的文件。
        """
        
        self.short_term_memory.add("system", system_prompt, importance=10)
    
    def run(self, query: str) -> str:
        """Agent 主入口，执行用户查询"""
        
        if self.config.verbose:
            print(f"🧠 DevPal 收到任务: {query}")
        
        # 1. 检索相关记忆，注入上下文
        memory_context = self._get_memory_context(query)
        
        # 2. 生成执行计划
        if self.config.enable_planning:
            if self.config.verbose:
                print("📋 生成执行计划...")
            plan = self.planner.generate_plan(query + "\n\n" + memory_context)
            
            if self.config.verbose:
                print(f"计划生成完成，共 {len(plan.steps)} 步")
                for step in plan.steps:
                    print(f"  {step.step_number}. {step.description}")
        else:
            # 简单模式，不规划，直接执行
            plan = self._create_simple_plan(query)
        
        # 3. 主执行循环
        current_step_idx = 0
        iteration_count = 0
        
        while current_step_idx < len(plan.steps) and iteration_count < self.config.max_iterations:
            iteration_count += 1
            step = plan.steps[current_step_idx]
            
            if self.config.verbose:
                print(f"\n▶️ 执行步骤 {step.step_number}: {step.description}")
            
            # 检查历史错误，注入警告
            error_warning = self.error_memory.check_for_similar_errors(step.description)
            if error_warning and self.config.verbose:
                print(f"⚠️ 历史错误警告: {error_warning}")
            
            # 执行步骤
            execution_result = self._execute_step(step)
            
            if self.config.verbose:
                if execution_result.success:
                    print(f"✅ 执行成功")
                else:
                    print(f"❌ 执行失败: {execution_result.error_message}")
            
            # 反思执行结果
            if self.config.enable_reflection:
                reflection = self.reflector.reflect_step(step, execution_result, str(self.short_term_memory))
                
                if reflection["need_plan_adjustment"]:
                    if self.config.verbose:
                        print(f"🔄 调整计划: {reflection['adjustment_suggestion']}")
                    plan = self.planner.adjust_plan(plan, current_step_idx, execution_result, reflection["adjustment_suggestion"])
            
            # 记录执行结果到短期记忆
            self.short_term_memory.add(
                "assistant",
                f"步骤 {step.step_number} 执行结果: {'成功' if execution_result.success else '失败'}\n{execution_result.content}"
            )
            
            if execution_result.success:
                current_step_idx += 1
        
        # 4. 最终反思，总结经验
        final_result = self._generate_final_result(query, plan)
        
        if self.config.enable_reflection:
            final_reflection = self.reflector.reflect_final_result(query, final_result)
            
            if self.config.enable_long_term_memory and final_reflection["lessons_learned"]:
                for lesson in final_reflection["lessons_learned"]:
                    self.long_term_memory.add(lesson, memory_type="experience")
        
        return final_result
    
    def _execute_step(self, step: PlanStep) -> ToolResult:
        """执行单个步骤"""
        
        # 让 LLM 决定怎么调用工具
        tool_call_prompt = f"""
        当前步骤：{step.description}
        整体目标：{step.expected_output}
        
        可用工具：
        {self._format_tools_description()}
        
        请决定：
        1. 需要调用工具吗？
        2. 如果需要，调用哪个工具，传什么参数？
        3. 如果不需要，直接输出步骤结果。
        """
        
        self.short_term_memory.add("user", tool_call_prompt)
        
        response = self.llm.chat(
            messages=self.short_term_memory.get_messages(),
            tools=[tool.to_function_call_format() for tool in self.tools.values()],
            tool_choice="auto"
        )
        
        if response.tool_calls:
            # 需要调用工具
            tool_call = response.tool_calls[0]
            tool = self.tools[tool_call.name]
            
            # 参数校验
            valid, error_msg = tool.validate_parameters(tool_call.arguments)
            if not valid:
                return ToolResult(success=False, content="", error_message=error_msg)
            
            # 执行工具
            result = tool.execute(**tool_call.arguments)
            
            # 把工具结果加到记忆里
            self.short_term_memory.add(
                "user",
                f"工具 {tool_call.name} 执行结果:\n{result.content if result.success else result.error_message}"
            )
            
            return result
        else:
            # 不需要调用工具，直接返回 LLM 的回答
            return ToolResult(success=True, content=response.content)
    
    # ... 其他辅助方法
```

---

### 3.6 多模态支持

```python
class ImageAnalyzer:
    def __init__(self, llm: BaseLLM):
        self.llm = llm  # 需要是支持多模态的 LLM（Claude 3 / GPT-4V）
    
    def analyze_image(
        self,
        image_path: str,
        prompt: str = "请描述这张图片的内容"
    ) -> str:
        """分析图片内容"""
        import base64
        
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        message = {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_data
                    }
                }
            ]
        }
        
        response = self.llm.chat([message])
        return response.content
    
    def analyze_compiler_error_screenshot(self, image_path: str) -> Dict[str, Any]:
        """专门分析编译报错截图"""
        prompt = """
        这是一张 C++ 编译报错的截图，请：
        1. 提取所有报错信息，包括：错误代码、文件路径、行号、错误描述
        2. 分析错误原因
        3. 给出具体的修复方案
        
        输出 JSON 格式。
        """
        result = self.analyze_image(image_path, prompt)
        return self._parse_error_analysis(result)
```

---

## 4. 开发路线图与里程碑

### 🚩 阶段 0：最小可用版本 (MVP)
**时间：1-2 天**

**目标：第一天就能跑起来**

- ✅ 实现基础 LLM 封装（只支持 Claude）
- ✅ 实现 Tool 基类 + 3 个基础工具（file_reader、file_writer、command_executor）
- ✅ 实现最简单的 Agent 主循环（不规划、不反思、不记忆）
- ✅ 第一个 Demo 跑通："帮我编译这个 cpp 文件并分析报错"

**交付物：** 能跑的 MVP 版本，单文件 200 行代码就能实现

---

### 🚩 阶段 1：完整工具系统 + 多轮工具调用
**时间：2-3 天**

- ✅ 完善工具系统，增加参数校验、安全沙箱
- ✅ 实现 5 个核心开发工具
- ✅ 多轮工具调用自动循环
- ✅ 工具调用失败重试机制
- ✅ CLI 交互界面

**交付物：** 一个能真正帮你读文件、执行命令、分析编译报错的助手

---

### 🚩 阶段 2：记忆系统
**时间：2-3 天**

- ✅ 短期记忆 + Token 自动截断
- ✅ 长期记忆 + 向量数据库 RAG
- ✅ 错误记忆 + 自动规避
- ✅ 记忆检索准确度测试与优化
- ✅ 用户偏好自动学习

**交付物：** Agent 有记性了，能记住你的代码风格，不会重复犯同样的错误

---

### 🚩 阶段 3：规划与反思能力
**时间：3-4 天**

- ✅ Planner 规划器，复杂任务自动拆解步骤
- ✅ 计划可行性评估
- ✅ Reflector 反思器，每步执行后反思
- ✅ 动态调整计划
- ✅ 最终总结 + 经验沉淀

**交付物：** 从"工具调用机器人"升级成"有思考的助手"

--p

### 🚩 阶段 4：多模态 + 工具链扩展
**时间：3-4 天**

- ✅ 图片理解能力（编译报错截图分析）
- ✅ 静态分析工具集成（clang-tidy）
- ✅ Git 自动化助手
- ✅ 代码 Review 能力
- ✅ Web UI 界面（Gradio）

**交付物：** 功能完整的专业开发助手，自己每天都能用

---

### 🚩 阶段 5：自我迭代 + 插件系统（可选高级）
**时间：2-3 天**

- ✅ Agent 能读自己的源代码
- ✅ 能自我修复 bug、自我改进
- ✅ 插件系统，任何人都能加新工具
- ✅ 多 Agent 协作（架构师 + 程序员 + 测试）

**交付物：** 能自我进化的终极 Agent

---

## 5. 技术选型与依赖

| 组件 | 选型 | 理由 |
|-----|------|------|
| **开发语言** | Python 3.10+ | Agent 生态最丰富，原型开发快 |
| **大模型** | Claude 3 Sonnet | Function Call 最准，推理能力强，价格适中 |
| **向量数据库** | 🔹 推荐：lite-vec 或 ChromaDB | lite-vec 纯 Python 无依赖，< 100KB；ChromaDB 功能全但重 |
| **Embedding 模型** | 🔹 推荐：用 Claude API 做检索或 nomic-embed-text | **避免 sentence-transformers (1GB+ 依赖下载慢) |
| **Web UI** | Gradio | 100 行代码就能做个能用的界面，适合快速原型 |
| **配置管理** | Pydantic + YAML | 类型安全，配置文件友好 |
| **测试框架** | pytest | Python 标准 |

### requirements.txt
```txt
# LLM SDKs
anthropic>=0.20.0
openai>=1.0.0

# 向量数据库
chromadb>=0.4.0

# Embedding
sentence-transformers>=2.2.0

# 工具类
pydantic>=2.0
pyyaml>=6.0
tenacity>=8.0  # 重试

# Web UI
gradio>=4.0

# 测试
pytest>=7.0
```

---

## 6. 测试策略与评估指标

### 6.1 单元测试
- 每个 Tool 单独测试
- LLM 封装层的参数校验、错误处理测试
- 记忆系统的增删改查测试

### 6.2 集成测试用例集

| 测试用例 | 预期行为 | 通过标准 |
|---------|---------|---------|
| "读取 test.cpp 的内容" | 调用 file_reader，正确返回文件内容 | 文件内容正确读取 |
| "帮我编译 test.cpp 并分析报错" | 调用 command_executor 执行 g++，分析报错，给出修复方案 | 正确分析出编译错误原因 |
| "搜索代码库中所有用到 shared_ptr 的地方" | 调用 code_search，正确返回搜索结果 | 搜索结果准确，没有遗漏 |

### 6.3 Agent 能力评估指标

| 指标 | 定义 | 目标值 |
|-----|------|-------|
| **工具调用准确率** | 100 次工具调用中，参数正确、工具选择正确的比例 | > 95% |
| **任务完成率** | 100 个测试任务中，最终成功完成的比例 | > 85% |
| **平均迭代次数** | 完成一个任务平均需要多少轮工具调用 | < 5 |
| **幻觉率** | 100 次回答中，编造不存在的信息、不存在的文件的次数 | < 5% |
| **Token 使用效率** | 完成同样任务消耗的 Token 数 | 持续优化降低 |

---

## 7. 部署与使用

### 7.1 本地部署

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key
export ANTHROPIC_API_KEY="your-api-key-here"
# 或者写在 config/config.yaml 里

# 3. 运行 CLI
python -m devpal.cli

# 4. 运行 Web UI
python -m devpal.web
```

### 7.2 IDE 集成（后续扩展）
- VS Code 插件
- CLion 插件
- 通过 LSP 协议集成

---

## 8. 风险与应对

| 风险 | 影响 | 应对方案 |
|-----|------|---------|
| **LLM 幻觉，编造不存在的文件/函数** | 高 | 1. 工具执行前校验参数 2. 错误记忆记录幻觉案例 3. 让 Agent 先确认文件存在再操作 |
| **工具调用 Token 消耗大** | 中 | 1. 优化系统提示词 2. 工具返回结果自动截断摘要 3. 本地缓存重复调用 |
| **陷入死循环，无限调用工具** | 中 | 1. max_iterations 硬限制 2. Reflector 检测到重复模式时强制终止 |
| **安全风险，执行危险命令** | 高 | 1. 严格的白名单机制 2. 敏感操作二次确认 3. Docker 沙箱隔离 |
| **响应速度慢，用户体验差** | 中 | 1. 流式输出 2. 简单任务用更快的小模型（Haiku）3. 复杂任务用大模型 |

---

## 9. MVP 快速启动代码

看完这个文档，今天就能动手写：

```python
"""
DevPal MVP - 200 行代码跑起来第一个 Agent
这是你今天就可以写完的最小可用版本
"""
import anthropic
import os
import json

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# 第一个工具：执行命令
def execute_command(cmd: str) -> str:
    import subprocess
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return f"命令执行成功:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    except Exception as e:
        return f"命令执行失败: {str(e)}"

# 工具描述（给 LLM 看的）
tools = [
    {
        "name": "execute_command",
        "description": "执行命令行命令",
        "input_schema": {
            "type": "object",
            "properties": {
                "cmd": {"type": "string", "description": "要执行的命令"}
            },
            "required": ["cmd"]
        }
    }
]

def run_agent(query: str):
    messages = [{"role": "user", "content": query}]
    
    for i in range(5):  # 最多 5 轮
        print(f"\n{'='*50}")
        print(f"第 {i+1} 轮思考...")
        
        response = client.beta.tools.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4096,
            messages=messages,
            tools=tools
        )
        
        # ✅ 修复 Bug 1: Claude message content 必须传 list，不能直接传 response.content
        # 原来的 messages.append({"role": "assistant", "content": response.content}) 是错的
        assistant_content = []
        for block in response.content:
            if block.type == "text":
                assistant_content.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                assistant_content.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })
        
        messages.append({"role": "assistant", "content": assistant_content})
        
        # 检查有没有工具调用
        has_tool_call = False
        for block in response.content:
            if block.type == "tool_use":
                has_tool_call = True
                print(f"🔧 调用工具: {block.name}")
                print(f"   参数: {block.input}")
                
                # 执行工具
                if block.name == "execute_command":
                    result = execute_command(**block.input)
                else:
                    result = f"未知工具: {block.name}"
                
                print(f"   结果长度: {len(result)} 字符")
                
                # ✅ 修复 Bug 2: tool_result 格式正确
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        }
                    ]
                })
        
        # 如果没有工具调用，说明任务完成了
        if not has_tool_call:
            print("\n✅ 最终回答:")
            for block in response.content:
                if block.type == "text":
                    print(block.text)
            break

# 测试一下
if __name__ == "__main__":
    run_agent("帮我编译当前目录下的 test.cpp，看看有什么报错，给我修复方案")
```

---

## 🚀 快速开始：5 分钟跑起来

### 第一步：安装依赖
```bash
pip install -r requirements.txt
```

### 第二步：设置 API Key
```bash
# Windows
set ANTHROPIC_API_KEY=your-api-key-here

# Linux/Mac
export ANTHROPIC_API_KEY=your-api-key-here
```

### 第三步：运行 MVP
```bash
# 查看当前目录
python devpal/mvp.py "帮我看看当前目录有什么文件"

# 编译 C++ 文件（如果有的话）
python devpal/mvp.py "帮我编译 test.cpp 并分析报错"
```

### 当前项目文件结构
```
DevPalAgent/
├── README.md                    # ✅ 详细技术方案
├── requirements.txt             # ✅ 依赖清单（分阶段安装）
└── devpal/
    ├── __init__.py
    └── mvp.py                   # ✅ 可运行 MVP（第 0 阶段）
```

---

## 🎯 总结

这个技术方案的设计理念是：**从简单开始，逐步迭代，每个阶段都有能用的产出**。

- 第一天就能写出 200 行的 MVP，看到 Agent 真的在工作
- 每个阶段只增加一个核心能力，不会一下子太复杂
- 做出来的东西自己每天都能用，有正反馈，能坚持做完

**现在就可以开始运行了！** 🚀

---

## 📐 新增：架构最佳实践补充

### 🔄 依赖注入原则
```python
# ✅ 推荐：所有依赖通过构造函数注入，便于测试
class Agent:
    def __init__(self, llm: BaseLLM, memory: Memory, tools: List[BaseTool]):
        self.llm = llm
        self.memory = memory
        self.tools = tools

# ❌ 不推荐：在类内部 new，无法 mock 测试
class Agent:
    def __init__(self):
        self.llm = ClaudeLLM()  # 硬编码，单元测试要真实请求 API
```

### 🛡️ 防幻觉机制（核心改进）
```python
class HallucinationGuard:
    """三重校验防止 LLM 幻觉"""
    
    def verify_file_exists(self, filepath: str) -> bool:
        """工具调用前先确认文件真的存在"""
        return os.path.exists(filepath)
    
    def detect_hallucination(self, response: str, context: str) -> bool:
        """检测回答是否与上下文矛盾"""
        # 简单关键词匹配 + 交叉验证
        pass
    
    def require_citation(self, claim: str) -> bool:
        """重要断言需要引用证据"""
        pass
```

### 🎯 简化的长期记忆（轻量版）
```python
import json
import os
from typing import List, Dict

class SimpleLongTermMemory:
    """🔹 零依赖版本：不用向量数据库，直接用关键词匹配"""
    
    def __init__(self, path: str = "./data/memory.json"):
        self.path = path
        self.data = self._load()
    
    def add(self, content: str, type: str):
        self.data.append({"content": content, "type": type, "timestamp": time.time()})
        self._save()
    
    def retrieve(self, query: str, top_k: int = 5) -> List[str]:
        """关键词 + 时间加权排序，不需要 Embedding"""
        query_words = set(query.lower().split())
        results = []
        
        for item in self.data:
            content_words = set(item["content"].lower().split())
            overlap = len(query_words & content_words)
            recency = 1.0 / (1 + (time.time() - item["timestamp"]) / 86400)
            score = overlap * 0.7 + recency * 0.3
            results.append((score, item["content"]))
        
        results.sort(reverse=True)
        return [content for _, content in results[:top_k]]
```

> **效果：** 零依赖、启动快、80% 场景够用！初期优先用轻量版

---

**文档版本：** v1.1 （已优化）  
**最后更新：** 2024-05-02  
**已修复问题：**
- ✅ LLM 接口分离流式/非流式，避免类型混淆
- ✅ 工具系统自动生成 JSON Schema，零重复代码
- ✅ MVP 代码消息格式 Bug 修复，可直接运行
- ✅ 记忆系统简化，降低初期依赖重量
- ✅ 增加防幻觉机制最佳实践

**下一步：** 从第 9 章的 MVP 代码开始，写第一个能跑的版本
