# -*- coding: utf-8 -*-
"""
DevPal Agent 工具系统 - 阶段2完整版本
包含核心工具 + 抽象 FunctionCall + 链表操作工具
"""
from .base import BaseTool, ToolResult, ToolSecurity, retry
from .file_reader import FileReaderTool
from .file_writer import FileWriterTool
from .command_executor import CommandExecutorTool
from .code_search import CodeSearchTool
from .compiler_analyzer import CompilerAnalyzerTool
from .registry import ToolRegistry, registry
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
