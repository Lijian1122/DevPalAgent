# -*- coding: utf-8 -*-
"""Shell project infrastructure templates."""

from typing import List

from .base import BaseTemplate, GeneratedFile, TemplateContext, TemplateCategory
from .registry import registry


@registry.register
class ShellProjectSkeletonTemplate(BaseTemplate):
    """Shell project skeleton template."""

    name = "shell_skeleton"
    description = "Shell project base files"
    category = TemplateCategory.BUILD
    language = "shell"
    priority = 100

    def generate(self, context: TemplateContext) -> List[GeneratedFile]:
        return [
            GeneratedFile(
                path=".gitignore",
                content="""# Shell
*.log
*.tmp

# Test output
coverage/

# OS
.DS_Store
Thumbs.db
""",
                description="Git ignore file for shell projects",
            )
        ]


@registry.register
class ShellReadmeTemplate(BaseTemplate):
    """Shell README template."""

    name = "shell_readme"
    description = "Shell project README"
    category = TemplateCategory.DOCS
    language = "shell"
    priority = 50

    def generate(self, context: TemplateContext) -> List[GeneratedFile]:
        content = f'''# {context.project_name}

## 项目简介

Shell 脚本项目。

## 环境要求

- Bash 4.0+

## 使用方法

```bash
bash scripts/main.sh
```

## 项目结构

```
.
├── scripts/          # Shell scripts
├── tests/            # Test scripts
├── lib/              # Shared shell libraries
└── README.md         # Project documentation
```

## 测试

```bash
bats tests/
```
'''
        return [GeneratedFile(
            path="README.md",
            content=content,
            description="Shell project README",
        )]
