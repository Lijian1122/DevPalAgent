# -*- coding: utf-8 -*-
"""
OpenSpec v2.0 - 完整架构图生成器
生成以下架构图：
1. 整体架构概览图
2. 9阶段工作流图
3. Schema架构层详解图
4. Validation Engine四层架构图
5. ArtifactGraph依赖关系图
6. Delta Spec变更流程图
7. EventBus事件总线架构图
8. 多语言插件系统架构图
9. 完整数据流转图
"""
from graphviz import Digraph
import os

os.makedirs('./doc2.0', exist_ok=True)

# 全局样式
GRAPH_STYLE = {
    'fontname': 'Microsoft YaHei',
    'fontsize': '16',
    'dpi': '300',
    'nodesep': '1.0',
    'ranksep': '1.2',
    'charset': 'utf8',
}

NODE_STYLE = {
    'fontname': 'Microsoft YaHei',
    'fontsize': '13',
    'shape': 'box',
    'style': 'filled,rounded,bold',
    'penwidth': '2',
}

CLUSTER_STYLE = {
    'fontname': 'Microsoft YaHei',
    'fontsize': '16',
    'penwidth': '3',
}

EDGE_STYLE = {
    'fontname': 'Microsoft YaHei',
    'fontsize': '11',
}


def create_architecture_overview():
    """1. OpenSpec v2.0 整体架构概览图"""
    dot = Digraph(
        'OpenSpec_Architecture_Overview_v2.0',
        filename='./doc2.0/01_OpenSpec_Architecture_Overview',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='32,24', rankdir='TB', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    # 顶层：用户交互层
    with dot.subgraph(name='cluster_user') as c:
        c.attr(style='filled', color='#FFF3E0', label='【用户交互层】', pencolor='#E65100', **CLUSTER_STYLE)
        c.node('User', '用户\nChat交互', fillcolor='#E65100', fontcolor='white', fontsize='18')
        c.node('CLI', 'CLI命令行\nopenspec-cli', fillcolor='#F57C00', fontcolor='white', fontsize='14')
        c.node('Web', 'Web界面\n待实现', fillcolor='#FB8C00', fontcolor='white', fontsize='14')

    # 第二层：工作流执行引擎
    with dot.subgraph(name='cluster_workflow') as c:
        c.attr(style='filled', color='#E3F2FD', label='【工作流执行层】', pencolor='#1565C0', **CLUSTER_STYLE)
        c.node('Detection', '需求检测引擎\n关键词识别\n.md文件检测', fillcolor='#42A5F5', fontcolor='white')
        c.node('OpenSpecExecutor', 'OpenSpec执行器\n9阶段工作流编排\n状态管理', fillcolor='#1976D2', fontcolor='white', fontsize='14')
        c.node('WorkflowEngine', 'WorkflowEngine\nYAML声明式\n拓扑排序执行', fillcolor='#0D47A1', fontcolor='white')

    # 第三层：Schema 核心架构层
    with dot.subgraph(name='cluster_schema') as c:
        c.attr(style='filled', color='#E8F5E9', label='【Schema核心架构层 v2.0】', pencolor='#1B5E20', **CLUSTER_STYLE)
        c.node('Validation', 'ValidationEngine\n四层验证架构\n语法→语义→解析→业务', fillcolor='#66BB6A')
        c.node('DeltaSpec', 'DeltaSpec\n增量变更\n差异对比→冲突检测', fillcolor='#43A047', fontcolor='white')
        c.node('ArtifactGraph', 'ArtifactGraph\n工件依赖图\n代码/测试/文档/需求关联', fillcolor='#2E7D32', fontcolor='white')
        c.node('Requirements', 'RequirementsMgr\n需求文档管理\n结构化解析→验收标准', fillcolor='#1B5E20', fontcolor='white')
        c.node('EventBus', 'EventBus\n事件总线\n发布→订阅→过滤', fillcolor='#004D40', fontcolor='white')

    # 第四层：深化体验层 (Phase 5)
    with dot.subgraph(name='cluster_phase5') as c:
        c.attr(style='filled', color='#F3E5F5', label='【深化体验层 v2.0】', pencolor='#4A148C', **CLUSTER_STYLE)
        c.node('Diagnostic', 'DiagnosticEngine\n智能诊断\n健康评分→问题定位', fillcolor='#AB47BC')
        c.node('ConfigPolicy', 'ConfigPolicy\n配置策略\n质量门禁→发布策略', fillcolor='#8E24AA', fontcolor='white')
        c.node('Rollout', 'RolloutEngine\n渐进式发布\n灰度→全量→回滚', fillcolor='#7B1FA2', fontcolor='white')
        c.node('ErrorMgr', 'ErrorManager\n统一错误处理\n错误分类→恢复策略', fillcolor='#6A1B9A', fontcolor='white')

    # 第五层：多语言支持层 (Phase 6)
    with dot.subgraph(name='cluster_phase6') as c:
        c.attr(style='filled', color='#FFEBEE', label='【多语言支持层 v2.0】', pencolor='#B71C1C', **CLUSTER_STYLE)
        c.node('LangPlugin', 'LanguagePluginMgr\n插件管理器\n动态加载→扩展接口', fillcolor='#EF5350')
        c.node('CppPlugin', 'C++插件\nAST解析→编译数据库\n12+代码质量规则', fillcolor='#E53935', fontcolor='white')
        c.node('CompileDB', 'CompileDB\n编译数据库\nCMake/MSVC集成', fillcolor='#C62828', fontcolor='white')

    # 第六层：工具执行层
    with dot.subgraph(name='cluster_tools') as c:
        c.attr(style='filled', color='#E0F7FA', label='【工具执行层】', pencolor='#006064', **CLUSTER_STYLE)
        c.node('ToolRegistry', 'ToolRegistry\n22个工具注册\n统一执行接口', fillcolor='#00BCD4')
        tools = [
            'file_reader', 'file_writer', 'code_review', 'auto_fixer',
            'test_doc_gen', 'test_code_gen', 'test_runner', 'test_orchestrator'
        ]
        for i, tool in enumerate(tools):
            c.node(f'tool_{i}', tool, fillcolor='#0097A7', fontcolor='white', fontsize='11')

    # 第七层：持久化层
    with dot.subgraph(name='cluster_storage') as c:
        c.attr(style='filled', color='#F5F5F5', label='【持久化层】', pencolor='#424242', **CLUSTER_STYLE)
        c.node('FileStorage', '文件存储\n源码/测试/文档', fillcolor='#757575', fontcolor='white')
        c.node('EventLog', '事件日志\nevents.jsonl', fillcolor='#616161', fontcolor='white')
        c.node('Reports', '执行报告\nWorkflow Reports', fillcolor='#424242', fontcolor='white')

    # 连接关系
    dot.edge('User', 'Detection', label='输入查询', penwidth='2')
    dot.edge('CLI', 'Detection', label='命令执行', penwidth='2')
    dot.edge('Web', 'Detection', label='HTTP请求', penwidth='2', style='dashed')

    dot.edge('Detection', 'OpenSpecExecutor', label='检测到需求', penwidth='2')
    dot.edge('OpenSpecExecutor', 'WorkflowEngine', label='调用工作流', penwidth='2')

    dot.edge('OpenSpecExecutor', 'Validation', label='调用', penwidth='2')
    dot.edge('OpenSpecExecutor', 'DeltaSpec', label='增量写入', penwidth='2')
    dot.edge('OpenSpecExecutor', 'ArtifactGraph', label='依赖追踪', penwidth='2')
    dot.edge('OpenSpecExecutor', 'Requirements', label='需求解析', penwidth='2')
    dot.edge('OpenSpecExecutor', 'EventBus', label='发布事件', penwidth='2')

    dot.edge('Validation', 'Diagnostic', label='验证结果', penwidth='2')
    dot.edge('DeltaSpec', 'Rollout', label='变更发布', penwidth='2')
    dot.edge('EventBus', 'ConfigPolicy', label='事件触发', penwidth='2')

    dot.edge('Diagnostic', 'LangPlugin', label='多语言诊断', penwidth='2')
    dot.edge('ConfigPolicy', 'CompileDB', label='编译配置', penwidth='2')

    dot.edge('LangPlugin', 'CppPlugin', label='插件调用', penwidth='2')
    dot.edge('CppPlugin', 'CompileDB', label='编译数据', penwidth='2')

    dot.edge('OpenSpecExecutor', 'ToolRegistry', label='工具调用', penwidth='3', color='#1565C0')
    for i in range(8):
        dot.edge('ToolRegistry', f'tool_{i}', penwidth='1.5')

    dot.edge('file_writer', 'DeltaSpec', label='增量变更', penwidth='2', style='dashed', color='#1B5E20')
    dot.edge('code_review', 'Validation', label='审查结果', penwidth='2', style='dashed', color='#1B5E20')

    for i in range(8):
        dot.edge(f'tool_{i}', 'FileStorage', penwidth='1', style='dotted')

    dot.edge('EventBus', 'EventLog', penwidth='2', style='dotted')
    dot.edge('WorkflowEngine', 'Reports', penwidth='2', style='dotted')

    dot.render(cleanup=True)
    print("[OK] 01_OpenSpec_Architecture_Overview.png 生成完成")


def create_nine_phase_workflow():
    """2. OpenSpec 9阶段工作流图"""
    dot = Digraph(
        'OpenSpec_9_Phase_Workflow',
        filename='./doc2.0/02_OpenSpec_9_Phase_Workflow',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='36,24', rankdir='LR', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', fontsize='12', fontname='Microsoft YaHei')

    # 颜色渐变：蓝→绿→黄→橙→红
    phase_colors = [
        '#E3F2FD', '#BBDEFB', '#90CAF9',  # 蓝色系 (准备阶段)
        '#E8F5E9', '#C8E6C9',             # 绿色系 (代码阶段)
        '#FFF8E1', '#FFECB3', '#FFE082',  # 黄色系 (测试阶段)
        '#FFF3E0'                          # 橙色系 (报告阶段)
    ]

    phase_text_colors = [
        'black', 'black', 'black',
        'black', 'black',
        'black', 'black', 'black',
        'black'
    ]

    phases = [
        ("Phase1", "Phase 1\n需求文档解析",
         "• 读取 .md 需求文件\n• YAML Frontmatter 解析\n• 提取项目名称/版本/作者\n• 识别语言类型 (C++/Python)\n• 提取验收标准"),
        ("Phase2", "Phase 2\n创建项目结构",
         "• 创建项目根目录\n• include/ - 头文件\n• src/ - 源代码\n• tests/ - 测试代码\n• docs/ - 文档\n• config/ - 配置\n• data/ - 数据"),
        ("Phase3", "Phase 3\n生成核心代码",
         "• 根据语言类型生成\n• 认证系统核心类\n• User 类 (用户管理)\n• Session 类 (会话管理)\n• Authenticator 类 (认证)\n• 密码哈希/盐值生成"),
        ("Phase4", "Phase 4\n代码质量审查",
         "• 语法检查\n• 代码风格检查\n• 安全漏洞扫描\n• 复杂度分析\n• 可维护性评分\n• 生成审查报告"),
        ("Phase5", "Phase 5\n自动修复",
         "• 自动备份源文件\n• 修复可自动修复问题\n• 格式化代码\n• 变量命名规范化\n• 计算修复率\n• 生成修复报告"),
        ("Phase6", "Phase 6\n生成测试文档",
         "• 解析代码结构\n• 识别所有类/方法\n• 生成功能测试用例\n• 生成边界测试用例\n• 生成异常测试用例\n• 计算覆盖率估算"),
        ("Phase7", "Phase 7\n生成测试代码",
         "• 生成测试框架代码\n• C++: Google Test\n• Python: pytest\n• 生成断言逻辑\n• 集成测试用例\n• Setup/Teardown"),
        ("Phase8", "Phase 8\n运行测试",
         "• 编译测试代码 (C++)\n• 执行所有测试用例\n• 捕获测试输出\n• 统计通过/失败数\n• 计算通过率\n• 生成测试报告"),
        ("Phase9", "Phase 9\n生成最终报告",
         "• 汇总各阶段结果\n• 统计执行时间\n• 列出生成文件\n• 生成工作流报告 JSON\n• 输出执行摘要"),
    ]

    for i, (node_id, label, details) in enumerate(phases):
        with dot.subgraph(name=f'cluster_{node_id}') as c:
            phase_num = i + 1
            color = phase_colors[i]
            c.attr(style='filled', color=color, label=label, pencolor='#212121',
                   fontsize='15', fontname='Microsoft YaHei', penwidth='2')
            c.node(f'{node_id}_details', details, shape='note', style='filled',
                   fillcolor='white', fontsize='10', fontname='Microsoft YaHei',
                   penwidth='1')

    # 连接各阶段
    for i in range(8):
        dot.edge(f'Phase{i+1}_details', f'Phase{i+2}_details',
                label=f'阶段 {i+1} → {i+2}', penwidth='3', color='#1976D2')

    # 起点和终点
    dot.node('Start', '开始\n用户输入需求', fillcolor='#4CAF50', fontcolor='white',
             fontsize='16', shape='ellipse')
    dot.node('End', '完成\n项目交付', fillcolor='#F44336', fontcolor='white',
             fontsize='16', shape='ellipse')

    dot.edge('Start', 'Phase1_details', label='触发 OpenSpec\n工作流', penwidth='3', color='#4CAF50')
    dot.edge('Phase9_details', 'End', label='工作流完成', penwidth='3', color='#F44336')

    # 特殊连接：Phase 8 失败可重试
    dot.edge('Phase8_details', 'Phase7_details', label='测试失败\n自动重试',
             penwidth='2', color='#FF5722', style='dashed', constraint='false')

    dot.render(cleanup=True)
    print("[OK] 02_OpenSpec_9_Phase_Workflow.png 生成完成")


def create_schema_architecture():
    """3. Schema架构层详解图"""
    dot = Digraph(
        'Schema_Architecture',
        filename='./doc2.0/03_Schema_Architecture_Layer',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='32,28', rankdir='TB', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    # 核心 Schema 模块
    with dot.subgraph(name='cluster_core') as c:
        c.attr(style='filled', color='#E3F2FD', label='【Schema Core 核心模块】',
               pencolor='#0D47A1', **CLUSTER_STYLE)

        # 从左到右排列核心模块
        modules = [
            ('ValidationEngine', 'ValidationEngine\n四层验证架构\n\n1. Format 格式层\n2. Semantic 语义层\n3. Parser 解析层\n4. Business 业务层', '#1565C0'),
            ('DeltaSpec', 'DeltaSpec\n增量变更机制\n\n• 变更块 DeltaHunk\n• ADD/MODIFY/REMOVE\n• 冲突检测\n• Diff 预览\n• 原子应用', '#0D47A1'),
            ('ArtifactGraph', 'ArtifactGraph\n工件依赖图\n\n• networkx 图计算\n• 代码/测试/文档/需求\n• 依赖类型：实现/测试/引用\n• 影响范围分析', '#01579B'),
        ]

        for node_id, label, color in modules:
            c.node(node_id, label, fillcolor=color, fontcolor='white', fontsize='12')

    # 工作流模块
    with dot.subgraph(name='cluster_workflow') as c:
        c.attr(style='filled', color='#E8F5E9', label='【Workflow Engine 工作流引擎】',
               pencolor='#1B5E20', **CLUSTER_STYLE)
        c.node('WorkflowEngine', 'WorkflowEngine\n声明式工作流引擎\n\n• YAML Pipeline 定义\n• 拓扑排序执行\n• 条件分支\n• 依赖管理\n• 变量替换\n• 重试机制',
               fillcolor='#2E7D32', fontcolor='white', fontsize='12')

    # 需求管理模块
    with dot.subgraph(name='cluster_requirements') as c:
        c.attr(style='filled', color='#FFF8E1', label='【Requirements Manager 需求管理】',
               pencolor='#FF8F00', **CLUSTER_STYLE)
        c.node('RequirementsMgr', 'RequirementsManager\n结构化需求管理\n\n• Markdown + YAML Frontmatter\n• RequirementItem 需求项\n• AcceptanceCriteria 验收标准\n• 状态追踪 (提议→批准→实现)',
               fillcolor='#F57C00', fontcolor='white', fontsize='12')

    # 事件总线
    with dot.subgraph(name='cluster_eventbus') as c:
        c.attr(style='filled', color='#F3E5F5', label='【Event Bus 事件总线】',
               pencolor='#4A148C', **CLUSTER_STYLE)
        c.node('EventBus', 'EventBus\n发布订阅系统\n\n• Event 事件对象\n• Priority Queue 优先级队列\n• Filter 过滤器\n• Subscription 订阅\n• Adapter 适配器\n• 全局单例模式',
               fillcolor='#7B1FA2', fontcolor='white', fontsize='12')

    # 事件类型
    with dot.subgraph(name='cluster_events') as c:
        c.attr(style='filled', color='#FCE4EC', label='【Event Types 事件类型】',
               pencolor='#880E4F', **CLUSTER_STYLE)
        events = [
            ('FileChanged', 'FileChangedEvent\n文件变更事件'),
            ('StepExecuted', 'StepExecutedEvent\n步骤执行事件'),
            ('ValidationCompleted', 'ValidationCompletedEvent\n验证完成事件'),
            ('ArtifactDiscovered', 'ArtifactDiscoveredEvent\n工件发现事件'),
            ('DeltaApplied', 'DeltaAppliedEvent\nDelta应用事件'),
            ('ImpactAnalysis', 'ImpactAnalysisEvent\n影响分析事件'),
        ]
        for i, (node_id, label) in enumerate(events):
            c.node(node_id, label, fillcolor='#C2185B', fontcolor='white', fontsize='10')

    # 连接核心模块
    dot.edge('ValidationEngine', 'DeltaSpec', label='验证通过\n允许变更', penwidth='2')
    dot.edge('DeltaSpec', 'ArtifactGraph', label='变更触发\n依赖更新', penwidth='2')
    dot.edge('ArtifactGraph', 'WorkflowEngine', label='工件信息\n驱动工作流', penwidth='2')

    # 工作流连接需求
    dot.edge('RequirementsMgr', 'WorkflowEngine', label='需求文档\n作为输入', penwidth='2')

    # 事件总线连接
    dot.edge('ValidationEngine', 'EventBus', label='发布\n验证事件', penwidth='2', style='dashed')
    dot.edge('DeltaSpec', 'EventBus', label='发布\n变更事件', penwidth='2', style='dashed')
    dot.edge('ArtifactGraph', 'EventBus', label='发布\n工件事件', penwidth='2', style='dashed')
    dot.edge('WorkflowEngine', 'EventBus', label='发布\n工作流事件', penwidth='2', style='dashed')

    # 事件总线分发
    for event_id, _ in events:
        dot.edge('EventBus', event_id, penwidth='1.5', style='dashed')

    dot.render(cleanup=True)
    print("[OK] 03_Schema_Architecture_Layer.png 生成完成")


def create_validation_engine():
    """4. Validation Engine四层架构图"""
    dot = Digraph(
        'Validation_Engine',
        filename='./doc2.0/04_Validation_Engine_Four_Layer',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='28,32', rankdir='TB', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    # 输入
    dot.node('Input', '输入内容\n代码/文档/配置',
             fillcolor='#424242', fontcolor='white', fontsize='16')

    # 四层架构，从下往上
    layers = [
        ("Layer1", "第一层: Format 格式验证",
         ['编码验证', '语法检查', '括号匹配', '换行符统一', 'BOM检测'],
         '#E3F2FD', '#1565C0'),
        ("Layer2", "第二层: Semantic 语义验证",
         ['逻辑一致性', '无幻觉检测', '引用有效性', '重复检测', '上下文匹配'],
         '#E8F5E9', '#2E7D32'),
        ("Layer3", "第三层: Parser 解析验证",
         ['现有代码兼容', 'AST解析', '符号表检查', '类型检查', '依赖分析'],
         '#FFF8E1', '#F57C00'),
        ("Layer4", "第四层: Business 业务验证",
         ['项目规范检查', '命名规范', '架构约束', '质量门禁', '安全策略'],
         '#F3E5F5', '#7B1FA2'),
    ]

    for i, (layer_id, label, checks, bg_color, border_color) in enumerate(layers):
        with dot.subgraph(name=f'cluster_{layer_id}') as c:
            c.attr(style='filled', color=bg_color, label=label, pencolor=border_color,
                   **CLUSTER_STYLE)
            for j, check in enumerate(checks):
                c.node(f'{layer_id}_check{j}', check, fillcolor=border_color,
                       fontcolor='white', fontsize='11')

    # 连接各层
    dot.edge('Input', 'Layer1_check0', label='进入验证', penwidth='3', color='#1565C0')

    for i in range(3):
        for j in range(5):
            dot.edge(f'Layer{i+1}_check{j}', f'Layer{i+2}_check{min(j,4)}',
                    penwidth='1.5', style='solid', constraint='true')

    # 输出
    dot.node('Output', '验证结果\nValidationResult\n• passed: bool\n• issues: List\n• context: Dict',
             fillcolor='#4CAF50', fontcolor='white', fontsize='14', shape='note')

    for j in range(5):
        dot.edge(f'Layer4_check{j}', 'Output', penwidth='2', color='#4CAF50')

    # 失败分支
    dot.node('Failed', '验证失败\n停止执行\n返回错误',
             fillcolor='#F44336', fontcolor='white', fontsize='14', shape='ellipse')

    for i in range(1, 5):
        dot.edge(f'Layer{i}_check0', 'Failed', label=f'L{i} 失败\n停止',
                 penwidth='2', color='#F44336', style='dashed', constraint='false')

    dot.render(cleanup=True)
    print("[OK] 04_Validation_Engine_Four_Layer.png 生成完成")


def create_artifact_graph():
    """5. ArtifactGraph依赖关系图"""
    dot = Digraph(
        'Artifact_Graph',
        filename='./doc2.0/05_ArtifactGraph_Dependency',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='30,26', rankdir='LR', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    # 工件类型
    artifact_types = [
        ('REQ', '需求工件\nRequirement', '#E65100'),
        ('CODE', '代码工件\nSource Code', '#1565C0'),
        ('TEST', '测试工件\nTest Code', '#2E7D32'),
        ('DOC', '文档工件\nDocumentation', '#7B1FA2'),
        ('CFG', '配置工件\nConfiguration', '#006064'),
    ]

    with dot.subgraph(name='cluster_types') as c:
        c.attr(style='filled', color='#F5F5F5', label='【工件类型 Artifact Types】',
               pencolor='#424242', **CLUSTER_STYLE)
        for node_id, label, color in artifact_types:
            c.node(node_id, label, fillcolor=color, fontcolor='white', fontsize='14')

    # 依赖类型
    with dot.subgraph(name='cluster_deps') as c:
        c.attr(style='filled', color='#E8F5E9', label='【依赖关系 Dependency Types】',
               pencolor='#1B5E20', **CLUSTER_STYLE)
        dep_types = [
            ('IMPLEMENTS', 'IMPLEMENTS\n代码实现需求', '#4CAF50'),
            ('TESTS', 'TESTS\n测试验证代码', '#8BC34A'),
            ('REFERENCES', 'REFERENCES\n文档引用代码', '#CDDC39'),
            ('DEPENDS_ON', 'DEPENDS_ON\n代码依赖代码', '#FFC107'),
            ('INCLUDES', 'INCLUDES\n头文件包含', '#FF9800'),
            ('EXTENDS', 'EXTENDS\n继承/扩展', '#FF5722'),
        ]
        for node_id, label, color in dep_types:
            c.node(node_id, label, fillcolor=color, fontcolor='black', fontsize='11')

    # 示例项目结构
    with dot.subgraph(name='cluster_example') as c:
        c.attr(style='filled', color='#E3F2FD', label='【示例项目依赖关系】',
               pencolor='#0D47A1', **CLUSTER_STYLE)

        # 需求
        c.node('req_auth', 'REQ: 认证系统\nauth_requirements.md',
               fillcolor='#E65100', fontcolor='white')

        # 代码
        c.node('code_h', 'CODE: auth.h\n头文件', fillcolor='#1976D2', fontcolor='white')
        c.node('code_cpp', 'CODE: auth.cpp\n实现文件', fillcolor='#1565C0', fontcolor='white')
        c.node('code_user', 'CODE: User 类\n用户管理', fillcolor='#0D47A1', fontcolor='white')
        c.node('code_session', 'CODE: Session 类\n会话管理', fillcolor='#0D47A1', fontcolor='white')
        c.node('code_auth', 'CODE: Authenticator\n认证器', fillcolor='#0D47A1', fontcolor='white')

        # 测试
        c.node('test_auth', 'TEST: test_auth.cpp\n认证测试', fillcolor='#2E7D32', fontcolor='white')
        c.node('test_user', 'TEST: test_user.cpp\n用户测试', fillcolor='#388E3C', fontcolor='white')

        # 文档
        c.node('doc_api', 'DOC: API.md\n接口文档', fillcolor='#7B1FA2', fontcolor='white')
        c.node('doc_test', 'DOC: test_doc.md\n测试文档', fillcolor='#8E24AA', fontcolor='white')

        # 配置
        c.node('cfg_build', 'CFG: CMakeLists.txt\n构建配置', fillcolor='#006064', fontcolor='white')

    # 连接：需求 → 代码
    dot.edge('req_auth', 'code_h', label='IMPLEMENTS', fontcolor='#4CAF50', penwidth='2', color='#4CAF50')
    dot.edge('req_auth', 'code_cpp', label='IMPLEMENTS', fontcolor='#4CAF50', penwidth='2', color='#4CAF50')

    # 连接：代码内部
    dot.edge('code_h', 'code_cpp', label='INCLUDES', fontcolor='#FF9800', penwidth='2', color='#FF9800')
    dot.edge('code_cpp', 'code_user', label='DEFINES', fontcolor='#FFC107', penwidth='1.5', style='dashed')
    dot.edge('code_cpp', 'code_session', label='DEFINES', fontcolor='#FFC107', penwidth='1.5', style='dashed')
    dot.edge('code_cpp', 'code_auth', label='DEFINES', fontcolor='#FFC107', penwidth='1.5', style='dashed')
    dot.edge('code_auth', 'code_user', label='DEPENDS_ON', fontcolor='#FFC107', penwidth='2', color='#FFC107')
    dot.edge('code_auth', 'code_session', label='DEPENDS_ON', fontcolor='#FFC107', penwidth='2', color='#FFC107')

    # 连接：代码 → 测试
    dot.edge('test_auth', 'code_auth', label='TESTS', fontcolor='#8BC34A', penwidth='2', color='#8BC34A')
    dot.edge('test_user', 'code_user', label='TESTS', fontcolor='#8BC34A', penwidth='2', color='#8BC34A')

    # 连接：代码 → 文档
    dot.edge('doc_api', 'code_h', label='REFERENCES', fontcolor='#CDDC39', penwidth='2', color='#CDDC39')
    dot.edge('doc_test', 'test_auth', label='REFERENCES', fontcolor='#CDDC39', penwidth='2', color='#CDDC39')

    # 连接：配置
    dot.edge('cfg_build', 'code_cpp', label='BUILDS', fontcolor='#006064', penwidth='2', color='#006064')

    # ArtifactGraph 核心
    dot.node('AGCore', 'ArtifactGraph 核心\n使用 networkx.DiGraph\n• add_node()\n• add_dependency()\n• get_affected_artifacts()\n• discover_from_directory()',
             fillcolor='#263238', fontcolor='white', fontsize='12', shape='box3d')

    dot.edge('AGCore', 'req_auth', style='dotted', penwidth='1')
    dot.edge('AGCore', 'code_h', style='dotted', penwidth='1')
    dot.edge('AGCore', 'test_auth', style='dotted', penwidth='1')
    dot.edge('AGCore', 'doc_api', style='dotted', penwidth='1')

    dot.render(cleanup=True)
    print("[OK] 05_ArtifactGraph_Dependency.png 生成完成")


def create_delta_flow():
    """6. Delta Spec变更流程图"""
    dot = Digraph(
        'Delta_Flow',
        filename='./doc2.0/06_DeltaSpec_Change_Flow',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='30,24', rankdir='LR', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    # 原始文件
    dot.node('Original', '原始文件\nOriginal File\n\n• 读取内容\n• 计算哈希\n• 保存备份',
             fillcolor='#795548', fontcolor='white', fontsize='14')

    # Delta 操作类型
    with dot.subgraph(name='cluster_ops') as c:
        c.attr(style='filled', color='#FFF3E0', label='【Delta 操作类型】',
               pencolor='#E65100', **CLUSTER_STYLE)
        ops = [
            ('ADD', 'ADD\n新增内容\n• 插入位置\n• 新内容', '#4CAF50'),
            ('MODIFY', 'MODIFY\n修改内容\n• 旧内容\n• 新内容\n• 行范围', '#FF9800'),
            ('REMOVE', 'REMOVE\n删除内容\n• 行范围\n• 删除原因', '#F44336'),
            ('RENAME', 'RENAMED\n重命名\n• 标识符替换\n• 引用更新', '#9C27B0'),
        ]
        for node_id, label, color in ops:
            c.node(node_id, label, fillcolor=color, fontcolor='white', fontsize='11')

    # DeltaHunk 结构
    dot.node('DeltaHunk', 'DeltaHunk 变更块\n\n• operation: 操作类型\n• target_path: 目标路径\n• old_content: 原内容\n• new_content: 新内容\n• start_line: 起始行\n• end_line: 结束行\n• reason: 变更原因',
             fillcolor='#263238', fontcolor='white', fontsize='11', shape='box3d')

    # 验证阶段
    dot.node('Validation', '冲突检测与验证\n\n• 行范围有效性\n• 内容匹配检查\n• 重叠检测\n• 语法验证',
             fillcolor='#FF5722', fontcolor='white', fontsize='12')

    # 应用阶段
    dot.node('Apply', '应用 Delta\n\n• 按逆序应用\n(防止行号偏移)\n• 逐行替换\n• 原子性保证',
             fillcolor='#FF9800', fontcolor='white', fontsize='12')

    # 冲突处理
    dot.node('Conflict', '冲突处理\n\n• 标记冲突\n• 生成冲突报告\n• 回滚变更\n• 用户干预',
             fillcolor='#F44336', fontcolor='white', fontsize='12')

    # 成功输出
    dot.node('Result', 'DeltaResult 结果\n\n• success: bool\n• applied_deltas: List\n• conflicts: List\n• new_content: str\n• diff_preview: str\n\n统一 Diff 格式\n+ 新增行\n- 删除行\n  上下文行',
             fillcolor='#4CAF50', fontcolor='white', fontsize='11', shape='note')

    # 连接
    dot.edge('Original', 'ADD', penwidth='2')
    dot.edge('Original', 'MODIFY', penwidth='2')
    dot.edge('Original', 'REMOVE', penwidth='2')
    dot.edge('Original', 'RENAME', penwidth='2')

    dot.edge('ADD', 'DeltaHunk', penwidth='2')
    dot.edge('MODIFY', 'DeltaHunk', penwidth='2')
    dot.edge('REMOVE', 'DeltaHunk', penwidth='2')
    dot.edge('RENAME', 'DeltaHunk', penwidth='2')

    dot.edge('DeltaHunk', 'Validation', label=' 验证变更', penwidth='3')
    dot.edge('Validation', 'Apply', label=' 验证通过', penwidth='3', color='#4CAF50')
    dot.edge('Validation', 'Conflict', label=' 检测到冲突', penwidth='3', color='#F44336', style='dashed')
    dot.edge('Conflict', 'DeltaHunk', label=' 修正后重试', penwidth='2', color='#FF9800', style='dashed')
    dot.edge('Apply', 'Result', label=' 应用成功', penwidth='3', color='#4CAF50')

    # FileWriter 集成
    dot.node('FileWriter', 'FileWriter 集成\n\nfile_writer tool 支持 Delta 模式:\n• delta_mode: bool\n• deltas: List[DeltaHunk]\n• reason: str\n• show_diff: bool',
             fillcolor='#00BCD4', fontcolor='white', fontsize='11')

    dot.edge('Result', 'FileWriter', penwidth='2', style='dashed')
    dot.edge('FileWriter', 'Original', label=' 写入文件', penwidth='2', color='#00BCD4', style='dashed')

    dot.render(cleanup=True)
    print("[OK] 06_DeltaSpec_Change_Flow.png 生成完成")


def create_eventbus_arch():
    """7. EventBus事件总线架构图"""
    dot = Digraph(
        'EventBus_Arch',
        filename='./doc2.0/07_EventBus_Architecture',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='32,26', rankdir='TB', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    # 事件发布者
    with dot.subgraph(name='cluster_publishers') as c:
        c.attr(style='filled', color='#E3F2FD', label='【事件发布者 Publishers】',
               pencolor='#0D47A1', **CLUSTER_STYLE)
        publishers = [
            ('P_Workflow', 'WorkflowEngine\n工作流执行事件', '#1976D2'),
            ('P_Validation', 'ValidationEngine\n验证完成事件', '#1565C0'),
            ('P_Delta', 'DeltaSpec\n变更应用事件', '#0D47A1'),
            ('P_Artifact', 'ArtifactGraph\n工件发现事件', '#01579B'),
            ('P_Tools', 'Tools\n工具执行事件', '#006064'),
        ]
        for node_id, label, color in publishers:
            c.node(node_id, label, fillcolor=color, fontcolor='white', fontsize='11')

    # EventBus 核心
    with dot.subgraph(name='cluster_eventbus') as c:
        c.attr(style='filled', color='#F5F5F5', label='【EventBus 核心】',
               pencolor='#424242', **CLUSTER_STYLE)
        c.node('EventBusCore', 'EventBus\n\n• publish() 发布\n• subscribe() 订阅\n• unsubscribe() 取消\n• filter() 过滤\n• dispatch() 分发',
               fillcolor='#263238', fontcolor='white', fontsize='13', shape='box3d')

        # 内部组件
        internal = [
            ('EventQueue', 'Priority Queue\n优先级队列\nHIGH/NORMAL/LOW', '#607D8B'),
            ('EventFilter', 'Filter 过滤器\n按类型/范围/源过滤', '#546E7A'),
            ('EventAdapter', 'Adapter 适配器\n跨系统事件转换', '#455A64'),
        ]
        for node_id, label, color in internal:
            c.node(node_id, label, fillcolor=color, fontcolor='white', fontsize='10')

    # Event 基类
    with dot.subgraph(name='cluster_event_base') as c:
        c.attr(style='filled', color='#FFF8E1', label='【Event 基类结构】',
               pencolor='#FF8F00', **CLUSTER_STYLE)
        c.node('EventBase', 'Event 基类\n\n• event_id: UUID\n• event_type: str\n• timestamp: datetime\n• priority: Priority\n• scope: Scope\n• source: str\n• data: Dict\n\n优先级: HIGH > NORMAL > LOW\n范围: GLOBAL / LOCAL',
               fillcolor='#F57C00', fontcolor='white', fontsize='11')

    # 具体事件类型
    with dot.subgraph(name='cluster_event_types') as c:
        c.attr(style='filled', color='#E8F5E9', label='【具体事件类型】',
               pencolor='#1B5E20', **CLUSTER_STYLE)
        events = [
            ('E_File', 'FileChangedEvent\n文件变更', '#4CAF50'),
            ('E_Step', 'StepExecutedEvent\n步骤执行', '#66BB6A'),
            ('E_Validation', 'ValidationCompletedEvent\n验证完成', '#81C784'),
            ('E_Artifact', 'ArtifactDiscoveredEvent\n工件发现', '#A5D6A7'),
            ('E_Delta', 'DeltaAppliedEvent\nDelta应用', '#C8E6C9'),
            ('E_Workflow', 'WorkflowCompletedEvent\n工作流完成', '#E8F5E9'),
            ('E_Impact', 'ImpactAnalysisEvent\n影响分析', '#E8F5E9'),
        ]
        for node_id, label, color in events:
            c.node(node_id, label, fillcolor=color, fontcolor='black', fontsize='10')

    # 订阅者
    with dot.subgraph(name='cluster_subscribers') as c:
        c.attr(style='filled', color='#F3E5F5', label='【事件订阅者 Subscribers】',
               pencolor='#4A148C', **CLUSTER_STYLE)
        subscribers = [
            ('S_Log', 'EventLogger\n事件日志记录', '#8E24AA'),
            ('S_Report', 'ReportGenerator\n报告生成器', '#9C27B0'),
            ('S_UI', 'UI Notifier\n界面通知', '#AB47BC'),
            ('S_Metric', 'MetricsCollector\n指标收集', '#BA68C8'),
        ]
        for node_id, label, color in subscribers:
            c.node(node_id, label, fillcolor=color, fontcolor='white', fontsize='11')

    # 全局单例
    dot.node('Global', 'get_global_eventbus()\n全局单例访问\n\n模块间共享事件总线\n无需实例传递',
             fillcolor='#E91E63', fontcolor='white', fontsize='11', shape='ellipse')

    # 连接：发布者 → EventBus
    for p_id, _, _ in publishers:
        dot.edge(p_id, 'EventBusCore', label='publish()', penwidth='2', color='#1565C0')

    # 连接：EventBus 内部
    dot.edge('EventBusCore', 'EventQueue', penwidth='2')
    dot.edge('EventQueue', 'EventFilter', penwidth='2')
    dot.edge('EventFilter', 'EventAdapter', penwidth='2')

    # 连接：Event 继承
    dot.edge('EventBase', 'E_File', penwidth='2', style='solid', color='#F57C00')
    dot.edge('EventBase', 'E_Step', penwidth='2', style='solid', color='#F57C00')
    dot.edge('EventBase', 'E_Validation', penwidth='2', style='solid', color='#F57C00')
    dot.edge('EventBase', 'E_Artifact', penwidth='2', style='solid', color='#F57C00')
    dot.edge('EventBase', 'E_Delta', penwidth='2', style='solid', color='#F57C00')
    dot.edge('EventBase', 'E_Workflow', penwidth='2', style='solid', color='#F57C00')
    dot.edge('EventBase', 'E_Impact', penwidth='2', style='solid', color='#F57C00')

    # 连接：EventBus → 订阅者
    for s_id, _, _ in subscribers:
        dot.edge('EventAdapter', s_id, label='dispatch()', penwidth='2', color='#7B1FA2')

    # 连接：全局单例
    dot.edge('Global', 'EventBusCore', penwidth='2', style='dashed', color='#E91E63')

    dot.render(cleanup=True)
    print("[OK] 07_EventBus_Architecture.png 生成完成")


def create_multilang_arch():
    """8. 多语言插件系统架构图"""
    dot = Digraph(
        'Multilang_Arch',
        filename='./doc2.0/08_Multilingual_Plugin_System',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='32,26', rankdir='TB', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', **EDGE_STYLE)

    # 插件管理器
    dot.node('PluginMgr', 'LanguagePluginManager\n\n• register_plugin()\n• get_plugin()\n• list_languages()\n• detect_language()\n\n支持语言自动检测',
             fillcolor='#263238', fontcolor='white', fontsize='13', shape='box3d')

    # 插件接口
    with dot.subgraph(name='cluster_interface') as c:
        c.attr(style='filled', color='#E3F2FD', label='【LanguagePlugin 接口】',
               pencolor='#0D47A1', **CLUSTER_STYLE)
        c.node('PluginInterface', 'LanguagePlugin (ABC)\n\n抽象基类接口:\n\n• name: str\n• extensions: List[str]\n• parse_ast()\n• get_symbols()\n• get_dependencies()\n• analyze_file()\n• check_code_quality()\n• get_build_system()',
               fillcolor='#1565C0', fontcolor='white', fontsize='12')

    # 数据结构
    with dot.subgraph(name='cluster_data') as c:
        c.attr(style='filled', color='#E8F5E9', label='【数据结构 Data Structures】',
               pencolor='#1B5E20', **CLUSTER_STYLE)
        data_structs = [
            ('ASTNode', 'ASTNode\n抽象语法树节点\n• type: str\n• name: str\n• location: LineCol\n• children: List'),
            ('SymbolInfo', 'SymbolInfo\n符号信息\n• name: str\n• kind: class/func/var\n• type: str\n• visibility: public/private'),
            ('TypeInfo', 'TypeInfo\n类型信息\n• name: str\n• base_classes: List\n• methods: List\n• fields: List'),
            ('DependencyInfo', 'DependencyInfo\n依赖信息\n• file: Path\n• includes: List\n• imports: List\n• libraries: List'),
            ('FileAnalysis', 'FileAnalysisResult\n文件分析结果\n• ast: ASTNode\n• symbols: List[SymbolInfo]\n• types: List[TypeInfo]\n• dependencies: DependencyInfo\n• issues: List'),
        ]
        for i, (node_id, label) in enumerate(data_structs):
            c.node(node_id, label, fillcolor='#2E7D32', fontcolor='white', fontsize='10')

    # C++ 插件
    with dot.subgraph(name='cluster_cpp') as c:
        c.attr(style='filled', color='#FFF3E0', label='【C++ Language Plugin】',
               pencolor='#E65100', **CLUSTER_STYLE)
        c.node('CppPlugin', 'CppLanguagePlugin\n\n• Clang AST 解析 (可选)\n• 正则表达式解析\n• 预处理指令处理\n• 模板支持\n• C++11/14/17/20',
               fillcolor='#E65100', fontcolor='white', fontsize='12')

        # C++ 代码质量规则
        with dot.subgraph(name='cluster_cpp_rules') as rc:
            rc.attr(style='filled', color='#FFECB3', label='【C++ Code Quality Rules (12+)】',
                   pencolor='#FF8F00')
            rules = [
                ('R_Naming', '命名规范\n• PascalCase 类名\n• camelCase 方法\n• UPPER_CASE 常量'),
                ('R_Header', '头文件保护\n• #pragma once\n• #ifndef 守卫'),
                ('R_Modern', '现代C++特性\n• 使用 smart_ptr\n• 避免裸 new/delete\n• range-based for'),
                ('R_Style', '代码风格\n• 缩进 4 空格\n• 大括号换行\n• 行长度限制'),
                ('R_Safety', '内存安全\n• 初始化检查\n• nullptr 代替 NULL\n• 越界检查'),
            ]
            for node_id, label in rules:
                rc.node(node_id, label, fillcolor='#FF9800', fontcolor='white', fontsize='9')

    # 编译数据库
    with dot.subgraph(name='cluster_compile') as c:
        c.attr(style='filled', color='#F3E5F5', label='【Compilation Database 编译数据库】',
               pencolor='#4A148C', **CLUSTER_STYLE)
        c.node('CompileDB', 'CompilationDatabase\n\n• compile_commands.json\n• CMake 集成\n• MSVC 集成\n• include_directories\n• compile_flags\n• defines',
               fillcolor='#7B1FA2', fontcolor='white', fontsize='12')

    # 构建系统检测
    with dot.subgraph(name='cluster_build') as c:
        c.attr(style='filled', color='#FFEBEE', label='【Build System Detector】',
               pencolor='#B71C1C', **CLUSTER_STYLE)
        builds = [
            ('B_CMake', 'CMake\nCMakeLists.txt 检测', '#C62828'),
            ('B_Make', 'Makefile\nMakefile 检测', '#D32F2F'),
            ('B_MSVC', 'MSVC\n.vcxproj 检测', '#E53935'),
            ('B_Meson', 'Meson\nmeson.build 检测', '#EF5350'),
        ]
        for node_id, label, color in builds:
            c.node(node_id, label, fillcolor=color, fontcolor='white', fontsize='10')

    # 未来扩展
    with dot.subgraph(name='cluster_future') as c:
        c.attr(style='filled', color='#E0F7FA', label='【Future Plugins 未来扩展】',
               pencolor='#006064', **CLUSTER_STYLE)
        future = [
            ('F_Python', 'Python Plugin\n• AST 解析\n• 类型注解检查\n• PEP8 规范', '#00BCD4'),
            ('F_Rust', 'Rust Plugin\n• cargo 集成\n• unsafe 检查\n• clippy 集成', '#00ACC1'),
            ('F_Go', 'Go Plugin\n• go fmt 集成\n• go vet 检查\n• module 支持', '#0097A7'),
        ]
        for node_id, label, color in future:
            c.node(node_id, label, fillcolor=color, fontcolor='white', fontsize='10',
                   style='dashed,filled,rounded')

    # 连接
    dot.edge('PluginMgr', 'PluginInterface', penwidth='3', color='#1565C0')
    dot.edge('PluginInterface', 'CppPlugin', label='实现', penwidth='3', color='#E65100')
    dot.edge('CppPlugin', 'CompileDB', label='使用', penwidth='2', color='#7B1FA2')
    dot.edge('CompileDB', 'B_CMake', penwidth='2')
    dot.edge('CompileDB', 'B_Make', penwidth='2')
    dot.edge('CompileDB', 'B_MSVC', penwidth='2')
    dot.edge('CompileDB', 'B_Meson', penwidth='2')

    dot.edge('CppPlugin', 'R_Naming', penwidth='1.5')
    dot.edge('CppPlugin', 'R_Header', penwidth='1.5')
    dot.edge('CppPlugin', 'R_Modern', penwidth='1.5')
    dot.edge('CppPlugin', 'R_Style', penwidth='1.5')
    dot.edge('CppPlugin', 'R_Safety', penwidth='1.5')

    dot.edge('PluginInterface', 'F_Python', label='待实现', penwidth='2', style='dashed')
    dot.edge('PluginInterface', 'F_Rust', label='待实现', penwidth='2', style='dashed')
    dot.edge('PluginInterface', 'F_Go', label='待实现', penwidth='2', style='dashed')

    dot.edge('PluginInterface', 'ASTNode', penwidth='1.5', style='dotted')
    dot.edge('PluginInterface', 'SymbolInfo', penwidth='1.5', style='dotted')
    dot.edge('PluginInterface', 'TypeInfo', penwidth='1.5', style='dotted')
    dot.edge('PluginInterface', 'DependencyInfo', penwidth='1.5', style='dotted')
    dot.edge('PluginInterface', 'FileAnalysis', penwidth='1.5', style='dotted')

    dot.render(cleanup=True)
    print("[OK] 08_Multilingual_Plugin_System.png 生成完成")


def create_complete_data_flow():
    """9. 完整数据流转图"""
    dot = Digraph(
        'Complete_Data_Flow',
        filename='./doc2.0/09_Complete_Data_Flow',
        format='png',
        encoding='utf8'
    )
    dot.attr(size='36,28', rankdir='LR', **GRAPH_STYLE)
    dot.attr('node', **NODE_STYLE)
    dot.attr('edge', fontsize='10', fontname='Microsoft YaHei')

    # 阶段1: 输入
    with dot.subgraph(name='cluster_input') as c:
        c.attr(style='filled', color='#FFF3E0', label='【阶段1: 输入层】', pencolor='#E65100', **CLUSTER_STYLE)
        c.node('UserQuery', '用户查询\n"实现需求文件 xxx.md"', fillcolor='#E65100', fontcolor='white', fontsize='14')
        c.node('ReqFile', '需求文件 .md\n• title: 项目名\n• version: 版本\n• author: 作者\n• 验收标准列表',
               fillcolor='#F57C00', fontcolor='white', fontsize='12')

    # 阶段2: 检测与解析
    with dot.subgraph(name='cluster_detect') as c:
        c.attr(style='filled', color='#E3F2FD', label='【阶段2: 检测解析】', pencolor='#0D47A1', **CLUSTER_STYLE)
        c.node('Detection', '需求检测引擎\n• 关键词匹配\n• .md 文件检测\n• 语言识别\n(C++/Python)', fillcolor='#1976D2', fontcolor='white')
        c.node('ReqParse', '需求文档解析\n• YAML Frontmatter\n• Markdown 解析\n• 提取验收标准\n• 需求项结构化',
               fillcolor='#1565C0', fontcolor='white')

    # 阶段3: Schema 处理
    with dot.subgraph(name='cluster_schema') as c:
        c.attr(style='filled', color='#E8F5E9', label='【阶段3: Schema 处理】', pencolor='#1B5E20', **CLUSTER_STYLE)
        c.node('Artifact', 'ArtifactGraph\n• 自动发现工件\n• 构建依赖图\n• 影响范围分析',
               fillcolor='#43A047', fontcolor='white')
        c.node('Event', 'EventBus\n• 发布事件\n• 事件过滤\n• 通知订阅者',
               fillcolor='#2E7D32', fontcolor='white')

    # 阶段4: 9阶段工作流
    with dot.subgraph(name='cluster_workflow') as c:
        c.attr(style='filled', color='#FFF8E1', label='【阶段4: 9阶段工作流执行】', pencolor='#FF8F00', **CLUSTER_STYLE)

        workflow_nodes = [
            ('WF1', 'P1: 创建结构\ninclude/src/tests/docs', '#FFC107'),
            ('WF2', 'P2: 生成代码\n核心类实现', '#FFB300'),
            ('WF3', 'P3: 代码审查\n质量分析', '#FFA000'),
            ('WF4', 'P4: 自动修复\n问题修正', '#FF8F00'),
            ('WF5', 'P5: 测试文档\n用例生成', '#FF6F00'),
            ('WF6', 'P6: 测试代码\n框架生成', '#E65100'),
            ('WF7', 'P7: 运行测试\n执行验证', '#BF360C'),
        ]
        for node_id, label, color in workflow_nodes:
            c.node(node_id, label, fillcolor=color, fontcolor='white', fontsize='11')

    # 阶段5: Delta 变更系统
    with dot.subgraph(name='cluster_delta') as c:
        c.attr(style='filled', color='#F3E5F5', label='【阶段5: Delta 变更系统】', pencolor='#4A148C', **CLUSTER_STYLE)
        c.node('Delta', 'DeltaSpec\n• 计算差异\n• 生成 DeltaHunk\n• 冲突检测\n• 增量写入',
               fillcolor='#8E24AA', fontcolor='white')
        c.node('Validation', 'ValidationEngine\n• 格式验证\n• 语义验证\n• 解析验证\n• 业务验证',
               fillcolor='#7B1FA2', fontcolor='white')

    # 阶段6: 工具执行
    with dot.subgraph(name='cluster_tools') as c:
        c.attr(style='filled', color='#E0F7FA', label='【阶段6: 工具执行】', pencolor='#006064', **CLUSTER_STYLE)
        tools = [
            ('T_FW', 'file_writer\nDelta 模式写入', '#00BCD4'),
            ('T_CR', 'code_review\n静态分析', '#00ACC1'),
            ('T_AF', 'auto_fixer\n自动修复', '#0097A7'),
            ('T_TD', 'test_doc_generator\n测试文档', '#00838F'),
            ('T_TG', 'test_generator\n测试代码', '#006064'),
            ('T_TR', 'test_runner\n运行测试', '#004D40'),
        ]
        for node_id, label, color in tools:
            c.node(node_id, label, fillcolor=color, fontcolor='white', fontsize='10')

    # 阶段7: 输出
    with dot.subgraph(name='cluster_output') as c:
        c.attr(style='filled', color='#F5F5F5', label='【阶段7: 输出】', pencolor='#424242', **CLUSTER_STYLE)
        outputs = [
            ('O_Code', '项目源码\nauth.h / auth.cpp', '#616161'),
            ('O_Test', '测试代码\ntest_auth.cpp', '#757575'),
            ('O_Doc', '文档\ntest_doc.md / README', '#9E9E9E'),
            ('O_Report', '执行报告\nWorkflow Report JSON', '#BDBDBD'),
            ('O_Log', '事件日志\nevents.jsonl', '#E0E0E0'),
        ]
        for node_id, label, color in outputs:
            c.node(node_id, label, fillcolor=color, fontcolor='black', fontsize='10')

    # 数据流连接
    dot.edge('UserQuery', 'Detection', penwidth='3', color='#E65100')
    dot.edge('ReqFile', 'ReqParse', penwidth='3', color='#E65100')

    dot.edge('Detection', 'WF1', penwidth='2', color='#1976D2')
    dot.edge('ReqParse', 'WF2', penwidth='2', color='#1976D2')

    # 工作流内部连接
    for i in range(6):
        dot.edge(f'WF{i+1}', f'WF{i+2}', penwidth='2', color='#FF8F00')

    # 工作流 → Delta
    dot.edge('WF1', 'Delta', penwidth='2', style='dashed')
    dot.edge('WF2', 'Delta', penwidth='2', style='dashed')
    dot.edge('WF4', 'Delta', penwidth='2', style='dashed')

    # Delta → Validation
    dot.edge('Delta', 'Validation', penwidth='3', color='#7B1FA2')

    # 工作流 → 工具
    dot.edge('WF2', 'T_FW', penwidth='2')
    dot.edge('WF3', 'T_CR', penwidth='2')
    dot.edge('WF4', 'T_AF', penwidth='2')
    dot.edge('WF5', 'T_TD', penwidth='2')
    dot.edge('WF6', 'T_TG', penwidth='2')
    dot.edge('WF7', 'T_TR', penwidth='2')

    # 工具 → 输出
    dot.edge('T_FW', 'O_Code', penwidth='2')
    dot.edge('T_TG', 'O_Test', penwidth='2')
    dot.edge('T_TD', 'O_Doc', penwidth='2')
    dot.edge('T_TR', 'O_Report', penwidth='2')

    # EventBus 连接所有阶段
    dot.edge('Detection', 'Event', style='dotted', penwidth='1')
    dot.edge('WF1', 'Event', style='dotted', penwidth='1')
    dot.edge('WF7', 'Event', style='dotted', penwidth='1')
    dot.edge('Event', 'O_Log', penwidth='2', style='dotted')

    # ArtifactGraph 连接
    dot.edge('O_Code', 'Artifact', style='dotted', penwidth='1')
    dot.edge('O_Test', 'Artifact', style='dotted', penwidth='1')
    dot.edge('O_Doc', 'Artifact', style='dotted', penwidth='1')

    dot.render(cleanup=True)
    print("[OK] 09_Complete_Data_Flow.png 生成完成")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  OpenSpec v2.0 架构图生成器")
    print("="*60 + "\n")

    create_architecture_overview()
    create_nine_phase_workflow()
    create_schema_architecture()
    create_validation_engine()
    create_artifact_graph()
    create_delta_flow()
    create_eventbus_arch()
    create_multilang_arch()
    create_complete_data_flow()

    print("\n" + "="*60)
    print("  所有架构图生成完成！共 9 张 PNG 图片")
    print("  输出目录: ./doc2.0/")
    print("="*60 + "\n")
