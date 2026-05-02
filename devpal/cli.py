# -*- coding: utf-8 -*-
"""
DevPal Agent CLI 入口
命令行交互界面
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from devpal.core import AgentEngine, AgentConfig


def main():
    parser = argparse.ArgumentParser(description="DevPal Agent - 你的智能开发助手")

    parser.add_argument(
        "query",
        nargs="*",
        help="要执行的查询（省略则进入交互模式）"
    )

    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="安静模式，不显示详细执行过程"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        default=True,
        help="详细模式（默认）"
    )

    parser.add_argument(
        "--show-tool-output",
        action="store_true",
        help="显示工具完整输出"
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=5,
        help="最大工具Calling轮数（默认 5）"
    )

    args = parser.parse_args()

    # 构建配置
    agent_config = AgentConfig(
        verbose=args.verbose and not args.quiet,
        show_tool_output=args.show_tool_output,
        max_iterations=args.max_iterations,
    )

    # 创建 Agent
    agent = AgentEngine(config=agent_config)

    # 如果有查询参数，单次执行；否则进入交互模式
    if args.query:
        query = " ".join(args.query)
        answer = agent.run(query)
        print("\n" + "=" * 60)
        print(" 最终回答:")
        print("=" * 60)
        print(answer)
    else:
        # 进入交互模式
        agent.chat()


if __name__ == "__main__":
    main()
