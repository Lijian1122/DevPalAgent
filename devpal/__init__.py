# -*- coding: utf-8 -*-
"""
DevPal Agent - 个人开发助手
版本: v1.0 - 阶段1完整工具系统

核心能力：
- 5个内置工具：file_reader, file_writer, execute_command, code_search, compiler_analyzer
- 自动工具Calling和多轮对话
- 安全沙箱机制
- 参数自动校验
- 重试机制
"""
__version__ = "1.0.0"
__author__ = "DevPal Team"

from .core import AgentEngine, AgentConfig
from .tools import registry
from .config import get_config

__all__ = [
    "AgentEngine",
    "AgentConfig",
    "registry",
    "get_config",
]
