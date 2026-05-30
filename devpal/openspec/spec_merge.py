# -*- coding: utf-8 -*-
"""OpenSpec spec delta merge helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class SpecMergeResult:
    merged: bool
    target_path: Path
    marker: str


class SpecMerger:
    def merge_change_spec(self, project_dir: Path, change_id: str, change_root: Path | None = None) -> SpecMergeResult:
        change_root = change_root or project_dir
        change_spec = change_root / "openspec" / "changes" / change_id / "specs" / "spec.md"
        if not change_spec.exists():
            raise FileNotFoundError(f"change spec not found: {change_spec}")

        target = project_dir / "openspec" / "specs" / "main.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        marker = f"<!-- change:{change_id} -->"
        end_marker = f"<!-- /change:{change_id} -->"
        existing = target.read_text(encoding="utf-8") if target.exists() else "# Main OpenSpec\n"
        if marker in existing:
            return SpecMergeResult(merged=False, target_path=target, marker=marker)

        delta = change_spec.read_text(encoding="utf-8")
        block = f"\n\n{marker}\n## Change: {change_id}\n\n{delta.strip()}\n{end_marker}\n"
        target.write_text(existing.rstrip() + block, encoding="utf-8")
        return SpecMergeResult(merged=True, target_path=target, marker=marker)
