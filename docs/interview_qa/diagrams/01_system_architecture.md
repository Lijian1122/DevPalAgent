# System Architecture Diagram

## DevPalAgent 整体架构图

```mermaid
graph TB
    subgraph "User Interface Layer"
        CLI[CLI Interface]
        Web[Web Interface]
        IDE[IDE Extensions]
    end

    subgraph "Agent Layer - Plan-Act-Reflect"
        Planner[Planner<br/>任务规划]
        Executor[Executor<br/>工具执行]
        Reflector[Reflector<br/>结果反思]
        
        Planner --> Executor
        Executor --> Reflector
        Reflector -.重试.-> Planner
    end
    subgraph "OpenSpec Runtime Layer"
        OSExecutor[OpenSpec Executor<br/>工作流门面]
      Scheduler[Enhanced Scheduler<br/>阶段调度器]
        Context[OpenSpec Context<br/>共享状态]
        
        OSExecutor --> Scheduler
        Scheduler --> Context
    end

    subgraph "Phase Execution Layer"
        Phase1[Phase 1<br/>Parse Requirements]
        Phase2[Phase 2<br/>Create Structure]
        Phase3[Phase 3<br/>Technical Design]
      Phase4[Phase 4<br/>Generate Code<br/>Multi-Agent]
        Phase5[Phase 5<br/>Generate Tests<br/>Multi-Agent]
     Phase9[Phase 9<br/>Quality Gate]
        Phase10[Phase 10<br/>Run Tests]
        Phase11[Phase 11<br/>Final Report]
        
        Phase1 --> Phase2
        Phase2 --> Phase3
        Phase3 --> Phase4
        Phase4 --> Phase5
        Phase5 --> Phase9
        Phase9 --> Phase10
        Phase10 --> Phase11
  end

  subgraph "Multi-Agent Layer"
    Coordinator[Multi-Agent<br/>Coordinator]
        AgentPool[Agent Pool<br/>4-16 Agents]
        MessageBus[Message Bus<br/>事件总线]
        
        Coordinator --> AgentPool
        AgentPool --> MessageBus
    end

    subgraph "Core Services Layer"
        ToolRegistry[Tool Registry<br/>工具注册表]
        SkillRegistry[Skill Registry<br/>技能注册表]
        LLMClient[LLM Client<br/>Prompt Cache]
        ValidationEngine[Validation Engine<br/>四层验证]
        EventBus[EventBus<br/>事件总线]
    end

    subgraph "Memory & Knowledge Layer"
        ShortMemory[Short-term Memory<br/>对话上下文]
        LongMemory[Long-term Memory<br/>用户偏好]
        ErrorMemory[Error Memory<br/>失败案例]
        VectorDB[Vector Database<br/>Chroma/FAISS]
    end

    subgraph "Storage Layer"
        FileSystem[File System<br/>代码/文档]
        ChangeDB[OpenSpec Changes<br/>变更管理]
        EventLog[Event Logs<br/>JSONL]
        Checkpoint[Checkpoints<br/>断点恢复]
    end

    %% Connections
    CLI --> Planner
    Web --> Planner
    IDE --> Planner
    
    Planner --> ToolRegistry
    Planner --> SkillRegistry
    
    Executor --> ToolRegistry
    Executor --> SkillRegistry
    Executor --> OSExecutor
    
    Scheduler --> Phase1
    Scheduler --> Phase4
    Scheduler --> Phase9
    
    Phase4 --> Coordinator
    Phase5 --> Coordinator
    
    Coordinator --> LLMClient
    AgentPool --> LLMClient
    
    Phase9 --> ValidationEngine
    
    Context --> EventBus
    MessageBus --> EventBus
    
    Planner --> ShortMemory
    Executor --> LongMemory
    Reflector --> ErrorMemory
    
    Phase3 --> VectorDB
    Phase4 --> VectorDB
    
    Phase1 --> ChangeDB
    Phase11 --> ChangeDB
    
    EventBus --> EventLog
    Scheduler --> Checkpoint
    
    Phase4 --> FileSystem
    Phase11 --> FileSystem

    %% Styling
    classDef agentClass fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef openspecClass fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef phaseClass fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef multiClass fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef serviceClass fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef memoryClass fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef storageClass fill:#e0f2f1,stroke:#004d40,stroke-width:2px
    
    class Planner,Executor,Reflector agentClass
    class OSExecutor,Scheduler,Context openspecClass
    class Phase1,Phase2,Phase3,Phase4,Phase5,Phase9,Phase10,Phase11 phaseClass
    class Coordinator,AgentPool,MessageBus multiClass
    class ToolRegistry,SkillRegistry,LLMClient,ValidationEngine,EventBus serviceClass
    class ShortMemory,LongMemory,ErrorMemory,VectorDB memoryClass
    class FileSystem,ChangeDB,EventLog,Checkpoint storageClass
```

## 架构说明

### 分层设计

1. **User Interface Layer**: CLI、Web、IDE 多入口
2. **Agent Layer**: Plan-Act-Reflect 交互式链路
3. **OpenSpec Runtime Layer**: 确定性工作流执行
4. **Phase Execution Layer**: 11 阶段流水线
5. **Multi-Agent Layer**: 并行执行协调
6. **Core Services Layer**: 核心服务组件
7. **Memory & Knowledge Layer**: 记忆与知识管理
8. **Storage Layer**: 持久化存储

### 关键特性

- **双链路**: Agent 链路（灵活）+ OpenSpec 链路（确定性）
- **多智能体**: Phase 4/5 支持 4-16 个 Agent 并行
- **事件驱动**: EventBus 贯穿全流程
- **记忆系统**: 三层记忆 + 向量检索
- **可恢复**: Checkpoint 断点续传

### 数据流

```
User Request
    ↓
Planner (规划)
    ↓
Executor (执行) → OpenSpec Workflow
    ↓                     ↓
Reflector (反思)    Phase 1-11 (确定性流程)
    ↓                  ↓
                 Multi-Agent (并行)
              ↓
                 Quality Gate (验证)
                          ↓
                    Final Report (交付)
```
