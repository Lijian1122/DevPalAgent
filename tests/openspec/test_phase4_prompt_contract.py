# -*- coding: utf-8 -*-

from devpal.core.openspec_phases.base import OpenSpecContext
from devpal.core.openspec_phases.phase4_generate_code import Phase4GenerateCode
from devpal.core.prompts.prompt_engine import get_prompt_engine
from devpal.vector_store.documents import VectorDocument


class _DummyRegistry:
    pass


class _FakeSearchStore:
    enabled = True

    def __init__(self, documents):
        self.documents = documents

    def upsert(self, documents):
        self.documents.extend(documents)

    def search(self, query, top_k=5, filters=None):
        return self.documents[:top_k]

    def delete_by_project(self, project_name):
        return None


def _make_phase4_context(tmp_path):
    context = OpenSpecContext(
        project_dir=tmp_path,
        requirements_file=tmp_path / "requirements.md",
        requirements_content="Build login password validation",
        tech_design_content="Use LoginService",
        project_name="cpp_simple_login",
        language="cpp",
    )
    context.vector_prefer_chroma = False
    return context


def test_phase4_system_prompt_includes_cpp_requirements():
    """Test that C++ code generation prompt includes key requirements"""
    engine = get_prompt_engine()
    prompt = engine.generate_code_gen_prompt('cpp')

    # Check file structure requirements
    assert "include/<name>.h" in prompt
    assert "src/<name>.cpp" in prompt
    assert "tests/test_<class>.cpp" in prompt

    # Check constructor requirements
    assert "default constructor" in prompt
    assert "parameterized constructors" in prompt

    # Check third-party library constraint
    assert "ONLY C++17 STL" in prompt or "NO third-party libraries" in prompt


def test_phase4_prompt_includes_best_practices():
    """Test that prompt includes C++ best practices"""
    engine = get_prompt_engine()
    prompt = engine.generate_code_gen_prompt('cpp')

    # Check best practices are included
    assert "C++17" in prompt
    assert "STL" in prompt or "standard library" in prompt


def test_phase4_prompt_includes_naming_conventions():
    """Test that prompt includes naming conventions"""
    engine = get_prompt_engine()
    prompt = engine.generate_code_gen_prompt('cpp')

    # Check naming conventions
    assert "PascalCase" in prompt
    assert "snake_case" in prompt


def test_phase4_retrieved_context_is_empty_by_default(tmp_path):
    context = _make_phase4_context(tmp_path)
    phase = Phase4GenerateCode(context, _DummyRegistry())

    assert phase._build_retrieved_context_section(context.project_name) == ""
    assert context.vector_retrieval_enabled is False


def test_phase4_retrieved_context_can_be_injected_when_enabled(tmp_path, monkeypatch):
    context = _make_phase4_context(tmp_path)
    context.vector_retrieval_enabled = True
    context.vector_top_k = 1
    phase = Phase4GenerateCode(context, _DummyRegistry())
    document = VectorDocument(
        id="doc-1",
        content="Existing LoginService validates password length.",
        metadata={"path": "src/login_service.cpp", "artifact_type": "source"},
        score=0.9,
    )

    def fake_from_context(cls, context, log=None):
        service = cls(enabled=True, prefer_chroma=False, log=log)
        service.store = _FakeSearchStore([document])
        return service

    monkeypatch.setattr(
        "devpal.vector_store.semantic_search.SemanticSearchService.from_context",
        classmethod(fake_from_context),
    )

    section = phase._build_retrieved_context_section(context.project_name)

    assert "=== RETRIEVED RELATED CONTEXT ===" in section
    assert "src/login_service.cpp" in section
    assert "Existing LoginService validates password length" in section
    assert context.vector_retrieval_stats["search_count"] == 1


def test_phase4_retrieved_context_indexes_project_artifacts_and_records_empty_stats(tmp_path):
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    (source_dir / "login_service.cpp").write_text(
        "bool LoginService::validatePassword() { return true; }",
        encoding="utf-8",
    )
    context = _make_phase4_context(tmp_path)
    context.vector_retrieval_enabled = True
    context.vector_top_k = 1
    phase = Phase4GenerateCode(context, _DummyRegistry())

    section = phase._build_retrieved_context_section(context.project_name)

    assert "=== RETRIEVED RELATED CONTEXT ===" in section
    assert "src/login_service.cpp" in section
    assert "validatePassword" in section
    assert context.vector_retrieval_stats["indexed_documents"] == 1
    assert context.vector_retrieval_stats["search_count"] == 1


def test_phase4_retrieved_context_records_empty_search_stats(tmp_path):
    context = _make_phase4_context(tmp_path)
    context.vector_retrieval_enabled = True
    phase = Phase4GenerateCode(context, _DummyRegistry())

    section = phase._build_retrieved_context_section(context.project_name)

    assert section == ""
    assert context.vector_retrieval_stats["search_count"] == 1
