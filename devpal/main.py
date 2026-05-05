# -*- coding: utf-8 -*-
"""
DevPal Agent 快速启动脚本
支持命令行模式和 Web UI 模式
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
  python -m devpal.main --web                    # 启动 Web UI
        """
    )

    parser.add_argument(
        "query",
        nargs="*",
        help="执行单次查询"
    )

    parser.add_argument(
        "--web",
        action="store_true",
        help="启动 Web UI 界面"
    )

    parser.add_argument(
        "--no-plan",
        action="store_true",
        help="禁用规划模式，直接执行"
    )

    args = parser.parse_args()

    if args.web:
        start_web_ui(args)
    else:
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
    print("DevPal Agent v1.1 - 阶段4多模态+工具链扩展")
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


def start_web_ui(args):
    """启动 Web UI 模式"""
    from devpal.web import HAS_GRADIO, main as web_main

    if HAS_GRADIO:
        print("=" * 60)
        print("DevPal Agent v1.1 - 启动 Web UI")
        print("=" * 60)
        print("正在启动 Web 服务器...")
        print("访问地址: http://localhost:7860")
        print()

    web_main()


if __name__ == "__main__":
    main()
