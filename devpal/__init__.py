# -*- coding: utf-8 -*-
"""
DevPal Agent - 个人开发助手
版本: v1.1 - 阶段4多模态+工具链扩展

核心能力：
- 8个内置工具：file_reader, file_writer, execute_command, code_search, compiler_analyzer, linked_list_tool, git_tool, static_analyzer
- 多模态图片分析（编译错误截图、代码截图）
- Git 自动化操作
- 代码静态分析（clang-tidy、cppcheck）
- Web UI 界面
- 自动工具调用和多轮对话
- 安全沙箱机制
- 参数自动校验
- 重试机制
"""
__version__ = "1.1.0"
__author__ = "DevPal Team"

from .core import AgentEngine, AgentConfig
from .tools import registry
from .config import get_config
from .multimodal import ImageAnalyzer

__all__ = [
    "AgentEngine",
    "AgentConfig",
    "registry",
    "get_config",
    "ImageAnalyzer",
]
