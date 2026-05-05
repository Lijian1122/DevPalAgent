# -*- coding: utf-8 -*-
"""
DevPal Agent v1.5 - 架构图生成器
更新内容：阶段5 - 添加自我改进系统 + 插件系统
新增: SelfSourceReaderTool, SelfImproveTool, PluginSystemTool
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


def create_architecture_overview_v15():
    """系统整体架构图 v1.5 - 新增自我改进层 + 插件系统"""
    dot = Digraph(
        'DevPal_Architecture_v1.5',
        filename='./docs/DevPal_Architecture_Overview_v1.5',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='32,26', rankdir='TB', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    # 用户层
    with dot.subgraph(name='cluster_user') as c:
        c.attr(style='filled', color='#FFF3E0', label='【用户层】', **CLUSTER_STYLE)
        c.node('User', '用户\n输入查询', fillcolor='#E64A19', fontcolor='white', fontsize='20')
        c.node('CLI', '命令行\n交互式模式', fillcolor='#FF5722', fontcolor='white', fontsize='18')
        c.node('Web', 'Web界面\n多标签工具', fillcolor='#FF7043', fontcolor='white', fontsize='18')

    # 核心引擎层
    with dot.subgraph(name='cluster_core') as c:
        c.attr(style='filled', color='#E3F2FD', label='【核心引擎层】', **CLUSTER_STYLE)
        c.node('Engine', '代理引擎\n主执行循环', fillcolor='#0D47A1', fontcolor='white', **HEADER_STYLE)

        with c.subgraph(name='cluster_planner') as pc:
            pc.attr(style='filled', color='#BBDEFB', label='规划模块', fontsize='18')
            pc.node('PlanGen', '计划生成\n启发式/LLM', fillcolor='#42A5F5', fontsize='16')
            pc.node('Feasibility', '可行性评估\n危险检测', fillcolor='#42A5F5', fontsize='16')
            pc.node('PlanAdjust', '计划调整\n动态修改', fillcolor='#42A5F5', fontsize='16')

        with c.subgraph(name='cluster_reflector') as rc:
            rc.attr(style='filled', color='#C8E6C9', label='反思模块', fontsize='18')
            rc.node('Reflection', '执行反思\n结果分析', fillcolor='#2E7D32', fontcolor='white', fontsize='16')
            rc.node('PatternMatch', '模式匹配\n错误检测', fillcolor='#2E7D32', fontcolor='white', fontsize='16')
            rc.node('Lessons', '经验提取\n总结学习', fillcolor='#2E7D32', fontcolor='white', fontsize='16')

    # 记忆层
    with dot.subgraph(name='cluster_memory') as c:
        c.attr(style='filled', color='#FFF8E1', label='【记忆系统层】', **CLUSTER_STYLE)
        c.node('MM', '记忆管理器\n统一入口', fillcolor='#E65100', fontcolor='white', **HEADER_STYLE)
        c.node('STM', '短期记忆\n对话上下文\n滑动窗口', fillcolor='#FFCA28', fontsize='14')
        c.node('LTM', '长期记忆\n用户偏好\n任务经验', fillcolor='#FFA000', fontsize='14')
        c.node('EM', '错误记忆\n模式跟踪\n修正建议', fillcolor='#FF6F00', fontcolor='white', fontsize='14')

    # 自我改进层 - 阶段5新增
    with dot.subgraph(name='cluster_self_improve') as c:
        c.attr(style='filled', color='#FFEBEE', label='【自我改进层】', pencolor='#C62828', **CLUSTER_STYLE)
        c.node('SelfImprove', '自我改进系统\n代码自修复', fillcolor='#C62828', fontcolor='white', **HEADER_STYLE)
        with c.subgraph(name='cluster_self_tools') as st:
            st.attr(rank='same')
            st.node('SSR', 'SelfSourceReader\n读取自身源码\nAST分析\n结构获取', fillcolor='#D32F2F', fontcolor='white', fontsize='13')
            st.node('SIM', 'SelfImproveTool\n备份恢复\n问题分析\n代码修复\n自检', fillcolor='#D32F2F', fontcolor='white', fontsize='13')
            st.node('PS', 'PluginSystem\n插件加载/卸载\n模板生成\n动态扩展', fillcolor='#D32F2F', fontcolor='white', fontsize='13')

    # 工具层 - 扩展到13个工具
    with dot.subgraph(name='cluster_tools') as c:
        c.attr(style='filled', color='#F3E5F5', label='【工具系统层】', **CLUSTER_STYLE)
        c.node('ToolReg', '工具注册表\n统一调度\n13个工具', fillcolor='#4A148C', fontcolor='white', **HEADER_STYLE)

        # FunctionCall 抽象层
        with c.subgraph(name='cluster_func_call') as fc:
            fc.attr(style='filled', color='#E1BEE7', label='抽象FunctionCall层', fontsize='18')
            fc.node('AbsFC', 'AbstractFunctionCall\n泛型基类\n参数校验\n执行追踪\n错误处理', fillcolor='#7B1FA2', fontcolor='white', fontsize='15')
            fc.node('FCtx', 'FunctionCallContext\n调用链\n变量存储\n计时统计', fillcolor='#8E24AA', fontcolor='white', fontsize='14')
            fc.node('FChain', 'FunctionChain\n链式执行\n结果传递\n参数合并', fillcolor='#9C27B0', fontcolor='white', fontsize='14')
            fc.node('ExecRes', 'ExecutionResult\nsuccess/data\nerror/duration\nmetadata', fillcolor='#BA68C8', fontcolor='white', fontsize='13')

        # 具体工具 - 13个
        with c.subgraph(name='cluster_concrete') as tc:
            tc.attr(rank='same')
            tc.node('FR', '文件\n读取', fillcolor='#6A1B9A', fontcolor='white', fontsize='13')
            tc.node('FW', '文件\n写入', fillcolor='#6A1B9A', fontcolor='white', fontsize='13')
            tc.node('EC', '命令\n执行', fillcolor='#6A1B9A', fontcolor='white', fontsize='13')
            tc.node('CS', '代码\n搜索', fillcolor='#6A1B9A', fontcolor='white', fontsize='13')
            tc.node('CA', '编译\n分析', fillcolor='#6A1B9A', fontcolor='white', fontsize='13')
            tc.node('LL', '链表\n工具', fillcolor='#6A1B9A', fontcolor='white', fontsize='13')
        with c.subgraph(name='cluster_concrete2') as tc2:
            tc2.attr(rank='same')
            tc2.node('Git', 'Git\n工具', fillcolor='#6A1B9A', fontcolor='white', fontsize='13')
            tc2.node('SA', '静态\n分析', fillcolor='#6A1B9A', fontcolor='white', fontsize='13')
            tc2.node('CR', '代码\n审查', fillcolor='#6A1B9A', fontcolor='white', fontsize='13')
            tc2.node('ASAN', 'MSVC\nASAN', fillcolor='#6A1B9A', fontcolor='white', fontsize='13')

    # LLM层
    with dot.subgraph(name='cluster_llm') as c:
        c.attr(style='filled', color='#E0F7FA', label='【大模型层】', **CLUSTER_STYLE)
        c.node('LLM', 'Claude大模型\n兼容火山引擎\nThinking支持', fillcolor='#006064', fontcolor='white', fontsize='17')

    # 插件目录 - 外部扩展
    with dot.subgraph(name='cluster_plugins') as c:
        c.attr(style='filled', color='#F1F8E9', label='【插件目录】', pencolor='#558B2F', **CLUSTER_STYLE)
        c.node('PluginDir', './plugins/\n第三方插件\n动态加载', fillcolor='#558B2F', fontcolor='white', fontsize='14')
        c.node('BackupDir', './.devpal_backups/\n代码快照\n安全回滚', fillcolor='#689F38', fontcolor='white', fontsize='14')

    # 连接线
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
    dot.edge('Engine', 'ToolReg', color='#7B1FA2', **EDGE_STYLE)
    dot.edge('ToolReg', 'AbsFC', color='#7B1FA2', **EDGE_STYLE)
    dot.edge('AbsFC', 'FCtx', color='#7B1FA2', **EDGE_STYLE)
    dot.edge('AbsFC', 'FChain', color='#7B1FA2', **EDGE_STYLE)
    dot.edge('AbsFC', 'ExecRes', color='#7B1FA2', **EDGE_STYLE)
    # 10个工具
    dot.edge('AbsFC', 'FR', color='#7B1FA2', **EDGE_STYLE)
    dot.edge('AbsFC', 'FW', color='#7B1FA2', **EDGE_STYLE)
    dot.edge('AbsFC', 'EC', color='#7B1FA2', **EDGE_STYLE)
    dot.edge('AbsFC', 'CS', color='#7B1FA2', **EDGE_STYLE)
    dot.edge('AbsFC', 'CA', color='#7B1FA2', **EDGE_STYLE)
    dot.edge('AbsFC', 'LL', color='#7B1FA2', **EDGE_STYLE)
    dot.edge('AbsFC', 'Git', color='#7B1FA2', **EDGE_STYLE)
    dot.edge('AbsFC', 'SA', color='#7B1FA2', **EDGE_STYLE)
    dot.edge('AbsFC', 'CR', color='#7B1FA2', **EDGE_STYLE)
    dot.edge('AbsFC', 'ASAN', color='#7B1FA2', **EDGE_STYLE)
    # 自我改进层连接
    dot.edge('ToolReg', 'SelfImprove', color='#C62828', **EDGE_STYLE)
    dot.edge('SelfImprove', 'SSR', color='#C62828', **EDGE_STYLE)
    dot.edge('SelfImprove', 'SIM', color='#C62828', **EDGE_STYLE)
    dot.edge('SelfImprove', 'PS', color='#C62828', **EDGE_STYLE)
    dot.edge('PS', 'PluginDir', color='#558B2F', style='dashed', **EDGE_STYLE)
    dot.edge('SIM', 'BackupDir', color='#558B2F', style='dashed', **EDGE_STYLE)
    dot.edge('SSR', 'FR', color='#C62828', style='dashed', **EDGE_STYLE)
    # 结果返回
    dot.edge('FR', 'Engine', color='#7B1FA2', style='dashed', **EDGE_STYLE)
    dot.edge('FW', 'Engine', color='#7B1FA2', style='dashed', **EDGE_STYLE)
    dot.edge('EC', 'Engine', color='#7B1FA2', style='dashed', **EDGE_STYLE)
    dot.edge('CS', 'Engine', color='#7B1FA2', style='dashed', **EDGE_STYLE)
    dot.edge('CA', 'Engine', color='#7B1FA2', style='dashed', **EDGE_STYLE)
    dot.edge('LL', 'Engine', color='#7B1FA2', style='dashed', **EDGE_STYLE)
    dot.edge('SSR', 'Engine', color='#C62828', style='dashed', **EDGE_STYLE)
    dot.edge('SIM', 'Engine', color='#C62828', style='dashed', **EDGE_STYLE)
    dot.edge('PS', 'Engine', color='#C62828', style='dashed', **EDGE_STYLE)
    # 反思
    dot.edge('Engine', 'Reflection', color='#2E7D32', **EDGE_STYLE)
    dot.edge('Reflection', 'PatternMatch', color='#2E7D32', **EDGE_STYLE)
    dot.edge('PatternMatch', 'Lessons', color='#2E7D32', **EDGE_STYLE)
    dot.edge('Reflection', 'PlanAdjust', color='#2E7D32', style='dashed', **EDGE_STYLE)
    dot.edge('Engine', 'LLM', color='#006064', **EDGE_STYLE)
    dot.edge('LLM', 'Engine', color='#006064', **EDGE_STYLE)
    dot.edge('Engine', 'CLI', color='#1B5E20', **{**EDGE_STYLE, 'penwidth': '6'})
    dot.edge('Engine', 'Web', color='#1B5E20', **{**EDGE_STYLE, 'penwidth': '6'})

    dot.render(cleanup=True)
    print("[OK] 系统整体架构图 v1.5 已生成")


def create_self_improve_architecture_v15():
    """新增: 自我改进系统架构图 v1.5"""
    dot = Digraph(
        'SelfImprove_Architecture_v1.5',
        filename='./docs/SelfImprove_System_Architecture_v1.5',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='30,28', rankdir='TB', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    # 核心引擎
    with dot.subgraph(name='cluster_core') as c:
        c.attr(style='filled', color='#E3F2FD', label='【触发源】', pencolor='#0D47A1', **CLUSTER_STYLE)
        c.node('Engine', '代理引擎\n自我诊断触发\n检测到异常\n用户主动调用', fillcolor='#0D47A1', fontcolor='white', fontsize='16')

    # SelfSourceReaderTool
    with dot.subgraph(name='cluster_ssr') as c:
        c.attr(style='filled', color='#FFF8E1', label='【SelfSourceReaderTool - 自源代码读取】', pencolor='#E65100', **CLUSTER_STYLE)
        c.node('SSR', 'SelfSourceReaderTool\nname: self_source_reader\ndescription: 读取和分析Agent自身源代码', fillcolor='#E65100', fontcolor='white', fontsize='15')
        with c.subgraph(name='cluster_ssr_actions') as sa:
            sa.attr(rank='same')
            sa.node('SSR1', 'list_files\n列出所有源码文件\n递归查找 *.py', fillcolor='#FF8F00', fontcolor='white', fontsize='13')
            sa.node('SSR2', 'read_file\n读取指定文件内容\n完整源码获取', fillcolor='#FF8F00', fontcolor='white', fontsize='13')
            sa.node('SSR3', 'search_code\n正则搜索代码\nGrep模式匹配', fillcolor='#FF8F00', fontcolor='white', fontsize='13')
        with c.subgraph(name='cluster_ssr_actions2') as sa2:
            sa2.attr(rank='same')
            sa2.node('SSR4', 'analyze_module\nAST语法树分析\n类/函数/导入提取', fillcolor='#FFA000', fontcolor='white', fontsize='13')
            sa2.node('SSR5', 'get_structure\n整体结构概览\n模块分类统计', fillcolor='#FFA000', fontcolor='white', fontsize='13')
        c.node('SSR6', 'Path: devpal/\nAST分析使用 ast 模块\n相对路径安全校验', fillcolor='#FFB300', fontcolor='white', fontsize='13')

    # SelfImproveTool
    with dot.subgraph(name='cluster_sim') as c:
        c.attr(style='filled', color='#FFEBEE', label='【SelfImproveTool - 自我修复改进】', pencolor='#C62828', **CLUSTER_STYLE)
        c.node('SIM', 'SelfImproveTool\nname: self_improve\ndescription: Agent自我修复bug和自我改进代码', fillcolor='#C62828', fontcolor='white', fontsize='15')
        with c.subgraph(name='cluster_sim_backup') as sb:
            sb.attr(rank='same')
            sb.node('SIM1', 'create_backup\n创建代码快照\n备份到 .devpal_backups/', fillcolor='#EF5350', fontcolor='white', fontsize='13')
            sb.node('SIM2', 'list_backups\n列出所有备份\n时间戳+描述', fillcolor='#EF5350', fontcolor='white', fontsize='13')
            sb.node('SIM3', 'restore_backup\n安全回滚\n先备份再恢复', fillcolor='#EF5350', fontcolor='white', fontsize='13')
        with c.subgraph(name='cluster_sim_fix') as sf:
            sf.attr(rank='same')
            sf.node('SIM4', 'analyze_issue\n检测代码问题\nTODO/FIXME/print调试', fillcolor='#E53935', fontcolor='white', fontsize='13')
            sf.node('SIM5', 'apply_fix\n应用代码修复\n自动安全备份', fillcolor='#E53935', fontcolor='white', fontsize='13')
            sf.node('SIM6', 'run_self_test\n4项自检\n导入/注册/核心模块', fillcolor='#E53935', fontcolor='white', fontsize='13')
        c.node('SIM7', '备份机制: backup_YYYYMMDD_HHMMSS_name\n安全恢复: 先创建safety_backup再恢复\n问题检测: TODO/FIXME/debug print 扫描', fillcolor='#C62828', fontcolor='white', fontsize='12')

    # PluginSystemTool
    with dot.subgraph(name='cluster_ps') as c:
        c.attr(style='filled', color='#E8F5E9', label='【PluginSystemTool - 插件系统】', pencolor='#1B5E20', **CLUSTER_STYLE)
        c.node('PS', 'PluginSystemTool\nname: plugin_system\ndescription: 加载、管理和卸载第三方工具插件', fillcolor='#1B5E20', fontcolor='white', fontsize='15')
        with c.subgraph(name='cluster_ps_ops') as po:
            po.attr(rank='same')
            po.node('PS1', 'list_plugins\n列出已注册工具\n显示可用插件文件', fillcolor='#43A047', fontcolor='white', fontsize='13')
            po.node('PS2', 'load_plugin\n动态导入模块\nBaseTool子类发现\n自动注册', fillcolor='#43A047', fontcolor='white', fontsize='13')
            po.node('PS3', 'unload_plugin\n从注册表移除\n(模块仍在内存)', fillcolor='#43A047', fontcolor='white', fontsize='13')
        with c.subgraph(name='cluster_ps_tpl') as pt:
            pt.attr(rank='same')
            pt.node('PS4', 'create_template\nbasic: 简单工具模板\nfull: 完整多工具模板', fillcolor='#66BB6A', fontcolor='white', fontsize='13')
            pt.node('PS5', 'show_help\n快速开始指南\n可用操作说明\n注意事项提示', fillcolor='#66BB6A', fontcolor='white', fontsize='13')
        c.node('PS6', '插件目录: ./plugins/\n动态加载: importlib.util.spec_from_file_location\n模板内置: @retry装饰器 + ToolSecurity安全检查', fillcolor='#2E7D32', fontcolor='white', fontsize='12')

    # 工具注册表集成
    with dot.subgraph(name='cluster_reg') as c:
        c.attr(style='filled', color='#F3E5F5', label='【工具注册表】', pencolor='#4A148C', **CLUSTER_STYLE)
        c.node('Registry', 'ToolRegistry\nregister() / unregister()\nexecute_tool()\nget_tool_descriptions()\n当前已注册: 13个工具', fillcolor='#4A148C', fontcolor='white', fontsize='15')

    # 外部目录
    with dot.subgraph(name='cluster_dirs') as c:
        c.attr(style='filled', color='#E0F7FA', label='【文件系统】', pencolor='#006064', **CLUSTER_STYLE)
        c.node('BackupDir', './.devpal_backups/\n代码备份存储\n格式: backup_timestamp_name\ninfo.txt: 描述+时间戳', fillcolor='#006064', fontcolor='white', fontsize='14')
        c.node('PluginDir', './plugins/\n第三方插件目录\n自动添加到sys.path\n*.py文件自动发现', fillcolor='#00838F', fontcolor='white', fontsize='14')

    # 连接线
    dot.edge('Engine', 'SSR', color='#E65100', penwidth='5', **EDGE_STYLE)
    dot.edge('Engine', 'SIM', color='#C62828', penwidth='5', **EDGE_STYLE)
    dot.edge('Engine', 'PS', color='#1B5E20', penwidth='5', **EDGE_STYLE)
    # SSR actions
    dot.edge('SSR', 'SSR1', color='#E65100', **EDGE_STYLE)
    dot.edge('SSR', 'SSR2', color='#E65100', **EDGE_STYLE)
    dot.edge('SSR', 'SSR3', color='#E65100', **EDGE_STYLE)
    dot.edge('SSR', 'SSR4', color='#E65100', **EDGE_STYLE)
    dot.edge('SSR', 'SSR5', color='#E65100', **EDGE_STYLE)
    dot.edge('SSR', 'SSR6', color='#E65100', style='dashed', **EDGE_STYLE)
    # SIM actions
    dot.edge('SIM', 'SIM1', color='#C62828', **EDGE_STYLE)
    dot.edge('SIM', 'SIM2', color='#C62828', **EDGE_STYLE)
    dot.edge('SIM', 'SIM3', color='#C62828', **EDGE_STYLE)
    dot.edge('SIM', 'SIM4', color='#C62828', **EDGE_STYLE)
    dot.edge('SIM', 'SIM5', color='#C62828', **EDGE_STYLE)
    dot.edge('SIM', 'SIM6', color='#C62828', **EDGE_STYLE)
    dot.edge('SIM', 'SIM7', color='#C62828', style='dashed', **EDGE_STYLE)
    # PS actions
    dot.edge('PS', 'PS1', color='#1B5E20', **EDGE_STYLE)
    dot.edge('PS', 'PS2', color='#1B5E20', **EDGE_STYLE)
    dot.edge('PS', 'PS3', color='#1B5E20', **EDGE_STYLE)
    dot.edge('PS', 'PS4', color='#1B5E20', **EDGE_STYLE)
    dot.edge('PS', 'PS5', color='#1B5E20', **EDGE_STYLE)
    dot.edge('PS', 'PS6', color='#1B5E20', style='dashed', **EDGE_STYLE)
    # 注册
    dot.edge('SSR', 'Registry', color='#4A148C', **EDGE_STYLE)
    dot.edge('SIM', 'Registry', color='#4A148C', **EDGE_STYLE)
    dot.edge('PS', 'Registry', color='#4A148C', **EDGE_STYLE)
    # 目录连接
    dot.edge('SIM1', 'BackupDir', color='#006064', style='dashed', **EDGE_STYLE)
    dot.edge('SIM3', 'BackupDir', color='#006064', style='dashed', **EDGE_STYLE)
    dot.edge('PS2', 'PluginDir', color='#006064', style='dashed', **EDGE_STYLE)
    dot.edge('PS4', 'PluginDir', color='#006064', style='dashed', **EDGE_STYLE)
    # 循环依赖
    dot.edge('Registry', 'Engine', color='#4A148C', style='dashed', penwidth='4', **EDGE_STYLE)

    dot.render(cleanup=True)
    print("[OK] 自我改进系统架构图 v1.5 已生成")


def create_tool_system_diagram_v15():
    """工具系统架构图 v1.5 - 更新为13个工具"""
    dot = Digraph(
        'Tool_System_v1.5',
        filename='./docs/Tool_System_Architecture_v1.5',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='32,28', rankdir='TB', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    # 两层架构：AbstractFunctionCall + BaseTool
    dot.node('AbsFC', 'AbstractFunctionCall\n泛型基类\n参数校验\n执行追踪\n错误处理', fillcolor='#4A148C', fontcolor='white', **HEADER_STYLE)

    dot.node('Base', 'BaseTool抽象基类\n  - name: 工具名称\n  - description: 描述\n  - parameters: 参数\n  - execute(): 执行\n  - validate_params()\n  - to_function_call_format()', fillcolor='#E65100', fontcolor='white', **HEADER_STYLE)

    # 工具注册表
    dot.node('Registry', '工具注册表\n  - tools: 13个工具字典\n  - register(): 注册\n  - unregister(): 注销\n  - execute_tool(): 执行\n  - get_tool_descriptions()\n  - get_tool_help()', fillcolor='#3E2723', fontcolor='white', **HEADER_STYLE)

    # 具体工具 - 13个工具分3行
    with dot.subgraph(name='cluster_tools') as c:
        c.attr(style='filled', color='#F3E5F5', label='【具体工具 (共13个)】', pencolor='#4A148C', **CLUSTER_STYLE)

        with c.subgraph(name='cluster_row1') as r1:
            r1.attr(rank='same')
            r1.node('FR', '1. FileReader\n文件读取器\n只读安全\n参数: path', fillcolor='#7B1FA2', fontcolor='white', fontsize='12')
            r1.node('FW', '2. FileWriter\n文件写入器\n路径校验\n防目录穿越', fillcolor='#7B1FA2', fontcolor='white', fontsize='12')
            r1.node('EC', '3. CommandExecutor\n命令执行器\n安全过滤\n白+黑名单', fillcolor='#7B1FA2', fontcolor='white', fontsize='12')
            r1.node('CS', '4. CodeSearch\n代码搜索器\nGrep模式\n文件过滤', fillcolor='#7B1FA2', fontcolor='white', fontsize='12')

        with c.subgraph(name='cluster_row2') as r2:
            r2.attr(rank='same')
            r2.node('CA', '5. CompilerAnalyzer\n编译分析器\n错误提取分类\nMSVC/GCC兼容', fillcolor='#7B1FA2', fontcolor='white', fontsize='12')
            r2.node('LL', '6. LinkedListTool\n链表操作工具\n12种操作\nFunctionCall抽象', fillcolor='#7B1FA2', fontcolor='white', fontsize='12')
            r2.node('Git', '7. GitTool\nGit版本控制\nreview/deploy\n委托CodeReview', fillcolor='#7B1FA2', fontcolor='white', fontsize='12')
            r2.node('SA', '8. StaticAnalyzer\n静态代码分析\n语法检查\n问题扫描', fillcolor='#7B1FA2', fontcolor='white', fontsize='12')

        with c.subgraph(name='cluster_row3') as r3:
            r3.attr(rank='same')
            r3.node('CR', '9. CodeReview\n独立代码审查\n多语言支持\n结构化输出', fillcolor='#4A148C', fontcolor='white', fontsize='12')
            r3.node('ASAN', '10. MsvcAsanCompiler\nMSVC ASAN编译器\n/fsanitize=address\n内存错误检测', fillcolor='#4A148C', fontcolor='white', fontsize='12')
            r3.node('SSR', '11. SelfSourceReader\n自源码读取器\nAST分析\n结构获取', fillcolor='#AD1457', fontcolor='white', fontsize='12')
            r3.node('SIM', '12. SelfImprove\n自我改进工具\n备份/修复/自检', fillcolor='#AD1457', fontcolor='white', fontsize='12')
            r3.node('PS', '13. PluginSystem\n插件系统\n动态加载扩展', fillcolor='#AD1457', fontcolor='white', fontsize='12')

    # 自我改进核心区
    with dot.subgraph(name='cluster_self_improve') as si:
        si.attr(style='filled', color='#FFEBEE', label='【阶段5核心: 自我改进】', pencolor='#C62828', **CLUSTER_STYLE)
        si.node('SICore', '三大能力支柱\n\n1. 代码内省: SSR读取分析自身\n2. 代码自修复: SIM备份+修复+自检\n3. 能力扩展: PluginSystem动态加载\n\nAgent闭环进化: 自查 -> 自修复 -> 自扩展', fillcolor='#C62828', fontcolor='white', fontsize='14')

    # 工具结果
    dot.node('Result', '工具结果数据类\n  - success: bool\n  - content: str\n  - error_message: str\n  - raw_output: Any\n  - metadata: 附加数据', fillcolor='#006064', fontcolor='white', fontsize='16')

    # 消费者
    dot.node('AE', '代理引擎\nMVP模式', fillcolor='#1B5E20', fontcolor='white', fontsize='20')
    dot.node('LLM', 'Claude大语言模型\nJSON Schema工具定义\n13个工具自动发现', fillcolor='#004D40', fontcolor='white', fontsize='16')

    # 安全特性
    with dot.subgraph(name='cluster_safety') as s:
        s.attr(style='filled', color='#FFEBEE', label='【安全机制】', pencolor='#C62828', **CLUSTER_STYLE)
        s.node('S1', '危险操作过滤\nrm -rf/format/sudo/drop table\n黑名单+白名单双检', fillcolor='#EF5350', fontcolor='white', fontsize='14')
        s.node('S2', '路径验证\n防止目录穿越\n路径白名单\n相对路径校验', fillcolor='#EF5350', fontcolor='white', fontsize='14')
        s.node('S3', '插件安全\nBaseTool子类强制验证\n插件目录隔离\n无eval执行', fillcolor='#E53935', fontcolor='white', fontsize='14')

    # 连接线
    dot.edge('AbsFC', 'Base', color='#E65100', **EDGE_STYLE)
    # 13个工具连接
    dot.edge('Base', 'FR', color='#4A148C', **EDGE_STYLE)
    dot.edge('Base', 'FW', color='#4A148C', **EDGE_STYLE)
    dot.edge('Base', 'EC', color='#4A148C', **EDGE_STYLE)
    dot.edge('Base', 'CS', color='#4A148C', **EDGE_STYLE)
    dot.edge('Base', 'CA', color='#4A148C', **EDGE_STYLE)
    dot.edge('Base', 'LL', color='#4A148C', **EDGE_STYLE)
    dot.edge('Base', 'Git', color='#4A148C', **EDGE_STYLE)
    dot.edge('Base', 'SA', color='#4A148C', **EDGE_STYLE)
    dot.edge('Base', 'CR', color='#4A148C', **EDGE_STYLE)
    dot.edge('Base', 'ASAN', color='#4A148C', **EDGE_STYLE)
    dot.edge('Base', 'SSR', color='#AD1457', **EDGE_STYLE)
    dot.edge('Base', 'SIM', color='#AD1457', **EDGE_STYLE)
    dot.edge('Base', 'PS', color='#AD1457', **EDGE_STYLE)
    # 自我改进核心区连接
    dot.edge('SSR', 'SICore', color='#C62828', **EDGE_STYLE)
    dot.edge('SIM', 'SICore', color='#C62828', **EDGE_STYLE)
    dot.edge('PS', 'SICore', color='#C62828', **EDGE_STYLE)
    # 注册表连接
    dot.edge('FR', 'Registry', color='#3E2723', **EDGE_STYLE)
    dot.edge('FW', 'Registry', color='#3E2723', **EDGE_STYLE)
    dot.edge('EC', 'Registry', color='#3E2723', **EDGE_STYLE)
    dot.edge('CS', 'Registry', color='#3E2723', **EDGE_STYLE)
    dot.edge('CA', 'Registry', color='#3E2723', **EDGE_STYLE)
    dot.edge('LL', 'Registry', color='#3E2723', **EDGE_STYLE)
    dot.edge('Git', 'Registry', color='#3E2723', **EDGE_STYLE)
    dot.edge('SA', 'Registry', color='#3E2723', **EDGE_STYLE)
    dot.edge('CR', 'Registry', color='#3E2723', **EDGE_STYLE)
    dot.edge('ASAN', 'Registry', color='#3E2723', **EDGE_STYLE)
    dot.edge('SSR', 'Registry', color='#3E2723', **EDGE_STYLE)
    dot.edge('SIM', 'Registry', color='#3E2723', **EDGE_STYLE)
    dot.edge('PS', 'Registry', color='#3E2723', **EDGE_STYLE)
    # 结果连接
    dot.edge('Registry', 'Result', color='#006064', **EDGE_STYLE)
    dot.edge('Result', 'AE', color='#1B5E20', **EDGE_STYLE)
    dot.edge('AE', 'Registry', color='#3E2723', penwidth='5', **EDGE_STYLE)
    dot.edge('Registry', 'LLM', color='#004D40', **EDGE_STYLE)
    dot.edge('LLM', 'AE', color='#004D40', **EDGE_STYLE)
    # 安全连接
    dot.edge('EC', 'S1', style='dashed', color='#C62828', **EDGE_STYLE)
    dot.edge('FW', 'S2', style='dashed', color='#C62828', **EDGE_STYLE)
    dot.edge('PS', 'S3', style='dashed', color='#C62828', **EDGE_STYLE)

    dot.render(cleanup=True)
    print("[OK] 工具系统架构图 v1.5 已生成")


def create_plan_act_reflect_flowchart_v15():
    """执行流程图 v1.5 - 添加自我改进分支"""
    dot = Digraph(
        'Plan_Act_Reflect_v1.5',
        filename='./docs/Plan_Act_Reflect_Flowchart_v1.5',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='30,34', rankdir='TB', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    dot.node('Start', '开始\n接收用户查询', fillcolor='#1B5E20', fontcolor='white', fontsize='22')

    with dot.subgraph(name='cluster_plan') as c:
        c.attr(style='filled', color='#E3F2FD', label='【规划阶段】', pencolor='#0D47A1', **CLUSTER_STYLE)
        c.node('P1', '是否简单任务?', shape='diamond', fillcolor='#FFC107', fontsize='19', penwidth='5')
        c.node('P2', '生成简单计划\n最多2个步骤', fillcolor='#64B5F6', fontsize='17')
        c.node('P3', '启发式任务分解\n分析任务类型', fillcolor='#64B5F6', fontsize='17')
        c.node('P4', '可行性评估\n危险操作检测\n步骤连续检查\n目标清晰性检查', fillcolor='#64B5F6', fontsize='17')
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
        c.node('A3', '构建增强提示词\n记忆增强\n对话历史\n工具定义', fillcolor='#81C784', fontsize='17')
        c.node('A4', '调用大模型API', fillcolor='#81C784', fontsize='17')
        c.node('A5', '有工具调用?', shape='diamond', fillcolor='#FFC107', fontsize='19', penwidth='5')
        c.node('A6', '执行工具\n通过注册表\nFunctionCall', fillcolor='#81C784', fontsize='17')
        c.node('A7', '执行成功?', shape='diamond', fillcolor='#FFC107', fontsize='19', penwidth='5')
        c.node('A8', '收集执行结果', fillcolor='#81C784', fontsize='17')
        c.node('A9', '标记步骤完成', fillcolor='#81C784', fontsize='17')
        c.node('A10', '本步完成?', shape='diamond', fillcolor='#FFC107', fontsize='19', penwidth='5')
        # 新增: 自我改进分支
        c.node('AS1', '自我修复?\n检测到代码问题', shape='diamond', fillcolor='#FF7043', fontsize='17', penwidth='5')
        c.node('AS2', '调用SelfImproveTool\n创建备份\n应用修复\n验证修复', fillcolor='#EF5350', fontcolor='white', fontsize='16')

    with dot.subgraph(name='cluster_reflect') as c:
        c.attr(style='filled', color='#FFF8E1', label='【反思阶段】', pencolor='#E65100', **CLUSTER_STYLE)
        c.node('R1', '分析执行结果', fillcolor='#FFB74D', fontsize='17')
        c.node('R2', '错误模式匹配\n文件不存在\n权限不足\n超时\n语法错误\n命令不存在', fillcolor='#FFB74D', fontsize='17')
        c.node('R3', '提取经验教训', fillcolor='#FFB74D', fontsize='17')
        c.node('R4', '持久化到记忆', fillcolor='#FFB74D', fontsize='17')
        c.node('R5', '需要调整计划?', shape='diamond', fillcolor='#FFC107', fontsize='19', penwidth='5')
        c.node('R6', '插入新步骤\n或修改计划', fillcolor='#FFB74D', fontsize='17')
        c.node('R7', '计数器+1', fillcolor='#FFB74D', fontsize='17')
        # 新增: 自我改进反思
        c.node('RS1', '需要自改进?\nAgent代码缺陷检测', shape='diamond', fillcolor='#FF8F00', fontsize='17', penwidth='5')
        c.node('RS2', '触发自我改进流程\nSSR读取源码分析\nSIM应用修复\n验证修复效果', fillcolor='#FF6F00', fontcolor='white', fontsize='15')

    with dot.subgraph(name='cluster_finalize') as c:
        c.attr(style='filled', color='#F3E5F5', label='【终态阶段】', pencolor='#4A148C', **CLUSTER_STYLE)
        c.node('F1', '全部完成?\n或达最大迭代?', shape='diamond', fillcolor='#FFC107', fontsize='19', penwidth='5')
        c.node('F2', '生成执行总结\n步骤数/成功率/详情\n含自改进记录', fillcolor='#AB47BC', fontcolor='white', fontsize='17')
        c.node('F3', '生成最终答案\n通过大模型', fillcolor='#BA68C8', fontcolor='white', fontsize='17')
        c.node('F4', '执行完成\n返回结果\n含自改进摘要', fillcolor='#4A148C', fontcolor='white', fontsize='22')

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
    dot.edge('A9', 'AS1', color='#1B5E20', **EDGE_STYLE)
    dot.edge('A10', 'R1', color='#E65100', **EDGE_STYLE)
    # 自我修复分支
    dot.edge('AS1', 'AS2', color='#C62828', label='是', **EDGE_STYLE)
    dot.edge('AS1', 'R1', color='#E65100', label='否', **EDGE_STYLE)
    dot.edge('AS2', 'R1', color='#C62828', **EDGE_STYLE)
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
    print("[OK] 执行流程图 v1.5 已生成")


def create_data_flow_diagram_v15():
    """完整数据流图 v1.5 - 添加自我改进数据流"""
    dot = Digraph(
        'Data_Flow_v1.5',
        filename='./docs/Complete_Data_Flow_v1.5',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='34,26', rankdir='LR', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    with dot.subgraph(name='cluster_input') as c:
        c.attr(style='filled', color='#FFF3E0', label='【输入层】', pencolor='#E65100', **CLUSTER_STYLE)
        c.node('User', '用户输入\n查询字符串\n自我改进指令', fillcolor='#E64A19', fontcolor='white', fontsize='21')

    with dot.subgraph(name='cluster_plan_data') as c:
        c.attr(style='filled', color='#E3F2FD', label='【规划数据流】', pencolor='#0D47A1', **CLUSTER_STYLE)
        c.node('Query', '查询分析\n模式检测\n复杂度评估\n任务分类\n自改进识别', fillcolor='#64B5F6', fontsize='16')
        c.node('PlanData', '计划对象\n  - original_query: 原始查询\n  - steps: 步骤列表\n  - overall_goal: 总体目标\n  - complexity: 复杂度\n  - feasibility_score: 可行性\n  - current_step: 当前步骤\n  - self_improve: 自改进标记', fillcolor='#0D47A1', fontcolor='white', fontsize='13')
        c.node('StepData', '计划步骤\n  - step_number: 步骤编号\n  - description: 步骤描述\n  - tool_needed: 需要工具\n  - expected_output: 预期输出\n  - importance: 重要性\n  - completed: 已完成\n  - success: 成功\n  - result_summary: 结果摘要\n  - error_message: 错误信息', fillcolor='#1A237E', fontcolor='white', fontsize='12')

    with dot.subgraph(name='cluster_act_data') as c:
        c.attr(style='filled', color='#E8F5E9', label='【执行数据流】', pencolor='#1B5E20', **CLUSTER_STYLE)
        c.node('Prompt', '增强提示词\n  - 系统提示\n  - 记忆增强\n  - 对话历史\n  - 工具定义(13个)', fillcolor='#81C784', fontsize='15')
        c.node('LLMReq', 'LLM请求\n  - model: 模型\n  - max_tokens: 最大Token\n  - system: 系统提示\n  - messages: 消息列表\n  - tools: 工具定义', fillcolor='#43A047', fontcolor='white', fontsize='14')
        c.node('LLMResp', 'LLM响应\n  - 内容块\n  - Thinking块\n  - 工具调用块', fillcolor='#2E7D32', fontcolor='white', fontsize='14')
        c.node('ToolCall', '工具调用\n  - id: 标识\n  - name: 工具名\n  - input: 输入参数', fillcolor='#1B5E20', fontcolor='white', fontsize='14')
        c.node('FCData', 'FunctionCall执行\n  - Parameters: 参数校验\n  - do_call(): 实际执行\n  - ExecutionResult: 结果\n  - call_chain: 调用链\n  - duration_ms: 耗时', fillcolor='#004D40', fontcolor='white', fontsize='13')

    with dot.subgraph(name='cluster_self_data') as c:
        c.attr(style='filled', color='#FFEBEE', label='【自我改进数据流】', pencolor='#C62828', **CLUSTER_STYLE)
        c.node('SSRData', 'SSR读取结果\n  - file_path: 文件路径\n  - line_count: 行数\n  - content: 源码内容\n  - structure: 结构信息', fillcolor='#EF5350', fontcolor='white', fontsize='13')
        c.node('SIMData', 'SIM修复数据\n  - backup_name: 备份名称\n  - target_file: 目标文件\n  - new_content: 新内容\n  - description: 修复描述\n  - test_results: 自检结果', fillcolor='#E53935', fontcolor='white', fontsize='13')
        c.node('PluginData', '插件系统数据\n  - plugin_path: 插件路径\n  - plugin_name: 插件名\n  - template_type: 模板类型\n  - loaded_tools: 已加载工具', fillcolor='#C62828', fontcolor='white', fontsize='13')
        c.node('BackupData', '备份元数据\n  - timestamp: 时间戳\n  - info.txt: 描述文件\n  - backup_dir: 备份目录\n  - pre_restore_safety: 安全备份', fillcolor='#B71C1C', fontcolor='white', fontsize='13')

    with dot.subgraph(name='cluster_memory_data') as c:
        c.attr(style='filled', color='#FFF8E1', label='【记忆数据流】', pencolor='#E65100', **CLUSTER_STYLE)
        c.node('MsgHist', '消息历史\n列表[字典]\n  - role: 角色\n  - content: 内容', fillcolor='#FFCA28', fontsize='14')
        c.node('MemItem', '记忆项\n  - content: 内容\n  - memory_type: 类型\n  - importance: 重要性\n  - timestamp: 时间戳\n  - metadata: 元数据\n  - self_improve_record', fillcolor='#FFA000', fontsize='14')
        c.node('ErrItem', '错误记录\n  - type: 错误类型\n  - description: 描述\n  - correction: 修正\n  - context: 上下文\n  - severity: 严重度\n  - occurrences: 次数\n  - self_fix_applied', fillcolor='#FF6F00', fontcolor='white', fontsize='13')

    with dot.subgraph(name='cluster_reflect_data') as c:
        c.attr(style='filled', color='#F3E5F5', label='【反思数据流】', pencolor='#4A148C', **CLUSTER_STYLE)
        c.node('Reflection', '反思对象\n  - success: 是否成功\n  - goal_achieved: 目标达成\n  - issues_found: 发现问题\n  - improvements: 改进建议\n  - need_plan_adjustment: 需调整\n  - adjustment_suggestion: 调整建议\n  - lessons_learned: 经验教训\n  - confidence_score: 信心评分\n  - self_improve_needed', fillcolor='#AB47BC', fontcolor='white', fontsize='12')
        c.node('Summary', '执行总结\n  - 总步骤数\n  - 已完成数\n  - 成功数\n  - 成功率\n  - 详细步骤\n  - 自我改进记录', fillcolor='#7B1FA2', fontcolor='white', fontsize='14')

    with dot.subgraph(name='cluster_output') as c:
        c.attr(style='filled', color='#E0F7FA', label='【输出层】', pencolor='#006064', **CLUSTER_STYLE)
        c.node('Output', '最终答案\n清理响应\n纯文本输出\n格式化展示\n含自改进报告', fillcolor='#006064', fontcolor='white', fontsize='19')

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
    dot.edge('PlanData', 'Summary', color='#4A148C', penwidth='5', **EDGE_STYLE)
    dot.edge('Summary', 'Output', color='#006064', penwidth='6', **EDGE_STYLE)
    dot.edge('LLMResp', 'Output', color='#006064', penwidth='6', **EDGE_STYLE)

    dot.render(cleanup=True)
    print("[OK] 完整数据流图 v1.5 已生成")


if __name__ == '__main__':
    print("=" * 70)
    print("DevPal Agent v1.5 - 架构图生成器")
    print("=" * 70)
    print("主要更新 (阶段5 - 自我改进系统):")
    print("  1. 系统架构图添加 自我改进层 + Web界面 + 13个工具")
    print("  2. 新增 SelfImprove_System_Architecture 架构图")
    print("  3. 工具系统架构图更新为 13个工具 + 3大能力支柱")
    print("  4. 执行流程图添加 自我修复分支 + 自改进反思")
    print("  5. 数据流图添加 自我改进数据流 (SSR/SIM/Plugin/Backup)")
    print("  6. 所有图版本号升级为 v1.5")
    print("=" * 70)

    create_architecture_overview_v15()
    create_self_improve_architecture_v15()
    create_tool_system_diagram_v15()
    create_plan_act_reflect_flowchart_v15()
    create_data_flow_diagram_v15()

    print("=" * 70)
    print("所有架构图已成功生成到 ./docs/ 目录!")
    print("=" * 70)
    print("\n生成的文件列表 (v1.5):")
    print("  1. DevPal_Architecture_Overview_v1.5.png")
    print("  2. SelfImprove_System_Architecture_v1.5.png    [新]")
    print("  3. Tool_System_Architecture_v1.5.png")
    print("  4. Plan_Act_Reflect_Flowchart_v1.5.png")
    print("  5. Complete_Data_Flow_v1.5.png")
    print("\n字体: 微软雅黑 Microsoft YaHei")
    print("分辨率: 600 DPI 超高清")
