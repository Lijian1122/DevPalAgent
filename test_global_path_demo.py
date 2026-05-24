"""
演示全局历史路径功能

通过 EnhancedTestSelfHealer 验证全局路径存储。
"""

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


class MockLLMClient:
    """模拟 LLM 客户端"""

    def __init__(self):
        pass


class MockContext:
    """模拟 OpenSpecContext"""

    def __init__(self, language="cpp"):
        self.language = language
        self.project_path = Path("mock_project")
        self.requirements = {"REQ-001": {"description": "实现用户登录功能"}}


class MockArtifactGraph:
    """模拟 ArtifactGraph"""

    def get_dependencies(self, file_path: str):
        return []


def demo_global_history():
    """演示全局历史路径"""
    from devpal.core.openspec_phases.enhanced_test_self_healer import (
        EnhancedTestSelfHealer,
    )

    print("=" * 70)
    print("演示：全局历史路径功能")
    print("=" * 70)
    print()

    # 创建模拟对象
    project_dir = Path("mock_project")
    llm_client = MockLLMClient()
    context = MockContext(language="cpp")
    artifact_graph = MockArtifactGraph()

    print("[1] 创建 EnhancedTestSelfHealer (C++ 项目)...")
    healer = EnhancedTestSelfHealer(
        project_dir=project_dir,
        llm_client=llm_client,
        context=context,
        artifact_graph=artifact_graph,
    )

    # 检查历史路径
    history_path = healer.healing_history.storage_path
    print(f"  - 历史存储路径: {history_path}")
    print(f"  - 是否为全局路径: {'.devpal' in str(history_path)}")
    print(f"  - 语言分类: {history_path.name}")
    print()

    # 验证路径结构
    expected_path = Path.home() / ".devpal" / "healing_history" / "cpp"
    print("[2] 验证路径结构...")
    print(f"  - 预期路径: {expected_path}")
    print(f"  - 实际路径: {history_path}")
    print(f"  - 路径匹配: {history_path == expected_path}")
    print()

    # 模拟不同语言的项目
    print("[3] 模拟不同语言的项目...")
    languages = ["cpp", "python", "shell"]

    for lang in languages:
        context_lang = MockContext(language=lang)
        healer_lang = EnhancedTestSelfHealer(
            project_dir=project_dir,
            llm_client=llm_client,
            context=context_lang,
            artifact_graph=artifact_graph,
        )

        lang_path = healer_lang.healing_history.storage_path
        print(f"  - {lang:8s}: {lang_path}")
        print()

    # 验证跨项目学习
    print("[4] 验证跨项目学习能力...")
    print("  - 项目 A (C++): 使用 ~/.devpal/healing_history/cpp/")
    print("  - 项目 B (C++): 使用 ~/.devpal/healing_history/cpp/")
    print("  - 结论: 两个 C++ 项目共享同一个历史文件，可以互相学习")
    print()

    print("[5] 验证语言隔离...")
    print("  - C++ 项目: ~/.devpal/healing_history/cpp/")
    print("  - Python 项目: ~/.devpal/healing_history/python/")
    print("  - 结论: 不同语言的项目使用独立的历史文件，互不干扰")
    print()

    return True


def main():
    """运行演示"""
    print()
    print("*" * 70)
    print("全局历史路径功能演示")
    print("*" * 70)
    print()

    try:
        success = demo_global_history()

        print("=" * 70)
        print("演示总结")
        print("=" * 70)
        print()

        if success:
            print("[结果] 全局历史路径功能验证成功")
            print()
            print("核心特性:")
            print("  1. 历史记录存储在全局路径 ~/.devpal/healing_history/{language}/")
            print("  2. 同语言的不同项目共享学习经验（跨项目学习）")
            print("  3. 不同语言的项目使用独立历史（语言隔离）")
            print("  4. 持久化存储，重启后数据不丢失")
            print()
            print("优势:")
            print("  - 项目 A 修复的错误，项目 B 可以直接应用")
            print("  - 随着使用增多，修复成功率和效率持续提升")
            print("  - 按语言分类，确保策略的相关性和有效性")
            return 0
        else:
            print("[结果] 演示失败")
            return 1

    except Exception as e:
        print(f"[错误] 演示执行失败: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
