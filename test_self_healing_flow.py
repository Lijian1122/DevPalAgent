"""
Self-Healing 流程独立测试

使用 cpp_simple_login 项目测试根因分析和修复策略选择流程。
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from devpal.core.self_healing import (
    ErrorContext,
    ErrorType,
    ErrorSeverity,
    RootCauseAnalyzer,
    HealingStrategySelector,
    HealingHistory,
    HealingRecord,
    StrategyType
)


class MockContext:
    """模拟 OpenSpecContext"""
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.requirements = {
        "REQ-001": {"description": "实现用户登录功能"},
            "REQ-002": {"description": "实现用户注册功能"}
        }


class MockArtifactGraph:
    """模拟 ArtifactGraph"""
    def get_dependencies(self, file_path: str):
        if "auth" in file_path:
            return ["src/user.cpp", "include/user.h"]
        return []


def test_compile_error_scenario():
    """测试场景1: 编译错误"""
    print("=" * 70)
    print("测试场景 1: 编译错误 - undefined reference")
    print("=" * 70)
    print()

    project_path = Path("cpp_simple_login")
    context = MockContext(project_path)
    artifact_graph = MockArtifactGraph()
    print("[1] 初始化根因分析器...")
    analyzer = RootCauseAnalyzer(artifact_graph=artifact_graph, context=context)

    print("[2] 初始化修复历史...")
    history_path = Path("test_healing_history")
    history_path.mkdir(exist_ok=True)
    history = HealingHistory(storage_path=history_path)

    print("[3] 初始化策略选择器...")
    selector = HealingStrategySelector(healing_history=history)
    print()

    error_output = """src/auth.cpp:42:5: error: undefined reference to login_user"""

    print("[Step 1] 构建错误上下文...")
    error_context = ErrorContext(
        error_message=error_output.strip(),
        error_type=ErrorType.UNKNOWN,
        severity=ErrorSeverity.CRITICAL,
        file_path=Path("src/auth.cpp"),
        line_number=42,
        phase="Phase 10: Test Execution",
        timestamp=datetime.now().isoformat()
    )
    print(f"  - 错误文件: {error_context.file_path}")
    print(f"  - 错误行号: {error_context.line_number}")
    print()

    print("[Step 2] 执行根因分析...")
    root_cause = analyzer.analyze(error_context)
  print(f"  - 错误类型: {root_cause.error_context.error_type.value}")
    print(f"  - 根因类型: {root_cause.root_cause_type}")
    print(f"  - 根因描述: {root_cause.root_cause_description}")
    print(f"  - 置信度: {root_cause.confidence:.2f}")
    print()

    if root_cause.trace_chain:
        print("  - 追溯链路:")
        for i, node in enumerate(root_cause.trace_chain, 1):
            print(f"    {i}. [{node.node_type}] {node.node_id}: {node.content}")
    print()

    if root_cause.suggested_fixes:
        print("  - 建议修复:")
        for i, fix in enumerate(root_cause.suggested_fixes, 1):
            print(f"    {i}. {fix}")
    print()

    print("[Step 3] 选择修复策略...")
    strategies = selector.select_strategy(root_cause)
    print(f"  - 生成策略数: {len(strategies)}")
    for i, strategy in enumerate(strategies, 1):
      print(f"  - 策略 {i}: {strategy.strategy_type.value}")
        print(f"    置信度: {strategy.confidence:.2f}, 预计耗时: {strategy.estimated_time:.1f}s")
    print()

    print("[Step 4] 模拟修复执行...")
    if strategies:
        record = HealingRecord(
            record_id="test_001",
            error_context=error_context,
            root_cause=root_cause,
            strategy=strategies[0],
            success=True,
            execution_time=45.2,
            timestamp=datetime.now(),
            retry_count=0
        )
        history.add_record(record)
        print(f"  - 修复记录已保存, 结果: 成功, 耗时: 45.2s")
    print()

    print("[Step 5] 查看修复统计...")
    stats = history.get_statistics()
    print(f"  - 总记录数: {stats['total_records']}")
  print(f"  - 成功率: {stats['success_rate']:.1%}")
    print()

    return True


def test_similar_error_learning():
    """测试场景2: 相似错误学习"""
    print("=" * 70)
    print("测试场景 2: 相似错误学习")
    print("=" * 70)
    print()

    history_path = Path("test_healing_history")
    history = HealingHistory(storage_path=history_path)
    print(f"[1] 加载历史记录: {len(history.records)} 条")
    print()

    similar_error = ErrorContext(
        error_message="undefined reference to register_user",
        error_type=ErrorType.SYNTAX,
        severity=ErrorSeverity.CRITICAL,
        file_path=Path("src/auth.cpp"),
        line_number=58,
        timestamp=datetime.now().isoformat()
    )

    print("[2] 查找相似错误...")
    similar_records = history.find_similar_errors(similar_error, similarity_threshold=0.6)
    print(f"  - 找到 {len(similar_records)} 条相似记录")

    for i, record in enumerate(similar_records, 1):
        similarity = history._calculate_similarity(similar_error, record.error_context)
        print(f"  - 记录 {i}: 相似度 {similarity:.2f}, 成功: {record.success}")
    print()

    if similar_records:
        print("[3] 应用历史学习策略...")
        context = MockContext(Path("cpp_simple_login"))
        artifact_graph = MockArtifactGraph()
        analyzer = RootCauseAnalyzer(artifact_graph=artifact_graph, context=context)
        selector = HealingStrategySelector(healing_history=history)

        root_cause = analyzer.analyze(similar_error)
        strategies = selector.select_strategy(root_cause)

        historical_strategies = [s for s in strategies if "[历史学习]" in s.description]
        print(f"  - 历史学习策略数: {len(historical_strategies)}")
    print()

    return True


def cleanup():
    """清理测试数据"""
    import shutil
    history_path = Path("test_healing_history")
    if history_path.exists():
        shutil.rmtree(history_path)
     print("[清理] 测试历史数据已删除")


def main():
    """运行所有测试场景"""
    print()
    print("*" * 70)
    print("Self-Healing 流程独立测试 - cpp_simple_login 项目")
    print("*" * 70)
    print()

    try:
        success1 = test_compile_error_scenario()
      success2 = test_similar_error_learning()
      print("=" * 70)
        print("测试总结")
        print("=" * 70)
        print(f"场景1 (编译错误): {'通过' if success1 else '失败'}")
        print(f"场景2 (历史学习): {'通过' if success2 else '失败'}")
        print()

        if success1 and success2:
          print("[结果] 所有测试场景通过")
            return 0
        else:
        print("[结果] 部分测试场景失败")
            return 1

    except Exception as e:
        print(f"[错误] 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
      print()
        cleanup()


if __name__ == "__main__":
    sys.exit(main())
