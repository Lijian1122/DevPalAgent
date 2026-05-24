# -*- coding: utf-8 -*-
"""
OpenSpec 统一上下文管理器 - Phase 4: 闭环集成

核心入口类：OpenSpecContext
  - 作为所有 OpenSpec 组件的统一入口
  - 管理组件生命周期
  - 提供事件总线作为通信枢纽
  - 提供统一的配置和状态管理

架构：
    OpenSpecContext
         │
         ├─ event_bus (EventBus)          ← 所有组件通信枢纽
         ├─ spec_engine (SpecEngine)       ← 规范引擎
         ├─ artifact_graph (ArtifactGraph) ← 工件依赖图
         ├─ validation_engine (ValidationEngine) ← 四层验证
         ├─ workflow_engine (WorkflowEngine) ← 工作流执行
         └─ spec_state (SpecStateManager)  ← 状态快照管理

数据流：
    用户输入 → 上下文解析需求 → ArtifactGraph分析影响 →
    Workflow执行 → DeltaSpec应用变更 → EventBus发布事件 →
    所有组件响应 → 状态自动更新
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from devpal.core.schema import (
    ArtifactGraph,
    EventBus,
    EventBusAdapter,
    SpecContext,
    SpecEngine,
    ValidationEngine,
    WorkflowEngine,
)
from devpal.core.schema.spec import SpecStateManager


@dataclass
class OpenSpecConfig:
    """OpenSpec 配置"""

    workspace: Path
    spec_dir: Optional[Path] = None
    enable_event_bus: bool = True
    enable_artifact_graph: bool = True
    enable_validation: bool = True
    enable_workflow: bool = True
    auto_discover_artifacts: bool = True
    auto_publish_events: bool = True
    event_store_path: Optional[Path] = None


class OpenSpecContext:
    """OpenSpec 统一上下文 - Phase 4 核心架构

    这是所有 OpenSpec 组件的统一入口和生命周期管理器。
    所有组件通过 EventBus 通信，状态自动同步。

    使用方式：
        # 创建上下文
        ctx = OpenSpecContext.create("./my_project")

        # 访问组件
        ctx.spec_engine.add_requirement(...)
        ctx.artifact_graph.discover_from_directory(...)
        ctx.workflow_engine.execute_workflow(...)

        # 订阅事件
        ctx.subscribe("file_changed", lambda e: print(f"文件变更: {e.file_path}"))

        # 状态管理
        snapshot_id = ctx.create_snapshot("变更前状态")
        ctx.restore_snapshot(snapshot_id)

        # 获取上下文摘要
        summary = ctx.summary()
    """

    def __init__(self, config: OpenSpecConfig):
        self.config = config
        self.workspace = config.workspace
        self.spec_dir = config.spec_dir or self.workspace / ".spec"

        # 状态
        self._initialized = False
        self._metadata: Dict[str, Any] = {}

        # 核心组件（延迟初始化）
        self._event_bus: Optional[EventBus] = None
        self._event_adapter: Optional[EventBusAdapter] = None
        self._artifact_graph: Optional[ArtifactGraph] = None
        self._spec_engine: Optional[SpecEngine] = None
        self._validation_engine: Optional[ValidationEngine] = None
        self._workflow_engine: Optional[WorkflowEngine] = None
        self._spec_state_manager: Optional[SpecStateManager] = None

    @classmethod
    def create(
        cls,
        workspace: Union[str, Path],
        spec_dir: Optional[Union[str, Path]] = None,
        enable_event_bus: bool = True,
        auto_initialize: bool = True,
    ) -> "OpenSpecContext":
        """创建 OpenSpec 上下文

        Args:
            workspace: 工作目录
            spec_dir: 规范存储目录，默认 {workspace}/.spec
            enable_event_bus: 是否启用事件总线
            auto_initialize: 是否自动初始化所有组件

        Returns:
            初始化后的上下文对象
        """
        config = OpenSpecConfig(
            workspace=Path(workspace),
            spec_dir=Path(spec_dir) if spec_dir else None,
            enable_event_bus=enable_event_bus,
        )

        ctx = cls(config)

        if auto_initialize:
            ctx.initialize()

        return ctx

    # -------------------------------------------------------------------------
    # 初始化与生命周期
    # -------------------------------------------------------------------------

    def initialize(self):
        """初始化所有 OpenSpec 组件

        初始化顺序很重要：
        1. EventBus (所有组件通信基础)
        2. SpecStateManager (状态管理基础)
        3. SpecEngine (规范管理)
        4. ArtifactGraph (工件依赖图)
        5. ValidationEngine (验证引擎)
        6. WorkflowEngine (工作流引擎)
        """
        if self._initialized:
            return

        # 1. EventBus - 所有组件的通信枢纽
        if self.config.enable_event_bus:
            event_store = self.config.event_store_path or self.spec_dir / "events.jsonl"
            self._event_bus = EventBus(event_store_path=event_store)
            self._event_adapter = EventBusAdapter(self._event_bus, "OpenSpecContext")

            from devpal.core.schema import set_global_event_bus

            set_global_event_bus(self._event_bus)

        # 2. SpecStateManager
        self._spec_state_manager = SpecStateManager(self.spec_dir)

        # 3. SpecEngine
        self._spec_engine = SpecEngine(self.spec_dir)

        # 4. ArtifactGraph
        if self.config.enable_artifact_graph:
            self._artifact_graph = ArtifactGraph()
            if self.config.auto_discover_artifacts:
                self._artifact_graph.discover_from_directory(self.workspace)

        # 5. ValidationEngine
        if self.config.enable_validation:
            self._validation_engine = ValidationEngine()

        # 6. WorkflowEngine
        if self.config.enable_workflow:
            self._workflow_engine = WorkflowEngine(
                tool_registry=None,  # 延迟设置
                spec_engine=self._spec_engine,
            )

        self._initialized = True

        if self._event_adapter and self.config.auto_publish_events:
            self._event_adapter.publish_workflow_completed(
                workflow_name="context_initialization",
                success=True,
                duration=0.0,
                total_steps=1,
                success_steps=1,
                failed_steps=0,
            )

    def close(self):
        """关闭上下文，释放资源"""
        if self._event_bus:
            # 处理所有待处理事件
            self._event_bus.process_queue()

        self._initialized = False

    # -------------------------------------------------------------------------
    # 组件访问属性
    # -------------------------------------------------------------------------

    @property
    def event_bus(self) -> EventBus:
        if not self._event_bus:
            raise RuntimeError("EventBus 未启用或未初始化")
        return self._event_bus

    @property
    def event_adapter(self) -> EventBusAdapter:
        if not self._event_adapter:
            raise RuntimeError("EventBus 未启用或未初始化")
        return self._event_adapter

    @property
    def artifact_graph(self) -> Optional[ArtifactGraph]:
        return self._artifact_graph

    @property
    def spec_engine(self) -> Optional[SpecEngine]:
        return self._spec_engine

    @property
    def validation_engine(self) -> Optional[ValidationEngine]:
        return self._validation_engine

    @property
    def workflow_engine(self) -> Optional[WorkflowEngine]:
        if not self._workflow_engine:
            raise RuntimeError("WorkflowEngine 未启用或未初始化")
        return self._workflow_engine

    @property
    def spec_state_manager(self) -> SpecStateManager:
        if not self._spec_state_manager:
            raise RuntimeError("SpecStateManager 未初始化")
        return self._spec_state_manager

    # -------------------------------------------------------------------------
    # 事件订阅与发布（快捷方法）
    # -------------------------------------------------------------------------

    def subscribe(self, event_type: str, handler: Callable, **kwargs) -> str:
        """订阅事件

        Args:
            event_type: 事件类型，如 "file_changed", "step_executed", "delta_applied"
            handler: 处理函数
            **kwargs: 其他订阅参数

        Returns:
            subscription_id: 订阅 ID
        """
        return self.event_bus.subscribe(event_type, handler, **kwargs)

    def subscribe_all(self, handler: Callable, **kwargs) -> str:
        """订阅所有事件"""
        return self.event_bus.subscribe_all(handler, **kwargs)

    def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅"""
        return self.event_bus.unsubscribe(subscription_id)

    # -------------------------------------------------------------------------
    # 状态管理
    # -------------------------------------------------------------------------

    def create_snapshot(self, message: str = "") -> str:
        """创建当前状态快照

        Args:
            message: 快照说明

        Returns:
            snapshot_id: 快照 ID
        """
        # 构建 SpecContext
        context = SpecContext(
            requirements=self.spec_engine.requirements,
            snapshots=self.spec_engine.snapshots,
            workspace=self.workspace,
            validation_engine=self._validation_engine,
            artifact_graph=self._artifact_graph,
            metadata={
                "snapshot_message": message,
                "created_at": datetime.now().isoformat(),
            },
        )

        snapshot_id = self.spec_state_manager.create_snapshot(context, message)

        if self.config.auto_publish_events:
            self.event_adapter.publish_delta_applied(
                target_file="state_snapshot",
                delta_count=1,
                conflict_count=0,
            )

        return snapshot_id

    def restore_snapshot(self, snapshot_id: str = "latest") -> bool:
        """从快照恢复状态

        Args:
            snapshot_id: 快照 ID 或 "latest", "previous"

        Returns:
            是否恢复成功
        """
        context = self.spec_state_manager.restore_snapshot(snapshot_id)
        if not context:
            return False

        # 恢复 SpecEngine 状态
        self.spec_engine.requirements = dict(context.requirements)
        self.spec_engine.snapshots = list(context.snapshots)

        # TODO: 恢复 ArtifactGraph, ValidationEngine 等状态

        if self.config.auto_publish_events:
            self.event_adapter.publish_workflow_completed(
                workflow_name="snapshot_restore",
                success=True,
                duration=0.0,
                total_steps=1,
                success_steps=1,
                failed_steps=0,
            )

        return True

    def list_snapshots(self, limit: int = 20) -> List[Dict[str, Any]]:
        """列出所有快照"""
        return self.spec_state_manager.list_snapshots(limit=limit)

    # -------------------------------------------------------------------------
    # 快捷操作：需求驱动开发闭环
    # -------------------------------------------------------------------------

    def analyze_change_impact(self, changed_files: List[str]) -> Dict[str, Any]:
        """分析文件变更的影响范围

        这是闭环的核心：变更 → 分析影响 → 智能处理

        Args:
            changed_files: 变更的文件路径列表

        Returns:
            影响分析结果：受影响的需求、测试、代码等
        """
        result = {
            "changed_files": changed_files,
            "affected_requirements": [],
            "affected_tests": [],
            "affected_code": [],
            "recommendations": [],
            "impact_score": 0.0,
        }

        # 通过 ArtifactGraph 分析每个变更文件的影响
        for file_path in changed_files:
            # 查找文件关联的需求
            for req_id, req in self.spec_engine.requirements.items():
                for artifact in req.artifacts:
                    if artifact.file_path == file_path or file_path in str(
                        artifact.file_path
                    ):
                        result["affected_requirements"].append(
                            {
                                "req_id": req_id,
                                "title": req.title,
                                "artifact_id": artifact.artifact_id,
                            }
                        )

            # 查找受影响的测试（测试依赖于变更文件）
            # （简化实现）
            for test_file in self.workspace.rglob("test_*"):
                if test_file.suffix in (".py", ".cpp", ".h"):
                    content = test_file.read_text(encoding="utf-8", errors="ignore")
                    if Path(file_path).stem in content:
                        result["affected_tests"].append(str(test_file))

        # 计算影响分数
        total_affected = len(result["affected_requirements"]) + len(
            result["affected_tests"]
        )
        result["impact_score"] = min(1.0, total_affected / 10.0)

        # 生成建议
        if result["impact_score"] > 0.5:
            result["recommendations"].append("高影响变更，建议运行完整回归测试")
        elif result["impact_score"] > 0.2:
            result["recommendations"].append("中等影响，建议运行关联测试")
        else:
            result["recommendations"].append("低影响，可快速验证")

        if result["affected_requirements"]:
            result["recommendations"].append(
                f"需要验证 {len(result['affected_requirements'])} 个需求"
            )

        if self.config.auto_publish_events:
            self.event_adapter.publish_impact_analysis(
                changed_item=",".join(changed_files),
                change_type="code_change",
                affected_artifacts=[str(a) for a in result["affected_requirements"]],
                impact_score=result["impact_score"],
            )

        return result

    def validate_change(
        self, content: str, file_path: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """验证变更（使用 ValidationEngine）

        这是闭环的质量闸门：变更 → 验证 → 通过/拒绝
        """
        validation_result = self.validation_engine.validate_pipeline(
            content,
            context={
                "file_path": file_path,
                "workspace": str(self.workspace),
                **(context or {}),
            },
        )

        return {
            "passed": validation_result.passed,
            "error_count": validation_result.error_count,
            "warning_count": validation_result.warning_count,
            "issues": [
                {
                    "severity": issue.severity.value,
                    "message": issue.message,
                    "location": issue.location,
                    "suggestion": issue.suggestion,
                }
                for issue in validation_result.all_issues
            ],
        }

    # -------------------------------------------------------------------------
    # 上下文摘要与诊断
    # -------------------------------------------------------------------------

    def summary(self) -> Dict[str, Any]:
        """获取当前上下文摘要"""
        req_count = len(self.spec_engine.requirements) if self._spec_engine else 0
        req_by_status = {}
        if self._spec_engine:
            for req in self.spec_engine.requirements.values():
                status = req.status.value
                req_by_status[status] = req_by_status.get(status, 0) + 1

        artifact_count = len(self.artifact_graph._nodes) if self._artifact_graph else 0
        snapshot_count = len(self.list_snapshots(limit=1000))

        event_stats = self._event_bus.get_event_stats() if self._event_bus else {}

        return {
            "workspace": str(self.workspace),
            "spec_dir": str(self.spec_dir),
            "initialized": self._initialized,
            "requirements": {
                "total": req_count,
                "by_status": req_by_status,
            },
            "artifact_graph": {
                "total_nodes": artifact_count,
            },
            "snapshots": {
                "total": snapshot_count,
            },
            "event_bus": event_stats,
            "metadata": self._metadata,
        }

    def health_check(self) -> Dict[str, Any]:
        """健康检查 - 诊断各组件状态"""
        results = {
            "overall_status": "healthy",
            "components": {},
            "warnings": [],
            "errors": [],
        }

        # 检查各组件
        components = [
            ("event_bus", self._event_bus),
            ("spec_engine", self._spec_engine),
            ("artifact_graph", self._artifact_graph),
            ("validation_engine", self._validation_engine),
            ("workflow_engine", self._workflow_engine),
        ]

        for name, component in components:
            status = "enabled" if component else "disabled"
            if component and name == "artifact_graph":
                node_count = len(self.artifact_graph._nodes)
                results["components"][name] = {
                    "status": status,
                    "node_count": node_count,
                }
                if node_count == 0:
                    results["warnings"].append(f"{name}: 没有发现工件")
            else:
                results["components"][name] = {"status": status}

        # 总体状态
        if results["errors"]:
            results["overall_status"] = "error"
        elif results["warnings"]:
            results["overall_status"] = "warning"

        return results
