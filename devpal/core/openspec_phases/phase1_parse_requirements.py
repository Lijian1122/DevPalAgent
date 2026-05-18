# -*- coding: utf-8 -*-
"""
Phase 1: 解析需求文档

输出：
- context.requirements_content
- context.structured_requirements  (含 scenarios, priority, status)
- context.requirements_delta
- .spec/requirements.json
- .spec/delta.json
"""

import json
import re
from datetime import datetime
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

        # 检测项目特性和类型
        self.context.features = self._detect_features(result.content)
        self.context.project_type = self._detect_project_type(result.content)

        # 根据项目类型更新 is_cpp 和 language
        if self.context.project_type in ['installer', 'cli_tool', 'tooling'] or 'install' in self.context.features:
            self.context.is_cpp = False
            self.context.language = 'python'  # 安装脚本默认使用 Python

        if self.context.features:
            self.log(f"[INFO] 检测到特性: {', '.join(self.context.features)}")
        if self.context.project_type:
            self.log(f"[INFO] 项目类型: {self.context.project_type}")
        self.log(f"[INFO] 语言: {self.context.language}, is_cpp: {self.context.is_cpp}")

        delta = self._compute_requirements_delta()
        self.context.requirements_delta = delta
        if delta["changed"]:
            self.log(f"[DELTA] 需求变更: +{len(delta['added'])} ~{len(delta['modified'])} -{len(delta['removed'])}")
        else:
            self.log("[DELTA] 需求未变更")

        # P1.3: 写入 .spec/delta.json
        self._write_delta_json(delta)

        return PhaseResult.ok(
            "需求文档解析成功",
            content_length=len(result.content),
            file_path=str(self.context.requirements_file),
            requirement_count=len(self.context.structured_requirements),
            delta_changed=delta["changed"],
        )

    # --------------------------------------------------------
    # P1.1 + P1.2: 解析需求，包含场景、优先级、状态
    # --------------------------------------------------------

    def _parse_structured_requirements(self, content: str) -> List[Dict[str, object]]:
        """
        从Markdown格式内容中解析结构化需求
        支持两种模式：
        1. 无标题的纯文本（整体作为单个需求）
        2. 多级标题组织的结构化需求（## 开头的章节）

        返回标准化的需求列表，每个需求包含：
        - id: 需求ID (REQ-XXX格式)
        - title: 需求标题
        - description: 描述文本
        - acceptance_criteria: 验收标准列表
        - scenarios: 场景列表（Given/When/Then结构）
        - priority: 优先级 (P0-P3)
        - status: 状态 (固定为PROPOSED)
        """
        # 提取所有##开头的章节
        sections = re.findall(r"(^##\s+.+?)(?=^##\s+|\Z)", content, re.MULTILINE | re.DOTALL)
        requirements: List[Dict[str, object]] = []

        # 处理无章节的纯文本情况
        if not sections:
            stripped = content.strip()
            if stripped:
                return [{
                    "id": "REQ-001",
                    "title": "需求文档",
                    "description": stripped,
                    "acceptance_criteria": [],
                    "scenarios": [],
                    "priority": "P1",
                    "status": "PROPOSED",
                }]
            return []

        # 处理结构化章节
        for index, section in enumerate(sections, start=1):
            lines = section.strip().splitlines()
            header = lines[0].strip().lstrip("#").strip()

            # 解析需求ID和标题
            req_match = re.match(r"(REQ[-_]?\d+|REQ\d+)\s*[:：-]?\s*(.*)", header, re.IGNORECASE)
            if req_match:
                req_id = req_match.group(1).replace("_", "-").upper()
                title = req_match.group(2).strip() or req_id
            else:
                req_id = f"REQ-{index:03d}"
                title = header

            # 初始化需求字段
            description_lines: List[str] = []
            acceptance_criteria: List[str] = []
            scenarios: List[Dict[str, str]] = []
            priority = "P1"
            in_acceptance = False
            current_scenario: Dict[str, str] = {}

            # 逐行解析内容
            for raw_line in lines[1:]:
                line = raw_line.strip()
                if not line:
                    if current_scenario and ("given" in current_scenario or "when" in current_scenario):
                        scenarios.append(current_scenario)
                        current_scenario = {}
                    continue

                # 1. 优先级解析 (P0/P1/P2/P3)
                priority_match = re.search(
                    r'(P0|P1|P2|P3|Critical|High|Medium|Low|高|中|低)',
                    line, re.IGNORECASE
                )
                if priority_match:
                    raw_p = priority_match.group(1).upper()
                    priority_map = {
                        "CRITICAL": "P0", "HIGH": "P1", "MEDIUM": "P2", "LOW": "P3",
                        "高": "P0", "中": "P1", "低": "P2",
                    }
                    priority = priority_map.get(raw_p, raw_p if raw_p.startswith("P") else "P1")
                    continue

                # 2. 场景解析 (Given/When/Then)
                given_match = re.match(r"[-*]?\s*(?:Given|给定|前提)[：:]\s*(.*)", line, re.IGNORECASE)
                when_match = re.match(r"[-*]?\s*(?:When|当|操作)[：:]\s*(.*)", line, re.IGNORECASE)
                then_match = re.match(r"[-*]?\s*(?:Then|则|结果)[：:]\s*(.*)", line, re.IGNORECASE)

                if given_match:
                    if current_scenario and ("given" in current_scenario or "when" in current_scenario):
                        scenarios.append(current_scenario)
                    current_scenario = {"given": given_match.group(1).strip()}
                    continue

                if when_match:
                    current_scenario["when"] = when_match.group(1).strip()
                    continue

                if then_match:
                    current_scenario["then"] = then_match.group(1).strip()
                    continue

                # 3. 验收标准解析
                if "验收" in line or "acceptance" in line.lower():
                    in_acceptance = True
                    continue

                if line.startswith(("- [ ]", "- [x]", "- [X]")):
                    acceptance_criteria.append(line[5:].strip())
                    continue

                if in_acceptance and line.startswith("-"):
                    acceptance_criteria.append(line.lstrip("- ").strip())
                    continue

                # 4. 描述内容处理
                if line.startswith("**描述**"):
                    description_lines.append(
                        line.split(":", 1)[-1].strip() if ":" in line else line
                    )
                    continue

                if not in_acceptance and "given" not in current_scenario:
                    description_lines.append(line)

            # 清理最后的待处理场景
            if current_scenario and ("given" in current_scenario or "when" in current_scenario):
                scenarios.append(current_scenario)

            # 构建标准化需求对象
            requirements.append({
                "id": req_id,
                "title": title,
                "description": "\n".join(filter(None, description_lines)).strip(),
                "acceptance_criteria": acceptance_criteria,
                "scenarios": scenarios,
                "priority": priority,
                "status": "PROPOSED",
            })

        return requirements

    # ---------------------------------------------
    # Delta 计算 (逻辑不变，现在也写入 delta.json)
    # ---------------------------------------------

    def _compute_requirements_delta(self) -> Dict[str, object]:
        """比较当前需求与之前版本以检测变更"""
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

    # ------------------------------------
    # P1.3: 写入 .spec/delta.json
    # ------------------------------------

    def _write_delta_json(self, delta: Dict[str, object]) -> None:
        """将 delta 摘要写入 .spec/delta.json 供外部工具使用"""
        spec_dir = self.context.project_dir / ".spec"
        spec_dir.mkdir(parents=True, exist_ok=True)
        delta_path = spec_dir / "delta.json"

        added = delta.get("added", [])
        modified = delta.get("modified", [])
        removed = delta.get("removed", [])

        payload = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "added": added,
            "modified": modified,
            "removed": removed,
            "changed": bool(delta.get("changed", False)),
            "summary": f"{len(added)} added, {len(modified)} modified, {len(removed)} removed",
        }
        delta_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self.log(f"  [OK] .spec/delta.json written ({payload['summary']})")

    # ------------------------------------
    # 项目特性和类型检测
    # -------------------------

    def _detect_features(self, content: str) -> List[str]:
        """检测项目特性

        Args:
            content: 需求文档内容

        Returns:
            特性列表，如 ['install', 'auth', 'database']
        """
        features = []
        content_lower = content.lower()

        # 安装脚本特性
        install_keywords = ['install', 'installer', 'setup', 'deploy', 'script', '安装', '部署']
        if any(keyword in content_lower for keyword in install_keywords):
            features.append('install')

        # 认证特性
        auth_keywords = ['auth', 'login', 'authentication', '认证', '登录']
        if any(keyword in content_lower for keyword in auth_keywords):
            features.append('auth')

        # 数据库特性
        db_keywords = ['database', 'db', 'sql', 'mysql', 'postgres', '数据库']
        if any(keyword in content_lower for keyword in db_keywords):
            features.append('database')

    # API 特性
        api_keywords = ['api', 'rest', 'restful', 'endpoint', 'http']
        if any(keyword in content_lower for keyword in api_keywords):
           features.append('api')

        # Web 特性
        web_keywords = ['web', 'html', 'css', 'javascript', 'frontend', '前端', '网页']
        if any(keyword in content_lower for keyword in web_keywords):
          features.append('web')

        return features

    def _detect_project_type(self, content: str) -> str:
        """检测项目类型

        Args:
            content: 需求文档内容

        Returns:
            项目类型，如 'installer', 'cli_tool', 'library', 'application'
    """
        content_lower = content.lower()

        # 安装脚本项目
        if any(kw in content_lower for kw in ['installer', 'install script', '安装脚本', 'setup script']):
            return 'installer'

        # CLI 工具
        if any(kw in content_lower for kw in ['cli tool', 'command line', '命令行工具', 'terminal']):
           return 'cli_tool'

      # 库/框架
        if any(kw in content_lower for kw in ['library', 'framework', '库', '框架', 'sdk']):
            return 'library'

        # Web 应用
        if any(kw in content_lower for kw in ['web app', 'web application', 'website', '网站', 'web服务']):
            return 'web_app'

        # 默认为应用程序
        return ''
