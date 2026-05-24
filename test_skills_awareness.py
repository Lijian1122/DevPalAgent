#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Skills LLM Awareness Implementation
"""
import sys
sys.path.insert(0, '.')

from devpal.skills import SkillRouter
from devpal.skills.builtin import (
    InstallerSkill,
    CodeReviewSkill,
    MultiAgentSkill,
    TestGenerationSkill,
    OpenSpecSkill
)
from devpal.core.planner import Plan

print("=" * 60)
print("Test 1: Skills Formatting")
print("=" * 60)

# Create skill router
skill_router = SkillRouter([
    InstallerSkill(),
    CodeReviewSkill(),
    MultiAgentSkill(),
    TestGenerationSkill(),
    OpenSpecSkill()
])

# Test that skills are registered
assert len(skill_router.skills) == 5
print(f"[OK] {len(skill_router.skills)} skills registered")

# Test skill names
skill_names = [s.name for s in skill_router.skills]
assert "openspec_skill" in skill_names
assert "test_generation_skill" in skill_names
assert "code_review_skill" in skill_names
print(f"[OK] All expected skills found: {', '.join(skill_names)}")

print("\n" + "=" * 60)
print("Test 2: Plan with recommended_skill field")
print("=" * 60)

# Test Plan dataclass has recommended_skill field
plan = Plan(
    original_query="Test query",
    overall_goal="Test goal",
    recommended_skill="openspec_skill"
)

assert hasattr(plan, 'recommended_skill')
assert plan.recommended_skill == "openspec_skill"
print(f"[OK] Plan.recommended_skill field works: {plan.recommended_skill}")

print("\n" + "=" * 60)
print("Test 3: Planner System Prompt")
print("=" * 60)

from devpal.core.planner import Planner
from devpal.tools.registry import registry

planner = Planner(tool_registry=registry)
system_prompt = planner.system_prompt

# Check if Skills are mentioned
assert "Skills" in system_prompt
assert "openspec_skill" in system_prompt
assert "recommended_skill" in system_prompt
print("[OK] Planner system prompt includes Skills awareness")
print(f"\nPrompt length: {len(system_prompt)} characters")

# Show relevant section
lines = system_prompt.split('\n')
for i, line in enumerate(lines):
    if 'Available capabilities' in line:
        print("\nRelevant section:")
        print('\n'.join(lines[i:i+5]))
        break

print("\n" + "=" * 60)
print("All Tests PASSED!")
print("=" * 60)
