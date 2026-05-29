from pathlib import Path

from devpal.vector_store.documents import VectorDocument
from devpal.vector_store.embeddings import MockEmbeddingProvider
from devpal.vector_store.indexer import ProjectArtifactIndexer
from devpal.vector_store.semantic_search import SemanticSearchService
from devpal.vector_store.vector_db import DisabledVectorStore, create_vector_store


def test_mock_embedding_is_deterministic():
    provider = MockEmbeddingProvider(dimensions=16)
    assert provider.embed_text("Login password") == provider.embed_text("Login password")
    assert len(provider.embed_text("Login password")) == 16


def test_vector_store_disabled_returns_empty():
    store = create_vector_store(enabled=False)
    assert isinstance(store, DisabledVectorStore)
    assert store.search("anything") == []


def test_markdown_chunking_keeps_metadata(tmp_path):
    project = tmp_path / "project"
    req_dir = project / "requirements"
    req_dir.mkdir(parents=True)
    req = req_dir / "login.md"
    req.write_text("# Login\n\nPassword validation\n\n## Security\nHash passwords", encoding="utf-8")

    indexer = ProjectArtifactIndexer(max_chunk_chars=40)
    docs = indexer.index_file(req, project, "demo", "requirements", language="cpp")

    assert docs
    assert docs[0].metadata["project_name"] == "demo"
    assert docs[0].metadata["artifact_type"] == "requirements"
    assert docs[0].metadata["path"] == "requirements/login.md"
    assert "hash" in docs[0].metadata


def test_code_file_indexing_keeps_path_and_hash(tmp_path):
    project = tmp_path / "project"
    src = project / "src"
    src.mkdir(parents=True)
    file_path = src / "login.cpp"
    file_path.write_text("bool validate_password() { return true; }", encoding="utf-8")

    docs = ProjectArtifactIndexer().index_file(file_path, project, "demo", "source", language="cpp")

    assert len(docs) == 1
    assert docs[0].metadata["path"] == "src/login.cpp"
    assert docs[0].metadata["phase_number"] == 4


def test_semantic_search_returns_empty_when_disabled(tmp_path):
    service = SemanticSearchService(enabled=False, persist_dir=tmp_path)
    assert service.build_context("login", "demo") == ""
    assert service.stats["fallback_count"] == 1


def test_semantic_search_build_context_format(tmp_path):
    project = tmp_path / "project"
    src = project / "src"
    src.mkdir(parents=True)
    file_path = src / "login.cpp"
    file_path.write_text("bool validate_password() { return true; }", encoding="utf-8")

    service = SemanticSearchService(enabled=True, persist_dir=tmp_path, prefer_chroma=False)
    count = service.index_project(project, "demo", language="cpp")
    context = service.build_context("password validation", "demo", artifact_types=["source"], top_k=1)

    assert count == 1
    assert "=== RETRIEVED RELATED CONTEXT ===" in context
    assert "src/login.cpp" in context
    assert "validate_password" in context


def test_index_context_includes_external_requirements_file(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    requirements = tmp_path / "requirements.md"
    requirements.write_text("Calculator add two integers", encoding="utf-8")
    context = type("Context", (), {})()
    context.project_dir = project
    context.requirements_file = requirements
    context.current_change_dir = None
    context.language = "cpp"

    service = SemanticSearchService(enabled=True, persist_dir=tmp_path, prefer_chroma=False)
    count = service.index_context(context, "demo")
    retrieved = service.build_context("add integers", "demo", artifact_types=["requirements"], top_k=1)

    assert count == 1
    assert "Calculator add two integers" in retrieved


def test_index_project_replaces_stale_documents(tmp_path):
    project = tmp_path / "project"
    src = project / "src"
    src.mkdir(parents=True)
    file_path = src / "calculator.cpp"
    file_path.write_text("int add(int a, int b) { return a + b; }", encoding="utf-8")

    service = SemanticSearchService(enabled=True, persist_dir=tmp_path, prefer_chroma=False)
    assert service.index_project(project, "demo", language="cpp") == 1
    file_path.write_text("int subtract(int a, int b) { return a - b; }", encoding="utf-8")
    assert service.index_project(project, "demo", language="cpp") == 1

    retrieved = service.build_context("calculator", "demo", artifact_types=["source"], top_k=5)

    assert "subtract" in retrieved
    assert "return a + b" not in retrieved


def test_multi_artifact_search_overfetches_before_filtering(tmp_path):
    from devpal.vector_store.vector_db import InMemoryVectorStore

    service = SemanticSearchService(enabled=True, persist_dir=tmp_path, prefer_chroma=False)
    service.store = InMemoryVectorStore(service.embedding_provider)
    docs = []
    for index in range(5):
        docs.append(VectorDocument(
            id=f"report-{index}",
            content="calculator add integers",
            metadata={"project_name": "demo", "artifact_type": "report", "path": f"docs/{index}.md"},
        ))
    docs.append(VectorDocument(
        id="source-1",
        content="calculator add integers",
        metadata={"project_name": "demo", "artifact_type": "source", "path": "src/calculator.cpp"},
    ))
    service.store.upsert(docs)

    results = service.search("calculator add integers", "demo", artifact_types=["source", "test"], top_k=1)

    assert len(results) == 1
    assert results[0].metadata["artifact_type"] == "source"


def test_error_memory_documents_can_be_searched(tmp_path):
    service = SemanticSearchService(enabled=True, persist_dir=tmp_path, prefer_chroma=False)
    records = [
        {
            "type": "compile_error",
            "description": "missing include for vector",
            "correction": "add #include <vector>",
            "context": "C++ STL header",
            "severity": 7,
            "timestamp": 1,
        }
    ]
    docs = service.indexer.index_error_memory(records, "demo")
    service.store.upsert(docs)

    results = service.search_similar_errors("vector header compile error", "demo")

    assert results
    assert results[0].metadata["artifact_type"] == "error"
