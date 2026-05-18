# -*- coding: utf-8 -*-
"""
Phase skip rules for different project types
"""

from typing import Tuple


def should_skip_for_non_cpp_project(phase_num: int, context) -> Tuple[bool, str]:
    """
    判断非 C++ 项目是否应该跳过某个阶段

    Args:
        phase_num: 阶段编号
        context: OpenSpecContext 实例

    Returns:
        (should_skip, reason): 是否跳过和跳过原因
    """
    # 如果是 C++ 项目，不跳过任何阶段
    if context.is_cpp:
        return False, ""

    # 安装脚本项目的跳过规则
    is_installer = 'install' in context.features or context.project_type in ['installer', 'cli_tool', 'tooling']

    if is_installer:
        skip_rules = {
            3: "安装脚本项目不需要 AI 技术设计",
            5: "安装脚本项目不需要生成测试代码",
            6: "安装脚本项目不需要 CMake 配置",
            7: "安装脚本项目不需要测试文档",
            10: "安装脚本项目不需要编译和运行测试",
        }

        if phase_num in skip_rules:
            return True, skip_rules[phase_num]

    # Python 项目的跳过规则
    if context.language == 'python' and not context.is_cpp:
        skip_rules = {
            6: "Python 项目不需要 CMake 配置",
        }

        if phase_num in skip_rules:
            return True, skip_rules[phase_num]

    return False, ""
