# -*- coding: utf-8 -*-
"""
OpenSpec CLI 工具 - Phase 5: 深化与体验

命令行工具，提供以下功能:
- openspec diagnose: 代码健康度诊断
- openspec policy init: 初始化策略配置
- openspec rollout: 渐进式发布管理
- openspec status: 查看当前 OpenSpec 状态
"""

import sys
import argparse
from pathlib import Path
from typing import Optional


def cmd_diagnose(args):
    """诊断命令 - 扫描代码健康度"""
    from devpal.core.schema import DiagnosticEngine

    target = Path(args.target) if args.target else Path.cwd()

    print("=" * 70)
    print("OpenSpec 智能诊断引擎")
    print("=" * 70)
    print(f"扫描目标: {target}")
    print()

    engine = DiagnosticEngine()

    if args.file:
        issues = engine.scan_file(target / args.file)
        print(f"扫描文件: {args.file}")
        print(f"发现问题: {len(issues)} 个")
        for issue in issues:
            print(f"  [{issue.severity.value}] {issue.message}")
            if issue.file_path:
                print(f"    文件: {issue.file_path}:{issue.line_number}")
            if issue.suggestion:
                print(f"    建议: {issue.suggestion}")
    else:
        result = engine.scan_directory(target)
        report = engine.generate_report(result)
        print(report)

    return 0


def cmd_policy(args):
    """策略命令"""
    from devpal.core.schema import PolicyConfig

    if args.subcommand == 'init':
        output = Path(args.output) if args.output else Path.cwd() / "openspec_policy.yaml"

        print("=" * 70)
        print("OpenSpec 策略配置初始化")
        print("=" * 70)

        PolicyConfig.create_default_config(output)
        print(f"[OK] 配置文件已创建: {output}")
        print()
        print("配置文件包含:")
        print("  - 默认质量门禁设置")
        print("  - 验证规则参数")
        print("  - 变更策略")
        print("  - 发布策略")
        print()
        print("使用方法:")
        print("  openspec policy lint     # 验证配置")
        print("  openspec policy show     # 查看当前配置")

    elif args.subcommand == 'show':
        config_path = Path(args.config) if args.config else Path("openspec_policy.yaml")
        if not config_path.exists():
            print(f"[ERROR] 配置文件不存在: {config_path}")
            return 1

        from devpal.core.schema import PolicyConfig
        config = PolicyConfig(config_path)

        print("=" * 70)
        print("OpenSpec 策略配置")
        print("=" * 70)
        print(f"环境: {config.environment}")
        print()

        print("质量门禁:")
        for gate in config.all_quality_gates:
            print(f"  - {gate.name}:")
            print(f"    最小健康度: {gate.min_health_score}")
            print(f"    最大关键问题: {gate.max_critical_issues}")
            print(f"    最大高优先级问题: {gate.max_high_issues}")

        print()
        print("变更策略:")
        for strat in config.all_change_strategies:
            print(f"  - {strat.name}:")
            print(f"    自动应用: {strat.auto_apply}")
            print(f"    需要审查: {strat.require_review}")

        print()
        print("发布策略:")
        for strat in config.all_rollout_strategies:
            print(f"  - {strat.name}:")
            print(f"    类型: {strat.strategy_type}")
            print(f"    自动晋升: {strat.auto_promote}")

    elif args.subcommand == 'lint':
        config_path = Path(args.config) if args.config else Path("openspec_policy.yaml")
        if not config_path.exists():
            print(f"[ERROR] 配置文件不存在: {config_path}")
            return 1

        try:
            from devpal.core.schema import PolicyConfig
            PolicyConfig(config_path)
            print(f"[OK] 配置文件验证通过: {config_path}")
        except Exception as e:
            print(f"[ERROR] 配置文件验证失败: {e}")
            return 1

    return 0


