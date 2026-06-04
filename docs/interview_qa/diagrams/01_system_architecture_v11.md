# System Architecture Diagram (v11 - No Overlapping)

## DevPalAgent 整体架构图 - 无重叠版

```mermaid
%%{init: {'theme':'default', 'themeVariables': { 'fontSize':'20px', 'fontFamily':'Arial, Helvetica, sans-serif', 'background':'#FFFFFF', 'mainBkg':'#FFFFFF', 'secondBkg':'#FFFFFF', 'primaryColor':'#BA68C8', 'primaryTextColor':'#fff', 'primaryBorderColor':'#6A1B9A', 'lineColor':'#757575', 'secondaryColor':'#4FC3F7', 'tertiaryColor':'#81C784', 'clusterBkg':'#FFFFFF', 'clusterBorder':'#BDBD', 'edgeLabelBackground':'#FFFFFF'}}}%%
graph TB
    %% Layer 1: User Interface
    subgraph UILayer["User Interface Layer"]
        CLI["CLI Interface"]
        Web["Web Interface"]
        IDE["IDE Extensions"]
    end

    %% Layer 2: Agent Layer
    subgraph AgentLayer["Agent Layer - Plan Act Reflect"]
        Planner["Planner<br/>任务规划"]
        Executor["Executor<br/>工具执行"]
        Reflector["Reflector<br/>结果反思"]
      
        Planner --> Executor
        Executor --> Reflector
        Reflector -.retry.-> Planner
    end

    %% Layer 3: OpenSpec Runtime
    subgraph OpenSpecLayer["OpenSpec Runtime Layer"]
        OSExecutor["OpenSpec<br/>Executor"]
        Scheduler["Enhanced<br/>Scheduler"]
        Context["OpenSpec<br/>Context"]
        
        OSExecutor --> Scheduler
        Scheduler --> Context
    end

    %% Layer 4: Phase Execution
    subgraph PhaseLayer["Phase Execution Layer - 11 Phases"]
        Phase1["Phase 1<br/>Parse"]
        Phase2["Phase 2<br/>Structure"]
        Phase3["Phase 3<br/>Design"]
      Phase4["Phase 4<br/>Code"]
      Phase5["Phase 5<br/>Tests"]
        Phase9["Phase 9<br/>Quality"]
        Phase10["Phase 10<br/>Run"]
        Phase11["Phase 11<br/>Report"]
        
        Phase1 --> Phase2
        Phase2 --> Phase3
        Phase3 --> Phase4
        Phase4 --> Phase5
        Phase5 --> Phase9
        Phase9 --> Phase10
        Phase10 --> Phase11
    end

    %% Layer 5: Multi-Agent
    subgraph MultiLayer["Multi-Agent Layer"]
        Coordinator["Multi-Agent<br/>Coordinator"]
        AgentPool["Agent Pool<br/>4-16 Agents"]
        MessageBus["Message Bus"]
        
        Coordinator --> AgentPool
     AgentPool --> MessageBus
    end

    %% Layer 6: Core Services
    subgraph ServiceLayer["Core Services Layer"]
      ToolReg["Tool<br/>Registry"]
        SkillReg["Skill<br/>Registry"]
        LLM["LLM<br/>Client"]
        Validation["Validation<br/>Engine"]
        EventBus["Event<br/>Bus"]
    end

    %% Layer 7: Memory & Knowledge
  subgraph MemoryLayer["Memory and Knowledge Layer"]
        ShortMem["Short-term<br/>Memory"]
        LongMem["Long-term<br/>Memory"]
        ErrorMem["Error<br/>Memory"]
        VectorDB["Vector<br/>Database"]
    end

    %% Layer 8: Storage
    subgraph StorageLayer["Storage Layer"]
        FileSystem["File<br/>System"]
        ChangeDB["OpenSpec<br/>Changes"]
      EventLog["Event<br/>Logs"]
        Checkpoint["Checkpoints"]
    end

    %% Main Flow Connections
    UILayer ==> AgentLayer
    AgentLayer ==> OpenSpecLayer
    OpenSpecLayer ==> PhaseLayer
    
    PhaseLayer ==> MultiLayer
    MultiLayer --> ServiceLayer
    
    AgentLayer --> ServiceLayer
    ServiceLayer --> MemoryLayer
    
    PhaseLayer --> StorageLayer
    ServiceLayer --> StorageLayer
    
    %% Detailed Connections
    CLI --> Planner
    Web --> Planner
    IDE --> Planner
    
    Executor ==> OSExecutor
    
    Scheduler ==> Phase1
    
    Phase4 ==> Coordinator
    Phase5 ==> Coordinator
    
    Planner --> ToolReg
    Executor --> ToolReg
    Planner --> SkillReg
    Executor --> SkillReg
    
    Coordinator --> LLM
    AgentPool --> LLM
    Phase9 --> Validation
    
    Context --> EventBus
    MessageBus --> EventBus
    
    Planner --> ShortMem
    Executor --> LongMem
    Reflector --> ErrorMem
    Phase3 --> VectorDB
    Phase4 --> VectorDB
    
    Phase1 --> ChangeDB
    Phase11 --> ChangeDB
    EventBus --> EventLog
    Scheduler --> Checkpoint
    Phase4 --> FileSystem
    Phase11 --> FileSystem

    %% Styling with Layer Colors
    classDef uiClass fill:#E91E63,stroke:#C2185B,stroke-width:4px,color:#fff
    classDef agentClass fill:#2196F3,stroke:#1565C0,stroke-width:4px,color:#fff
    classDef openspecClass fill:#FF9800,stroke:#E65100,stroke-width:4px,color:#fff
    classDef phaseClass fill:#9C27B0,stroke:#6A1B9A,stroke-width:4px,color:#fff
    classDef multiClass fill:#4CAF50,stroke:#2E7D32,stroke-width:4px,color:#fff
    classDef serviceClass fill:#FFC107,stroke:#F57F17,stroke-width:4px,color:#000
    classDef memoryClass fill:#FF5722,stroke:#D84315,stroke-width:4px,color:#fff
    classDef storageClass fill:#009688,stroke:#00695C,stroke-width:4px,color:#fff
    
    class CLI,Web,IDE uiClass
    class Planner,Executor,Reflector agentClass
    class OSExecutor,Scheduler,Context openspecClass
    class Phase1,Phase2,Phase3,Phase4,Phase5,Phase9,Phase10,Phase11 phaseClass
    class Coordinator,AgentPool,MessageBus multiClass
    class ToolReg,SkillReg,LLM,Validation,EventBus serviceClass
    class ShortMem,LongMem,ErrorMem,VectorDB memoryClass
  class FileSystem,ChangeDB,EventLog,Checkpoint storageClass
```

