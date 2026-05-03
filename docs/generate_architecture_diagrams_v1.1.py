# -*- coding: utf-8 -*-
"""
DevPal Agent v1.1 - 架构图生成器
更新内容：添加 AbstractFunctionCall 抽象函数调用模块 + LinkedList 链表工具
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


def create_architecture_overview():
    """系统整体架构图 v1.1 - 新增 FunctionCall 层"""
    dot = Digraph(
        'DevPal_Architecture_v1.1',
        filename='./docs/DevPal_Architecture_Overview_v1.1',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='30,24', rankdir='TB', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    # 用户层
    with dot.subgraph(name='cluster_user') as c:
        c.attr(style='filled', color='#FFF3E0', label='【用户层】', **CLUSTER_STYLE)
        c.node('User', '用户\n输入查询', fillcolor='#E64A19', fontcolor='white', fontsize='20')
        c.node('CLI', '命令行\n交互式模式', fillcolor='#FF5722', fontcolor='white', fontsize='18')

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

    # 工具层 - 新增 FunctionCall 抽象层
    with dot.subgraph(name='cluster_tools') as c:
        c.attr(style='filled', color='#F3E5F5', label='【工具系统层】', **CLUSTER_STYLE)
        c.node('ToolReg', '工具注册表\n统一调度', fillcolor='#4A148C', fontcolor='white', **HEADER_STYLE)

        # FunctionCall 抽象层（新增）
        with c.subgraph(name='cluster_func_call') as fc:
            fc.attr(style='filled', color='#E1BEE7', label='抽象FunctionCall层', fontsize='18')
            fc.node('AbsFC', 'AbstractFunctionCall\n泛型基类\n参数校验\n执行追踪\n错误处理', fillcolor='#7B1FA2', fontcolor='white', fontsize='15')
            fc.node('FCtx', 'FunctionCallContext\n调用链\n变量存储\n计时统计', fillcolor='#8E24AA', fontcolor='white', fontsize='14')
            fc.node('FChain', 'FunctionChain\n链式执行\n结果传递\n参数合并', fillcolor='#9C27B0', fontcolor='white', fontsize='14')
            fc.node('ExecRes', 'ExecutionResult\nsuccess/data\nerror/duration\nmetadata', fillcolor='#BA68C8', fontcolor='white', fontsize='13')

        # 具体工具
        with c.subgraph(name='cluster_concrete') as tc:
            tc.attr(rank='same')
            tc.node('FR', '文件\n读取', fillcolor='#6A1B9A', fontcolor='white', fontsize='14')
            tc.node('FW', '文件\n写入', fillcolor='#6A1B9A', fontcolor='white', fontsize='14')
            tc.node('EC', '命令\n执行', fillcolor='#6A1B9A', fontcolor='white', fontsize='14')
            tc.node('CS', '代码\n搜索', fillcolor='#6A1B9A', fontcolor='white', fontsize='14')
            tc.node('CA', '编译\n分析', fillcolor='#6A1B9A', fontcolor='white', fontsize='14')
            tc.node('LL', '链表\n工具', fillcolor='#6A1B9A', fontcolor='white', fontsize='14')

    # LLM层
    with dot.subgraph(name='cluster_llm') as c:
        c.attr(style='filled', color='#E0F7FA', label='【大模型层】', **CLUSTER_STYLE)
        c.node('LLM', 'Claude大模型\n兼容火山引擎\nThinking支持', fillcolor='#006064', fontcolor='white', fontsize='17')

    # 连接线
    dot.edge('User', 'CLI', color='#E64A19', **EDGE_STYLE)
    dot.edge('CLI', 'Engine', color='#E64A19', **EDGE_STYLE)
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
    dot.edge('AbsFC', 'FR', color='#7B1FA2', **EDGE_STYLE)
    dot.edge('AbsFC', 'FW', color='#7B1FA2', **EDGE_STYLE)
    dot.edge('AbsFC', 'EC', color='#7B1FA2', **EDGE_STYLE)
    dot.edge('AbsFC', 'CS', color='#7B1FA2', **EDGE_STYLE)
    dot.edge('AbsFC', 'CA', color='#7B1FA2', **EDGE_STYLE)
    dot.edge('AbsFC', 'LL', color='#7B1FA2', **EDGE_STYLE)
    dot.edge('FR', 'Engine', color='#7B1FA2', style='dashed', **EDGE_STYLE)
    dot.edge('FW', 'Engine', color='#7B1FA2', style='dashed', **EDGE_STYLE)
    dot.edge('EC', 'Engine', color='#7B1FA2', style='dashed', **EDGE_STYLE)
    dot.edge('CS', 'Engine', color='#7B1FA2', style='dashed', **EDGE_STYLE)
    dot.edge('CA', 'Engine', color='#7B1FA2', style='dashed', **EDGE_STYLE)
    dot.edge('LL', 'Engine', color='#7B1FA2', style='dashed', **EDGE_STYLE)
    dot.edge('Engine', 'Reflection', color='#2E7D32', **EDGE_STYLE)
    dot.edge('Reflection', 'PatternMatch', color='#2E7D32', **EDGE_STYLE)
    dot.edge('PatternMatch', 'Lessons', color='#2E7D32', **EDGE_STYLE)
    dot.edge('Reflection', 'PlanAdjust', color='#2E7D32', style='dashed', **EDGE_STYLE)
    dot.edge('Engine', 'LLM', color='#006064', **EDGE_STYLE)
    dot.edge('LLM', 'Engine', color='#006064', **EDGE_STYLE)
    dot.edge('Engine', 'CLI', color='#1B5E20', **{**EDGE_STYLE, 'penwidth': '6'})

    dot.render(cleanup=True)
    print("[OK] 系统整体架构图 v1.1 已生成")


def create_function_call_architecture():
    """新增: FunctionCall 抽象函数调用架构图"""
    dot = Digraph(
        'FunctionCall_Architecture_v1.1',
        filename='./docs/FunctionCall_Architecture_v1.1',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='30,26', rankdir='TB', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    # 核心抽象层
    with dot.subgraph(name='cluster_core') as c:
        c.attr(style='filled', color='#E3F2FD', label='【核心抽象层】', pencolor='#0D47A1', **CLUSTER_STYLE)
        c.node('AbsFC', 'AbstractFunctionCall[T, R]\n\n- name: 函数名称\n- description: 描述\n- validate_params(): 参数校验\n- do_call(): 实际执行\n- __call__(): 统一入口\n- chain(): 链式调用', fillcolor='#0D47A1', fontcolor='white', fontsize='16')
        c.node('Params', 'Parameters\nPydantic 基类\n类型安全\n自动验证', fillcolor='#1565C0', fontcolor='white', fontsize='15')

    # 上下文和结果
    with dot.subgraph(name='cluster_context') as c:
        c.attr(style='filled', color='#FFF8E1', label='【上下文与结果】', pencolor='#E65100', **CLUSTER_STYLE)
        c.node('FCtx', 'FunctionCallContext\n\n- call_chain: 调用链\n- variables: 变量存储\n- add_call(): 记录调用\n- get_total_duration(): 统计耗时', fillcolor='#E65100', fontcolor='white', fontsize='15')
        c.node('ExecRes', 'ExecutionResult\n\n- success: bool\n- data: Any\n- error_message: str\n- execution_id: UUID\n- timestamp: datetime\n- duration_ms: float\n- metadata: 元数据', fillcolor='#FF6F00', fontcolor='white', fontsize='14')

    # 函数链
    with dot.subgraph(name='cluster_chain') as c:
        c.attr(style='filled', color='#E8F5E9', label='【函数链】', pencolor='#1B5E20', **CLUSTER_STYLE)
        c.node('FChain', 'FunctionChain\n\n- functions: 函数列表\n- execute(): 串行执行\n- 初始参数 + 结果合并\n- 失败中断链条\n- get_summary(): 执行摘要', fillcolor='#1B5E20', fontcolor='white', fontsize='15')

    # 具体实现 - LinkedList 12个FunctionCall
    with dot.subgraph(name='cluster_linkedlist') as c:
        c.attr(style='filled', color='#F3E5F5', label='【LinkedList 具体实现 (12个)】', pencolor='#4A148C', **CLUSTER_STYLE)

        with c.subgraph(name='cluster_create') as r1:
            r1.attr(rank='same')
            r1.node('Create', 'CreateLinkedList\n创建链表', fillcolor='#7B1FA2', fontcolor='white', fontsize='13')
            r1.node('Append', 'AppendNode\n尾部添加', fillcolor='#7B1FA2', fontcolor='white', fontsize='13')
            r1.node('Prepend', 'PrependNode\n头部添加', fillcolor='#7B1FA2', fontcolor='white', fontsize='13')
            r1.node('Insert', 'InsertNode\n指定位置插入', fillcolor='#7B1FA2', fontcolor='white', fontsize='13')

        with c.subgraph(name='cluster_delete') as r2:
            r2.attr(rank='same')
            r2.node('DelAt', 'DeleteNodeAtIndex\n按索引删除', fillcolor='#8E24AA', fontcolor='white', fontsize='13')
            r2.node('DelVal', 'DeleteNodeByValue\n按值删除', fillcolor='#8E24AA', fontcolor='white', fontsize='13')
            r2.node('Update', 'UpdateNode\n更新节点值', fillcolor='#8E24AA', fontcolor='white', fontsize='13')
            r2.node('Get', 'GetNode\n获取节点值', fillcolor='#8E24AA', fontcolor='white', fontsize='13')

        with c.subgraph(name='cluster_query') as r3:
            r3.attr(rank='same')
            r3.node('Find', 'FindNode\n查找节点', fillcolor='#9C27B0', fontcolor='white', fontsize='13')
            r3.node('GetList', 'GetLinkedList\n获取完整链表', fillcolor='#9C27B0', fontcolor='white', fontsize='13')
            r3.node('Clear', 'ClearLinkedList\n清空链表', fillcolor='#9C27B0', fontcolor='white', fontsize='13')
            r3.node('DelList', 'DeleteLinkedList\n删除链表', fillcolor='#9C27B0', fontcolor='white', fontsize='13')

        c.node('ListAll', 'ListAllLinkedLists\n列出所有链表', fillcolor='#4A148C', fontcolor='white', fontsize='13')

    # LinkedList 数据结构
    with dot.subgraph(name='cluster_ds') as c:
        c.attr(style='filled', color='#E0F7FA', label='【链表数据结构】', pencolor='#006064', **CLUSTER_STYLE)
        c.node('ListNode', 'ListNode\n- value: Any\n- next: Optional[ListNode]\n- to_dict(): 序列化', fillcolor='#006064', fontcolor='white', fontsize='14')
        c.node('LinkedList', 'LinkedList\n- name: str\n- head: Optional[ListNode]\n- size: int\n- append/prepend/insert\n- delete_at/delete_value\n- update_at/get_at/find\n- to_list/to_dict/clear', fillcolor='#00838F', fontcolor='white', fontsize='14')

    # 全局注册表
    with dot.subgraph(name='cluster_reg') as c:
        c.attr(style='filled', color='#FFF3E0', label='【全局注册表】', pencolor='#E64A19', **CLUSTER_STYLE)
        c.node('GlobalReg', '_linked_lists: Dict[str, LinkedList]\n\n- get_linked_list(name)\n- create_linked_list(name)\n- delete_linked_list(name)\n- get_all_linked_lists()', fillcolor='#E64A19', fontcolor='white', fontsize='14')

    # 集成到 Tool 系统
    with dot.subgraph(name='cluster_tool') as c:
        c.attr(style='filled', color='#FCE4EC', label='【Tool系统集成】', pencolor='#C2185B', **CLUSTER_STYLE)
        c.node('LLTool', 'LinkedListTool(BaseTool)\n\n- operation: create/append/prepend\n  insert/delete_at/delete_value\n  update/get/find/get_list\n  clear/delete_list/list_all\n- list_name: 链表名称\n- index/value/new_value', fillcolor='#C2185B', fontcolor='white', fontsize='14')

    # 连接线
    dot.edge('AbsFC', 'Params', color='#0D47A1', **EDGE_STYLE)
    dot.edge('AbsFC', 'FCtx', color='#0D47A1', **EDGE_STYLE)
    dot.edge('AbsFC', 'ExecRes', color='#0D47A1', **EDGE_STYLE)
    dot.edge('AbsFC', 'FChain', color='#0D47A1', **EDGE_STYLE)

    # 抽象到具体
    dot.edge('AbsFC', 'Create', color='#4A148C', **EDGE_STYLE)
    dot.edge('AbsFC', 'Append', color='#4A148C', **EDGE_STYLE)
    dot.edge('AbsFC', 'Prepend', color='#4A148C', **EDGE_STYLE)
    dot.edge('AbsFC', 'Insert', color='#4A148C', **EDGE_STYLE)
    dot.edge('AbsFC', 'DelAt', color='#4A148C', **EDGE_STYLE)
    dot.edge('AbsFC', 'DelVal', color='#4A148C', **EDGE_STYLE)
    dot.edge('AbsFC', 'Update', color='#4A148C', **EDGE_STYLE)
    dot.edge('AbsFC', 'Get', color='#4A148C', **EDGE_STYLE)
    dot.edge('AbsFC', 'Find', color='#4A148C', **EDGE_STYLE)
    dot.edge('AbsFC', 'GetList', color='#4A148C', **EDGE_STYLE)
    dot.edge('AbsFC', 'Clear', color='#4A148C', **EDGE_STYLE)
    dot.edge('AbsFC', 'DelList', color='#4A148C', **EDGE_STYLE)
    dot.edge('AbsFC', 'ListAll', color='#4A148C', **EDGE_STYLE)

    # 链表数据结构
    dot.edge('Create', 'LinkedList', color='#006064', **EDGE_STYLE)
    dot.edge('Append', 'LinkedList', color='#006064', **EDGE_STYLE)
    dot.edge('LinkedList', 'ListNode', color='#006064', **EDGE_STYLE)
    dot.edge('LinkedList', 'GlobalReg', color='#E64A19', **EDGE_STYLE)

    # Tool集成
    dot.edge('Create', 'LLTool', color='#C2185B', **EDGE_STYLE)
    dot.edge('Append', 'LLTool', color='#C2185B', **EDGE_STYLE)
    dot.edge('GlobalReg', 'LLTool', color='#C2185B', **EDGE_STYLE)

    dot.render(cleanup=True)
    print("[OK] FunctionCall 架构图已生成")


def create_tool_system_diagram_v11():
    """工具系统架构图 v1.1 - 更新添加 LinkedListTool"""
    dot = Digraph(
        'Tool_System_v1.1',
        filename='./docs/Tool_System_Architecture_v1.1',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='30,26', rankdir='TB', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    # 两层架构：AbstractFunctionCall + BaseTool
    dot.node('AbsFC', 'AbstractFunctionCall\n泛型基类\n参数校验\n执行追踪\n错误处理', fillcolor='#4A148C', fontcolor='white', **HEADER_STYLE)

    dot.node('Base', 'BaseTool抽象基类\n  - name: 工具名称\n  - description: 描述\n  - parameters: 参数\n  - execute(): 执行\n  - validate_params()', fillcolor='#E65100', fontcolor='white', **HEADER_STYLE)

    # 工具注册表
    dot.node('Registry', '工具注册表\n  - tools: 工具字典\n  - register(): 注册\n  - execute_tool(): 执行\n  - get_tool_descriptions()', fillcolor='#3E2723', fontcolor='white', **HEADER_STYLE)

    # 具体工具 - 新增 LinkedListTool
    with dot.subgraph(name='cluster_tools') as c:
        c.attr(style='filled', color='#F3E5F5', label='【具体工具】', pencolor='#4A148C', **CLUSTER_STYLE)

        with c.subgraph(name='cluster_row1') as r1:
            r1.attr(rank='same')
            r1.node('FR', '文件读取器\n只读安全\n参数: path', fillcolor='#7B1FA2', fontcolor='white', fontsize='14')
            r1.node('FW', '文件写入器\n路径校验\n防目录穿越', fillcolor='#7B1FA2', fontcolor='white', fontsize='14')
            r1.node('EC', '命令执行器\n安全过滤\n白+黑名单', fillcolor='#7B1FA2', fontcolor='white', fontsize='14')

        with c.subgraph(name='cluster_row2') as r2:
            r2.attr(rank='same')
            r2.node('CS', '代码搜索器\nGrep模式\n文件过滤', fillcolor='#7B1FA2', fontcolor='white', fontsize='14')
            r2.node('CA', '编译分析器\n错误提取分类', fillcolor='#7B1FA2', fontcolor='white', fontsize='14')
            r2.node('LL', 'LinkedListTool\n链表操作工具\n12种操作', fillcolor='#4A148C', fontcolor='white', fontsize='14')

    # 工具结果
    dot.node('Result', '工具结果数据类\n  - success: bool\n  - content: str\n  - error_message: str\n  - raw_output: Any', fillcolor='#006064', fontcolor='white', fontsize='16')

    # 消费者
    dot.node('AE', '代理引擎', fillcolor='#1B5E20', fontcolor='white', fontsize='20')
    dot.node('LLM', 'Claude大语言模型\nJSON Schema工具定义', fillcolor='#004D40', fontcolor='white', fontsize='16')

    # 安全特性
    with dot.subgraph(name='cluster_safety') as s:
        s.attr(style='filled', color='#FFEBEE', label='【安全机制】', pencolor='#C62828', **CLUSTER_STYLE)
        s.node('S1', '危险操作过滤\nrm -rf/format/sudo/drop table\n黑名单+白名单双检', fillcolor='#EF5350', fontcolor='white', fontsize='14')
        s.node('S2', '路径验证\n防止目录穿越\n路径白名单', fillcolor='#EF5350', fontcolor='white', fontsize='14')

    # 连接线
    dot.edge('AbsFC', 'Base', color='#E65100', **EDGE_STYLE)
    dot.edge('Base', 'FR', color='#4A148C', **EDGE_STYLE)
    dot.edge('Base', 'FW', color='#4A148C', **EDGE_STYLE)
    dot.edge('Base', 'EC', color='#4A148C', **EDGE_STYLE)
    dot.edge('Base', 'CS', color='#4A148C', **EDGE_STYLE)
    dot.edge('Base', 'CA', color='#4A148C', **EDGE_STYLE)
    dot.edge('Base', 'LL', color='#4A148C', **EDGE_STYLE)

    dot.edge('FR', 'Registry', color='#3E2723', **EDGE_STYLE)
    dot.edge('FW', 'Registry', color='#3E2723', **EDGE_STYLE)
    dot.edge('EC', 'Registry', color='#3E2723', **EDGE_STYLE)
    dot.edge('CS', 'Registry', color='#3E2723', **EDGE_STYLE)
    dot.edge('CA', 'Registry', color='#3E2723', **EDGE_STYLE)
    dot.edge('LL', 'Registry', color='#3E2723', **EDGE_STYLE)

    dot.edge('Registry', 'Result', color='#006064', **EDGE_STYLE)
    dot.edge('Result', 'AE', color='#1B5E20', **EDGE_STYLE)
    dot.edge('AE', 'Registry', color='#3E2723', penwidth='5', **EDGE_STYLE)
    dot.edge('Registry', 'LLM', color='#004D40', **EDGE_STYLE)
    dot.edge('LLM', 'AE', color='#004D40', **EDGE_STYLE)

    dot.edge('EC', 'S1', style='dashed', color='#C62828', **EDGE_STYLE)
    dot.edge('FW', 'S2', style='dashed', color='#C62828', **EDGE_STYLE)

    dot.render(cleanup=True)
    print("[OK] 工具系统架构图 v1.1 已生成")


def create_plan_act_reflect_flowchart_v11():
    """执行流程图 v1.1 - 保持不变，版本号更新"""
    dot = Digraph(
        'Plan_Act_Reflect_v1.1',
        filename='./docs/Plan_Act_Reflect_Flowchart_v1.1',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='28,32', rankdir='TB', **GRAPH_STYLE)
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

    with dot.subgraph(name='cluster_reflect') as c:
        c.attr(style='filled', color='#FFF8E1', label='【反思阶段】', pencolor='#E65100', **CLUSTER_STYLE)
        c.node('R1', '分析执行结果', fillcolor='#FFB74D', fontsize='17')
        c.node('R2', '错误模式匹配\n文件不存在\n权限不足\n超时\n语法错误\n命令不存在', fillcolor='#FFB74D', fontsize='17')
        c.node('R3', '提取经验教训', fillcolor='#FFB74D', fontsize='17')
        c.node('R4', '持久化到记忆', fillcolor='#FFB74D', fontsize='17')
        c.node('R5', '需要调整计划?', shape='diamond', fillcolor='#FFC107', fontsize='19', penwidth='5')
        c.node('R6', '插入新步骤\n或修改计划', fillcolor='#FFB74D', fontsize='17')
        c.node('R7', '计数器+1', fillcolor='#FFB74D', fontsize='17')

    with dot.subgraph(name='cluster_finalize') as c:
        c.attr(style='filled', color='#F3E5F5', label='【终态阶段】', pencolor='#4A148C', **CLUSTER_STYLE)
        c.node('F1', '全部完成?\n或达最大迭代?', shape='diamond', fillcolor='#FFC107', fontsize='19', penwidth='5')
        c.node('F2', '生成执行总结\n步骤数/成功率/详情', fillcolor='#BA68C8', fontcolor='white', fontsize='17')
        c.node('F3', '生成最终答案\n通过大模型', fillcolor='#BA68C8', fontcolor='white', fontsize='17')
        c.node('F4', '执行完成\n返回结果', fillcolor='#4A148C', fontcolor='white', fontsize='22')

    dot.edge('Start', 'P1', color='#1B5E20', penwidth='6', **EDGE_STYLE)
    dot.edge('P5', 'A1', color='#0D47A1', **EDGE_STYLE)
    dot.edge('A1', 'A2', color='#1B5E20', **EDGE_STYLE)
    dot.edge('A2', 'A3', color='#1B5E20', **EDGE_STYLE)
    dot.edge('A3', 'A4', color='#1B5E20', **EDGE_STYLE)
    dot.edge('A4', 'A5', color='#1B5E20', **EDGE_STYLE)
    dot.edge('A5', 'A10', color='#1B5E20', **EDGE_STYLE)
    dot.edge('A5', 'A6', color='#1B5E20', **EDGE_STYLE)
    dot.edge('A6', 'A7', color='#1B5E20', **EDGE_STYLE)
    dot.edge('A7', 'A8', color='#1B5E20', **EDGE_STYLE)
    dot.edge('A8', 'A9', color='#1B5E20', **EDGE_STYLE)
    dot.edge('A9', 'R1', color='#E65100', **EDGE_STYLE)
    dot.edge('A10', 'R1', color='#E65100', **EDGE_STYLE)
    dot.edge('R1', 'R2', color='#E65100', **EDGE_STYLE)
    dot.edge('R2', 'R3', color='#E65100', **EDGE_STYLE)
    dot.edge('R3', 'R4', color='#E65100', **EDGE_STYLE)
    dot.edge('R4', 'R5', color='#E65100', **EDGE_STYLE)
    dot.edge('R5', 'R6', color='#C62828', **EDGE_STYLE)
    dot.edge('R5', 'R7', color='#E65100', **EDGE_STYLE)
    dot.edge('R6', 'R7', color='#E65100', **EDGE_STYLE)
    dot.edge('R7', 'F1', color='#4A148C', **EDGE_STYLE)
    dot.edge('F1', 'A2', color='#0D47A1', style='dashed', **EDGE_STYLE)
    dot.edge('F1', 'F2', color='#4A148C', **EDGE_STYLE)
    dot.edge('F2', 'F3', color='#4A148C', **EDGE_STYLE)
    dot.edge('F3', 'F4', color='#4A148C', penwidth='6', **EDGE_STYLE)

    dot.render(cleanup=True)
    print("[OK] 执行流程图 v1.1 已生成")


def create_memory_system_diagram_v11():
    """记忆系统架构图 v1.1 - 版本号更新"""
    dot = Digraph(
        'Memory_System_v1.1',
        filename='./docs/Memory_System_Architecture_v1.1',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='28,24', rankdir='TB', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    dot.node('MM', '记忆管理器\n统一访问入口', fillcolor='#E65100', fontcolor='white', **HEADER_STYLE)

    with dot.subgraph(name='cluster_stm') as c:
        c.attr(style='filled', color='#E3F2FD', label='【短期记忆】', pencolor='#0D47A1', **CLUSTER_STYLE)
        c.node('STM', '短期记忆管理器\n对话上下文', fillcolor='#0D47A1', fontcolor='white', fontsize='18')
        c.node('STM1', '核心API\n- add_user\n- add_assistant\n- add_tool_results\n- get_messages', fillcolor='#64B5F6', fontsize='15')
        c.node('STM2', '高级功能\n- Token估算\n- 智能截断\n- 对话摘要', fillcolor='#64B5F6', fontsize='15')
        c.node('SF1', '滑动窗口\n最少保留6条消息', fillcolor='#90CAF9', fontsize='15')
        c.node('SF2', '大模型格式兼容\n标准消息格式', fillcolor='#90CAF9', fontsize='15')
        c.node('SF3', '工具调用跟踪\n完整上下文', fillcolor='#90CAF9', fontsize='15')
        c.edge('STM', 'STM1', color='#0D47A1', **EDGE_STYLE)
        c.edge('STM', 'STM2', color='#0D47A1', **EDGE_STYLE)
        c.edge('STM1', 'SF1', color='#0D47A1', **EDGE_STYLE)
        c.edge('STM1', 'SF2', color='#0D47A1', **EDGE_STYLE)
        c.edge('STM2', 'SF3', color='#0D47A1', **EDGE_STYLE)

    with dot.subgraph(name='cluster_ltm') as c:
        c.attr(style='filled', color='#E8F5E9', label='【长期记忆】', pencolor='#1B5E20', **CLUSTER_STYLE)
        c.node('LTM', '长期记忆\n持久化JSON存储\n./data/long_term_memory.json', fillcolor='#1B5E20', fontcolor='white', fontsize='18')
        c.node('UP', '用户偏好\n用户设置\n执行偏好', fillcolor='#81C784', fontsize='15')
        c.node('EXP', '任务经验\n成功记录\n失败教训\n步骤学习', fillcolor='#81C784', fontsize='15')
        c.node('KNOW', '代码知识\n模式学习\n最佳实践\n方案库', fillcolor='#81C784', fontsize='15')
        c.node('PAT', '行为模式\n趋势统计\n常用模式', fillcolor='#81C784', fontsize='15')
        c.node('LTM1', '检索算法\n关键词+时间+重要性加权', fillcolor='#4CAF50', fontsize='15')
        c.node('LTM2', '相似度评分\nScore = 重叠*0.5 + 新鲜度*0.3 + 重要性*0.2', fillcolor='#4CAF50', fontsize='15')
        c.node('LTM3', '提示词注入\n增强大模型上下文', fillcolor='#4CAF50', fontsize='15')
        c.edge('LTM', 'UP', color='#1B5E20', **EDGE_STYLE)
        c.edge('LTM', 'EXP', color='#1B5E20', **EDGE_STYLE)
        c.edge('LTM', 'KNOW', color='#1B5E20', **EDGE_STYLE)
        c.edge('LTM', 'PAT', color='#1B5E20', **EDGE_STYLE)
        c.edge('LTM', 'LTM1', color='#1B5E20', **EDGE_STYLE)
        c.edge('LTM1', 'LTM2', color='#1B5E20', **EDGE_STYLE)
        c.edge('LTM2', 'LTM3', color='#1B5E20', **EDGE_STYLE)

    with dot.subgraph(name='cluster_em') as c:
        c.attr(style='filled', color='#FFEBEE', label='【错误记忆】', pencolor='#C62828', **CLUSTER_STYLE)
        c.node('EM', '错误记忆\n持久化JSON存储\n./data/error_memory.json', fillcolor='#C62828', fontcolor='white', fontsize='18')
        c.node('T1', '工具调用错误\n执行失败', fillcolor='#EF9A9A', fontsize='14')
        c.node('T2', '逻辑错误\n推理失败', fillcolor='#EF9A9A', fontsize='14')
        c.node('T3', '幻觉错误\n虚构信息', fillcolor='#EF9A9A', fontsize='14')
        c.node('T4', '参数错误\n无效参数', fillcolor='#EF9A9A', fontsize='14')
        c.node('T5', '格式错误\n格式问题', fillcolor='#EF9A9A', fontsize='14')
        c.node('T6', '安全违规\n危险操作', fillcolor='#EF9A9A', fontsize='14')
        c.node('EM1', '错误模式匹配\n上下文相似度检测', fillcolor='#E53935', fontcolor='white', fontsize='15')
        c.node('EM2', '警告提示生成\n自动注入系统提示', fillcolor='#E53935', fontcolor='white', fontsize='15')
        c.node('EM3', '出现次数跟踪\n严重程度1-10级', fillcolor='#E53935', fontcolor='white', fontsize='15')
        c.edge('EM', 'T1', color='#C62828', **EDGE_STYLE)
        c.edge('EM', 'T2', color='#C62828', **EDGE_STYLE)
        c.edge('EM', 'T3', color='#C62828', **EDGE_STYLE)
        c.edge('EM', 'T4', color='#C62828', **EDGE_STYLE)
        c.edge('EM', 'T5', color='#C62828', **EDGE_STYLE)
        c.edge('EM', 'T6', color='#C62828', **EDGE_STYLE)
        c.edge('EM', 'EM1', color='#C62828', **EDGE_STYLE)
        c.edge('EM1', 'EM2', color='#C62828', **EDGE_STYLE)
        c.edge('EM', 'EM3', color='#C62828', **EDGE_STYLE)

    dot.edge('MM', 'STM', color='#0D47A1', penwidth='5', **EDGE_STYLE)
    dot.edge('MM', 'LTM', color='#1B5E20', penwidth='5', **EDGE_STYLE)
    dot.edge('MM', 'EM', color='#C62828', penwidth='5', **EDGE_STYLE)

    dot.node('AE', '代理引擎', fillcolor='#1B5E20', fontcolor='white', fontsize='20')
    dot.edge('AE', 'MM', color='#1B5E20', **EDGE_STYLE)
    dot.edge('MM', 'AE', color='#1B5E20', **EDGE_STYLE)

    dot.node('SP', '增强系统提示词\n记忆上下文\n错误警告\n历史经验', fillcolor='#4A148C', fontcolor='white', fontsize='17')
    dot.edge('MM', 'SP', color='#4A148C', **EDGE_STYLE)
    dot.edge('SP', 'LLM', color='#4A148C', **EDGE_STYLE)
    dot.node('LLM', 'Claude大语言模型', fillcolor='#006064', fontcolor='white', fontsize='18')

    dot.render(cleanup=True)
    print("[OK] 记忆系统架构图 v1.1 已生成")


def create_data_flow_diagram_v11():
    """完整数据流图 v1.1 - 添加 FunctionCall 数据流"""
    dot = Digraph(
        'Data_Flow_v1.1',
        filename='./docs/Complete_Data_Flow_v1.1',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='32,22', rankdir='LR', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    with dot.subgraph(name='cluster_input') as c:
        c.attr(style='filled', color='#FFF3E0', label='【输入层】', pencolor='#E65100', **CLUSTER_STYLE)
        c.node('User', '用户输入\n查询字符串', fillcolor='#E64A19', fontcolor='white', fontsize='21')

    with dot.subgraph(name='cluster_plan_data') as c:
        c.attr(style='filled', color='#E3F2FD', label='【规划数据流】', pencolor='#0D47A1', **CLUSTER_STYLE)
        c.node('Query', '查询分析\n模式检测\n复杂度评估\n任务分类', fillcolor='#64B5F6', fontsize='16')
        c.node('PlanData', '计划对象\n  - original_query: 原始查询\n  - steps: 步骤列表\n  - overall_goal: 总体目标\n  - complexity: 复杂度\n  - feasibility_score: 可行性\n  - current_step: 当前步骤', fillcolor='#0D47A1', fontcolor='white', fontsize='14')
        c.node('StepData', '计划步骤\n  - step_number: 步骤编号\n  - description: 步骤描述\n  - tool_needed: 需要工具\n  - expected_output: 预期输出\n  - importance: 重要性\n  - completed: 已完成\n  - success: 成功\n  - result_summary: 结果摘要\n  - error_message: 错误信息', fillcolor='#1A237E', fontcolor='white', fontsize='13')

    with dot.subgraph(name='cluster_act_data') as c:
        c.attr(style='filled', color='#E8F5E9', label='【执行数据流】', pencolor='#1B5E20', **CLUSTER_STYLE)
        c.node('Prompt', '增强提示词\n  - 系统提示\n  - 记忆增强\n  - 对话历史\n  - 工具定义', fillcolor='#81C784', fontsize='15')
        c.node('LLMReq', 'LLM请求\n  - model: 模型\n  - max_tokens: 最大Token\n  - system: 系统提示\n  - messages: 消息列表\n  - tools: 工具定义', fillcolor='#43A047', fontcolor='white', fontsize='14')
        c.node('LLMResp', 'LLM响应\n  - 内容块\n  - Thinking块\n  - 工具调用块', fillcolor='#2E7D32', fontcolor='white', fontsize='14')
        c.node('ToolCall', '工具调用\n  - id: 标识\n  - name: 工具名\n  - input: 输入参数', fillcolor='#1B5E20', fontcolor='white', fontsize='14')
        # 新增 FunctionCall 数据
        c.node('FCData', 'FunctionCall执行\n  - Parameters: 参数校验\n  - do_call(): 实际执行\n  - ExecutionResult: 结果\n  - call_chain: 调用链\n  - duration_ms: 耗时', fillcolor='#004D40', fontcolor='white', fontsize='13')

    with dot.subgraph(name='cluster_memory_data') as c:
        c.attr(style='filled', color='#FFF8E1', label='【记忆数据流】', pencolor='#E65100', **CLUSTER_STYLE)
        c.node('MsgHist', '消息历史\n列表[字典]\n  - role: 角色\n  - content: 内容', fillcolor='#FFCA28', fontsize='14')
        c.node('MemItem', '记忆项\n  - content: 内容\n  - memory_type: 类型\n  - importance: 重要性\n  - timestamp: 时间戳\n  - metadata: 元数据', fillcolor='#FFA000', fontsize='14')
        c.node('ErrItem', '错误记录\n  - type: 错误类型\n  - description: 描述\n  - correction: 修正\n  - context: 上下文\n  - severity: 严重度\n  - occurrences: 次数', fillcolor='#FF6F00', fontcolor='white', fontsize='13')

    with dot.subgraph(name='cluster_reflect_data') as c:
        c.attr(style='filled', color='#F3E5F5', label='【反思数据流】', pencolor='#4A148C', **CLUSTER_STYLE)
        c.node('Reflection', '反思对象\n  - success: 是否成功\n  - goal_achieved: 目标达成\n  - issues_found: 发现问题\n  - improvements: 改进建议\n  - need_plan_adjustment: 需调整\n  - adjustment_suggestion: 调整建议\n  - lessons_learned: 经验教训\n  - confidence_score: 信心评分', fillcolor='#AB47BC', fontcolor='white', fontsize='13')
        c.node('Summary', '执行总结\n  - 总步骤数\n  - 已完成数\n  - 成功数\n  - 成功率\n  - 详细步骤', fillcolor='#7B1FA2', fontcolor='white', fontsize='14')

    with dot.subgraph(name='cluster_output') as c:
        c.attr(style='filled', color='#E0F7FA', label='【输出层】', pencolor='#006064', **CLUSTER_STYLE)
        c.node('Output', '最终答案\n清理响应\n纯文本输出\n格式化展示', fillcolor='#006064', fontcolor='white', fontsize='19')

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
    dot.edge('FCData', 'StepData', color='#1B5E20', penwidth='4', **EDGE_STYLE)
    dot.edge('StepData', 'Reflection', color='#4A148C', penwidth='5', **EDGE_STYLE)
    dot.edge('Reflection', 'MemItem', color='#E65100', penwidth='4', style='dashed', **EDGE_STYLE)
    dot.edge('Reflection', 'ErrItem', color='#E65100', penwidth='4', style='dashed', **EDGE_STYLE)
    dot.edge('Reflection', 'PlanData', color='#0D47A1', penwidth='4', style='dashed', **EDGE_STYLE)
    dot.edge('LLMResp', 'MsgHist', color='#E65100', penwidth='4', **EDGE_STYLE)
    dot.edge('ToolCall', 'MsgHist', color='#E65100', penwidth='4', **EDGE_STYLE)
    dot.edge('FCData', 'MsgHist', color='#E65100', penwidth='4', **EDGE_STYLE)
    dot.edge('PlanData', 'Summary', color='#4A148C', penwidth='5', **EDGE_STYLE)
    dot.edge('Summary', 'Output', color='#006064', penwidth='6', **EDGE_STYLE)
    dot.edge('LLMResp', 'Output', color='#006064', penwidth='6', **EDGE_STYLE)

    dot.render(cleanup=True)
    print("[OK] 完整数据流图 v1.1 已生成")


if __name__ == '__main__':
    print("=" * 70)
    print("DevPal Agent v1.1 - 架构图生成器")
    print("=" * 70)
    print("主要更新:")
    print("  1. 新增 AbstractFunctionCall 架构图")
    print("  2. 系统架构图添加 FunctionCall 层")
    print("  3. 工具系统架构图添加 LinkedListTool")
    print("  4. 数据流图添加 FunctionCall 数据")
    print("  5. 所有图版本号升级为 v1.1")
    print("=" * 70)

    create_architecture_overview()
    create_function_call_architecture()
    create_tool_system_diagram_v11()
    create_plan_act_reflect_flowchart_v11()
    create_memory_system_diagram_v11()
    create_data_flow_diagram_v11()

    print("=" * 70)
    print("所有架构图已成功生成到 ./docs/ 目录!")
    print("=" * 70)
    print("\n生成的文件列表 (v1.1):")
    print("  1. DevPal_Architecture_Overview_v1.1.png")
    print("  2. FunctionCall_Architecture_v1.1.png    [新]")
    print("  3. Tool_System_Architecture_v1.1.png")
    print("  4. Plan_Act_Reflect_Flowchart_v1.1.png")
    print("  5. Memory_System_Architecture_v1.1.png")
    print("  6. Complete_Data_Flow_v1.1.png")
    print("\n字体: 微软雅黑 Microsoft YaHei")
    print("分辨率: 600 DPI 超高清")
