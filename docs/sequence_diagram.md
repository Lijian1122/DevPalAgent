# DevPal Agent Tool Calling 时序图（优化版）

```mermaid
sequenceDiagram
    actor User as 用户
    participant MVP as mvp.py
    participant Reg as registry.py
    participant LLM as 大模型API
    participant Tool as 工具实现

    User->>MVP: 1. 输入任务
    Note over MVP: 初始化工具
    
    MVP->>Reg: get_tool_descriptions()
    Reg-->>MVP: [工具列表]
    
    loop 最多 max_iterations 次
        MVP->>LLM: 2. messages + tools
        Note over LLM: 大模型理解工具描述
        
        alt 需要调用工具
            LLM-->>MVP: 3. tool_use(name, args)
            Note over MVP: 收到工具名 + 参数
            
            MVP->>Reg: 4. execute_tool(name, args)
            Reg->>Tool: 5. 根据name匹配执行
            Tool-->>Reg: 6. ToolResult
            Reg-->>MVP: 返回执行结果
            
            MVP->>LLM: 7. tool_result 发回
        else 不需要工具
            LLM-->>MVP: 3. 直接回答
        end
    end
    
    MVP-->>User: 8. 输出最终结果
```

---

## 关键交互点：

| 步骤 | 说明 | 核心契约 |
|------|------|---------|
| 2 | **工具描述发送** | name + description + schema |
| 3 | **大模型返回** | 严格使用相同的 `name` 字符串 |
| 4 | **本地匹配** | `registry.get(name)` 精确查找 |

---

## 核心设计原则：

**工具名 `name` 是贯穿全流程的唯一契约 ID**

```
定义时: FileWriterTool.name = "file_writer"
    ↓
发送时: "name": "file_writer"
    ↓
返回时: block.name = "file_writer"
    ↓
执行时: registry.get("file_writer")
```
