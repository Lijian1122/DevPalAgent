# -*- coding: utf-8 -*-
"""
DevPal Agent 工具系统 - 阶段4完整版本
包含核心工具 + 抽象 FunctionCall + 链表操作工具 + Git 工具 + 静态分析工具
"""
from .base import BaseTool, ToolResult, ToolSecurity, retry
from .file_reader import FileReaderTool
from .file_writer import FileWriterTool
from .command_executor import CommandExecutorTool
from .code_search import CodeSearchTool
from .compiler_analyzer import CompilerAnalyzerTool
from .registry import ToolRegistry, registry
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
from .function_call_base import (
    AbstractFunctionCall,
    FunctionCallContext,
    ExecutionResult,
    FunctionChain
)
from .linked_list import (
    LinkedList,
    ListNode,
    LinkedListTool,
    CreateLinkedList,
    AppendNode,
    PrependNode,
    InsertNode,
    DeleteNodeAtIndex,
    DeleteNodeByValue,
    UpdateNode,
    GetNode,
    FindNode,
    GetLinkedList,
    ClearLinkedList,
    DeleteLinkedList,
    ListAllLinkedLists,
    get_linked_list,
    create_linked_list,
    delete_linked_list,
    get_all_linked_lists
)

__all__ = [
    "BaseTool",
    "ToolResult",
    "ToolSecurity",
    "retry",
    "FileReaderTool",
    "FileWriterTool",
    "CommandExecutorTool",
    "CodeSearchTool",
    "CompilerAnalyzerTool",
    "ToolRegistry",
    "registry",
    # 阶段4新工具
    "GitTool",
    "StaticAnalyzer",
    "CodeReviewTool",
    "MsvcAsanCompilerTool",
    # 阶段5新工具
    "SelfSourceReaderTool",
    "SelfImproveTool",
    "PluginSystemTool",
    "AutoFixerTool",
    "TestGeneratorTool",
    "TestRunnerTool",
    "TestDocGeneratorTool",
    "TestOrchestratorTool",
    "CodeReviewReportTool",
    # 抽象 FunctionCall 模块
    "AbstractFunctionCall",
    "FunctionCallContext",
    "ExecutionResult",
    "FunctionChain",
    # 链表模块
    "LinkedList",
    "ListNode",
    "LinkedListTool",
    "CreateLinkedList",
    "AppendNode",
    "PrependNode",
    "InsertNode",
    "DeleteNodeAtIndex",
    "DeleteNodeByValue",
    "UpdateNode",
    "GetNode",
    "FindNode",
    "GetLinkedList",
    "ClearLinkedList",
    "DeleteLinkedList",
    "ListAllLinkedLists",
    "get_linked_list",
    "create_linked_list",
    "delete_linked_list",
    "get_all_linked_lists",
]
