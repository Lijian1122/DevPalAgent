# -*- coding: utf-8 -*-
"""
DevPal Agent - 防幻觉系统架构图生成器
生成 4 层防御体系的流程图和时序图
"""
from graphviz import Digraph
import os

os.makedirs('./docs', exist_ok=True)

# 全局样式
COMMON_STYLE = {
    'fontname': 'Microsoft YaHei',
    'fontsize': '11',
}

NODE_STYLE = {
    'shape': 'box',
    'style': 'filled,rounded',
    'fontname': 'Microsoft YaHei',
    'fontsize': '12',
}

EDGE_STYLE = {
    'fontname': 'Microsoft YaHei',
    'fontsize': '10',
}


# ======================================================================
# 图 1: 防幻觉系统整体架构图
# ======================================================================
def create_architecture_overview():
    dot = Digraph(
        'Anti_Hallucination_Architecture',
        filename='./docs/Anti_Hallucination_Architecture',
        format='png',
        encoding='utf-8'
    )
    dot.attr(size='18,12', rankdir='TB', dpi='300')
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    # 输入层
    with dot.subgraph(name='cluster_input') as c:
        c.attr(style='filled', color='#FFF3E0', label='Input Layer', pencolor='#E65100', fontname='Microsoft YaHei', fontsize='14')
        c.node('user_query', 'User Query\n用户查询', fillcolor='#FFE0B2', fontsize='14')
        c.node('llm_output', 'LLM Output\n工具调用/计划', fillcolor='#FFE0B2', fontsize='14')

    # 4 层防御架构
    with dot.subgraph(name='cluster_defense') as c:
        c.attr(style='filled', color='#E3F2FD', label='4-Layer Defense System\n四层防御体系', pencolor='#1565C0', fontname='Microsoft YaHei', fontsize='14')

        # Layer 1: 规划层
        with c.subgraph(name='cluster_layer1') as l1:
            l1.attr(style='filled', color='#BBDEFB', label='Layer 1: Planning Phase\n第一层: 规划阶段防御', pencolor='#0D47A1', fontname='Microsoft YaHei', fontsize='12')
            l1.node('planner_check', 'Planner.evaluate_feasibility()\n'
                                        '- 检测计划中不存在的工具\n'
                                        '- 检测步骤描述含糊不清\n'
                                        '- 检测可行性评分过高风险',
                                        fillcolor='#64B5F6', fontcolor='white')

        # Layer 2: 执行前
        with c.subgraph(name='cluster_layer2') as l2:
            l2.attr(style='filled', color='#C8E6C9', label='Layer 2: Pre-Execution\n第二层: 执行前防御', pencolor='#1B5E20', fontname='Microsoft YaHei', fontsize='12')
            l2.node('engine_check', 'AgentEngine._check_tool_call_hallucination()\n'
                                        '- 检测工具是否存在\n'
                                        '- 检测参数是否为 None/空\n'
                                        '- 检测高风险操作\n'
                                        '- 检测参数过长异常',
                                        fillcolor='#81C784', fontcolor='white')

        # Layer 3: 执行层
        with c.subgraph(name='cluster_layer3') as l3:
            l3.attr(style='filled', color='#FFF9C4', label='Layer 3: Execution Phase\n第三层: 执行层防御', pencolor='#F57F17', fontname='Microsoft YaHei', fontsize='12')
            l3.node('param_fix', '_intelligent_param_fix()\n'
                                      '- 智能修复参数\n'
                                      '- 链表操作自动补全\n'
                                      '- 提取用户查询中的真实参数',
                                      fillcolor='#FFF176')

        # Layer 4: 反思层
        with c.subgraph(name='cluster_layer4') as l4:
            l4.attr(style='filled', color='#F8BBD9', label='Layer 4: Reflection Phase\n第四层: 反思阶段防御', pencolor='#880E4F', fontname='Microsoft YaHei', fontsize='12')
            l4.node('reflector_check', 'Reflector.detect_hallucination_from_result()\n'
                                           '- 检测执行结果中的幻觉信号\n'
                                           '- 检测连续失败幻觉循环\n'
                                           '- 记录错误模式到记忆系统',
                                           fillcolor='#F06292', fontcolor='white')

    # 输出层
    with dot.subgraph(name='cluster_output') as c:
        c.attr(style='filled', color='#E0F7FA', label='Output Layer\n输出层', pencolor='#006064', fontname='Microsoft YaHei', fontsize='14')
        c.node('blocked', '[BLOCK]\n阻止执行\n高风险幻觉', fillcolor='#EF5350', fontcolor='white', fontsize='13')
        c.node('warning', '[WARN]\n发出警告\n需要人工确认', fillcolor='#FFCA28', fontsize='13')
        c.node('proceed', '[OK]\n正常执行\n但持续监控', fillcolor='#66BB6A', fontcolor='white', fontsize='13')
        c.node('fixed', '[FIX]\n自动修复\n参数修复后执行', fillcolor='#42A5F5', fontcolor='white', fontsize='13')

    # 核心检测器
    with dot.subgraph(name='cluster_detector') as c:
        c.attr(style='filled', color='#F3E5F5', label='Core Detector\n核心检测器', pencolor='#4A148C', fontname='Microsoft YaHei', fontsize='14')
        c.node('detector', 'HallucinationDetectorTool\n'
                              'check_type = all/tool_call/plan/code/fact\n'
                              '- 工具存在性检测\n'
                              '- 参数空值检测\n'
                              '- 事实性陈述验证\n'
                              '- 代码幻觉检测',
                              fillcolor='#AB47BC', fontcolor='white', fontsize='13')

    # 连接线
    dot.edge('user_query', 'planner_check', label='1. Generate Plan', penwidth='2')
    dot.edge('llm_output', 'engine_check', label='2. Before Tool Call', penwidth='2')

    dot.edge('planner_check', 'detector', style='dashed', label='Call Detector')
    dot.edge('engine_check', 'detector', style='dashed', label='Call Detector')

    dot.edge('engine_check', 'param_fix', label='Parameter Error', penwidth='2')
    dot.edge('param_fix', 'proceed', label='Fixed', penwidth='2')

    dot.edge('planner_check', 'warning', label='Issues Found', penwidth='2')
    dot.edge('engine_check', 'blocked', label='High Risk', penwidth='2')

    dot.edge('proceed', 'reflector_check', label='3. Post Execution', penwidth='2')
    dot.edge('reflector_check', 'warning', label='Post Hallucination', penwidth='2')

    dot.render(cleanup=True)
    print("[OK] 图 1: 防幻觉系统整体架构图 已生成")


