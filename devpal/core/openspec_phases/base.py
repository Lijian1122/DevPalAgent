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

    def get_phase_result(self, phase_num: int) -> Optional[PhaseResult]:
        return self.phase_results.get(phase_num)

    def set_phase_result(self, phase_num: int, result: PhaseResult) -> None:
        self.phase_results[phase_num] = result


class PhaseInterface(ABC):
    """Phase 接口基类"""

    def __init__(self, context: OpenSpecContext):
        self.context = context
        self.phase_number = 0
        self.phase_name = "Base Phase"

    @abstractmethod
    def execute(self) -> PhaseResult:
        """执行当前阶段"""
        pass

    def log(self, message: str) -> None:
        """输出阶段日志"""
        print(f"[Phase {self.phase_number}/11] {message}")
