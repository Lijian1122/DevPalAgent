# 美团 Agent Memory 二面 8 道核心题详解

**基于 DevPalAgent 实际架构的回答**  
**日期**：2026-05-19  
**参考实现**：`devpal/memory/` 模块

---

## 问题 1：用例子解释 Memory 怎么做及插入上下文？

### 核心回答

Memory 的核心是**三层架构 + 动态上下文注入**：

1. **Short-term Memory（对话级）**：存储当前会话的 user/assistant/tool_result 消息序列。
2. **Long-term Memory（持久化）**：存储用户偏好、历史经验、代码知识、行为模式。
3. **Error Memory（错误记忆）**：记录历史错误和修正方法，避免重复犯错。

### 实际例子（DevPalAgent）

```python
# 场景：用户第一次问"帮我写个登录功能"
memory_manager = MemoryManager()

# 1. Short-term 记录对话
memory_manager.short_term.add_user("帮我写个登录功能")
memory_manager.short_term.add_assistant("好的，我会生成登录代码...")

# 2. 执行成功后，Long-term 记录经验
memory_manager.record_success(
  task="生成登录功能",
    result="成功生成 login.cpp，包含密码哈希和 session 管理"
)

# 3. 如果用户第二次问"再写个注册功能"
query = "再写个注册功能"

# 检索相关记忆
long_term_context = memory_manager.long_term.get_relevant_context(query)
# 返回：
# [Past Experience]
# - Success: 生成登录功能, result: 成功生成 login.cpp，包含密码哈希...

# 4. 插入上下文到 System Prompt
enhanced_prompt = f"""
你是一个代码生成助手。

{long_term_context}

用户当前请求：{query}
""
```

### 插入上下文的时机

| 时机 | 插入内容 | 目的 |
|---|---|---|
| **每次 LLM 调用前** | Long-term 相关记忆 | 让 LLM 知道用户偏好和历史经验 |
| **检测到相似错误场景** | Error Memory 警告 | 避免重复犯错 |
| **工具调用后** | Tool result 追加到 Short-term | 保持工具调用上下文完整 |

### 关键代码（DevPalAgent 实现）

```python
# devpal/memory/memory_manager.py
def get_system_prompt_enhancement(self, current_query: str) -> str:
    enhancements = []
    
    # 注入长期记忆
    if self.long_term is not None:
        context = self.long_term.get_relevant_context(current_query)
    if context:
            enhancements.append(context)
    
  # 注入错误警告
    if self.error is not None:
        warning = self.error.generate_warning_prompt(current_query)
        if warning:
            enhancements.append(warning)
    
    return "\n".join(enhancements)
```

---

## 问题 2：Memory 如何考虑上下文长度？

### 核心回答

上下文长度管理采用**分层截断 + 智能保留**策略：

1. **Short-term 滑动窗口**：超过 token 阈值时，保留最近 N 轮对话。
2. **Long-term 按需检索**：不全量加载，只检索 top-k 相关记忆。
3. **Error Memory 优先级过滤**：只注入高相似度 + 高严重性的错误。

### DevPalAgent 的实现策略

```python
# devpal/memory/short_term.py
class ShortTermMemory:
  def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens
        self.messages = []
    
    def _truncate_if_needed(self):
        estimated_tokens = self.count_tokens_estimate()
        
        # 触发截断阈值：70% 容量
        if estimated_tokens < self.max_tokens * 0.7:
            return
        
        # 保留最近 6 条消息（约 3 轮对话）
        min_messages = 6
        if len(self.messages) > min_messages:
            self.messages = self.messages[-min_messages:]
```

### 上下文长度预算分配

假设总 context window = 200K tokens：

| 组件 | 预算 | 说明 |
|---|---:|---|
| System Prompt | 2K | 固定角色定义 |
| Long-term Memory | 1K | Top-3 相关记忆 |
| Error Memory | 0.5K | Top-3 错误警告 |
| Short-term Messages | 8K | 最近 3-5 轮对话 |
| Tool Results | 动态 | 工具输出，按需截断 |
| 输出预留 | 4K | LLM 生成空间 |
| **总计** | **~15.5K** | 实际使用远小于 window |

