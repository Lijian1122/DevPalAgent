# -*- coding: utf-8 -*-
"""
OpenSpec 统一错误处理系统 - Phase 5: 深化与体验

核心功能:
- 结构化错误分类
- 错误严重级别
- 自动恢复策略
- 友好的错误报告
- 错误溯源与聚合
"""

from typing import Any, Dict, List, Optional, Callable, TypeVar
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import traceback
import uuid
from datetime import datetime
from collections import defaultdict


class ErrorSeverity(Enum):
    """错误严重级别"""
    DEBUG = "debug"                # 调试信息
    INFO = "info"                  # 信息性
    WARNING = "warning"            # 警告
    ERROR = "error"                # 错误
    CRITICAL = "critical"          # 严重错误
    FATAL = "fatal"                # 致命错误


class ErrorCategory(Enum):
    """错误类别"""
    VALIDATION = "validation"      # 验证错误
    CONFIG = "config"              # 配置错误
    FILESYSTEM = "filesystem"      # 文件系统错误
    NETWORK = "network"            # 网络错误
    PARSING = "parsing"            # 解析错误
    EXECUTION = "execution"        # 执行错误
    INTEGRATION = "integration"    # 集成错误
    PERMISSION = "permission"      # 权限错误
    TIMEOUT = "timeout"            # 超时错误
    UNKNOWN = "unknown"            # 未知错误


class RecoveryAction(Enum):
    """恢复动作"""
    NONE = "none"                  # 不处理
    RETRY = "retry"                # 重试
    FALLBACK = "fallback"          # 降级方案
    ROLLBACK = "rollback"          # 回滚
    ESCALATE = "escalate"          # 上报
    CLEANUP = "cleanup"            # 清理后重试


@dataclass
class ErrorContext:
    """错误上下文"""
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    tool_name: Optional[str] = None
    user_input: Optional[str] = None
    system_state: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryStrategy:
    """恢复策略"""
    action: RecoveryAction = RecoveryAction.NONE
    max_retries: int = 3
    retry_delay: float = 1.0  # 秒
    retry_backoff: float = 2.0  # 指数退避系数
    fallback_function: Optional[str] = None
    cleanup_function: Optional[str] = None
    escalation_threshold: int = 5
    auto_recover: bool = True


@dataclass
class OpenSpecError:
    """结构化错误"""
    error_id: str
    error_code: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    context: ErrorContext = field(default_factory=ErrorContext)
    stack_trace: Optional[str] = None
    user_friendly_message: str = ""
    suggestion: Optional[str] = None
    recovery_strategy: RecoveryStrategy = field(default_factory=RecoveryStrategy)
    occurred_count: int = 1
    related_errors: List[str] = field(default_factory=list)
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'error_id': self.error_id,
            'error_code': self.error_code,
            'category': self.category.value,
            'severity': self.severity.value,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'context': {
                'file_path': self.context.file_path,
                'line_number': self.context.line_number,
                'function_name': self.context.function_name,
                'tool_name': self.context.tool_name,
                **self.context.metadata,
            },
            'user_friendly_message': self.user_friendly_message or self.message,
            'suggestion': self.suggestion,
            'resolved': self.resolved,
        }


