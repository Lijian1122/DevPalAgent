# -*- coding: utf-8 -*-
"""
工具注册表
统一管理所有可用的工具
"""
from typing import Dict, List, Optional
from .base import BaseTool, ToolResult
from .file_reader import FileReaderTool
from .file_writer import FileWriterTool
from .command_executor import CommandExecutorTool


class ToolRegistry:
    """工具注册表，管理所有可用的工具"""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        # 注册默认工具
        self.register(FileReaderTool())
        self.register(FileWriterTool())
        self.register(CommandExecutorTool())

    def register(self, tool: BaseTool) -> None:
        """注册一个工具"""
        self._tools[tool.name] = tool

    def unregister(self, tool_name: str) -> None:
        """注销一个工具"""
        if tool_name in self._tools:
            del self._tools[tool_name]

    def get(self, tool_name: str) -> Optional[BaseTool]:
        """获取指定工具"""
        return self._tools.get(tool_name)

    def list_tools(self) -> List[BaseTool]:
        """列出所有工具"""
        return list(self._tools.values())

    def get_tool_descriptions(self) -> List[dict]:
        """获取所有工具的描述（用于 LLM）"""
        return [tool.to_function_call_format() for tool in self._tools.values()]

    def execute_tool(self, tool_name: str, parameters: dict) -> ToolResult:
        """执行指定工具"""
        tool = self.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                content="",
                error_message=f"未知工具: {tool_name}"
            )
        return tool.execute_with_validation(parameters)


# 全局工具注册表
registry = ToolRegistry()
