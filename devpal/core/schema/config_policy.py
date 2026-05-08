# -*- coding: utf-8 -*-
"""
OpenSpec 配置驱动策略系统 - Phase 5: 深化与体验

核心功能:
- YAML 配置文件驱动
- 可自定义验证规则
- 可自定义变更策略
- 多环境配置支持
- 配置继承与覆盖
"""

from typing import Any, Dict, List, Optional, Callable, TypeVar, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import yaml
import copy


class PolicyType(Enum):
    """策略类型"""
    VALIDATION = "validation"          # 验证规则
    CHANGE_STRATEGY = "change_strategy"  # 变更策略
    ROLLOUT = "rollout"                # 发布策略
    NOTIFICATION = "notification"      # 通知策略
    QUALITY_GATE = "quality_gate"      # 质量门禁


class EnforcementLevel(Enum):
    """强制执行级别"""
    OFF = "off"                        # 关闭
    WARN = "warn"                      # 仅警告
    ENFORCE = "enforce"                # 强制（阻断）
    AUTO_FIX = "auto_fix"              # 自动修复


@dataclass
class PolicyRule:
    """策略规则"""
    rule_id: str
    name: str
    description: str = ""
    policy_type: PolicyType = PolicyType.VALIDATION
    level: EnforcementLevel = EnforcementLevel.ENFORCE
    enabled: bool = True
    conditions: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    actions: List[str] = field(default_factory=list)

    def matches(self, context: Dict[str, Any]) -> bool:
        """检查是否匹配上下文条件"""
        if not self.enabled:
            return False

        for key, expected_value in self.conditions.items():
            actual_value = context.get(key)

            # 通配符支持
            if isinstance(expected_value, str) and expected_value.endswith('*'):
                prefix = expected_value[:-1]
                if not (isinstance(actual_value, str) and actual_value.startswith(prefix)):
                    return False
            elif isinstance(expected_value, list):
                if actual_value not in expected_value:
                    return False
            elif actual_value != expected_value:
                return False

        return True


@dataclass
class QualityGate:
    """质量门禁"""
    gate_id: str
    name: str
    description: str = ""
    enabled: bool = True
    min_health_score: float = 70.0
    max_critical_issues: int = 0
    max_high_issues: int = 5
    max_tech_debt_days: float = 10.0
    fail_on_error: bool = True

    def evaluate(self, diagnostic_result) -> Tuple[bool, List[str]]:
        """评估是否通过门禁"""
        if not self.enabled:
            return True, []

        reasons = []
        passed = True

        hs = diagnostic_result.health_score
        if hs.overall < self.min_health_score:
            reasons.append(f"健康度 {hs.overall:.1f} 低于阈值 {self.min_health_score}")
            passed = False

        by_sev = diagnostic_result.by_severity()
        critical_count = by_sev.get('critical', 0)
        if critical_count > self.max_critical_issues:
            reasons.append(f"关键问题 {critical_count} 超过阈值 {self.max_critical_issues}")
            passed = False

        high_count = by_sev.get('high', 0)
        if high_count > self.max_high_issues:
            reasons.append(f"高优先级问题 {high_count} 超过阈值 {self.max_high_issues}")
            passed = False

        if diagnostic_result.tech_debt_days > self.max_tech_debt_days:
            reasons.append(f"技术债务 {diagnostic_result.tech_debt_days:.1f} 超过阈值 {self.max_tech_debt_days}")
            passed = False

        return passed, reasons


@dataclass
class ChangeStrategy:
    """变更策略"""
    strategy_id: str
    name: str
    description: str = ""
    auto_apply: bool = False           # 自动应用变更
    require_review: bool = True        # 需要代码审查
    backup_before_change: bool = True  # 变更前备份
    incremental_apply: bool = True     # 增量应用
    max_changes_per_batch: int = 10    # 每批最大变更数
    dry_run_first: bool = True         # 先执行 dry-run


@dataclass
class RolloutStrategy:
    """发布策略"""
    strategy_id: str
    name: str
    description: str = ""
    strategy_type: str = "canary"      # canary, incremental, blue_green, ab_test
    canary_percentage: float = 10.0    # 金丝雀发布比例
    stages: int = 5                    # 阶段数（增量发布）
    auto_promote: bool = False         # 自动晋升到下一阶段
    promotion_threshold: float = 95.0  # 晋升阈值（健康度）
    rollback_on_failure: bool = True   # 失败自动回滚
    monitoring_window: int = 300       # 监控窗口（秒）


