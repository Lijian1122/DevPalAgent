# -*- coding: utf-8 -*-
"""
OpenSpec 完整工作流测试脚本

使用 OpenSpecWorkflowExecutor 执行完整的 11 阶段流程。

Prerequisites:
  1. pip install anthropic pyyaml
  2. Set env ANTHROPIC_AUTH_TOKEN (or edit config/config.yaml with anthropic.auth_token)
  3. A requirements file under requirements/*.md
"""

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from devpal.core.openspec_executor import OpenSpecRunOptions, OpenSpecWorkflowExecutor
from devpal.tools.registry import registry as tool_registry


def main() -> int:
    """执行 OpenSpec 完整工作流

    Returns:
        int: 退出码 (0=成功, 1=失败)
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='OpenSpec 需求驱动开发工作流',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_ai_flow.py
  python run_ai_flow.py -r requirements/simple_login.md
  python run_ai_flow.py --no-abort  # 关键阶段失败时不终止
  python run_ai_flow.py --resume    # 从项目 checkpoint 恢复"""
    )
    parser.add_argument(
        '--requirements', '-r',
        default='requirements/simple_login.md',
        help='需求文档路径 (默认: requirements/simple_login.md)'
    )
    parser.add_argument(
        '--no-abort',
        action='store_true',
        help='关键阶段失败时不终止流程（默认会终止）'
    )
    parser.add_argument(
        '--force-regenerate-code',
        action='store_true',
        help='强制重新生成所有业务代码（默认为增量模式：仅在需求变更时重新生成）'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
      help='从项目 .spec/checkpoint.json 恢复执行（默认从头执行）'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
      help='启用详细输出模式'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试日志（包含所有 DEBUG 级别信息）'
    )
    args = parser.parse_args()

    # 检查需求文件
    requirements_file = ROOT / args.requirements
    if not requirements_file.exists():
        print(f"[ERROR] 需求文件不存在: {requirements_file}")
        return 1

    # 检查 API 密钥
    if not os.environ.get("ANTHROPIC_AUTH_TOKEN") and not os.environ.get("ANTHROPIC_API_KEY"):
        print("[WARNING] ANTHROPIC_AUTH_TOKEN / ANTHROPIC_API_KEY 未设置")
        print("      请设置环境变量或填充 config/config.yaml 后再运行")
        print()

    # 创建执行器并执行
    executor = OpenSpecWorkflowExecutor(tool_registry)
    result = executor.run(
        str(requirements_file),
        OpenSpecRunOptions(
            abort_on_critical_failure=not args.no_abort,
            enable_timeout=True,
            enable_retry=True,
            enable_checkpoint=True,
            enable_progress=True,
              resume=args.resume,
            force_regenerate_code=args.force_regenerate_code,
        ),
    )

    # 处理结果
    if not result['success']:
        print("\n" + "=" * 70)
        print(
            f"[CRITICAL] 流程失败于 Phase {result['failed_phase']}: "
            f"{result['failed_phase_name']}"
        )
        print(f"错误: {result['error_message']}")

        if result.get('errors'):
            print("详细错误:")
            for error in result['errors']:
                print(f"  - {error}")

        if result.get('log_file'):
            print(f"\n详细日志: {result['log_file']}")

        print("=" * 70)
        return 1

    # 成功
    print("\n[SUCCESS] 流程成功完成")
    if result.get('log_file'):
        print(f"详细日志: {result['log_file']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
