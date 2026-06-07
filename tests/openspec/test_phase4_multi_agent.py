# -*- coding: utf-8 -*-

from pathlib import Path

from devpal.core.multi_agent import AgentPolicy, CodegenAgent
from devpal.core.schema.delta_spec import DeltaSpec
from devpal.core.openspec_phases.base import OpenSpecContext
from devpal.core.openspec_phases.parallel_executor import ParallelTask
from devpal.core.openspec_phases.phase4_file_plan import FileGenerationPlanItem
from devpal.core.openspec_phases.phase4_generate_code import Phase4GenerateCode


class _DummyRegistry:
    pass


class _Usage:
    calls = 1
    input_tokens = 11
    output_tokens = 7
    cache_read_tokens = 3
    cache_creation_tokens = 2


class _ToolLoopResult:
    turns = 1
    stop_reason = "tool_use"


class _FakeClient:
    def __init__(self, content="generated", path=None):
        self.usage = _Usage()
        self.content = content
        self.path = path

    def generate_with_tool_loop(self, **kwargs):
        user_message = kwargs["user_message"]
        path = self.path
        if path is None:
            marker = "Generate exactly one file: "
            path = user_message.split(marker, 1)[1].split("\n", 1)[0]
        kwargs["tool_handler"](
            "write_file",
            {"path": path, "content": f"// {self.content} {path}\n"},
        )
        return _ToolLoopResult()


class _DiffClient(_FakeClient):
    def generate_with_tool_loop(self, **kwargs):
        user_message = kwargs["user_message"]
        marker = "Generate exactly one file: "
        path = user_message.split(marker, 1)[1].split("\n", 1)[0]
        kwargs["tool_handler"](
            "write_file",
            {
                "path": path,
                "content": "--- a/src/simple_login.py\n+++ b/src/simple_login.py\n@@ -1 +1 @@\n-old\n+new\n",
            },
        )
        return _ToolLoopResult()


class _MissingIncludeClient(_FakeClient):
    def generate_with_tool_loop(self, **kwargs):
        user_message = kwargs["user_message"]
        marker = "Generate exactly one file: "
        path = user_message.split(marker, 1)[1].split("\n", 1)[0]
        kwargs["tool_handler"](
            "write_file",
            {"path": path, "content": '#include "missing_local.h"\n\nclass Example {};\n'},
        )
        return _ToolLoopResult()


class _IncompletePublicTypeClient(_FakeClient):
    def generate_with_tool_loop(self, **kwargs):
        user_message = kwargs["user_message"]
        marker = "Generate exactly one file: "
        path = user_message.split(marker, 1)[1].split("\n", 1)[0]
        kwargs["tool_handler"](
            "write_file",
            {"path": path, "content": "struct Result;\n\nclass Service {\npublic:\n    Result run();\n};\n"},
        )
        return _ToolLoopResult()


def _make_context(project_dir: Path) -> OpenSpecContext:
    context = OpenSpecContext(
        project_dir=project_dir,
        requirements_file=project_dir / "requirements.md",
        requirements_content="Build login service",
        tech_design_content="Use a service class",
        project_name="simple_login",
        language="python",
    )
    context.enable_multi_agent = True
    context.agent_pool_size = 2
    context.sandbox_level = "staging"
    context.structured_requirements = [{"id": "REQ-1"}]
    return context


def test_codegen_agent_generates_content_without_writing_target(tmp_path):
    item = FileGenerationPlanItem(
        path="src/simple_login.py",
        purpose="module",
        stage="implementation",
    )
    task = ParallelTask(
        task_id="phase4:src/simple_login.py",
        phase_number=4,
        task_type="code_file",
        input_payload={
            "plan_item": item,
            "project_dir": tmp_path,
            "system_prompt": "system",
            "base_user_message": "base",
            "cached_context": [],
        },
    )
    policy = AgentPolicy(enabled=True, allowed_write_paths=[item.path])
    from devpal.core.multi_agent.adapters import parallel_task_to_agent_task

    agent_task = parallel_task_to_agent_task(task, policy, allowed_paths=[item.path])

    result = CodegenAgent(lambda: _FakeClient(), policy).execute(agent_task)

    assert result.success is True
    assert result.metadata["content"].startswith("// generated")
    assert not (tmp_path / item.path).exists()


