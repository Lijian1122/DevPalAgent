# -*- coding: utf-8 -*-
"""
Phase 2: 创建项目目录结构

简化版本：直接使用和 Phase4 一致的命名逻辑，不调用多余的 project_generator
"""

from pathlib import Path
from .base import PhaseInterface, PhaseResult, OpenSpecContext


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

        # 创建标准子目录
        for subdir in ['src', 'tests', 'include', 'docs', 'data', '.spec']:
            (project_dir / subdir).mkdir(exist_ok=True)
            self.log(f"  [OK] 创建子目录: {subdir}/")

        return PhaseResult.ok(
            "项目结构创建成功",
            project_dir=str(project_dir),
            project_name=project_name,
            subdirs=['src', 'tests', 'include', 'docs', 'data', '.spec']
        )

    def _infer_project_name(self) -> str:
        """从需求文件路径推断项目名称（和 Phase4 模板系统一致）"""
        req_file_path = Path(self.context.requirements_file)
        project_name = req_file_path.stem

        # 清理常见后缀
        if project_name.endswith('_requirements'):
            project_name = project_name.replace('_requirements', '')
        if project_name.startswith('req_'):
            project_name = project_name.replace('req_', '')

        # C++ 项目前缀
        if self.context.is_cpp and not project_name.startswith('cpp_'):
            project_name = f'cpp_{project_name}'

        return project_name
