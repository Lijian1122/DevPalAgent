# -*- coding: utf-8 -*-
"""Content sanitation helpers for generated source files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable


def _strip_outer_code_fence(content: str) -> tuple[str, bool]:
    stripped = content.strip()
    if not stripped.startswith("```"):
        return content, False
    lines = stripped.splitlines()
    if len(lines) < 3 or not lines[-1].strip().startswith("```"):
        return content, False
    return "\n".join(lines[1:-1]) + "\n", True


def find_unified_diff_marker(content: str) -> tuple[int, str] | None:
    content, _ = _strip_outer_code_fence(content)
    lines = content.lstrip("﻿ \t\r\n").splitlines()
    if not lines:
        return None

    scan_limit = min(len(lines), 20)
    for idx, line in enumerate(lines[:scan_limit], 1):
        marker = line.strip()
        if marker.startswith(("diff --git ", "--- ", "+++ ", "@@")):
            return idx, marker[:80]

    for idx in range(scan_limit - 1):
        current = lines[idx].strip()
        nxt = lines[idx + 1].strip()
        if current.startswith("--- ") and nxt.startswith("+++ "):
            return idx + 1, current[:80]
    return None


def has_unified_diff_markers(content: str) -> bool:
    return find_unified_diff_marker(content) is not None


def unified_diff_to_content(content: str) -> str:
    content, stripped_fence = _strip_outer_code_fence(content)
    if not has_unified_diff_markers(content):
        return content if stripped_fence else content

    output_lines: list[str] = []
    in_hunk = False
    for raw_line in content.splitlines(keepends=True):
        line = raw_line.rstrip("\r\n")
        newline = raw_line[len(line) :]
        if line.startswith(("diff --git ", "index ", "--- ", "+++ ")):
            continue
        if line.startswith("@@"):
            in_hunk = True
            continue
        if not in_hunk:
            continue
        if line.startswith("+"):
            output_lines.append(line[1:] + newline)
        elif line.startswith(" "):
            output_lines.append(line[1:] + newline)
        elif line.startswith("-"):
            continue
        elif line == "\\ No newline at end of file":
            continue
        else:
            output_lines.append(raw_line)
    return "".join(output_lines)


def sanitize_generated_content(content: str) -> tuple[str, bool]:
    sanitized = unified_diff_to_content(content)
    return sanitized, sanitized != content


def missing_local_includes(
    content: str,
    current_path: str,
    project_dir: Path,
    planned_paths: Iterable[str] = (),
) -> list[str]:
    planned = {Path(path).as_posix() for path in planned_paths}
    current = Path(current_path)
    missing = []
    for include in re.findall(r'^\s*#\s*include\s+"([^"]+)"', content, re.MULTILINE):
        candidates = [
            (current.parent / include).as_posix(),
            (Path("include") / include).as_posix(),
            Path(include).as_posix(),
        ]
        if any(candidate in planned or (project_dir / candidate).exists() for candidate in candidates):
            continue
        missing.append(include)
    return sorted(set(missing))


def cpp_header_public_incomplete_type_errors(content: str) -> list[str]:
    forward_declared = set(
        re.findall(r"^\s*(?:struct|class|enum\s+class|enum)\s+([A-Za-z_]\w*)\s*;\s*$", content, re.MULTILINE)
    )
    if not forward_declared:
        return []

    errors = []
    body = re.sub(
        r"^\s*(?:struct|class|enum\s+class|enum)\s+[A-Za-z_]\w*\s*;\s*$",
        "",
        content,
        flags=re.MULTILINE,
    )
    for name in sorted(forward_declared):
        by_value_return = re.search(rf"\b{name}\s+[A-Za-z_]\w*\s*\(", body)
        by_value_param = re.search(rf"[(,]\s*(?:const\s+)?{name}\s+[A-Za-z_]\w*", body)
        by_value_field = re.search(rf"^\s*(?:const\s+)?{name}\s+[A-Za-z_]\w*\s*[;=]", body, re.MULTILINE)
        if by_value_return or by_value_param or by_value_field:
            errors.append(
                f"{name} is only forward-declared but used by value in a public header"
            )
    return errors


def _issue(path: Path, content: str) -> dict[str, object]:
    marker = find_unified_diff_marker(content)
    line, text = marker if marker else (0, "")
    return {"path": str(path), "line": line, "marker": text}


def detect_diff_pollution_in_files(paths: Iterable[Path]) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    for path in sorted({Path(p) for p in paths}, key=lambda p: p.as_posix()):
        if not path.exists() or not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            issues.append({"path": str(path), "line": 0, "marker": f"read_error: {exc}"})
            continue
        if has_unified_diff_markers(content):
            issues.append(_issue(path, content))
    return issues


def sanitize_landed_generated_files(paths: Iterable[Path]) -> dict[str, list[dict[str, object]]]:
    report: dict[str, list[dict[str, object]]] = {
        "sanitized": [],
        "remaining": [],
        "errors": [],
    }
    for path in sorted({Path(p) for p in paths}, key=lambda p: p.as_posix()):
        if not path.exists() or not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            report["errors"].append({"path": str(path), "line": 0, "marker": str(exc)})
            continue
        if not has_unified_diff_markers(content):
            continue

        issue = _issue(path, content)
        sanitized, changed = sanitize_generated_content(content)
        if changed and sanitized.strip():
            path.write_text(sanitized, encoding="utf-8")
            if has_unified_diff_markers(sanitized):
                report["remaining"].append(_issue(path, sanitized))
            else:
                report["sanitized"].append(issue)
        else:
            report["remaining"].append(issue)
    return report
