# -*- coding: utf-8 -*-
"""
模板基类和上下文
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class TemplateCategory(Enum):
    """模板分类"""
    CORE = "core"              # 核心功能
    AUTH = "auth"              # 认证系统
    DATABASE = "database"      # 数据库
    API = "api"                # API 服务
    WEB = "web"                # Web 应用
    CLI = "cli"                # 命令行工具
    TEST = "test"              # 测试
    DOCS = "docs"              # 文档
    BUILD = "build"            # 构建配置


@dataclass
class GeneratedFile:
    """生成的文件"""
    path: str
    content: str
    description: str = ""


@dataclass
class TemplateContext:
    """模板渲染上下文"""
    project_name: str
    project_type: str = "generic"
    language: str = "cpp"      # cpp, python, rust, go
    features: List[str] = field(default_factory=list)
    requirements: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, str] = field(default_factory=dict)

    # 运行时数据
    existing_files: List[str] = field(default_factory=list)
    existing_symbols: List[str] = field(default_factory=list)

    def get(self, key: str, default: Any = None) -> Any:
        """获取变量"""
        return self.variables.get(key, default)

    def set(self, key: str, value: Any):
        """设置变量"""
        self.variables[key] = value


class BaseTemplate(ABC):
    """
    模板基类

    所有自定义模板都需要继承此类。
    """

    name: str = "base_template"
    description: str = "基础模板"
    category: TemplateCategory = TemplateCategory.CORE
    language: str = "generic"
    priority: int = 0  # 优先级，数值越大越先执行

    @abstractmethod
    def generate(self, context: TemplateContext) -> List[GeneratedFile]:
        """
        生成代码文件

        Args:
            context: 模板上下文

        Returns:
            生成的文件列表
        """
        pass

    def get_dependencies(self) -> List[str]:
        """
        获取依赖的其他模板名称

        Returns:
            依赖模板名称列表
        """
        return []

    def should_apply(self, context: TemplateContext) -> bool:
        """
        判断模板是否应该应用

        Args:
            context: 模板上下文

        Returns:
            True 表示应该应用
        """
        return True

    def apply_to_existing(self, context: TemplateContext, file_path: Path) -> Optional[GeneratedFile]:
        """
        增量应用到现有文件

        Args:
            context: 模板上下文
            file_path: 现有文件路径

        Returns:
            如果有修改则返回新的内容，否则返回 None
        """
        return None