### 关键设计原则

1. **懒加载**：Long-term 和 Error Memory 不预加载，只在需要时检索。
2. **时间衰减**：Long-term 检索时，越新的记忆权重越高。
3. **重要性加权**：高 importance 的记忆优先保留。
4. **工具调用完整性**：尽量保留完整的 tool_use → tool_result 对。

---

## 问题 3：结构化与文本信息怎么区分，会重复吗？

### 核心回答

**结构化信息**和**文本信息**在 Memory 中有明确分层：

| 类型 | 存储位置 | 格式 | 用途 |
|---|---|---|---|
| **结构化** | Short-term messages | JSON (role/content/tool_use) | LLM API 调用 |
| **文本** | Long-term / Error Memory | 自然语言描述 | System Prompt 注入 |

### 不会重复的设计

#### 1. Short-term 存储原始结构

```python
# 结构化：工具调用
{
    "role": "assistant",
    "content": [
        {"type": "text", "text": "我会读取文件"},
        {"type": "tool_use", "id": "call_123", "name": "read_file", "input": {"path": "main.cpp"}}
    ]
}

# 结构化：工具结果
{
    "role": "user",
    "content": [
        {"type": "tool_result", "tool_use_id": "call_123", "content": "int main() {...}"}
    ]
}
```

#### 2. Long-term 存储文本摘要

```python
# 文本：经验总结
memory_manager.long_term.add_experience(
    "Success: 读取 main.cpp 并生成测试，用户偏好 Google Test 框架"
)
```

#### 3. 去重机制

```python
# devpal/memory/long_term.py
def _is_duplicate(self, content: str, threshold: float = 0.8) -> bool:
    """避免重复添加相似内容"""
    content_words = set(content.lower().split())
    
    for mem in self.memories:
    mem_words = set(mem.content.lower().split())
        similarity = len(content_words & mem_words) / len(content_words | mem_words)
        if similarity > threshold:
            return True  # 相似度 > 80% 视为重复
    return False
```

### 实际例子

```python
# 场景：用户连续两次问"帮我写测试"

# 第一次
memory.long_term.add_experience("生成了 Google Test 测试代码")

# 第二次（相似度 > 80%，不会重复添加）
memory.long_term.add_experience("生成了 Google Test 测试")  # 被去重拦截
```

---

## 问题 4：记忆冲突怎么解决（如不同过敏信息）？

### 核心回答

记忆冲突采用**时间戳 + 重要性 + 显式覆盖**策略：
### 冲突场景分类

| 场景 | 策略 | 实现 |
|---|---|---|
| **用户偏好变更** | 新记忆覆盖旧记忆 | 时间戳排序，取最新 |
| **矛盾信息（如过敏）** | 高 importance 优先 | 检索时按 importance 加权 |
| **错误修正** | 增加 occurrence 计数 | 重复错误权重更高 |

### DevPalAgent 的冲突解决

#### 1. 时间戳优先（最新覆盖）

```python
# devpal/memory/long_term.py
def retrieve(self, query: str, top_k: int = 5):
  for item in self.memories:
      # 时间衰减：越新分数越高
        age_days = (time.time() - item.timestamp) / 86400
        recency = 1.0 / (1 + age_days)
        
        # 综合评分
        score = overlap * 0.5 + recency * 0.3 + importance_weight * 0.2
```

#### 2. 重要性加权

```python
# 场景：用户过敏信息冲突
memory.add_user_preference("我对花生过敏", importance=10)  # 高优先级
memory.add_user_preference("我喜欢吃坚果", importance=3)   # 低优先级

# 检索时，importance=10 的记忆权重更高
```

#### 3. 显式更新机制（推荐扩展）

```python
# 当前 DevPalAgent 未实现，但可扩展：
def update_preference(self, old_content: str, new_content: str):
    """显式更新偏好，标记旧记忆为过期"""
    for mem in self.memories:
        if mem.content == old_content:
         mem.metadata['deprecated'] = True
            mem.metadata['replaced_by'] = new_content
    
    self.add_user_preference(new_content, importance=10)
```

### 实际例子

