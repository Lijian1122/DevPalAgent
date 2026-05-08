# -*- coding: utf-8 -*-
"""
OpenSpec 智能诊断引擎 - Phase 5: 深化与体验

核心功能:
- 代码健康度扫描
- 反模式检测 (Anti-Pattern Detection)
- 复杂度分析
- 技术债务评估
- 自动修复建议
"""

from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import ast
import re
from collections import defaultdict


class DiagnosticSeverity(Enum):
    """诊断严重级别"""
    CRITICAL = "critical"    # 必须立即修复
    HIGH = "high"            # 高优先级
    MEDIUM = "medium"        # 中优先级
    LOW = "low"              # 低优先级
    INFO = "info"            # 信息性提示


class DiagnosticCategory(Enum):
    """诊断类别"""
    COMPLEXITY = "complexity"          # 复杂度问题
    MAINTAINABILITY = "maintainability"  # 可维护性问题
    SECURITY = "security"              # 安全问题
    PERFORMANCE = "performance"        # 性能问题
    STYLE = "style"                    # 代码风格
    ARCHITECTURE = "architecture"      # 架构问题
    DOCUMENTATION = "documentation"    # 文档问题
    TECH_DEBT = "tech_debt"            # 技术债务


@dataclass
class DiagnosticIssue:
    """单个诊断问题"""
    issue_id: str
    category: DiagnosticCategory
    severity: DiagnosticSeverity
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    auto_fixable: bool = False
    fix_cost_estimate: int = 1  # 预估修复成本（人天）
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'issue_id': self.issue_id,
            'category': self.category.value,
            'severity': self.severity.value,
            'message': self.message,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'suggestion': self.suggestion,
            'auto_fixable': self.auto_fixable,
            'fix_cost_estimate': self.fix_cost_estimate,
            'metadata': self.metadata,
        }


@dataclass
class HealthScore:
    """代码健康度评分"""
    overall: float = 100.0  # 综合评分 0-100
    complexity: float = 100.0
    maintainability: float = 100.0
    security: float = 100.0
    documentation: float = 100.0
    architecture: float = 100.0
    grade: str = "A"  # A+, A, B, C, D, F

    def calculate_grade(self):
        """计算等级"""
        if self.overall >= 95:
            self.grade = "A+"
        elif self.overall >= 85:
            self.grade = "A"
        elif self.overall >= 75:
            self.grade = "B"
        elif self.overall >= 65:
            self.grade = "C"
        elif self.overall >= 50:
            self.grade = "D"
        else:
            self.grade = "F"
        return self.grade


@dataclass
class DiagnosticResult:
    """诊断结果汇总"""
    files_scanned: int = 0
    total_issues: int = 0
    issues: List[DiagnosticIssue] = field(default_factory=list)
    health_score: HealthScore = field(default_factory=HealthScore)
    tech_debt_days: float = 0.0  # 技术债务总天数
    scan_duration: float = 0.0

    def by_severity(self) -> Dict[str, int]:
        """按严重级别统计"""
        counts = defaultdict(int)
        for issue in self.issues:
            counts[issue.severity.value] += 1
        return dict(counts)

    def by_category(self) -> Dict[str, int]:
        """按类别统计"""
        counts = defaultdict(int)
        for issue in self.issues:
            counts[issue.category.value] += 1
        return dict(counts)

    def get_critical_issues(self) -> List[DiagnosticIssue]:
        """获取关键问题"""
        return [i for i in self.issues if i.severity == DiagnosticSeverity.CRITICAL]

    def get_auto_fixable(self) -> List[DiagnosticIssue]:
        """获取可自动修复的问题"""
        return [i for i in self.issues if i.auto_fixable]


class DiagnosticRule:
    """诊断规则基类"""

    def __init__(self,
                 rule_id: str,
                 category: DiagnosticCategory,
                 severity: DiagnosticSeverity,
                 description: str):
        self.rule_id = rule_id
        self.category = category
        self.severity = severity
        self.description = description
        self.enabled = True

    def check(self, content: str, file_path: Path) -> List[DiagnosticIssue]:
        """执行检查 - 子类重写此方法"""
        raise NotImplementedError

    def calculate_impact(self, issue_count: int) -> float:
        """计算对健康度的影响"""
        severity_weights = {
            DiagnosticSeverity.CRITICAL: 10.0,
            DiagnosticSeverity.HIGH: 5.0,
            DiagnosticSeverity.MEDIUM: 2.0,
            DiagnosticSeverity.LOW: 0.5,
            DiagnosticSeverity.INFO: 0.1,
        }
        return issue_count * severity_weights.get(self.severity, 1.0)


