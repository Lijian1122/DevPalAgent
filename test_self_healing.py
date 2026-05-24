"""
Self-Healing 根因分析功能测试

测试核心模块的基本功能。
"""

import sys
import traceback
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime

from devpal.core.self_healing import (
    ErrorContext,
    ErrorSeverity,
    ErrorType,
    HealingHistory,
    HealingRecord,
    HealingStrategy,
    HealingStrategySelector,
    RootCause,
    RootCauseAnalyzer,
    StrategyType,
    TraceNode,
)


def test_error_context():
    """测试错误上下文创建"""
    print("Testing ErrorContext...")

    error_ctx = ErrorContext(
        error_message="undefined reference to `login_user`",
        error_type=ErrorType.SYNTAX,
        severity=ErrorSeverity.CRITICAL,
        file_path=Path("src/auth.cpp"),
        line_number=42,
        phase="Phase 10: Test Execution",
        timestamp=datetime.now().isoformat(),
    )

    assert error_ctx.error_message == "undefined reference to `login_user`"
    assert error_ctx.error_type == ErrorType.SYNTAX
    assert error_ctx.severity == ErrorSeverity.CRITICAL
    print("[OK] ErrorContext test passed")


def test_root_cause():
    """测试根因分析结果"""
    print("Testing RootCause...")

    error_ctx = ErrorContext(
        error_message="test error",
        error_type=ErrorType.SYNTAX,
        severity=ErrorSeverity.HIGH,
        timestamp=datetime.now().isoformat(),
    )

    root_cause = RootCause(
        error_context=error_ctx,
        root_cause_type="code_generation_error",
        root_cause_description="代码生成错误",
        confidence=0.85,
        trace_chain=[
            TraceNode("code", "src/auth.cpp", "错误文件", 1.0),
            TraceNode("phase", "Phase 4", "代码生成阶段", 1.0),
        ],
    )

    assert root_cause.root_cause_type == "code_generation_error"
    assert root_cause.confidence == 0.85
    assert len(root_cause.trace_chain) == 2
    print("[OK] RootCause test passed")


def test_healing_strategy():
    """测试修复策略"""
    print("Testing HealingStrategy...")

    error_ctx = ErrorContext(
        error_message="test error",
        error_type=ErrorType.SYNTAX,
        severity=ErrorSeverity.HIGH,
        timestamp=datetime.now().isoformat(),
    )

    root_cause = RootCause(
        error_context=error_ctx,
        root_cause_type="code_generation_error",
        root_cause_description="代码生成错误",
        confidence=0.85,
    )

    strategy = HealingStrategy(
        strategy_type=StrategyType.REGENERATE_CODE,
        description="重新生成代码",
        confidence=0.8,
        estimated_time=60.0,
        root_cause=root_cause,
    )

    assert strategy.strategy_type == StrategyType.REGENERATE_CODE
    assert strategy.confidence == 0.8
    print("[OK] HealingStrategy test passed")


def test_healing_history():
    """测试修复历史"""
    print("Testing HealingHistory...")

    import tempfile

    temp_dir = Path(tempfile.mkdtemp())

    history = HealingHistory(storage_path=temp_dir)

    # 创建测试记录
    error_ctx = ErrorContext(
        error_message="test error",
        error_type=ErrorType.SYNTAX,
        severity=ErrorSeverity.HIGH,
        timestamp=datetime.now().isoformat(),
    )

    root_cause = RootCause(
        error_context=error_ctx,
        root_cause_type="code_generation_error",
        root_cause_description="代码生成错误",
        confidence=0.85,
    )

    strategy = HealingStrategy(
        strategy_type=StrategyType.REGENERATE_CODE,
        description="重新生成代码",
        confidence=0.8,
        estimated_time=60.0,
        root_cause=root_cause,
    )

    record = HealingRecord(
        record_id="test123",
        error_context=error_ctx,
        root_cause=root_cause,
        strategy=strategy,
        success=True,
        execution_time=45.2,
        timestamp=datetime.now(),
    )

    history.add_record(record)

    # 验证记录
    assert len(history.records) == 1
    assert history.records[0].record_id == "test123"

    # 测试统计
    stats = history.get_statistics()
    assert stats["total_records"] == 1
    assert stats["success_rate"] == 1.0

    print("[OK] HealingHistory test passed")

    # 清理
    import shutil

    shutil.rmtree(temp_dir)


def test_root_cause_analyzer():
    """测试根因分析器"""
    print("Testing RootCauseAnalyzer...")

    # 创建模拟的 context 和 artifact_graph
    class MockContext:
        def __init__(self):
            self.requirements = {"REQ-001": {"description": "用户登录功能"}}

    class MockArtifactGraph:
        def get_dependencies(self, file_path):
            return []

    context = MockContext()
    artifact_graph = MockArtifactGraph()

    analyzer = RootCauseAnalyzer(artifact_graph=artifact_graph, context=context)

    # 测试错误分类
    error_ctx = ErrorContext(
        error_message="undefined reference to `login_user`",
        error_type=ErrorType.UNKNOWN,
        severity=ErrorSeverity.CRITICAL,
        file_path=Path("src/auth.cpp"),
        timestamp=datetime.now().isoformat(),
    )

    root_cause = analyzer.analyze(error_ctx)

    assert root_cause.error_context.error_type == ErrorType.SYNTAX
    assert root_cause.root_cause_type == "code_generation_error"
    assert root_cause.confidence > 0.8
    assert len(root_cause.suggested_fixes) > 0

    print("[OK] RootCauseAnalyzer test passed")


def test_strategy_selector():
    """测试策略选择器"""
    print("Testing HealingStrategySelector...")

    import tempfile

    temp_dir = Path(tempfile.mkdtemp())

    history = HealingHistory(storage_path=temp_dir)
    selector = HealingStrategySelector(healing_history=history)

    # 创建根因
    error_ctx = ErrorContext(
        error_message="undefined reference to `login_user`",
        error_type=ErrorType.SYNTAX,
        severity=ErrorSeverity.CRITICAL,
        timestamp=datetime.now().isoformat(),
    )

    root_cause = RootCause(
        error_context=error_ctx,
        root_cause_type="code_generation_error",
        root_cause_description="代码生成错误",
        confidence=0.85,
    )

    # 选择策略
    strategies = selector.select_strategy(root_cause)

    assert len(strategies) > 0
    assert strategies[0].strategy_type == StrategyType.REGENERATE_CODE
    assert strategies[0].confidence > 0

    print("[OK] HealingStrategySelector test passed")

    # 清理
    import shutil

    shutil.rmtree(temp_dir)


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Self-Healing Root Cause Analysis - Unit Tests")
    print("=" * 60)
    print()

    tests = [
        test_error_context,
        test_root_cause,
        test_healing_strategy,
        test_healing_history,
        test_root_cause_analyzer,
        test_strategy_selector,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__} failed: {e}")
            traceback.print_exc()
            failed += 1
        print()

    print("=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
