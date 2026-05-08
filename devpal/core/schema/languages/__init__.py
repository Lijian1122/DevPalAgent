# -*- coding: utf-8 -*-
"""
OpenSpec 语言插件系统 - Phase 6: 多语言支持

核心抽象:
- LanguagePlugin: 语言插件基类
- ASTNode: 统一 AST 节点抽象
- SymbolInfo: 符号信息
- TypeInfo: 类型信息
- DependencyInfo: 依赖信息

支持的语言:
- C/C++: Clang 绑定
- Python: 内置 ast 模块
- 更多待扩展
"""

from .base import (
    LanguagePlugin,
    LanguagePluginManager,
    ASTNode,
    SymbolInfo,
    TypeInfo,
    DependencyInfo,
    Diagnostic,
    FileAnalysisResult,
)
from .cpp_plugin import CppLanguagePlugin

__all__ = [
    'LanguagePlugin',
    'LanguagePluginManager',
    'ASTNode',
    'SymbolInfo',
    'TypeInfo',
    'DependencyInfo',
    'Diagnostic',
    'FileAnalysisResult',
    'CppLanguagePlugin',
]
