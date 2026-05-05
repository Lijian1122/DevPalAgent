# -*- coding: utf-8 -*-
"""
DevPal Agent v1.6 - 架构图生成器 (最终优化版)
优化重点：测试编排数据流部分的可读性
"""
from graphviz import Digraph
import os

os.makedirs('./docs', exist_ok=True)

# 全局设置 - 紧凑高效版
GRAPH_STYLE = {
    'fontname': 'Microsoft YaHei',
    'fontsize': '16',
    'dpi': '300',  # 降低到300 DPI以减少内存占用
    'nodesep': '1.2',
    'ranksep': '1.5',
    'charset': 'utf8',
}

NODE_STYLE = {
    'fontname': 'Microsoft YaHei',
    'fontsize': '14',
    'shape': 'box',
    'style': 'filled,rounded,bold',
    'penwidth': '3',
}

HEADER_STYLE = {
    'fontname': 'Microsoft YaHei',
    'fontsize': '16',
    'style': 'filled,bold',
    'penwidth': '4',
}

CLUSTER_STYLE = {
    'fontname': 'Microsoft YaHei',
    'fontsize': '18',
    'penwidth': '4',
}

EDGE_STYLE = {
    'fontname': 'Microsoft YaHei',
    'fontsize': '12',
}


def create_data_flow_diagram_v16():
    """完整数据流图 v1.6 - 重点优化测试编排数据流部分"""
    dot = Digraph(
        'Data_Flow_v1.6',
        filename='./docs/Complete_Data_Flow_v1.6',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='28,20', rankdir='LR', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    with dot.subgraph(name='cluster_input') as c:
        c.attr(style='filled', color='#FFF8E1', label='【输入层】', pencolor='#FF8F00', **CLUSTER_STYLE)
        c.node('User', '用户输入\n查询字符串', fillcolor='#E65100', fontcolor='white', fontsize='18')

    with dot.subgraph(name='cluster_plan_data') as c:
        c.attr(style='filled', color='#E3F2FD', label='【规划数据流】', pencolor='#1565C0', **CLUSTER_STYLE)
        c.node('Query', '查询分析\n模式检测\n任务分类\n测试任务识别', fillcolor='#64B5F6', fontsize='14')
        c.node('PlanData', '计划对象\n- 步骤列表\n- 总体目标\n- 复杂度\n- 可行性评分', fillcolor='#0D47A1', fontcolor='white', fontsize='13')
        c.node('StepData', '计划步骤\n- 步骤编号\n- 工具需求\n- 预期输出\n- 重要性', fillcolor='#1A237E', fontcolor='white', fontsize='13')

    with dot.subgraph(name='cluster_act_data') as c:
        c.attr(style='filled', color='#E8F5E9', label='【执行数据流】', pencolor='#1B5E20', **CLUSTER_STYLE)
        c.node('Prompt', '增强提示词\n- 系统提示\n- 记忆增强\n- 工具定义', fillcolor='#81C784', fontsize='14')
        c.node('LLMReq', 'LLM请求\n- model模型\n- messages消息\n- tools工具定义', fillcolor='#43A047', fontcolor='white', fontsize='13')
        c.node('LLMResp', 'LLM响应\n- 内容块\n- Thinking块\n- 工具调用块', fillcolor='#2E7D32', fontcolor='white', fontsize='13')
        c.node('ToolCall', '工具调用\n- ID标识\n- 工具名称\n- 输入参数', fillcolor='#1B5E20', fontcolor='white', fontsize='13')
        c.node('FCData', 'FunctionCall执行\n- 参数校验\n- 实际执行\n- 执行结果\n- 调用链', fillcolor='#004D40', fontcolor='white', fontsize='13')

    # ==============================
    # 测试编排数据流 - 重点优化！
    # ==============================
    with dot.subgraph(name='cluster_test_data') as td:
        td.attr(style='filled', color='#A5D6A7', label='【测试编排数据流】', pencolor='#2E7D32', **CLUSTER_STYLE)

        # 第一行：输入
        td.node('TOData', '[1] 编排器输入\n• file_path: 源文件\n• project_name: 项目名\n• 流程开关配置',
                 fillcolor='#00C853', fontcolor='white', fontsize='15', penwidth='4')

        # 第二行：审查和修复
        td.node('CRData', '[2] 代码审查结果\n• issues: 问题列表\n• severity: 严重程度\n• counts: 统计数据',
                 fillcolor='#4CAF50', fontcolor='white', fontsize='14')
        td.node('AFData', '[3] 自动修复结果\n• backup_file: 备份路径\n• fixed_issues: 已修复\n• unfixed_issues: 未修复\n• fix_rate: 修复率',
                 fillcolor='#81C784', fontcolor='white', fontsize='14')

        # 第三行：文档和代码生成
        td.node('TDocData', '[4] 测试文档生成\n• doc_path: 文档路径\n• test_cases: 用例列表\n• coverage: 覆盖率\n• quality_score: 质量评分',
                 fillcolor='#A5D6A7', fontcolor='white', fontsize='14')
        td.node('TGenData', '[5] 测试代码生成\n• test_path: 测试路径\n• language: 语言类型\n• tests_generated: 生成数量',
                 fillcolor='#C8E6C9', fontcolor='black', fontsize='14')

        # 第四行：运行和结果
        td.node('TRunData', '[6] 测试运行结果\n• compile_success: 编译成功\n• run_success: 运行成功\n• passed/total: 通过/总数\n• pass_rate: 通过率%\n• errors: 错误列表',
                 fillcolor='#E8F5E9', fontcolor='black', fontsize='14')

    with dot.subgraph(name='cluster_output') as c:
        c.attr(style='filled', color='#E0F7FA', label='【输出层】', pencolor='#006064', **CLUSTER_STYLE)
        c.node('Output', '最终答案\n格式化输出\n- 完整测试报告\n- 代码修复率统计', fillcolor='#006064', fontcolor='white', fontsize='16')

    # 主连接线 - 加粗更清晰
    dot.edge('User', 'Query', color='#E64A19', penwidth='5', **EDGE_STYLE)
    dot.edge('Query', 'PlanData', color='#0D47A1', penwidth='4', **EDGE_STYLE)
    dot.edge('PlanData', 'StepData', color='#0D47A1', penwidth='4', **EDGE_STYLE)
    dot.edge('PlanData', 'Prompt', color='#1B5E20', penwidth='4', **EDGE_STYLE)
    dot.edge('Prompt', 'LLMReq', color='#1B5E20', penwidth='4', **EDGE_STYLE)
    dot.edge('LLMReq', 'LLMResp', color='#1B5E20', penwidth='4', **EDGE_STYLE)
    dot.edge('LLMResp', 'ToolCall', color='#1B5E20', penwidth='4', **EDGE_STYLE)
    dot.edge('ToolCall', 'FCData', color='#004D40', penwidth='4', **EDGE_STYLE)

    # 测试编排数据流连线 - 重点优化！
    dot.edge('ToolCall', 'TOData', color='#00C853', penwidth='6', **EDGE_STYLE)
    dot.edge('TOData', 'CRData', color='#00C853', penwidth='5', **EDGE_STYLE)
    dot.edge('CRData', 'AFData', color='#00C853', penwidth='5', **EDGE_STYLE)
    dot.edge('AFData', 'TDocData', color='#00C853', penwidth='5', **EDGE_STYLE)
    dot.edge('TDocData', 'TGenData', color='#00C853', penwidth='5', **EDGE_STYLE)
    dot.edge('TGenData', 'TRunData', color='#00C853', penwidth='5', **EDGE_STYLE)

    # 测试数据回流到步骤
    dot.edge('TRunData', 'StepData', color='#1B5E20', penwidth='5', **EDGE_STYLE)

    # 最终输出
    dot.edge('StepData', 'Output', color='#006064', penwidth='5', **EDGE_STYLE)
    dot.edge('LLMResp', 'Output', color='#006064', penwidth='4', **EDGE_STYLE)

    dot.render(cleanup=True)
    print("[OK] 完整数据流图 v1.6 (重点优化测试编排数据流) 已生成")


def create_test_orchestrator_detail_v16():
    """测试编排系统详细架构图 v1.6 - 清晰简洁版"""
    dot = Digraph(
        'Test_Orchestrator_v1.6',
        filename='./docs/Test_Orchestrator_System_Architecture_v1.6',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='24,18', rankdir='TB', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    # 核心编排器
    with dot.subgraph(name='cluster_orchestrator') as c:
        c.attr(style='filled', color='#E8F5E9', label='【TestOrchestrator 测试编排器】', pencolor='#1B5E20', **CLUSTER_STYLE)
        c.node('Orch', '测试编排器核心\n6步一站式自动化流程\n代码审查 → 自动修复\n测试文档 → 测试代码\n测试运行 → 结果更新',
                fillcolor='#1B5E20', fontcolor='white', fontsize='18', style='filled,bold', penwidth='4')

    # 6步流程 - 两行排列
    with dot.subgraph(name='cluster_steps') as c:
        c.attr(style='filled', color='#C8E6C9', label='【执行步骤】', pencolor='#2E7D32', **CLUSTER_STYLE)

        with c.subgraph(name='cluster_row1') as r1:
            r1.attr(rank='same')
            r1.node('S1', '① 代码审查\nCodeReview\n检测潜在问题', fillcolor='#2E7D32', fontcolor='white', fontsize='15')
            r1.node('S2', '② 生成报告\nCodeReviewReport\n详细Markdown报告', fillcolor='#2E7D32', fontcolor='white', fontsize='15')
            r1.node('S3', '③ 自动修复\nAutoFixer\n智能修复bug', fillcolor='#2E7D32', fontcolor='white', fontsize='15')

        with c.subgraph(name='cluster_row2') as r2:
            r2.attr(rank='same')
            r2.node('S4', '④ 生成测试文档\nTestDocGenerator\n结构化测试用例', fillcolor='#004D40', fontcolor='white', fontsize='15')
            r2.node('S5', '⑤ 生成测试代码\nTestGenerator\n多语言测试模板', fillcolor='#004D40', fontcolor='white', fontsize='15')
            r2.node('S6', '⑥ 运行测试\nTestRunner\nMSVC/GCC双支持', fillcolor='#004D40', fontcolor='white', fontsize='15')

    # 输出产物
    with dot.subgraph(name='cluster_output') as c:
        c.attr(style='filled', color='#FFF8E1', label='【输出产物】', pencolor='#FF8F00', **CLUSTER_STYLE)
        with c.subgraph(name='cluster_files') as f:
            f.attr(rank='same')
            f.node('F1', '源码备份\nbackup.cpp', fillcolor='#FFA000', fontcolor='white', fontsize='14')
            f.node('F2', '审查报告\nreview.md', fillcolor='#FFA000', fontcolor='white', fontsize='14')
            f.node('F3', '测试文档\ntest_doc.md', fillcolor='#FFA000', fontcolor='white', fontsize='14')
            f.node('F4', '测试代码\ntest.cpp', fillcolor='#FFA000', fontcolor='white', fontsize='14')

    # 流程连线
    dot.edge('Orch', 'S1', color='#2E7D32', penwidth='5', **EDGE_STYLE)
    dot.edge('S1', 'S2', color='#2E7D32', penwidth='4', **EDGE_STYLE)
    dot.edge('S2', 'S3', color='#2E7D32', penwidth='4', **EDGE_STYLE)
    dot.edge('S3', 'S4', color='#004D40', penwidth='4', **EDGE_STYLE)
    dot.edge('S4', 'S5', color='#004D40', penwidth='4', **EDGE_STYLE)
    dot.edge('S5', 'S6', color='#004D40', penwidth='4', **EDGE_STYLE)
    dot.edge('S6', 'F1', color='#FF8F00', penwidth='4', **EDGE_STYLE)
    dot.edge('S6', 'F2', color='#FF8F00', penwidth='4', **EDGE_STYLE)
    dot.edge('S6', 'F3', color='#FF8F00', penwidth='4', **EDGE_STYLE)
    dot.edge('S6', 'F4', color='#FF8F00', penwidth='4', **EDGE_STYLE)

    dot.render(cleanup=True)
    print("[OK] 测试编排系统详细架构图 v1.6 已生成")


if __name__ == '__main__':
    print("=" * 80)
    print("DevPal Agent v1.6 - 架构图生成器 (最终优化版)")
    print("=" * 80)
    print("优化重点:")
    print("  1. 测试编排数据流部分 - 字体增大到14-15px")
    print("  2. 使用 ①②③④⑤⑥ 圆圈序号标记6个步骤")
    print("  3. 优化连线粗细 - 核心流程加粗显示")
    print("  4. 增大节点间距,布局更清晰")
    print("  5. 降低DPI到300以避免内存问题")
    print("  6. 简化节点内容,减少换行")
    print("=" * 80)

    create_data_flow_diagram_v16()
    create_test_orchestrator_detail_v16()

    print("=" * 80)
    print("架构图生成完成!")
    print("=" * 80)
    print("\n生成的文件:")
    print("  1. Complete_Data_Flow_v1.6.png      - 完整数据流图 (测试编排部分已优化)")
    print("  2. Test_Orchestrator_System_Architecture_v1.6.png - 测试编排系统详情")