class PolicyConfig:
    """策略配置 - 管理所有策略

    支持的配置文件格式:
    ```yaml
    policy:
      version: "2.0"
      environment: production

      quality_gates:
        default:
          min_health_score: 70
          max_critical_issues: 0
          fail_on_error: true

      validation_rules:
        PY001:
          enabled: true
          level: enforce
          max_complexity: 15

      change_strategy:
        default:
          auto_apply: false
          require_review: true
          backup_before_change: true

      rollout:
        default:
          strategy_type: canary
          canary_percentage: 10
          auto_promote: false
    ```
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._rules: Dict[str, PolicyRule] = {}
        self._quality_gates: Dict[str, QualityGate] = {}
        self._change_strategies: Dict[str, ChangeStrategy] = {}
        self._rollout_strategies: Dict[str, RolloutStrategy] = {}
        self._environment = "default"
        self._parent_config: Optional['PolicyConfig'] = None

        # 注册默认配置
        self._register_defaults()

        if config_path and config_path.exists():
            self.load_from_yaml(config_path)

    def _register_defaults(self):
        """注册默认策略"""
        # 默认质量门禁
        self._quality_gates['default'] = QualityGate(
            gate_id='default',
            name='默认质量门禁',
            min_health_score=70.0,
            max_critical_issues=0,
            max_high_issues=5,
            max_tech_debt_days=10.0,
        )

        # 默认变更策略
        self._change_strategies['default'] = ChangeStrategy(
            strategy_id='default',
            name='默认变更策略',
            auto_apply=False,
            require_review=True,
            backup_before_change=True,
        )

        # 默认发布策略
        self._rollout_strategies['default'] = RolloutStrategy(
            strategy_id='default',
            name='默认发布策略',
            strategy_type='canary',
            canary_percentage=10.0,
            auto_promote=False,
        )

    def load_from_yaml(self, config_path: Path):
        """从 YAML 文件加载配置"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        self._config = config_data or {}
        policy_config = self._config.get('policy', {})

        self._environment = policy_config.get('environment', 'default')

        # 加载质量门禁
        for gate_id, gate_config in policy_config.get('quality_gates', {}).items():
            self._quality_gates[gate_id] = QualityGate(
                gate_id=gate_id,
                name=gate_config.get('name', gate_id),
                description=gate_config.get('description', ''),
                enabled=gate_config.get('enabled', True),
                min_health_score=gate_config.get('min_health_score', 70.0),
                max_critical_issues=gate_config.get('max_critical_issues', 0),
                max_high_issues=gate_config.get('max_high_issues', 5),
                max_tech_debt_days=gate_config.get('max_tech_debt_days', 10.0),
                fail_on_error=gate_config.get('fail_on_error', True),
            )

        # 加载验证规则
        for rule_id, rule_config in policy_config.get('validation_rules', {}).items():
            rule = PolicyRule(
                rule_id=rule_id,
                name=rule_config.get('name', rule_id),
                description=rule_config.get('description', ''),
                enabled=rule_config.get('enabled', True),
                level=EnforcementLevel(rule_config.get('level', 'enforce')),
                parameters={k: v for k, v in rule_config.items()
                           if k not in ['name', 'description', 'enabled', 'level']}
            )
            self._rules[rule_id] = rule

        # 加载变更策略
        for strat_id, strat_config in policy_config.get('change_strategy', {}).items():
            self._change_strategies[strat_id] = ChangeStrategy(
                strategy_id=strat_id,
                name=strat_config.get('name', strat_id),
                auto_apply=strat_config.get('auto_apply', False),
                require_review=strat_config.get('require_review', True),
                backup_before_change=strat_config.get('backup_before_change', True),
                incremental_apply=strat_config.get('incremental_apply', True),
                max_changes_per_batch=strat_config.get('max_changes_per_batch', 10),
                dry_run_first=strat_config.get('dry_run_first', True),
            )

        # 加载发布策略
        for strat_id, strat_config in policy_config.get('rollout', {}).items():
            self._rollout_strategies[strat_id] = RolloutStrategy(
                strategy_id=strat_id,
                name=strat_config.get('name', strat_id),
                strategy_type=strat_config.get('strategy_type', 'canary'),
                canary_percentage=strat_config.get('canary_percentage', 10.0),
                stages=strat_config.get('stages', 5),
                auto_promote=strat_config.get('auto_promote', False),
                promotion_threshold=strat_config.get('promotion_threshold', 95.0),
                rollback_on_failure=strat_config.get('rollback_on_failure', True),
                monitoring_window=strat_config.get('monitoring_window', 300),
            )

    def save_to_yaml(self, config_path: Optional[Path] = None):
        """保存配置到 YAML 文件"""
        path = config_path or self.config_path
        if not path:
            raise ValueError("No config path specified")

        config_data = {
            'policy': {
                'version': '2.0',
                'environment': self._environment,
                'quality_gates': {},
                'validation_rules': {},
                'change_strategy': {},
                'rollout': {},
            }
        }

        # 质量门禁
        for gate_id, gate in self._quality_gates.items():
            config_data['policy']['quality_gates'][gate_id] = {
                'name': gate.name,
                'description': gate.description,
                'enabled': gate.enabled,
                'min_health_score': gate.min_health_score,
                'max_critical_issues': gate.max_critical_issues,
                'max_high_issues': gate.max_high_issues,
                'max_tech_debt_days': gate.max_tech_debt_days,
                'fail_on_error': gate.fail_on_error,
            }

        # 验证规则
        for rule_id, rule in self._rules.items():
            config_data['policy']['validation_rules'][rule_id] = {
                'name': rule.name,
                'description': rule.description,
                'enabled': rule.enabled,
                'level': rule.level.value,
                **rule.parameters,
            }

        # 变更策略
        for strat_id, strat in self._change_strategies.items():
            config_data['policy']['change_strategy'][strat_id] = {
                'name': strat.name,
                'auto_apply': strat.auto_apply,
                'require_review': strat.require_review,
                'backup_before_change': strat.backup_before_change,
                'incremental_apply': strat.incremental_apply,
                'max_changes_per_batch': strat.max_changes_per_batch,
                'dry_run_first': strat.dry_run_first,
            }

        # 发布策略
        for strat_id, strat in self._rollout_strategies.items():
            config_data['policy']['rollout'][strat_id] = {
                'name': strat.name,
                'strategy_type': strat.strategy_type,
                'canary_percentage': strat.canary_percentage,
                'stages': strat.stages,
                'auto_promote': strat.auto_promote,
                'promotion_threshold': strat.promotion_threshold,
                'rollback_on_failure': strat.rollback_on_failure,
                'monitoring_window': strat.monitoring_window,
            }

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True,
                     sort_keys=False)

    def get_quality_gate(self, gate_id: str = 'default') -> Optional[QualityGate]:
        """获取质量门禁"""
        return self._quality_gates.get(gate_id)

    def get_change_strategy(self, strategy_id: str = 'default') -> Optional[ChangeStrategy]:
        """获取变更策略"""
        return self._change_strategies.get(strategy_id)

    def get_rollout_strategy(self, strategy_id: str = 'default') -> Optional[RolloutStrategy]:
        """获取发布策略"""
        return self._rollout_strategies.get(strategy_id)

    def get_rule(self, rule_id: str) -> Optional[PolicyRule]:
        """获取验证规则"""
        return self._rules.get(rule_id)

    def set_parent_config(self, parent_config: 'PolicyConfig'):
        """设置父配置（用于继承）"""
        self._parent_config = parent_config

    def evaluate_quality_gate(self, diagnostic_result, gate_id: str = 'default') -> Tuple[bool, List[str]]:
        """评估是否通过质量门禁"""
        gate = self.get_quality_gate(gate_id)
        if not gate:
            # 如果没有找到，尝试从父配置获取
            if self._parent_config:
                return self._parent_config.evaluate_quality_gate(diagnostic_result, gate_id)
            return True, []

        return gate.evaluate(diagnostic_result)

    def apply_to_diagnostic_engine(self, diagnostic_engine):
        """应用配置到诊断引擎"""
        for rule_id, rule in self._rules.items():
            if not rule.enabled:
                diagnostic_engine.disable_rule(rule_id)
            else:
                # 更新规则参数
                for d_rule in diagnostic_engine._rules:
                    if d_rule.rule_id == rule_id:
                        for key, value in rule.parameters.items():
                            if hasattr(d_rule, key):
                                setattr(d_rule, key, value)

    @classmethod
    def create_default_config(cls, output_path: Path) -> 'PolicyConfig':
        """创建默认配置文件"""
        config = cls()
        config.config_path = output_path

        # 添加一些示例规则
        config._rules['PY001'] = PolicyRule(
            rule_id='PY001',
            name='函数复杂度限制',
            description='控制函数圈复杂度，提高可维护性',
            level=EnforcementLevel.WARN,
            enabled=True,
            parameters={'max_complexity': 15}
        )

        config._rules['PY002'] = PolicyRule(
            rule_id='PY002',
            name='上帝对象检测',
            description='防止单个类承担过多职责',
            level=EnforcementLevel.ENFORCE,
            enabled=True,
            parameters={'max_methods': 20, 'max_attributes': 15}
        )

        config.save_to_yaml(output_path)
        return config

    @property
    def environment(self) -> str:
        return self._environment

    @property
    def all_quality_gates(self) -> List[QualityGate]:
        return list(self._quality_gates.values())

    @property
    def all_change_strategies(self) -> List[ChangeStrategy]:
        return list(self._change_strategies.values())

    @property
    def all_rollout_strategies(self) -> List[RolloutStrategy]:
        return list(self._rollout_strategies.values())
