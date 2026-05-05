# -*- coding: utf-8 -*-
"""
DevPal Agent v1.6 - 架构图生成器 (优化版)
优化内容：大幅提升可读性和美观度
- 增大字体，优化节点内容简洁化
- 优化颜色对比度
- 增大节点间距
- 测试编排数据流部分重点优化
"""
from graphviz import Digraph
import os

os.makedirs('./docs', exist_ok=True)

# 全局设置 - 优化版
GRAPH_STYLE = {
    'fontname': 'Microsoft YaHei',
    'fontpath': 'C:/Windows/Fonts/msyh.ttc',
    'fontsize': '20',  # 增大字体
    'dpi': '600',
    'nodesep': '1.8',  # 增大节点间距
    'ranksep': '2.2',   # 增大行间距
    'charset': 'utf8',
}

NODE_STYLE = {
    'fontname': 'Microsoft YaHei',
    'fontsize': '18',  # 增大节点字体
    'shape': 'box',
    'style': 'filled,rounded,bold',
    'penwidth': '5',
}

HEADER_STYLE = {
    'fontname': 'Microsoft YaHei',
    'fontsize': '22',
    'style': 'filled,bold',
    'penwidth': '6',
}

CLUSTER_STYLE = {
    'fontname': 'Microsoft YaHei',
    'fontsize': '24',
    'penwidth': '6',
}

EDGE_STYLE = {
    'fontname': 'Microsoft YaHei',
    'fontsize': '16',
}


