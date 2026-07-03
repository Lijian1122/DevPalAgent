# -*- coding: utf-8 -*-

import os

from devpal.core.compiler_detector import _select_path_with_executable


def test_select_path_with_executable_prefers_candidate_that_contains_tool(tmp_path):
    old_path = tmp_path / "old"
    tool_path = tmp_path / "tool"
    old_path.mkdir()
    tool_path.mkdir()
    (tool_path / "cl.exe").write_text("", encoding="utf-8")

    selected = _select_path_with_executable(
        [
            str(tool_path),
            str(old_path),
        ],
        "cl.exe",
    )

    assert selected == str(tool_path)


def test_select_path_with_executable_falls_back_to_last_candidate(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()

    selected = _select_path_with_executable(
        [
            str(first),
            str(second),
        ],
        "cl.exe",
    )

    assert selected == str(second)


def test_select_path_with_executable_checks_path_entries(tmp_path):
    first_entry = tmp_path / "first_entry"
    second_entry = tmp_path / "second_entry"
    first_entry.mkdir()
    second_entry.mkdir()
    (second_entry / "cl.exe").write_text("", encoding="utf-8")
    candidate = os.pathsep.join([str(first_entry), str(second_entry)])

    selected = _select_path_with_executable([candidate], "cl.exe")

    assert selected == candidate
