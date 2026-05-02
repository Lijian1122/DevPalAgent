# -*- coding: utf-8 -*-
"""
文件读取工具
"""
from typing import Optional
from pathlib import Path
from pydantic import BaseModel, Field
from .base import BaseTool, ToolResult, ToolSecurity, retry


class FileReaderTool(BaseTool):
    """读取本地文件内容"""

    name = "file_reader"
    description = "读取本地文件的内容，支持读取文本文件，可指定读取的行号范围"

    class Parameters(BaseModel):
        path: str = Field(description="要读取的文件的路径，可以是相对路径或绝对路径")
        start_line: int = Field(default=1, description="从Iteration几行开始读，默认从Iteration一行开始")
        end_line: int = Field(default=-1, description="读到Iteration几行结束，-1 表示读到末尾")

    @retry(max_retries=2, delay=0.5)
    def _execute(self, params: Parameters) -> ToolResult:
        # 安全检查
        safe, reason = ToolSecurity.check_path_safety(params.path)
        if not safe:
            return ToolResult.error(reason)

        try:
            path = Path(params.path)

            # 如果是目录，列出目录内容
            if path.is_dir():
                files = []
                for item in path.iterdir():
                    item_type = "目录" if item.is_dir() else "文件"
                    files.append(f"[{item_type}] {item.name}")
                files.sort()
                content = "\n".join(files)
                return ToolResult.ok(
                    content=f"目录: {params.path}\n\n共 {len(files)} 项\n\n{content}",
                    is_directory=True,
                    item_count=len(files)
                )

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

            return ToolResult.ok(
                content=f"文件: {params.path} (Iteration {params.start_line}-{end_idx} 行，共 {total_lines} 行)\n\n{content}",
                file_path=params.path,
                total_lines=total_lines,
                read_lines=end_idx - start_idx
            )

        except FileNotFoundError:
            return ToolResult.error(f"文件不存在: {params.path}")
        except UnicodeDecodeError:
            return ToolResult.error(f"文件不是 UTF-8 编码，可能是二进制文件: {params.path}")
        except Exception as e:
            return ToolResult.error(f"读取文件失败: {str(e)}")
