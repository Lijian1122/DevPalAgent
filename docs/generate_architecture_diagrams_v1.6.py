# -*- coding: utf-8 -*-
"""
DevPal Agent v1.6 - 架构图生成器
更新内容：阶段6 - 自动化测试编排系统
新增: TestOrchestrator + 5个测试相关工具 (共18个工具)
  - TestOrchestratorTool: 一站式测试编排
  - CodeReviewReportTool: 代码审查报告
  - AutoFixerTool: 自动修复bug
  - TestDocGeneratorTool: 测试文档生成
  - TestGeneratorTool: 测试代码生成
  - TestRunnerTool: 增强MSVC编译器支持
"""
from graphviz import Digraph
import os

os.makedirs('./docs', exist_ok=True)

# 全局设置
GRAPH_STYLE = {
    'fontname': 'Microsoft YaHei',
    'fontpath': 'C:/Windows/Fonts/msyh.ttc',
    'fontsize': '16',
    'dpi': '600',
    'nodesep': '1.2',
    'ranksep': '1.5',
    'charset': 'utf8',
}

NODE_STYLE = {
    'fontname': 'Microsoft YaHei',
    'fontsize': '15',
    'shape': 'box',
    'style': 'filled,rounded',
    'penwidth': '4',
}

HEADER_STYLE = {
    'fontname': 'Microsoft YaHei',
    'fontsize': '20',
    'style': 'filled,bold',
    'penwidth': '5',
}

CLUSTER_STYLE = {
    'fontname': 'Microsoft YaHei',
    'fontsize': '22',
    'penwidth': '5',
}

EDGE_STYLE = {
    'fontname': 'Microsoft YaHei',
    'fontsize': '14',
}


