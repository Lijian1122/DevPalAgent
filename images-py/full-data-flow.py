#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate Mermaid diagram for DevPal Agent full data flow - Optimized layout."""

import os
import subprocess
import tempfile

mermaid_content = """flowchart LR
    User["👤 用户输入"] --> Orchestrator["🎯 Agent 协调器"]

    Orchestrator --> MemoryRead["📖 读取记忆"]
    MemoryRead --> ShortTerm["短期记忆\n对话历史"]
    MemoryRead --> LongTerm["长期记忆\nRAG 检索"]
    MemoryRead --> ErrorMem["错误记忆\n模式匹配"]

    MemoryRead --> Planner["📋 规划器"]
    Planner --> PlanGen["生成计划"]
    PlanGen --> PlanEval["可行性评估"]
    PlanEval --> Steps["执行步骤"]

    Steps --> Executor["🚀 执行器"]
    Executor --> LLM["🤖 LLM 推理"]
    LLM --> ToolDecide["工具决策"]

    ToolDecide -->|调用工具| ToolSelect["选择工具"]
    ToolSelect --> ToolExec["执行工具"]
    ToolExec --> ResultHandle["处理结果"]
    ResultHandle --> LLM

    ToolDecide -->|无需工具| ResultGen["生成结果"]

    ResultHandle --> Check["✅ 完成检查"]
    ResultGen --> Check

    Check -->|未完成| Reflector["💡 反思器"]
    Reflector --> ErrorDetect["错误检测"]
    ErrorDetect --> Pattern["提取模式"]
    Pattern --> MemoryWrite["写入记忆"]
    Pattern --> PlanAdjust["调整计划"]
    PlanAdjust --> Executor

    Check -->|已完成| Output["📤 最终输出"]
    Output --> Summary["经验总结"]
    Summary --> MemorySystem["记忆系统"]
    MemoryWrite --> MemorySystem

    classDef user fill:#fff3e0,stroke:#e65100,stroke-width:2px;
    classDef orchestrator fill:#fce4ec,stroke:#880e4f,stroke-width:2px;
    classDef memory fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px;
    classDef planner fill:#e3f2fd,stroke:#0d47a1,stroke-width:2px;
    classDef executor fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;
    classDef reflector fill:#fff8e1,stroke:#ff6f00,stroke-width:2px;
    classDef output fill:#ffebee,stroke:#b71c1c,stroke-width:2px;

    class User user;
    class Orchestrator orchestrator;
    class MemoryRead,ShortTerm,LongTerm,ErrorMem,MemoryWrite,MemorySystem memory;
    class Planner,PlanGen,PlanEval,Steps planner;
    class Executor,LLM,ToolDecide,ToolSelect,ToolExec,ResultHandle,ResultGen,Check executor;
    class Reflector,ErrorDetect,Pattern,PlanAdjust reflector;
    class Output,Summary output;
"""

output_path = os.path.join(os.path.dirname(__file__), "full-data-flow.png")

with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False, encoding='utf-8') as f:
    f.write(mermaid_content)
    temp_mmd = f.name

try:
    cmd = [
        'C:\\NVM\\nodejs\\node.exe',
        'C:\\NVM\\nodejs\\node_modules\\@mermaid-js\\mermaid-cli\\src\\cli.js',
        '-i', temp_mmd,
        '-o', output_path,
        '-b', 'white',
        '-w', '1600',
        '-H', '900'
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Exit code: {result.returncode}")
    if result.stdout:
        print(f"stdout: {result.stdout}")
    if result.stderr:
        print(f"stderr: {result.stderr}")
    if result.returncode == 0:
        print(f"[OK] Diagram generated: {output_path}")
    else:
        raise Exception(f"Command failed with exit code {result.returncode}")

finally:
    os.unlink(temp_mmd)
