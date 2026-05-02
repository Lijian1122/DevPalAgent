# -*- coding: utf-8 -*-
"""
工具注册表 - 阶段1完整版本
统一管理所有可用工具
"""
from typing import Dict, List, Optional
from .base import BaseTool, ToolResult
from .file_reader import FileReaderTool
from .file_writer import FileWriterTool
from .command_executor import CommandExecutorTool
from .code_search import CodeSearchTool
from .compiler_analyzer import CompilerAnalyzerTool


class ToolRegistry:
    """工具注册表，管理所有可用的工具"""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        # 注册阶段1所有核心工具
        self.register(FileReaderTool())
        self.register(FileWriterTool())
        self.register(CommandExecutorTool())
        self.register(CodeSearchTool())
        self.register(CompilerAnalyzerTool())

    def register(self, tool: BaseTool) -> None:
        """注册一 tool(s)"""
        self._tools[tool.name] = tool

    def unregister(self, tool_name: str) -> None:
        """注销一 tool(s)"""
        if tool_name in self._tools:
            del self._tools[tool_name]

    def get(self, tool_name: str) -> Optional[BaseTool]:
        """获取指定工具"""
        return self._tools.get(tool_name)

    def list_tools(self) -> List[BaseTool]:
        """列出所有工具"""
        return list(self._tools.values())

    def list_tool_names(self) -> List[str]:
        """列出所有工具名称"""
        return list(self._tools.keys())

    def get_tool_descriptions(self) -> List[dict]:
        """获取所有工具的描述（用于 LLM）"""
        return [tool.to_function_call_format() for tool in self._tools.values()]

    def execute_tool(self, tool_name: str, parameters: dict) -> ToolResult:
        """执行指定工具"""
        tool = self.get(tool_name)
        if not tool:
            return ToolResult.error(
                f"未知工具: '{tool_name}'。可用工具: {', '.join(self.list_tool_names())}"
            )
        return tool.execute_with_validation(parameters)

    def get_tool_help(self, tool_name: str = None) -> str:
        """获取工具帮助信息"""
        if tool_name:
            tool = self.get(tool_name)
            if not tool:
                return f"未知工具: {tool_name}"
            desc = tool.to_function_call_format()
            params = desc['input_schema']['properties']
            required = desc['input_schema']['required']

            help_lines = [
                f"工具: {tool_name}",
                f"描述: {desc['description']}",
                f"参数:",
            ]
            for param_name, param_def in params.items():
                req_mark = "" if param_name in required else "  "
                help_lines.append(f"  {req_mark} {param_name}: {param_def.get('description', '')}")
            return "\n".join(help_lines)

        # 所有工具列表
        help_lines = ["可用工具列表：\n"]
        for tool in self.list_tools():
            help_lines.append(f" {tool.name}: {tool.description}")
        return "\n".join(help_lines)


# 全局工具注册表
registry = ToolRegistry()