def create_architecture_overview_v16():
    """系统整体架构图 v1.6 - 新增测试编排系统层"""
    dot = Digraph(
        'DevPal_Architecture_v1.6',
        filename='./docs/DevPal_Architecture_Overview_v1.6',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='36,30', rankdir='TB', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    # 用户层
    with dot.subgraph(name='cluster_user') as c:
        c.attr(style='filled', color='#FFF3E0', label='【用户层】', **CLUSTER_STYLE)
        c.node('User', '用户\n输入查询\n"review code test run"', fillcolor='#E64A19', fontcolor='white', fontsize='20')
        c.node('CLI', '命令行\n交互式模式\n--test 快捷入口', fillcolor='#FF5722', fontcolor='white', fontsize='18')
        c.node('Web', 'Web界面\n多标签工具\n测试面板', fillcolor='#FF7043', fontcolor='white', fontsize='18')

    # 核心引擎层
    with dot.subgraph(name='cluster_core') as c:
        c.attr(style='filled', color='#E3F2FD', label='【核心引擎层】', **CLUSTER_STYLE)
        c.node('Engine', '代理引擎\n主执行循环\n多工具编排', fillcolor='#0D47A1', fontcolor='white', **HEADER_STYLE)

        with c.subgraph(name='cluster_planner') as pc:
            pc.attr(style='filled', color='#BBDEFB', label='规划模块', fontsize='18')
            pc.node('PlanGen', '计划生成\n启发式/LLM\n测试任务识别', fillcolor='#42A5F5', fontsize='16')
            pc.node('Feasibility', '可行性评估\n危险检测\n参数校验', fillcolor='#42A5F5', fontsize='16')
            pc.node('PlanAdjust', '计划调整\n动态修改\n结果反馈', fillcolor='#42A5F5', fontsize='16')

        with c.subgraph(name='cluster_reflector') as rc:
            rc.attr(style='filled', color='#C8E6C9', label='反思模块', fontsize='18')
            rc.node('Reflection', '执行反思\n结果分析\n测试评估', fillcolor='#2E7D32', fontcolor='white', fontsize='16')
            rc.node('PatternMatch', '模式匹配\n错误检测\n编译失败分析', fillcolor='#2E7D32', fontcolor='white', fontsize='16')
            rc.node('Lessons', '经验提取\n总结学习\n测试优化建议', fillcolor='#2E7D32', fontcolor='white', fontsize='16')

    # 记忆层
    with dot.subgraph(name='cluster_memory') as c:
        c.attr(style='filled', color='#FFF8E1', label='【记忆系统层】', **CLUSTER_STYLE)
        c.node('MM', '记忆管理器\n统一入口\n测试记忆', fillcolor='#E65100', fontcolor='white', **HEADER_STYLE)
        c.node('STM', '短期记忆\n对话上下文\n滑动窗口', fillcolor='#FFCA28', fontsize='14')
        c.node('LTM', '长期记忆\n用户偏好\n任务经验\n测试最佳实践', fillcolor='#FFA000', fontsize='14')
        c.node('EM', '错误记忆\n模式跟踪\n修正建议\n编译错误库', fillcolor='#FF6F00', fontcolor='white', fontsize='14')

    # 测试编排系统层 - 阶段6新增核心
    with dot.subgraph(name='cluster_test_orchestrator') as tc:
        tc.attr(style='filled', color='#E8F5E9', label='【测试编排系统层】', pencolor='#1B5E20', **CLUSTER_STYLE)
        tc.node('TestOrch', 'TestOrchestrator\n一站式测试编排\n6步自动化流程', fillcolor='#1B5E20', fontcolor='white', **HEADER_STYLE)
        with tc.subgraph(name='cluster_test_steps') as ts:
            ts.attr(rank='same')
            ts.node('TS1', '代码审查\nCodeReview\n多语言支持', fillcolor='#2E7D32', fontcolor='white', fontsize='13')
            ts.node('TS2', '自动修复\nAutoFixer\n智能修复bug', fillcolor='#2E7D32', fontcolor='white', fontsize='13')
            ts.node('TS3', '测试文档\nTestDocGenerator\n结构化输出', fillcolor='#2E7D32', fontcolor='white', fontsize='13')
        with tc.subgraph(name='cluster_test_steps2') as ts2:
            ts2.attr(rank='same')
            ts2.node('TS4', '代码生成\nTestGenerator\n多语言适配', fillcolor='#2E7D32', fontcolor='white', fontsize='13')
            ts2.node('TS5', '测试运行\nTestRunner\nMSVC/GCC双支持', fillcolor='#2E7D32', fontcolor='white', fontsize='13')
            ts2.node('TS6', '结果更新\nUpdateDoc\nMarkdown报告', fillcolor='#2E7D32', fontcolor='white', fontsize='13')
        tc.node('TS0', '统一输出目录:\nProjectName/\n  - source_backup.cpp\n  - review_report.md\n  - test_doc.md\n  - test_code.cpp', fillcolor='#004D40', fontcolor='white', fontsize='13')

    # 自我改进层 - 阶段5新增
    with dot.subgraph(name='cluster_self_improve') as c:
        c.attr(style='filled', color='#FFEBEE', label='【自我改进层】', pencolor='#C62828', **CLUSTER_STYLE)
        c.node('SelfImprove', '自我改进系统\n代码自修复\n工具内省', fillcolor='#C62828', fontcolor='white', **HEADER_STYLE)
        with c.subgraph(name='cluster_self_tools') as st:
            st.attr(rank='same')
            st.node('SSR', 'SelfSourceReader\n读取自身源码\nAST分析\n结构获取', fillcolor='#D32F2F', fontcolor='white', fontsize='13')
            st.node('SIM', 'SelfImproveTool\n备份恢复\n问题分析\n代码修复\n自检', fillcolor='#D32F2F', fontcolor='white', fontsize='13')
            st.node('PS', 'PluginSystem\n插件加载/卸载\n模板生成\n动态扩展', fillcolor='#D32F2F', fontcolor='white', fontsize='13')

    # 工具层 - 扩展到18个工具
    with dot.subgraph(name='cluster_tools') as c:
        c.attr(style='filled', color='#F3E5F5', label='【工具系统层】(共18个工具)', **CLUSTER_STYLE)
        c.node('ToolReg', '工具注册表\n统一调度\n18个工具', fillcolor='#4A148C', fontcolor='white', **HEADER_STYLE)

        # FunctionCall 抽象层
        with c.subgraph(name='cluster_func_call') as fc:
            fc.attr(style='filled', color='#E1BEE7', label='抽象FunctionCall层', fontsize='18')
            fc.node('AbsFC', 'AbstractFunctionCall\n泛型基类\n参数校验\n执行追踪\n错误处理', fillcolor='#7B1FA2', fontcolor='white', fontsize='15')
            fc.node('FCtx', 'FunctionCallContext\n调用链\n变量存储\n计时统计', fillcolor='#8E24AA', fontcolor='white', fontsize='14')
            fc.node('FChain', 'FunctionChain\n链式执行\n结果传递\n参数合并', fillcolor='#9C27B0', fontcolor='white', fontsize='14')
            fc.node('ExecRes', 'ExecutionResult\nsuccess/data\nerror/duration\nmetadata', fillcolor='#BA68C8', fontcolor='white', fontsize='13')

        # 具体工具 - 18个分4行
        with c.subgraph(name='cluster_row1') as r1:
            r1.attr(rank='same')
            r1.node('FR', '1.文件读取', fillcolor='#6A1B9A', fontcolor='white', fontsize='12')
            r1.node('FW', '2.文件写入', fillcolor='#6A1B9A', fontcolor='white', fontsize='12')
            r1.node('EC', '3.命令执行', fillcolor='#6A1B9A', fontcolor='white', fontsize='12')
            r1.node('CS', '4.代码搜索', fillcolor='#6A1B9A', fontcolor='white', fontsize='12')
        with c.subgraph(name='cluster_row2') as r2:
            r2.attr(rank='same')
            r2.node('CA', '5.编译分析', fillcolor='#6A1B9A', fontcolor='white', fontsize='12')
            r2.node('LL', '6.链表工具', fillcolor='#6A1B9A', fontcolor='white', fontsize='12')
            r2.node('Git', '7.Git工具', fillcolor='#6A1B9A', fontcolor='white', fontsize='12')
            r2.node('SA', '8.静态分析', fillcolor='#6A1B9A', fontcolor='white', fontsize='12')
        with c.subgraph(name='cluster_row3') as r3:
            r3.attr(rank='same')
            r3.node('CR', '9.代码审查', fillcolor='#4A148C', fontcolor='white', fontsize='12')
            r3.node('ASAN', '10.MSVC ASAN', fillcolor='#4A148C', fontcolor='white', fontsize='12')
            r3.node('SSR2', '11.自源码读取', fillcolor='#AD1457', fontcolor='white', fontsize='12')
            r3.node('SIM2', '12.自我改进', fillcolor='#AD1457', fontcolor='white', fontsize='12')
        with c.subgraph(name='cluster_row4') as r4:
            r4.attr(rank='same')
            r4.node('PS2', '13.插件系统', fillcolor='#AD1457', fontcolor='white', fontsize='12')
            r4.node('TO', '14.测试编排', fillcolor='#1B5E20', fontcolor='white', fontsize='12')
            r4.node('TG', '15.测试代码生成', fillcolor='#1B5E20', fontcolor='white', fontsize='12')
            r4.node('TR', '16.测试运行器', fillcolor='#1B5E20', fontcolor='white', fontsize='12')
        with c.subgraph(name='cluster_row5') as r5:
            r5.attr(rank='same')
            r5.node('TD', '17.测试文档生成', fillcolor='#1B5E20', fontcolor='white', fontsize='12')
            r5.node('CRR', '18.审查报告生成', fillcolor='#1B5E20', fontcolor='white', fontsize='12')

    # LLM层
    with dot.subgraph(name='cluster_llm') as c:
        c.attr(style='filled', color='#E0F7FA', label='【大模型层】', **CLUSTER_STYLE)
        c.node('LLM', 'Claude大模型\n兼容火山引擎\nThinking支持\n测试指令理解', fillcolor='#006064', fontcolor='white', fontsize='17')

    # 输出层 - 测试产物
    with dot.subgraph(name='cluster_output') as c:
        c.attr(style='filled', color='#FFF8E1', label='【输出产物】', pencolor='#E65100', **CLUSTER_STYLE)
        c.node('TestOut', '测试输出目录\n统一项目结构\n可复现测试环境', fillcolor='#E65100', fontcolor='white', fontsize='14')
        c.node('Out1', 'source_backup.cpp\n修复前源代码备份', fillcolor='#FFA000', fontcolor='white', fontsize='12')
        c.node('Out2', 'review_report.md\n代码审查详细报告', fillcolor='#FFA000', fontcolor='white', fontsize='12')
        c.node('Out3', 'test_doc.md\n测试文档+执行结果', fillcolor='#FFA000', fontcolor='white', fontsize='12')
        c.node('Out4', 'test_code.cpp\n生成的测试代码', fillcolor='#FFA000', fontcolor='white', fontsize='12')

    # 插件目录 - 外部扩展
    with dot.subgraph(name='cluster_plugins') as c:
        c.attr(style='filled', color='#F1F8E9', label='【插件目录】', pencolor='#558B2F', **CLUSTER_STYLE)
        c.node('PluginDir', './plugins/\n第三方插件\n动态加载', fillcolor='#558B2F', fontcolor='white', fontsize='14')
        c.node('BackupDir', './.devpal_backups/\n代码快照\n安全回滚', fillcolor='#689F38', fontcolor='white', fontsize='14')

    # 连接线 - 主流程
    dot.edge('User', 'CLI', color='#E64A19', **EDGE_STYLE)
    dot.edge('User', 'Web', color='#E64A19', **EDGE_STYLE)
    dot.edge('CLI', 'Engine', color='#E64A19', **EDGE_STYLE)
    dot.edge('Web', 'Engine', color='#E64A19', **EDGE_STYLE)
    dot.edge('Engine', 'PlanGen', color='#1565C0', **EDGE_STYLE)
    dot.edge('PlanGen', 'Feasibility', color='#1565C0', **EDGE_STYLE)
    dot.edge('Feasibility', 'PlanAdjust', color='#1565C0', **EDGE_STYLE)
    dot.edge('PlanAdjust', 'Engine', color='#1565C0', **EDGE_STYLE)
    dot.edge('Engine', 'MM', color='#F57C00', **EDGE_STYLE)
    dot.edge('MM', 'STM', color='#F57C00', **EDGE_STYLE)
    dot.edge('MM', 'LTM', color='#F57C00', **EDGE_STYLE)
    dot.edge('MM', 'EM', color='#F57C00', **EDGE_STYLE)
    dot.edge('Lessons', 'LTM', color='#2E7D32', style='dashed', **EDGE_STYLE)
    dot.edge('Lessons', 'EM', color='#2E7D32', style='dashed', **EDGE_STYLE)

    # 测试编排系统连接
    dot.edge('Engine', 'TestOrch', color='#1B5E20', penwidth='6', **EDGE_STYLE)
    dot.edge('TestOrch', 'TS1', color='#1B5E20', **EDGE_STYLE)
    dot.edge('TestOrch', 'TS2', color='#1B5E20', **EDGE_STYLE)
    dot.edge('TestOrch', 'TS3', color='#1B5E20', **EDGE_STYLE)
    dot.edge('TestOrch', 'TS4', color='#1B5E20', **EDGE_STYLE)
    dot.edge('TestOrch', 'TS5', color='#1B5E20', **EDGE_STYLE)
    dot.edge('TestOrch', 'TS6', color='#1B5E20', **EDGE_STYLE)
    dot.edge('TestOrch', 'TS0', color='#004D40', style='dashed', **EDGE_STYLE)
    dot.edge('TS0', 'TestOut', color='#E65100', **EDGE_STYLE)
    dot.edge('TestOut', 'Out1', color='#FFA000', **EDGE_STYLE)
    dot.edge('TestOut', 'Out2', color='#FFA000', **EDGE_STYLE)
    dot.edge('TestOut', 'Out3', color='#FFA000', **EDGE_STYLE)
    dot.edge('TestOut', 'Out4', color='#FFA000', **EDGE_STYLE)

    # 自我改进层连接
    dot.edge('Engine', 'SelfImprove', color='#C62828', penwidth='5', **EDGE_STYLE)
    dot.edge('SelfImprove', 'SSR', color='#C62828', **EDGE_STYLE)
    dot.edge('SelfImprove', 'SIM', color='#C62828', **EDGE_STYLE)
    dot.edge('SelfImprove', 'PS', color='#C62828', **EDGE_STYLE)
    dot.edge('PS', 'PluginDir', color='#558B2F', style='dashed', **EDGE_STYLE)
    dot.edge('SIM', 'BackupDir', color='#558B2F', style='dashed', **EDGE_STYLE)

    # 工具系统连接
    dot.edge('Engine', 'ToolReg', color='#7B1FA2', penwidth='5', **EDGE_STYLE)
    dot.edge('ToolReg', 'AbsFC', color='#7B1FA2', **EDGE_STYLE)
    dot.edge('AbsFC', 'FCtx', color='#7B1FA2', **EDGE_STYLE)
    dot.edge('AbsFC', 'FChain', color='#7B1FA2', **EDGE_STYLE)
    dot.edge('AbsFC', 'ExecRes', color='#7B1FA2', **EDGE_STYLE)
    # 18个工具连接（简化显示）
    for t in ['FR', 'FW', 'EC', 'CS', 'CA', 'LL', 'Git', 'SA', 'CR', 'ASAN']:
        dot.edge('AbsFC', t, color='#7B1FA2', **EDGE_STYLE)

    # 反思
    dot.edge('Engine', 'Reflection', color='#2E7D32', **EDGE_STYLE)
    dot.edge('Reflection', 'PatternMatch', color='#2E7D32', **EDGE_STYLE)
    dot.edge('PatternMatch', 'Lessons', color='#2E7D32', **EDGE_STYLE)
    dot.edge('Reflection', 'PlanAdjust', color='#2E7D32', style='dashed', **EDGE_STYLE)
    dot.edge('Engine', 'LLM', color='#006064', **EDGE_STYLE)
    dot.edge('LLM', 'Engine', color='#006064', **EDGE_STYLE)
    dot.edge('Engine', 'CLI', color='#1B5E20', penwidth='6', **EDGE_STYLE)
    dot.edge('Engine', 'Web', color='#1B5E20', penwidth='6', **EDGE_STYLE)

    dot.render(cleanup=True)
    print("[OK] 系统整体架构图 v1.6 已生成")


def create_test_orchestrator_architecture_v16():
    """新增: 测试编排系统架构图 v1.6 - 阶段6核心"""
    dot = Digraph(
        'Test_Orchestrator_Architecture_v1.6',
        filename='./docs/Test_Orchestrator_System_Architecture_v1.6',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='34,30', rankdir='TB', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    # 触发入口
    with dot.subgraph(name='cluster_trigger') as c:
        c.attr(style='filled', color='#E3F2FD', label='【触发入口】', pencolor='#0D47A1', **CLUSTER_STYLE)
        c.node('Trigger', '用户查询触发\n"review code test run"\nPlanner自动识别测试任务\nAgentEngine直接执行', fillcolor='#0D47A1', fontcolor='white', fontsize='16')

    # 核心编排器
    with dot.subgraph(name='cluster_orchestrator') as c:
        c.attr(style='filled', color='#E8F5E9', label='【TestOrchestrator - 核心编排器】', pencolor='#1B5E20', **CLUSTER_STYLE)
        c.node('Orch', 'TestOrchestratorTool\nname: test_orchestrator\n一站式自动化测试编排\n6步闭环流程', fillcolor='#1B5E20', fontcolor='white', **HEADER_STYLE)

        # 核心参数
        with c.subgraph(name='cluster_params') as p:
            p.attr(style='filled', color='#A5D6A7', label='参数配置', fontsize='16')
            p.node('P1', 'file_path: 源文件路径\n支持: C/C++/Python/JS', fillcolor='#43A047', fontcolor='white', fontsize='13')
            p.node('P2', 'project_name: 项目名称\n自动创建输出目录', fillcolor='#43A047', fontcolor='white', fontsize='13')
            p.node('P3', '6个流程开关\n可单独启用/禁用', fillcolor='#43A047', fontcolor='white', fontsize='13')

    # 6步执行流程
    with dot.subgraph(name='cluster_steps') as c:
        c.attr(style='filled', color='#C8E6C9', label='【6步自动化执行流程】', pencolor='#2E7D32', **CLUSTER_STYLE)

        # 第1-3步
        with c.subgraph(name='cluster_row1') as r1:
            r1.attr(rank='same')
            r1.node('S1', '步骤1: 代码审查\nCodeReview\n检测: TODO/调试代码\n魔法数字/空except\n安全问题/命名规范\n输出结构化issues', fillcolor='#2E7D32', fontcolor='white', fontsize='12')
            r1.node('S2', '步骤2: 生成审查报告\nCodeReviewReport\n详细Markdown报告\nissue统计+位置\n问题分类+严重性\n修复建议列表', fillcolor='#2E7D32', fontcolor='white', fontsize='12')
            r1.node('S3', '步骤3: 自动修复\nAutoFixer\n修复常见问题\n创建备份文件\n标记已修复issues\n修复率统计', fillcolor='#2E7D32', fontcolor='white', fontsize='12')

        # 第4-6步
        with c.subgraph(name='cluster_row2') as r2:
            r2.attr(rank='same')
            r2.node('S4', '步骤4: 生成测试文档\nTestDocGenerator\n分析代码结构\n提取类/函数/方法\n生成测试策略文档\n边界条件分析\n测试覆盖率规划', fillcolor='#004D40', fontcolor='white', fontsize='12')
            r2.node('S5', '步骤5: 生成测试代码\nTestGenerator\n多语言模板\nC++ #include 模式\nPython import 模式\nMain函数测试框架\n断言验证模板', fillcolor='#004D40', fontcolor='white', fontsize='12')
            r2.node('S6', '步骤6: 运行测试+更新文档\nTestRunner\nMSVC/GCC双支持\n编译+执行\n解析测试结果\n更新到文档\n通过率统计', fillcolor='#004D40', fontcolor='white', fontsize='12')

    # 增强的 TestRunner 细节
    with dot.subgraph(name='cluster_test_runner') as c:
        c.attr(style='filled', color='#E1BEE7', label='【增强: TestRunner 编译器支持】', pencolor='#7B1FA2', **CLUSTER_STYLE)
        c.node('TR', 'TestRunnerTool 核心增强\nWindows MSVC 编译器检测\nVS2019/VS2022 Build Tools', fillcolor='#7B1FA2', fontcolor='white', fontsize='16')

        with c.subgraph(name='cluster_detect') as d:
            d.attr(rank='same')
            d.node('TR1', 'vswhere.exe探测\n"Microsoft.VisualStudio.Component.VC.Tools.x86.x64"', fillcolor='#9C27B0', fontcolor='white', fontsize='12')
            d.node('TR2', '已知路径扫描\n%ProgramFiles(x86)%/Microsoft Visual Studio\n%ProgramFiles%/Microsoft Visual Studio', fillcolor='#9C27B0', fontcolor='white', fontsize='12')
            d.node('TR3', 'cl.exe 直接执行\nPATH环境变量检查', fillcolor='#9C27B0', fontcolor='white', fontsize='12')

        with c.subgraph(name='cluster_env') as e:
            e.attr(rank='same')
            e.node('TR4', 'INCLUDE环境设置\nMSVC headers + ATL/MFC\nWindows SDK 路径', fillcolor='#BA68C8', fontcolor='white', fontsize='12')
            e.node('TR5', 'LIB环境设置\nx86/x64 库目录\n自动架构识别', fillcolor='#BA68C8', fontcolor='white', fontsize='12')
            e.node('TR6', '编译参数\n/FSANITIZE=address /Zi /Od\n/EHsc /MDd + include路径', fillcolor='#BA68C8', fontcolor='white', fontsize='12')

    # 输出产物
    with dot.subgraph(name='cluster_output') as c:
        c.attr(style='filled', color='#FFF8E1', label='【输出产物】', pencolor='#E65100', **CLUSTER_STYLE)
        c.node('Out', '统一输出目录结构\nproject_name/', fillcolor='#E65100', fontcolor='white', fontsize='16')
        with c.subgraph(name='cluster_files') as f:
            f.attr(rank='same')
            f.node('F1', 'source_backup.cpp\n修复前源代码\n可对比验证', fillcolor='#FFA000', fontcolor='white', fontsize='13')
            f.node('F2', 'code_review.md\n完整审查报告\n问题+修复建议', fillcolor='#FFA000', fontcolor='white', fontsize='13')
            f.node('F3', 'test_document.md\n测试文档 + 执行结果\n通过率统计', fillcolor='#FFA000', fontcolor='white', fontsize='13')
            f.node('F4', 'test_code.cpp\n可编译测试代码\nMain函数框架', fillcolor='#FFA000', fontcolor='white', fontsize='13')

    # 结果统计
    with dot.subgraph(name='cluster_stats') as c:
        c.attr(style='filled', color='#FFEBEE', label='【统计与反馈】', pencolor='#C62828', **CLUSTER_STYLE)
        c.node('Stats', '执行统计与闭环反馈', fillcolor='#C62828', fontcolor='white', fontsize='16')
        with c.subgraph(name='cluster_stats_items') as si:
            si.attr(rank='same')
            si.node('ST1', '修复率统计\n按严重性分类\n警告/错误/信息', fillcolor='#EF5350', fontcolor='white', fontsize='12')
            si.node('ST2', '未修复问题详情\n含具体修复建议\n开发者可手动修复', fillcolor='#EF5350', fontcolor='white', fontsize='12')
            si.node('ST3', '测试执行摘要\n编译状态\n运行状态\n通过率统计', fillcolor='#EF5350', fontcolor='white', fontsize='12')

    # 流程连接线 - 主流程
    dot.edge('Trigger', 'Orch', color='#1B5E20', penwidth='7', **EDGE_STYLE)
    dot.edge('Orch', 'P1', color='#1B5E20', **EDGE_STYLE)
    dot.edge('Orch', 'P2', color='#1B5E20', **EDGE_STYLE)
    dot.edge('Orch', 'P3', color='#1B5E20', **EDGE_STYLE)
    dot.edge('Orch', 'S1', color='#2E7D32', penwidth='6', **EDGE_STYLE)
    dot.edge('S1', 'S2', color='#2E7D32', penwidth='5', **EDGE_STYLE)
    dot.edge('S2', 'S3', color='#2E7D32', penwidth='5', **EDGE_STYLE)
    dot.edge('S3', 'S4', color='#004D40', penwidth='5', **EDGE_STYLE)
    dot.edge('S4', 'S5', color='#004D40', penwidth='5', **EDGE_STYLE)
    dot.edge('S5', 'S6', color='#004D40', penwidth='5', **EDGE_STYLE)
    dot.edge('S6', 'Out', color='#E65100', penwidth='6', **EDGE_STYLE)

    # TestRunner 增强
    dot.edge('S6', 'TR', color='#7B1FA2', penwidth='5', **EDGE_STYLE)
    dot.edge('TR', 'TR1', color='#7B1FA2', **EDGE_STYLE)
    dot.edge('TR', 'TR2', color='#7B1FA2', **EDGE_STYLE)
    dot.edge('TR', 'TR3', color='#7B1FA2', **EDGE_STYLE)
    dot.edge('TR', 'TR4', color='#7B1FA2', **EDGE_STYLE)
    dot.edge('TR', 'TR5', color='#7B1FA2', **EDGE_STYLE)
    dot.edge('TR', 'TR6', color='#7B1FA2', **EDGE_STYLE)

    # 输出文件
    dot.edge('Out', 'F1', color='#FFA000', **EDGE_STYLE)
    dot.edge('Out', 'F2', color='#FFA000', **EDGE_STYLE)
    dot.edge('Out', 'F3', color='#FFA000', **EDGE_STYLE)
    dot.edge('Out', 'F4', color='#FFA000', **EDGE_STYLE)

    # 统计反馈
    dot.edge('S6', 'Stats', color='#C62828', penwidth='5', **EDGE_STYLE)
    dot.edge('Stats', 'ST1', color='#C62828', **EDGE_STYLE)
    dot.edge('Stats', 'ST2', color='#C62828', **EDGE_STYLE)
    dot.edge('Stats', 'ST3', color='#C62828', **EDGE_STYLE)

    dot.render(cleanup=True)
    print("[OK] 测试编排系统架构图 v1.6 已生成")


def create_tool_system_diagram_v16():
    """工具系统架构图 v1.6 - 更新为18个工具"""
    dot = Digraph(
        'Tool_System_v1.6',
        filename='./docs/Tool_System_Architecture_v1.6',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='36,30', rankdir='TB', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    # 两层架构：AbstractFunctionCall + BaseTool
    dot.node('AbsFC', 'AbstractFunctionCall\n泛型基类\n参数校验\n执行追踪\n错误处理', fillcolor='#4A148C', fontcolor='white', **HEADER_STYLE)

    dot.node('Base', 'BaseTool抽象基类\n  - name: 工具名称\n  - description: 描述\n  - parameters: 参数\n  - execute(): 执行\n  - validate_params()\n  - to_function_call_format()', fillcolor='#E65100', fontcolor='white', **HEADER_STYLE)

    # 工具注册表
    dot.node('Registry', '工具注册表\n  - tools: 18个工具字典\n  - register(): 注册\n  - unregister(): 注销\n  - execute_tool(): 执行\n  - get_tool_descriptions()\n  - get_tool_help()', fillcolor='#3E2723', fontcolor='white', **HEADER_STYLE)

    # 具体工具 - 18个分5行
    with dot.subgraph(name='cluster_tools') as c:
        c.attr(style='filled', color='#F3E5F5', label='【具体工具 (共18个)】', pencolor='#4A148C', **CLUSTER_STYLE)

        # 行1: 基础IO工具
        with c.subgraph(name='cluster_row1') as r1:
            r1.attr(rank='same')
            r1.node('FR', '1. FileReader\n文件读取器\n只读安全\n参数: path', fillcolor='#7B1FA2', fontcolor='white', fontsize='11')
            r1.node('FW', '2. FileWriter\n文件写入器\n路径校验\n防目录穿越', fillcolor='#7B1FA2', fontcolor='white', fontsize='11')
            r1.node('EC', '3. CommandExecutor\n命令执行器\n安全过滤\n白+黑名单', fillcolor='#7B1FA2', fontcolor='white', fontsize='11')
            r1.node('CS', '4. CodeSearch\n代码搜索器\nGrep模式\n文件过滤', fillcolor='#7B1FA2', fontcolor='white', fontsize='11')

        # 行2: 分析工具
        with c.subgraph(name='cluster_row2') as r2:
            r2.attr(rank='same')
            r2.node('CA', '5. CompilerAnalyzer\n编译分析器\n错误提取分类\nMSVC/GCC兼容', fillcolor='#7B1FA2', fontcolor='white', fontsize='11')
            r2.node('LL', '6. LinkedListTool\n链表操作工具\n12种操作\nFunctionCall抽象', fillcolor='#7B1FA2', fontcolor='white', fontsize='11')
            r2.node('Git', '7. GitTool\nGit版本控制\nreview/deploy\n委托CodeReview', fillcolor='#7B1FA2', fontcolor='white', fontsize='11')
            r2.node('SA', '8. StaticAnalyzer\n静态代码分析\n语法检查\n问题扫描', fillcolor='#7B1FA2', fontcolor='white', fontsize='11')

        # 行3: 核心审查
        with c.subgraph(name='cluster_row3') as r3:
            r3.attr(rank='same')
            r3.node('CR', '9. CodeReview\n独立代码审查\n多语言支持\n结构化输出', fillcolor='#4A148C', fontcolor='white', fontsize='11')
            r3.node('ASAN', '10. MsvcAsanCompiler\nMSVC ASAN编译器\n/FSANITIZE=address\n内存错误检测', fillcolor='#4A148C', fontcolor='white', fontsize='11')
            r3.node('SSR', '11. SelfSourceReader\n自源码读取器\nAST分析\n结构获取', fillcolor='#AD1457', fontcolor='white', fontsize='11')
            r3.node('SIM', '12. SelfImprove\n自我改进工具\n备份/修复/自检', fillcolor='#AD1457', fontcolor='white', fontsize='11')

        # 行4: 插件 + 测试编排
        with c.subgraph(name='cluster_row4') as r4:
            r4.attr(rank='same')
            r4.node('PS', '13. PluginSystem\n插件系统\n动态加载扩展', fillcolor='#AD1457', fontcolor='white', fontsize='11')
            r4.node('TO', '14. TestOrchestrator\n测试编排器\n6步一站式流程\n核心编排引擎', fillcolor='#1B5E20', fontcolor='white', fontsize='11')
            r4.node('CRR', '15. CodeReviewReport\n审查报告生成\nMarkdown格式\n问题统计', fillcolor='#2E7D32', fontcolor='white', fontsize='11')
            r4.node('AF', '16. AutoFixer\n自动修复器\n智能修复bug\n备份安全机制', fillcolor='#2E7D32', fontcolor='white', fontsize='11')

        # 行5: 测试工具链
        with c.subgraph(name='cluster_row5') as r5:
            r5.attr(rank='same')
            r5.node('TDG', '17. TestDocGenerator\n测试文档生成\n结构化用例\n边界分析', fillcolor='#2E7D32', fontcolor='white', fontsize='11')
            r5.node('TG', '18. TestGenerator\n测试代码生成\n多语言模板\nMain框架', fillcolor='#2E7D32', fontcolor='white', fontsize='11')
            r5.node('TR', '19. TestRunner\n测试运行器\nMSVC/GCC双支持\n结果解析', fillcolor='#2E7D32', fontcolor='white', fontsize='11')

    # 测试编排核心区 - 阶段6核心
    with dot.subgraph(name='cluster_test_core') as tc:
        tc.attr(style='filled', color='#E8F5E9', label='【阶段6核心: 测试编排系统】', pencolor='#1B5E20', **CLUSTER_STYLE)
        tc.node('TestCore', '五大测试能力支柱\n\n1. 代码审查: CodeReview + CodeReviewReport\n2. 自动修复: AutoFixer 智能修复\n3. 文档生成: TestDocGenerator 结构化\n4. 代码生成: TestGenerator 多语言模板\n5. 测试运行: TestRunner MSVC/GCC双支持\n\n统一编排: TestOrchestrator 一站式流程', fillcolor='#1B5E20', fontcolor='white', fontsize='14')

    # 自我改进核心区 - 阶段5
    with dot.subgraph(name='cluster_self_improve') as si:
        si.attr(style='filled', color='#FFEBEE', label='【阶段5核心: 自我改进】', pencolor='#C62828', **CLUSTER_STYLE)
        si.node('SICore', '三大能力支柱\n\n1. 代码内省: SSR读取分析自身\n2. 代码自修复: SIM备份+修复+自检\n3. 能力扩展: PluginSystem动态加载\n\nAgent闭环进化: 自查 -> 自修复 -> 自扩展', fillcolor='#C62828', fontcolor='white', fontsize='14')

    # 工具结果
    dot.node('Result', '工具结果数据类\n  - success: bool\n  - content: str\n  - error_message: str\n  - raw_output: Any\n  - metadata: 附加数据', fillcolor='#006064', fontcolor='white', fontsize='16')

    # 消费者
    dot.node('AE', '代理引擎\nMVP模式\n测试编排集成', fillcolor='#1B5E20', fontcolor='white', fontsize='20')
    dot.node('LLM', 'Claude大语言模型\nJSON Schema工具定义\n18个工具自动发现\n测试指令理解', fillcolor='#004D40', fontcolor='white', fontsize='16')

    # 安全特性
    with dot.subgraph(name='cluster_safety') as s:
        s.attr(style='filled', color='#FFEBEE', label='【安全机制】', pencolor='#C62828', **CLUSTER_STYLE)
        s.node('S1', '危险操作过滤\nrm -rf/format/sudo/drop table\n黑名单+白名单双检', fillcolor='#EF5350', fontcolor='white', fontsize='14')
        s.node('S2', '路径验证\n防止目录穿越\n路径白名单\n相对路径校验', fillcolor='#EF5350', fontcolor='white', fontsize='14')
        s.node('S3', '插件安全\nBaseTool子类强制验证\n插件目录隔离\n无eval执行', fillcolor='#E53935', fontcolor='white', fontsize='14')

    # 连接线
    dot.edge('AbsFC', 'Base', color='#E65100', penwidth='5', **EDGE_STYLE)
    # 18个工具连接（简化显示关键路径）
    for t in ['FR', 'FW', 'EC', 'CS', 'CA', 'LL', 'Git', 'SA', 'CR', 'ASAN']:
        dot.edge('Base', t, color='#4A148C', **EDGE_STYLE)
    for t in ['SSR', 'SIM', 'PS']:
        dot.edge('Base', t, color='#AD1457', **EDGE_STYLE)
    # 测试工具链
    for t in ['TO', 'CRR', 'AF', 'TDG', 'TG', 'TR']:
        dot.edge('Base', t, color='#1B5E20', **EDGE_STYLE)

    # 核心区连接
    dot.edge('TO', 'TestCore', color='#1B5E20', penwidth='5', **EDGE_STYLE)
    dot.edge('CRR', 'TestCore', color='#1B5E20', **EDGE_STYLE)
    dot.edge('AF', 'TestCore', color='#1B5E20', **EDGE_STYLE)
    dot.edge('TDG', 'TestCore', color='#1B5E20', **EDGE_STYLE)
    dot.edge('TG', 'TestCore', color='#1B5E20', **EDGE_STYLE)
    dot.edge('TR', 'TestCore', color='#1B5E20', **EDGE_STYLE)

    # 自我改进核心区连接
    dot.edge('SSR', 'SICore', color='#C62828', **EDGE_STYLE)
    dot.edge('SIM', 'SICore', color='#C62828', **EDGE_STYLE)
    dot.edge('PS', 'SICore', color='#C62828', **EDGE_STYLE)

    # 注册表连接
    dot.edge('TestCore', 'Registry', color='#3E2723', penwidth='5', **EDGE_STYLE)
    dot.edge('SICore', 'Registry', color='#3E2723', penwidth='5', **EDGE_STYLE)

    # 结果连接
    dot.edge('Registry', 'Result', color='#006064', penwidth='5', **EDGE_STYLE)
    dot.edge('Result', 'AE', color='#1B5E20', penwidth='6', **EDGE_STYLE)
    dot.edge('AE', 'Registry', color='#3E2723', penwidth='6', **EDGE_STYLE)
    dot.edge('Registry', 'LLM', color='#004D40', penwidth='5', **EDGE_STYLE)
    dot.edge('LLM', 'AE', color='#004D40', penwidth='5', **EDGE_STYLE)

    # 安全连接
    dot.edge('EC', 'S1', style='dashed', color='#C62828', **EDGE_STYLE)
    dot.edge('FW', 'S2', style='dashed', color='#C62828', **EDGE_STYLE)
    dot.edge('PS', 'S3', style='dashed', color='#C62828', **EDGE_STYLE)

    dot.render(cleanup=True)
    print("[OK] 工具系统架构图 v1.6 已生成")


def create_plan_act_reflect_flowchart_v16():
    """执行流程图 v1.6 - 添加测试编排分支"""
    dot = Digraph(
        'Plan_Act_Reflect_v1.6',
        filename='./docs/Plan_Act_Reflect_Flowchart_v1.6',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='36,34', rankdir='TB', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    dot.node('Start', '开始\n接收用户查询\n"review code test run"', fillcolor='#1B5E20', fontcolor='white', fontsize='22')

    with dot.subgraph(name='cluster_plan') as c:
        c.attr(style='filled', color='#E3F2FD', label='【规划阶段】', pencolor='#0D47A1', **CLUSTER_STYLE)
        c.node('P1', '是否简单任务?\n检测: test/修复/审查/生成\norchestrator关键词', shape='diamond', fillcolor='#FFC107', fontsize='19', penwidth='5')
        c.node('P2', '生成简单计划\n最多2个步骤', fillcolor='#64B5F6', fontsize='17')
        c.node('P3', '启发式任务分解\n分析任务类型\n测试任务识别', fillcolor='#64B5F6', fontsize='17')
        c.node('P4', '可行性评估\n危险操作检测\n步骤连续检查\n目标清晰性', fillcolor='#64B5F6', fontsize='17')
        c.node('P5', '计划可行?', shape='diamond', fillcolor='#FFC107', fontsize='19', penwidth='5')
        c.node('P6', '返回错误', fillcolor='#C62828', fontcolor='white', fontsize='17')

        c.edge('P1', 'P2', color='#0D47A1', **EDGE_STYLE)
        c.edge('P1', 'P3', color='#0D47A1', **EDGE_STYLE)
        c.edge('P2', 'P4', color='#0D47A1', **EDGE_STYLE)
        c.edge('P3', 'P4', color='#0D47A1', **EDGE_STYLE)
        c.edge('P4', 'P5', color='#0D47A1', **EDGE_STYLE)
        c.edge('P5', 'P6', color='#C62828', **EDGE_STYLE)

    with dot.subgraph(name='cluster_act') as c:
        c.attr(style='filled', color='#E8F5E9', label='【执行阶段】', pencolor='#1B5E20', **CLUSTER_STYLE)
        c.node('A1', '初始化计数器=0', fillcolor='#81C784', fontsize='17')
        c.node('A2', '获取当前步骤\n+对话历史', fillcolor='#81C784', fontsize='17')
        c.node('A3', '构建增强提示词\n记忆增强\n对话历史\n工具定义(18个)', fillcolor='#81C784', fontsize='17')
        c.node('A4', '调用大模型API', fillcolor='#81C784', fontsize='17')
        c.node('A5', '有工具调用?', shape='diamond', fillcolor='#FFC107', fontsize='19', penwidth='5')
        c.node('A6', '执行工具\n通过注册表\nFunctionCall', fillcolor='#81C784', fontsize='17')
        c.node('A7', '执行成功?', shape='diamond', fillcolor='#FFC107', fontsize='19', penwidth='5')
        c.node('A8', '收集执行结果', fillcolor='#81C784', fontsize='17')
        c.node('A9', '标记步骤完成', fillcolor='#81C784', fontsize='17')
        c.node('A10', '本步完成?', shape='diamond', fillcolor='#FFC107', fontsize='19', penwidth='5')

        # 新增: 测试编排快捷分支
        c.node('AT1', '是测试编排任务?\ntool_needed == test_orchestrator', shape='diamond', fillcolor='#004D40', fontcolor='white', fontsize='17', penwidth='5')
        c.node('AT2', '直接执行 TestOrchestrator\n跳过LLM调用\n直接提取文件名\n创建项目目录\n执行6步完整流程', fillcolor='#2E7D32', fontcolor='white', fontsize='15')

        # 自我修复分支
        c.node('AS1', '自我修复?\n检测到代码问题', shape='diamond', fillcolor='#FF7043', fontsize='17', penwidth='5')
        c.node('AS2', '调用SelfImproveTool\n创建备份\n应用修复\n验证修复', fillcolor='#EF5350', fontcolor='white', fontsize='16')

    with dot.subgraph(name='cluster_reflect') as c:
        c.attr(style='filled', color='#FFF8E1', label='【反思阶段】', pencolor='#E65100', **CLUSTER_STYLE)
        c.node('R1', '分析执行结果\n含测试执行结果', fillcolor='#FFB74D', fontsize='17')
        c.node('R2', '错误模式匹配\n文件不存在\n权限不足\n超时\n语法错误\n编译失败\n测试失败', fillcolor='#FFB74D', fontsize='17')
        c.node('R3', '提取经验教训\n测试最佳实践', fillcolor='#FFB74D', fontsize='17')
        c.node('R4', '持久化到记忆\n测试记忆库', fillcolor='#FFB74D', fontsize='17')
        c.node('R5', '需要调整计划?', shape='diamond', fillcolor='#FFC107', fontsize='19', penwidth='5')
        c.node('R6', '插入新步骤\n或修改计划\n修复编译问题', fillcolor='#FFB74D', fontsize='17')
        c.node('R7', '计数器+1', fillcolor='#FFB74D', fontsize='17')
        # 自我改进反思
        c.node('RS1', '需要自改进?\nAgent代码缺陷检测', shape='diamond', fillcolor='#FF8F00', fontsize='17', penwidth='5')
        c.node('RS2', '触发自我改进流程\nSSR读取源码分析\nSIM应用修复\n验证修复效果', fillcolor='#FF6F00', fontcolor='white', fontsize='15')

    with dot.subgraph(name='cluster_finalize') as c:
        c.attr(style='filled', color='#F3E5F5', label='【终态阶段】', pencolor='#4A148C', **CLUSTER_STYLE)
        c.node('F1', '全部完成?\n或达最大迭代?', shape='diamond', fillcolor='#FFC107', fontsize='19', penwidth='5')
        c.node('F2', '生成执行总结\n步骤数/成功率/详情\n含自改进记录\n含测试通过率', fillcolor='#AB47BC', fontcolor='white', fontsize='17')
        c.node('F3', '生成最终答案\n通过大模型\n含测试报告', fillcolor='#BA68C8', fontcolor='white', fontsize='17')
        c.node('F4', '执行完成\n返回结果\n含完整测试报告\n修复率+通过率', fillcolor='#4A148C', fontcolor='white', fontsize='22')

    # 主流程线
    dot.edge('Start', 'P1', color='#1B5E20', penwidth='6', **EDGE_STYLE)
    dot.edge('P5', 'A1', color='#0D47A1', **EDGE_STYLE)
    dot.edge('A1', 'A2', color='#1B5E20', **EDGE_STYLE)
    dot.edge('A2', 'A3', color='#1B5E20', **EDGE_STYLE)
    dot.edge('A3', 'A4', color='#1B5E20', **EDGE_STYLE)
    dot.edge('A4', 'A5', color='#1B5E20', **EDGE_STYLE)
    dot.edge('A5', 'A10', color='#1B5E20', label='否', **EDGE_STYLE)
    dot.edge('A5', 'A6', color='#1B5E20', label='是', **EDGE_STYLE)
    dot.edge('A6', 'A7', color='#1B5E20', **EDGE_STYLE)
    dot.edge('A7', 'A8', color='#1B5E20', label='成功', **EDGE_STYLE)
    dot.edge('A8', 'A9', color='#1B5E20', **EDGE_STYLE)
    dot.edge('A9', 'AT1', color='#1B5E20', **EDGE_STYLE)

    # 测试编排快捷路径
    dot.edge('AT1', 'AT2', color='#004D40', penwidth='5', label='是 - 直接执行', **EDGE_STYLE)
    dot.edge('AT1', 'AS1', color='#1B5E20', label='否', **EDGE_STYLE)
    dot.edge('AT2', 'R1', color='#004D40', penwidth='5', **EDGE_STYLE)

    # 自我修复分支
    dot.edge('AS1', 'AS2', color='#C62828', label='是', **EDGE_STYLE)
    dot.edge('AS1', 'R1', color='#E65100', label='否', **EDGE_STYLE)
    dot.edge('AS2', 'R1', color='#C62828', **EDGE_STYLE)
    dot.edge('A10', 'R1', color='#E65100', **EDGE_STYLE)

    # 失败重试
    dot.edge('A7', 'A2', color='#C62828', style='dashed', label='失败 重试', **EDGE_STYLE)

    # 反思流程
    dot.edge('R1', 'R2', color='#E65100', **EDGE_STYLE)
    dot.edge('R2', 'R3', color='#E65100', **EDGE_STYLE)
    dot.edge('R3', 'R4', color='#E65100', **EDGE_STYLE)
    dot.edge('R4', 'RS1', color='#E65100', **EDGE_STYLE)
    dot.edge('RS1', 'RS2', color='#FF6F00', label='是', **EDGE_STYLE)
    dot.edge('RS1', 'R5', color='#E65100', label='否', **EDGE_STYLE)
    dot.edge('RS2', 'R5', color='#FF6F00', **EDGE_STYLE)
    dot.edge('R5', 'R6', color='#C62828', label='是', **EDGE_STYLE)
    dot.edge('R5', 'R7', color='#E65100', label='否', **EDGE_STYLE)
    dot.edge('R6', 'R7', color='#E65100', **EDGE_STYLE)
    dot.edge('R7', 'F1', color='#4A148C', **EDGE_STYLE)
    dot.edge('F1', 'A2', color='#0D47A1', style='dashed', label='未完成', **EDGE_STYLE)
    dot.edge('F1', 'F2', color='#4A148C', label='完成', **EDGE_STYLE)
    dot.edge('F2', 'F3', color='#4A148C', **EDGE_STYLE)
    dot.edge('F3', 'F4', color='#4A148C', penwidth='6', **EDGE_STYLE)

    dot.render(cleanup=True)
    print("[OK] 执行流程图 v1.6 已生成")


def create_data_flow_diagram_v16():
    """完整数据流图 v1.6 - 添加测试编排数据流"""
    dot = Digraph(
        'Data_Flow_v1.6',
        filename='./docs/Complete_Data_Flow_v1.6',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='38,30', rankdir='LR', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    with dot.subgraph(name='cluster_input') as c:
        c.attr(style='filled', color='#FFF3E0', label='【输入层】', pencolor='#E65100', **CLUSTER_STYLE)
        c.node('User', '用户输入\n查询字符串\n"review code test run"\n自我改进指令', fillcolor='#E64A19', fontcolor='white', fontsize='21')

    with dot.subgraph(name='cluster_plan_data') as c:
        c.attr(style='filled', color='#E3F2FD', label='【规划数据流】', pencolor='#0D47A1', **CLUSTER_STYLE)
        c.node('Query', '查询分析\n模式检测\n复杂度评估\n任务分类\n自改进识别\n测试任务识别', fillcolor='#64B5F6', fontsize='16')
        c.node('PlanData', '计划对象\n  - original_query: 原始查询\n  - steps: 步骤列表\n  - overall_goal: 总体目标\n  - complexity: 复杂度\n  - feasibility_score: 可行性\n  - current_step: 当前步骤\n  - self_improve: 自改进标记\n  - test_orchestrator: 测试标记', fillcolor='#0D47A1', fontcolor='white', fontsize='13')
        c.node('StepData', '计划步骤\n  - step_number: 步骤编号\n  - description: 步骤描述\n  - tool_needed: 需要工具\n  - expected_output: 预期输出\n  - importance: 重要性\n  - completed: 已完成\n  - success: 成功\n  - result_summary: 结果摘要\n  - error_message: 错误信息', fillcolor='#1A237E', fontcolor='white', fontsize='12')

    with dot.subgraph(name='cluster_act_data') as c:
        c.attr(style='filled', color='#E8F5E9', label='【执行数据流】', pencolor='#1B5E20', **CLUSTER_STYLE)
        c.node('Prompt', '增强提示词\n  - 系统提示\n  - 记忆增强\n  - 对话历史\n  - 工具定义(18个)', fillcolor='#81C784', fontsize='15')
        c.node('LLMReq', 'LLM请求\n  - model: 模型\n  - max_tokens: 最大Token\n  - system: 系统提示\n  - messages: 消息列表\n  - tools: 工具定义', fillcolor='#43A047', fontcolor='white', fontsize='14')
        c.node('LLMResp', 'LLM响应\n  - 内容块\n  - Thinking块\n  - 工具调用块', fillcolor='#2E7D32', fontcolor='white', fontsize='14')
        c.node('ToolCall', '工具调用\n  - id: 标识\n  - name: 工具名\n  - input: 输入参数', fillcolor='#1B5E20', fontcolor='white', fontsize='14')
        c.node('FCData', 'FunctionCall执行\n  - Parameters: 参数校验\n  - do_call(): 实际执行\n  - ExecutionResult: 结果\n  - call_chain: 调用链\n  - duration_ms: 耗时', fillcolor='#004D40', fontcolor='white', fontsize='13')

    # 新增: 测试编排数据流
    with dot.subgraph(name='cluster_test_data') as td:
        td.attr(style='filled', color='#A5D6A7', label='【测试编排数据流】', pencolor='#2E7D32', **CLUSTER_STYLE)
        td.node('TOData', 'TestOrchestrator输入\n  - file_path: 源文件路径\n  - project_name: 项目名称\n  - 6个流程开关参数', fillcolor='#43A047', fontcolor='white', fontsize='13')
        td.node('CRData', 'CodeReview结果\n  - issues: 问题列表[]\n  - severity: 严重程度\n  - counts: 统计数据', fillcolor='#66BB6A', fontcolor='white', fontsize='13')
        td.node('AFData', 'AutoFixer结果\n  - backup_file: 备份路径\n  - fixed_issues: 已修复[]\n  - unfixed_issues: 未修复[]\n  - fix_rate: 修复率%', fillcolor='#81C784', fontcolor='white', fontsize='13')
        td.node('TDocData', 'TestDocGenerator结果\n  - doc_path: 文档路径\n  - test_cases: 测试用例[]\n  - coverage: 覆盖率估算\n  - quality_score: 质量评分', fillcolor='#A5D6A7', fontcolor='white', fontsize='13')
        td.node('TGenData', 'TestGenerator结果\n  - test_path: 测试代码路径\n  - language: 语言\n  - tests_generated: 数量', fillcolor='#C8E6C9', fontcolor='white', fontsize='13')
        td.node('TRunData', 'TestRunner结果\n  - compile_success: bool\n  - run_success: bool\n  - passed: 通过数\n  - total: 总数\n  - pass_rate: 通过率%\n  - errors: 错误列表', fillcolor='#E8F5E9', fontcolor='white', fontsize='13')

    # 自我改进数据流
    with dot.subgraph(name='cluster_self_data') as c:
        c.attr(style='filled', color='#FFEBEE', label='【自我改进数据流】', pencolor='#C62828', **CLUSTER_STYLE)
        c.node('SSRData', 'SSR读取结果\n  - file_path: 文件路径\n  - line_count: 行数\n  - content: 源码内容\n  - structure: 结构信息', fillcolor='#EF5350', fontcolor='white', fontsize='13')
        c.node('SIMData', 'SIM修复数据\n  - backup_name: 备份名称\n  - target_file: 目标文件\n  - new_content: 新内容\n  - description: 修复描述\n  - test_results: 自检结果', fillcolor='#E53935', fontcolor='white', fontsize='13')
        c.node('PluginData', '插件系统数据\n  - plugin_path: 插件路径\n  - plugin_name: 插件名\n  - template_type: 模板类型\n  - loaded_tools: 已加载工具', fillcolor='#C62828', fontcolor='white', fontsize='13')
        c.node('BackupData', '备份元数据\n  - timestamp: 时间戳\n  - info.txt: 描述文件\n  - backup_dir: 备份目录\n  - pre_restore_safety: 安全备份', fillcolor='#B71C1C', fontcolor='white', fontsize='13')

    with dot.subgraph(name='cluster_memory_data') as c:
        c.attr(style='filled', color='#FFF8E1', label='【记忆数据流】', pencolor='#E65100', **CLUSTER_STYLE)
        c.node('MsgHist', '消息历史\n列表[字典]\n  - role: 角色\n  - content: 内容', fillcolor='#FFCA28', fontsize='14')
        c.node('MemItem', '记忆项\n  - content: 内容\n  - memory_type: 类型\n  - importance: 重要性\n  - timestamp: 时间戳\n  - metadata: 元数据\n  - self_improve_record\n  - test_best_practices', fillcolor='#FFA000', fontsize='14')
        c.node('ErrItem', '错误记录\n  - type: 错误类型\n  - description: 描述\n  - correction: 修正\n  - context: 上下文\n  - severity: 严重度\n  - occurrences: 次数\n  - self_fix_applied\n  - compile_errors_db', fillcolor='#FF6F00', fontcolor='white', fontsize='13')

    with dot.subgraph(name='cluster_reflect_data') as c:
        c.attr(style='filled', color='#F3E5F5', label='【反思数据流】', pencolor='#4A148C', **CLUSTER_STYLE)
        c.node('Reflection', '反思对象\n  - success: 是否成功\n  - goal_achieved: 目标达成\n  - issues_found: 发现问题\n  - improvements: 改进建议\n  - need_plan_adjustment: 需调整\n  - adjustment_suggestion: 调整建议\n  - lessons_learned: 经验教训\n  - confidence_score: 信心评分\n  - self_improve_needed\n  - test_pass_rate: 测试通过率', fillcolor='#AB47BC', fontcolor='white', fontsize='12')
        c.node('Summary', '执行总结\n  - 总步骤数\n  - 已完成数\n  - 成功数\n  - 成功率\n  - 详细步骤\n  - 自我改进记录\n  - 测试通过率\n  - 代码修复率', fillcolor='#7B1FA2', fontcolor='white', fontsize='14')

    with dot.subgraph(name='cluster_output') as c:
        c.attr(style='filled', color='#E0F7FA', label='【输出层】', pencolor='#006064', **CLUSTER_STYLE)
        c.node('Output', '最终答案\n清理响应\n纯文本输出\n格式化展示\n含自改进报告\n含完整测试报告\n代码修复率统计', fillcolor='#006064', fontcolor='white', fontsize='19')

    # 主连接线
    dot.edge('User', 'Query', color='#E64A19', penwidth='6', **EDGE_STYLE)
    dot.edge('Query', 'PlanData', color='#0D47A1', penwidth='5', **EDGE_STYLE)
    dot.edge('PlanData', 'StepData', color='#0D47A1', penwidth='5', **EDGE_STYLE)
    dot.edge('PlanData', 'Prompt', color='#1B5E20', penwidth='4', **EDGE_STYLE)
    dot.edge('MemItem', 'Prompt', color='#1B5E20', penwidth='4', **EDGE_STYLE)
    dot.edge('MsgHist', 'Prompt', color='#1B5E20', penwidth='4', **EDGE_STYLE)
    dot.edge('Prompt', 'LLMReq', color='#1B5E20', penwidth='5', **EDGE_STYLE)
    dot.edge('LLMReq', 'LLMResp', color='#1B5E20', penwidth='5', **EDGE_STYLE)
    dot.edge('LLMResp', 'ToolCall', color='#1B5E20', penwidth='4', **EDGE_STYLE)
    dot.edge('ToolCall', 'FCData', color='#004D40', penwidth='4', **EDGE_STYLE)

    # 测试编排数据流
    dot.edge('ToolCall', 'TOData', color='#2E7D32', penwidth='5', **EDGE_STYLE)
    dot.edge('TOData', 'CRData', color='#2E7D32', **EDGE_STYLE)
    dot.edge('CRData', 'AFData', color='#2E7D32', **EDGE_STYLE)
    dot.edge('AFData', 'TDocData', color='#2E7D32', **EDGE_STYLE)
    dot.edge('TDocData', 'TGenData', color='#2E7D32', **EDGE_STYLE)
    dot.edge('TGenData', 'TRunData', color='#2E7D32', **EDGE_STYLE)
    # 测试数据回流到步骤
    dot.edge('TRunData', 'StepData', color='#1B5E20', penwidth='5', **EDGE_STYLE)

    # 自我改进数据流向
    dot.edge('ToolCall', 'SSRData', color='#C62828', penwidth='4', **EDGE_STYLE)
    dot.edge('ToolCall', 'SIMData', color='#C62828', penwidth='4', **EDGE_STYLE)
    dot.edge('ToolCall', 'PluginData', color='#C62828', penwidth='4', **EDGE_STYLE)
    dot.edge('SIMData', 'BackupData', color='#B71C1C', style='dashed', **EDGE_STYLE)
    dot.edge('SSRData', 'StepData', color='#1B5E20', penwidth='4', **EDGE_STYLE)
    dot.edge('SIMData', 'StepData', color='#1B5E20', penwidth='4', **EDGE_STYLE)
    dot.edge('PluginData', 'StepData', color='#1B5E20', penwidth='4', **EDGE_STYLE)

    # 原流程
    dot.edge('FCData', 'StepData', color='#1B5E20', penwidth='4', **EDGE_STYLE)
    dot.edge('StepData', 'Reflection', color='#4A148C', penwidth='5', **EDGE_STYLE)
    dot.edge('Reflection', 'MemItem', color='#E65100', penwidth='4', style='dashed', **EDGE_STYLE)
    dot.edge('Reflection', 'ErrItem', color='#E65100', penwidth='4', style='dashed', **EDGE_STYLE)
    dot.edge('Reflection', 'PlanData', color='#0D47A1', penwidth='4', style='dashed', **EDGE_STYLE)
    dot.edge('LLMResp', 'MsgHist', color='#E65100', penwidth='4', **EDGE_STYLE)
    dot.edge('ToolCall', 'MsgHist', color='#E65100', penwidth='4', **EDGE_STYLE)
    dot.edge('FCData', 'MsgHist', color='#E65100', penwidth='4', **EDGE_STYLE)
    dot.edge('SSRData', 'MsgHist', color='#E65100', penwidth='4', **EDGE_STYLE)
    dot.edge('SIMData', 'MsgHist', color='#E65100', penwidth='4', **EDGE_STYLE)
    dot.edge('PluginData', 'MsgHist', color='#E65100', penwidth='4', **EDGE_STYLE)
    # 测试数据也更新到消息历史
    dot.edge('CRData', 'MsgHist', color='#E65100', style='dashed', **EDGE_STYLE)
    dot.edge('TRunData', 'MsgHist', color='#E65100', style='dashed', **EDGE_STYLE)

    dot.edge('PlanData', 'Summary', color='#4A148C', penwidth='5', **EDGE_STYLE)
    dot.edge('Summary', 'Output', color='#006064', penwidth='6', **EDGE_STYLE)
    dot.edge('LLMResp', 'Output', color='#006064', penwidth='6', **EDGE_STYLE)

    dot.render(cleanup=True)
    print("[OK] 完整数据流图 v1.6 已生成")


if __name__ == '__main__':
    print("=" * 80)
    print("DevPal Agent v1.6 - 架构图生成器")
    print("=" * 80)
    print("主要更新 (阶段6 - 自动化测试编排系统):")
    print("  1. 系统架构图 添加 测试编排系统层 (18个工具)")
    print("  2. 新增 Test_Orchestrator_System_Architecture 架构图")
    print("  3. 工具系统架构图 更新为 18个工具 + 5大测试能力支柱")
    print("  4. 执行流程图 添加 TestOrchestrator 快捷执行分支")
    print("  5. 数据流图 添加 测试编排数据流 (6步完整数据流)")
    print("  6. 所有图版本号升级为 v1.6")
    print("=" * 80)

    create_architecture_overview_v16()
    create_test_orchestrator_architecture_v16()
    create_tool_system_diagram_v16()
    create_plan_act_reflect_flowchart_v16()
    create_data_flow_diagram_v16()

    print("=" * 80)
    print("所有架构图已成功生成到 ./docs/ 目录!")
    print("=" * 80)
    print("\n生成的文件列表 (v1.6):")
    print("  1. DevPal_Architecture_Overview_v1.6.png")
    print("  2. Test_Orchestrator_System_Architecture_v1.6.png  [新增]")
    print("  3. Tool_System_Architecture_v1.6.png")
    print("  4. Plan_Act_Reflect_Flowchart_v1.6.png")
    print("  5. Complete_Data_Flow_v1.6.png")
    print("\n字体: 微软雅黑 Microsoft YaHei")
    print("分辨率: 600 DPI 超高清")
