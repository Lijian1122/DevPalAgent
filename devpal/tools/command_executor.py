# -*- coding: utf-8 -*-
"""
命令行执行工具
"""
import subprocess
from typing import Optional
from pydantic import BaseModel, Field
from .base import BaseTool, ToolResult


class CommandExecutorTool(BaseTool):
    """执行命令行命令"""

    name = "execute_command"
    description = "执行命令行命令，可以运行 shell 命令、编译代码、查看目录等"

    class Parameters(BaseModel):
        command: str = Field(description="要执行的 shell 命令")
        timeout: int = Field(default=30, description="命令超时时间，单位秒")
        shell: bool = Field(default=True, description="是否通过 shell 执行")

    def execute(self, params: Parameters) -> ToolResult:
        # 安全检查：不允许执行危险命令
        is_safe, reason = self._check_safe_command(params.command)
        if not is_safe:
            return ToolResult(
                success=False,
                content="",
                error_message=f"安全限制: {reason}"
            )

        try:
            result = subprocess.run(
                params.command,
                shell=params.shell,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=params.timeout,
            )

            stdout = result.stdout.strip() if result.stdout else ""
            stderr = result.stderr.strip() if result.stderr else ""

            output_parts = []
            if stdout:
                output_parts.append(f"stdout:\n{stdout}")
            if stderr:
                output_parts.append(f"stderr:\n{stderr}")

            output = "\n\n".join(output_parts) if output_parts else "(无输出)"

            return ToolResult(
                success=True,
                content=f"命令执行成功 (exit_code={result.returncode})\n\n{output}",
                metadata={
                    "command": params.command,
                    "return_code": result.returncode,
                    "stdout_length": len(stdout),
                    "stderr_length": len(stderr),
                }
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                content="",
                error_message=f"命令执行超时（{params.timeout}秒）"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error_message=f"命令执行失败: {str(e)}"
            )

    def _check_safe_command(self, command: str) -> tuple[bool, Optional[str]]:
        """检查命令是否安全"""
        command_lower = command.lower()

        # 危险命令黑名单
        dangerous_patterns = [
            ("rm -rf /", "删除根目录"),
            ("rm -rf ~", "删除用户目录"),
            ("mkfs", "格式化磁盘"),
            ("dd if=", "磁盘写入"),
            (":(){ :|:& };:", "fork bomb"),
            ("shred", "擦除文件"),
            ("wget", "下载文件"),
            ("curl", "网络请求"),
            ("nc ", "网络连接"),
            ("netcat", "网络连接"),
            ("ssh ", "SSH 连接"),
            ("scp ", "文件传输"),
        ]

        for pattern, reason in dangerous_patterns:
            if pattern.lower() in command_lower:
                return False, f"禁止执行 '{reason}' 相关命令"

        return True, None
