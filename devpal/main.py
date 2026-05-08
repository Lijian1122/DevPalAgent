# -*- coding: utf-8 -*-
"""
DevPal Agent 快速启动脚本
命令行模式
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from devpal.core import AgentEngine, AgentConfig


def main():
    """快速启动"""
    parser = argparse.ArgumentParser(
        description="DevPal Agent - AI 开发助手",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m devpal.main "帮我读取当前目录结构"       # 单次查询
  python -m devpal.main                          # 交互模式
        """
    )

    parser.add_argument(
        "query",
        nargs="*",
        help="执行单次查询"
    )

    parser.add_argument(
        "--no-plan",
        action="store_true",
        help="禁用规划模式，直接执行"
    )

    args = parser.parse_args()

    start_cli(args)


def start_cli(args):
    """启动命令行模式"""
    config = AgentConfig(
        verbose=True,
        show_tool_output=True,
        enable_planning=not args.no_plan
    )
    agent = AgentEngine(config=config)

    print("=" * 60)
    print("DevPal Agent v2.0 - OpenSpec 闭环集成")
    print("=" * 60)
    print(f"已加载工具: {', '.join(agent.tool_registry.list_tool_names())}")
    print()

    if args.query:
        # 单次查询
        query = " ".join(args.query)
        answer = agent.run(query)
        print("\n" + "=" * 60)
        print(" 最终回答:")
        print("=" * 60)
        print(answer)
    else:
        # 交互模式
        agent.chat()


if __name__ == "__main__":
    main()