```python
# Day 1: 用户说"我喜欢用 C++"
memory.add_user_preference("用户偏好 C++", importance=5)

# Day 30: 用户说"我现在主要用 Python"
memory.add_user_preference("用户偏好 Python", importance=5)

# 检索时，Day 30 的记忆因为 recency 更高，会优先返回
```

---

## 问题 5：记忆怎么写入上下文？结构是怎样的？

### 核心回答

记忆写入上下文采用**分段注入 + 标记分隔**：

### 上下文结构（4 段式）

```python
# 1. System Prompt（固定角色定义）
system_prompt = """
你是一个智能代码助手，擅长 C++/Python 开发。
"""

# 2. Memory Enhancement（动态注入）
memory_context = memory_manager.get_system_prompt_enhancement(query)
# 返回：
# [User Preferences]
# - 用户偏好 Google Test 框架
# [Past Experience]
# - Success: 生成登录功能，包含密码哈希
# [Warning] Avoid repeating these similar errors:
# 1. [Tool Call Error] 忘记检查文件是否存在
#    Correct: 先用 file_exists 检查

# 3. Short-term Messages（对话历史）
messages = memory_manager.short_term.get_messages()
# [
#   {"role": "user", "content": "帮我写个登录功能"},
#   {"role": "assistant", "content": "好的，我会..."},
#   ...
# ]

# 4. Current Query（当前请求）
current_query = "再写个注册功能"
```

### 完整上下文组装

```python
# DevPalAgent 实际调用 LLM 的结构
def call_llm(query: str):
    # 1. 基础 System Prompt
    base_system = "你是一个代码助手..."
    
    # 2. 动态注入 Memory
    memory_enhancement = memory_manager.get_system_prompt_enhancement(query)
    
    # 3. 组合 System Prompt
    full_system_prompt = f"{base_system}\n\n{memory_enhancement}"
    
    # 4. 构建消息列表
    messages = [
        {"role": "system", "content": full_system_prompt},
        *memory_manager.short_term.get_messages(),
        {"role": "user", "content": query}
    ]
    
    # 5. 调用 LLM
    response = llm_client.call(messages)
    
    # 6. 记录到 Short-term
    memory_manager.short_term.add_assistant(response)
```

### 关键设计

1. **System Prompt 动态拼接**：Memory 不占用 messages 数组，而是注入到 system prompt。
2. **分段标记**：用 `[User Preferences]`、`[Warning]` 等标记区分不同类型记忆。
3. **懒加载**：只在需要时检索 Long-term 和 Error Memory。

---

## 问题 6：上下文结构是 System Prompt 等四个环节吗？

### 核心回答

是的，标准 Agent 上下文结构是**四段式**：

### 标准四段式结构

```python
[
    # 1. System Prompt（角色定义 + Memory 注入）
    {
        "role": "system",
        "content": """
        你是一个代码助手。
        
        [User Preferences]
    - 用户偏好 Google Test
        
        [Warning] Avoid repeating:
        - 忘记检查文件存在
        ""
    },
    
  # 2. Historical Messages（对话历史）
    {"role": "user", "content": "帮我写登录"},
    {"role": "assistant", "content": "好的..."},
    
    # 3. Tool Interactions（工具调用历史）
    {
        "role": "assistant",
        "content": [
            {"type": "tool_use", "name": "read_file", ...}
        ]
    },
    {
        "role": "user",
        "content": [
            {"type": "tool_result", "content": "..."}
        ]
    },
    
    # 4. Current Query（当前请求）
    {"role": "user", "content": "再写个注册"}
]
```

### DevPalAgent 的实际实现

```python
# devpal/core/agent_engine.py (简化版)
def run(self, user_query: str):
    # 1. 构建 System Prompt
    base_system = self._get_base_system_prompt()
    memory_context = self.memory.get_system_prompt_enhancement(user_query)
    full_system = f"{base_system}\n\n{memory_context}"
    
    # 2. 获取历史消息
    history = self.memory.short_term.get_messages()
    
    # 3. 组装完整上下文
    messages = [
        {"role": "system", "content": full_system},
    *history,
        {"role": "user", "content": user_query}
    ]
    
    # 4. 调用 LLM
    response = self.llm_client.call(messages)
    
    # 5. 处理工具调用（如果有）
    if response.has_tool_calls():
      tool_results = self._execute_tools(response.tool_calls)
        self.memory.short_term.add_tool_results(tool_results)
        # 递归调用，继续对话
        return self.run(user_query)
    
    return response
```