# ======================================================================
# 图 2: 防幻觉时序图 - 完整执行流程
# ======================================================================
def create_timing_diagram():
    dot = Digraph(
        'Anti_Hallucination_Timing',
        filename='./docs/Anti_Hallucination_Timing_Flow',
        format='png',
        encoding='utf-8'
    )
    dot.attr(size='20,14', rankdir='LR', dpi='300', ranksep='1.2', nodesep='0.6')
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    # ========== 泳道：参与者 ==========
    # 用户
    dot.node('user', 'User\n用户', fillcolor='#E3F2FD', fontsize='13', penwidth='3', width='2')

    # AgentEngine
    dot.node('agent', 'AgentEngine\n代理引擎', fillcolor='#BBDEFB', fontsize='13', penwidth='3', width='2')

    # Planner
    dot.node('planner', 'Planner\n规划器', fillcolor='#90CAF9', fontsize='13', penwidth='3', width='2')

    # Detector
    dot.node('detector', 'HallucinationDetector\n幻觉检测器', fillcolor='#64B5F6', fontsize='13', penwidth='3', width='2')

    # ToolRegistry
    dot.node('registry', 'ToolRegistry\n工具注册表', fillcolor='#2196F3', fontcolor='white', fontsize='13', penwidth='3', width='2')

    # Reflector
    dot.node('reflector', 'Reflector\n反思器', fillcolor='#42A5F5', fontcolor='white', fontsize='13', penwidth='3', width='2')

    # ========== 时序步骤 ==========
    # 步骤 1: 用户发起查询
    dot.node('s1', 'S1: Query', shape='note', fillcolor='#F5F5F5', fontsize='10')
    dot.edge('user', 'agent', label='1. User Query', penwidth='2')

    # 步骤 2: Planner 生成计划
    dot.node('s2', 'S2: Plan Gen', shape='note', fillcolor='#F5F5F5', fontsize='10')
    dot.edge('agent', 'planner', label='2. Call Planner', penwidth='2')

    # 步骤 3: 第一次幻觉检测 (计划阶段)
    dot.node('s3', 'S3: Plan Check', shape='note', fillcolor='#F5F5F5', fontsize='10')
    dot.edge('planner', 'detector', label='3. Plan Hallucination Check', penwidth='2')

    # 步骤 4: 检测结果返回
    dot.node('s4', 'S4: Result', shape='note', fillcolor='#F5F5F5', fontsize='10')
    dot.edge('detector', 'planner', label='4. Return Result', penwidth='2')

    # 分支判断 - 高风险则阻止
    dot.node('block_node', '[High Risk]\nBlock Execution', fillcolor='#EF5350', fontcolor='white', width='2')
    dot.edge('planner', 'block_node', label='Severe Hallucination', penwidth='2', color='#C62828')

    # 步骤 5: LLM 生成工具调用
    dot.node('s5', 'S5: Tool Call Gen', shape='note', fillcolor='#F5F5F5', fontsize='10')
    dot.edge('planner', 'agent', label='5. Next Step', penwidth='2')

    # 步骤 6: 第二次幻觉检测 (执行前)
    dot.node('s6', 'S6: Pre-Exec Check', shape='note', fillcolor='#F5F5F5', fontsize='10')
    dot.edge('agent', 'detector', label='6. Pre-Exec Check', penwidth='2')

    # 分支：参数修复
    dot.node('fix_node', '[Param Fix]\nIntelligent Fix', fillcolor='#FFB74D', width='2')
    dot.edge('detector', 'fix_node', label='Param Needs Fix', penwidth='2', color='#F57C00')

    # 步骤 7: 工具执行
    dot.node('s7', 'S7: Execute', shape='note', fillcolor='#F5F5F5', fontsize='10')
    dot.edge('fix_node', 'registry', label='7. Execute Fixed', penwidth='2')
    dot.edge('detector', 'registry', label='7. Execute Normal', penwidth='2', color='#2E7D32')

    # 步骤 8: 结果返回 + 反思
    dot.node('s8', 'S8: Reflection', shape='note', fillcolor='#F5F5F5', fontsize='10')
    dot.edge('registry', 'reflector', label='8. Result Return', penwidth='2')

    # 步骤 9: 事后幻觉检测
    dot.node('s9', 'S9: Post Check', shape='note', fillcolor='#F5F5F5', fontsize='10')
    dot.edge('reflector', 'detector', label='9. Post Hallucination Check', penwidth='2')

    # 步骤 10: 记录错误模式
    dot.node('s10', 'S10: Record', shape='note', fillcolor='#F5F5F5', fontsize='10')
    dot.edge('detector', 'reflector', label='10. Return Result', penwidth='2')
    dot.edge('reflector', 'reflector', label='11. Record Pattern', penwidth='2')

    # 步骤 11: 返回最终结果
    dot.node('s11', 'S11: Response', shape='note', fillcolor='#F5F5F5', fontsize='10')
    dot.edge('reflector', 'user', label='12. Final Response', penwidth='2')

    dot.render(cleanup=True)
    print("[OK] 图 2: 防幻觉完整时序图 已生成")


