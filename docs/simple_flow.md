# DevPal Agent 极简流程图

```mermaid
graph LR
    A[用户] -->|输入任务| B(大模型)
    B -->|返回 tool_name| C{本地代码}
    C -->|根据 name 执行工具| D[工具实现]
    D -->|返回结果| B
    B -->|最终回答| A
    
    style A fill:#e3f2fd,stroke:#2196f3,stroke-width:4px,font-size:36px
    style B fill:#fff3e0,stroke:#ff9800,stroke-width:4px,font-size:36px
    style C fill:#e8f5e9,stroke:#4caf50,stroke-width:4px,font-size:36px
    style D fill:#f3e5f5,stroke:#9c27b0,stroke-width:4px,font-size:36px
    
    linkStyle 0 stroke-width:4px,font-size:24px
    linkStyle 1 stroke-width:4px,font-size:24px
    linkStyle 2 stroke-width:4px,font-size:24px
    linkStyle 3 stroke-width:4px,font-size:24px
    linkStyle 4 stroke-width:4px,font-size:24px
```

---

```
              工具描述发给大模型
                     ↓
用户输入 → 大模型决策 → 返回 name → 本地匹配执行 → 结果回传
                     ↑                          │
                     └──────────────────────────┘
```

**核心：工具名 name 是唯一契约，贯穿全程！**