def test_codegen_agent_rejects_diff_patch_content(tmp_path):
    item = FileGenerationPlanItem(
        path="src/simple_login.py",
        purpose="module",
        stage="implementation",
    )
    task = ParallelTask(
        task_id="phase4:src/simple_login.py",
        phase_number=4,
        task_type="code_file",
        input_payload={
            "plan_item": item,
            "project_dir": tmp_path,
            "system_prompt": "system",
            "base_user_message": "base",
            "cached_context": [],
        },
    )
    policy = AgentPolicy(enabled=True, allowed_write_paths=[item.path])
    from devpal.core.multi_agent.adapters import parallel_task_to_agent_task

    agent_task = parallel_task_to_agent_task(task, policy, allowed_paths=[item.path])

    result = CodegenAgent(lambda: _DiffClient(), policy).execute(agent_task)

    assert result.success is False
    assert "did not produce" in result.error
    assert not (tmp_path / item.path).exists()


def test_codegen_agent_rejects_unplanned_local_include(tmp_path):
    item = FileGenerationPlanItem(
        path="include/service.h",
        purpose="header",
        stage="headers",
    )
    task = ParallelTask(
        task_id="phase4:include/service.h",
        phase_number=4,
        task_type="code_file",
        input_payload={
            "plan_item": item,
            "project_dir": tmp_path,
            "system_prompt": "system",
            "base_user_message": "base",
            "cached_context": [],
            "planned_paths": ["include/service.h", "include/repository.h"],
        },
    )
    policy = AgentPolicy(enabled=True, allowed_write_paths=[item.path])
    from devpal.core.multi_agent.adapters import parallel_task_to_agent_task

    agent_task = parallel_task_to_agent_task(task, policy, allowed_paths=[item.path])

    result = CodegenAgent(lambda: _MissingIncludeClient(), policy).execute(agent_task)

    assert result.success is False
    assert "did not produce" in result.error
    assert not (tmp_path / item.path).exists()


def test_codegen_agent_rejects_public_header_incomplete_value_type(tmp_path):
    item = FileGenerationPlanItem(
        path="include/service.h",
        purpose="header",
        stage="headers",
    )
    task = ParallelTask(
        task_id="phase4:include/service.h",
        phase_number=4,
        task_type="code_file",
        input_payload={
            "plan_item": item,
            "project_dir": tmp_path,
            "system_prompt": "system",
            "base_user_message": "base",
            "cached_context": [],
            "planned_paths": ["include/service.h"],
        },
    )
    policy = AgentPolicy(enabled=True, allowed_write_paths=[item.path])
    from devpal.core.multi_agent.adapters import parallel_task_to_agent_task

    agent_task = parallel_task_to_agent_task(task, policy, allowed_paths=[item.path])

    result = CodegenAgent(lambda: _IncompletePublicTypeClient(), policy).execute(agent_task)

    assert result.success is False
    assert "did not produce" in result.error
    assert not (tmp_path / item.path).exists()


