# DevPal Agent Tool Calling 完整时序图

```mermaid
sequenceDiagram
    participant User as 👤 用户
    participant MVP as 📄 devpal/mvp.py
    participant Registry as 🗄️ tools/registry.py
    participant LLM as 🤖 大模型 API
    participant Tool as 🔧 具体工具实现

    Note over User,Tool: 🔄 完整 Tool Calling 流程

    User->>MVP: 1. 输入任务（如"帮我写个文件"）
    
    Note over MVP, Registry: 初始化阶段
    MVP->>Registry: registry.get_tool_descriptions()
    Registry->>MVP: 返回 [file_reader, file_writer, execute_command] 完整描述
    
    Note over MVP, LLM: 每轮循环
    MVP->>LLM: 2. client.messages.create()
    Note right of MVP: 包含：messages + tools
    
    LLM-->>MVP: 3. 返回 response
    Note over LLM,MVP: response.stop_reason="tool_use"
    Note over LLM,MVP: response.content[].type="tool_use"
    Note over LLM,MVP: response.content[].name="file_writer" ✅ 契约名称
    
    MVP->>MVP: 4. 解析 response，提取 block.name 和 block.input
    
    MVP->>Registry: 5. registry.execute_tool(block.name, block.input)
    Note right of MVP: block.name = "file_writer"
    
    Registry->>Tool: 6. 根据 name 找到 FileWriterTool 并执行
    Note over Registry,Tool: self._tools.get("file_writer") → FileWriterTool
    
    Tool->>Tool: 7. Pydantic 参数校验 + execute() 逻辑
    Tool-->>Registry: 8. 返回 ToolResult(success=True/False)
    
    Registry-->>MVP: 9. 返回执行结果
    
    MVP->>MVP: 10. 把工具结果包装成 tool_result message
    
    MVP->>LLM: 11. 把工具结果发回给大模型（下一轮循环）
    Note right of MVP: messages.append(tool_result)
    
    LLM-->>MVP: 12. 根据工具结果生成最终回答
    Note over LLM,MVP: stop_reason="end_turn"
    
    MVP-->>User: 13. 输出最终回答
```

---

## 🔍 关键节点详解

| 步骤 | 说明 | 核心代码 |
|------|------|---------|
| **契约绑定** | 工具名 `file_writer` 是双方约定的唯一 ID | `FileWriterTool.name = "file_writer"` |
| **工具描述发送** | 把 name/description/schema 发给大模型 | `client.messages.create(tools=...)` |
| **大模型决策** | 阅读工具描述，选择最适合的工具，生成合法参数 | 大模型内部逻辑 |
| **精确匹配** | 根据返回的 `block.name` 找到对应实现 | `self._tools.get(tool_name)` |
| **结果回传** | 把执行结果发回大模型，让它看到工具做了什么 | `messages.append(tool_result)` |

---

## 📊 循环流程示意图

```
用户输入
   ↓
┌─────────────────────────────────────────┐
│  🔄 主循环 (最多 max_iterations 次)     │
│                                         │
│  ┌──────────┐     ┌────────────────┐  │
│  │  问大模型 │────▶│ 需要调用工具吗?│  │
│  └──────────┘     └────────┬───────┘  │
│      ↑                     │ 是        │
│      │                     ▼           │
│      │               ┌──────────┐      │
│      │               │ 执行工具 │      │
│      │               └────┬─────┘      │
│      │                    │            │
│      │                    ▼            │
│      │            ┌─────────────┐     │
│      │            │ 结果发回大模型│────┘
│      │            └─────────────┘
│      │                    否
│      └─────────────────────┘
   ↓
输出最终回答
```
