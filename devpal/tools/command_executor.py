# -*- coding: utf-8 -*-
"""
命令行执行工具
"""
import subprocess
import os
from typing import Optional
from pydantic import BaseModel, Field
from .base import BaseTool, ToolResult, ToolSecurity, retry


class CommandExecutorTool(BaseTool):
    """执行命令行命令"""

    name = "execute_command"
    description = "执行命令行命令，可以运行编译、查看目录、搜索文件等操作"

    class Parameters(BaseModel):
        command: str = Field(description="要执行的 shell 命令")
        timeout: int = Field(default=30, description="命令超时时间，单位秒")
        cwd: Optional[str] = Field(default=None, description="工作目录，默认为当前目录")

    @retry(max_retries=2, delay=1.0)
    def _execute(self, params: Parameters) -> ToolResult:
        # 安全检查
        safe, reason = ToolSecurity.check_command_safety(params.command)
        if not safe:
            return ToolResult.error(reason)

        try:
            result = subprocess.run(
                params.command,
                shell=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=params.timeout,
                cwd=params.cwd
            )

            stdout = result.stdout.strip() if result.stdout else ""
            stderr = result.stderr.strip() if result.stderr else ""

            output_parts = []
            if stdout:
                output_parts.append(f"stdout:\n{stdout}")
            if stderr:
                output_parts.append(f"stderr:\n{stderr}")

            output = "\n\n".join(output_parts) if output_parts else "(无输出)"

            return ToolResult.ok(
                content=f"命令Success (exit_code={result.returncode})\n\n{output}",
                command=params.command,
                return_code=result.returncode,
                stdout_length=len(stdout),
                stderr_length=len(stderr)
            )

        except subprocess.TimeoutExpired:
            return ToolResult.error(
                f"命令执行超时（{params.timeout}秒）",
                command=params.command
            )
        except Exception as e:
            return ToolResult.error(
                f"命令Failed: {str(e)}",
                command=params.command
            )
