# OpenSpec 11-Phase Pipeline Diagram

## OpenSpec 11 阶段流程图

```mermaid
graph TD
    Start([需求文档<br/>requirements.md]) --> Phase1

    Phase1[Phase 1: Parse Requirements<br/>需求解析]
    Phase2[Phase 2: Create Structure<br/>创建目录结构]
    Phase3[Phase 3: Technical Design<br/>技术设计]
    Phase4[Phase 4: Generate Code<br/>代码生成 Multi-Agent]
    Phase5[Phase 5: Generate Tests<br/>测试生成 Multi-Agent]
    Phase6[Phase 6: Build Configuration<br/>构建配置]
    Phase7[Phase 7: Test Documentation<br/>测试文档]
    Phase8[Phase 8: README<br/>项目文档]
    Phase9[Phase 9: Quality Gate<br/>质量门禁]
    Phase10[Phase 10: Run Tests<br/>测试执行]
    Phase11[Phase 11: Final Report<br/>最终报告]

    Phase1 -->|structured_requirements<br/>delta.json<br/>change_id| Phase2
    Phase2 -->|project_structure<br/>.spec/requirements.json| Phase3
    Phase3 -->|tech_design_content<br/>design.md| Phase4
    
    Phase4 -->|generated_files<br/>source code| Phase5
    Phase5 -->|test_files<br/>test code| Phase6
    
    Phase6 -->|CMakeLists.txt<br/>setup.py| Phase7
    Phase7 -->|test_docs| Phase8
    Phase8 -->|README.md| Phase9
    
    Phase9 -->|quality_report<br/>validation_issues| Decision1{Quality<br/>Gate<br/>Pass?}
    
    Decision1 -->|Yes| Phase10
    Decision1 -->|No| SelfHeal[Self-Healing<br/>根因分析 + 自动修复]
    SelfHeal -->|Fixed| Phase9
    SelfHeal -->|Cannot Fix| Fail([失败<br/>人工介入])
    
    Phase10 -->|test_results<br/>test_summary| Decision2{Tests<br/>Pass?}
    
    Decision2 -->|Yes| Phase11
    Decision2 -->|No| SelfHeal2[Self-Healing<br/>测试修复]
    SelfHeal2 -->|Fixed| Phase10
    SelfHeal2 -->|Cannot Fix| Fail
    
    Phase11 --> End([交付物<br/>final_report<br/>artifact_graph<br/>CLAUDE.md])

    %% Skip Rules
    Phase3 -.installer/tooling<br/>skip.-> Phase4
    Phase5 -.installer<br/>skip.-> Phase6
    Phase6 -.Python<br/>skip.-> Phase7
    Phase9 -.installer<br/>skip.-> Phase10
    %% Multi-Agent Highlight
    Phase4 -.-> MultiAgent1[Multi-Agent Pool<br/>4-16 agents parallel]
    Phase5 -.-> MultiAgent2[Multi-Agent Pool<br/>4-16 agents parallel]

    %% Checkpoint
    Phase1 -.checkpoint.-> CP1[(Checkpoint)]
    Phase4 -.checkpoint.-> CP2[(Checkpoint)]
    Phase9 -.checkpoint.-> CP3[(Checkpoint)]

    %% Styling
    classDef parseClass fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef genClass fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef validateClass fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef reportClass fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef decisionClass fill:#ffebee,stroke:#c62828,stroke-width:2px
    classDef multiClass fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    
    class Phase1,Phase2 parseClass
    class Phase3,Phase4,Phase5,Phase6,Phase7,Phase8 genClass
    class Phase9,Phase10 validateClass
    class Phase11 reportClass
  class Decision1,Decision2 decisionClass
    class MultiAgent1,MultiAgent2 multiClass
```

## 阶段详情

### Phase 1-3: 需求与设计
- **Phase 1**: 解析需求 → structured_requirements + delta.json + change_id
- **Phase 2**: 创建项目结构（语言感知）
- **Phase 3**: AI 生成技术设计文档

### Phase 4-5: 代码生成 (支持 Multi-Agent)
- **Phase 4**: 生成源代码（基础设施 + AI 业务代码）
  - 支持 4-16 个 Agent 并行生成
  - 依赖解析 + 拓扑排序
  - 3-4x 加速
- **Phase 5**: 生成测试代码
  - 同样支持 Multi-Agent 并行

### Phase 6-8: 构建与文档
- **Phase 6**: 生成构建配置（CMake/setup.py）
- **Phase 7**: 生成测试文档
- **Phase 8**: 生成 README

### Phase 9-10: 验证与测试
- **Phase 9**: Quality Gate 四层验证
  - L1: FORMAT
  - L2: SEMANTIC
  - L3: PARSER
  - L4: BUSINESS
  - 失败 → Self-Healing
- **Phase 10**: 执行测试
  - C++: GoogleTest
  - Python: pytest
  - 失败 → Self-Healing

### Phase 11: 最终报告
- 生成 final_report
- 生成 artifact_graph
- 生成 CLAUDE.md

## Phase Skip Rules

不同项目类型跳过不同阶段：

| 项目类型 | 跳过阶段 | 原因 |
|---------|---------|------|
| installer | Phase 3, 5-7, 9-10 | 安装脚本不需要复杂设计和测试 |
| tooling | Phase 3, 6 | 工具脚本简化流程 |
| python | Phase 6 | Python 不需要 CMake |

## Checkpoint & Resume

关键节点设置 Checkpoint：
- Phase 1: 需求解析完成
- Phase 4: 代码生成完成
- Phase 9: 质量验证完成

失败后可从最近的 Checkpoint 恢复。

## Self-Healing 流程

```
Phase 失败
    ↓
Root Cause Analysis (根因分析)
    ↓
Auto-Fix Strategy (自动修复策略)
    ↓
Apply Fix (应用修复)
    ↓
Re-run Phase (重新执行)
```

成功率：~80%
