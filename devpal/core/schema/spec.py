# -*- coding: utf-8 -*-
"""
Spec 对象模型 - OpenSpec 规范优先架构的核心
Phase 1: Spec-First 基础能力实现

包含:
- SpecRequirement: 单个需求规范对象
- SpecDelta: 增量变更对象
- SpecSnapshot: 规范快照 (归档用)
- SpecEngine: 规范引擎入口
"""
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import hashlib
import json
import re
from datetime import datetime

from .requirements import RequirementDocument, RequirementItem


class SpecStatus(Enum):
    """规范状态"""
    DRAFT = "draft"           # 草稿
    PROPOSED = "proposed"     # 已提出
    APPROVED = "approved"     # 已批准
    IN_PROGRESS = "in_progress"  # 实现中
    IMPLEMENTED = "implemented"  # 已实现
    VERIFIED = "verified"     # 已验证
    DEPRECATED = "deprecated"  # 已废弃
    ARCHIVED = "archived"     # 已归档


class DeltaType(Enum):
    """Delta 变更类型"""
    ADD = "add"
    MODIFY = "modify"
    REMOVE = "remove"
    RENAME = "rename"
    REORDER = "reorder"
    SPLIT = "split"
    MERGE = "merge"


class ChangeSeverity(Enum):
    """变更影响等级"""
    PATCH = "patch"       # 最小变更（不影响功能，如格式修正）
    MINOR = "minor"       # 小变更（不影响现有功能）
    MAJOR = "major"       # 大变更（可能破坏现有功能）
    BREAKING = "breaking"  # 破坏性变更（必须重新评估所有依赖）


@dataclass
class SpecArtifactRef:
    """规范关联的工件引用"""
    artifact_id: str
    artifact_type: str  # code, test, doc, config
    file_path: Optional[str] = None
    confidence: float = 1.0  # 关联可信度 0-1
    evidence: List[str] = field(default_factory=list)  # 关联证据（如代码中出现 REQ-001）


