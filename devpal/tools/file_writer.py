# -*- coding: utf-8 -*-
"""
文件写入工具
"""
from pathlib import Path
from pydantic import BaseModel, Field
from .base import BaseTool, ToolResult


class FileWriterTool(BaseTool):
    """写入内容到本地文件"""

    name = "file_writer"
    description = "写入内容到本地文件，可以创建新文件或覆盖已有文件"

    class Parameters(BaseModel):
        path: str = Field(description="文件路径，可以是相对路径或绝对路径")
        content: str = Field(description="要写入的文件内容")
        append: bool = Field(default=False, description="是否追加模式，False=覆盖，True=追加")

    def execute(self, params: Parameters) -> ToolResult:
        # 安全检查
        if self._is_sensitive_path(params.path):
            return ToolResult(
                success=False,
                content="",
                error_message="不允许写入系统敏感文件（.ssh、.env、id_rsa 等）"
            )

        try:
            # 确保父目录存在
            file_path = Path(params.path)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件
            mode = "a" if params.append else "w"
            with open(params.path, mode, encoding="utf-8") as f:
                f.write(params.content)

            action = "追加" if params.append else "写入"
            return ToolResult(
                success=True,
                content=f"成功{action}文件: {params.path} ({len(params.content)} 字符)",
                metadata={
                    "file_path": params.path,
                    "chars_written": len(params.content),
                    "mode": mode,
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error_message=f"写入文件失败: {str(e)}"
            )

    def _is_sensitive_path(self, path: str) -> bool:
        """安全检查，防止写入敏感文件"""
        sensitive_patterns = [
            "/etc/",
            "/root/",
            ".ssh",
            ".env",
            "id_rsa",
            "id_dsa",
            "id_ed25519",
            "_rsa",
            "password",
            "secret",
            "key",
        ]
        return any(p.lower() in path.lower() for p in sensitive_patterns)
