# -*- coding: utf-8 -*-
"""
DevPal Agent 快速启动脚本
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from devpal.core import AgentEngine, AgentConfig


def main():
    """快速启动"""
    config = AgentConfig(verbose=True, show_tool_output=True)
    agent = AgentEngine(config=config)

    print("=" * 60)
    print("DevPal Agent v1.0 - 阶段1完整工具系统")
    print("=" * 60)
    print(f"已加载工具: {', '.join(agent.tool_registry.list_tool_names())}")
    print()

    if len(sys.argv) > 1:
        # 单次查询
        query = " ".join(sys.argv[1:])
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