## 无重叠版特性 (v11)

### 🎯 彻底修复重叠问题

**1. 简化 subgraph 标题**:
- ❌ 去除中文描述（避免与节点重叠）
- ✅ 只保留简洁的英文标题
- 例如：`"User Interface Layer"` 代替 `"🖥️ User Interface Layer - 用户界面层"`

**2. 极简节点内容**:
- 节点只有 1-2 行文字
- 关键节点保留中文（如 Planner、Executor）
- Phase 节点简化为 "Phase X + 功能"

**3. 减小字体**:
- 字体大小：20px（更小，避免重叠）

**4. 对比示例**:

| 元素 | v10（重叠） | v11（无重叠）✅ |
|-----|------------|-------------|
| Subgraph 标题 | "🖥️ User Interface Layer - 用户界面层" | **"User Interface Layer"** |
| LLM Client 节点 | "LLM Client<br/>Prompt Cache<br/>缓存优化" | **"LLM<br/>Client"** |
| Phase 1 节点 | "Phase 1<br/>Parse Requirements<br/>需求解析" | **"Phase 1<br/>Parse"** |
| Multi-Agent Coordinator | "Multi-Agent Coordinator<br/>多智能体协调器<br/>..." | **"Multi-Agent<br/>Coordinator"** |

### ✨ 最终效果

- ✅ Subgraph 标题不再与节点重叠
- ✅ 节点内容极简（1-2 行）
- ✅ 字体更小（20px）
- ✅ 8 层架构结构清晰
- ✅ 颜色分类保留

### 🔧 生成命令

```bash
mmdc -i 01_system_architecture_v11.md \
     -o 01_system_architecture_v11.png \
     -w 3600 \
     -H 4800 \
     -s 3 \
     -b white
```
---

**版本**: v11.0 No Overlapping  
**关键修复**: 彻底解决所有文字重叠问题  
**方法**: 简化 subgraph 标题 + 极简节点内容 + 20px 小字体