# ======================================================================
# 图 3: 幻觉检测类型详解图
# ======================================================================
def create_detection_types():
    dot = Digraph(
        'Hallucination_Types',
        filename='./docs/Hallucination_Detection_Types',
        format='png',
        encoding='utf-8'
    )
    dot.attr(size='16,12', rankdir='TB', dpi='300')
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    # 根节点
    dot.node('root', 'HallucinationDetectorTool\n幻觉检测工具', fillcolor='#1565C0', fontcolor='white', fontsize='16', penwidth='4')

    # 4 种检测类型
    detection_types = [
        ('tool_call', 'tool_call\n工具调用检测', '#E53935', [
            ('tc1', 'Tool Exists Check\n工具存在性检测\n比对 ToolRegistry 列表'),
            ('tc2', 'Null Param Check\n参数空值检测\nNone/null/空字符串'),
            ('tc3', 'High Risk Op Check\n高风险操作检测\ndelete/remove/drop/format'),
            ('tc4', 'Param Too Long Check\n参数过长检测\n可能是 LLM 输出混乱'),
        ]),
        ('plan', 'plan\n执行计划检测', '#F57C00', [
            ('p1', 'Non-existent Tool Ref\n不存在工具引用检测\n计划步骤中的 tool_needed'),
            ('p2', 'Vague Desc Check\n步骤描述模糊检测\n描述过短/语义含糊'),
            ('p3', 'Overconfidence Check\n可行性评分过高检测\n过度自信风险'),
        ]),
        ('code', 'code\n代码幻觉检测', '#388E3C', [
            ('c1', 'TODO/FIXME Marker\nTODO/FIXME 标记检测\n未完成的代码实现'),
            ('c2', 'Placeholder Var Check\n占位符变量名检测\nyour_/my_/test_ 前缀'),
            ('c3', 'Non-existent Func Ref\n引用函数存在性检测\n原文件中不存在的函数'),
        ]),
        ('fact', 'fact\n事实性陈述检测', '#7B1FA2', [
            ('f1', 'Research Ref Check\n研究引用检测\n未引用具体来源'),
            ('f2', 'Precise Number Check\n具体数字过度检测\n多个精确百分比/数字'),
            ('f3', 'Paper Ref Check\n论文/文献引用检测\n可能编造的文献'),
        ]),
    ]

    # 创建类型节点和子节点
    for type_id, label, color, subitems in detection_types:
        dot.node(type_id, label, fillcolor=color, fontcolor='white', fontsize='14', penwidth='3')
        dot.edge('root', type_id, penwidth='2')

        # 创建子项节点
        for sub_id, sub_label in subitems:
            dot.node(sub_id, sub_label, fillcolor=f'{color}22', color=color, penwidth='2', fontsize='11')
            dot.edge(type_id, sub_id, penwidth='1.5')

    # 风险等级说明
    with dot.subgraph(name='cluster_risk') as c:
        c.attr(style='filled', color='#F5F5F5', label='Risk Levels\n风险等级说明', pencolor='#424242', fontname='Microsoft YaHei', fontsize='12')
        c.node('risk_high', 'HIGH\n高风险\n立即阻止执行\n需要人工确认', fillcolor='#EF5350', fontcolor='white')
        c.node('risk_medium', 'MEDIUM\n中风险\n发出警告\n继续执行但监控', fillcolor='#FFCA28')
        c.node('risk_low', 'LOW\n低风险\n正常执行\n记录日志', fillcolor='#81C784')

    dot.render(cleanup=True)
    print("[OK] 图 3: 幻觉检测类型详解图 已生成")


