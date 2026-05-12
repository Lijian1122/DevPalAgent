# -*- coding: utf-8 -*-
"""
通用模板系统 - 支持多种项目类型和编程语言
"""

from .base import BaseTemplate, TemplateContext, TemplateCategory
from .registry import TemplateRegistry, registry
from .requirements_parser import RequirementsParser

# 注册内置模板
from . import cpp_templates
from . import python_templates

__all__ = [
    'BaseTemplate',
    'TemplateContext',
    'TemplateCategory',
    'TemplateRegistry',
    'registry',
    'RequirementsParser',
]
