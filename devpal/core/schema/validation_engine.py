from typing import Any, Dict, List, Optional, Callable, Union, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import re
import hashlib
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


class ValidationLevel(Enum):
    FORMAT = "format"      # 格式验证: 语法、类型
    SEMANTIC = "semantic"  # 语义验证: 逻辑自洽
    PARSER = "parser"      # 解析器验证: 与现有代码兼容
    BUSINESS = "business"  # 业务规则验证: 符合项目规范


class ValidationSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    level: ValidationLevel
    severity: ValidationSeverity
    message: str
    location: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    passed: bool
    issues: List[ValidationIssue]
    context: Dict[str, Any]
    duration: float = 0.0
    executed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "issues": [
                {
                    "level": i.level.value,
                    "severity": i.severity.value,
                    "message": i.message,
                    "location": i.location,
                    "suggestion": i.suggestion
                }
                for i in self.issues
            ],
            "context": self.context,
            "duration": self.duration,
            "executed_at": self.executed_at.isoformat()
        }

    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.ERROR)

    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.WARNING)


class PipelineStatus(Enum):
    """流水线状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"  # 部分阶段成功


@dataclass
class PipelineStage:
    """流水线阶段定义"""
    level: ValidationLevel
    name: str
    enabled: bool = True
    stop_on_failure: bool = True
    validators: List[str] = field(default_factory=list)  # 指定使用哪些验证器，空表示全部
    timeout: int = 30  # 秒

    def __post_init__(self):
        if not self.name:
            self.name = self.level.value


@dataclass
class PipelineStageResult:
    """流水线阶段执行结果"""
    stage: PipelineStage
    status: PipelineStatus
    issues: List[ValidationIssue] = field(default_factory=list)
    duration: float = 0.0
    error_message: Optional[str] = None

    @property
    def passed(self) -> bool:
        return all(i.severity != ValidationSeverity.ERROR for i in self.issues)


@dataclass
class ValidationPipelineResult:
    """完整流水线执行结果"""
    status: PipelineStatus
    stages: List[PipelineStageResult]
    total_duration: float
    context: Dict[str, Any]
    content_hash: str = ""
    executed_at: datetime = field(default_factory=datetime.now)

    @property
    def passed(self) -> bool:
        return self.status == PipelineStatus.SUCCESS

    @property
    def all_issues(self) -> List[ValidationIssue]:
        return [issue for stage in self.stages for issue in stage.issues]

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.all_issues if i.severity == ValidationSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.all_issues if i.severity == ValidationSeverity.WARNING)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "stages": [
                {
                    "level": s.stage.level.value,
                    "name": s.stage.name,
                    "status": s.status.value,
                    "duration": s.duration,
                    "issue_count": len(s.issues),
                    "error": s.error_message
                }
                for s in self.stages
            ],
            "total_duration": self.total_duration,
            "issue_count": len(self.all_issues),
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "executed_at": self.executed_at.isoformat(),
            "content_hash": self.content_hash
        }

    def summary(self) -> str:
        """生成摘要报告"""
        lines = [
            "=" * 60,
            f"验证流水线结果: {self.status.value.upper()}",
            "-" * 60,
        ]
        for stage in self.stages:
            icon = "✅" if stage.status == PipelineStatus.SUCCESS else "❌" if stage.status == PipelineStatus.FAILED else "⚠️"
            lines.append(f"{icon} {stage.stage.name}: {len(stage.issues)} 个问题 ({stage.duration:.2f}s)")
        lines.extend([
            "-" * 60,
            f"总计: {len(self.all_issues)} 个问题, {self.error_count} 个错误, {self.warning_count} 个警告",
            f"总耗时: {self.total_duration:.2f}s",
            "=" * 60,
        ])
        return "\n".join(lines)


class ValidationPipeline:
    """验证流水线 - 编排和执行完整的验证流程

    功能:
    1. 可配置的阶段执行
    2. 并行/串行执行模式
    3. 结果聚合与报告
    4. 历史记录管理
    """

    def __init__(self, engine: 'ValidationEngine'):
        self.engine = engine
        self.stages: List[PipelineStage] = []
        self._history: List[ValidationPipelineResult] = []
        self.parallel_execution = False  # 默认串行执行

    def add_stage(self, stage: PipelineStage):
        """添加验证阶段"""
        self.stages.append(stage)

    def set_stages(self, stages: List[PipelineStage]):
        """批量设置阶段"""
        self.stages = stages

    def setup_default_pipeline(self):
        """设置默认的四层验证流水线"""
        self.stages = [
            PipelineStage(level=ValidationLevel.FORMAT, name="格式验证", stop_on_failure=True),
            PipelineStage(level=ValidationLevel.SEMANTIC, name="语义验证", stop_on_failure=True),
            PipelineStage(level=ValidationLevel.PARSER, name="兼容性验证", stop_on_failure=False),
            PipelineStage(level=ValidationLevel.BUSINESS, name="业务规则验证", stop_on_failure=False),
        ]

    def run(self, content: Any, context: Dict[str, Any] = None) -> ValidationPipelineResult:
        """执行完整验证流水线

        Args:
            content: 要验证的内容
            context: 上下文参数

        Returns:
            流水线执行结果
        """
        import time
        start_time = time.time()
        context = context or {}
        stage_results = []

        # 计算内容哈希用于追踪
        content_str = str(content) if not isinstance(content, (dict, list)) else json.dumps(content)
        content_hash = hashlib.md5(content_str.encode()).hexdigest()[:16]

        if self.parallel_execution:
            stage_results = self._run_parallel(content, context)
        else:
            stage_results = self._run_sequential(content, context)

        total_duration = time.time() - start_time

        # 计算最终状态
        has_errors = any(
            sr.status == PipelineStatus.FAILED or
            any(i.severity == ValidationSeverity.ERROR for i in sr.issues)
            for sr in stage_results
        )
        has_partial = any(sr.status == PipelineStatus.PARTIAL for sr in stage_results)

        if has_errors:
            final_status = PipelineStatus.FAILED
        elif has_partial:
            final_status = PipelineStatus.PARTIAL
        elif all(sr.status == PipelineStatus.SUCCESS for sr in stage_results):
            final_status = PipelineStatus.SUCCESS
        else:
            final_status = PipelineStatus.PARTIAL

        result = ValidationPipelineResult(
            status=final_status,
            stages=stage_results,
            total_duration=total_duration,
            context=context,
            content_hash=content_hash
        )

        # 保存历史记录（最多保留 100 条）
        self._history.append(result)
        if len(self._history) > 100:
            self._history = self._history[-100:]

        return result

    def _run_sequential(self, content: Any, context: Dict[str, Any]) -> List[PipelineStageResult]:
        """串行执行所有阶段"""
        import time
        results = []

        for stage in self.stages:
            if not stage.enabled:
                continue

            stage_start = time.time()
            stage_issues = []
            status = PipelineStatus.SUCCESS

            try:
                # 确定要运行的验证器
                validators = self.engine.get_validators_for_level(stage.level)
                if stage.validators:
                    # 只运行指定的验证器
                    validator_names = set(stage.validators)
                    validators = [
                        v for v in validators
                        if getattr(v, '__name__', str(v)) in validator_names
                    ]

                for validator in validators:
                    try:
                        issues = validator(content, context)
                        if issues:
                            stage_issues.extend(issues)
                    except Exception as e:
                        stage_issues.append(ValidationIssue(
                            stage.level,
                            ValidationSeverity.WARNING,
                            f"验证器执行异常: {getattr(validator, '__name__', str(validator))}: {e}"
                        ))

                # 检查是否有错误
                if any(i.severity == ValidationSeverity.ERROR for i in stage_issues):
                    status = PipelineStatus.FAILED

            except Exception as e:
                status = PipelineStatus.FAILED
                stage_issues.append(ValidationIssue(
                    stage.level,
                    ValidationSeverity.ERROR,
                    f"阶段执行失败: {e}"
                ))

            stage_duration = time.time() - stage_start
            results.append(PipelineStageResult(
                stage=stage,
                status=status,
                issues=stage_issues,
                duration=stage_duration
            ))

            # 如果该阶段失败且配置了停止，则终止后续阶段
            if status == PipelineStatus.FAILED and stage.stop_on_failure:
                # 剩余阶段标记为跳过
                for remaining_stage in self.stages[len(results):]:
                    if remaining_stage.enabled:
                        results.append(PipelineStageResult(
                            stage=remaining_stage,
                            status=PipelineStatus.PENDING,
                            issues=[],
                            duration=0.0,
                            error_message="因前序阶段失败而跳过"
                        ))
                break

        return results

    def _run_parallel(self, content: Any, context: Dict[str, Any]) -> List[PipelineStageResult]:
        """并行执行所有阶段（忽略依赖关系）"""
        import time
        results = []

        enabled_stages = [s for s in self.stages if s.enabled]

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            for stage in enabled_stages:
                future = executor.submit(self._run_single_stage, stage, content, context)
                futures[future] = stage

            for future in as_completed(futures):
                stage = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append(PipelineStageResult(
                        stage=stage,
                        status=PipelineStatus.FAILED,
                        issues=[ValidationIssue(stage.level, ValidationSeverity.ERROR, f"执行异常: {e}")],
                        duration=0.0
                    ))

        # 按原始顺序排列结果
        stage_order = {s.name: i for i, s in enumerate(self.stages)}
        results.sort(key=lambda r: stage_order.get(r.stage.name, 999))
        return results

    def _run_single_stage(self, stage: PipelineStage, content: Any,
                          context: Dict[str, Any]) -> PipelineStageResult:
        """执行单个阶段"""
        import time
        start = time.time()
        issues = []

        try:
            validators = self.engine.get_validators_for_level(stage.level)
            for validator in validators:
                try:
                    result = validator(content, context)
                    if result:
                        issues.extend(result)
                except Exception as e:
                    issues.append(ValidationIssue(
                        stage.level,
                        ValidationSeverity.WARNING,
                        f"验证器 {getattr(validator, '__name__', str(validator))} 异常: {e}"
                    ))

            status = PipelineStatus.SUCCESS if not issues else PipelineStatus.SUCCESS
            if any(i.severity == ValidationSeverity.ERROR for i in issues):
                status = PipelineStatus.FAILED

        except Exception as e:
            status = PipelineStatus.FAILED
            issues.append(ValidationIssue(
                stage.level, ValidationSeverity.ERROR, f"阶段执行异常: {e}"
            ))

        return PipelineStageResult(
            stage=stage,
            status=status,
            issues=issues,
            duration=time.time() - start
        )

    def get_history(self, limit: int = 20) -> List[ValidationPipelineResult]:
        """获取验证历史"""
        return self._history[-limit:]

    def compare_runs(self, index1: int, index2: int) -> Dict[str, Any]:
        """比较两次验证结果"""
        if index1 >= len(self._history) or index2 >= len(self._history):
            return {"error": "Invalid index"}

        r1 = self._history[index1]
        r2 = self._history[index2]

        return {
            "status_change": f"{r1.status.value} -> {r2.status.value}",
            "issues_diff": len(r2.all_issues) - len(r1.all_issues),
            "errors_diff": r2.error_count - r1.error_count,
            "warnings_diff": r2.warning_count - r1.warning_count,
            "duration_change": f"{r1.total_duration:.2f}s -> {r2.total_duration:.2f}s",
            "content_changed": r1.content_hash != r2.content_hash
        }


class ValidationEngine:
    """四层验证引擎 - OpenSpec 核心架构

    执行顺序: FORMAT → SEMANTIC → PARSER → BUSINESS
    任何一层失败默认阻止继续执行
    """

    def __init__(self):
        self._validators: Dict[ValidationLevel, List[Callable]] = {
            ValidationLevel.FORMAT: [],
            ValidationLevel.SEMANTIC: [],
            ValidationLevel.PARSER: [],
            ValidationLevel.BUSINESS: [],
        }
        self._register_default_validators()
        self._pipeline = ValidationPipeline(self)
        self._pipeline.setup_default_pipeline()

    def _register_default_validators(self):
        """注册默认验证器"""
        # FORMAT level validators
        self.register_validator(ValidationLevel.FORMAT, self._validate_file_encoding)
        self.register_validator(ValidationLevel.FORMAT, self._validate_syntax)

        # SEMANTIC level validators
        self.register_validator(ValidationLevel.SEMANTIC, self._validate_logical_consistency)
        self.register_validator(ValidationLevel.SEMANTIC, self._validate_no_hallucination)

        # PARSER level validators
        self.register_validator(ValidationLevel.PARSER, self._validate_existing_code_compat)

        # BUSINESS level validators
        self.register_validator(ValidationLevel.BUSINESS, self._validate_project_rules)

    def register_validator(self, level: ValidationLevel, validator: Callable):
        """注册自定义验证器"""
        self._validators[level].append(validator)

    def get_validators_for_level(self, level: ValidationLevel) -> List[Callable]:
        """获取指定层级的所有验证器"""
        return self._validators.get(level, [])

    def _run_validators(self, level: ValidationLevel, content: Any, context: Dict[str, Any]) -> List[ValidationIssue]:
        """运行指定层级的所有验证器"""
        all_issues = []
        for validator in self._validators[level]:
            try:
                issues = validator(content, context)
                if issues:
                    all_issues.extend(issues)
            except Exception as e:
                all_issues.append(ValidationIssue(
                    level,
                    ValidationSeverity.WARNING,
                    f"验证器 {validator.__name__} 执行异常: {e}"
                ))
        return all_issues

    def validate(self, content: Any, context: Dict[str, Any] = None,
                 stop_on_error: bool = True) -> ValidationResult:
        """执行完整四层验证（简单模式）"""
        import time
        start = time.time()

        all_issues = []
        context = context or {}

        for level in [ValidationLevel.FORMAT, ValidationLevel.SEMANTIC,
                      ValidationLevel.PARSER, ValidationLevel.BUSINESS]:
            level_issues = self._run_validators(level, content, context)
            all_issues.extend(level_issues)

            if stop_on_error and any(i.severity == ValidationSeverity.ERROR
                                   for i in level_issues):
                break

        passed = all(i.severity != ValidationSeverity.ERROR for i in all_issues)
        duration = time.time() - start
        return ValidationResult(passed=passed, issues=all_issues, context=context, duration=duration)

    def validate_pipeline(self, content: Any, context: Dict[str, Any] = None,
                          use_pipeline: Optional[ValidationPipeline] = None) -> ValidationPipelineResult:
        """使用验证流水线执行验证（高级模式）"""
        pipeline = use_pipeline or self._pipeline
        return pipeline.run(content, context)

    @property
    def pipeline(self) -> ValidationPipeline:
        """获取默认流水线实例"""
        return self._pipeline

    def create_custom_pipeline(self, stages: List[PipelineStage]) -> ValidationPipeline:
        """创建自定义验证流水线"""
        pipeline = ValidationPipeline(self)
        pipeline.set_stages(stages)
        return pipeline

    def _validate_file_encoding(self, content, context) -> List[ValidationIssue]:
        """验证文件编码和格式"""
        issues = []
        if isinstance(content, str):
            if '\0' in content:
                issues.append(ValidationIssue(
                    ValidationLevel.FORMAT, ValidationSeverity.ERROR,
                    "文件包含空字符，可能是编码错误"
                ))
        return issues

    def _validate_syntax(self, content, context) -> List[ValidationIssue]:
        """验证语法正确性"""
        issues = []
        file_path = context.get('file_path', '')
        if not isinstance(content, str):
            return issues

        if file_path.endswith('.py'):
            try:
                compile(content, file_path, 'exec')
            except SyntaxError as e:
                issues.append(ValidationIssue(
                    ValidationLevel.FORMAT, ValidationSeverity.ERROR,
                    f"Python 语法错误: {e.msg}",
                    location=f"line {e.lineno}"
                ))
        elif file_path.endswith(('.cpp', '.h', '.cc', '.cxx')):
            # C++ 语法快速检查: 括号匹配
            brackets = {'(': ')', '{': '}', '[': ']'}
            stack = []
            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                for char_num, char in enumerate(line, 1):
                    if char in brackets:
                        stack.append((char, line_num, char_num))
                    elif char in brackets.values():
                        if not stack:
                            issues.append(ValidationIssue(
                                ValidationLevel.FORMAT, ValidationSeverity.WARNING,
                                f"C++ 括号不匹配: 多余的 {char}",
                                location=f"line {line_num}, char {char_num}"
                            ))
                        else:
                            opening, _, _ = stack.pop()
                            if brackets[opening] != char:
                                issues.append(ValidationIssue(
                                    ValidationLevel.FORMAT, ValidationSeverity.WARNING,
                                    f"C++ 括号不匹配: {opening} 与 {char} 不配对",
                                    location=f"line {line_num}"
                                ))
            if stack:
                opening, line_num, _ = stack[0]
                issues.append(ValidationIssue(
                    ValidationLevel.FORMAT, ValidationSeverity.WARNING,
                    f"C++ 括号不匹配: {opening} 未闭合",
                    location=f"line {line_num}"
                ))
        return issues

    def _validate_logical_consistency(self, content, context) -> List[ValidationIssue]:
        """验证逻辑自洽性"""
        issues = []
        if not isinstance(content, str):
            return issues

        # 检查常见的反模式
        anti_patterns = [
            (r"if\s*\(\s*True\s*\)|if\s*\(\s*1\s*\)", "不必要的 if True 判断"),
            (r"while\s*\(\s*True\s*\)|while\s*\(\s*1\s*\)", "无限循环，确保有退出条件"),
            (r"return\s*[Nn]one|return\s*$", "函数返回 None，确保这是预期行为"),
        ]

        for pattern, message in anti_patterns:
            if re.search(pattern, content):
                issues.append(ValidationIssue(
                    ValidationLevel.SEMANTIC, ValidationSeverity.INFO,
                    message
                ))

        return issues

    def _validate_no_hallucination(self, content, context) -> List[ValidationIssue]:
        """验证无幻觉 - 调用现有 HallucinationDetectorTool"""
        issues = []
        if not isinstance(content, str):
            return issues

        try:
            from devpal.tools.hallucination_detector import HallucinationDetectorTool
            detector = HallucinationDetectorTool()
            result = detector.execute_with_validation({
                'check_type': context.get('check_type', 'code'),
                'content_to_check': content,
                'context': context.get('context', '')
            })

            # Check metadata issues from hallucination detector
            if result.metadata:
                detected_issues = result.metadata.get('issues', [])
                for issue in detected_issues:
                    severity_map = {
                        'high': ValidationSeverity.ERROR,
                        'medium': ValidationSeverity.WARNING,
                        'low': ValidationSeverity.INFO
                    }
                    severity = severity_map.get(issue.get('severity', 'medium'), ValidationSeverity.WARNING)
                    issues.append(ValidationIssue(
                        ValidationLevel.SEMANTIC, severity,
                        issue.get('message', ''),
                        suggestion=issue.get('suggestion')
                    ))
        except ImportError:
            # HallucinationDetectorTool not available - skip
            pass
        except Exception as e:
            issues.append(ValidationIssue(
                ValidationLevel.SEMANTIC, ValidationSeverity.WARNING,
                f"幻觉检测工具执行异常: {e}"
            ))

        return issues

    def _validate_existing_code_compat(self, content, context) -> List[ValidationIssue]:
        """验证与现有代码兼容性"""
        issues = []
        if not isinstance(content, str):
            return issues

        file_path = context.get('file_path', '')
        if not file_path or not Path(file_path).exists():
            return issues

        # 检查修改是否会破坏现有函数签名
        try:
            original_content = Path(file_path).read_text(encoding='utf-8')

            # 提取原有的函数签名
            original_funcs = set(re.findall(r'def\s+(\w+)\s*\(', original_content))
            new_funcs = set(re.findall(r'def\s+(\w+)\s*\(', content))

            # 检查是否有函数被删除
            removed_funcs = original_funcs - new_funcs
            for func_name in removed_funcs:
                issues.append(ValidationIssue(
                    ValidationLevel.PARSER, ValidationSeverity.WARNING,
                    f"函数 {func_name} 被删除，可能破坏现有调用",
                    suggestion="请确保没有其他代码调用此函数，或更新所有调用点"
                ))

            # 检查类名变更
            original_classes = set(re.findall(r'class\s+(\w+)\s*[:\(]', original_content))
            new_classes = set(re.findall(r'class\s+(\w+)\s*[:\(]', content))
            removed_classes = original_classes - new_classes
            for class_name in removed_classes:
                issues.append(ValidationIssue(
                    ValidationLevel.PARSER, ValidationSeverity.ERROR,
                    f"类 {class_name} 被删除，可能破坏现有代码",
                    suggestion="请确保类的删除是故意的，并更新所有引用点"
                ))
        except Exception as e:
            issues.append(ValidationIssue(
                ValidationLevel.PARSER, ValidationSeverity.WARNING,
                f"兼容性检查异常: {e}"
            ))

        return issues

    def _validate_project_rules(self, content, context) -> List[ValidationIssue]:
        """验证项目业务规则"""
        issues = []
        if not isinstance(content, str):
            return issues

        project_rules = context.get('project_rules', [])
        if not project_rules:
            # 默认规则
            project_rules = [
                # TODO: 可配置的项目规则
            ]

        for rule in project_rules:
            pattern = rule.get('pattern')
            if pattern:
                try:
                    matches = re.findall(pattern, content)
                    if matches:
                        issues.append(ValidationIssue(
                            ValidationLevel.BUSINESS,
                            ValidationSeverity(rule.get('severity', 'warning')),
                            rule.get('message', f"违反规则: {pattern}"),
                            suggestion=rule.get('suggestion')
                        ))
                except re.error:
                    pass

        return issues