def create_architecture_overview_v16():
    """系统整体架构图 v1.6 - 优化版"""
    dot = Digraph(
        'DevPal_Architecture_v1.6',
        filename='./docs/DevPal_Architecture_Overview_v1.6',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='40,32', rankdir='TB', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    # 用户层
    with dot.subgraph(name='cluster_user') as c:
        c.attr(style='filled', color='#FFF8E1', label='【用户层】', pencolor='#FF8F00', **CLUSTER_STYLE)
        c.node('User', '用户\n输入查询\n"review code test run"', fillcolor='#E65100', fontcolor='white', fontsize='24')
        c.node('CLI', '命令行\n交互式模式', fillcolor='#FF7043', fontcolor='white', fontsize='20')
        c.node('Web', 'Web界面\n多标签工具', fillcolor='#FF8A65', fontcolor='white', fontsize='20')

    # 核心引擎层
    with dot.subgraph(name='cluster_core') as c:
        c.attr(style='filled', color='#E3F2FD', label='【核心引擎层】', pencolor='#1565C0', **CLUSTER_STYLE)
        c.node('Engine', '代理引擎\n主执行循环\n多工具编排', fillcolor='#0D47A1', fontcolor='white', **HEADER_STYLE)

        with c.subgraph(name='cluster_planner') as pc:
            pc.attr(style='filled', color='#BBDEFB', label='规划模块', fontsize='20')
            pc.node('PlanGen', '计划生成\n启发式/LLM\n测试任务识别', fillcolor='#42A5F5', fontsize='18')
            pc.node('Feasibility', '可行性评估\n危险检测\n参数校验', fillcolor='#42A5F5', fontsize='18')
            pc.node('PlanAdjust', '计划调整\n动态修改\n结果反馈', fillcolor='#42A5F5', fontsize='18')

        with c.subgraph(name='cluster_reflector') as rc:
            rc.attr(style='filled', color='#C8E6C9', label='反思模块', fontsize='20')
            rc.node('Reflection', '执行反思\n结果分析\n测试评估', fillcolor='#2E7D32', fontcolor='white', fontsize='18')
            rc.node('PatternMatch', '模式匹配\n错误检测\n编译失败分析', fillcolor='#2E7D32', fontcolor='white', fontsize='18')
            rc.node('Lessons', '经验提取\n总结学习\n测试最佳实践', fillcolor='#2E7D32', fontcolor='white', fontsize='18')

    # 记忆层
    with dot.subgraph(name='cluster_memory') as c:
        c.attr(style='filled', color='#FFF3E0', label='【记忆系统层】', pencolor='#E65100', **CLUSTER_STYLE)
        c.node('MM', '记忆管理器\n统一入口\n测试记忆', fillcolor='#E65100', fontcolor='white', **HEADER_STYLE)
        c.node('STM', '短期记忆\n对话上下文\n滑动窗口', fillcolor='#FFCA28', fontsize='16')
        c.node('LTM', '长期记忆\n用户偏好\n任务经验\n测试最佳实践', fillcolor='#FFA000', fontsize='16')
        c.node('EM', '错误记忆\n模式跟踪\n修正建议\n编译错误库', fillcolor='#FF6F00', fontcolor='white', fontsize='16')

    # 连接线
    dot.edge('User', 'CLI', color='#E64A19', penwidth='6', **EDGE_STYLE)
    dot.edge('User', 'Web', color='#E64A19', penwidth='6', **EDGE_STYLE)
    dot.edge('CLI', 'Engine', color='#E64A19', penwidth='6', **EDGE_STYLE)
    dot.edge('Web', 'Engine', color='#E64A19', penwidth='6', **EDGE_STYLE)
    dot.edge('Engine', 'PlanGen', color='#1565C0', penwidth='5', **EDGE_STYLE)
    dot.edge('PlanGen', 'Feasibility', color='#1565C0', penwidth='4', **EDGE_STYLE)
    dot.edge('Feasibility', 'PlanAdjust', color='#1565C0', penwidth='4', **EDGE_STYLE)
    dot.edge('PlanAdjust', 'Engine', color='#1565C0', penwidth='4', **EDGE_STYLE)
    dot.edge('Engine', 'MM', color='#F57C00', penwidth='5', **EDGE_STYLE)
    dot.edge('MM', 'STM', color='#F57C00', penwidth='4', **EDGE_STYLE)
    dot.edge('MM', 'LTM', color='#F57C00', penwidth='4', **EDGE_STYLE)
    dot.edge('MM', 'EM', color='#F57C00', penwidth='4', **EDGE_STYLE)
    dot.edge('Lessons', 'LTM', color='#2E7D32', style='dashed', penwidth='4', **EDGE_STYLE)
    dot.edge('Lessons', 'EM', color='#2E7D32', style='dashed', penwidth='4', **EDGE_STYLE)
    dot.edge('Engine', 'Reflection', color='#2E7D32', penwidth='5', **EDGE_STYLE)
    dot.edge('Reflection', 'PatternMatch', color='#2E7D32', penwidth='4', **EDGE_STYLE)
    dot.edge('PatternMatch', 'Lessons', color='#2E7D32', penwidth='4', **EDGE_STYLE)
    dot.edge('Reflection', 'PlanAdjust', color='#2E7D32', style='dashed', penwidth='4', **EDGE_STYLE)

    dot.render(cleanup=True)
    print("[OK] 系统整体架构图 v1.6 (优化版) 已生成")


def create_test_orchestrator_architecture_v16():
    """测试编排系统架构图 v1.6 - 优化版"""
    dot = Digraph(
        'Test_Orchestrator_v1.6',
        filename='./docs/Test_Orchestrator_System_Architecture_v1.6',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='42,34', rankdir='TB', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    # 触发入口
    with dot.subgraph(name='cluster_trigger') as c:
        c.attr(style='filled', color='#E3F2FD', label='【触发入口】', pencolor='#1565C0', **CLUSTER_STYLE)
        c.node('Trigger', '用户查询触发\n"review code test run"\nPlanner自动识别测试任务\nAgentEngine直接执行',
                fillcolor='#0D47A1', fontcolor='white', fontsize='20')

    # 核心编排器
    with dot.subgraph(name='cluster_orchestrator') as c:
        c.attr(style='filled', color='#E8F5E9', label='【TestOrchestrator 核心编排器】', pencolor='#1B5E20', **CLUSTER_STYLE)
        c.node('Orch', 'TestOrchestrator\n一站式自动化测试编排\n6步闭环流程',
                fillcolor='#1B5E20', fontcolor='white', **HEADER_STYLE)

        # 核心参数
        with c.subgraph(name='cluster_params') as p:
            p.attr(style='filled', color='#A5D6A7', label='参数配置', fontsize='20', pencolor='#2E7D32')
            p.node('P1', 'file_path\n源文件路径\nC/C++/Python/JS', fillcolor='#43A047', fontcolor='white', fontsize='16')
            p.node('P2', 'project_name\n项目名称\n自动创建输出目录', fillcolor='#43A047', fontcolor='white', fontsize='16')
            p.node('P3', '流程开关\n可单独启用/禁用', fillcolor='#43A047', fontcolor='white', fontsize='16')

    # 6步执行流程 - 优化版
    with dot.subgraph(name='cluster_steps') as c:
        c.attr(style='filled', color='#C8E6C9', label='【6步自动化执行流程】', pencolor='#2E7D32', **CLUSTER_STYLE)

        with c.subgraph(name='cluster_row1') as r1:
            r1.attr(rank='same')
            r1.node('S1', '步骤1\n代码审查\nCodeReview', fillcolor='#2E7D32', fontcolor='white', fontsize='16')
            r1.node('S2', '步骤2\n生成报告\nCodeReviewReport', fillcolor='#2E7D32', fontcolor='white', fontsize='16')
            r1.node('S3', '步骤3\n自动修复\nAutoFixer', fillcolor='#2E7D32', fontcolor='white', fontsize='16')

        with c.subgraph(name='cluster_row2') as r2:
            r2.attr(rank='same')
            r2.node('S4', '步骤4\n生成测试文档\nTestDocGenerator', fillcolor='#004D40', fontcolor='white', fontsize='16')
            r2.node('S5', '步骤5\n生成测试代码\nTestGenerator', fillcolor='#004D40', fontcolor='white', fontsize='16')
            r2.node('S6', '步骤6\n运行测试\nTestRunner', fillcolor='#004D40', fontcolor='white', fontsize='16')

    # 增强的 TestRunner 细节
    with dot.subgraph(name='cluster_test_runner') as c:
        c.attr(style='filled', color='#E1BEE7', label='【TestRunner 编译器支持】', pencolor='#7B1FA2', **CLUSTER_STYLE)
        c.node('TR', 'TestRunner 核心增强\nWindows MSVC 编译器检测\nVS2019/VS2022 Build Tools',
                fillcolor='#7B1FA2', fontcolor='white', fontsize='18')

        with c.subgraph(name='cluster_detect') as d:
            d.attr(rank='same')
            d.node('TR1', 'vswhere探测\nVC Tools 检测', fillcolor='#9C27B0', fontcolor='white', fontsize='15')
            d.node('TR2', '已知路径扫描\nProgram Files 扫描', fillcolor='#9C27B0', fontcolor='white', fontsize='15')
            d.node('TR3', '环境变量检查\nPATH 环境变量', fillcolor='#9C27B0', fontcolor='white', fontsize='15')

        with c.subgraph(name='cluster_env') as e:
            e.attr(rank='same')
            e.node('TR4', 'INCLUDE 设置\n头文件路径配置', fillcolor='#BA68C8', fontcolor='white', fontsize='15')
            e.node('TR5', 'LIB 设置\n库文件路径配置', fillcolor='#BA68C8', fontcolor='white', fontsize='15')
            e.node('TR6', '编译参数\n/FSANITIZE /Zi /Od', fillcolor='#BA68C8', fontcolor='white', fontsize='15')

    # 输出产物
    with dot.subgraph(name='cluster_output') as c:
        c.attr(style='filled', color='#FFF8E1', label='【输出产物】', pencolor='#FF8F00', **CLUSTER_STYLE)
        c.node('Out', '统一输出目录结构\nproject_name/', fillcolor='#FF8F00', fontcolor='white', **HEADER_STYLE)
        with c.subgraph(name='cluster_files') as f:
            f.attr(rank='same')
            f.node('F1', '源码备份\nbackup.cpp', fillcolor='#FFA000', fontcolor='white', fontsize='16')
            f.node('F2', '审查报告\nreview.md', fillcolor='#FFA000', fontcolor='white', fontsize='16')
            f.node('F3', '测试文档\ntest_doc.md', fillcolor='#FFA000', fontcolor='white', fontsize='16')
            f.node('F4', '测试代码\ntest.cpp', fillcolor='#FFA000', fontcolor='white', fontsize='16')

    # 结果统计
    with dot.subgraph(name='cluster_stats') as c:
        c.attr(style='filled', color='#FFEBEE', label='【统计与反馈】', pencolor='#C62828', **CLUSTER_STYLE)
        c.node('Stats', '执行统计与闭环反馈', fillcolor='#C62828', fontcolor='white', **HEADER_STYLE)
        with c.subgraph(name='cluster_stats_items') as si:
            si.attr(rank='same')
            si.node('ST1', '修复率统计\n按严重程度分类', fillcolor='#EF5350', fontcolor='white', fontsize='16')
            si.node('ST2', '未修复问题详情\n含具体修复建议', fillcolor='#EF5350', fontcolor='white', fontsize='16')
            si.node('ST3', '测试执行摘要\n编译/运行/通过率', fillcolor='#EF5350', fontcolor='white', fontsize='16')

    # 流程连接线 - 主流程
    dot.edge('Trigger', 'Orch', color='#1B5E20', penwidth='7', **EDGE_STYLE)
    dot.edge('Orch', 'P1', color='#1B5E20', penwidth='5', **EDGE_STYLE)
    dot.edge('Orch', 'P2', color='#1B5E20', penwidth='5', **EDGE_STYLE)
    dot.edge('Orch', 'P3', color='#1B5E20', penwidth='5', **EDGE_STYLE)
    dot.edge('Orch', 'S1', color='#2E7D32', penwidth='6', **EDGE_STYLE)
    dot.edge('S1', 'S2', color='#2E7D32', penwidth='5', **EDGE_STYLE)
    dot.edge('S2', 'S3', color='#2E7D32', penwidth='5', **EDGE_STYLE)
    dot.edge('S3', 'S4', color='#004D40', penwidth='5', **EDGE_STYLE)
    dot.edge('S4', 'S5', color='#004D40', penwidth='5', **EDGE_STYLE)
    dot.edge('S5', 'S6', color='#004D40', penwidth='5', **EDGE_STYLE)
    dot.edge('S6', 'Out', color='#FF8F00', penwidth='6', **EDGE_STYLE)

    # TestRunner 增强
    dot.edge('S6', 'TR', color='#7B1FA2', penwidth='5', **EDGE_STYLE)
    dot.edge('TR', 'TR1', color='#7B1FA2', penwidth='4', **EDGE_STYLE)
    dot.edge('TR', 'TR2', color='#7B1FA2', penwidth='4', **EDGE_STYLE)
    dot.edge('TR', 'TR3', color='#7B1FA2', penwidth='4', **EDGE_STYLE)
    dot.edge('TR', 'TR4', color='#7B1FA2', penwidth='4', **EDGE_STYLE)
    dot.edge('TR', 'TR5', color='#7B1FA2', penwidth='4', **EDGE_STYLE)
    dot.edge('TR', 'TR6', color='#7B1FA2', penwidth='4', **EDGE_STYLE)

    # 输出文件
    dot.edge('Out', 'F1', color='#FFA000', penwidth='4', **EDGE_STYLE)
    dot.edge('Out', 'F2', color='#FFA000', penwidth='4', **EDGE_STYLE)
    dot.edge('Out', 'F3', color='#FFA000', penwidth='4', **EDGE_STYLE)
    dot.edge('Out', 'F4', color='#FFA000', penwidth='4', **EDGE_STYLE)

    # 统计反馈
    dot.edge('S6', 'Stats', color='#C62828', penwidth='5', **EDGE_STYLE)
    dot.edge('Stats', 'ST1', color='#C62828', penwidth='4', **EDGE_STYLE)
    dot.edge('Stats', 'ST2', color='#C62828', penwidth='4', **EDGE_STYLE)
    dot.edge('Stats', 'ST3', color='#C62828', penwidth='4', **EDGE_STYLE)

    dot.render(cleanup=True)
    print("[OK] 测试编排系统架构图 v1.6 (优化版) 已生成")


def create_data_flow_diagram_v16():
    """完整数据流图 v1.6 - 优化版"""
    dot = Digraph(
        'Data_Flow_v1.6',
        filename='./docs/Complete_Data_Flow_v1.6',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='44,32', rankdir='LR', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    with dot.subgraph(name='cluster_input') as c:
        c.attr(style='filled', color='#FFF8E1', label='【输入层】', pencolor='#FF8F00', **CLUSTER_STYLE)
        c.node('User', '用户输入\n查询字符串\n"review code test run"', fillcolor='#E65100', fontcolor='white', fontsize='22')

    with dot.subgraph(name='cluster_plan_data') as c:
        c.attr(style='filled', color='#E3F2FD', label='【规划数据流】', pencolor='#1565C0', **CLUSTER_STYLE)
        c.node('Query', '查询分析\n模式检测\n复杂度评估\n任务分类\n测试任务识别', fillcolor='#64B5F6', fontsize='17')
        c.node('PlanData', '计划对象\n- original_query\n- steps: 步骤列表\n- overall_goal\n- complexity\n- feasibility_score\n- current_step\n- test_orchestrator', fillcolor='#0D47A1', fontcolor='white', fontsize='15')
        c.node('StepData', '计划步骤\n- step_number: 编号\n- description: 描述\n- tool_needed: 工具\n- expected_output\n- importance: 重要性\n- completed/success\n- result_summary\n- error_message', fillcolor='#1A237E', fontcolor='white', fontsize='14')

    with dot.subgraph(name='cluster_act_data') as c:
        c.attr(style='filled', color='#E8F5E9', label='【执行数据流】', pencolor='#1B5E20', **CLUSTER_STYLE)
        c.node('Prompt', '增强提示词\n- 系统提示\n- 记忆增强\n- 对话历史\n- 工具定义', fillcolor='#81C784', fontsize='17')
        c.node('LLMReq', 'LLM请求\n- model: 模型\n- max_tokens\n- system: 系统提示\n- messages: 消息\n- tools: 工具定义', fillcolor='#43A047', fontcolor='white', fontsize='15')
        c.node('LLMResp', 'LLM响应\n- 内容块\n- Thinking块\n- 工具调用块', fillcolor='#2E7D32', fontcolor='white', fontsize='15')
        c.node('ToolCall', '工具调用\n- id: 标识\n- name: 工具名\n- input: 参数', fillcolor='#1B5E20', fontcolor='white', fontsize='15')
        c.node('FCData', 'FunctionCall执行\n- Parameters: 参数校验\n- do_call(): 实际执行\n- ExecutionResult\n- call_chain\n- duration_ms: 耗时', fillcolor='#004D40', fontcolor='white', fontsize='14')

    # 测试编排数据流 - 重点优化！
    with dot.subgraph(name='cluster_test_data') as td:
        td.attr(style='filled', color='#A5D6A7', label='【测试编排数据流】', pencolor='#2E7D32', **CLUSTER_STYLE)
        td.node('TOData', '[1] 编排输入\nfile_path, project_name\n流程开关', fillcolor='#43A047', fontcolor='white', fontsize='17')
        td.node('CRData', '[2] 审查结果\nissues: 问题列表\nseverity: 严重程度\ncounts: 统计数据', fillcolor='#66BB6A', fontcolor='white', fontsize='17')
        td.node('AFData', '[3] 修复结果\nbackup_file: 备份\nfixed_issues: 已修复\nunfixed_issues: 未修复\nfix_rate: 修复率', fillcolor='#81C784', fontcolor='white', fontsize='16')
        td.node('TDocData', '[4] 文档生成\ndoc_path: 路径\ntest_cases: 用例\ncoverage: 覆盖率\nquality_score: 评分', fillcolor='#A5D6A7', fontcolor='white', fontsize='16')
        td.node('TGenData', '[5] 代码生成\ntest_path: 路径\nlanguage: 语言\ntests_generated: 数量', fillcolor='#C8E6C9', fontcolor='white', fontsize='16')
        td.node('TRunData', '[6] 测试运行\ncompile_success\nrun_success\npassed/total\npass_rate: 通过率\nerrors: 错误列表', fillcolor='#E8F5E9', fontcolor='white', fontsize='16')

    with dot.subgraph(name='cluster_output') as c:
        c.attr(style='filled', color='#E0F7FA', label='【输出层】', pencolor='#006064', **CLUSTER_STYLE)
        c.node('Output', '最终答案\n格式化展示\n- 自改进报告\n- 完整测试报告\n- 代码修复率统计', fillcolor='#006064', fontcolor='white', fontsize='20')

    # 主连接线
    dot.edge('User', 'Query', color='#E64A19', penwidth='7', **EDGE_STYLE)
    dot.edge('Query', 'PlanData', color='#0D47A1', penwidth='6', **EDGE_STYLE)
    dot.edge('PlanData', 'StepData', color='#0D47A1', penwidth='6', **EDGE_STYLE)
    dot.edge('PlanData', 'Prompt', color='#1B5E20', penwidth='5', **EDGE_STYLE)
    dot.edge('Prompt', 'LLMReq', color='#1B5E20', penwidth='5', **EDGE_STYLE)
    dot.edge('LLMReq', 'LLMResp', color='#1B5E20', penwidth='5', **EDGE_STYLE)
    dot.edge('LLMResp', 'ToolCall', color='#1B5E20', penwidth='5', **EDGE_STYLE)
    dot.edge('ToolCall', 'FCData', color='#004D40', penwidth='5', **EDGE_STYLE)

    # 测试编排数据流 - 优化连线
    dot.edge('ToolCall', 'TOData', color='#2E7D32', penwidth='6', **EDGE_STYLE)
    dot.edge('TOData', 'CRData', color='#2E7D32', penwidth='5', **EDGE_STYLE)
    dot.edge('CRData', 'AFData', color='#2E7D32', penwidth='5', **EDGE_STYLE)
    dot.edge('AFData', 'TDocData', color='#2E7D32', penwidth='5', **EDGE_STYLE)
    dot.edge('TDocData', 'TGenData', color='#2E7D32', penwidth='5', **EDGE_STYLE)
    dot.edge('TGenData', 'TRunData', color='#2E7D32', penwidth='5', **EDGE_STYLE)
    # 测试数据回流到步骤
    dot.edge('TRunData', 'StepData', color='#1B5E20', penwidth='6', **EDGE_STYLE)

    # 最终输出
    dot.edge('StepData', 'Output', color='#006064', penwidth='7', **EDGE_STYLE)
    dot.edge('LLMResp', 'Output', color='#006064', penwidth='6', **EDGE_STYLE)

    dot.render(cleanup=True)
    print("[OK] 完整数据流图 v1.6 (优化版) 已生成")


def create_tool_system_diagram_v16():
    """工具系统架构图 v1.6 - 优化版"""
    dot = Digraph(
        'Tool_System_v1.6',
        filename='./docs/Tool_System_Architecture_v1.6',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='40,32', rankdir='TB', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    # 抽象层
    dot.node('AbsFC', 'AbstractFunctionCall\n泛型基类\n参数校验\n执行追踪\n错误处理',
             fillcolor='#4A148C', fontcolor='white', **HEADER_STYLE)

    dot.node('Base', 'BaseTool 抽象基类\n- name: 工具名称\n- description: 描述\n- parameters: 参数\n- execute(): 执行\n- validate_params()',
             fillcolor='#E65100', fontcolor='white', **HEADER_STYLE)

    # 工具注册表
    dot.node('Registry', '工具注册表\n- tools: 18个工具字典\n- register(): 注册\n- unregister(): 注销\n- execute_tool(): 执行\n- get_tool_descriptions()',
             fillcolor='#3E2723', fontcolor='white', **HEADER_STYLE)

    # 核心工具 - 第一行
    with dot.subgraph(name='cluster_row1') as r1:
        r1.attr(rank='same')
        r1.node('FR', '1. FileReader\n文件读取器', fillcolor='#7B1FA2', fontcolor='white', fontsize='15')
        r1.node('FW', '2. FileWriter\n文件写入器', fillcolor='#7B1FA2', fontcolor='white', fontsize='15')
        r1.node('EC', '3. CommandExecutor\n命令执行器', fillcolor='#7B1FA2', fontcolor='white', fontsize='15')
        r1.node('CS', '4. CodeSearch\n代码搜索器', fillcolor='#7B1FA2', fontcolor='white', fontsize='15')

    # 第二行
    with dot.subgraph(name='cluster_row2') as r2:
        r2.attr(rank='same')
        r2.node('CA', '5. CompilerAnalyzer\n编译分析器', fillcolor='#7B1FA2', fontcolor='white', fontsize='15')
        r2.node('LL', '6. LinkedListTool\n链表操作工具', fillcolor='#7B1FA2', fontcolor='white', fontsize='15')
        r2.node('Git', '7. GitTool\n版本控制工具', fillcolor='#7B1FA2', fontcolor='white', fontsize='15')
        r2.node('SA', '8. StaticAnalyzer\n静态分析器', fillcolor='#7B1FA2', fontcolor='white', fontsize='15')

    # 第三行 - 测试工具核心
    with dot.subgraph(name='cluster_row3') as r3:
        r3.attr(rank='same')
        r3.node('CR', '9. CodeReview\n代码审查', fillcolor='#2E7D32', fontcolor='white', fontsize='15')
        r3.node('TO', '10. TestOrchestrator\n测试编排器', fillcolor='#1B5E20', fontcolor='white', fontsize='15')
        r3.node('AF', '11. AutoFixer\n自动修复器', fillcolor='#2E7D32', fontcolor='white', fontsize='15')
        r3.node('TR', '12. TestRunner\n测试运行器', fillcolor='#2E7D32', fontcolor='white', fontsize='15')

    # 第四行
    with dot.subgraph(name='cluster_row4') as r4:
        r4.attr(rank='same')
        r4.node('TDG', '13. TestDocGenerator\n测试文档生成', fillcolor='#004D40', fontcolor='white', fontsize='15')
        r4.node('TG', '14. TestGenerator\n测试代码生成', fillcolor='#004D40', fontcolor='white', fontsize='15')
        r4.node('SSR', '15. SelfSourceReader\n自源码读取', fillcolor='#AD1457', fontcolor='white', fontsize='15')
        r4.node('SIM', '16. SelfImprove\n自我改进工具', fillcolor='#AD1457', fontcolor='white', fontsize='15')

    # 第五行
    with dot.subgraph(name='cluster_row5') as r5:
        r5.attr(rank='same')
        r5.node('PS', '17. PluginSystem\n插件系统', fillcolor='#AD1457', fontcolor='white', fontsize='15')
        r5.node('CRR', '18. CodeReviewReport\n审查报告生成', fillcolor='#004D40', fontcolor='white', fontsize='15')
        r5.node('ASAN', '19. MsvcAsanCompiler\n内存检测编译', fillcolor='#4A148C', fontcolor='white', fontsize='15')

    # 测试编排核心区
    with dot.subgraph(name='cluster_test_core') as tc:
        tc.attr(style='filled', color='#E8F5E9', label='【测试编排系统核心】', pencolor='#1B5E20', **CLUSTER_STYLE)
        tc.node('TestCore', '五大测试能力支柱\n\n1. 代码审查: CodeReview + CodeReviewReport\n2. 自动修复: AutoFixer 智能修复\n3. 文档生成: TestDocGenerator 结构化\n4. 代码生成: TestGenerator 多语言模板\n5. 测试运行: TestRunner MSVC/GCC双支持\n\n统一编排: TestOrchestrator 一站式流程',
                fillcolor='#1B5E20', fontcolor='white', fontsize='17')

    # 消费者
    dot.node('AE', '代理引擎\nMVP模式', fillcolor='#1B5E20', fontcolor='white', fontsize='22')
    dot.node('LLM', 'Claude大语言模型\nJSON Schema工具定义\n18个工具自动发现', fillcolor='#004D40', fontcolor='white', fontsize='18')

    # 连接线
    dot.edge('AbsFC', 'Base', color='#E65100', penwidth='6', **EDGE_STYLE)
    # 所有工具连接
    for t in ['FR', 'FW', 'EC', 'CS', 'CA', 'LL', 'Git', 'SA', 'CR', 'ASAN', 'SSR', 'SIM', 'PS', 'TO', 'CRR', 'AF', 'TDG', 'TG', 'TR']:
        dot.edge('Base', t, color='#4A148C', penwidth='4', **EDGE_STYLE)

    # 核心区连接
    dot.edge('TO', 'TestCore', color='#1B5E20', penwidth='6', **EDGE_STYLE)
    dot.edge('CR', 'TestCore', color='#1B5E20', penwidth='4', **EDGE_STYLE)
    dot.edge('AF', 'TestCore', color='#1B5E20', penwidth='4', **EDGE_STYLE)
    dot.edge('TDG', 'TestCore', color='#1B5E20', penwidth='4', **EDGE_STYLE)
    dot.edge('TG', 'TestCore', color='#1B5E20', penwidth='4', **EDGE_STYLE)
    dot.edge('TR', 'TestCore', color='#1B5E20', penwidth='4', **EDGE_STYLE)

    # 注册表连接
    dot.edge('TestCore', 'Registry', color='#3E2723', penwidth='6', **EDGE_STYLE)

    # 结果连接
    dot.edge('Registry', 'AE', color='#1B5E20', penwidth='7', **EDGE_STYLE)
    dot.edge('AE', 'Registry', color='#3E2723', penwidth='6', **EDGE_STYLE)
    dot.edge('Registry', 'LLM', color='#004D40', penwidth='5', **EDGE_STYLE)
    dot.edge('LLM', 'AE', color='#004D40', penwidth='5', **EDGE_STYLE)

    dot.render(cleanup=True)
    print("[OK] 工具系统架构图 v1.6 (优化版) 已生成")


def create_plan_act_reflect_flowchart_v16():
    """执行流程图 v1.6 - 优化版"""
    dot = Digraph(
        'Plan_Act_Reflect_v1.6',
        filename='./docs/Plan_Act_Reflect_Flowchart_v1.6',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='38,34', rankdir='TB', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    dot.node('Start', '开始\n接收用户查询\n"review code test run"', fillcolor='#1B5E20', fontcolor='white', fontsize='24')

    with dot.subgraph(name='cluster_plan') as c:
        c.attr(style='filled', color='#E3F2FD', label='【规划阶段】', pencolor='#1565C0', **CLUSTER_STYLE)
        c.node('P1', '是否简单任务?\n检测: test/修复/审查\norchestrator关键词', shape='diamond', fillcolor='#FFC107', fontsize='20', penwidth='6')
        c.node('P2', '生成简单计划', fillcolor='#64B5F6', fontsize='18')
        c.node('P3', '启发式任务分解\n分析任务类型\n测试任务识别', fillcolor='#64B5F6', fontsize='18')
        c.node('P4', '可行性评估\n危险操作检测\n步骤连续检查\n目标清晰性', fillcolor='#64B5F6', fontsize='18')
        c.node('P5', '计划可行?', shape='diamond', fillcolor='#FFC107', fontsize='20', penwidth='6')
        c.node('P6', '返回错误', fillcolor='#C62828', fontcolor='white', fontsize='18')

    with dot.subgraph(name='cluster_act') as c:
        c.attr(style='filled', color='#E8F5E9', label='【执行阶段】', pencolor='#1B5E20', **CLUSTER_STYLE)
        c.node('A1', '初始化计数器=0', fillcolor='#81C784', fontsize='18')
        c.node('A2', '获取当前步骤\n+对话历史', fillcolor='#81C784', fontsize='18')
        c.node('A3', '构建增强提示词\n记忆增强\n对话历史\n工具定义', fillcolor='#81C784', fontsize='18')
        c.node('A4', '调用大模型API', fillcolor='#81C784', fontsize='18')
        c.node('A5', '有工具调用?', shape='diamond', fillcolor='#FFC107', fontsize='20', penwidth='6')
        c.node('A6', '执行工具\n通过注册表\nFunctionCall', fillcolor='#81C784', fontsize='18')
        c.node('A7', '执行成功?', shape='diamond', fillcolor='#FFC107', fontsize='20', penwidth='6')
        c.node('A8', '收集执行结果', fillcolor='#81C784', fontsize='18')
        c.node('A9', '标记步骤完成', fillcolor='#81C784', fontsize='18')
        c.node('A10', '本步完成?', shape='diamond', fillcolor='#FFC107', fontsize='20', penwidth='6')

        # 新增: 测试编排快捷分支
        c.node('AT1', '是测试编排任务?', shape='diamond', fillcolor='#004D40', fontcolor='white', fontsize='18', penwidth='6')
        c.node('AT2', '直接执行 TestOrchestrator\n跳过LLM调用\n直接提取文件名\n创建项目目录\n执行6步完整流程', fillcolor='#2E7D32', fontcolor='white', fontsize='17')

    with dot.subgraph(name='cluster_reflect') as c:
        c.attr(style='filled', color='#FFF8E1', label='【反思阶段】', pencolor='#FF8F00', **CLUSTER_STYLE)
        c.node('R1', '分析执行结果\n含测试执行结果', fillcolor='#FFB74D', fontsize='18')
        c.node('R2', '错误模式匹配\n文件不存在\n权限不足\n超时\n语法错误\n编译失败\n测试失败', fillcolor='#FFB74D', fontsize='17')
        c.node('R3', '提取经验教训\n测试最佳实践', fillcolor='#FFB74D', fontsize='18')
        c.node('R4', '持久化到记忆\n测试记忆库', fillcolor='#FFB74D', fontsize='18')
        c.node('R5', '需要调整计划?', shape='diamond', fillcolor='#FFC107', fontsize='20', penwidth='6')
        c.node('R6', '插入新步骤\n或修改计划\n修复编译问题', fillcolor='#FFB74D', fontsize='18')
        c.node('R7', '计数器+1', fillcolor='#FFB74D', fontsize='18')

    with dot.subgraph(name='cluster_finalize') as c:
        c.attr(style='filled', color='#F3E5F5', label='【终态阶段】', pencolor='#4A148C', **CLUSTER_STYLE)
        c.node('F1', '全部完成?\n或达最大迭代?', shape='diamond', fillcolor='#FFC107', fontsize='20', penwidth='6')
        c.node('F2', '生成执行总结\n步骤数/成功率/详情\n含自改进记录\n含测试通过率', fillcolor='#AB47BC', fontcolor='white', fontsize='18')
        c.node('F3', '生成最终答案\n通过大模型\n含测试报告', fillcolor='#BA68C8', fontcolor='white', fontsize='18')
        c.node('F4', '执行完成\n返回结果\n含完整测试报告\n修复率+通过率', fillcolor='#4A148C', fontcolor='white', fontsize='24')

    # 主流程线
    dot.edge('Start', 'P1', color='#1B5E20', penwidth='7', **EDGE_STYLE)
    dot.edge('P5', 'A1', color='#0D47A1', penwidth='5', **EDGE_STYLE)
    dot.edge('A1', 'A2', color='#1B5E20', penwidth='4', **EDGE_STYLE)
    dot.edge('A2', 'A3', color='#1B5E20', penwidth='4', **EDGE_STYLE)
    dot.edge('A3', 'A4', color='#1B5E20', penwidth='4', **EDGE_STYLE)
    dot.edge('A4', 'A5', color='#1B5E20', penwidth='4', **EDGE_STYLE)
    dot.edge('A5', 'A10', color='#1B5E20', label='否', **EDGE_STYLE)
    dot.edge('A5', 'A6', color='#1B5E20', label='是', **EDGE_STYLE)
    dot.edge('A6', 'A7', color='#1B5E20', penwidth='4', **EDGE_STYLE)
    dot.edge('A7', 'A8', color='#1B5E20', label='成功', **EDGE_STYLE)
    dot.edge('A8', 'A9', color='#1B5E20', penwidth='4', **EDGE_STYLE)
    dot.edge('A9', 'AT1', color='#1B5E20', penwidth='4', **EDGE_STYLE)

    # 测试编排快捷路径
    dot.edge('AT1', 'AT2', color='#004D40', penwidth='6', label='是 - 直接执行', **EDGE_STYLE)
    dot.edge('AT1', 'R1', color='#FF8F00', penwidth='4', label='否', **EDGE_STYLE)
    dot.edge('AT2', 'R1', color='#004D40', penwidth='6', **EDGE_STYLE)

    # 失败重试
    dot.edge('A7', 'A2', color='#C62828', style='dashed', label='失败 重试', **EDGE_STYLE)
    dot.edge('A10', 'R1', color='#FF8F00', penwidth='5', **EDGE_STYLE)

    # 反思流程
    dot.edge('R1', 'R2', color='#FF8F00', penwidth='4', **EDGE_STYLE)
    dot.edge('R2', 'R3', color='#FF8F00', penwidth='4', **EDGE_STYLE)
    dot.edge('R3', 'R4', color='#FF8F00', penwidth='4', **EDGE_STYLE)
    dot.edge('R4', 'R5', color='#FF8F00', penwidth='4', **EDGE_STYLE)
    dot.edge('R5', 'R6', color='#C62828', penwidth='4', label='是', **EDGE_STYLE)
    dot.edge('R5', 'R7', color='#FF8F00', penwidth='4', label='否', **EDGE_STYLE)
    dot.edge('R6', 'R7', color='#FF8F00', penwidth='4', **EDGE_STYLE)
    dot.edge('R7', 'F1', color='#4A148C', penwidth='5', **EDGE_STYLE)
    dot.edge('F1', 'A2', color='#0D47A1', style='dashed', label='未完成', **EDGE_STYLE)
    dot.edge('F1', 'F2', color='#4A148C', penwidth='5', label='完成', **EDGE_STYLE)
    dot.edge('F2', 'F3', color='#4A148C', penwidth='5', **EDGE_STYLE)
    dot.edge('F3', 'F4', color='#4A148C', penwidth='7', **EDGE_STYLE)

    dot.render(cleanup=True)
    print("[OK] 执行流程图 v1.6 (优化版) 已生成")


if __name__ == '__main__':
    print("=" * 90)
    print("DevPal Agent v1.6 - 架构图生成器 (优化版)")
    print("=" * 90)
    print("优化内容:")
    print("  1. 大幅提升字体大小 (节点字体18px, 标题22px")
    print("  2. 增大节点间距和行间距 (更宽敞布局")
    print("  3. 优化颜色对比度 (更深更清晰")
    print("  4. 测试编排数据流部分重点优化:")
    print("     - 使用数字序号标记")
    print("     - 简化节点内容,减少换行")
    print("     - 增大字体到16-17px")
    print("     - 优化连线粗细")
    print("  5. 所有架构图统一优化风格")
    print("=" * 90)

    create_architecture_overview_v16()
    create_test_orchestrator_architecture_v16()
    create_tool_system_diagram_v16()
    create_plan_act_reflect_flowchart_v16()
    create_data_flow_diagram_v16()

    print("=" * 90)
    print("所有架构图已成功生成到 ./docs/ 目录!")
    print("=" * 90)
    print("\n生成的文件列表 (v1.6 优化版):")
    print("  1. DevPal_Architecture_Overview_v1.6.png")
    print("  2. Test_Orchestrator_System_Architecture_v1.6.png")
    print("  3. Tool_System_Architecture_v1.6.png")
    print("  4. Plan_Act_Reflect_Flowchart_v1.6.png")
    print("  5. Complete_Data_Flow_v1.6.png  <<< 测试编排数据流已优化")
    print("\n字体: 微软雅黑 Microsoft YaHei")
    print("分辨率: 600 DPI 超高清")
    print("字体大小: 节点16-24px, 大幅提升可读性")
