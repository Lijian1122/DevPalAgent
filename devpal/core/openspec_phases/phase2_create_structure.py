# -*- coding: utf-8 -*-
"""
Phase 2: 创建项目目录结构

简化版本：直接使用和 Phase4 一致的命名逻辑，不调用多余的 project_generator
"""

import json
from pathlib import Path

from .base import (
    OpenSpecContext,
    PhaseInterface,
    PhaseResult,
    infer_openspec_project_name,
)


class Phase2CreateStructure(PhaseInterface):
    """Phase 2: 创建项目目录结构"""

    def __init__(self, context: OpenSpecContext, tool_registry):
        super().__init__(context)
        self.phase_number = 2
        self.phase_name = "创建项目目录结构"
        self.tool_registry = tool_registry

    def execute(self) -> PhaseResult:
        """执行 Phase 2：简化版本"""
        self.log("开始创建项目目录结构...")

        # 直接使用和 Phase4 一致的命名逻辑，简洁高效
        project_name = self._infer_project_name()
        self.context.project_name = project_name

        project_dir = Path(project_name)
        project_dir.mkdir(exist_ok=True)
        self.context.project_dir = project_dir

        self.log(f"[OK] 项目名称: {project_name}")
        self.log(f"[OK] 项目目录: {project_dir.absolute()}")

        subdirs = self._get_project_subdirs()
        for subdir in subdirs:
            (project_dir / subdir).mkdir(exist_ok=True)
            self.log(f"  [OK] 创建子目录: {subdir}/")

        requirements_json = project_dir / ".spec" / "requirements.json"
        requirements_json.write_text(
            json.dumps(
                {"requirements": self.context.structured_requirements},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        self.context.generated_files.append(requirements_json)
        self.log(f"  [OK] 写入结构化需求: {requirements_json}")

        return PhaseResult.ok(
            "项目结构创建成功",
            project_dir=str(project_dir),
            project_name=project_name,
            subdirs=subdirs,
        )

    def _get_project_subdirs(self) -> list:
        """获取项目子目录列表（使用 LanguagePlugin）"""
        project_type = getattr(self.context, "project_type", "")
        language = getattr(self.context, "language", "cpp")

        # 特殊项目类型的目录结构
        if project_type in {"installer", "tooling"}:
            return ["scripts", "tests", "docs", ".spec"]

        # 使用 LanguagePlugin 获取目录结构
        try:
            from devpal.core.schema.languages.cpp_plugin import CppLanguagePlugin
            from devpal.core.schema.languages.python_plugin import PythonLanguagePlugin
            from devpal.core.schema.languages.shell_plugin import ShellLanguagePlugin

            # 根据语言选择插件
            if language == "python":
                plugin = PythonLanguagePlugin()
            elif language == "shell":
                plugin = ShellLanguagePlugin()
            else:  # cpp
                plugin = CppLanguagePlugin()

            subdirs = list(plugin.get_project_structure().keys())
        except Exception as e:
            # 降级到默认结构
            self.log(f"[WARNING] Failed to get structure from plugin: {e}")
            if language == "cpp":
                subdirs = ["src", "tests", "include", "docs"]
            elif language == "python":
                subdirs = ["src", "tests", "docs", "data"]
            else:  # shell
                subdirs = ["scripts", "tests", "docs", "lib"]

        # 确保 .spec 目录存在
        if ".spec" not in subdirs:
            subdirs.append(".spec")

        return subdirs

    def _infer_project_name(self) -> str:
        """从需求文件路径推断项目名称（和 Phase4 模板系统一致）"""
        return infer_openspec_project_name(
            self.context.requirements_file,
            language=self.context.language,
        )