@dataclass
class SpecRequirement:
    """单个需求规范对象 - 规范优先架构的核心实体"""
    id: str
    title: str
    description: str = ""
    status: SpecStatus = SpecStatus.DRAFT

    # 验收标准
    acceptance_criteria: List[str] = field(default_factory=list)

    # 关联工件
    artifacts: List[SpecArtifactRef] = field(default_factory=list)

    # 元数据
    priority: int = 3  # 1-5, 1最高
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # 追踪信息
    version: str = "1.0"
    parent_id: Optional[str] = None  # 父需求ID
    depends_on: List[str] = field(default_factory=list)  # 依赖的其他需求

    # 实现状态
    implementation_progress: float = 0.0  # 实现进度 0-1
    test_coverage: float = 0.0  # 测试覆盖度 0-1

    metadata: Dict[str, Any] = field(default_factory=dict)

    def content_hash(self) -> str:
        """内容哈希，用于检测变更"""
        content = f"{self.id}|{self.title}|{self.description}|{'|'.join(self.acceptance_criteria)}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:12]

    def to_dict(self) -> Dict[str, Any]:
        """序列化"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "acceptance_criteria": self.acceptance_criteria,
            "artifacts": [
                {
                    "artifact_id": a.artifact_id,
                    "artifact_type": a.artifact_type,
                    "file_path": a.file_path,
                    "confidence": a.confidence,
                    "evidence": a.evidence
                }
                for a in self.artifacts
            ],
            "priority": self.priority,
            "tags": self.tags,
            "version": self.version,
            "parent_id": self.parent_id,
            "depends_on": self.depends_on,
            "implementation_progress": self.implementation_progress,
            "test_coverage": self.test_coverage,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpecRequirement':
        """反序列化"""
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            status=SpecStatus(data.get("status", "draft")),
            acceptance_criteria=data.get("acceptance_criteria", []),
            artifacts=[
                SpecArtifactRef(
                    artifact_id=a["artifact_id"],
                    artifact_type=a["artifact_type"],
                    file_path=a.get("file_path"),
                    confidence=a.get("confidence", 1.0),
                    evidence=a.get("evidence", [])
                )
                for a in data.get("artifacts", [])
            ],
            priority=data.get("priority", 3),
            tags=data.get("tags", []),
            version=data.get("version", "1.0"),
            parent_id=data.get("parent_id"),
            depends_on=data.get("depends_on", []),
            implementation_progress=data.get("implementation_progress", 0.0),
            test_coverage=data.get("test_coverage", 0.0),
            metadata=data.get("metadata", {})
        )


@dataclass
class SpecDelta:
    """规范增量变更对象"""
    delta_id: str
    delta_type: DeltaType
    target_id: str  # 目标需求ID

    # 变更内容
    field_name: Optional[str] = None  # 变更的字段 (title, description, status 等)
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None

    # 元数据
    reason: str = ""
    author: str = "agent"
    created_at: datetime = field(default_factory=datetime.now)
    severity: ChangeSeverity = ChangeSeverity.MINOR

    # 影响分析
    affected_artifacts: List[str] = field(default_factory=list)
    affected_requirements: List[str] = field(default_factory=list)

    # 验证结果
    validation_passed: Optional[bool] = None
    validation_issues: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "delta_id": self.delta_id,
            "delta_type": self.delta_type.value,
            "target_id": self.target_id,
            "field_name": self.field_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "reason": self.reason,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "severity": self.severity.value,
            "affected_artifacts": self.affected_artifacts,
            "affected_requirements": self.affected_requirements,
            "validation_passed": self.validation_passed,
            "validation_issues": self.validation_issues,
        }

    @classmethod
    def from_requirement_diff(cls, old: SpecRequirement, new: SpecRequirement, reason: str = "") -> List['SpecDelta']:
        """对比两个需求版本，生成Delta列表"""
        deltas = []

        # 对比标题
        if old.title != new.title:
            deltas.append(cls(
                delta_id=f"{old.id}_title_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                delta_type=DeltaType.MODIFY,
                target_id=old.id,
                field_name="title",
                old_value=old.title,
                new_value=new.title,
                reason=reason or "标题更新",
                severity=ChangeSeverity.MINOR
            ))

        # 对比描述
        if old.description != new.description:
            deltas.append(cls(
                delta_id=f"{old.id}_desc_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                delta_type=DeltaType.MODIFY,
                target_id=old.id,
                field_name="description",
                old_value=old.description,
                new_value=new.description,
                reason=reason or "描述更新",
                severity=ChangeSeverity.MINOR
            ))

        # 对比验收标准
        if old.acceptance_criteria != new.acceptance_criteria:
            deltas.append(cls(
                delta_id=f"{old.id}_ac_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                delta_type=DeltaType.MODIFY,
                target_id=old.id,
                field_name="acceptance_criteria",
                old_value=old.acceptance_criteria,
                new_value=new.acceptance_criteria,
                reason=reason or "验收标准更新",
                severity=ChangeSeverity.MAJOR  # 验收标准变更是重要变更
            ))

        # 对比状态
        if old.status != new.status:
            deltas.append(cls(
                delta_id=f"{old.id}_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                delta_type=DeltaType.MODIFY,
                target_id=old.id,
                field_name="status",
                old_value=old.status.value,
                new_value=new.status.value,
                reason=reason or "状态更新",
                severity=ChangeSeverity.MINOR
            ))

        return deltas


@dataclass
class SpecSnapshot:
    """规范快照 - 用于归档和版本对比"""
    snapshot_id: str
    name: str
    description: str = ""
    requirements: Dict[str, SpecRequirement] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def content_hash(self) -> str:
        """整个快照的内容哈希"""
        hashes = sorted([r.content_hash() for r in self.requirements.values()])
        return hashlib.md5('|'.join(hashes).encode('utf-8')).hexdigest()[:16]

    def save_to_file(self, file_path: Union[str, Path]):
        """保存快照到文件"""
        data = {
            "snapshot_id": self.snapshot_id,
            "name": self.name,
            "description": self.description,
            "content_hash": self.content_hash(),
            "created_at": self.created_at.isoformat(),
            "requirements": {
                rid: req.to_dict()
                for rid, req in self.requirements.items()
            },
            "metadata": self.metadata
        }
        Path(file_path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    @classmethod
    def load_from_file(cls, file_path: Union[str, Path]) -> 'SpecSnapshot':
        """从文件加载快照"""
        data = json.loads(Path(file_path).read_text(encoding='utf-8'))
        return cls(
            snapshot_id=data["snapshot_id"],
            name=data["name"],
            description=data.get("description", ""),
            requirements={
                rid: SpecRequirement.from_dict(req_data)
                for rid, req_data in data.get("requirements", {}).items()
            },
            created_at=datetime.fromisoformat(data["created_at"]),
            metadata=data.get("metadata", {})
        )


class SpecEngine:
    """规范引擎 - Phase 1 核心入口

    Phase 1 功能:
    1. 解析需求文档 → SpecRequirement 对象
    2. 分析需求与代码的关联
    3. 生成 Delta 变更计划
    4. 执行验证流程
    5. 应用变更到工件
    """

    def __init__(self, workspace_path: Optional[Union[str, Path]] = None):
        self.workspace = Path(workspace_path) if workspace_path else Path.cwd()
        self.requirements: Dict[str, SpecRequirement] = {}
        self.snapshots: List[SpecSnapshot] = []

        # P0 状态管理器
        self._state_manager = SpecStateManager(self.workspace / ".spec")

        # 初始化工作目录
        self._init_workspace()

        # 自动加载最新状态（如果存在）
        self._auto_load_latest_state()

    def _init_workspace(self):
        """初始化工作目录结构"""
        (self.workspace / ".spec").mkdir(exist_ok=True)
        (self.workspace / ".spec" / "snapshots").mkdir(exist_ok=True)
        (self.workspace / ".spec" / "deltas").mkdir(exist_ok=True)
        (self.workspace / ".spec" / "rules").mkdir(exist_ok=True)

    # -------------------------------------------------------------------------
    # Phase 1: 需求文档解析与规范对象化
    # -------------------------------------------------------------------------

    def parse_requirement_doc(self, file_path: Union[str, Path]) -> List[SpecRequirement]:
        """解析需求文档，转换为 SpecRequirement 对象

        支持格式:
        - Markdown + FrontMatter (推荐)
        - 纯 Markdown 需求列表

        P0 整合: 自动使用 spec_first_framework 的高性能解析器，
        支持分隔符检测、元数据解析、验收标准精确匹配
        """
        file_path = Path(file_path)

        # P0 整合: 优先使用 spec_first_framework 的高性能解析器
        try:
            from spec_first_framework.parser import RequirementParser

            parser = RequirementParser()
            parsed_specs = parser.parse_from_markdown(file_path)

            specs = []
            for parsed in parsed_specs:
                # 转换 spec_first_framework/parser RequirementSpec → SpecRequirement
                ac_list = []
                for ac in parsed.acceptance_criteria:
                    if hasattr(ac, 'description'):
                        ac_list.append(ac.description)
                    else:
                        ac_list.append(str(ac))

                spec = SpecRequirement(
                    id=parsed.id,
                    title=parsed.title,
                    description=parsed.description,
                    status=SpecStatus.PROPOSED,  # 默认状态
                    acceptance_criteria=ac_list,
                    priority=parsed.priority,
                    tags=parsed.tags,
                )
                specs.append(spec)

        except (ImportError, NameError):
            # 降级: 使用 schema/requirements.py 的基础解析器
            doc = RequirementDocument.load_from_markdown(file_path)

            specs = []
            for req_item in doc.requirements:
                # 转换 RequirementItem → SpecRequirement
                ac_list = []
                for ac in req_item.acceptance_criteria:
                    if hasattr(ac, 'description'):
                        ac_list.append(ac.description)
                    else:
                        ac_list.append(str(ac))

                spec = SpecRequirement(
                    id=req_item.id,
                    title=req_item.title,
                    description=req_item.description,
                    status=SpecStatus(req_item.status.value),
                    acceptance_criteria=ac_list,
                    priority=req_item.priority,
                    tags=req_item.tags,
                )
                specs.append(spec)

        # 自动分析代码关联
        for spec in specs:
            self._analyze_artifact_relations(spec)
            # 存储到 requirements 字典供后续操作
            self.requirements[spec.id] = spec

        return specs

    def _analyze_artifact_relations(self, spec: SpecRequirement):
        """分析需求与代码工件的关联关系

        Phase 1 实现: 简单的字符串匹配，检测代码中是否出现需求ID
        """
        code_patterns = [
            f"REQ-{spec.id.split('-')[-1]}" if '-' in spec.id else spec.id,
            spec.id,
            f"{spec.id}:",
        ]

        # 扫描代码文件
        for ext in ['.py', '.cpp', '.h', '.js', '.ts', '.java']:
            for code_file in self.workspace.rglob(f"*{ext}"):
                if '.git' in str(code_file) or '.spec' in str(code_file):
                    continue

                try:
                    content = code_file.read_text(encoding='utf-8', errors='ignore')
                    for pattern in code_patterns:
                        if pattern in content:
                            artifact_id = f"file:{code_file.relative_to(self.workspace)}"
                            rel_path = str(code_file.relative_to(self.workspace))

                            # 判断工件类型
                            art_type = "code"
                            if "test" in rel_path.lower() or "tests" in rel_path.lower():
                                art_type = "test"
                            elif any(s in rel_path for s in ['docs', 'doc/', 'readme']):
                                art_type = "doc"

                            # 收集证据行
                            lines = content.split('\n')
                            evidence = []
                            for i, line in enumerate(lines, 1):
                                if pattern in line:
                                    evidence.append(f"Line {i}: {line.strip()[:80]}")

                            spec.artifacts.append(SpecArtifactRef(
                                artifact_id=artifact_id,
                                artifact_type=art_type,
                                file_path=rel_path,
                                confidence=0.8 if len(evidence) > 1 else 0.5,
                                evidence=evidence[:3]  # 最多保留3条证据
                            ))
                            break  # 这个文件已经找到关联，继续下一个文件
                except:
                    pass

    def load_all_requirements(self, docs_path: Optional[Union[str, Path]] = None) -> int:
        """加载工作区所有需求文档"""
        search_path = Path(docs_path) if docs_path else self.workspace
        count = 0

        for md_file in search_path.rglob("req_*.md"):
            specs = self.parse_requirement_doc(md_file)
            for spec in specs:
                self.requirements[spec.id] = spec
                count += 1

        return count

    # -------------------------------------------------------------------------
    # Phase 1: Delta 变更规划引擎
    # -------------------------------------------------------------------------

    def plan_delta(self, spec_id: str, changes: Dict[str, Any], reason: str = "") -> List[SpecDelta]:
        """规划单个需求的变更

        Args:
            spec_id: 需求ID
            changes: 变更字典 {field: new_value}
            reason: 变更原因

        Returns:
            变更Delta列表
        """
        if spec_id not in self.requirements:
            raise ValueError(f"需求不存在: {spec_id}")

        old_spec = self.requirements[spec_id]
        new_spec = SpecRequirement.from_dict(old_spec.to_dict())

        # 应用变更
        for field, value in changes.items():
            if hasattr(new_spec, field):
                # 处理枚举类型转换
                if field == 'status' and isinstance(value, str):
                    value = SpecStatus(value)
                setattr(new_spec, field, value)

        # 生成 Delta
        deltas = SpecDelta.from_requirement_diff(old_spec, new_spec, reason)

        # 分析每个Delta的影响
        for delta in deltas:
            self._analyze_delta_impact(delta)

        return deltas

    def _analyze_delta_impact(self, delta: SpecDelta):
        """分析 Delta 的影响范围

        Phase 1 实现:
        - 识别受影响的工件
        - 识别受影响的关联需求
        - 评估变更严重等级
        """
        target_spec = self.requirements.get(delta.target_id)
        if not target_spec:
            return

        # 受影响的工件
        delta.affected_artifacts = [a.artifact_id for a in target_spec.artifacts]

        # 受影响的需求（依赖此需求的其他需求）
        affected_reqs = []
        for req_id, req in self.requirements.items():
            if delta.target_id in req.depends_on:
                affected_reqs.append(req_id)
        delta.affected_requirements = affected_reqs

        # 评估严重等级
        if delta.field_name in ['acceptance_criteria', 'id']:
            delta.severity = ChangeSeverity.BREAKING
        elif delta.field_name in ['description', 'status']:
            delta.severity = ChangeSeverity.MAJOR
        else:
            delta.severity = ChangeSeverity.MINOR

    def dry_run_delta(self, delta: SpecDelta) -> Tuple[bool, List[str], SpecRequirement]:
        """Delta 变更预览（Dry-Run）

        Returns:
            (success, issues, updated_spec)
        """
        if delta.target_id not in self.requirements:
            return False, ["目标需求不存在"], None

        target_spec = self.requirements[delta.target_id]

        # 应用变更到一个副本
        updated_spec = SpecRequirement.from_dict(target_spec.to_dict())

        issues = []
        try:
            if delta.field_name and hasattr(updated_spec, delta.field_name):
                # 处理枚举类型转换
                if delta.field_name == 'status' and isinstance(delta.new_value, str):
                    setattr(updated_spec, delta.field_name, SpecStatus(delta.new_value))
                else:
                    setattr(updated_spec, delta.field_name, delta.new_value)
        except Exception as e:
            issues.append(f"应用变更失败: {str(e)}")
            return False, issues, None

        # 简单验证
        if not updated_spec.title or len(updated_spec.title) < 3:
            issues.append("标题太短，至少需要3个字符")

        if updated_spec.acceptance_criteria and len(updated_spec.acceptance_criteria) == 0:
            issues.append("验收标准不能为空")

        return len(issues) == 0, issues, updated_spec

    def apply_delta(self, delta: SpecDelta, validate: bool = True) -> bool:
        """应用 Delta 变更

        Args:
            delta: 变更对象
            validate: 是否执行验证

        Returns:
            是否成功应用
        """
        if validate:
            success, issues, _ = self.dry_run_delta(delta)
            delta.validation_passed = success
            delta.validation_issues = [{"message": i, "severity": "error"} for i in issues]
            if not success:
                return False

        # 应用变更
        target_spec = self.requirements.get(delta.target_id)
        if not target_spec:
            return False

        if delta.field_name and hasattr(target_spec, delta.field_name):
            setattr(target_spec, delta.field_name, delta.new_value)
            target_spec.updated_at = datetime.now()

        # 保存 Delta 记录
        self._save_delta_record(delta)

        return True

    def _save_delta_record(self, delta: SpecDelta):
        """保存 Delta 历史记录"""
        delta_file = self.workspace / ".spec" / "deltas" / f"{delta.delta_id}.json"
        delta_file.write_text(json.dumps(delta.to_dict(), ensure_ascii=False, indent=2), encoding='utf-8')

    # -------------------------------------------------------------------------
    # Phase 1: 规范优先工作流
    # -------------------------------------------------------------------------

    def spec_first_workflow(self, req_doc_path: str, update_message: str = "") -> Dict[str, Any]:
        """Spec-First 完整工作流

        流程: 需求文档 → 解析为Spec对象 → 变更规划 → 验证 → 生成应用计划
        """
        result = {
            "success": False,
            "requirements_parsed": 0,
            "deltas_planned": 0,
            "validation_issues": [],
            "impact_summary": {},
            "apply_plan": []
        }

        # Step 1: 解析需求文档
        try:
            specs = self.parse_requirement_doc(req_doc_path)
            result["requirements_parsed"] = len(specs)

            # 加入引擎
            for spec in specs:
                self.requirements[spec.id] = spec

        except Exception as e:
            result["validation_issues"].append(f"解析需求文档失败: {str(e)}")
            return result

        # Step 2: 影响分析
        impact = {
            "total_artifacts": sum(len(s.artifacts) for s in specs),
            "artifacts_by_type": {},
            "affected_files": []
        }
        for spec in specs:
            for art in spec.artifacts:
                art_type = art.artifact_type
                impact["artifacts_by_type"][art_type] = impact["artifacts_by_type"].get(art_type, 0) + 1
                if art.file_path:
                    impact["affected_files"].append(art.file_path)

        result["impact_summary"] = impact

        # Step 3: 验证
        all_issues = []
        for spec in specs:
            issues = self._validate_spec(spec)
            all_issues.extend(issues)

        result["validation_issues"] = all_issues

        # Step 4: 生成应用计划
        apply_plan = []
        for spec in specs:
            apply_plan.append({
                "requirement_id": spec.id,
                "title": spec.title,
                "artifacts_to_update": [a.file_path for a in spec.artifacts if a.file_path],
                "estimated_effort": self._estimate_effort(spec)
            })

        result["apply_plan"] = apply_plan
        result["success"] = len(all_issues) == 0 or all(i.get("severity") != "error" for i in all_issues)

        # Step 5: 创建快照
        snapshot = SpecSnapshot(
            snapshot_id=f"snap_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=f"Snapshot for {Path(req_doc_path).name}",
            requirements={s.id: s for s in specs}
        )
        snapshot.save_to_file(
            self.workspace / ".spec" / "snapshots" / f"{snapshot.snapshot_id}.json"
        )
        self.snapshots.append(snapshot)

        return result

    def _validate_spec(self, spec: SpecRequirement) -> List[Dict[str, Any]]:
        """验证单个规范对象"""
        issues = []

        if not spec.title or len(spec.title.strip()) < 3:
            issues.append({
                "severity": "error",
                "field": "title",
                "message": "需求标题过短（至少3个字符）"
            })

        if not spec.description or len(spec.description.strip()) < 10:
            issues.append({
                "severity": "warning",
                "field": "description",
                "message": "需求描述较短，建议补充详细说明"
            })

        if not spec.acceptance_criteria:
            issues.append({
                "severity": "warning",
                "field": "acceptance_criteria",
                "message": "未定义验收标准"
            })

        if spec.artifacts:
            high_conf = sum(1 for a in spec.artifacts if a.confidence >= 0.7)
            if high_conf == 0:
                issues.append({
                    "severity": "info",
                    "field": "artifacts",
                    "message": "未发现高可信度的实现代码"
                })

        return issues

    def _estimate_effort(self, spec: SpecRequirement) -> str:
        """估算实现工作量"""
        ac_count = len(spec.acceptance_criteria)
        art_count = len(spec.artifacts)

        if ac_count <= 2 and art_count > 0:
            return "Small"
        elif ac_count <= 5:
            return "Medium"
        else:
            return "Large"

    # -------------------------------------------------------------------------
    # 状态报告
    # -------------------------------------------------------------------------

    def get_status_report(self) -> Dict[str, Any]:
        """获取规范系统状态报告"""
        status_counts = {}
        for spec in self.requirements.values():
            status = spec.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        artifact_counts = {}
        for spec in self.requirements.values():
            for art in spec.artifacts:
                art_type = art.artifact_type
                artifact_counts[art_type] = artifact_counts.get(art_type, 0) + 1

        return {
            "total_requirements": len(self.requirements),
            "status_distribution": status_counts,
            "artifact_distribution": artifact_counts,
            "snapshots_count": len(self.snapshots),
            "workspace": str(self.workspace)
        }

    # -------------------------------------------------------------------------
    # P0 整合功能: 统一上下文管理
    # -------------------------------------------------------------------------

    def get_context(self) -> 'SpecContext':
        """获取当前规范上下文对象

        Returns:
            包含所有状态的不可变上下文快照
        """
        return SpecContext(
            requirements=self.requirements.copy(),
            snapshots=self.snapshots.copy(),
            workspace=self.workspace,
            validation_engine=self._validation_engine if hasattr(self, '_validation_engine') else None,
            artifact_graph=self._artifact_graph if hasattr(self, '_artifact_graph') else None
        )

    def restore_from_context(self, context: 'SpecContext'):
        """从上下文快照恢复状态"""
        self.requirements = context.requirements.copy()
        self.snapshots = context.snapshots.copy()
        self.workspace = context.workspace

    # -------------------------------------------------------------------------
    # P0: 完整状态快照与版本管理 (增强版)
    # -------------------------------------------------------------------------

    def create_snapshot(self, message: str = "", auto_save: bool = True) -> str:
        """创建状态快照

        Args:
            message: 快照描述
            auto_save: 是否自动持久化到磁盘

        Returns:
            snapshot_id: 快照 ID
        """
        # 创建快照对象
        snapshot = SpecSnapshot(
            snapshot_id=f"snap_{int(datetime.now().timestamp())}",
            name=message or f"Snapshot at {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            description=message,
            requirements=dict(self.requirements)
        )
        self.snapshots.append(snapshot)

        # 自动保存到状态管理器
        if auto_save:
            context = self.get_context()
            return self._state_manager.create_snapshot(context, message)

        return snapshot.id

    def restore_snapshot(self, snapshot_id: str) -> bool:
        """从快照恢复状态

        Args:
            snapshot_id: 快照 ID 或特殊标识符 ("latest", "previous")

        Returns:
            是否成功恢复
        """
        context = self._state_manager.restore_snapshot(snapshot_id)
        if context:
            self.restore_from_context(context)
            return True
        return False

    def list_snapshots(self, limit: int = 20) -> List[Dict[str, Any]]:
        """列出所有快照历史"""
        return self._state_manager.list_snapshots(limit=limit)

    def compare_snapshots(self, snap_id1: str, snap_id2: str) -> Dict[str, Any]:
        """比较两个快照的差异"""
        return self._state_manager.compare_snapshots(snap_id1, snap_id2)

    def create_branch(self, branch_name: str, from_snapshot: Optional[str] = None) -> bool:
        """创建开发分支"""
        return self._state_manager.create_branch(branch_name, from_snapshot)

    def switch_branch(self, branch_name: str) -> bool:
        """切换到指定分支"""
        return self._state_manager.switch_branch(branch_name)

    @property
    def current_branch(self) -> str:
        """获取当前分支名"""
        return self._state_manager.current_branch

    def _auto_load_latest_state(self):
        """启动时自动加载最新状态"""
        try:
            latest = self._state_manager.restore_snapshot("latest")
            if latest:
                self.restore_from_context(latest)
        except Exception:
            # 静默失败，继续使用空状态
            pass

    # -------------------------------------------------------------------------
    # P0: 事务性变更 (Atomic Transactions)
    # -------------------------------------------------------------------------

    def transaction_begin(self) -> str:
        """开始事务

        创建一个恢复点，后续可通过 transaction_rollback 回滚
        """
        tx_id = hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:12]
        setattr(self, f"_tx_{tx_id}_snapshot", self.get_context())
        return tx_id

    def transaction_commit(self, tx_id: str, message: str = "") -> str:
        """提交事务

        事务成功后，自动创建快照
        """
        snapshot_id = self.create_snapshot(message or f"Transaction commit: {tx_id}")
        # 清理事务快照
        if hasattr(self, f"_tx_{tx_id}_snapshot"):
            delattr(self, f"_tx_{tx_id}_snapshot")
        return snapshot_id

    def transaction_rollback(self, tx_id: str) -> bool:
        """回滚事务到开始时的状态"""
        snapshot_attr = f"_tx_{tx_id}_snapshot"
        if hasattr(self, snapshot_attr):
            context = getattr(self, snapshot_attr)
            self.restore_from_context(context)
            delattr(self, snapshot_attr)
            return True
        return False

    # -------------------------------------------------------------------------
    # P0: 批量变更与验证 (Batch Operations)
    # -------------------------------------------------------------------------

    def batch_update_requirements(self, updates: Dict[str, Dict[str, Any]],
                                  validate: bool = True) -> Dict[str, Any]:
        """批量更新多个需求

        Args:
            updates: {req_id: {field: new_value}}
            validate: 是否执行验证

        Returns:
            执行摘要: {success: bool, applied: list, failed: list, errors: list}
        """
        tx_id = self.transaction_begin()
        applied = []
        failed = []
        errors = []

        try:
            for req_id, fields in updates.items():
                if req_id not in self.requirements:
                    failed.append(req_id)
                    errors.append(f"需求 {req_id} 不存在")
                    continue

                # 对每个字段应用变更
                for field_name, new_value in fields.items():
                    old_value = getattr(self.requirements[req_id], field_name, None)
                    if old_value == new_value:
                        continue  # 值未变，跳过

                    # 直接应用变更（简化版，不经过完整 delta 流程）
                    if field_name == 'status' and isinstance(new_value, str):
                        new_value = SpecStatus(new_value)
                    setattr(self.requirements[req_id], field_name, new_value)
                    self.requirements[req_id].updated_at = datetime.now()

                if req_id not in failed:
                    applied.append(req_id)

            # 全部成功后提交
            if not failed:
                self.transaction_commit(tx_id, f"批量更新 {len(applied)} 个需求")
            else:
                self.transaction_rollback(tx_id)

        except Exception as e:
            self.transaction_rollback(tx_id)
            errors.append(str(e))
            return {
                "success": False,
                "applied": [],
                "failed": list(updates.keys()),
                "errors": errors
            }

        return {
            "success": len(failed) == 0,
            "applied": applied,
            "failed": failed,
            "errors": errors
        }

    # -------------------------------------------------------------------------
    # P0 整合功能: 统一工件图管理 (ArtifactGraph Integration)
    # -------------------------------------------------------------------------

    def init_artifact_graph(self, scan_on_init: bool = True) -> int:
        """初始化工件图并扫描工作区

        Args:
            scan_on_init: 是否立即扫描所有工件

        Returns:
            发现的工件总数
        """
        from .artifact_graph import ArtifactGraph, ArtifactNode, ArtifactType, DependencyType

        self._artifact_graph = ArtifactGraph()

        # 将已有的需求节点加入工件图
        for req_id, req in self.requirements.items():
            node = ArtifactNode(
                id=f"req:{req_id}",
                type=ArtifactType.REQUIREMENT,
                name=req.title,
                description=req.description
            )
            self._artifact_graph.add_node(node)

        if scan_on_init:
            self._artifact_graph.discover_from_directory(self.workspace)

            # 建立需求 -> 代码/测试 关联
            for req_id, req in self.requirements.items():
                for art in req.artifacts:
                    try:
                        self._artifact_graph.add_dependency(
                            from_id=art.artifact_id,
                            to_id=f"req:{req_id}",
                            dep_type=DependencyType.IMPLEMENTS,
                            metadata={
                                "confidence": art.confidence,
                                "evidence": art.evidence[:3]
                            }
                        )
                    except:
                        pass  # 节点可能不存在，忽略错误

        return len(self._artifact_graph._nodes)

    def get_artifact_graph(self):
        """获取工件图实例（懒加载）"""
        if not hasattr(self, '_artifact_graph') or self._artifact_graph is None:
            self.init_artifact_graph(scan_on_init=False)
        return self._artifact_graph

    def find_affected_artifacts_by_requirement(self, req_id: str) -> List[Dict[str, str]]:
        """查找受需求变更影响的所有工件

        Args:
            req_id: 需求ID (如 REQ-001)

        Returns:
            受影响的工件列表，每个包含 id, type, path, name
        """
        graph = self.get_artifact_graph()
        affected = graph.get_affected_artifacts(f"req:{req_id}")

        results = []
        for node in affected:
            results.append({
                "id": node.id,
                "type": node.type.value if hasattr(node.type, 'value') else str(node.type),
                "path": str(node.path) if node.path else None,
                "name": node.name
            })
        return results

    def find_test_files_for_requirement(self, req_id: str) -> List[Path]:
        """查找实现了指定需求的测试文件

        Args:
            req_id: 需求ID

        Returns:
            测试文件路径列表
        """
        affected = self.find_affected_artifacts_by_requirement(req_id)
        test_files = []
        for art in affected:
            if art['type'] == 'test' and art['path']:
                test_files.append(Path(art['path']))
        return test_files

    def get_original_content(self, file_path: str) -> Optional[str]:
        """获取文件的原始内容（基线版本）

        用于 DeltaSpec 增量变更检测。优先从快照获取，其次从文件系统读取。

        Args:
            file_path: 文件路径（相对或绝对）

        Returns:
            原始内容，不存在则返回 None
        """
        path = Path(file_path)
        abs_path = path if path.is_absolute() else self.workspace / path

        # 尝试从快照中获取基线版本
        if hasattr(self, '_state_manager'):
            try:
                baseline = self._state_manager.get_file_baseline(str(abs_path))
                if baseline:
                    return baseline
            except:
                pass

        # 降级：如果文件存在，返回当前内容作为基线
        if abs_path.exists():
            try:
                return abs_path.read_text(encoding='utf-8')
            except:
                pass

        return None

    def find_test_files_for_requirement(self, req_id: str) -> List[str]:
        """查找对应需求的所有测试文件

        Args:
            req_id: 需求ID

        Returns:
            测试文件路径列表
        """
        graph = self.get_artifact_graph()
        affected = graph.get_affected_artifacts(f"req:{req_id}")

        test_files = []
        for node in affected:
            if str(node.id).startswith("file:") and "test" in str(node.id).lower():
                test_files.append(str(node.path) if node.path else str(node.id).replace("file:", ""))

        return test_files

    # -------------------------------------------------------------------------
    # P1 整合功能: Delta 模式文件写入 (用于 FileWriter)
    # -------------------------------------------------------------------------

    def write_file_with_delta(self, file_path: Union[str, Path], new_content: str,
                              reason: str = "", dry_run: bool = False) -> Dict[str, Any]:
        """使用 Delta 模式写入文件，记录增量变更

        Args:
            file_path: 目标文件路径
            new_content: 新文件内容
            reason: 变更原因
            dry_run: 是否只预览不实际写入

        Returns:
            变更结果字典，包含:
            - success: 是否成功
            - applied: 实际应用的 Deltas
            - conflicts: 冲突列表
            - diff_preview: 差异预览
            - original_content: 原内容
            - new_content: 新内容
        """
        from .delta_spec import DeltaSpec

        file_path = Path(file_path)
        delta_spec = DeltaSpec(file_path)
        delta_spec.load_original()

        # 自动生成 Delta 列表
        deltas = delta_spec.create_delta_from_diff(new_content, reason)

        # 执行 Dry-Run 预览
        result = delta_spec.apply(validate=True)

        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "delta_count": len(deltas),
                "applied": [d.__dict__ for d in result.applied_deltas],
                "conflicts": result.conflicts,
                "diff_preview": result.diff_preview,
                "original_content": delta_spec._original_content,
                "new_content": new_content
            }

        if not result.success:
            return {
                "success": False,
                "delta_count": len(deltas),
                "applied": [],
                "conflicts": result.conflicts,
                "diff_preview": result.diff_preview,
                "reason": "Delta 应用存在冲突"
            }

        # 实际写入
        file_path.write_text(result.new_content, encoding='utf-8')

        # 保存 Delta 记录
        delta_record_path = self.workspace / ".spec" / "deltas" / f"{file_path.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            delta_data = {
                "target_file": str(file_path),
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
                "deltas": delta_spec.to_dict()
            }
            delta_record_path.parent.mkdir(parents=True, exist_ok=True)
            delta_record_path.write_text(json.dumps(delta_data, ensure_ascii=False, indent=2), encoding='utf-8')
        except:
            pass

        return {
            "success": True,
            "dry_run": False,
            "delta_count": len(deltas),
            "applied": [d.__dict__ for d in result.applied_deltas],
            "conflicts": result.conflicts,
            "diff_preview": result.diff_preview,
            "delta_record": str(delta_record_path) if 'delta_data' in locals() else None
        }

    # -------------------------------------------------------------------------
    # P1 整合功能: 测试失败智能修复引导
    # -------------------------------------------------------------------------

    def analyze_test_failure_for_fix(self, test_file: str, error_info: str,
                                     source_file: Optional[str] = None) -> Dict[str, Any]:
        """分析测试失败并给出修复建议

        Args:
            test_file: 失败的测试文件路径
            error_info: 错误信息（编译错误、测试失败详情等）
            source_file: 对应的源代码文件（可选）

        Returns:
            修复分析结果，包含:
            - related_requirements: 关联的需求列表
            - affected_files: 受影响的文件列表
            - suggested_fix_hint: 修复建议提示
            - priority: 修复优先级
            - confidence: 建议可信度 (0-1)
        """
        graph = self.get_artifact_graph()

        # 查找测试文件关联的工件
        test_artifact_id = None
        for node_id in graph._nodes.keys():
            if node_id.startswith("file:") and test_file in node_id:
                test_artifact_id = node_id
                break

        # 查找测试 -> 代码 -> 需求 的依赖链
        related_requirements = []
        affected_files = []

        if test_artifact_id:
            # 获取测试文件依赖的所有代码文件
            deps = graph.get_dependencies(test_artifact_id)
            for dep_node, dep_type in deps:
                affected_files.append(dep_node.file_path or dep_node.id)

            # 向上追溯需求
            for node in graph._nodes.values():
                if node.id.startswith("req:"):
                    # 检查是否有代码文件关联到此需求
                    for code_file in affected_files:
                        if code_file and str(code_file) in str(node.path or ""):
                            related_requirements.append(node.id.replace("req:", ""))

        # 如果找不到，尝试通过文件名匹配
        if not related_requirements:
            for req_id in self.requirements.keys():
                req_num = req_id.split('-')[-1] if '-' in req_id else req_id
                if req_num in test_file or str(req_num) in test_file:
                    related_requirements.append(req_id)

        # 根据错误信息生成修复建议
        error_lower = error_info.lower()
        suggested_fix_hint = []
        confidence = 0.3

        if any(key in error_lower for key in ['type', '类型', 'return', '返回', 'std::string']):
            suggested_fix_hint.append("返回值类型不匹配，请检查函数返回类型")
            confidence = 0.8

        if any(key in error_lower for key in ['syntax', '语法', 'parse', 'error:', 'expected']):
            suggested_fix_hint.append("可能存在语法错误，请检查括号、分号、引号等")
            confidence = 0.7

        if any(key in error_lower for key in ['assert', '断言', 'fail', 'expected']):
            suggested_fix_hint.append("测试断言失败，请检查业务逻辑实现")
            confidence = 0.6

        if any(key in error_lower for key in ['compile', 'build', '编译', 'undefined', '未定义']):
            suggested_fix_hint.append("编译错误，可能缺少头文件或符号定义")
            confidence = 0.75

        if any(key in error_lower for key in ['null', 'none', '空指针', 'segmentation']):
            suggested_fix_hint.append("空指针或越界访问，请检查边界条件")
            confidence = 0.85

        if not suggested_fix_hint:
            suggested_fix_hint.append("建议检查源代码文件，对比预期实现和验收标准")

        # 优先级判断
        priority = "high" if confidence >= 0.7 else ("medium" if confidence >= 0.5 else "low")

        return {
            "related_requirements": list(set(related_requirements)),
            "affected_files": list(set(affected_files)),
            "suggested_fix_hint": suggested_fix_hint,
            "priority": priority,
            "confidence": confidence,
            "error_analysis": {
                "has_type_error": any(k in error_lower for k in ['type', '类型', 'return', 'std::string']),
                "has_syntax_error": any(k in error_lower for k in ['syntax', '语法', 'parse']),
                "has_assertion_error": any(k in error_lower for k in ['assert', '断言', 'fail']),
                "has_compile_error": any(k in error_lower for k in ['compile', 'build', '编译', 'undefined'])
            }
        }


# -----------------------------------------------------------------------------
# P0 整合功能: 统一上下文对象
# -----------------------------------------------------------------------------

@dataclass(frozen=True)  # 不可变对象，确保状态快照一致性
class SpecContext:
    """规范上下文快照 - 状态机的不可变状态

    用于:
    1. 状态回滚
    2. 工作流之间传递状态
    3. 审计和调试
    """
    requirements: Dict[str, SpecRequirement]
    snapshots: List[SpecSnapshot]
    workspace: Path
    validation_engine: Optional[Any] = None
    artifact_graph: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """创建时进行深拷贝，确保上下文独立于原始数据"""
        import copy
        # 深拷贝 requirements，防止外部修改影响上下文
        object.__setattr__(self, 'requirements', copy.deepcopy(self.requirements))
        # 深拷贝 snapshots 列表
        object.__setattr__(self, 'snapshots', copy.deepcopy(self.snapshots))
        # 深拷贝 metadata
        object.__setattr__(self, 'metadata', copy.deepcopy(self.metadata))

    def summary(self) -> Dict[str, Any]:
        """获取上下文摘要信息"""
        status_counts = {}
        for spec in self.requirements.values():
            status = spec.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_requirements": len(self.requirements),
            "status_distribution": status_counts,
            "snapshots_count": len(self.snapshots),
            "workspace": str(self.workspace),
            "has_validation": self.validation_engine is not None,
            "has_artifact_graph": self.artifact_graph is not None,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }

    def to_dict(self) -> Dict[str, Any]:
        """序列化上下文"""
        return {
            "requirements": {
                req_id: req.to_dict()
                for req_id, req in self.requirements.items()
            },
            "snapshots": [
                {
                    "snapshot_id": s.snapshot_id,
                    "name": s.name,
                    "description": s.description,
                    "content_hash": s.content_hash(),
                    "created_at": s.created_at.isoformat(),
                    "requirements": {rid: req.to_dict() for rid, req in s.requirements.items()},
                    "metadata": s.metadata
                }
                for s in self.snapshots
            ],
            "workspace": str(self.workspace),
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpecContext':
        """从字典反序列化上下文"""
        requirements = {}
        for req_id, req_data in data["requirements"].items():
            requirements[req_id] = SpecRequirement.from_dict(req_data)

        snapshots = []
        for s in data["snapshots"]:
            # 解析 requirements 字段
            reqs = {}
            for rid, req_data in s.get("requirements", {}).items():
                reqs[rid] = SpecRequirement.from_dict(req_data)
            snapshots.append(SpecSnapshot(
                snapshot_id=s["snapshot_id"],
                name=s["name"],
                description=s.get("description", ""),
                requirements=reqs,
                created_at=datetime.fromisoformat(s["created_at"]),
                metadata=s.get("metadata", {})
            ))

        return cls(
            requirements=requirements,
            snapshots=snapshots,
            workspace=Path(data["workspace"]),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"])
        )


class SpecStateManager:
    """SpecEngine 状态管理器

    功能:
    1. 状态快照与恢复
    2. 分支管理（轻量级）
    3. 变更历史追踪
    4. 状态比较
    """

    def __init__(self, spec_dir: Union[str, Path]):
        self.spec_dir = Path(spec_dir)
        self.spec_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.spec_dir / "spec_state.json"
        self.snapshots_dir = self.spec_dir / "snapshots"
        self.snapshots_dir.mkdir(exist_ok=True)
        self.current_branch = "main"
        self.branches: Dict[str, str] = {}  # branch name -> latest snapshot id

    def create_snapshot(self, context: SpecContext, message: str = "") -> str:
        """创建状态快照

        Returns:
            snapshot_id: 快照 ID
        """
        snapshot_id = hashlib.md5(f"{datetime.now().isoformat()}{message}".encode()).hexdigest()[:16]

        # 保存完整快照
        snapshot_data = context.to_dict()
        snapshot_data["snapshot_id"] = snapshot_id
        snapshot_data["message"] = message
        snapshot_data["branch"] = self.current_branch

        snapshot_file = self.snapshots_dir / f"{snapshot_id}.json"
        snapshot_file.write_text(json.dumps(snapshot_data, indent=2, ensure_ascii=False), encoding='utf-8')

        # 更新当前状态
        self._update_state_ref(snapshot_id)

        return snapshot_id

    def restore_snapshot(self, snapshot_id: str) -> Optional[SpecContext]:
        """从快照恢复状态

        Args:
            snapshot_id: 快照 ID 或特殊标识符 ("latest", "previous")

        Returns:
            恢复的上下文，失败返回 None
        """
        if snapshot_id == "latest":
            snapshot_id = self._get_latest_snapshot_id()
        elif snapshot_id == "previous":
            snapshot_id = self._get_previous_snapshot_id()

        if not snapshot_id:
            return None

        snapshot_file = self.snapshots_dir / f"{snapshot_id}.json"
        if not snapshot_file.exists():
            return None

        data = json.loads(snapshot_file.read_text(encoding='utf-8'))
        return SpecContext.from_dict(data)

    def list_snapshots(self, branch: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """列出所有快照"""
        snapshots = []
        for f in self.snapshots_dir.glob("*.json"):
            data = json.loads(f.read_text(encoding='utf-8'))
            if branch is None or data.get("branch") == branch:
                snapshots.append({
                    "id": data["snapshot_id"],
                    "message": data.get("message", ""),
                    "created_at": data["created_at"],
                    "branch": data.get("branch", "main"),
                    "req_count": len(data.get("requirements", {})),
                    "file": f.name
                })

        return sorted(snapshots, key=lambda x: x["created_at"], reverse=True)[:limit]

    def compare_snapshots(self, snapshot_id1: str, snapshot_id2: str) -> Dict[str, Any]:
        """比较两个快照的差异"""
        ctx1 = self.restore_snapshot(snapshot_id1)
        ctx2 = self.restore_snapshot(snapshot_id2)

        if not ctx1 or not ctx2:
            return {"error": "Snapshot not found"}

        reqs1 = set(ctx1.requirements.keys())
        reqs2 = set(ctx2.requirements.keys())

        changed_reqs = []
        for req_id in reqs1 & reqs2:
            r1 = ctx1.requirements[req_id]
            r2 = ctx2.requirements[req_id]
            if r1.to_dict() != r2.to_dict():
                changed_reqs.append(req_id)

        return {
            "requirements": {
                "added": list(reqs2 - reqs1),
                "removed": list(reqs1 - reqs2),
                "changed": changed_reqs,
                "count_before": len(reqs1),
                "count_after": len(reqs2)
            },
            "snapshots": {
                "count_before": len(ctx1.snapshots),
                "count_after": len(ctx2.snapshots)
            },
            "metadata_diff": self._dict_diff(ctx1.metadata, ctx2.metadata)
        }

    def create_branch(self, branch_name: str, from_snapshot: Optional[str] = None) -> bool:
        """创建分支

        Args:
            branch_name: 分支名称
            from_snapshot: 从哪个快照创建分支，None 表示当前状态

        Returns:
            是否成功
        """
        if from_snapshot is None:
            from_snapshot = self._get_latest_snapshot_id()

        if not from_snapshot:
            return False

        self.branches[branch_name] = from_snapshot
        return True

    def switch_branch(self, branch_name: str) -> bool:
        """切换分支"""
        if branch_name not in self.branches and branch_name != "main":
            return False
        self.current_branch = branch_name
        return True

    def _update_state_ref(self, snapshot_id: str):
        """更新最新状态引用"""
        state = {
            "latest_snapshot": snapshot_id,
            "current_branch": self.current_branch,
            "branches": self.branches,
            "updated_at": datetime.now().isoformat()
        }
        self.state_file.write_text(json.dumps(state, indent=2), encoding='utf-8')

    def _get_latest_snapshot_id(self) -> Optional[str]:
        """获取最新的快照 ID"""
        if not self.state_file.exists():
            # 从文件系统找最新的
            snapshots = list(self.snapshots_dir.glob("*.json"))
            if snapshots:
                latest = max(snapshots, key=lambda x: x.stat().st_mtime)
                return latest.stem
            return None

        state = json.loads(self.state_file.read_text(encoding='utf-8'))
        return state.get("latest_snapshot")

    def _get_previous_snapshot_id(self) -> Optional[str]:
        """获取上一个快照 ID"""
        snapshots = self.list_snapshots(limit=2)
        if len(snapshots) >= 2:
            return snapshots[1]["id"]
        return None

    @staticmethod
    def _dict_diff(d1: Dict, d2: Dict) -> Dict[str, Any]:
        """比较两个字典的差异"""
        keys1 = set(d1.keys())
        keys2 = set(d2.keys())

        return {
            "added": {k: d2[k] for k in keys2 - keys1},
            "removed": {k: d1[k] for k in keys1 - keys2},
            "changed": {k: (d1[k], d2[k]) for k in keys1 & keys2 if d1[k] != d2[k]}
        }