# ======================================================================
# 图 4: 参数智能修复流程图
# ======================================================================
def create_param_fix_flow():
    dot = Digraph(
        'Param_Fix_Flow',
        filename='./docs/Parameter_Intelligent_Fix_Flow',
        format='png',
        encoding='utf-8'
    )
    dot.attr(size='16,10', rankdir='LR', dpi='300')
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    # 开始
    dot.node('start', 'START\nLLM Generates Tool Call\nLLM生成工具调用', fillcolor='#E3F2FD', fontsize='13')

    # 检测阶段
    with dot.subgraph(name='cluster_detect') as c:
        c.attr(style='filled', color='#FFF3E0', label='Detection Phase\n幻觉检测阶段', pencolor='#E65100', fontname='Microsoft YaHei', fontsize='12')
        c.node('check1', 'Tool Exists?\n工具存在吗?', fillcolor='#FFE0B2')
        c.node('check2', 'Params Complete?\n参数是否完整?', fillcolor='#FFE0B2')
        c.node('check3', 'Linked List Op?\n是否链表操作?', fillcolor='#FFE0B2')

    # 修复分支
    dot.node('block', '[BLOCK]\n阻止执行\n工具不存在', fillcolor='#EF5350', fontcolor='white')

    with dot.subgraph(name='cluster_fix') as c:
        c.attr(style='filled', color='#C8E6C9', label='Fix Branch\n智能修复分支', pencolor='#2E7D32', fontname='Microsoft YaHei', fontsize='12')
        c.node('fix_name', 'Unify List Name\n强制统一 list_name\n= demo_list', fillcolor='#81C784')
        c.node('fix_op', 'Correct Operation\n根据步骤描述修正 operation\n创建 -> create\n删除 -> delete_at/delete_value\n显示 -> get_list', fillcolor='#81C784')
        c.node('fix_value', 'Extract Real Params\n从用户查询中提取真实参数\n正则匹配数字/文件名/路径', fillcolor='#81C784')

    # 执行分支
    dot.node('execute', 'EXECUTE\n执行工具调用', fillcolor='#4CAF50', fontcolor='white', fontsize='13')
    dot.node('fail', 'FAIL\n参数仍异常\n返回错误', fillcolor='#F44336', fontcolor='white')

    # 连接线
    dot.edge('start', 'check1', penwidth='2')
    dot.edge('check1', 'block', label='Not Exist\n不存在', penwidth='2', color='#C62828')
    dot.edge('check1', 'check2', label='Exists\n存在', penwidth='2')

    dot.edge('check2', 'check3', label='Complete\n完整', penwidth='2')
    dot.edge('check2', 'fix_value', label='Param Missing/None\n参数缺失/空', penwidth='2', color='#F57C00')

    dot.edge('check3', 'fix_name', label='Linked List\n是链表', penwidth='2')
    dot.edge('check3', 'execute', label='Not Linked List\n直接执行', penwidth='2', color='#2E7D32')

    dot.edge('fix_name', 'fix_op', penwidth='2')
    dot.edge('fix_op', 'fix_value', penwidth='2')

    dot.edge('fix_value', 'check2', label='Re-Check\n重新校验', penwidth='2', color='#1976D2')

    dot.edge('fix_value', 'fail', label='Fix Failed\n修复失败', penwidth='2', color='#C62828')
    dot.edge('fix_value', 'execute', label='Fix Success\n修复成功', penwidth='2', color='#2E7D32')

    dot.render(cleanup=True)
    print("[OK] 图 4: 参数智能修复流程图 已生成")


