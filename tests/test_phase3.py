# -*- coding: utf-8 -*-
"""Test Phase 3 with Multi-LLM Provider"""

import sys
from pathlib import Path

from devpal.core.openspec_phases.base import OpenSpecContext
from devpal.core.openspec_phases.phase3_technical_design import Phase3TechnicalDesign
print("=== Testing Phase 3 with Multi-LLM Provider ===\n")

# 创建测试上下文
project_dir = Path("test_phase3_output")
project_dir.mkdir(exist_ok=True)

requirements_file = Path("requirements/simple_login.md")
if not requirements_file.exists():
    print(f"Error: {requirements_file} not found")
    sys.exit(1)

# 读取需求内容
requirements_content = requirements_file.read_text(encoding='utf-8')

context = OpenSpecContext(
    project_dir=project_dir,
    requirements_file=requirements_file
)
context.requirements_content = requirements_content
context.structured_requirements = {
    "title": "Simple Login System",
    "description": "A simple login system for testing",
    "language": "cpp"
}

# 创建 Phase 3 实例
phase3 = Phase3TechnicalDesign(context)

print("Starting Phase 3 execution...")
print(f"Project dir: {project_dir}")
print(f"Requirements length: {len(requirements_content)} chars")
print(f"Language: {context.structured_requirements.get('language')}\n")

try:
    # 执行 Phase 3
    result = phase3.execute()

    print("\n=== Phase 3 Result ===")
    print(f"Success: {result.success}")
    print(f"Message: {result.message}")

    if result.success:
        print(f"\nTech design length: {len(context.tech_design_content)} chars")
        print(f"LLM calls: {context.llm_calls}")
        print(f"Input tokens: {context.llm_input_tokens}")
        print(f"Output tokens: {context.llm_output_tokens}")
        print(f"Cache read tokens: {context.llm_cache_read_tokens}")
        print(f"Cache creation tokens: {context.llm_cache_creation_tokens}")

        # 显示技术设计的前500字符
        print(f"\nTech design preview:")
        print(context.tech_design_content[:500])
        print("...")

        print("\n[SUCCESS] Phase 3 test PASSED")
    else:
        print(f"\n[FAILED] Phase 3 test FAILED: {result.message}")
        if result.errors:
            for error in result.errors:
             print(f"  - {error}")
        sys.exit(1)

except Exception as e:
    print(f"\n[FAILED] Phase 3 test FAILED with exception:")
    print(f"  {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n=== Test completed successfully ===")