### 为什么是四段式？

| 段落 | 作用 | 可否省略 |
|---|---|---|
| System Prompt | 定义角色、注入记忆 | 否 |
| Historical Messages | 保持对话连贯性 | 可（首次对话） |
| Tool Interactions | 保持工具调用上下文 | 可（无工具调用） |
| Current Query | 当前用户请求 | 否 |

---

## 问题 7：上下文超长怎么办？考虑压缩吗？

### 核心回答

上下文超长采用**分层截断 + 选择性压缩**，而不是全量压缩：

### DevPalAgent 的策略

#### 1. Short-term 滑动窗口（主策略）

```python
# devpal/memory/short_term.py
def _truncate_if_needed(self):
    estimated_tokens = self.count_tokens_estimate()
    
    # 触发阈值：70% 容量
    if estimated_tokens < self.max_tokens * 0.7:
        return
    
    # 保留最近 6 条消息
    min_messages = 6
    if len(self.messages) > min_messages:
        self.messages = self.messages[-min_messages:]
```

#### 2. Long-term 按需检索（避免全量加载）

```python
# 不压缩，而是只检索 top-k
long_term_context = memory.long_term.retrieve(query, top_k=3)
```

#### 3. Tool Result 截断（可选）

```python
# 如果工具输出过长，截断并保留摘要
def add_tool_result_truncated(self, tool_use_id: str, content: str, max_len: int = 2000):
    if len(content) > max_len:
        truncated = content[:max_len] + f"\n... (truncated, total {len(content)} chars)"
        self.add_tool_result(tool_use_id, truncated)
    else:
        self.add_tool_result(tool_use_id, content)
```

### 压缩策略对比

| 策略 | 优点 | 缺点 | DevPalAgent 采用 |
|---|---|---|:---:|
| **滑动窗口** | 简单、可控 | 丢失早期上下文 | ✅ |
| **LLM 摘要压缩** | 保留语义 | 成本高、延迟大 | ❌ |
| **向量检索** | 精准召回 | 需要向量库 | ❌ |
| **按需检索** | 零成本 | 需要良好索引 | ✅ |

### 为什么不用 LLM 压缩？

```python
# LLM 压缩的问题：
# 1. 成本高：每次压缩都要调用 LLM
# 2. 延迟大：增加 1-2 秒延迟
# 3. 信息损失：摘要可能丢失关键细节
# 4. 工具调用丢失：压缩后无法保留 tool_use 结构

# DevPalAgent 的选择：
# - Short-term 用滑动窗口（简单高效）
# - Long-term 用按需检索（零成本）
# - 只在必要时（如生成 final report）才用 LLM 摘要
```

---

## 问题 8：压缩丢失工具调用历史导致重复调用怎么解决？

### 核心回答

这是 Memory 系统的**核心难题**，DevPalAgent 采用**工具调用去重 + 结果缓存**策略：

### 问题场景

```python
# 场景：压缩后丢失工具调用历史
# 原始对话：
user: "读取 main.cpp"
assistant: [tool_use: read_file(main.cpp)]
user: [tool_result: "int main() {...}"]
assistant: "文件内容是..."

# 压缩后：
assistant: "我读取了 main.cpp，内容是..."  # 丢失了 tool_use 结构

# 问题：用户再问"main.cpp 里有什么？"
# LLM 不知道已经读过，会重复调用 read_file
```

### DevPalAgent 的解决方案

#### 1. 保留完整 Tool 对（主策略）

```python
# devpal/memory/short_term.py
def _truncate_if_need(self):
    # 截断时，尽量保留完整的 tool_use → tool_result 对
    min_messages = 6  # 保留最近 3 轮对话（每轮 2 条消息）
    
    # 如果最后一条是 tool_use，保留到下一条 tool_result
    if self.messages and self.messages[-1].get("role") == "assistant":
        content = self.messages[-1].get("content", [])
      if isinstance(content, list) and any(item.get("type") == "tool_use" for item in content):
            min_messages += 1  # 多保留一条，等待 tool_result
```

