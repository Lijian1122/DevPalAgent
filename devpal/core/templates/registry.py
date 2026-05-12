# -*- coding: utf-8 -*-
"""
模板注册表
"""

from typing import Dict, List, Type, Optional
from .base import BaseTemplate, TemplateContext, GeneratedFile, TemplateCategory


class TemplateRegistry:
    """
    模板注册表

    管理所有可用模板，提供查询、过滤、组合功能。
    """

    def __init__(self):
        self._templates: Dict[str, Type[BaseTemplate]] = {}
        self._template_instances: Dict[str, BaseTemplate] = {}

    def register(self, template_class: Type[BaseTemplate]) -> Type[BaseTemplate]:
        """
        注册模板类（装饰器）

        Args:
            template_class: 模板类

        Returns:
            原模板类
        """
        name = template_class.name
        if name not in self._templates:
            self._templates[name] = template_class
        return template_class

    def get_template(self, name: str) -> Optional[BaseTemplate]:
        """
        获取模板实例

        Args:
            name: 模板名称

        Returns:
            模板实例，如果不存在返回 None
        """
        if name in self._template_instances:
            return self._template_instances[name]

        template_class = self._templates.get(name)
        if template_class:
            instance = template_class()
            self._template_instances[name] = instance
            return instance

        return None

    def get_templates_by_language(self, language: str) -> List[BaseTemplate]:
        """
        按语言筛选模板

        Args:
            language: 编程语言 (cpp, python, etc.)

        Returns:
            模板实例列表
        """
        templates = []
        for name in self._templates:
            tpl = self.get_template(name)
            if tpl and (tpl.language == language or tpl.language == "generic"):
                templates.append(tpl)
        return sorted(templates, key=lambda t: t.priority, reverse=True)

    def get_templates_by_category(self, category: TemplateCategory) -> List[BaseTemplate]:
        """
        按分类筛选模板

        Args:
            category: 模板分类

        Returns:
            模板实例列表
        """
        templates = []
        for name in self._templates:
            tpl = self.get_template(name)
            if tpl and tpl.category == category:
                templates.append(tpl)
        return sorted(templates, key=lambda t: t.priority, reverse=True)

    def get_matching_templates(self, context: TemplateContext) -> List[BaseTemplate]:
        """
        获取匹配上下文的所有模板

        Args:
            context: 模板上下文

        Returns:
            匹配的模板列表
        """
        all_templates = self.get_templates_by_language(context.language)
        matching = []

        for tpl in all_templates:
            if tpl.should_apply(context):
                matching.append(tpl)

        # 解析依赖
        result = []
        added = set()

        def add_with_deps(tpl: BaseTemplate):
            if tpl.name in added:
                return
            # 先添加依赖
            for dep_name in tpl.get_dependencies():
                dep_tpl = self.get_template(dep_name)
                if dep_tpl and dep_tpl.name not in added:
                    add_with_deps(dep_tpl)
            result.append(tpl)
            added.add(tpl.name)

        for tpl in matching:
            add_with_deps(tpl)

        return result

    def generate_all(self, context: TemplateContext) -> List[GeneratedFile]:
        """
        生成所有匹配模板的文件

        Args:
            context: 模板上下文

        Returns:
            所有生成的文件
        """
        templates = self.get_matching_templates(context)
        all_files = []

        for tpl in templates:
            files = tpl.generate(context)
            all_files.extend(files)

        return all_files

    def list_all_templates(self) -> List[Dict]:
        """
        列出所有已注册模板

        Returns:
            模板信息字典列表
        """
        result = []
        for name in sorted(self._templates.keys()):
            tpl = self._templates[name]
            result.append({
                'name': name,
                'description': tpl.description,
                'category': tpl.category.value,
                'language': tpl.language,
                'priority': tpl.priority,
            })
        return result


# 全局注册表实例
registry = TemplateRegistry()
