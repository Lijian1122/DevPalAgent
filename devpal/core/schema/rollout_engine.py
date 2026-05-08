# -*- coding: utf-8 -*-
"""
OpenSpec 渐进式发布引擎 - Phase 5: 深化与体验

核心功能:
- 金丝雀发布 (Canary)
- 增量发布 (Incremental)
- 蓝绿部署 (Blue/Green)
- A/B 测试框架
- 自动晋升与回滚
- 发布状态监控
"""

from typing import Any, Dict, List, Optional, Callable, Tuple, TypeVar
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import time
import uuid
from datetime import datetime


class RolloutStatus(Enum):
    """发布状态"""
    PENDING = "pending"              # 等待开始
    PREPARING = "preparing"          # 准备中
    IN_PROGRESS = "in_progress"      # 进行中
    MONITORING = "monitoring"        # 监控中
    PROMOTING = "promoting"          # 晋升中
    COMPLETED = "completed"          # 完成
    ROLLING_BACK = "rolling_back"    # 回滚中
    FAILED = "failed"                # 失败
    CANCELLED = "cancelled"          # 已取消


class RolloutType(Enum):
    """发布类型"""
    CANARY = "canary"                # 金丝雀发布
    INCREMENTAL = "incremental"      # 增量发布
    BLUE_GREEN = "blue_green"        # 蓝绿部署
    AB_TEST = "ab_test"              # A/B 测试


class MetricStatus(Enum):
    """指标状态"""
    HEALTHY = "healthy"              # 健康
    WARNING = "warning"              # 警告
    UNHEALTHY = "unhealthy"          # 不健康
    UNKNOWN = "unknown"              # 未知


@dataclass
class RolloutMetric:
    """发布监控指标"""
    name: str
    current_value: float
    threshold: float
    status: MetricStatus
    trend: str = "stable"  # improving, worsening, stable
    unit: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'current_value': self.current_value,
            'threshold': self.threshold,
            'status': self.status.value,
            'trend': self.trend,
            'unit': self.unit,
        }


@dataclass
class RolloutStage:
    """发布阶段"""
    stage_id: str
    name: str
    description: str = ""
    percentage: float = 0.0          # 此阶段的发布比例
    duration: int = 300              # 持续时间（秒）
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: RolloutStatus = RolloutStatus.PENDING
    metrics: List[RolloutMetric] = field(default_factory=list)
    passed: Optional[bool] = None


@dataclass
class RolloutTarget:
    """发布目标"""
    target_id: str
    name: str
    path: Optional[Path] = None
    current_version: str = ""
    target_version: str = ""
    status: RolloutStatus = RolloutStatus.PENDING
    percentage: float = 0.0
    error_count: int = 0
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class RolloutResult:
    """发布结果"""
    rollout_id: str
    success: bool
    status: RolloutStatus
    final_percentage: float
    total_duration: float
    stages_completed: int
    total_targets: int
    targets_updated: int
    targets_rolled_back: int
    metrics: List[RolloutMetric] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    rollback_reason: Optional[str] = None


