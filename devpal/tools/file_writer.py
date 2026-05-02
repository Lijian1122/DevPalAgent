# -*- coding: utf-8 -*-
"""
文件写入工具
"""
from pathlib import Path
from pydantic import BaseModel, Field
from .base import BaseTool, ToolResult, ToolSecurity, retry


class FileWriterTool(BaseTool):
    """写入内容到本地文件"""

    name = "file_writer"
    description = "写入内容到本地文件，可以创建新文件、覆盖已有文件、或者追加内容"

    class Parameters(BaseModel):
        path: str = Field(description="文件路径，可以是相对路径或绝对路径")
        content: str = Field(description="要写入的文件内容")
        append: bool = Field(default=False, description="是否追加模式，False=覆盖，True=追加")

    @retry(max_retries=2, delay=0.5)
    def _execute(self, params: Parameters) -> ToolResult:
        # 安全检查
        safe, reason = ToolSecurity.check_path_safety(params.path)
        if not safe:
            return ToolResult.error(reason)

        try:
            # 确保父目录存在
            file_path = Path(params.path)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件
            mode = "a" if params.append else "w"
            with open(params.path, mode, encoding="utf-8") as f:
                f.write(params.content)

            action = "追加" if params.append else "写入"
            return ToolResult.ok(
                content=f"成功{action}文件: {params.path} ({len(params.content)} 字符)",
                file_path=params.path,
                chars_written=len(params.content),
                mode=mode
            )

        except Exception as e:
            return ToolResult.error(f"写入文件失败: {str(e)}")
