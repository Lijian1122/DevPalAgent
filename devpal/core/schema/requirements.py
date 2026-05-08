from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import yaml
import re
from datetime import datetime


class RequirementStatus(Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    VERIFIED = "verified"
    DEPRECATED = "deprecated"


@dataclass
class AcceptanceCriteria:
    """验收标准项"""
    description: str
    status: RequirementStatus = RequirementStatus.PROPOSED
    verification_method: str = ""

    def to_markdown(self, checkbox: bool = True) -> str:
        if checkbox:
            checked = 'x' if self.status in (RequirementStatus.IMPLEMENTED, RequirementStatus.VERIFIED) else ' '
            return f"- [{checked}] {self.description}"
        return f"- {self.description}"


@dataclass
class RequirementItem:
    """单个需求项"""
    id: str
    title: str
    description: str = ""
    acceptance_criteria: List[AcceptanceCriteria] = field(default_factory=list)
    status: RequirementStatus = RequirementStatus.PROPOSED
    priority: int = 3  # 1-5, 1最高
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    related_requirements: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """转换为 Markdown 格式"""
        lines = [
            f"## {self.id}: {self.title}",
            "",
            f"**状态**: `{self.status.value}`",
            f"**优先级**: {'⭐' * self.priority}",
            "",
        ]

        if self.tags:
            lines.append(f"**标签**: {', '.join(f'`{t}`' for t in self.tags)}")
            lines.append("")

        if self.description:
            lines.extend([
                "**描述**:",
                "",
                self.description,
                ""
            ])

        if self.acceptance_criteria:
            lines.extend([
                "**验收标准**:",
                "",
            ])
            for ac in self.acceptance_criteria:
                lines.append(ac.to_markdown())
            lines.append("")

        if self.related_requirements:
            lines.append(f"**关联需求**: {', '.join(self.related_requirements)}")
            lines.append("")

        return '\n'.join(lines)

    @classmethod
    def from_markdown(cls, md_text: str) -> 'RequirementItem':
        """从 Markdown 文本解析需求项"""
        lines = md_text.strip().split('\n')
        header_line = lines[0] if lines else ""

        # 解析标题行: ## REQ-001: 标题内容
        header_match = re.match(r'##\s+(\S+):\s+(.+)', header_line)
        if not header_match:
            raise ValueError(f"无法解析需求标题行: {header_line}")

        req_id = header_match.group(1).strip()
        title = header_match.group(2).strip()

        # 解析其他字段
        description = ""
        acceptance_criteria: List[AcceptanceCriteria] = []
        status = RequirementStatus.PROPOSED
        priority = 3
        tags: List[str] = []
        related: List[str] = []

        in_description = False
        in_ac = False
        description_lines = []

        for line in lines[1:]:
            line = line.strip()

            # 状态字段
            status_match = re.match(r'\*\*状态\*\*:\s*`?(\w+)`?', line)
            if status_match:
                status_str = status_match.group(1).lower()
                try:
                    status = RequirementStatus(status_str)
                except ValueError:
                    pass
                continue

            # 优先级字段
            priority_match = re.match(r'\*\*优先级\*\*:\s*(\S+)', line)
            if priority_match:
                stars = priority_match.group(1).count('⭐')
                priority = max(1, min(5, stars))
                continue

            # 标签字段
            tags_match = re.match(r'\*\*标签\*\*:\s*(.+)', line)
            if tags_match:
                tags = [t.strip().strip('`') for t in tags_match.group(1).split(',')]
                continue

            # 关联需求
            related_match = re.match(r'\*\*关联需求\*\*:\s*(.+)', line)
            if related_match:
                related = [r.strip() for r in related_match.group(1).split(',')]
                continue

            # 描述
            if line == '**描述**:' or line.startswith('**描述**:'):
                in_description = True
                continue

            # 验收标准
            if line.startswith('**验收标准**:'):
                in_description = False
                in_ac = True
                continue

            # 验收标准项
            if in_ac and line.startswith('- ['):
                ac_match = re.match(r'- \[([ xX])\]\s*(.+)', line)
                if ac_match:
                    checked = ac_match.group(1).lower() == 'x'
                    ac_text = ac_match.group(2).strip()
                    ac_status = RequirementStatus.IMPLEMENTED if checked else RequirementStatus.PROPOSED
                    acceptance_criteria.append(AcceptanceCriteria(
                        description=ac_text,
                        status=ac_status
                    ))
                continue

            # 收集描述文本
            if in_description and line:
                description_lines.append(line)

        description = '\n'.join(description_lines).strip()

        return cls(
            id=req_id,
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria,
            status=status,
            priority=priority,
            tags=tags,
            related_requirements=related
        )


@dataclass
class RequirementDocument:
    """需求文档 - 结构化 Markdown/YAML 混合格式"""
    file_path: Path
    title: str = ""
    version: str = "1.0"
    requirements: List[RequirementItem] = field(default_factory=list)
    related_docs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load_from_markdown(cls, file_path: Union[str, Path]) -> 'RequirementDocument':
        """从 Markdown 文件加载需求文档"""
        file_path = Path(file_path)
        content = file_path.read_text(encoding='utf-8')

        # 解析 YAML front matter
        front_matter = {}
        if content.startswith('---'):
            match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if match:
                front_matter = yaml.safe_load(match.group(1))
                content = content[match.end():]

        doc = cls(
            file_path=file_path,
            title=front_matter.get('title', file_path.stem),
            version=str(front_matter.get('version', '1.0')),
            related_docs=front_matter.get('related_docs', []),
            metadata={k: v for k, v in front_matter.items() if k not in ['title', 'version', 'related_docs']}
        )

        # 解析需求项
        req_sections = re.findall(r'##\s+\S+:.+?(?=##\s+\S+:|\Z)', content, re.DOTALL)
        for section in req_sections:
            try:
                req = RequirementItem.from_markdown(section)
                doc.requirements.append(req)
            except ValueError:
                # 跳过无法解析的部分
                continue

        return doc

    def save_to_markdown(self):
        """保存为 Markdown 文件"""
        lines = [
            '---',
            f'title: "{self.title}"',
            f'version: "{self.version}"',
        ]
        if self.related_docs:
            lines.append(f'related_docs: {self.related_docs}')
        for k, v in self.metadata.items():
            if isinstance(v, str):
                lines.append(f'{k}: "{v}"')
            else:
                lines.append(f'{k}: {v}')
        lines.extend([
            '---',
            '',
            f'# {self.title}',
            f'版本: {self.version}',
            '',
            '## 概述',
            '',
            f'本文档包含 {len(self.requirements)} 个需求项。',
            '',
        ])

        # 状态统计
        status_counts: Dict[str, int] = {}
        for req in self.requirements:
            status_counts[req.status.value] = status_counts.get(req.status.value, 0) + 1

        lines.append('**状态统计**:')
        lines.append('```')
        for status, count in sorted(status_counts.items()):
            lines.append(f'  {status}: {count} 个')
        lines.append('```')
        lines.append('')

        # 需求列表
        for req in self.requirements:
            lines.append(req.to_markdown())
            lines.append('')

        self.file_path.write_text('\n'.join(lines), encoding='utf-8')

    def add_requirement(self, req: RequirementItem):
        """添加需求项"""
        self.requirements.append(req)
        self._sort_requirements()

    def _sort_requirements(self):
        """按优先级排序需求"""
        self.requirements.sort(key=lambda r: (r.priority, r.id))

    def get_requirement_by_id(self, req_id: str) -> Optional[RequirementItem]:
        """通过 ID 查找需求"""
        for req in self.requirements:
            if req.id == req_id:
                return req
        return None

    def update_requirement_status(self, req_id: str, status: RequirementStatus):
        """更新需求状态"""
        req = self.get_requirement_by_id(req_id)
        if req:
            req.status = status
            req.updated_at = datetime.now()

    def filter_by_status(self, status: RequirementStatus) -> List[RequirementItem]:
        """按状态筛选需求"""
        return [r for r in self.requirements if r.status == status]

    def filter_by_tag(self, tag: str) -> List[RequirementItem]:
        """按标签筛选需求"""
        return [r for r in self.requirements if tag in r.tags]


class RequirementManager:
    """需求管理器 - 管理项目中所有需求文档"""

    def __init__(self, root_dir: Union[str, Path]):
        self.root_dir = Path(root_dir)
        self.docs: Dict[str, RequirementDocument] = {}

    def discover_requirements(self):
        """发现项目中所有需求文档"""
        self.docs.clear()
        for md_file in self.root_dir.rglob("req_*.md"):
            try:
                doc = RequirementDocument.load_from_markdown(md_file)
                rel_path = str(md_file.relative_to(self.root_dir))
                self.docs[rel_path] = doc
            except Exception as e:
                print(f"Warning: 无法加载需求文档 {md_file}: {e}")

    def get_requirement_by_id(self, req_id: str) -> Optional[RequirementItem]:
        """通过 ID 全局查找需求"""
        for doc in self.docs.values():
            req = doc.get_requirement_by_id(req_id)
            if req:
                return req
        return None

    def get_implementing_code(self, req_id: str, artifact_graph) -> List[str]:
        """获取实现该需求的所有代码文件（通过 ArtifactGraph 和代码中的引用）"""
        results = []
        for node_id, node in artifact_graph._nodes.items():
            if node_id.startswith('file:') and node.path:
                try:
                    content = node.path.read_text(encoding='utf-8', errors='ignore')
                    if req_id in content:
                        results.append(node_id)
                except:
                    pass
        return results

    def get_all_requirements(self) -> List[RequirementItem]:
        """获取所有需求项"""
        all_reqs = []
        for doc in self.docs.values():
            all_reqs.extend(doc.requirements)
        return all_reqs

    def create_requirement_document(self, name: str, title: str, version: str = "1.0") -> RequirementDocument:
        """创建新的需求文档"""
        file_path = self.root_dir / f"req_{name}.md"
        doc = RequirementDocument(file_path=file_path, title=title, version=version)
        self.docs[str(file_path.relative_to(self.root_dir))] = doc
        return doc

    def save_all(self):
        """保存所有需求文档"""
        for doc in self.docs.values():
            doc.save_to_markdown()

    @property
    def document_count(self) -> int:
        return len(self.docs)

    @property
    def requirement_count(self) -> int:
        return sum(len(doc.requirements) for doc in self.docs.values())


def create_example_requirement() -> str:
    """创建示例需求 Markdown"""
    return '''---
title: "用户登录系统需求"
version: "1.0"
author: "DevPal Agent"
created: "2024-05-06"
---

# 用户登录系统需求

版本: 1.0

## 概述

本文档包含用户登录系统相关的需求定义。

**状态统计**:
```
  proposed: 3 个
  implemented: 1 个
```

## REQ-001: 用户密码登录

**状态**: `implemented`
**优先级**: ⭐⭐⭐⭐⭐

**描述**:

用户可以通过用户名和密码登录系统。登录成功后跳转到首页，失败则显示错误提示。

**验收标准**:

- [x] 用户名长度限制在 4-20 个字符
- [x] 密码必须包含大小写字母、数字和特殊字符
- [x] 登录失败次数超过 5 次后锁定账号 30 分钟
- [x] 登录成功后生成 JWT Token

## REQ-002: 短信验证码登录

**状态**: `proposed`
**优先级**: ⭐⭐⭐⭐

**描述**:

用户可以通过手机号和短信验证码登录系统。

**验收标准**:

- [ ] 验证码有效期为 5 分钟
- [ ] 同一手机号每分钟只能请求一次验证码
- [ ] 验证码错误超过 3 次需刷新

## REQ-003: 第三方登录支持

**状态**: `proposed`
**优先级**: ⭐⭐⭐

**描述**:

支持微信、QQ、GitHub 第三方账号登录。

**验收标准**:

- [ ] 微信 OAuth 登录
- [ ] QQ OAuth 登录
- [ ] GitHub OAuth 登录
- [ ] 第三方账号绑定已有账号
'''
