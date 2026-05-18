#!/usr/bin/env python3
"""简单测试脚本 - 只运行关键阶段，节省 token"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from devpal.core.openspec_phases import OpenSpecPhaseScheduler
from devpal.tools.registry import ToolRegistry

def main():
    # 清理旧项目和 checkpoint
    import shutil
    for old_dir in ['test_phase_skip', 'cpp_test_phase_skip', '.spec']:
        if Path(old_dir).exists():
            shutil.rmtree(old_dir)
            print(f"Cleaned up {old_dir}")

    # 运行测试
    print("\n" + "="*60)
    print("Running OpenSpec test...")
    print("="*60 + "\n")

    tool_registry = ToolRegistry()
    scheduler = OpenSpecPhaseScheduler('requirements/test_phase_skip.md', tool_registry)
    result = scheduler.run_all_phases(resume=False)  # 禁用 checkpoint resume

    print("\n" + "="*60)
    print(f"Test result: {result}")
    print("="*60)

    # 检查生成的文件
    project_dir = Path('test_phase_skip')
    if project_dir.exists():
        print("\nGenerated files:")
        for py_file in sorted(project_dir.rglob("*.py")):
            print(f"  - {py_file.relative_to(project_dir)}")

        # 检查日志
        log_files = list(project_dir.glob("*.log"))
        if log_files:
            print(f"\nLog file: {log_files[0].name}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
