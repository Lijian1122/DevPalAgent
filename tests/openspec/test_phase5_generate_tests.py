from devpal.core.openspec_phases.base import OpenSpecContext
from devpal.core.openspec_phases.phase5_generate_tests import Phase5GenerateTests


class _ToolResult:
    def __init__(self, success, error_message="", content="", metadata=None):
        self.success = success
        self.error_message = error_message
        self.content = content
        self.metadata = metadata or {}


class _Registry:
    def __init__(self):
        self.calls = []

    def execute_tool(self, name, payload):
        self.calls.append((name, payload))
        if payload["test_file"].endswith("test_bad.cpp"):
            return _ToolResult(False, error_message="doc generation failed")
        output_doc = payload["output_doc"]
        return _ToolResult(True, metadata={"test_cases_generated": 1, "output_doc": output_doc})


def test_phase5_failure_isolation_records_partial_success(tmp_path):
    project = tmp_path / "cpp_demo"
    tests_dir = project / "tests"
    src_dir = project / "src"
    tests_dir.mkdir(parents=True)
    src_dir.mkdir()
    (tests_dir / "test_bad.cpp").write_text("int main() { return 0; }", encoding="utf-8")
    (tests_dir / "test_good.cpp").write_text("int main() { return 0; }", encoding="utf-8")
    (src_dir / "good.cpp").write_text("int good() { return 1; }", encoding="utf-8")

    context = OpenSpecContext(project_dir=project, requirements_file=tmp_path / "requirements.md")
    context.language = "cpp"
    context.phase5_max_concurrency = 2
    registry = _Registry()

    result = Phase5GenerateTests(context, registry).execute()

    assert result.success is True
    assert len(registry.calls) == 3
    assert len(context.test_docs) == 1
    assert context.test_docs[0].endswith("test_test_good_doc.md")
    assert result.data["parallel_summary"]["total_tasks"] == 2
    assert result.data["parallel_summary"]["success_count"] == 1
    assert result.data["parallel_summary"]["failed_count"] == 1
    assert any("test_bad.cpp" in error for error in result.data["errors"])
    assert context.test_doc_summary["test_count"] == 2
    assert context.test_doc_summary["docs_generated"] == 1
    assert result.data["test_doc_summary"] == context.test_doc_summary
