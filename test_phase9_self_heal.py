#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Phase 9 自愈功能

这个脚本会：
1. 运行 Phase 9 Quality Gate
2. 触发代码审查，检测 test_code_issues.cpp 中的问题
3. 触发自愈机制，自动修复 Critical 问题
4. 验证修复效果
"""

import sys
import io
from pathlib import Path

# 设置 stdout 编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from devpal.core.openspec_phases.phase9_quality_gate import Phase9QualityGate
from devpal.core.openspec_phases.base import OpenSpecContext
from devpal.core.llm_client import get_llm_client
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("=" * 80)
    print("Phase 9 Self-Heal Test")
    print("=" * 80)
    print()

    # 创建上下文
    project_dir = project_root / "cpp_simple_login"
    requirements_file = project_root / "requirements" / "simple_login.md"

    if not project_dir.exists():
        print(f"❌ Project directory not found: {project_dir}")
        return 1

    if not requirements_file.exists():
        print(f"❌ Requirements file not found: {requirements_file}")
        return 1

    context = OpenSpecContext(
        requirements_file=requirements_file,
        project_dir=project_dir
    )

    # 创建 LLM 客户端
    llm_client = get_llm_client()

    # 创建 Phase 9 实例（启用自愈）
    phase9 = Phase9QualityGate(context, tool_registry=None, llm_client=llm_client)

    # 确保自愈配置已启用
    phase9.config['code_review']['enabled'] = True
    phase9.config['code_review']['self_heal']['enabled'] = True
    phase9.config['code_review']['self_heal']['only_critical'] = True
    phase9.config['code_review']['self_heal']['max_attempts'] = 3
    phase9.config['code_review']['self_heal']['switch_model_after'] = 2

    print("Configuration:")
    print(f"  - Code Review: {phase9.config['code_review']['enabled']}")
    print(f"  - Self-Heal: {phase9.config['code_review']['self_heal']['enabled']}")
    print(f"  - Only Critical: {phase9.config['code_review']['self_heal']['only_critical']}")
    print(f"  - Max Attempts: {phase9.config['code_review']['self_heal']['max_attempts']}")
    print(f"  - Switch Model After: {phase9.config['code_review']['self_heal']['switch_model_after']}")
    print()

    # 运行 Phase 9
    print("Running Phase 9 Quality Gate...")
    print()

    try:
        result = phase9.execute()

        print()
        print("=" * 80)
        print("Phase 9 Result")
        print("=" * 80)
        print(f"Status: {'✅ PASSED' if result.success else '❌ FAILED'}")
        print()

        # 读取报告
        report_path = project_dir / "docs" / "quality_gate_report.md"
        if report_path.exists():
            print("Quality Gate Report:")
            print("-" * 80)
            print(report_path.read_text(encoding='utf-8'))
            print("-" * 80)
        else:
            print("⚠️  Report not found")

        return 0 if result.success else 1

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