# ============================================
# Python 代码分析规则
# ============================================

class FunctionComplexityRule(DiagnosticRule):
    """函数复杂度规则 - 圈复杂度检测"""

    def __init__(self):
        super().__init__(
            "PY001",
            DiagnosticCategory.COMPLEXITY,
            DiagnosticSeverity.MEDIUM,
            "检测函数圈复杂度过高"
        )
        self.max_complexity = 15

    def _calculate_cyclomatic_complexity(self, node) -> int:
        """计算圈复杂度"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.And, ast.Or,
                                  ast.IfExp, ast.Try, ast.ExceptHandler)):
                complexity += 1
        return complexity

    def check(self, content: str, file_path: Path) -> List[DiagnosticIssue]:
        issues = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    complexity = self._calculate_cyclomatic_complexity(node)
                    if complexity > self.max_complexity:
                        issues.append(DiagnosticIssue(
                            issue_id=self.rule_id,
                            category=self.category,
                            severity=self.severity,
                            message=f"函数 '{node.name}' 圈复杂度为 {complexity} (阈值: {self.max_complexity})",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            suggestion=f"考虑将函数拆分为多个更小的函数，每个函数专注于单一职责",
                            auto_fixable=False,
                            fix_cost_estimate=1,
                        ))
        except SyntaxError:
            pass
        return issues


class GodObjectRule(DiagnosticRule):
    """上帝对象检测 - 超大类"""

    def __init__(self):
        super().__init__(
            "PY002",
            DiagnosticCategory.ARCHITECTURE,
            DiagnosticSeverity.HIGH,
            "检测上帝对象（超大类）"
        )
        self.max_methods = 20
        self.max_attributes = 15

    def check(self, content: str, file_path: Path) -> List[DiagnosticIssue]:
        issues = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    attributes = [n for n in node.body if isinstance(n, ast.Assign)]

                    if len(methods) > self.max_methods:
                        issues.append(DiagnosticIssue(
                            issue_id=self.rule_id,
                            category=self.category,
                            severity=self.severity,
                            message=f"类 '{node.name}' 有 {len(methods)} 个方法，可能是上帝对象",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            suggestion=f"考虑按职责拆分此类，使用组合或继承来分解功能",
                            auto_fixable=False,
                            fix_cost_estimate=3,
                        ))
                    elif len(attributes) > self.max_attributes:
                        issues.append(DiagnosticIssue(
                            issue_id=self.rule_id,
                            category=self.category,
                            severity=DiagnosticSeverity.MEDIUM,
                            message=f"类 '{node.name}' 有 {len(attributes)} 个属性，可能承担过多职责",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            suggestion="考虑将相关属性封装到独立的数据类中",
                            auto_fixable=False,
                            fix_cost_estimate=1,
                        ))
        except SyntaxError:
            pass
        return issues


class MagicNumberRule(DiagnosticRule):
    """魔法数字检测"""

    def __init__(self):
        super().__init__(
            "PY003",
            DiagnosticCategory.MAINTAINABILITY,
            DiagnosticSeverity.LOW,
            "检测魔法数字（未命名的常量）"
        )
        self.allowed_numbers = {0, 1, 2, -1, 10, 100, 1000}

    def check(self, content: str, file_path: Path) -> List[DiagnosticIssue]:
        issues = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                    if node.value not in self.allowed_numbers:
                        issues.append(DiagnosticIssue(
                            issue_id=self.rule_id,
                            category=self.category,
                            severity=self.severity,
                            message=f"发现魔法数字: {node.value}",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            suggestion=f"将数字提取为命名常量，提高可读性",
                            auto_fixable=False,
                            fix_cost_estimate=1,
                        ))
        except SyntaxError:
            pass
        return issues


class NestedDepthRule(DiagnosticRule):
    """嵌套深度检测"""

    def __init__(self):
        super().__init__(
            "PY004",
            DiagnosticCategory.COMPLEXITY,
            DiagnosticSeverity.MEDIUM,
            "检测代码嵌套过深"
        )
        self.max_depth = 4

    def _calculate_nested_depth(self, node, depth: int = 0) -> int:
        """计算节点嵌套深度"""
        max_depth = depth
        nesting_nodes = (ast.If, ast.While, ast.For, ast.Try, ast.With)
        for child in ast.iter_child_nodes(node):
            if isinstance(child, nesting_nodes):
                max_depth = max(max_depth, self._calculate_nested_depth(child, depth + 1))
            else:
                max_depth = max(max_depth, self._calculate_nested_depth(child, depth))
        return max_depth

    def check(self, content: str, file_path: Path) -> List[DiagnosticIssue]:
        issues = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    depth = self._calculate_nested_depth(node)
                    if depth > self.max_depth:
                        issues.append(DiagnosticIssue(
                            issue_id=self.rule_id,
                            category=self.category,
                            severity=self.severity,
                            message=f"函数 '{node.name}' 嵌套深度为 {depth} (阈值: {self.max_depth})",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            suggestion="考虑将深层嵌套提取为独立函数或使用早期返回模式",
                            auto_fixable=False,
                            fix_cost_estimate=2,
                        ))
        except SyntaxError:
            pass
        return issues


class TodoCommentRule(DiagnosticRule):
    """TODO/FIXME 注释检测"""

    def __init__(self):
        super().__init__(
            "PY005",
            DiagnosticCategory.TECH_DEBT,
            DiagnosticSeverity.INFO,
            "检测待办事项注释"
        )

    def check(self, content: str, file_path: Path) -> List[DiagnosticIssue]:
        issues = []
        patterns = [
            (r'(?i)todo[:\s]', "TODO", DiagnosticSeverity.LOW),
            (r'(?i)fixme[:\s]', "FIXME", DiagnosticSeverity.MEDIUM),
            (r'(?i)hack[:\s]', "HACK", DiagnosticSeverity.HIGH),
            (r'(?i)xxx[:\s]', "XXX", DiagnosticSeverity.HIGH),
        ]

        for i, line in enumerate(content.split('\n'), 1):
            for pattern, tag, severity in patterns:
                if re.search(pattern, line):
                    match = re.search(pattern + r'(.*)', line)
                    note = match.group(1).strip() if match else ""
                    issues.append(DiagnosticIssue(
                        issue_id=self.rule_id,
                        category=self.category,
                        severity=severity,
                        message=f"{tag}: {note}" if note else "待处理注释" if not note else note,
                        file_path=str(file_path),
                        line_number=i,
                        suggestion="尽快处理此待办事项",
                        auto_fixable=False,
                        fix_cost_estimate=1,
                    ))
        return issues


class MissingDocstringRule(DiagnosticRule):
    """缺失文档字符串检测"""

    def __init__(self):
        super().__init__(
            "PY006",
            DiagnosticCategory.DOCUMENTATION,
            DiagnosticSeverity.LOW,
            "检测缺失文档字符串"
        )

    def check(self, content: str, file_path: Path) -> List[DiagnosticIssue]:
        issues = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    docstring = ast.get_docstring(node)
                    if not docstring:
                        issues.append(DiagnosticIssue(
                            issue_id=self.rule_id,
                            category=self.category,
                            severity=DiagnosticSeverity.LOW,
                            message=f"类 '{node.name}' 缺少文档字符串",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            suggestion="添加类级别的文档说明其用途和职责",
                            auto_fixable=False,
                            fix_cost_estimate=1,
                        ))
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    docstring = ast.get_docstring(node)
                    if not docstring and not node.name.startswith('_'):
                        issues.append(DiagnosticIssue(
                            issue_id=self.rule_id,
                            category=self.category,
                            severity=DiagnosticSeverity.LOW,
                            message=f"函数 '{node.name}' 缺少文档字符串",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            suggestion="添加函数级别的文档，说明参数、返回值和行为",
                            auto_fixable=False,
                            fix_cost_estimate=1,
                        ))
        except SyntaxError:
            pass
        return issues


# ============================================
# 通用文件分析规则
# ============================================

class FileSizeRule(DiagnosticRule):
    """文件大小规则"""

    def __init__(self):
        super().__init__(
            "GEN001",
            DiagnosticCategory.MAINTAINABILITY,
            DiagnosticSeverity.MEDIUM,
            "检测超大文件"
        )
        self.max_lines = 500

    def check(self, content: str, file_path: Path) -> List[DiagnosticIssue]:
        issues = []
        line_count = len(content.split('\n'))
        if line_count > self.max_lines:
            issues.append(DiagnosticIssue(
                issue_id=self.rule_id,
                category=self.category,
                severity=self.severity,
                message=f"文件过大: {line_count} 行 (阈值: {self.max_lines})",
                file_path=str(file_path),
                suggestion="考虑按功能拆分此文件，提高可维护性",
                auto_fixable=False,
                fix_cost_estimate=2,
            ))
        return issues


# ============================================
# 诊断引擎
# ============================================

class DiagnosticEngine:
    """智能诊断引擎 - Phase 5 核心组件

    功能:
    - 多规则代码质量扫描
    - 健康度评分
    - 技术债务评估
    - 可扩展的规则系统
    - 批量文件扫描
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = config or {}
        self._rules: List[DiagnosticRule] = []
        self._register_default_rules()

    def _register_default_rules(self):
        """注册默认规则"""
        self.register_rule(FunctionComplexityRule())
        self.register_rule(GodObjectRule())
        self.register_rule(MagicNumberRule())
        self.register_rule(NestedDepthRule())
        self.register_rule(TodoCommentRule())
        self.register_rule(MissingDocstringRule())
        self.register_rule(FileSizeRule())

    def register_rule(self, rule: DiagnosticRule):
        """注册诊断规则"""
        self._rules.append(rule)

    def disable_rule(self, rule_id: str):
        """禁用规则"""
        for rule in self._rules:
            if rule.rule_id == rule_id:
                rule.enabled = False

    def enable_rule(self, rule_id: str):
        """启用规则"""
        for rule in self._rules:
            if rule.rule_id == rule_id:
                rule.enabled = True

    def scan_file(self, file_path: Path) -> List[DiagnosticIssue]:
        """扫描单个文件"""
        issues = []
        try:
            content = file_path.read_text(encoding='utf-8')
            for rule in self._rules:
                if rule.enabled:
                    rule_issues = rule.check(content, file_path)
                    issues.extend(rule_issues)
        except Exception as e:
            # 忽略无法读取的文件
            pass
        return issues

    def scan_directory(self,
                      root_dir: Path,
                      patterns: Optional[List[str]] = None,
                      exclude_patterns: Optional[List[str]] = None) -> DiagnosticResult:
        """扫描整个目录"""
        import time
        start_time = time.time()

        root_dir = Path(root_dir)
        patterns = patterns or ['*.py']
        exclude_patterns = exclude_patterns or ['__pycache__', '.git', '*.pyc']

        all_issues = []
        files_scanned = 0

        for pattern in patterns:
            for file_path in root_dir.rglob(pattern):
                # 检查排除模式
                should_exclude = False
                for excl in exclude_patterns:
                    if excl.startswith('*'):
                        if file_path.match(excl):
                            should_exclude = True
                            break
                    else:
                        if excl in file_path.parts:
                            should_exclude = True
                            break

                if should_exclude:
                    continue

                issues = self.scan_file(file_path)
                if issues:
                    all_issues.extend(issues)
                files_scanned += 1

        # 计算健康度评分
        health_score = self._calculate_health_score(all_issues)

        # 计算技术债务
        tech_debt = sum(issue.fix_cost_estimate for issue in all_issues)

        result = DiagnosticResult(
            files_scanned=files_scanned,
            total_issues=len(all_issues),
            issues=all_issues,
            health_score=health_score,
            tech_debt_days=tech_debt,
            scan_duration=time.time() - start_time
        )

        return result

    def _calculate_health_score(self, issues: List[DiagnosticIssue]) -> HealthScore:
        """计算健康度评分"""
        score = HealthScore()

        # 按类别统计扣分
        category_impacts = defaultdict(float)
        for issue in issues:
            weight = {
                DiagnosticSeverity.CRITICAL: 8.0,
                DiagnosticSeverity.HIGH: 4.0,
                DiagnosticSeverity.MEDIUM: 2.0,
                DiagnosticSeverity.LOW: 0.5,
                DiagnosticSeverity.INFO: 0.1,
            }.get(issue.severity, 1.0)

            category_map = {
                DiagnosticCategory.COMPLEXITY: 'complexity',
                DiagnosticCategory.MAINTAINABILITY: 'maintainability',
                DiagnosticCategory.SECURITY: 'security',
                DiagnosticCategory.DOCUMENTATION: 'documentation',
                DiagnosticCategory.ARCHITECTURE: 'architecture',
                DiagnosticCategory.PERFORMANCE: 'maintainability',
                DiagnosticCategory.STYLE: 'maintainability',
                DiagnosticCategory.TECH_DEBT: 'maintainability',
            }

            category_key = category_map.get(issue.category, 'maintainability')
            category_impacts[category_key] += weight

        # 应用扣分
        for cat, impact in category_impacts.items():
            if hasattr(score, cat):
                current = getattr(score, cat)
                setattr(score, cat, max(0.0, current - min(50.0, impact)))

        # 综合评分 = 各项的加权平均
        components = [
            score.complexity,
            score.maintainability,
            score.security,
            score.documentation,
            score.architecture,
        ]
        weights = [0.25, 0.25, 0.20, 0.15, 0.15]

        score.overall = sum(c * w for c, w in zip(components, weights))
        score.calculate_grade()

        return score

    def generate_report(self, result: DiagnosticResult, format: str = 'text') -> str:
        """生成诊断报告"""
        if format == 'json':
            import json
            return json.dumps({
                'files_scanned': result.files_scanned,
                'total_issues': result.total_issues,
                'by_severity': result.by_severity(),
                'by_category': result.by_category(),
                'health_score': {
                    'overall': result.health_score.overall,
                    'grade': result.health_score.grade,
                    'complexity': result.health_score.complexity,
                    'maintainability': result.health_score.maintainability,
                    'security': result.health_score.security,
                    'documentation': result.health_score.documentation,
                    'architecture': result.health_score.architecture,
                },
                'tech_debt_days': result.tech_debt_days,
                'issues': [i.to_dict() for i in result.issues[:50]],  # 只返回前50个
            }, indent=2, ensure_ascii=False)

        # 文本格式
        lines = []
        lines.append("=" * 70)
        lines.append("OpenSpec 智能诊断报告")
        lines.append("=" * 70)
        lines.append(f"扫描文件数: {result.files_scanned}")
        lines.append(f"发现问题数: {result.total_issues}")
        lines.append(f"扫描耗时: {result.scan_duration:.2f}秒")
        lines.append("")

        # 健康度
        hs = result.health_score
        lines.append(f"代码健康度: {hs.overall:.1f}/100 (等级: {hs.grade})")
        lines.append(f"  - 复杂度:     {hs.complexity:.1f}")
        lines.append(f"  - 可维护性:   {hs.maintainability:.1f}")
        lines.append(f"  - 安全性:     {hs.security:.1f}")
        lines.append(f"  - 文档:       {hs.documentation:.1f}")
        lines.append(f"  - 架构:       {hs.architecture:.1f}")
        lines.append("")

        # 技术债务
        lines.append(f"技术债务估算: {result.tech_debt_days:.1f} 人天")
        lines.append("")

        # 按严重程度统计
        by_sev = result.by_severity()
        lines.append("问题分布 (按严重程度):")
        for sev in ['critical', 'high', 'medium', 'low', 'info']:
            count = by_sev.get(sev, 0)
            if count > 0:
                lines.append(f"  {sev.upper():10s}: {count}")
        lines.append("")

        # 按类别统计
        by_cat = result.by_category()
        lines.append("问题分布 (按类别):")
        for cat, count in by_cat.items():
            lines.append(f"  {cat:20s}: {count}")
        lines.append("")

        # 关键问题
        critical = result.get_critical_issues()
        if critical:
            lines.append("关键问题 (需要优先处理):")
            for issue in critical[:5]:
                lines.append(f"  [{issue.severity.value}] {issue.message}")
                lines.append(f"    文件: {issue.file_path}:{issue.line_number}")
            lines.append("")

        lines.append("=" * 70)
        return "\n".join(lines)
