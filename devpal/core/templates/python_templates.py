# -*- coding: utf-8 -*-
"""Python 项目模板 - 只提供项目骨架，不包含业务逻辑"""

from typing import List
from .base import BaseTemplate, GeneratedFile, TemplateContext, TemplateCategory
from .registry import registry


@registry.register
class PythonProjectSkeletonTemplate(BaseTemplate):
    """Python 项目骨架模板 - 只创建目录结构和空文件"""
    name = "python_skeleton"
    description = "Python 项目基础目录结构"
    category = TemplateCategory.BUILD
    language = "python"
    priority = 100

    def generate(self, context: TemplateContext) -> List[GeneratedFile]:
        """生成基础目录结构和配置文件"""
        files = []

        # src/__init__.py
        files.append(GeneratedFile(
            path="src/__init__.py",
            content='"""项目源代码包"""\n',
            description="源代码包初始化文件"
        ))

        # tests/__init__.py
        files.append(GeneratedFile(
            path="tests/__init__.py",
            content='"""测试包"""\n',
            description="测试包初始化文件"
        ))

        # requirements.txt
        files.append(GeneratedFile(
            path="requirements.txt",
            content="# Python 依赖包\n# 根据项目需求添加依赖\n",
            description="Python 依赖配置"
        ))

        # .gitignore
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/

# OS
.DS_Store
Thumbs.db
"""
        files.append(GeneratedFile(
            path=".gitignore",
            content=gitignore_content,
            description="Git 忽略文件配置"
        ))

        return files


@registry.register
class PythonReadmeTemplate(BaseTemplate):
    """Python README 模板"""
    name = "python_readme"
    description = "Python 项目 README 文档"
    category = TemplateCategory.DOCS
    language = "python"
    priority = 50

    def generate(self, context: TemplateContext) -> List[GeneratedFile]:
        """生成 README 文档"""
        # 从 requirements 获取描述，或使用默认值
        description = context.requirements.get('description', 'Python 项目')

        content = f'''# {context.project_name}

## 项目简介

{description}

## 功能特性

（根据需求文档自动生成）

## 环境要求

- Python 3.8+
- pip (Python 包管理器)

## 安装步骤

1. 克隆项目
```bash
git clone <repository-url>
cd {context.project_name}
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

## 使用方法

（根据项目类型自动生成）

## 项目结构

```
.
├── src/              # 源代码目录
├── tests/            # 测试目录
├── requirements.txt  # Python 依赖
└── README.md         # 项目文档
```

## 测试

运行测试：
```bash
pytest tests/
```

## 许可证

MIT License
'''

        return [GeneratedFile(
            path="README.md",
            content=content,
            description="Python 项目 README 文档"
        )]
