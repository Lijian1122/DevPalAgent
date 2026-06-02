# -*- coding: utf-8 -*-
"""Restore OpenSpecContext from change artifacts."""

from pathlib import Path
from typing import Dict, Any, List


class ContextRestorer:
    """Restore OpenSpecContext from change artifacts.""

    def restore_context(
        self,
        project_dir: Path,
        change_artifacts: Dict[str, Any],
        context: Any  # OpenSpecContext
    ) -> None:
      """Restore context from loaded change artifacts.

        Args:
          project_dir: Project directory
            change_artifacts: Loaded change artifacts from ChangeLoader
            context: OpenSpecContext to restore into
        """
        metadata = change_artifacts["metadata"]

        # Restore basic info
        context.current_change_id = change_artifacts["change_id"]
        context.project_type = metadata.get("project_type", "unknown")
        context.language = metadata.get("language", "unknown")

        # Restore requirements
        if "requirements" in metadata:
            context.structured_requirements = metadata["requirements"]

        # Restore design decisions
        if change_artifacts["design"]:
            context.technical_design = change_artifacts["design"]

        # Restore task list
        if change_artifacts["tasks"]:
          context.task_list = self._parse_tasks(change_artifacts["tasks"])

        # Restore spec
        if change_artifacts["spec"]:
            context.spec_content = change_artifacts["spec"]

        # Restore metadata fields
        if "features" in metadata:
            context.features = metadata["features"]

        if "project_name" in metadata:
            context.project_name = metadata["project_name"]

    def _parse_tasks(self, tasks_md: str) -> List[str]:
     """Parse tasks from tasks.md.

        Args:
            tasks_md: Content of tasks.md file

        Returns:
          List of task descriptions
        """
        tasks = []
        for line in tasks_md.split("\n"):
         line = line.strip()
            if line.startswith("- [ ]") or line.startswith("- [x]"):
        task = line[5:].strip()
          if task:
            tasks.append(task)
        return tasks

    def get_change_status(self, metadata: Dict[str, Any]) -> str:
    """Get change status from metadata.

        Args:
            metadata: Change metadata dictionary

        Returns:
      Change status (PROPOSED, IMPLEMENTED, ARCHIVED)
        """
        return metadata.get("status", "UNKNOWN")
