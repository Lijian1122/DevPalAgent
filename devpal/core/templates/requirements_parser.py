# -*- coding: utf-8 -*-
"""
需求文档解析器
"""

import re
from pathlib import Path
from typing import Dict, List, Any
from .base import TemplateContext


class RequirementsParser:
    """
    需求文档解析器

    将需求文档转换为模板上下文，支持：
    - 提取项目名称和类型
    - 识别编程语言
    - 提取功能特性列表
    - 解析需求章节内容
    """

    # 语言检测关键词 (按优先级排序，先检测更具体的)
    LANGUAGE_KEYWORDS = {
        'cpp': ['c++', 'cpp', 'cplusplus', 'C++', 'C++标准库', 'CMake', 'std::', '#include'],
        'python': ['python', 'Python', 'py', 'import ', 'def ', 'class '],
        'rust': ['rust', 'Rust', 'rs', 'fn ', 'let mut', 'struct '],
        'go': ['golang', 'go', 'Go', 'func ', 'package '],
    }

    # 功能特性关键词
    FEATURE_KEYWORDS = {
        'auth': ['认证', '登录', '注册', 'auth', 'login', 'register', '用户', '用户登录'],
        'database': ['数据库', 'database', 'db', '存储', '持久化', 'sql', '数据持久化', '数据存储'],
        'api': ['api', 'API', '接口', 'rest', 'REST', 'http', 'RESTful'],
        'web': ['web', '网页', '前端', 'frontend'],
        'cli': ['cli', '命令行', '命令行工具', 'command'],
        'test': ['测试', 'test', '单元测试', 'unittest', '单元测试'],
        'docs': ['文档', 'doc', 'README', 'readme'],
        'build': ['构建', 'build', 'cmake', 'Makefile'],
    }

    def __init__(self, requirements_file: str):
        self.file_path = Path(requirements_file)
        self.content = self.file_path.read_text(encoding='utf-8', errors='ignore')
        self.lines = self.content.splitlines()

    def parse(self) -> TemplateContext:
        """
        解析需求文档，生成模板上下文

        Returns:
            TemplateContext 对象
        """
        project_name = self._extract_project_name()
        language = self._detect_language()
        features = self._extract_features()
        requirements = self._extract_requirements()
        variables = self._extract_variables()

        return TemplateContext(
            project_name=project_name,
            project_type=self._detect_project_type(),
            language=language,
            features=features,
            requirements=requirements,
            variables=variables
        )

    def _extract_project_name(self) -> str:
        """提取项目名称"""
        # 查找标题行
        for line in self.lines:
            if line.startswith('# '):
                name = line[2:].strip()
                # 清理常见后缀
                name = re.sub(r' -.*$', '', name)
                name = re.sub(r'（.*?）', '', name)
                return name.strip()

        # 使用文件名
        return self.file_path.stem.replace('_requirements', '').replace('req_', '')

    def _detect_language(self) -> str:
        """检测编程语言"""
        content_lower = self.content.lower()

        # 按优先级检测：计算每种语言的匹配得分
        lang_scores = {}
        for lang, keywords in self.LANGUAGE_KEYWORDS.items():
            score = 0
            for kw in keywords:
                kw_lower = kw.lower()
                # 确保关键词是完整的词（避免误判如 "rust" 在 "trust" 等词中）
                import re
                if re.search(r'\\b' + re.escape(kw_lower) + r'\\b', content_lower):
                    score += 1
                # 对于特殊标记如文件名、代码标记
                elif kw_lower in ['c++', 'std::', '#include', 'import ']:
                    if kw_lower in content_lower:
                        score += 2

            lang_scores[lang] = score

        # 返回得分最高的语言，如果都为0，默认 C++
        best_lang = max(lang_scores.items(), key=lambda x: x[1])
        if best_lang[1] > 0:
            return best_lang[0]
        return 'cpp'  # 默认 C++

    def _detect_project_type(self) -> str:
        """检测项目类型"""
        if any(kw in self.content.lower() for kw in ['web', 'http', 'api']):
            return 'web_api'
        if any(kw in self.content.lower() for kw in ['auth', '登录', '认证']):
            return 'authentication'
        if any(kw in self.content.lower() for kw in ['cli', '命令行']):
            return 'cli_tool'
        return 'generic'

    def _extract_features(self) -> List[str]:
        """提取功能特性列表"""
        features = set()

        # 关键词匹配
        for feature, keywords in self.FEATURE_KEYWORDS.items():
            for kw in keywords:
                if kw in self.content:
                    features.add(feature)
                    break

        # 查找列表形式的需求
        for line in self.lines:
            stripped = line.strip()
            if stripped.startswith('- ') or stripped.startswith('* '):
                item = stripped[2:].strip()
                # 简单的特征映射
                if '测试' in item or 'test' in item.lower():
                    features.add('test')
                if '文档' in item or 'doc' in item.lower():
                    features.add('docs')
                if '构建' in item or 'build' in item.lower():
                    features.add('build')

        return sorted(list(features))

    def _extract_requirements(self) -> Dict[str, Any]:
        """提取需求章节内容"""
        requirements = {}
        current_section = None
        section_content = []

        for line in self.lines:
            if line.startswith('## '):
                if current_section:
                    requirements[current_section] = '\n'.join(section_content)
                current_section = line[3:].strip()
                section_content = []
            elif current_section:
                section_content.append(line)

        if current_section:
            requirements[current_section] = '\n'.join(section_content)

        return requirements

    def _extract_variables(self) -> Dict[str, str]:
        """提取自定义变量"""
        variables = {}

        # 查找形如 key: value 的行
        for line in self.lines:
            match = re.match(r'^(\w+):\s*(.+)$', line.strip())
            if match:
                variables[match.group(1)] = match.group(2)

        return variables

    def get_summary(self) -> Dict[str, Any]:
        """获取解析摘要"""
        ctx = self.parse()
        return {
            'project_name': ctx.project_name,
            'project_type': ctx.project_type,
            'language': ctx.language,
            'features': ctx.features,
            'num_requirements': len(ctx.requirements),
            'requirements': list(ctx.requirements.keys()),
        }
