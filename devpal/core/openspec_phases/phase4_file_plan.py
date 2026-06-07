# -*- coding: utf-8 -*-
"""File generation planning for Phase 4."""

from __future__ import annotations

import re
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
        class_names = self._extract_cpp_class_names(context)

        if not class_names:
            class_names = [self._pascal_case(namespace + "_service")]

        items: List[FileGenerationPlanItem] = []
        header_paths: List[str] = []
        source_paths: List[str] = []

        for class_name in class_names:
            file_stem = self._snake_case(class_name)
            header_path = f"include/{file_stem}.h"
            source_path = f"src/{file_stem}.cpp"
            header_paths.append(header_path)
            source_paths.append(source_path)
            items.append(
                FileGenerationPlanItem(
                    path=header_path,
                    purpose=f"C++ header for {class_name}",
                    stage="headers",
                    related_requirements=req_ids,
                    metadata={"class_name": class_name},
                )
            )
            items.append(
                FileGenerationPlanItem(
                    path=source_path,
                    purpose=f"C++ implementation for {class_name}",
                    stage="implementations",
                    related_requirements=req_ids,
                    dependencies=[header_path],
                    metadata={"class_name": class_name},
                )
            )

        service_class = self._select_service_class(class_names)
        service_stem = self._snake_case(service_class)
        service_source = f"src/{service_stem}.cpp"
        if self._needs_main(context):
            items.append(
                FileGenerationPlanItem(
                    path="src/main.cpp",
                    purpose="Application entry point that demonstrates the core workflow",
                    stage="entrypoint",
                    related_requirements=req_ids,
                    dependencies=list(source_paths),
                )
            )

        items.append(
            FileGenerationPlanItem(
                path=f"tests/test_{service_stem}.cpp",
                purpose=f"Unit tests for {service_class} and related business classes",
                stage="tests",
                related_requirements=req_ids,
                dependencies=[service_source],
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

    def _extract_cpp_class_names(self, context) -> List[str]:
        requirements_text = getattr(context, "requirements_content", "") or ""
        names: List[str] = []
        for match in re.finditer(r"^###\s*\d+\.\s*([A-Z][A-Za-z0-9_]*)", requirements_text, re.MULTILINE):
            name = match.group(1)
            if name not in names:
                names.append(name)
        return names

    def _needs_main(self, context) -> bool:
        project_type = getattr(context, "project_type", "")
        requirements_text = (getattr(context, "requirements_content", "") or "").lower()
        if "main.cpp" in requirements_text or "main.c" in requirements_text:
            return True
        if project_type in {"library", "installer", "tooling"}:
            return False
        features = set(getattr(context, "features", []) or [])
        return bool(features) or project_type in {"application", "cli_tool", ""}

    def _select_service_class(self, class_names: List[str]) -> str:
        for class_name in class_names:
            if "service" in class_name.lower():
                return class_name
        return class_names[0]

    def _snake_case(self, name: str) -> str:
        s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def _pascal_case(self, name: str) -> str:
        return "".join(part.capitalize() for part in re.split(r"[_\-\s]+", name) if part)