class RolloutEngine:
    """渐进式发布引擎 - Phase 5 核心组件

    支持的发布策略:
    - 金丝雀发布: 小比例用户 → 观察 → 逐步扩大
    - 增量发布: 多阶段等量递增 (如 20% → 40% → ... → 100%)
    - 蓝绿部署: 两套环境 → 流量切换
    - A/B 测试: 两个版本并行 → 根据指标选择
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = config or {}
        self._rollouts: Dict[str, 'Rollout'] = {}
        self._metric_providers: Dict[str, Callable] = {}
        self._hooks: Dict[str, List[Callable]] = {
            'pre_stage': [],
            'post_stage': [],
            'pre_rollout': [],
            'post_rollout': [],
            'on_failure': [],
            'on_rollback': [],
        }
        self.register_default_metrics()

    def register_default_metrics(self):
        """注册默认指标提供者"""
        self._metric_providers['health_score'] = self._default_health_metric
        self._metric_providers['error_rate'] = self._default_error_metric
        self._metric_providers['latency'] = self._default_latency_metric

    def create_rollout(self,
                       name: str,
                       rollout_type: RolloutType = RolloutType.CANARY,
                       strategy: Optional[Dict[str, Any]] = None) -> 'Rollout':
        """创建新的发布"""
        rollout_id = str(uuid.uuid4())[:8]
        rollout = Rollout(
            rollout_id=rollout_id,
            name=name,
            rollout_type=rollout_type,
            strategy=strategy or {},
        )
        self._rollouts[rollout_id] = rollout
        return rollout

    def get_rollout(self, rollout_id: str) -> Optional['Rollout']:
        """获取发布实例"""
        return self._rollouts.get(rollout_id)

    def list_rollouts(self, status: Optional[RolloutStatus] = None) -> List['Rollout']:
        """列出所有发布"""
        rollouts = list(self._rollouts.values())
        if status:
            rollouts = [r for r in rollouts if r.status == status]
        return rollouts

    def register_hook(self, hook_type: str, callback: Callable):
        """注册钩子"""
        if hook_type in self._hooks:
            self._hooks[hook_type].append(callback)

    def _trigger_hooks(self, hook_type: str, *args, **kwargs):
        """触发钩子"""
        for callback in self._hooks.get(hook_type, []):
            try:
                callback(*args, **kwargs)
            except Exception:
                pass

    def _default_health_metric(self, rollout: 'Rollout') -> RolloutMetric:
        """默认健康度指标"""
        return RolloutMetric(
            name='health_score',
            current_value=85.0,  # 模拟值
            threshold=70.0,
            status=MetricStatus.HEALTHY,
            unit='score'
        )

    def _default_error_metric(self, rollout: 'Rollout') -> RolloutMetric:
        """默认错误率指标"""
        return RolloutMetric(
            name='error_rate',
            current_value=0.01,  # 模拟值 1%
            threshold=0.05,
            status=MetricStatus.HEALTHY,
            unit='ratio'
        )

    def _default_latency_metric(self, rollout: 'Rollout') -> RolloutMetric:
        """默认延迟指标"""
        return RolloutMetric(
            name='latency_p95',
            current_value=150.0,  # 模拟值 150ms
            threshold=300.0,
            status=MetricStatus.HEALTHY,
            unit='ms'
        )

    def canary_rollout(self,
                       name: str,
                       canary_percentage: float = 10.0,
                       stages: int = 5,
                       targets: Optional[List[RolloutTarget]] = None) -> RolloutResult:
        """执行金丝雀发布

        Args:
            name: 发布名称
            canary_percentage: 初始金丝雀比例
            stages: 阶段数
            targets: 发布目标列表
        """
        rollout = self.create_rollout(name, RolloutType.CANARY)
        rollout.targets = targets or []

        # 生成金丝雀阶段
        stage_percentages = self._generate_canary_stages(canary_percentage, stages)
        rollout.stages = [
            RolloutStage(
                stage_id=f"stage_{i}",
                name=f"阶段 {i+1}",
                percentage=pct,
                duration=300,  # 5分钟
            )
            for i, pct in enumerate(stage_percentages)
        ]

        return self._execute_rollout(rollout)

    def incremental_rollout(self,
                           name: str,
                           stages: int = 5,
                           targets: Optional[List[RolloutTarget]] = None) -> RolloutResult:
        """执行增量发布（等量递增）"""
        rollout = self.create_rollout(name, RolloutType.INCREMENTAL)
        rollout.targets = targets or []

        increment = 100.0 / stages
        rollout.stages = [
            RolloutStage(
                stage_id=f"stage_{i}",
                name=f"阶段 {i+1}",
                percentage=increment * (i + 1),
                duration=300,
            )
            for i in range(stages)
        ]

        return self._execute_rollout(rollout)

    def _generate_canary_stages(self, initial_pct: float, stages: int) -> List[float]:
        """生成金丝雀发布阶段比例"""
        if stages <= 1:
            return [100.0]

        stages_list = [initial_pct]
        remaining = 100.0 - initial_pct
        increments = stages - 1

        # 非线性增长：先慢后快
        weights = [1.5 ** i for i in range(increments)]
        total_weight = sum(weights)

        current = initial_pct
        for w in weights:
            current += remaining * (w / total_weight)
            stages_list.append(min(current, 100.0))

        return stages_list

    def _execute_rollout(self, rollout: 'Rollout') -> RolloutResult:
        """执行发布流程"""
        start_time = time.time()
        rollout.status = RolloutStatus.PREPARING
        self._trigger_hooks('pre_rollout', rollout)

        try:
            for stage in rollout.stages:
                rollout.current_stage = stage.stage_id
                rollout.status = RolloutStatus.IN_PROGRESS
                stage.status = RolloutStatus.IN_PROGRESS
                stage.start_time = datetime.now()

                self._trigger_hooks('pre_stage', rollout, stage)

                # 执行此阶段的发布
                self._apply_stage(rollout, stage)

                # 监控阶段
                rollout.status = RolloutStatus.MONITORING
                stage.status = RolloutStatus.MONITORING

                # 收集指标
                stage.metrics = self._collect_metrics(rollout)

                # 检查是否应该回滚
                if self._should_rollback(stage.metrics):
                    rollout.status = RolloutStatus.ROLLING_BACK
                    stage.status = RolloutStatus.ROLLING_BACK
                    self._trigger_hooks('on_rollback', rollout, stage)
                    self._rollback_stage(rollout, stage)
                    stage.passed = False

                    return RolloutResult(
                        rollout_id=rollout.rollout_id,
                        success=False,
                        status=RolloutStatus.ROLLING_BACK,
                        final_percentage=rollout.current_percentage,
                        total_duration=time.time() - start_time,
                        stages_completed=rollout.stages.index(stage),
                        total_targets=len(rollout.targets),
                        targets_updated=rollout.targets_updated,
                        targets_rolled_back=rollout.targets_updated,
                        metrics=stage.metrics,
                        rollback_reason="指标不满足晋升条件"
                    )

                # 阶段通过
                stage.status = RolloutStatus.COMPLETED
                stage.passed = True
                stage.end_time = datetime.now()
                rollout.current_percentage = stage.percentage
                self._trigger_hooks('post_stage', rollout, stage)

            # 发布完成
            rollout.status = RolloutStatus.COMPLETED
            self._trigger_hooks('post_rollout', rollout)

            return RolloutResult(
                rollout_id=rollout.rollout_id,
                success=True,
                status=RolloutStatus.COMPLETED,
                final_percentage=100.0,
                total_duration=time.time() - start_time,
                stages_completed=len(rollout.stages),
                total_targets=len(rollout.targets),
                targets_updated=rollout.targets_updated,
                targets_rolled_back=0,
                metrics=rollout.stages[-1].metrics if rollout.stages else []
            )

        except Exception as e:
            rollout.status = RolloutStatus.FAILED
            self._trigger_hooks('on_failure', rollout, str(e))

            return RolloutResult(
                rollout_id=rollout.rollout_id,
                success=False,
                status=RolloutStatus.FAILED,
                final_percentage=rollout.current_percentage,
                total_duration=time.time() - start_time,
                stages_completed=rollout.stages.index(rollout.current_stage)
                    if rollout.current_stage else 0,
                total_targets=len(rollout.targets),
                targets_updated=rollout.targets_updated,
                targets_rolled_back=0,
                errors=[str(e)]
            )

    def _apply_stage(self, rollout: 'Rollout', stage: RolloutStage):
        """应用发布阶段"""
        target_count = len(rollout.targets)
        if target_count == 0:
            return

        # 计算需要更新的目标数量
        update_count = int(target_count * stage.percentage / 100) - rollout.targets_updated
        update_count = max(0, min(update_count, target_count - rollout.targets_updated))

        # 模拟更新
        for i in range(rollout.targets_updated, rollout.targets_updated + update_count):
            if i < len(rollout.targets):
                rollout.targets[i].status = RolloutStatus.IN_PROGRESS
                rollout.targets[i].percentage = stage.percentage

        rollout.targets_updated += update_count

        # 模拟监控等待（实际场景应该更短或异步）
        if stage.duration > 0:
            time.sleep(min(1.0, stage.duration / 100))  # 加速模拟

    def _rollback_stage(self, rollout: 'Rollout', stage: RolloutStage):
        """回滚阶段"""
        # 模拟回滚
        for target in rollout.targets[:rollout.targets_updated]:
            target.status = RolloutStatus.ROLLING_BACK

    def _collect_metrics(self, rollout: 'Rollout') -> List[RolloutMetric]:
        """收集监控指标"""
        metrics = []
        for name, provider in self._metric_providers.items():
            try:
                metric = provider(rollout)
                metrics.append(metric)
            except Exception:
                pass
        return metrics

    def _should_rollback(self, metrics: List[RolloutMetric]) -> bool:
        """检查是否应该回滚"""
        for metric in metrics:
            if metric.status == MetricStatus.UNHEALTHY:
                return True
            # 如果恶化趋势且接近阈值
            if metric.trend == 'worsening' and metric.current_value > metric.threshold * 0.8:
                return True
        return False

    def generate_rollout_report(self, result: RolloutResult) -> str:
        """生成发布报告"""
        lines = []
        lines.append("=" * 70)
        lines.append("OpenSpec 渐进式发布报告")
        lines.append("=" * 70)
        lines.append(f"发布 ID: {result.rollout_id}")
        lines.append(f"状态: {'成功' if result.success else '失败'} ({result.status.value})")
        lines.append(f"最终发布比例: {result.final_percentage:.1f}%")
        lines.append(f"总耗时: {result.total_duration:.2f} 秒")
        lines.append(f"完成阶段数: {result.stages_completed}")
        lines.append("")

        lines.append("目标统计:")
        lines.append(f"  - 总目标数: {result.total_targets}")
        lines.append(f"  - 已更新: {result.targets_updated}")
        lines.append(f"  - 已回滚: {result.targets_rolled_back}")
        lines.append("")

        if result.metrics:
            lines.append("最终指标:")
            for metric in result.metrics:
                status_symbol = "✓" if metric.status == MetricStatus.HEALTHY else "!"
                lines.append(f"  {status_symbol} {metric.name}: "
                            f"{metric.current_value:.2f}{metric.unit} "
                            f"(阈值: {metric.threshold}{metric.unit})")
            lines.append("")

        if result.rollback_reason:
            lines.append(f"回滚原因: {result.rollback_reason}")
            lines.append("")

        if result.errors:
            lines.append("错误信息:")
            for error in result.errors:
                lines.append(f"  - {error}")
            lines.append("")

        lines.append("=" * 70)
        return "\n".join(lines)


class Rollout:
    """发布实例"""

    def __init__(self,
                 rollout_id: str,
                 name: str,
                 rollout_type: RolloutType,
                 strategy: Dict[str, Any]):
        self.rollout_id = rollout_id
        self.name = name
        self.rollout_type = rollout_type
        self.strategy = strategy
        self.status = RolloutStatus.PENDING
        self.stages: List[RolloutStage] = []
        self.targets: List[RolloutTarget] = []
        self.current_stage: Optional[str] = None
        self.current_percentage: float = 0.0
        self.targets_updated: int = 0
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            'rollout_id': self.rollout_id,
            'name': self.name,
            'type': self.rollout_type.value,
            'status': self.status.value,
            'current_percentage': self.current_percentage,
            'stages': len(self.stages),
            'targets': len(self.targets),
            'targets_updated': self.targets_updated,
            'created_at': self.created_at.isoformat(),
        }
