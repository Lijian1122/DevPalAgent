# -*- coding: utf-8 -*-
"""Generate AI-agnostic collaboration rule packs."""

from pathlib import Path
from typing import Optional


class RulePackGenerator:
    """Generate AI-agnostic collaboration rule packs."""

    def __init__(self, project_dir: Path, change_id: Optional[str] = None):
        """Initialize RulePackGenerator.

        Args:
            project_dir: Project directory path
            change_id: Optional change ID to include in templates
        """
        self.project_dir = Path(project_dir)
        self.change_id = change_id
        self.templates_dir = Path(__file__).parent / "templates"

    def generate_all(self) -> None:
        """Generate all rule pack files."""
        self.update_claude_md()
        self.generate_cursorrules()
        self.generate_cline_rules()

    def update_claude_md(self, change_id: Optional[str] = None) -> Path:
        """Update CLAUDE.md with spec-first collaboration section.

           Args:
           change_id: Optional change ID to include in template

        Returns:
               Path to updated CLAUDE.md
        """
        claude_md_path = self.project_dir / "CLAUDE.md"

        # Read template
        template = (self.templates_dir / "claude_code_rules.md").read_text(
            encoding="utf-8"
        )

        # Replace placeholders
        if change_id:
            template = template.replace("<change-id>", change_id)

        # Check if section already exists
        if claude_md_path.exists():
            content = claude_md_path.read_text(encoding="utf-8")
            marker_start = "## Spec-first Collaboration Rules"

            if marker_start in content:
                # Find section boundaries
                start_idx = content.find(marker_start)
                # Find next ## heading after this section
                next_section_idx = content.find("\n##", start_idx + 1)
                if next_section_idx == -1:
                    # This is the last section
                    content = content[:start_idx] + template
                else:
                    # Replace existing section
                    content = (
                        content[:start_idx]
                        + template
                        + "\n"
                        + content[next_section_idx:]
                    )
            else:
                # Append new section
                content += "\n\n" + template
        else:
            # Create new CLAUDE.md
            content = "# Project Documentation\n" + template

        claude_md_path.write_text(content, encoding="utf-8")
        return claude_md_path

    def generate_cursorrules(self) -> Path:
        """Generate .cursorrules file.

        Returns:
        Path to generated .cursorrules
        """
        cursorrules_path = self.project_dir / ".cursorrules"

        template = (self.templates_dir / "cursorrules.txt").read_text(encoding="utf-8")

        if self.change_id:
            template = template.replace("<change-id>", self.change_id)

        cursorrules_path.write_text(template, encoding="utf-8")
        return cursorrules_path

    def generate_cline_rules(self, change_id: Optional[str] = None) -> Path:
        """Generate cline-rules.md file.

        Args:
            change_id: Optional change ID to include in template

        Returns:
            Path to generated cline-rules.md
        """
        cline_rules_path = self.project_dir / "cline-rules.md"

        template = (self.templates_dir / "cline_rules.md").read_text(encoding="utf-8")

        if change_id:
            template = template.replace("<change-id>", change_id)

        cline_rules_path.write_text(template, encoding="utf-8")
        return cline_rules_path

    def remove_rule_pack(self) -> None:
        """Remove generated rule pack files (for cleanup)."""
        cursorrules_path = self.project_dir / ".cursorrules"
        cline_rules_path = self.project_dir / "cline-rules.md"

        if cursorrules_path.exists():
            cursorrules_path.unlink()

        if cline_rules_path.exists():
            cline_rules_path.unlink()