def cmd_rollout(args):
    """发布命令"""
    from devpal.core.schema import RolloutEngine, RolloutType

    rollout_engine = RolloutEngine()

    if args.subcommand == 'canary':
        print("=" * 70)
        print("OpenSpec 金丝雀发布")
        print("=" * 70)

        name = args.name or "金丝雀发布"
        percentage = args.percentage or 10.0
        stages = args.stages or 5

        print(f"发布名称: {name}")
        print(f"初始比例: {percentage}%")
        print(f"阶段数: {stages}")
        print()

        result = rollout_engine.canary_rollout(
            name=name,
            canary_percentage=percentage,
            stages=stages
        )

        report = rollout_engine.generate_rollout_report(result)
        print(report)

    elif args.subcommand == 'incremental':
        print("=" * 70)
        print("OpenSpec 增量发布")
        print("=" * 70)

        stages = args.stages or 5
        print(f"阶段数: {stages}")
        print()

        result = rollout_engine.incremental_rollout(
            name=args.name or "增量发布",
            stages=stages
        )

        report = rollout_engine.generate_rollout_report(result)
        print(report)

    elif args.subcommand == 'list':
        rollouts = rollout_engine.list_rollouts()
        print("=" * 70)
        print("OpenSpec 发布历史")
        print("=" * 70)

        if not rollouts:
            print("暂无发布记录")
        else:
            for r in rollouts:
                status_icon = "✓" if r.status.value == 'completed' else "○"
                print(f"  {status_icon} {r.rollout_id}: {r.name} ({r.current_percentage:.1f}%)")

    return 0


def cmd_status(args):
    """状态命令 - 查看当前 OpenSpec 上下文状态"""
    print("=" * 70)
    print("OpenSpec 系统状态")
    print("=" * 70)

    try:
        from devpal.core.schema import OpenSpecContext

        work_dir = Path(args.workspace) if args.workspace else Path.cwd()
        ctx = OpenSpecContext.create(work_dir, auto_initialize=True)

        status = ctx.health_check()
        print(f"工作目录: {work_dir}")
        print(f"整体状态: {status['overall_status']}")
        print()

        print("组件状态:")
        for name, component_status in status['components'].items():
            print(f"  {name}: {component_status['status']}")

        if status['warnings']:
            print()
            print("警告:")
            for warning in status['warnings']:
                print(f"  - {warning}")

        if status['errors']:
            print()
            print("错误:")
            for error in status['errors']:
                print(f"  - {error}")

    except Exception as e:
        print(f"[ERROR] 无法获取状态: {e}")
        return 1

    return 0


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(
        description="OpenSpec CLI - 规范驱动开发工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  openspec diagnose                    # 诊断当前目录代码健康度
  openspec diagnose --target src/      # 诊断指定目录
  openspec policy init                 # 初始化策略配置
  openspec policy show                 # 查看当前策略配置
  openspec rollout canary              # 执行金丝雀发布
  openspec rollout incremental         # 执行增量发布
  openspec status                      # 查看系统状态
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # diagnose 命令
    diagnose_parser = subparsers.add_parser('diagnose', help='代码健康度诊断')
    diagnose_parser.add_argument('--target', help='扫描目标目录')
    diagnose_parser.add_argument('--file', help='扫描单个文件')
    diagnose_parser.set_defaults(func=cmd_diagnose)

    # policy 命令
    policy_parser = subparsers.add_parser('policy', help='策略配置管理')
    policy_subparsers = policy_parser.add_subparsers(dest='subcommand', required=True)

    policy_init = policy_subparsers.add_parser('init', help='初始化策略配置')
    policy_init.add_argument('--output', help='输出文件路径')

    policy_show = policy_subparsers.add_parser('show', help='查看策略配置')
    policy_show.add_argument('--config', help='配置文件路径')

    policy_lint = policy_subparsers.add_parser('lint', help='验证配置文件')
    policy_lint.add_argument('--config', help='配置文件路径')

    policy_parser.set_defaults(func=cmd_policy)

    # rollout 命令
    rollout_parser = subparsers.add_parser('rollout', help='渐进式发布管理')
    rollout_subparsers = rollout_parser.add_subparsers(dest='subcommand', required=True)

    canary_parser = rollout_subparsers.add_parser('canary', help='金丝雀发布')
    canary_parser.add_argument('--name', help='发布名称')
    canary_parser.add_argument('--percentage', type=float, help='初始发布比例')
    canary_parser.add_argument('--stages', type=int, help='阶段数')

    inc_parser = rollout_subparsers.add_parser('incremental', help='增量发布')
    inc_parser.add_argument('--name', help='发布名称')
    inc_parser.add_argument('--stages', type=int, help='阶段数')

    rollout_subparsers.add_parser('list', help='列出发布历史')

    rollout_parser.set_defaults(func=cmd_rollout)

    # status 命令
    status_parser = subparsers.add_parser('status', help='查看系统状态')
    status_parser.add_argument('--workspace', help='工作目录')
    status_parser.set_defaults(func=cmd_status)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
