# -*- coding: utf-8 -*-
"""
OpenSpec Phase 基类和数据结构
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "data": _json_safe(self.data),
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PhaseResult':
        return cls(
            success=bool(data.get("success", False)),
            message=str(data.get("message", "")),
            data=dict(data.get("data", {}) or {}),
            errors=list(data.get("errors", []) or []),
            warnings=list(data.get("warnings", []) or []),
        )


@dataclass
class OpenSpecContext:
    """OpenSpec 全局上下文"""
    project_dir: Path
    requirements_file: Path
    requirements_content: str = ""
    structured_requirements: List[Dict[str, Any]] = field(default_factory=list)
    requirements_delta: Dict[str, Any] = field(default_factory=dict)
    artifact_graph_data: Dict[str, Any] = field(default_factory=dict)
    artifact_graph: Any = field(default=None, repr=False)  # ArtifactGraph instance, not serialized

    # 项目配置
    project_name: str = ""
    language: str = "cpp"  # cpp / python
    is_cpp: bool = True
    project_type: str = ""  # 项目类型：installer, cli_tool, library, application 等
    features: List[str] = field(default_factory=list)  # 项目特性：install, auth, database 等

    # 各阶段输出
    phase_results: Dict[int, PhaseResult] = field(default_factory=dict)
    generated_files: List[Path] = field(default_factory=list)

    # 需求状态生命周期 (P2.3): req_id -> status string
    # PROPOSED -> IN_PROGRESS -> VERIFIED | FAILED
    requirements_status: Dict[str, str] = field(default_factory=dict)

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

    # M2: OpenSpec Change tracking
    current_change_id: Optional[str] = None
    current_change_dir: Optional[Path] = None

    # 失败策略
    abort_on_critical_failure: bool = True  # 关键阶段失败时终止流程

    # 生成策略
    force_regenerate_code: bool = True  # 已存在业务代码时是否强制重新生成

    def get_phase_result(self, phase_num: int) -> Optional[PhaseResult]:
        return self.phase_results.get(phase_num)

    def set_phase_result(self, phase_num: int, result: PhaseResult) -> None:
        self.phase_results[phase_num] = result

    def update_requirement_status(self, req_id: str, status: str) -> None:
        """Update lifecycle status for a requirement. status: PROPOSED|IN_PROGRESS|VERIFIED|FAILED"""
        self.requirements_status[req_id] = status

    def get_requirement_status(self, req_id: str) -> str:
        return self.requirements_status.get(req_id, "PROPOSED")

    def get_status_summary(self) -> Dict[str, int]:
        """Return count of requirements per status."""
        summary: Dict[str, int] = {}
        for status in self.requirements_status.values():
            summary[status] = summary.get(status, 0) + 1
        return summary

    def to_checkpoint_dict(self) -> Dict[str, Any]:
        return {
            "requirements_file": self.requirements_file.as_posix(),
            "project_dir": self.project_dir.as_posix(),
            "requirements_content": self.requirements_content,
            "structured_requirements": _json_safe(self.structured_requirements),
            "requirements_delta": _json_safe(self.requirements_delta),
            "artifact_graph_data": _json_safe(self.artifact_graph_data),
            "project_name": self.project_name,
            "language": self.language,
            "is_cpp": self.is_cpp,
            "project_type": self.project_type,
            "features": list(self.features),
            "phase_results": {
                str(num): result.to_dict()
                for num, result in self.phase_results.items()
            },
            "generated_files": [path.as_posix() for path in self.generated_files],
            "build_dir": self.build_dir.as_posix() if self.build_dir else None,
            "compiler_path": self.compiler_path,
            "test_passed": self.test_passed,
            "test_failed": self.test_failed,
            "test_total": self.test_total,
            "test_output": self.test_output,
            "test_docs": list(self.test_docs),
            "tech_design_content": self.tech_design_content,
            "ai_generated_files": [path.as_posix() for path in self.ai_generated_files],
            "self_heal_attempts": self.self_heal_attempts,
            "llm_calls": self.llm_calls,
            "llm_input_tokens": self.llm_input_tokens,
            "llm_output_tokens": self.llm_output_tokens,
            "llm_cache_read_tokens": self.llm_cache_read_tokens,
            "log_file": self.log_file.as_posix() if self.log_file else None,
            "current_change_id": self.current_change_id,
            "current_change_dir": self.current_change_dir.as_posix() if self.current_change_dir else None,
            "abort_on_critical_failure": self.abort_on_critical_failure,
            "force_regenerate_code": self.force_regenerate_code,
        }

    def restore_from_checkpoint(self, data: Dict[str, Any]) -> None:
        if not data:
            return
        self.requirements_file = Path(data.get("requirements_file", self.requirements_file))
        self.project_dir = Path(data.get("project_dir", self.project_dir))
        self.requirements_content = data.get("requirements_content", self.requirements_content)
        self.structured_requirements = list(data.get("structured_requirements", self.structured_requirements) or [])
        self.requirements_delta = dict(data.get("requirements_delta", self.requirements_delta) or {})
        self.artifact_graph_data = dict(data.get("artifact_graph_data", self.artifact_graph_data) or {})
        self.project_name = data.get("project_name", self.project_name)
        self.language = data.get("language", self.language)
        self.is_cpp = bool(data.get("is_cpp", self.is_cpp))
        self.phase_results = {
            int(num): PhaseResult.from_dict(result)
            for num, result in (data.get("phase_results", {}) or {}).items()
        }
        self.generated_files = [Path(path) for path in data.get("generated_files", []) or []]
        build_dir = data.get("build_dir")
        self.build_dir = Path(build_dir) if build_dir else self.build_dir
        self.compiler_path = data.get("compiler_path", self.compiler_path)
        self.test_passed = int(data.get("test_passed", self.test_passed) or 0)
        self.test_failed = int(data.get("test_failed", self.test_failed) or 0)
        self.test_total = int(data.get("test_total", self.test_total) or 0)
        self.test_output = data.get("test_output", self.test_output)
        self.test_docs = list(data.get("test_docs", self.test_docs) or [])
        self.tech_design_content = data.get("tech_design_content", self.tech_design_content)
        self.ai_generated_files = [Path(path) for path in data.get("ai_generated_files", []) or []]
        self.self_heal_attempts = int(data.get("self_heal_attempts", self.self_heal_attempts) or 0)
        self.llm_calls = int(data.get("llm_calls", self.llm_calls) or 0)
        self.llm_input_tokens = int(data.get("llm_input_tokens", self.llm_input_tokens) or 0)
        self.llm_output_tokens = int(data.get("llm_output_tokens", self.llm_output_tokens) or 0)
        self.llm_cache_read_tokens = int(data.get("llm_cache_read_tokens", self.llm_cache_read_tokens) or 0)
        log_file = data.get("log_file")
        self.log_file = Path(log_file) if log_file else self.log_file
        self.current_change_id = data.get("current_change_id")
        change_dir = data.get("current_change_dir")
        self.current_change_dir = Path(change_dir) if change_dir else None
        self.abort_on_critical_failure = bool(data.get("abort_on_critical_failure", self.abort_on_critical_failure))
        self.force_regenerate_code = bool(data.get("force_regenerate_code", self.force_regenerate_code))


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
        if result.data.get("skipped") or result.data.get("test_skipped"):
            return violations
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
