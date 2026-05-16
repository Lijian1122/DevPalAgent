# -*- coding: utf-8 -*-
"""
Phase 1: 解析需求文档
"""

import json
import re
from pathlib import Path
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

        delta = self._compute_requirements_delta()
        self.context.requirements_delta = delta
        if delta["changed"]:
            self.log(f"[DELTA] 需求变更: +{len(delta['added'])} ~{len(delta['modified'])} -{len(delta['removed'])}")
        else:
            self.log("[DELTA] 需求未变更")

        return PhaseResult.ok(
            "需求文档解析成功",
       content_length=len(result.content),
            file_path=str(self.context.requirements_file),
            requirement_count=len(self.context.structured_requirements),
          delta_changed=delta["changed"],
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

    def _compute_requirements_delta(self) -> Dict[str, object]:
        """Compare current requirements with previous version to detect changes."""
        spec_dir = self.context.project_dir / ".spec"
        prev_req_file = spec_dir / "requirements.json"

        current_reqs = {req["id"]: req for req in self.context.structured_requirements}

        if not prev_req_file.exists():
            return {
                "changed": bool(current_reqs),
                "added": list(current_reqs.keys()),
                "modified": [],
                "removed": [],
            }

        try:
            prev_data = json.loads(prev_req_file.read_text(encoding="utf-8"))
            prev_reqs = {req["id"]: req for req in prev_data}
        except Exception:
            return {
           "changed": bool(current_reqs),
                "added": list(current_reqs.keys()),
                "modified": [],
                "removed": [],
            }

        added = [req_id for req_id in current_reqs if req_id not in prev_reqs]
        removed = [req_id for req_id in prev_reqs if req_id not in current_reqs]
        modified = []

        for req_id in current_reqs:
            if req_id in prev_reqs:
                curr = current_reqs[req_id]
                prev = prev_reqs[req_id]
                if (curr.get("title") != prev.get("title") or
                    curr.get("description") != prev.get("description") or
                    curr.get("acceptance_criteria") != prev.get("acceptance_criteria")):
                 modified.append(req_id)

        changed = bool(added or modified or removed)

        # Save current requirements for next comparison
        if changed:
            spec_dir.mkdir(parents=True, exist_ok=True)
            prev_req_file.write_text(
                json.dumps(self.context.structured_requirements, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

        return {
            "changed": changed,
            "added": added,
            "modified": modified,
            "removed": removed,
     }
