#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate 3-layer architecture diagram with Graphviz (better layout control)."""

import os
import subprocess
import tempfile

dot_content = '''digraph Architecture {
    rankdir=TB;
    nodesep=0.8;
    ranksep=1.2;
    node [shape=box, style="filled, rounded", fillcolor=white, fontname="Microsoft YaHei", fontsize=11];
    edge [style=invis];

    subgraph cluster_interface {
        label="交互层 Interface Layer";
        style="filled, dashed";
        fillcolor="#e1f5fe";
        color="#01579b";
        fontname="Microsoft YaHei";
        fontsize=14;
        rank=same;
        CLI [label="CLI 命令行"];
        WebUI [label="Web UI"];
        IDE [label="IDE 插件"];
    }

    subgraph cluster_core {
        label="Agent 核心引擎层 Core Engine";
        style="filled, dashed";
        fillcolor="#f3e5f5";
        color="#4a148c";
        fontname="Microsoft YaHei";
        fontsize=14;
        rank=same;
        Planner [label="规划器 Planner\\n任务拆解\\n计划生成\\n可行性评估"];
        Executor [label="执行器 Executor\\n工具选择\\n工具调用\\n结果处理"];
        Reflector [label="反思器 Reflector\\n错误检测\\n经验总结\\n计划调整"];
    }

    subgraph cluster_infra {
        label="基础能力层 Infrastructure";
        style="filled, dashed";
        fillcolor="#e8f5e9";
        color="#1b5e20";
        fontname="Microsoft YaHei";
        fontsize=14;
        rank=same;
        LLM [label="LLM 封装层\\n多模型支持\\nToken 管理\\n重试机制"];
        Memory [label="记忆系统\\n短期记忆\\n长期记忆\\n错误记忆"];
        Tools [label="工具系统\\n文件读写\\n命令执行\\n代码分析"];
    }

    cluster_interface -> cluster_core;
    cluster_core -> cluster_infra;
}
'''

output_path = os.path.join(os.path.dirname(__file__), "architecture-3layer.png")

with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False, encoding='utf-8') as f:
    f.write(dot_content)
    temp_dot = f.name

try:
    cmd = ['dot', '-Tpng', '-Gdpi=150', temp_dot, '-o', output_path]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    print(f"Exit code: {result.returncode}")
    if result.returncode == 0:
        print(f"[OK] Diagram generated: {output_path}")
    else:
        print(f"stderr: {result.stderr}")
        raise Exception(f"Command failed with exit code {result.returncode}")
finally:
    os.unlink(temp_dot)
