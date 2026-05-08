# -*- coding: utf-8 -*-
"""
Spec-First 规范优先工具 - Phase 1 实现

提供规范驱动开发的核心能力：
- 需求文档解析为 Spec 对象
- Delta 变更规划与影响分析
- 变更验证与预览
- 代码应用
"""
from typing import Dict, Any, Optional, List
from pathlib import Path
from pydantic import BaseModel, Field
from .base import BaseTool, ToolResult


class SpecTool(BaseTool):
    """Spec-First 规范优先开发工具"""

    name = "spec_tool"
    description = "规范驱动开发工具：解析需求文档→规划Delta变更→验证→应用到代码"

    class Parameters(BaseModel):
        action: str = Field(description="执行操作: parse|plan|dry_run|apply|analyze|workflow")
        req_doc_path: Optional[str] = Field(default=None, description="需求文档路径")
        spec_id: Optional[str] = Field(default=None, description="目标规范 ID")
        changes: Optional[Dict[str, Any]] = Field(default=None, description="变更内容字典")
        delta: Optional[Dict[str, Any]] = Field(default=None, description="Delta 对象数据")
        reason: str = Field(default="", description="变更原因说明")
        auto_apply: bool = Field(default=False, description="是否自动应用到代码")
        output_format: str = Field(default="json", description="输出格式: json|markdown|summary")

    def _execute(self, params: Parameters) -> ToolResult:
        try:
            from devpal.core.schema.spec import SpecEngine
            engine = SpecEngine()

            if params.action == "parse":
                return self._parse_requirement(engine, params)
            elif params.action == "plan":
                return self._plan_delta(engine, params)
            elif params.action == "dry_run":
                return self._dry_run_delta(engine, params)
            elif params.action == "apply":
                return self._apply_delta(engine, params)
            elif params.action == "analyze":
                return self._analyze_traceability(engine, params)
            elif params.action == "workflow":
                return self._run_spec_first_workflow(engine, params)
            else:
                return ToolResult.error(f"未知操作: {params.action}")

        except ImportError as e:
            return ToolResult.error(f"SpecEngine 加载失败: {str(e)}")
        except Exception as e:
            return ToolResult.error(f"操作失败: {str(e)}")

    def _parse_requirement(self, engine, params) -> ToolResult:
        """解析需求文档为 Spec 对象"""
        if not params.req_doc_path:
            return ToolResult.error("需要提供 req_doc_path 参数")

        specs = engine.parse_requirement_doc(params.req_doc_path)

        if params.output_format == "summary":
            content = [
                f"✅ 成功解析需求文档: {params.req_doc_path}",
                f"   共提取 {len(specs)} 个规范项:",
                ""
            ]
            for spec in specs:
                content.extend([
                    f"  {spec.id}: {spec.title}",
                    f"    状态: {spec.status.value} | 优先级: {spec.priority}",
                    f"    验收标准: {len(spec.acceptance_criteria)} 项",
                    f"    关联工件: {len(spec.artifacts)} 个",
                    ""
                ])
            return ToolResult.ok("\n".join(content), metadata={
                'spec_count': len(specs),
                'specs': [s.to_dict() for s in specs]
            })
        else:
            return ToolResult.ok(
                f"成功解析 {len(specs)} 个规范项",
                metadata={'specs': [s.to_dict() for s in specs]}
            )

    def _plan_delta(self, engine, params) -> ToolResult:
        """规划 Delta 变更"""
        if not params.spec_id or not params.changes:
            return ToolResult.error("需要提供 spec_id 和 changes 参数")

        deltas = engine.plan_delta(params.spec_id, params.changes, params.reason)

        if params.output_format == "summary":
            content = [
                f"✅ 变更规划完成 - 规范: {params.spec_id}",
                f"   生成 {len(deltas)} 个 Delta 变更:",
                ""
            ]
            for d in deltas:
                content.extend([
                    f"  {d.delta_id}: {d.delta_type.value} {d.field_name or '(整体)'}",
                    f"    原因: {d.reason}",
                    f"    影响: {len(d.affected_artifacts)} 个工件, {len(d.affected_requirements)} 个关联需求",
                    ""
                ])
            return ToolResult.ok("\n".join(content), metadata={
                'delta_count': len(deltas),
                'deltas': [d.to_dict() for d in deltas]
            })
        else:
            return ToolResult.ok(
                f"生成 {len(deltas)} 个 Delta 变更",
                metadata={'deltas': [d.to_dict() for d in deltas]}
            )

    def _dry_run_delta(self, engine, params) -> ToolResult:
        """Delta 变更预演"""
        if not params.delta:
            return ToolResult.error("需要提供 delta 参数")

        from devpal.core.schema.spec import SpecDelta
        delta_obj = SpecDelta.from_dict(params.delta)

        success, warnings, new_spec = engine.dry_run_delta(delta_obj)

        content = [
            f"{'✅' if success else '⚠️'} Delta 预演结果: {delta_obj.delta_id}",
            f"   状态: {'通过' if success else '存在问题'}",
            ""
        ]

        if warnings:
            content.append("   警告/风险:")
            for w in warnings:
                content.append(f"    - {w}")
            content.append("")

        if new_spec:
            # Handle both enum and string status
            status_value = new_spec.status.value if hasattr(new_spec.status, 'value') else new_spec.status
            content.extend([
                "   变更后的规范:",
                f"    ID: {new_spec.id}",
                f"    标题: {new_spec.title}",
                f"    状态: {status_value}",
                f"    实现进度: {new_spec.implementation_progress:.0%}",
            ])

        return ToolResult.ok("\n".join(content), metadata={
            'success': success,
            'warnings': warnings,
            'new_spec': new_spec.to_dict() if new_spec else None
        })

    def _apply_delta(self, engine, params) -> ToolResult:
        """应用 Delta 变更到代码"""
        if not params.delta:
            return ToolResult.error("需要提供 delta 参数")

        from devpal.core.schema.spec import SpecDelta
        delta_obj = SpecDelta.from_dict(params.delta)

        result = engine.apply_delta(delta_obj, validate=True)

        if result:
            return ToolResult.ok(
                f"✅ Delta 应用成功: {delta_obj.delta_id}",
                metadata={'applied': True}
            )
        else:
            return ToolResult.error(f"❌ Delta 应用失败: {delta_obj.delta_id}")

    def _analyze_traceability(self, engine, params) -> ToolResult:
        """分析可追踪性"""
        if not params.req_doc_path:
            return ToolResult.error("需要提供 req_doc_path 参数")

        specs = engine.parse_requirement_doc(params.req_doc_path)

        content = [
            "📊 可追踪性分析报告",
            f"   需求文档: {params.req_doc_path}",
            f"   规范项总数: {len(specs)}",
            ""
        ]

        implemented_count = sum(1 for s in specs if s.implementation_progress > 0)
        tested_count = sum(1 for s in specs if s.test_coverage > 0)
        linked_count = sum(1 for s in specs if len(s.artifacts) > 0)

        content.extend([
            "   覆盖统计:",
            f"    已实现: {implemented_count}/{len(specs)}",
            f"    已测试: {tested_count}/{len(specs)}",
            f"    有关联工件: {linked_count}/{len(specs)}",
            ""
        ])

        content.append("   详细追踪:")
        for spec in specs:
            status_icon = "✅" if spec.implementation_progress >= 1.0 else \
                         "🔄" if spec.implementation_progress > 0 else "📋"
            content.extend([
                f"    {status_icon} {spec.id}: {spec.title}",
                f"       实现: {spec.implementation_progress:.0%} | 测试: {spec.test_coverage:.0%}",
                f"       关联工件: {len(spec.artifacts)} 个"
            ])
            if spec.artifacts:
                for art in spec.artifacts:
                    content.append(f"         → {art.file_path} ({art.artifact_type})")
            content.append("")

        return ToolResult.ok("\n".join(content), metadata={
            'total': len(specs),
            'implemented': implemented_count,
            'tested': tested_count,
            'linked': linked_count,
        })

    def _run_spec_first_workflow(self, engine, params) -> ToolResult:
        """运行完整的 Spec-First 工作流"""
        if not params.req_doc_path:
            return ToolResult.error("需要提供 req_doc_path 参数")

        result = engine.spec_first_workflow(
            params.req_doc_path,
            update_message=params.reason
        )

        content = [
            "🔄 Spec-First 工作流执行报告",
            f"   输入文档: {params.req_doc_path}",
            "",
            f"   解析阶段: {'✅' if result.get('parse_success') else '❌'}",
            f"     提取规范: {result.get('spec_count', 0)} 项",
            "",
            f"   规划阶段: {'✅' if result.get('plan_success') else '❌'}",
            f"     Delta 变更: {len(result.get('deltas', []))} 个",
            "",
            f"   验证阶段: {'✅' if result.get('validate_success') else '❌'}",
            f"     验证问题: {len(result.get('validation_issues', []))} 个",
            ""
        ]

        if result.get('validation_issues'):
            content.append("   验证问题:")
            for issue in result['validation_issues']:
                content.append(f"    - {issue}")
            content.append("")

        if params.auto_apply and result.get('apply_success'):
            content.append(f"   应用阶段: ✅")
            content.append(f"     已应用到代码")
        else:
            content.append(f"   应用阶段: ⏸️ (需要手动确认)")

        content.extend([
            "",
            f"   整体状态: {'✅ 完成' if result.get('success') else '⚠️ 部分完成'}"
        ])

        return ToolResult.ok("\n".join(content), metadata=result)
