#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate Plan-Act-Reflect diagram with Graphviz."""

import os
import subprocess
import tempfile

dot_content = '''digraph PlanActReflect {
    rankdir=LR;
    nodesep=0.6;
    ranksep=1.0;
    node [shape=box, style="filled, rounded", fontname="Microsoft YaHei", fontsize=11];
    edge [fontname="Microsoft YaHei", fontsize=10];

    User [label="用户输入", fillcolor="#fff3e0"];

    subgraph cluster_plan {
        label="规划阶段 Plan";
        style="filled, dashed";
        fillcolor="#e3f2fd";
        color="#0d47a1";
        fontname="Microsoft YaHei";
        fontsize=13;

        Planner [label="规划器"];
        PlanEval [label="可行性评估"];
        StepBreak [label="任务拆解"];
    }

    subgraph cluster_act {
        label="执行阶段 Act";
        style="filled, dashed";
        fillcolor="#e8f5e9";
        color="#1b5e20";
        fontname="Microsoft YaHei";
        fontsize=13;

        Executor [label="执行器"];
        ToolDecide [label="工具决策"];
        ToolSelect [label="选择工具"];
        ToolExec [label="执行工具"];
        ResultHandle [label="处理结果"];
        ResultGen [label="生成结果"];
        Check [label="完成检查"];
    }

    subgraph cluster_reflect {
        label="反思阶段 Reflect";
        style="filled, dashed";
        fillcolor="#f3e5f5";
        color="#4a148c";
        fontname="Microsoft YaHei";
        fontsize=13;

        Reflector [label="反思器"];
        Eval [label="评估执行"];
        ErrorId [label="识别错误"];
        PlanAdjust [label="调整计划"];
        MemoryStore [label="存入记忆"];
    }

    Output [label="输出结果", fillcolor="#ffebee"];
    Summary [label="经验总结", fillcolor="#ffebee"];

    User -> Planner;
    Planner -> PlanEval;
    PlanEval -> StepBreak;

    StepBreak -> Executor;
    Executor -> ToolDecide;
    ToolDecide -> ToolSelect [label="调用工具"];
    ToolSelect -> ToolExec;
    ToolExec -> ResultHandle;
    ResultHandle -> Check;
    ToolDecide -> ResultGen [label="无需工具"];
    ResultGen -> Check;

    Check -> Reflector [label="未完成"];
    Reflector -> Eval;
    Eval -> ErrorId;
    ErrorId -> PlanAdjust;
    PlanAdjust -> MemoryStore;
    MemoryStore -> Executor;

    Check -> Output [label="已完成"];
    Output -> Summary;
}
'''

output_path = os.path.join(os.path.dirname(__file__), "plan-act-reflect.png")

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
