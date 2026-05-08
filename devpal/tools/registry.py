# -*- coding: utf-8 -*-
"""
工具注册表 - Phase 4: OpenSpec EventBus 集成版本

支持事件总线集成，工具执行时自动发布事件：
  - tool_execution_started: 工具开始执行
  - tool_execution_completed: 工具执行完成
  - tool_execution_failed: 工具执行失败
"""
from typing import Dict, List, Optional, Any
from .base import BaseTool, ToolResult
from .file_reader import FileReaderTool
from .file_writer import FileWriterTool
from .command_executor import CommandExecutorTool
from .code_search import CodeSearchTool
from .compiler_analyzer import CompilerAnalyzerTool
from .linked_list import LinkedListTool
from .git_tool import GitTool
from .static_analyzer import StaticAnalyzer
from .code_review import CodeReviewTool
from .msvc_asan_compiler import MsvcAsanCompilerTool
from .self_source_reader import SelfSourceReaderTool
from .self_improve import SelfImproveTool
from .plugin_system import PluginSystemTool
from .auto_fixer import AutoFixerTool
from .test_generator import TestGeneratorTool
from .test_runner import TestRunnerTool
from .test_doc_generator import TestDocGeneratorTool
from .test_orchestrator import TestOrchestratorTool
from .code_review_report import CodeReviewReportTool
from .hallucination_detector import HallucinationDetectorTool
from .spec_tool import SpecTool
from .project_generator import ProjectGeneratorTool


class ToolRegistry:
    """工具注册表，管理所有可用的工具

    Phase 4 增强：支持 EventBus 事件发布
    """

    def __init__(self, event_bus: Optional[Any] = None):
        self._tools: Dict[str, BaseTool] = {}
        self._event_bus = None
        self._event_adapter = None
        if event_bus:
            self.set_event_bus(event_bus)

        # 注册阶段1所有核心工具
        self.register(FileReaderTool())
        self.register(FileWriterTool())
        self.register(CommandExecutorTool())
        self.register(CodeSearchTool())
        self.register(CompilerAnalyzerTool())
        # 注册链表操作工具
        self.register(LinkedListTool())
        # 注册阶段4新工具
        self.register(GitTool())
        self.register(StaticAnalyzer())
        # 注册阶段5新工具
        self.register(SelfSourceReaderTool())
        self.register(SelfImproveTool())
        self.register(PluginSystemTool())
        # 注册新工具: 代码审查和MSVC ASAN编译器
        self.register(CodeReviewTool())
        self.register(MsvcAsanCompilerTool())
        # 注册自动修复工具
        self.register(AutoFixerTool())
        # 注册测试工具
        self.register(TestGeneratorTool())
        self.register(TestRunnerTool())
        # 注册测试文档工具
        self.register(TestDocGeneratorTool())
        # 注册测试流程编排工具
        self.register(TestOrchestratorTool())
        # 注册代码审查报告工具
        self.register(CodeReviewReportTool())
        # 注册幻觉检测工具
        self.register(HallucinationDetectorTool())
        # 注册 Spec-First 规范优先工具 (Phase 1)
        self.register(SpecTool())
        # 注册项目生成器工具
        self.register(ProjectGeneratorTool())

    def set_event_bus(self, event_bus: Any):
        """设置事件总线用于发布工具执行事件"""
        self._event_bus = event_bus
        if event_bus:
            # 延迟导入避免循环依赖
            from devpal.core.schema import EventBusAdapter
            self._event_adapter = EventBusAdapter(event_bus, "ToolRegistry")

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
        """执行指定工具（Phase 4 增强版：发布事件）

        发布的事件:
        - tool_execution_started: 工具开始执行
        - tool_execution_completed: 工具执行成功
        - tool_execution_failed: 工具执行失败
        """
        import time
        start_time = time.time()

        # 发布：工具执行开始事件
        if self._event_adapter:
            self._event_adapter.publish_step_executed(
                workflow_name="tool_execution",
                step_id=tool_name,
                status="started",
                duration=0.0,
            )

        tool = self.get(tool_name)
        if not tool:
            error_msg = f"未知工具: '{tool_name}'。可用工具: {', '.join(self.list_tool_names())}"
            result = ToolResult.error(error_msg)

            # 发布：工具执行失败事件
            if self._event_adapter:
                self._event_adapter.publish_step_executed(
                    workflow_name="tool_execution",
                    step_id=tool_name,
                    status="failed",
                    duration=time.time() - start_time,
                    error_message=error_msg,
                )
            return result

        try:
            result = tool.execute_with_validation(parameters)
            duration = time.time() - start_time

            # 发布：工具执行完成事件
            if self._event_adapter:
                self._event_adapter.publish_step_executed(
                    workflow_name="tool_execution",
                    step_id=tool_name,
                    status="success" if result.success else "failed",
                    duration=duration,
                    tool_name=tool_name,
                )

            return result

        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"工具执行异常: {str(e)}"

            # 发布：工具执行失败事件
            if self._event_adapter:
                self._event_adapter.publish_step_executed(
                    workflow_name="tool_execution",
                    step_id=tool_name,
                    status="failed",
                    duration=duration,
                    error_message=error_msg,
                )
            return ToolResult.error(error_msg)

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
