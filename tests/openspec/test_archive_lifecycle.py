import json

from devpal.core.openspec_phases.base import OpenSpecContext
from devpal.core.openspec_phases.phase11_final_report import Phase11FinalReport
from devpal.openspec.archive import ArchiveChangeService


def _make_change(project, change_id="add-calculator"):
    change_dir = project / "openspec" / "changes" / change_id
    specs_dir = change_dir / "specs"
    specs_dir.mkdir(parents=True)
    (change_dir / "proposal.md").write_text("# Proposal\n", encoding="utf-8")
    (change_dir / "tasks.md").write_text("- [x] implement calculator\n", encoding="utf-8")
    (change_dir / "design.md").write_text("# Design\n", encoding="utf-8")
    (specs_dir / "spec.md").write_text("### REQ-001\nCalculator add function\n", encoding="utf-8")
    (change_dir / "metadata.json").write_text(json.dumps({
        "change_id": change_id,
        "status": "IMPLEMENTED",
        "requirements": ["REQ-001"],
    }), encoding="utf-8")
    return change_dir


def _make_project(tmp_path):
    project = tmp_path / "cpp_calculator"
    (project / "src").mkdir(parents=True)
    (project / "tests").mkdir()
    (project / "docs").mkdir()
    (project / ".spec").mkdir()
    (project / "src" / "calculator.cpp").write_text("int add(int a, int b) { return a + b; }", encoding="utf-8")
    (project / "tests" / "test_calculator.cpp").write_text("int main() { return 0; }", encoding="utf-8")
    (project / "docs" / "final_report.md").write_text("# Final Report\n", encoding="utf-8")
    (project / ".spec" / "artifact_graph.json").write_text(json.dumps({
        "nodes": [
            {"id": "file:src/calculator.cpp", "type": "code", "metadata": {}},
            {"id": "file:tests/test_calculator.cpp", "type": "test", "metadata": {}},
        ],
        "edges": [],
    }), encoding="utf-8")
    _make_change(project)
    return project


class _EventIntegration:
    def __init__(self):
        self.events = []

    def emit_archive_event(self, event_name, payload):
        self.events.append((event_name, payload))


def test_archive_change_merges_spec_updates_metadata_and_manifest(tmp_path):
    project = _make_project(tmp_path)
    events = _EventIntegration()

    result = ArchiveChangeService(event_integration=events).archive_change(project, "add-calculator")

    assert result.success is True
    metadata = json.loads((project / "openspec" / "changes" / "add-calculator" / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["status"] == "ARCHIVED"
    assert metadata["merged_into"] == "openspec/specs/main.md"
    main_spec = (project / "openspec" / "specs" / "main.md").read_text(encoding="utf-8")
    assert "<!-- change:add-calculator -->" in main_spec
    assert "Calculator add function" in main_spec
    manifest = json.loads((project / ".spec" / "archive" / "add-calculator.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "ARCHIVED"
    assert manifest["coverage"]["coverage_percent"] == 100
    coverage_matrix = (project / ".spec" / "coverage_matrix.md").read_text(encoding="utf-8")
    assert "REQ-001" in coverage_matrix
    graph = json.loads((project / ".spec" / "artifact_graph.json").read_text(encoding="utf-8"))
    assert graph["nodes"][0]["metadata"]["change_id"] == "add-calculator"
    assert "completed" in [name for name, _ in events.events]


def test_archive_change_is_idempotent_for_spec_merge(tmp_path):
    project = _make_project(tmp_path)
    service = ArchiveChangeService()

    first = service.archive_change(project, "add-calculator")
    second = service.archive_change(project, "add-calculator")

    assert first.success is True
    assert second.success is True
    assert second.metadata["merged"] is False
    main_spec = (project / "openspec" / "specs" / "main.md").read_text(encoding="utf-8")
    assert main_spec.count("<!-- change:add-calculator -->") == 1


def test_archive_change_fails_when_change_missing(tmp_path):
    project = tmp_path / "project"
    project.mkdir()

    result = ArchiveChangeService().archive_change(project, "missing-change")

    assert result.success is False
    assert result.status == "FAILED"
    assert result.errors


def test_phase11_reports_archive_summary(tmp_path):
    project = _make_project(tmp_path)
    ArchiveChangeService().archive_change(project, "add-calculator")
    context = OpenSpecContext(project_dir=project, requirements_file=tmp_path / "requirements.md")

    result = Phase11FinalReport(context).execute()

    assert result.success is True
    report = (project / "docs" / "final_report.md").read_text(encoding="utf-8")
    assert "### Archive Summary" in report
    assert "add-calculator" in report
    assert "Coverage matrix" in report
