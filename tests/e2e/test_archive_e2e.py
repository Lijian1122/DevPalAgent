# -*- coding: utf-8 -*-
"""End-to-end test for Archive + Traceability lifecycle."""

import json
import subprocess


def test_archive_cli_command(tmp_path):
    """Test archive command via CLI."""
    project = tmp_path / "test_project"
    project.mkdir()
    (project / "src").mkdir()
    (project / "tests").mkdir()
    (project / "docs").mkdir()
    (project / ".spec").mkdir()

    change_id = "feature-001"
    change_dir = project / "openspec" / "changes" / change_id
    specs_dir = change_dir / "specs"
    specs_dir.mkdir(parents=True)

    (change_dir / "proposal.md").write_text("# Feature 001\n", encoding="utf-8")
    (change_dir / "tasks.md").write_text("- [x] Task 1\n", encoding="utf-8")
    (change_dir / "design.md").write_text("# Design\n", encoding="utf-8")
    (specs_dir / "spec.md").write_text(
        "### REQ-001\nFeature description.\n", encoding="utf-8"
    )

    metadata = {
        "change_id": change_id,
        "status": "IMPLEMENTED",
        "requirements": ["REQ-001"],
    }
    (change_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    (project / "src" / "feature.cpp").write_text("void feature() {}", encoding="utf-8")
    (project / "tests" / "test_feature.cpp").write_text(
        "int main() { return 0; }", encoding="utf-8"
    )
    (project / "docs" / "final_report.md").write_text("# Report\n", encoding="utf-8")

    artifact_graph = {
        "nodes": [
            {"id": "file:src/feature.cpp", "type": "code", "metadata": {}},
            {"id": "file:tests/test_feature.cpp", "type": "test", "metadata": {}},
        ],
        "edges": [],
    }
    (project / ".spec" / "artifact_graph.json").write_text(
        json.dumps(artifact_graph), encoding="utf-8"
    )

    result = subprocess.run(
        [
            "python",
            "-m",
            "devpal.openspec",
            "archive",
            change_id,
            "--project-dir",
            str(project),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 0, f"Archive failed: {result.stderr}"
    archive_result = json.loads(result.stdout)
    assert archive_result["success"] is True
    assert archive_result["status"] == "ARCHIVED"

    updated_metadata = json.loads(
        (change_dir / "metadata.json").read_text(encoding="utf-8")
    )
    assert updated_metadata["status"] == "ARCHIVED"
    assert "archived_at" in updated_metadata

    main_spec_path = project / "openspec" / "specs" / "main.md"
    assert main_spec_path.exists()
    main_spec = main_spec_path.read_text(encoding="utf-8")
    assert f"<!-- change:{change_id} -->" in main_spec
    assert "REQ-001" in main_spec

    coverage_path = project / ".spec" / "coverage_matrix.md"
    assert coverage_path.exists()

    manifest_path = project / ".spec" / "archive" / f"{change_id}.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["change_id"] == change_id
    assert manifest["status"] == "ARCHIVED"

    updated_graph = json.loads(
        (project / ".spec" / "artifact_graph.json").read_text(encoding="utf-8")
    )
    for node in updated_graph["nodes"]:
        assert "change_id" in node["metadata"]
        assert node["metadata"]["change_id"] == change_id

    assert "archive" in updated_graph
    assert change_id in updated_graph["archive"]
