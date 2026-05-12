#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OpenSpec 需求驱动开发 - C++ 认证系统生成

已重构为调用通用 OpenSpec 11 阶段流水线，
不再使用硬编码方式生成代码，统一代码生成入口。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from devpal.tools.registry import ToolRegistry
from devpal.core.openspec_phases import OpenSpecPhaseScheduler


def generate_auth_system(requirements_file: str = "requirements/login_requirements.md"):
    """
    基于需求文档生成完整的 C++ 认证系统

    使用 OpenSpec 11 阶段通用流水线：
    1. 需求解析
    2. 目录结构创建
    3. 技术设计文档
    4. 核心代码生成（模板系统）
    5. 测试代码生成
    6. CMake 构建配置
    7. 测试文档生成
    8. README 文档生成
    9. 代码审查
    10. 编译运行测试
    11. 最终报告

    Args:
        requirements_file: 需求文档路径
    """
    req_path = Path(requirements_file)
    if not req_path.exists():
        print(f"[ERROR] 需求文档不存在: {req_path.absolute()}")
        print(f"        请检查路径或指定正确的需求文档")
        return False

    # 创建工具注册表（简化版，无事件总线）
    tool_registry = ToolRegistry(event_bus=None)
    print(f"[INFO] 已加载工具: {', '.join(tool_registry.list_tool_names()[:10])}...")

    # 创建调度器并执行完整流水线
    scheduler = OpenSpecPhaseScheduler(str(req_path), tool_registry)
    result = scheduler.run_all_phases()

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="OpenSpec 需求驱动开发 - 生成 C++ 认证系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python generate_auth_system.py                           # 使用默认需求文档
  python generate_auth_system.py requirements/my_req.md   # 指定需求文档
        """
    )

    parser.add_argument(
        "requirements",
        nargs="?",
        default="requirements/login_requirements.md",
        help="需求文档路径 (默认: requirements/login_requirements.md)"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("  OpenSpec 需求驱动开发 - C++ 认证系统生成器")
    print("=" * 70)
    print(f"  需求文档: {args.requirements}")
    print(f"  架构设计: 调用通用 OpenSpec 11 阶段流水线")
    print(f"  模板系统: cpp_auth_header/cpp_auth_impl/cpp_main/cpp_auth_test...")
    print("=" * 70)
    print()

    generate_auth_system(args.requirements)
