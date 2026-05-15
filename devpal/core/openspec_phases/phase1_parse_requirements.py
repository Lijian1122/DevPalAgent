# -*- coding: utf-8 -*-
"""
Phase 1: 解析需求文档
"""

import re
from typing import Dict, List

from .base import PhaseInterface, PhaseResult, OpenSpecContext


class Phase1ParseRequirements(PhaseInterface):
    """Phase 1: 解析需求文档"""

    def __init__(self, context: OpenSpecContext, tool_registry):
        super().__init__(context)
        self.phase_number = 1
        self.phase_name = "解析需求文档"
        self.tool_registry = tool_registry

    def execute(self) -> PhaseResult:
        """执行 Phase 1"""
        self.log("开始解析需求文档...")

        result = self.tool_registry.execute_tool(
            'file_reader',
            {'path': str(self.context.requirements_file)}
        )

        if not result.success:
            self.log(f"[FAIL] {result.error_message}")
            return PhaseResult.fail(
                f"读取需求文档失败: {result.error_message}",
                errors=[result.error_message]
            )

        self.context.requirements_content = result.content
        self.context.structured_requirements = self._parse_structured_requirements(result.content)
        self.log(f"[OK] 需求文档已读取 ({len(result.content)} 字符)")
        self.log(f"[OK] 结构化需求: {len(self.context.structured_requirements)} 项")

        return PhaseResult.ok(
            "需求文档解析成功",
            content_length=len(result.content),
            file_path=str(self.context.requirements_file),
            requirement_count=len(self.context.structured_requirements),
        )

    def _parse_structured_requirements(self, content: str) -> List[Dict[str, object]]:
        sections = re.findall(r"(^##\s+.+?)(?=^##\s+|\Z)", content, re.MULTILINE | re.DOTALL)
        requirements: List[Dict[str, object]] = []

        if not sections:
            stripped = content.strip()
            if stripped:
                return [{
                    "id": "REQ-001",
                    "title": "需求文档",
                    "description": stripped,
                    "acceptance_criteria": [],
                }]
            return []

        for index, section in enumerate(sections, start=1):
            lines = section.strip().splitlines()
            header = lines[0].strip().lstrip("#").strip()
            req_match = re.match(r"(REQ[-_]?\d+|REQ\d+)\s*[:：-]?\s*(.*)", header, re.IGNORECASE)
            if req_match:
                req_id = req_match.group(1).replace("_", "-").upper()
                title = req_match.group(2).strip() or req_id
            else:
                req_id = f"REQ-{index:03d}"
                title = header

            description_lines: List[str] = []
            acceptance_criteria: List[str] = []
            in_acceptance = False

            for raw_line in lines[1:]:
                line = raw_line.strip()
                if not line:
                    continue
                if "验收" in line or "acceptance" in line.lower():
                    in_acceptance = True
                    continue
                if line.startswith(("- [ ]", "- [x]", "- [X]")):
                    acceptance_criteria.append(line[5:].strip())
                    continue
                if in_acceptance and line.startswith("-"):
                    acceptance_criteria.append(line.lstrip("- ").strip())
                    continue
                if line.startswith("**描述**"):
                    description_lines.append(line.split(":", 1)[-1].strip() if ":" in line else "")
                    continue
                if not in_acceptance:
                    description_lines.append(line)

            requirements.append({
                "id": req_id,
                "title": title,
                "description": "\n".join(part for part in description_lines if part).strip(),
                "acceptance_criteria": acceptance_criteria,
            })

        return requirements
