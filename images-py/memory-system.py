#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate Mermaid diagram for DevPal Agent Memory System."""

import os
import subprocess
import tempfile

mermaid_content = """flowchart TB
    AgentEngine["Agent 核心引擎"]

    subgraph MemorySystem["三层记忆系统 (3-Layer Memory System)"]
        subgraph ShortTerm["短期记忆 Short-Term Memory"]
            direction LR
            Conversation["对话历史\nConversation History"]
            ContextWindow["滑动上下文窗口\nSliding Context Window"]
            TokenManage["Token 计数与截断\nToken Management"]
        end

        subgraph LongTerm["长期记忆 Long-Term Memory"]
            direction LR
            Embedding["Embedding 生成\nall-MiniLM-L6-v2"]
            VectorDB["向量数据库\nChromaDB"]
            RAGRetrieval["RAG 检索\nSemantic Search"]
            Persistence["持久化存储\nLocal Persistence"]
        end

        subgraph ErrorMemory["错误记忆 Error Memory"]
            direction LR
            PatternStore["错误模式存储\nError Pattern Storage"]
            PatternMatch["错误模式匹配\nPattern Matching"]
            AvoidRepeat["避免重复犯错\nError Avoidance"]
        end
    end

    AgentEngine --> ShortTerm
    AgentEngine --> LongTerm
    AgentEngine --> ErrorMemory

    ShortTerm --> LongTerm
    LongTerm --> RAGRetrieval
    ErrorMemory --> PatternMatch

    classDef engine fill:#fce4ec,stroke:#880e4f,stroke-width:2px;
    classDef shortterm fill:#e3f2fd,stroke:#0d47a1,stroke-width:2px;
    classDef longterm fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px;
    classDef errormemory fill:#fff3e0,stroke:#e65100,stroke-width:2px;

    class AgentEngine engine;
    class ShortTerm,Conversation,ContextWindow,TokenManage shortterm;
    class LongTerm,Embedding,VectorDB,RAGRetrieval,Persistence longterm;
    class ErrorMemory,PatternStore,PatternMatch,AvoidRepeat errormemory;
"""

output_path = os.path.join(os.path.dirname(__file__), "memory-system.png")

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
        '-w', '1200',
        '-H', '800'
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
