from devpal.core.openspec_phases.base import OpenSpecContext
from devpal.core.openspec_phases.test_self_healer import TestSelfHealer
from devpal.vector_store.documents import VectorDocument


class _DummyClient:
    pass


class _FakeSemanticSearchService:
    stats = {
        "search_count": 2,
        "fallback_count": 0,
        "indexed_documents": 1,
        "retrieval_latency_ms": 0,
        "retrieved_context_count": 2,
        "last_result_count": 1,
    }
    similar_error_calls = []

    @classmethod
    def from_context(cls, context, log=None):
        return cls()

    def index_context(self, context, project_name):
        return 1

    def search_similar_errors(self, error_message, project_name, top_k=3, event_integration=None):
        self.similar_error_calls.append((error_message, project_name, top_k))
        return [
            VectorDocument(
                id="err-1",
                content="missing include for vector\nadd #include <vector>",
                metadata={"artifact_type": "error", "path": "error_memory"},
                score=0.95,
            )
        ]

    def build_context(self, query, project_name, artifact_types=None, top_k=5, event_integration=None):
        return "=== RETRIEVED RELATED CONTEXT ===\nsrc/main.cpp\n=== END RETRIEVED RELATED CONTEXT ==="


def test_self_healer_uses_similar_error_search(tmp_path, monkeypatch):
    context = OpenSpecContext(project_dir=tmp_path, requirements_file=tmp_path / "requirements.md")
    context.project_name = "cpp_demo"
    context.vector_retrieval_enabled = True
    context.vector_top_k = 5
    healer = TestSelfHealer(tmp_path, _DummyClient(), context=context)

    monkeypatch.setattr(
        "devpal.vector_store.semantic_search.SemanticSearchService",
        _FakeSemanticSearchService,
    )
    _FakeSemanticSearchService.similar_error_calls = []

    section = healer._build_retrieved_context_section("fatal error: vector: No such file or directory")

    assert _FakeSemanticSearchService.similar_error_calls == [
        ("fatal error: vector: No such file or directory", "cpp_demo", 3)
    ]
    assert "SIMILAR HISTORICAL ERRORS / FIX STRATEGIES" in section
    assert "add #include <vector>" in section
    assert "RETRIEVED RELATED CONTEXT" in section
    assert context.vector_retrieval_stats["retrieved_context_count"] == 2
