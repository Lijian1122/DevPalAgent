"""
测试新增的 Skills: TestGenerationSkill 和 OpenSpecSkill
"""
from pathlib import Path
from devpal.skills import SkillRouter, SkillContext
from devpal.skills.builtin import TestGenerationSkill, OpenSpecSkill


def test_test_generation_skill():
    """测试 TestGenerationSkill 的意图识别"""
    print("=" * 70)
    print("测试 TestGenerationSkill")
    print("=" * 70)

    skill = TestGenerationSkill()

    # 测试用例
    test_queries = [
        "生成测试用例 for file.cpp",
    "帮我写测试代码",
        "test generation for my code",
        "自动测试 file.py",
        "代码审查",  # 应该不匹配
    ]

    for query in test_queries:
        context = SkillContext(
            user_query=query,
         workspace_path=Path.cwd()
      )
        confidence = skill.can_handle(context)
        print(f"Query: '{query}'")
        print(f"  Confidence: {confidence:.2f}")
        print(f"  Match: {'YES' if confidence >= 0.8 else 'NO'}")
        print()


def test_openspec_skill():
    """测试 OpenSpecSkill 的意图识别"""
    print("=" * 70)
    print("测试 OpenSpecSkill")
    print("=" * 70)

    skill = OpenSpecSkill()

    # 测试用例
    test_queries = [
     "执行完整项目生成流程",
        "运行 openspec 11-phase workflow",
        "端到端需求到代码",
        "全流程生成 requirements/login.md",
        "生成安装脚本",  # 应该不匹配
    ]

    for query in test_queries:
        context = SkillContext(
            user_query=query,
            workspace_path=Path.cwd()
        )
        confidence = skill.can_handle(context)
        print(f"Query: '{query}'")
        print(f"  Confidence: {confidence:.2f}")
        print(f"  Match: {'YES' if confidence >= 0.8 else 'NO'}")
        print()


def test_skill_router():
    """测试 SkillRouter 对新 Skills 的路由"""
    print("=" * 70)
    print("测试 SkillRouter 路由")
    print("=" * 70)

    from devpal.skills.builtin import InstallerSkill, CodeReviewSkill, MultiAgentSkill

    router = SkillRouter([
        InstallerSkill(),
        CodeReviewSkill(),
        MultiAgentSkill(),
      TestGenerationSkill(),
        OpenSpecSkill()
    ], confidence_threshold=0.8)

  # 测试用例
    test_queries = [
     ("生成安装脚本", "InstallerSkill"),
      ("代码审查 file.cpp", "CodeReviewSkill"),
        ("多 Agent 协作", "MultiAgentSkill"),
        ("生成测试用例 file.py", "TestGenerationSkill"),
        ("执行完整项目 openspec 流程", "OpenSpecSkill"),
        ("这是一个复杂的需求", None),  # 应该 fallback
    ]

    for query, expected_skill in test_queries:
        context = SkillContext(
            user_query=query,
         workspace_path=Path.cwd()
        )
        skill, confidence = router.route(context)

        actual_skill = skill.name if skill else None
        match = "OK" if (skill and expected_skill and skill.name == expected_skill) or (not skill and not expected_skill) else "FAIL"

        print(f"Query: '{query}'")
        print(f"  Expected: {expected_skill}")
        print(f"  Actual: {actual_skill}")
        print(f"  Confidence: {confidence:.2f}")
        print(f"  Result: {match}")
        print()


if __name__ == "__main__":
    test_test_generation_skill()
    print("\n")
    test_openspec_skill()
    print("\n")
    test_skill_router()

    print("=" * 70)
    print("所有测试完成")
    print("=" * 70)