class ErrorManager:
    """错误管理器 - Phase 5 核心组件

    功能:
    - 结构化错误创建
    - 错误聚合与统计
    - 自动恢复执行
    - 友好错误报告
    - 错误模式检测
    """

    def __init__(self):
        self._errors: Dict[str, OpenSpecError] = {}
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._recovery_handlers: Dict[str, Callable] = {}
        self._error_patterns: Dict[str, int] = defaultdict(int)
        self._max_errors = 1000

    def capture_exception(self,
                         exception: Exception,
                         category: ErrorCategory = ErrorCategory.UNKNOWN,
                         severity: ErrorSeverity = ErrorSeverity.ERROR,
                         context: Optional[ErrorContext] = None) -> OpenSpecError:
        """捕获异常并创建结构化错误"""
        error_id = str(uuid.uuid4())[:8]

        # 生成用户友好的消息
        user_msg = self._get_user_friendly_message(exception, category)

        # 生成建议
        suggestion = self._get_suggestion(exception, category)

        # 确定恢复策略
        recovery = self._determine_recovery_strategy(exception, category, severity)

        error = OpenSpecError(
            error_id=error_id,
            error_code=self._get_error_code(exception),
            category=category,
            severity=severity,
            message=str(exception),
            context=context or ErrorContext(),
            stack_trace=traceback.format_exc(),
            user_friendly_message=user_msg,
            suggestion=suggestion,
            recovery_strategy=recovery,
        )

        # 存储错误
        self._store_error(error)

        return error

    def create_error(self,
                    error_code: str,
                    message: str,
                    category: ErrorCategory = ErrorCategory.UNKNOWN,
                    severity: ErrorSeverity = ErrorSeverity.ERROR,
                    context: Optional[ErrorContext] = None,
                    suggestion: Optional[str] = None,
                    user_message: Optional[str] = None) -> OpenSpecError:
        """创建结构化错误（非异常场景）"""
        error_id = str(uuid.uuid4())[:8]

        error = OpenSpecError(
            error_id=error_id,
            error_code=error_code,
            category=category,
            severity=severity,
            message=message,
            context=context or ErrorContext(),
            user_friendly_message=user_message or message,
            suggestion=suggestion,
            recovery_strategy=self._determine_recovery_strategy_from_code(error_code),
        )

        self._store_error(error)
        return error

    def _store_error(self, error: OpenSpecError):
        """存储错误"""
        # 检查是否为重复错误模式
        pattern_key = f"{error.error_code}:{error.category.value}"
        self._error_patterns[pattern_key] += 1

        # 限制存储数量
        if len(self._errors) >= self._max_errors:
            oldest = sorted(self._errors.values(), key=lambda e: e.timestamp)[0]
            del self._errors[oldest.error_id]

        self._errors[error.error_id] = error
        self._error_counts[error.category.value] += 1

    def _get_error_code(self, exception: Exception) -> str:
        """从异常获取错误码"""
        return type(exception).__name__

    def _get_user_friendly_message(self,
                                    exception: Exception,
                                    category: ErrorCategory) -> str:
        """生成用户友好的错误消息"""
        base_messages = {
            ErrorCategory.VALIDATION: "输入验证失败，请检查您的输入",
            ErrorCategory.CONFIG: "配置错误，请检查您的配置文件",
            ErrorCategory.FILESYSTEM: "文件操作失败，请检查文件权限和路径",
            ErrorCategory.NETWORK: "网络连接问题，请检查网络状态",
            ErrorCategory.PARSING: "解析失败，请检查文件格式",
            ErrorCategory.EXECUTION: "执行过程中出现错误",
            ErrorCategory.PERMISSION: "权限不足，请检查访问权限",
            ErrorCategory.TIMEOUT: "操作超时，请稍后重试",
        }

        base = base_messages.get(category, "操作过程中出现错误")
        exc_msg = str(exception)

        if exc_msg and len(exc_msg) < 100:
            return f"{base}: {exc_msg}"
        return base

    def _get_suggestion(self, exception: Exception, category: ErrorCategory) -> str:
        """生成修复建议"""
        suggestions = {
            ErrorCategory.VALIDATION: [
                "请检查输入的格式是否正确",
                "参考文档确认允许的取值范围",
                "如问题持续，请联系技术支持",
            ],
            ErrorCategory.CONFIG: [
                "检查配置文件语法是否正确",
                "确认所有必需的配置项都已设置",
                "可以使用默认配置作为参考",
            ],
            ErrorCategory.FILESYSTEM: [
                "确认文件或目录存在",
                "检查当前用户是否有读写权限",
                "确认磁盘空间是否充足",
            ],
            ErrorCategory.NETWORK: [
                "检查网络连接是否正常",
                "确认目标服务是否可访问",
                "检查防火墙和代理设置",
            ],
        }

        category_suggestions = suggestions.get(category, [])
        if category_suggestions:
            return "\n".join(f"- {s}" for s in category_suggestions)
        return ""

    def _determine_recovery_strategy(self,
                                     exception: Exception,
                                     category: ErrorCategory,
                                     severity: ErrorSeverity) -> RecoveryStrategy:
        """确定恢复策略"""
        # 默认策略
        strategy = RecoveryStrategy()

        # 网络和超时错误通常可以重试
        if category in [ErrorCategory.NETWORK, ErrorCategory.TIMEOUT]:
            strategy.action = RecoveryAction.RETRY
            strategy.max_retries = 5
            strategy.retry_delay = 2.0
            strategy.retry_backoff = 1.5

        # 文件系统错误可以尝试清理后重试
        elif category == ErrorCategory.FILESYSTEM:
            strategy.action = RecoveryAction.CLEANUP
            strategy.max_retries = 2

        # 配置和验证错误需要上报
        elif category in [ErrorCategory.CONFIG, ErrorCategory.VALIDATION]:
            strategy.action = RecoveryAction.ESCALATE
            strategy.auto_recover = False

        # 严重错误不自动恢复
        if severity in [ErrorSeverity.CRITICAL, ErrorSeverity.FATAL]:
            strategy.auto_recover = False
            strategy.action = RecoveryAction.ESCALATE

        return strategy

    def _determine_recovery_strategy_from_code(self, error_code: str) -> RecoveryStrategy:
        """根据错误码确定恢复策略"""
        # 简单实现，可以扩展为基于规则
        return RecoveryStrategy()

    def get_error(self, error_id: str) -> Optional[OpenSpecError]:
        """获取指定错误"""
        return self._errors.get(error_id)

    def get_errors_by_category(self, category: ErrorCategory) -> List[OpenSpecError]:
        """按类别获取错误"""
        return [e for e in self._errors.values() if e.category == category]

    def get_errors_by_severity(self, severity: ErrorSeverity) -> List[OpenSpecError]:
        """按严重级别获取错误"""
        return [e for e in self._errors.values() if e.severity == severity]

    def mark_resolved(self, error_id: str):
        """标记错误已解决"""
        error = self._errors.get(error_id)
        if error:
            error.resolved = True

    def execute_recovery(self, error_id: str,
                        callback: Optional[Callable] = None) -> bool:
        """执行恢复策略"""
        error = self.get_error(error_id)
        if not error:
            return False

        strategy = error.recovery_strategy
        if not strategy.auto_recover:
            return False

        # 执行恢复动作
        try:
            if strategy.action == RecoveryAction.RETRY and callback:
                for attempt in range(strategy.max_retries):
                    try:
                        callback()
                        return True
                    except Exception:
                        if attempt < strategy.max_retries - 1:
                            import time
                            delay = strategy.retry_delay * (strategy.retry_backoff ** attempt)
                            time.sleep(delay)

            elif strategy.action == RecoveryAction.CLEANUP and callback:
                # 先执行清理
                callback()

            self.mark_resolved(error_id)
            return True

        except Exception:
            return False

        return False

    def generate_error_report(self,
                             include_resolved: bool = False,
                             limit: int = 50) -> str:
        """生成错误报告"""
        errors = [
            e for e in self._errors.values()
            if include_resolved or not e.resolved
        ]
        errors = sorted(errors, key=lambda e: e.timestamp, reverse=True)[:limit]

        lines = []
        lines.append("=" * 70)
        lines.append("OpenSpec 错误报告")
        lines.append("=" * 70)
        lines.append(f"总错误数: {len(self._errors)}")
        lines.append(f"未解决: {sum(1 for e in self._errors.values() if not e.resolved)}")
        lines.append("")

        # 按类别统计
        lines.append("错误分布 (按类别):")
        for category, count in self._error_counts.items():
            lines.append(f"  {category:15s}: {count}")
        lines.append("")

        # 错误模式
        if self._error_patterns:
            lines.append("常见错误模式:")
            for pattern, count in sorted(self._error_patterns.items(),
                                        key=lambda x: x[1], reverse=True)[:5]:
                if count > 1:
                    lines.append(f"  {pattern:30s}: {count} 次")
            lines.append("")

        # 最新错误
        if errors:
            lines.append("最新错误:")
            for error in errors[:10]:
                status = "✓" if error.resolved else "✗"
                lines.append(f"  [{status}] {error.error_id}: {error.message}")
                lines.append(f"      类别: {error.category.value} | "
                            f"级别: {error.severity.value}")
                if error.suggestion:
                    lines.append(f"      建议: {error.suggestion}")
                lines.append("")

        lines.append("=" * 70)
        return "\n".join(lines)

    def get_summary(self) -> Dict[str, Any]:
        """获取错误摘要"""
        return {
            'total_errors': len(self._errors),
            'unresolved': sum(1 for e in self._errors.values() if not e.resolved),
            'by_category': dict(self._error_counts),
            'by_severity': {
                sev.value: len(self.get_errors_by_severity(sev))
                for sev in ErrorSeverity
            },
            'top_patterns': sorted(
                [(p, c) for p, c in self._error_patterns.items() if c > 1],
                key=lambda x: x[1],
                reverse=True
            )[:5],
        }

    def clear(self, resolved_only: bool = False):
        """清除错误"""
        if resolved_only:
            self._errors = {
                k: v for k, v in self._errors.items() if not v.resolved
            }
        else:
            self._errors.clear()
            self._error_counts.clear()
            self._error_patterns.clear()
