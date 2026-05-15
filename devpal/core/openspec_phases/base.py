# -*- coding: utf-8 -*-
"""
OpenSpec Phase 基类和数据结构
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class PhaseResult:
    """阶段执行结果"""
    success: bool
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @classmethod
    def ok(cls, message: str = "", **kwargs) -> 'PhaseResult':
        return cls(success=True, message=message, data=kwargs)

    @classmethod
    def fail(cls, message: str, errors: List[str] = None) -> 'PhaseResult':
        return cls(success=False, message=message, errors=errors or [])


@dataclass
class OpenSpecContext:
    """OpenSpec 全局上下文"""
    project_dir: Path
    requirements_file: Path
    requirements_content: str = ""
    structured_requirements: List[Dict[str, Any]] = field(default_factory=list)
    artifact_graph_data: Dict[str, Any] = field(default_factory=dict)

    # 项目配置
    project_name: str = ""
    language: str = "cpp"  # cpp / python
    is_cpp: bool = True

    # 各阶段输出
    phase_results: Dict[int, PhaseResult] = field(default_factory=dict)
    generated_files: List[Path] = field(default_factory=list)

    # 编译相关
    build_dir: Optional[Path] = None
    compiler_path: Optional[str] = None

    # 测试结果
    test_passed: int = 0
    test_failed: int = 0
    test_total: int = 0
    test_output: str = ""
    test_docs: List[str] = field(default_factory=list)  # Phase 5 生成的测试文档路径列表

    # AI 驱动流程 (Phase 3 产出 → Phase 4/10 复用)
    tech_design_content: str = ""
    ai_generated_files: List[Path] = field(default_factory=list)
    self_heal_attempts: int = 0

    # LLM 调用统计 (Phase 11 报告)
    llm_calls: int = 0
    llm_input_tokens: int = 0
    llm_output_tokens: int = 0
    llm_cache_read_tokens: int = 0

    # 日志系统
    logger: Optional[Any] = None  # OpenSpecLogger 实例
    log_file: Optional[Path] = None  # 日志文件路径

    # 失败策略
    abort_on_critical_failure: bool = True  # 关键阶段失败时终止流程

    # 生成策略
    force_regenerate_code: bool = True  # 已存在业务代码时是否强制重新生成

    def get_phase_result(self, phase_num: int) -> Optional[PhaseResult]:
        return self.phase_results.get(phase_num)

    def set_phase_result(self, phase_num: int, result: PhaseResult) -> None:
        self.phase_results[phase_num] = result


def validate_phase_success(phase_num: int, result: PhaseResult) -> List[str]:
    """Return policy violations for phase results that are too weak to count as success."""
    if not result.success:
        return []

    violations: List[str] = []
    if phase_num == 4:
        ai_count = int(result.data.get("ai_count", 0) or 0)
        skipped_ai_generation = bool(result.data.get("skipped_ai_generation", False))
        if ai_count <= 0 and not skipped_ai_generation:
            violations.append(
                "Phase 4 succeeded without generated code or explicit skipped_ai_generation"
            )

    if phase_num == 10:
        test_total = int(result.data.get("test_total", 0) or 0)
        test_failed = int(result.data.get("test_failed", 0) or 0)
        if test_total <= 0:
            violations.append("Phase 10 succeeded with test_total <= 0")
        if test_failed != 0:
            violations.append("Phase 10 succeeded with failing tests")

    return violations


class PhaseInterface(ABC):
    """Phase 接口基类"""

    def __init__(self, context: OpenSpecContext):
        self.context = context
        self.phase_number = 0
        self.phase_name = "Base Phase"
        self.is_critical = False  # 标记是否为关键阶段

    @abstractmethod
    def execute(self) -> PhaseResult:
        """执行当前阶段"""
        pass

    def execute_with_timing(self) -> tuple:
        """执行阶段并记录耗时

        Returns:
            (PhaseResult, duration): 执行结果和耗时（秒）
        """
        import time
        start_time = time.time()

        try:
            result = self.execute()
        except Exception as exc:
            duration = time.time() - start_time
            self.log_error(f"Phase {self.phase_number} 异常: {exc}", exc)
            return PhaseResult.fail(
                f"Phase {self.phase_number} 执行异常",
                errors=[str(exc)]
            ), duration

        duration = time.time() - start_time
        return result, duration

    def log(self, message: str) -> None:
        """输出阶段日志"""
        if hasattr(self.context, 'logger') and self.context.logger:
            self.context.logger.info(f"[Phase {self.phase_number}/11] {message}")
        else:
            print(f"[Phase {self.phase_number}/11] {message}")

    def log_error(self, message: str, exc: Optional[Exception] = None) -> None:
        """输出错误日志"""
        if hasattr(self.context, 'logger') and self.context.logger:
            self.context.logger.error(f"[Phase {self.phase_number}/11] {message}", exc)
        else:
            print(f"[Phase {self.phase_number}/11] ERROR: {message}")
