# -*- coding: utf-8 -*-
"""Load existing OpenSpec change artifacts."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class ChangeLoader:
    """Load existing OpenSpec change artifacts."""

    def __init__(self, project_dir: Path):
        """Initialize ChangeLoader.

        Args:
               project_dir: Project directory path
        """
        self.project_dir = Path(project_dir)
        self.changes_dir = self.project_dir / "openspec" / "changes"

    def load_change(self, change_id: str) -> Dict[str, Any]:
        """Load all artifacts for a change.

         Args:
             change_id: The change ID to load

         Returns:
        Dictionary containing all change artifacts

         Raises:
             FileNotFoundError: If change or metadata not found
        """
        change_dir = self.changes_dir / change_id

        if not change_dir.exists():
            raise FileNotFoundError(f"Change not found: {change_id}")

        # Load metadata
        metadata_path = change_dir / "metadata.json"
        if not metadata_path.exists():
            raise FileNotFoundError(f"metadata.json not found for change: {change_id}")

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

        # Load artifacts
        artifacts = {
            "change_id": change_id,
            "metadata": metadata,
            "proposal": self._load_file(change_dir / "proposal.md"),
            "tasks": self._load_file(change_dir / "tasks.md"),
            "design": self._load_file(change_dir / "design.md"),
            "spec": self._load_file(change_dir / "specs" / "spec.md"),
        }

        return artifacts

    def _load_file(self, path: Path) -> Optional[str]:
        """Load file content if exists.

          Args:
            path: File path to load

        Returns:
              File content or None if file doesn't exist
        """
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    def list_changes(self, status: Optional[str] = None) -> List[str]:
        if not self.changes_dir.exists():
            return []

        changes = []
        for change_dir in self.changes_dir.iterdir():
            if not change_dir.is_dir():
                continue

            metadata_path = change_dir / "metadata.json"
            if not metadata_path.exists():
                continue

            if status:
                try:
                    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                    if metadata.get("status") != status:
                        continue
                except (OSError, json.JSONDecodeError):
                    continue

            changes.append(change_dir.name)

        return sorted(changes)

    def change_exists(self, change_id: str) -> bool:
        """Check if a change exists.

        Args:
            change_id: The change ID to check

        Returns:
            True if change exists, False otherwise
        """
        change_dir = self.changes_dir / change_id
        metadata_path = change_dir / "metadata.json"
        return change_dir.exists() and metadata_path.exists()