# ======================================================================
# 图 5: 记忆系统与幻觉反馈闭环
# ======================================================================
def create_memory_feedback_loop():
    dot = Digraph(
        'Memory_Feedback_Loop',
        filename='./docs/Hallucination_Memory_Feedback_Loop',
        format='png',
        encoding='utf-8'
    )
    dot.attr(size='16,12', rankdir='TB', dpi='300')
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    # 主循环
    dot.node('query', 'User Query\n用户查询', fillcolor='#E3F2FD', fontsize='13')
    dot.node('plan', 'Planner Generate Plan\nPlanner 生成计划', fillcolor='#BBDEFB')
    dot.node('detect', 'Hallucination Detection\n幻觉检测', fillcolor='#90CAF9')
    dot.node('execute', 'Tool Execution\n工具执行', fillcolor='#64B5F6', fontcolor='white')
    dot.node('reflect', 'Post Execution Reflection\n执行后反思', fillcolor='#42A5F5', fontcolor='white')
    dot.node('record', 'Record Hallucination Pattern\n记录幻觉模式到错误记忆库', fillcolor='#1E88E5', fontcolor='white')
    dot.node('memory', 'Memory System\n记忆系统\n短期+长期+错误记忆', fillcolor='#0D47A1', fontcolor='white', fontsize='13')
    dot.node('prompt', 'Inject into System Prompt\n注入记忆到 System Prompt\n下次查询时预警', fillcolor='#1565C0', fontcolor='white')
    dot.node('next_query', 'Next Similar Query\n下次同类查询\nLLM 已有经验', fillcolor='#283593', fontcolor='white')

    # 循环箭头
    dot.edge('query', 'plan', penwidth='2', label='Step 1')
    dot.edge('plan', 'detect', penwidth='2', label='Step 2')
    dot.edge('detect', 'execute', penwidth='2', label='Step 3: Pass Check')
    dot.edge('execute', 'reflect', penwidth='2', label='Step 4: Result Return')
    dot.edge('reflect', 'record', penwidth='2', label='Step 5: Found Issue')
    dot.edge('record', 'memory', penwidth='2', label='Step 6: Store')
    dot.edge('memory', 'prompt', penwidth='2', label='Step 7: Memory Injection')
    dot.edge('prompt', 'next_query', penwidth='2', label='Step 8: Learned Query')
    dot.edge('next_query', 'detect', style='dashed', label='Feedback Loop\nDetection Accuracy Improved', penwidth='2', color='#4CAF50')

    # 错误模式示例
    with dot.subgraph(name='cluster_patterns') as c:
        c.attr(style='filled', color='#FFF3E0', label='Hallucination Pattern Examples\n已记录的幻觉模式示例', pencolor='#E65100', fontname='Microsoft YaHei', fontsize='12')
        c.node('p1', 'Pattern 1: Non-existent Tool\n模式1: 编造不存在的工具\ndebugger_tool, analyzer_tool, etc.')
        c.node('p2', 'Pattern 2: String "None" Param\n模式2: 参数值为字符串 None\n"None" 而非真实参数值')
        c.node('p3', 'Pattern 3: Chain Call Hallucination\n模式3: 链式调用幻觉\n调用A工具后必然编造B工具结果')
        c.node('p4', 'Pattern 4: Overconfidence\n模式4: 特定查询过度自信\n文件内容分析类查询容易编造结果')

    dot.edge('memory', 'p1', style='dashed')
    dot.edge('memory', 'p2', style='dashed')
    dot.edge('memory', 'p3', style='dashed')
    dot.edge('memory', 'p4', style='dashed')

    dot.render(cleanup=True)
    print("[OK] 图 5: 记忆系统与幻觉反馈闭环图 已生成")


# ======================================================================
# 主函数
# ======================================================================
if __name__ == '__main__':
    print("=" * 80)
    print("DevPal Agent - 防幻觉系统架构图生成器")
    print("=" * 80)

    create_architecture_overview()
    create_timing_diagram()
    create_detection_types()
    create_param_fix_flow()
    create_memory_feedback_loop()

    print("=" * 80)
    print("所有架构图生成完成!")
    print("=" * 80)
    print("\n生成的文件:")
    print("  1. Anti_Hallucination_Architecture.png       - 防幻觉系统整体架构")
    print("  2. Anti_Hallucination_Timing_Flow.png         - 防幻觉完整时序图")
    print("  3. Hallucination_Detection_Types.png          - 幻觉检测类型详解")
    print("  4. Parameter_Intelligent_Fix_Flow.png         - 参数智能修复流程图")
    print("  5. Hallucination_Memory_Feedback_Loop.png     - 记忆系统反馈闭环图")
