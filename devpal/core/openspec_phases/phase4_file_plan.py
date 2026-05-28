# -*- coding: utf-8 -*-
"""File generation planning for Phase 4."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class FileGenerationPlanItem:
    path: str
    purpose: str
    stage: str
    related_requirements: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "purpose": self.purpose,
            "stage": self.stage,
            "related_requirements": list(self.related_requirements),
            "dependencies": list(self.dependencies),
            "metadata": dict(self.metadata),
        }


class Phase4FilePlanner:
    def build_plan(self, context, project_name: str) -> List[FileGenerationPlanItem]:
        language = getattr(context, "language", "cpp")
        if language == "cpp":
            return self._build_cpp_plan(context, project_name)
        if language == "python":
            return self._build_python_plan(context, project_name)
        if language == "shell":
            return self._build_shell_plan(context, project_name)
        return []

    def _build_cpp_plan(self, context, project_name: str) -> List[FileGenerationPlanItem]:
        namespace = project_name.lower().replace("-", "_").replace(" ", "_")
        req_ids = self._requirement_ids(context)
        items = [
            FileGenerationPlanItem(
                path=f"include/{namespace}_service.h",
                purpose="Business service interface derived from requirements",
                stage="headers",
                related_requirements=req_ids,
            ),
            FileGenerationPlanItem(
                path=f"src/{namespace}_service.cpp",
                purpose="Business service implementation derived from requirements",
                stage="implementations",
                related_requirements=req_ids,
                dependencies=[f"include/{namespace}_service.h"],
            ),
            FileGenerationPlanItem(
                path=f"tests/test_{namespace}_service.cpp",
                purpose="Unit tests for generated business service",
                stage="tests",
                related_requirements=req_ids,
                dependencies=[f"src/{namespace}_service.cpp"],
            ),
        ]
        if self._needs_main(context):
            items.append(
                FileGenerationPlanItem(
                    path="src/main.cpp",
                    purpose="Application entry point",
                    stage="entrypoint",
                    related_requirements=req_ids,
                    dependencies=[f"src/{namespace}_service.cpp"],
                )
            )
        return items

    def _build_python_plan(self, context, project_name: str) -> List[FileGenerationPlanItem]:
        module_name = project_name.lower().replace("-", "_").replace(" ", "_")
        req_ids = self._requirement_ids(context)
        return [
            FileGenerationPlanItem(
                path=f"src/{module_name}.py",
                purpose="Python module implementation derived from requirements",
                stage="implementations",
                related_requirements=req_ids,
            ),
            FileGenerationPlanItem(
                path=f"tests/test_{module_name}.py",
                purpose="Pytest tests for generated module",
                stage="tests",
                related_requirements=req_ids,
                dependencies=[f"src/{module_name}.py"],
            ),
        ]

    def _build_shell_plan(self, context, project_name: str) -> List[FileGenerationPlanItem]:
        script_name = project_name.lower().replace(" ", "-").replace("_", "-")
        req_ids = self._requirement_ids(context)
        return [
            FileGenerationPlanItem(
                path=f"scripts/{script_name}.sh",
                purpose="Shell script implementation derived from requirements",
                stage="implementations",
                related_requirements=req_ids,
            ),
            FileGenerationPlanItem(
                path=f"tests/test_{script_name}.sh",
                purpose="Shell tests for generated script",
                stage="tests",
                related_requirements=req_ids,
                dependencies=[f"scripts/{script_name}.sh"],
            ),
        ]

    def _requirement_ids(self, context) -> List[str]:
        return [
            str(req.get("id"))
            for req in getattr(context, "structured_requirements", []) or []
            if req.get("id")
        ]

    def _needs_main(self, context) -> bool:
        project_type = getattr(context, "project_type", "")
        if project_type in {"library", "installer", "tooling"}:
            return False
        features = set(getattr(context, "features", []) or [])
        return bool(features) or project_type in {"application", "cli_tool", ""}
