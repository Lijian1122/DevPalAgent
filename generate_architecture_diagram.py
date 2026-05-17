#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DevPal Agent v2.0 架构图生成器
使用 matplotlib 生成高质量的架构图 PNG
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def create_architecture_diagram():
    """创建 DevPal Agent v2.0 完整架构图"""

    fig, ax = plt.subplots(figsize=(20, 28))
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 28)
    ax.axis('off')

    # 颜色方案
    colors = {
        'interface': '#E3F2FD',
        'workflow': '#FFF3E0',
        'core': '#F3E5F5',
        'spec': '#E8F5E9',
        'defense': '#FFEBEE',
        'tools': '#FFF9C4',
     'infra': '#E0F2F1',
        'border': '#424242',
        'text': '#212121'
    }

    # 标题
    title_box = FancyBboxPatch((1, 26.5), 18, 1.2,
                   boxstyle="round,pad=0.1",
                          edgecolor=colors['border'],
              facecolor='#1976D2',
                   linewidth=3)
    ax.add_patch(title_box)
    ax.text(10, 27.1, 'DevPal Agent v2.0 - 完整架构图',
            ha='center', va='center', fontsize=24, fontweight='bold', color='white')
    ax.text(10, 26.7, '7层架构 + 防幻觉体系 + 11阶段工作流',
          ha='center', va='center', fontsize=14, color='white')

    # Layer 1: 交互层
    y_start = 24.5
    layer1_box = FancyBboxPatch((1, y_start), 18, 1.8,
                       boxstyle="round,pad=0.05",
                        edgecolor=colors['border'],
                          facecolor=colors['interface'],
               linewidth=2)
    ax.add_patch(layer1_box)
    ax.text(10, y_start + 1.5, 'Layer 1: 交互层 (Interface)',
        ha='center', va='center', fontsize=16, fontweight='bold')

    # 交互层组件
    components = ['CLI\n命令行', 'Web UI\n界面', 'IDE 插件\n扩展', 'API 接口\n服务']
    x_positions = [3, 7, 11, 15]
    for comp, x in zip(components, x_positions):
        comp_box = FancyBboxPatch((x-1.5, y_start+0.2), 3, 1,
                          boxstyle="round,pad=0.05",
                            edgecolor=colors['border'],
                              facecolor='white',
                        linewidth=1.5)
        ax.add_patch(comp_box)
        ax.text(x, y_start+0.7, comp, ha='center', va='center', fontsize=11)

    # 箭头到 Layer 2
    arrow1 = FancyArrowPatch((10, y_start), (10, y_start-0.3),
                        arrowstyle='->', mutation_scale=30,
                          linewidth=3, color=colors['border'])
    ax.add_patch(arrow1)

    # Layer 2: 工作流执行层
    y_start = 18
    layer2_box = FancyBboxPatch((1, y_start), 18, 6,
                      boxstyle="round,pad=0.05",
                 edgecolor=colors['border'],
                       facecolor=colors['workflow'],
                 linewidth=2)
    ax.add_patch(layer2_box)
    ax.text(10, y_start + 5.6, 'Layer 2: 工作流执行层 (Workflow)',
            ha='center', va='center', fontsize=16, fontweight='bold')

    # OpenSpec 工作流
    workflow_box = FancyBboxPatch((1.5, y_start+0.3), 17, 5,
                    boxstyle="round,pad=0.05",
                              edgecolor='#FF6F00',
                                  facecolor='#FFF8E1',
                         linewidth=2)
    ax.add_patch(workflow_box)
    ax.text(10, y_start+5, 'OpenSpecWorkflowExecutor - 11阶段需求驱动开发引擎',
            ha='center', va='center', fontsize=13, fontweight='bold', color='#E65100')

    # 11个阶段
    phases = [
        'Phase 1: 🔍 需求文档解析', 'Phase 2: 📁 创建项目结构',
        'Phase 3: 💻 生成核心代码', 'Phase 4: 📊 代码质量审查',
        'Phase 5: 🔧 自动修复', 'Phase 6: 📝 生成测试文档',
        'Phase 7: 📚 生成 README', 'Phase 8: 🔍 代码审查报告',
    'Phase 9: 🧪 编译运行测试', 'Phase 10: ✅ 生成验证报告',
        'Phase 11: 📖 技术实现文档'
    ]

    y_phase = y_start + 4.3
    for i, phase in enumerate(phases):
        if i < 6:
            ax.text(2.5, y_phase - i*0.35, phase, ha='left', va='center', fontsize=9)
        else:
         ax.text(11, y_phase - (i-6)*0.35, phase, ha='left', va='center', fontsize=9)

    # 箭头到 Layer 3
    arrow2 = FancyArrowPatch((10, y_start), (10, y_start-0.3),
                    arrowstyle='->', mutation_scale=30,
             linewidth=3, color=colors['border'])
    ax.add_patch(arrow2)

    # Layer 3: Agent 核心引擎
    y_start = 14.5
    layer3_box = FancyBboxPatch((1, y_start), 18, 3.2,
                       boxstyle="round,pad=0.05",
                       edgecolor=colors['border'],
                      facecolor=colors['core'],
                  linewidth=2)
    ax.add_patch(layer3_box)
    ax.text(10, y_start + 2.9, 'Layer 3: Agent 核心引擎 (Core)',
          ha='center', va='center', fontsize=16, fontweight='bold')

    # Planner, Executor, Reflector
    agent_components = [
        ('Planner\n规划器', 3.5, ['任务拆解', '步骤规划', '可行性评估']),
        ('Executor\n执行器', 10, ['工具调用', '状态管理', '结果收集']),
        ('Reflector\n反思器', 16.5, ['错误检测', '自我纠正', '经验总结'])
    ]

    for comp, x, features in agent_components:
        comp_box = FancyBboxPatch((x-2, y_start+1.2), 4, 1.5,
                    boxstyle="round,pad=0.05",
                      edgecolor=colors['border'],
                           facecolor='#F8BBD0',
                      linewidth=1.5)
        ax.add_patch(comp_box)
        ax.text(x, y_start+2.3, comp, ha='center', va='center',
            fontsize=11, fontweight='bold')
        for i, feat in enumerate(features):
            ax.text(x, y_start+1.8-i*0.25, f'• {feat}', ha='center', va='center', fontsize=8)

    # 箭头连接
    arrow_p_e = FancyArrowPatch((5.5, y_start+1.9), (8, y_start+1.9),
                      arrowstyle='->', mutation_scale=20,
                     linewidth=2, color=colors['border'])
    ax.add_patch(arrow_p_e)
    arrow_e_r = FancyArrowPatch((12, y_start+1.9), (14.5, y_start+1.9),
                       arrowstyle='->', mutation_scale=20,
                     linewidth=2, color=colors['border'])
    ax.add_patch(arrow_e_r)

    # ToolRegistry
    tool_box = FancyBboxPatch((7, y_start+0.2), 6, 0.8,
              boxstyle="round,pad=0.05",
                       edgecolor=colors['border'],
                        facecolor='#FFCCBC',
                     linewidth=1.5)
    ax.add_patch(tool_box)
    ax.text(10, y_start+0.6, 'ToolRegistry 工具注册表 (26个内置工具)',
            ha='center', va='center', fontsize=10, fontweight='bold')

    # 箭头到 Layer 4
    arrow3 = FancyArrowPatch((10, y_start), (10, y_start-0.3),
                          arrowstyle='->', mutation_scale=30,
                             linewidth=3, color=colors['border'])
    ax.add_patch(arrow3)

    # Layer 4: 规范引擎层
    y_start = 10
    layer4_box = FancyBboxPatch((1, y_start), 18, 4.2,
                         boxstyle="round,pad=0.05",
                    edgecolor=colors['border'],
                                facecolor=colors['spec'],
                linewidth=2)
    ax.add_patch(layer4_box)
    ax.text(10, y_start + 3.9, 'Layer 4: 规范引擎层 (Spec Engine)',
            ha='center', va='center', fontsize=16, fontweight='bold')

    # 规范引擎组件（简化显示）
    ax.text(10, y_start + 3.2, 'ValidationEngine | DeltaEngine | ArtifactGraph',
         ha='center', va='center', fontsize=11, fontweight='bold')
    ax.text(10, y_start + 2.7, '四层验证流水线 | 增量变更引擎 | 工件依赖图',
         ha='center', va='center', fontsize=9)
    ax.text(10, y_start + 1.8, 'EventBus | StateManager | CompileDB',
            ha='center', va='center', fontsize=11, fontweight='bold')
    ax.text(10, y_start + 1.3, '事件总线 | 状态持久化 | 编译数据库',
            ha='center', va='center', fontsize=9)

    # 箭头到 Layer 5
    arrow4 = FancyArrowPatch((10, y_start), (10, y_start-0.3),
                     arrowstyle='->', mutation_scale=30,
                    linewidth=3, color=colors['border'])
    ax.add_patch(arrow4)

    # Layer 5: 防御层
    y_start = 5.5
    layer5_box = FancyBboxPatch((1, y_start), 18, 4.2,
                                boxstyle="round,pad=0.05",
              edgecolor=colors['border'],
                  facecolor=colors['defense'],
                           linewidth=2)
    ax.add_patch(layer5_box)
    ax.text(10, y_start + 3.9, 'Layer 5: 防御层 (Anti-Hallucination)',
            ha='center', va='center', fontsize=16, fontweight='bold')

    # HallucinationDetector
    halluc_box = FancyBboxPatch((1.5, y_start+2.2), 17, 1.5,
                         boxstyle="round,pad=0.05",
                     edgecolor='#C62828',
                           facecolor='#FFCDD2',
             linewidth=2)
    ax.add_patch(halluc_box)
    ax.text(10, y_start+3.4, 'HallucinationDetector - 幻觉检测器',
            ha='center', va='center', fontsize=12, fontweight='bold', color='#B71C1C')

    # 四种检测类型
    detect_types = ['tool_call\n工具调用', 'plan\n计划步骤', 'code\n代码生成', 'fact\n事实校验']
    x_positions = [3.5, 7.5, 11.5, 15.5]
    for comp, x in zip(detect_types, x_positions):
        comp_box = FancyBboxPatch((x-1.5, y_start+2.4), 3, 0.8,
                      boxstyle="round,pad=0.03",
                          edgecolor='#D32F2F',
                 facecolor='white',
                     linewidth=1)
        ax.add_patch(comp_box)
        ax.text(x, y_start+2.8, comp, ha='center', va='center', fontsize=9, fontweight='bold')

    # ValidationEngine
    valid_box = FancyBboxPatch((1.5, y_start+0.3), 17, 1.7,
                      boxstyle="round,pad=0.05",
                          edgecolor='#1565C0',
              facecolor='#BBDEFB',
                       linewidth=2)
    ax.add_patch(valid_box)
    ax.text(10, y_start+1.7, 'ValidationEngine - 四层验证流水线',
            ha='center', va='center', fontsize=12, fontweight='bold', color='#0D47A1')

    # 四层验证
    layers = ['L1: Format', 'L2: Semantic', 'L3: Parser', 'L4: Business']
    x_positions = [3, 7, 11, 15]
    for layer, x in zip(layers, x_positions):
        ax.text(x, y_start+1.1, layer, ha='center', va='center', fontsize=9)

    # 风险等级
    ax.text(2, y_start+0.5, '风险等级: 🔴 高 | 🟡 中 | 🟢 低',
            ha='left', va='center', fontsize=9, fontweight='bold')

    # 箭头到 Layer 6
    arrow5 = FancyArrowPatch((10, y_start), (10, y_start-0.3),
                       arrowstyle='->', mutation_scale=30,
                    linewidth=3, color=colors['border'])
    ax.add_patch(arrow5)
    # Layer 6: 工具层
    y_start = 2.5
    layer6_box = FancyBboxPatch((1, y_start), 18, 2.7,
                        boxstyle="round,pad=0.05",
                          edgecolor=colors['border'],
                       facecolor=colors['tools'],
                   linewidth=2)
    ax.add_patch(layer6_box)
    ax.text(10, y_start + 2.4, 'Layer 6: 工具层 (Tools - 26个)',
         ha='center', va='center', fontsize=16, fontweight='bold')

    # 工具分类
    tool_text = '📁 文件操作(3) | 💻 系统编译(4) | 🌿 代码质量(4) | 🧪 测试编排(5)\n🚀 OpenSpec(3) | 🔄 自我改进(3) | 🧩 其他工具(2)'
    ax.text(10, y_start + 1.2, tool_text, ha='center', va='center', fontsize=10)

    # 箭头到 Layer 7
    arrow6 = FancyArrowPatch((10, y_start), (10, y_start-0.3),
                      arrowstyle='->', mutation_scale=30,
                        linewidth=3, color=colors['border'])
    ax.add_patch(arrow6)

    # Layer 7: 基础能力层
    y_start = 0.3
    layer7_box = FancyBboxPatch((1, y_start), 18, 1.9,
                      boxstyle="round,pad=0.05",
                         edgecolor=colors['border'],
                    facecolor=colors['infra'],
                       linewidth=2)
    ax.add_patch(layer7_box)
    ax.text(10, y_start + 1.6, 'Layer 7: 基础能力层 (Infrastructure)',
            ha='center', va='center', fontsize=16, fontweight='bold')

    # 基础组件
    infra_components = ['LLM SDK\n大模型封装', 'Memory\n记忆系统', 'Multimodal\n多模态支持', 'Plugin\n插件系统']
    x_positions = [3.5, 7.5, 11.5, 15.5]
    for comp, x in zip(infra_components, x_positions):
        comp_box = FancyBboxPatch((x-1.8, y_start+0.2), 3.6, 1.2,
                          boxstyle="round,pad=0.03",
                         edgecolor=colors['border'],
                             facecolor='#B2DFDB',
                             linewidth=1.5)
        ax.add_patch(comp_box)
        ax.text(x, y_start+0.8, comp, ha='center', va='center', fontsize=10, fontweight='bold')

    # 保存图片
    plt.tight_layout()
    plt.savefig('docs/DevPal_Agent_v2.0_Architecture.png',
         dpi=300, bbox_inches='tight', facecolor='white')
    print("✅ 架构图已生成: docs/DevPal_Agent_v2.0_Architecture.png")
    plt.close()


if __name__ == '__main__':
    create_architecture_diagram()
