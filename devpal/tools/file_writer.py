# -*- coding: utf-8 -*-
"""
文件写入工具
"""
from typing import Dict, Any, Optional, List
from pathlib import Path
from pydantic import BaseModel, Field
from .base import BaseTool, ToolResult, ToolSecurity, retry


class FileWriterTool(BaseTool):
    """写入内容到本地文件"""

    name = "file_writer"
    description = "写入内容到本地文件，可以创建新文件、覆盖已有文件、或者追加内容，支持增量 Delta 模式"

    class Parameters(BaseModel):
        path: str = Field(description="文件路径，可以是相对路径或绝对路径")
        content: Optional[str] = Field(default=None, description="完整文件内容（全量模式）")
        append: bool = Field(default=False, description="是否追加模式，False=覆盖，True=追加")
        delta_mode: bool = Field(default=False, description="是否使用 Delta 增量模式")
        deltas: Optional[List[Dict[str, Any]]] = Field(default=None, description="Delta 变更列表，仅在 delta_mode=True 时使用")
        show_diff: bool = Field(default=True, description="是否显示 Diff 预览")
        reason: str = Field(default="", description="变更原因说明")

    @retry(max_retries=2, delay=0.5)
    def _execute(self, params: Parameters) -> ToolResult:
        # 安全检查
        safe, reason = ToolSecurity.check_path_safety(params.path)
        if not safe:
            return ToolResult.error(reason)

        try:
            file_path = Path(params.path)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Delta 增量模式
            if params.delta_mode:
                return self._apply_delta_mode(file_path, params)

            # 普通写入模式
            content = params.content or ""
            mode = "a" if params.append else "w"

            # ============================================================
            # OpenSpec Phase 2: 默认使用 DeltaSpec
            # 如果文件已存在且不是追加模式，使用增量变更方式
            # ============================================================
            if not params.append and file_path.exists() and content:
                # 文件已存在，使用智能 Delta 模式
                return self._auto_delta_write(file_path, content, params)

            # 普通写入（新文件或追加模式）
            with open(params.path, mode, encoding="utf-8") as f:
                f.write(content)

            action = "追加" if params.append else "写入"
            return ToolResult.ok(
                content=f"成功{action}文件: {params.path} ({len(content)} 字符)",
                file_path=params.path,
                chars_written=len(content),
                mode=mode,
                reason=params.reason,
                delta_mode=False
            )

        except Exception as e:
            return ToolResult.error(f"写入文件失败: {str(e)}")

    def _auto_delta_write(self, file_path: Path, new_content: str, params: Parameters) -> ToolResult:
        """智能 Delta 写入 - 自动生成 diff 并应用增量变更

        这是 Phase 2 的核心改进：默认使用 Delta 模式，提供变更预览和冲突检测
        """
        from devpal.core.schema.delta_spec import DeltaSpec

        delta_spec = DeltaSpec(file_path)
        delta_spec.load_original()

        # 自动生成 Delta 列表并添加到 Spec 中
        deltas = delta_spec.create_delta_from_diff(new_content, params.reason)

        if not deltas:
            # 文件内容无变化
            return ToolResult.ok(
                content=f"文件内容无变化: {file_path}",
                file_path=str(file_path),
                delta_mode=True,
                changes=0
            )

        # 将生成的 Delta 添加到 Spec 中
        for delta in deltas:
            delta_spec.add_delta(delta)

        # Dry-Run 预览
        dry_result = delta_spec.apply(dry_run=True)

        if not dry_result.success:
            return ToolResult.error(
                f"Delta 预览失败: {dry_result.conflicts}",
                metadata={'conflicts': dry_result.conflicts}
            )

        # 显示 Diff
        if params.show_diff and dry_result.diff_preview:
            diff_preview = dry_result.diff_preview
        else:
            diff_preview = ""

        # 实际应用
        real_result = delta_spec.apply(validate=True)

        if not real_result.success:
            return ToolResult.error(
                f"Delta 应用失败: {real_result.conflicts}",
                metadata={'conflicts': real_result.conflicts}
            )

        # 写入文件
        file_path.write_text(real_result.new_content, encoding='utf-8')

        # 更新统计（如果有 AgentEngine 上下文）
        try:
            from devpal.core import current_agent
            if hasattr(current_agent, 'stats'):
                current_agent.stats["deltas_applied"] += len(real_result.applied_deltas)
        except (ImportError, AttributeError):
            pass

        # 构建返回消息
        messages = [
            f"[OK] Delta 模式写入成功: {file_path}",
            f"变更数: {len(real_result.applied_deltas)} 个",
        ]
        if params.reason:
            messages.append(f"变更原因: {params.reason}")

        if diff_preview and params.show_diff:
            messages.extend([
                "",
                "变更预览:",
                "```diff",
                diff_preview,
                "```"
            ])

        return ToolResult.ok(
            content="\n".join(messages),
            file_path=str(file_path),
            delta_mode=True,
            deltas_applied=len(real_result.applied_deltas),
            diff=diff_preview,
            reason=params.reason
        )

    def _apply_delta_mode(self, file_path: Path, params: Parameters) -> ToolResult:
        """应用 Delta 增量模式"""
        from devpal.core.schema.delta_spec import DeltaSpec, DeltaHunk, DeltaOperation

        delta_spec = DeltaSpec(file_path)
        delta_spec.load_original()

        if not params.deltas:
            return ToolResult.error("Delta 模式需要提供 deltas 参数")

        applied_count = 0
        for delta_data in params.deltas:
            try:
                operation = DeltaOperation(delta_data['operation'])
                hunk = DeltaHunk(
                    operation=operation,
                    target_path=delta_data.get('target_path', f'file:{file_path}'),
                    old_content=delta_data.get('old_content'),
                    new_content=delta_data.get('new_content'),
                    start_line=delta_data.get('start_line'),
                    end_line=delta_data.get('end_line'),
                    reason=params.reason
                )
                delta_spec.add_delta(hunk)
                applied_count += 1
            except Exception as e:
                return ToolResult.error(f"解析 Delta 失败: {str(e)}")

        result = delta_spec.apply(validate=True)

        if not result.success:
            return ToolResult.error(f"Delta 应用失败: {result.conflicts}")

        # 写入文件
        file_path.write_text(result.new_content, encoding='utf-8')

        messages = [
            f"Delta 写入成功，应用了 {len(result.applied_deltas)} 个变更"
        ]
        if params.show_diff and result.diff_preview:
            messages.extend([
            "",
            "变更预览:",
            "```diff",
            result.diff_preview,
            "```"
        ])

        return ToolResult.ok(
            content="\n".join(messages),
            file_path=params.path,
            deltas_applied=len(result.applied_deltas),
            conflicts=result.conflicts,
            diff=result.diff_preview,
            reason=params.reason
        )

    @classmethod
    def write_with_auto_delta(cls, file_path: str, new_content: str, reason: str = "",
                              dry_run: bool = False, spec_engine: Optional[Any] = None) -> ToolResult:
        """静态方法：自动生成 Delta 并写入（智能增量模式）

        Args:
            file_path: 目标文件路径
            new_content: 新的文件内容
            reason: 变更原因（会被记录到 Delta 历史）
            dry_run: 是否只预览，不实际写入
            spec_engine: SpecEngine 实例（可选），用于统一状态管理

        Returns:
            ToolResult 包含变更详情和 diff
        """
        if spec_engine:
            # 通过 SpecEngine 统一管理（会保留变更历史）
            result = spec_engine.write_file_with_delta(
                file_path, new_content, reason, dry_run
            )

            if not result.get('success', False):
                return ToolResult.error(
                    f"Delta 写入失败: {result.get('reason', '未知错误')}",
                    **result
                )

            lines = [
                f"[OK] Delta 模式写入成功: {file_path}",
                f"变更数: {result.get('delta_count', 0)} 个",
                f"变更原因: {reason or '未说明'}"
            ]
            if 'diff_preview' in result and result['diff_preview']:
                lines.extend([
                    "",
                    "变更预览:",
                    "```diff",
                    result['diff_preview'],
                    "```"
                ])
            return ToolResult.ok("\n".join(lines), **result)
        else:
            # 无 SpecEngine 模式：直接使用 DeltaSpec
            from devpal.core.schema.delta_spec import DeltaSpec

            ds = DeltaSpec(file_path)
            ds.load_original()
            deltas = ds.create_delta_from_diff(new_content, reason)
            result = ds.apply(validate=True)

            if dry_run:
                return ToolResult.ok(
                    f"Delta 预览: {file_path}\n\n```diff\n{result.diff_preview}\n```",
                    metadata={
                        'delta_count': len(deltas),
                        'dry_run': True,
                        'diff_preview': result.diff_preview
                    }
                )

            if not result.success:
                return ToolResult.error(
                    f"Delta 应用冲突: {result.conflicts}",
                    success=result.success,
                    conflicts=result.conflicts
                )

            # 实际写入
            Path(file_path).write_text(result.new_content, encoding='utf-8')

            return ToolResult.ok(
                f"[OK] Delta 模式写入成功: {file_path} (应用了 {len(result.applied_deltas)} 个变更)\n\n```diff\n{result.diff_preview}\n```",
                delta_count=len(deltas),
                applied_count=len(result.applied_deltas),
                conflicts=result.conflicts,
                diff_preview=result.diff_preview
            )
