# -*- coding: utf-8 -*-
"""
文件读取工具
"""
from typing import Optional
from pydantic import BaseModel, Field
from .base import BaseTool, ToolResult


class FileReaderTool(BaseTool):
    """读取本地文件内容"""

    name = "file_reader"
    description = "读取本地文件的内容，支持读取文本文件，可指定读取的行范围"

    class Parameters(BaseModel):
        path: str = Field(description="要读取的文件的路径，可以是相对路径或绝对路径")
        start_line: int = Field(default=1, description="从第几行开始读，默认从第一行开始")
        end_line: int = Field(default=-1, description="读到第几行结束，-1 表示读到末尾")

    def execute(self, params: Parameters) -> ToolResult:
        # 安全检查：不允许读取敏感文件
        if self._is_sensitive_path(params.path):
            return ToolResult(
                success=False,
                content="",
                error_message="不允许读取系统敏感文件（.ssh、.env、id_rsa 等）"
            )

        try:
            with open(params.path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            total_lines = len(lines)

            # 行号范围处理
            start_idx = max(0, params.start_line - 1)
            if params.end_line == -1:
                end_idx = len(lines)
            else:
                end_idx = min(params.end_line, len(lines))

            content = "".join(lines[start_idx:end_idx])

            return ToolResult(
                success=True,
                content=f"文件: {params.path} (第 {params.start_line}-{end_idx} 行，共 {total_lines} 行)\n\n{content}",
                metadata={
                    "file_path": params.path,
                    "total_lines": total_lines,
                    "read_lines": end_idx - start_idx,
                    "start_line": params.start_line,
                    "end_line": end_idx,
                }
            )

        except FileNotFoundError:
            return ToolResult(
                success=False,
                content="",
                error_message=f"文件不存在: {params.path}"
            )
        except UnicodeDecodeError:
            return ToolResult(
                success=False,
                content="",
                error_message=f"文件不是 UTF-8 编码，可能是二进制文件: {params.path}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error_message=f"读取文件失败: {str(e)}"
            )

    def _is_sensitive_path(self, path: str) -> bool:
        """安全检查，防止读取敏感文件"""
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