#### 2. Tool Result 缓存（推荐扩展）

```python
# 当前 DevPalAgent 未实现，但可扩展：
class ToolResultCache:
    def __init__(self):
        self.cache = {}  # {(tool_name, args_hash): result}
    
    def get(self, tool_name: str, args: dict) -> Optional[str]:
        key = (tool_name, self._hash_args(args))
        return self.cache.get(key)
    
    def set(self, tool_name: str, args: dict, result: str):
        key = (tool_name, self._hash_args(args))
        self.cache[key] = result
    
    def _hash_args(self, args: dict) -> str:
        import json, hashlib
        return hashlib.md5(json.dumps(args, sort_keys=True).encode()).hexdigest()

# 使用：
tool_cache = ToolResultCache()

def execute_tool(tool_name: str, args: dict):
    # 先查缓存
    cached = tool_cache.get(tool_name, args)
    if cached:
        return cached
    
    # 执行工具
    result = actual_tool_execution(tool_name, args)
    
    # 写入缓存
    tool_cache.set(tool_name, args, result)
    return result
```

#### 3. Long-term 记录工具调用（辅助策略）

```python
# 工具调用成功后，记录到 Long-term
memory.long_term.add_experience(
    f"已读取 main.cpp，内容包含 main 函数和 login 逻辑",
    importance=4
)

# 下次用户问"main.cpp 里有什么？"
# Long-term 检索会返回：
# [Past Experience]
# - 已读取 main.cpp，内容包含 main 函数和 login 逻辑

# LLM 看到这个上下文，可能直接回答，而不重复调用工具
```

#### 4. System Prompt 注入去重提示

```python
system_prompt = """
你是一个代码助手。

重要规则：
- 如果 [Past Experience] 中已有文件内容，优先使用记忆，避免重复读取。
- 只有当记忆不足或文件可能已更新时，才调用 read_file。

[Past Experience]
- 已读取 main.cpp，内容包含 main 函数和 login 逻辑
"""
```

### 完整流程示例

```python
# 第一次：读取文件
user: "读取 main.cpp"
assistant: [tool_use: read_file(main.cpp)]
user: [tool_result: "int main() {...}"]
assistant: "文件内容是..."

# 记录到 Long-term
memory.long_term.add_experience("已读取 main.cpp，内容包含 main 函数")

# 压缩 Short-term（保留最近 6 条）
memory.short_term._truncate_if_needed()

# 第二次：用户再问
user: "main.cpp 里有什么？"

# Long-term 检索返回：
# [Past Experience]
# - 已读取 main.cpp，内容包含 main 函数

# LLM 看到记忆，直接回答，不重复调用工具
assistant: "根据之前的读取，main.cpp 包含 main 函数和 login 逻辑..."
```

---

## 总结：DevPalAgent Memory 系统的核心设计

| 维度 | 策略 | 优势 |
|---|---|---|
| **架构** | 三层（Short/Long/Error） | 分层管理，职责清晰 |
| **上下文长度** | 滑动窗口 + 按需检索 | 简单高效，零成本 |
| **去重** | 相似度检测（80% 阈值） | 避免冗余记忆 |
| **冲突** | 时间戳 + 重要性加权 | 最新优先，高优先级优先 |
| **注入** | System Prompt 动态拼接 | 不占用 messages 数组 |
| **压缩** | 不压缩，用截断 + 检索 | 避免信息损失 |
| **工具去重** | 完整对保留 + 缓存 + Long-term | 多层防护 |

### 关键代码文件

- `devpal/memory/memory_manager.py`：统一入口
- `devpal/memory/short_term.py`：对话上下文管理
- `devpal/memory/long_term.py`：持久化记忆
- `devpal/memory/error_memory.py`：错误记忆

### 面试加分项

1. **实际代码支撑**：能展示 DevPalAgent 的真实实现。
2. **工程权衡**：解释为什么不用 LLM 压缩（成本/延迟/信息损失）。
3. **多层防护**：工具去重不依赖单一策略，而是多层保障。
4. **可扩展性**：当前设计支持轻松扩展（如 Tool Cache、显式更新）。