def test_phase4_multi_agent_generates_and_merges_files(tmp_path, monkeypatch):
    context = _make_context(tmp_path)
    phase = Phase4GenerateCode(context, _DummyRegistry())
    monkeypatch.setattr(phase, "_create_parallel_llm_client", lambda: _FakeClient())
    monkeypatch.setattr(phase.compiledb, "index_project", lambda *args, **kwargs: None)
    monkeypatch.setattr(phase.compiledb, "save_cache", lambda *args, **kwargs: None)
    monkeypatch.setattr(phase, "_update_artifact_graph", lambda *args, **kwargs: None)
    file_plan = [
        FileGenerationPlanItem(
            path="src/simple_login.py",
            purpose="module",
            stage="implementation",
        ),
        FileGenerationPlanItem(
            path="tests/test_simple_login.py",
            purpose="tests",
            stage="tests",
            dependencies=["src/simple_login.py"],
        ),
    ]

    result = phase._try_generate_files_multi_agent(
        file_plan=file_plan,
        project_dir=tmp_path,
        infra_files=[],
        infra_errors=[],
        system_prompt="system",
        base_user_message="base",
        cached_context=[],
    )

    assert result.success is True
    assert result.data["multi_agent"] is True
    assert result.data["ai_count"] == 2
    assert result.data["parallel_summary"]["total_tasks"] == 2
    assert context.parallel_execution_stats["4"]["success_count"] == 2
    assert (tmp_path / "src/simple_login.py").exists()
    assert (tmp_path / "tests/test_simple_login.py").exists()
    assert {path.relative_to(tmp_path).as_posix() for path in context.ai_generated_files} == {
        "src/simple_login.py",
        "tests/test_simple_login.py",
    }
    assert context.get_requirement_status("REQ-1") == "IN_PROGRESS"
    assert context.llm_calls == 2


def test_phase4_multi_agent_merge_preserves_complete_content_when_unchanged(tmp_path, monkeypatch):
    context = _make_context(tmp_path)
    phase = Phase4GenerateCode(context, _DummyRegistry())
    target = tmp_path / "src/simple_login.py"
    target.parent.mkdir(parents=True)
    target.write_text("// generated src/simple_login.py\n", encoding="utf-8")
    monkeypatch.setattr(phase, "_create_parallel_llm_client", lambda: _FakeClient())
    monkeypatch.setattr(phase.compiledb, "index_project", lambda *args, **kwargs: None)
    monkeypatch.setattr(phase.compiledb, "save_cache", lambda *args, **kwargs: None)
    monkeypatch.setattr(phase, "_update_artifact_graph", lambda *args, **kwargs: None)

    result = phase._try_generate_files_multi_agent(
        file_plan=[
            FileGenerationPlanItem(
                path="src/simple_login.py",
                purpose="module",
                stage="implementation",
            )
        ],
        project_dir=tmp_path,
        infra_files=[],
        infra_errors=[],
        system_prompt="system",
        base_user_message="base",
        cached_context=[],
    )

    assert result.success is True
    assert target.read_text(encoding="utf-8") == "// generated src/simple_login.py\n"


def test_delta_spec_apply_sets_new_content_not_diff_preview(tmp_path):
    target = tmp_path / "app.py"
    target.write_text("old\n", encoding="utf-8")
    delta_spec = DeltaSpec(target)
    delta_spec.load_original()
    for delta in delta_spec.create_delta_from_diff("new\n", reason="test"):
        delta_spec.add_delta(delta)

    result = delta_spec.apply(validate=True)

    assert result.success is True
    assert result.new_content == "new\n"
    assert "---" in result.diff_preview


def test_phase4_multi_agent_failure_restores_existing_target(tmp_path, monkeypatch):
    context = _make_context(tmp_path)
    phase = Phase4GenerateCode(context, _DummyRegistry())
    target = tmp_path / "src/simple_login.py"
    target.parent.mkdir(parents=True)
    target.write_text("original", encoding="utf-8")
    monkeypatch.setattr(phase, "_create_parallel_llm_client", lambda: _FakeClient(path="src/other.py"))
    file_plan = [
        FileGenerationPlanItem(
            path="src/simple_login.py",
            purpose="module",
            stage="implementation",
        )
    ]

    result = phase._try_generate_files_multi_agent(
        file_plan=file_plan,
        project_dir=tmp_path,
        infra_files=[],
        infra_errors=[],
        system_prompt="system",
        base_user_message="base",
        cached_context=[],
    )

    assert result.success is False
    assert target.read_text(encoding="utf-8") == "original"
