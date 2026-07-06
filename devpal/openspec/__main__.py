# -*- coding: utf-8 -*-
"""CLI for OpenSpec lifecycle operations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .archive import ArchiveChangeService
from .sandbox_merge import SandboxMergeService
from devpal.core.sandbox.copy_out import SandboxCopyOutService


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DevPal OpenSpec lifecycle commands")
    subparsers = parser.add_subparsers(dest="command", required=True)

    archive_parser = subparsers.add_parser("archive", help="Archive an OpenSpec change")
    archive_parser.add_argument("change_id", help="Change id under openspec/changes/")
    archive_parser.add_argument("--project-dir", default=".", help="Project directory (default: current directory)")

    merge_parser = subparsers.add_parser("merge-sandbox", help="Preview or apply a pending sandbox merge")
    merge_parser.add_argument("manifest_path", help="Path to a sandbox manifest.json")
    merge_parser.add_argument("--project-dir", default=".", help="Project directory (default: current directory)")
    merge_parser.add_argument("--apply", action="store_true", help="Apply the merge to the project target file")

    copy_out_parser = subparsers.add_parser(
        "apply-copy-out",
        help="Preview or apply a sandbox copy-out manifest",
    )
    copy_out_parser.add_argument("manifest_path", help="Path to copy_out_manifest.json")
    copy_out_parser.add_argument("--project-dir", default=".", help="Project directory (default: current directory)")
    copy_out_parser.add_argument("--apply", action="store_true", help="Apply copy-out artifacts to the project")

    args = parser.parse_args(argv)
    if args.command == "archive":
        result = ArchiveChangeService().archive_change(Path(args.project_dir), args.change_id)
        sys.stdout.buffer.write(json.dumps(result.to_dict(), ensure_ascii=False, indent=2).encode("utf-8"))
        sys.stdout.buffer.write(b"\n")
        return 0 if result.success else 1
    if args.command == "merge-sandbox":
        result = SandboxMergeService().merge_manifest(
            Path(args.project_dir),
            Path(args.manifest_path),
            apply=args.apply,
        )
        sys.stdout.buffer.write(json.dumps(result.to_dict(), ensure_ascii=False, indent=2).encode("utf-8"))
        sys.stdout.buffer.write(b"\n")
        return 0 if result.success else 1
    if args.command == "apply-copy-out":
        result = SandboxCopyOutService().apply_manifest(
            Path(args.project_dir),
            Path(args.manifest_path),
            apply=args.apply,
        )
        sys.stdout.buffer.write(json.dumps(result.to_dict(), ensure_ascii=False, indent=2).encode("utf-8"))
        sys.stdout.buffer.write(b"\n")
        return 0 if result.success else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
