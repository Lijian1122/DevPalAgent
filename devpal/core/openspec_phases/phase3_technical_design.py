# -*- coding: utf-8 -*-
"""Phase 3: 调用 AI 生成技术设计文档.

输入: context.requirements_content (Phase 1 产出的需求文档)
输出: docs/技术实现文档.md  +  context.tech_design_content (供 Phase 4/10 复用)
"""

import hashlib
import json

from .base import PhaseInterface, PhaseResult, OpenSpecContext
from ..llm_client import get_llm_client
from ..prompts import get_prompt_engine


class Phase3TechnicalDesign(PhaseInterface):
    """Phase 3: AI 生成技术设计文档."""

    def __init__(self, context: OpenSpecContext):
        super().__init__(context)
        self.phase_number = 3
        self.phase_name = "生成技术设计文档"

    def should_skip(self) -> tuple:
        """判断是否应该跳过当前阶段"""
        from .phase_skip_rules import should_skip_for_non_cpp_project
        return should_skip_for_non_cpp_project(self.phase_number, self.context)

    def execute(self) -> PhaseResult:
        self.log("调用 AI 生成技术设计文档...")

        if not self.context.requirements_content:
            return PhaseResult.fail(
                "requirements_content 为空,Phase 1 是否成功?",
                errors=["context.requirements_content is empty"],
            )

        cached = self._load_cached_design()
        if cached:
            tech_design, tech_doc_path = cached
            self.context.tech_design_content = tech_design
            self.context.generated_files.append(tech_doc_path)
            self._write_design_to_change_dir(tech_design)
            self.log(f"  [CACHE] reused technical design: {tech_doc_path} ({len(tech_design)} chars)")
            return PhaseResult.ok(
                "技术设计文档复用成功",
                file_path=str(tech_doc_path),
                content_length=len(tech_design),
                llm_calls=0,
                cache_hit=True,
            )

        try:
            client = get_llm_client()
        except Exception as exc:
            self.log(f"  [FAIL] LLM 客户端初始化失败: {exc}")
            return PhaseResult.fail(
                f"LLM 客户端初始化失败: {exc}",
                errors=[str(exc)],
            )

        user_message = (
            "以下是软件需求文档,请按系统提示中的格式输出技术设计文档.\n"
            "\n=== 需求文档开始 ===\n"
        )
        cached_context = [self.context.requirements_content]

        # Use Prompt engine to generate dynamic System Prompt based on language
        prompt_engine = get_prompt_engine()
        system_prompt = prompt_engine.generate_design_prompt(
            language=self.context.language,
            features=getattr(self.context, 'features', None),
        )

        try:
            tech_design = client.generate(
                system=system_prompt,
                user_message=user_message,
                cached_context=cached_context,
                max_tokens=3072,
            )
        except Exception as exc:
            self.log(f"  [FAIL] AI 调用失败: {exc}")
            return PhaseResult.fail(
                f"AI 生成技术设计失败: {exc}",
                errors=[str(exc)],
            )

        if not tech_design.strip():
            return PhaseResult.fail(
                "AI 返回空文档",
                errors=["empty AI response"],
            )

        self._update_usage_stats(client)

        tech_doc_path = self.context.project_dir / "docs" / "技术实现文档.md"
        tech_doc_path.parent.mkdir(parents=True, exist_ok=True)
        tech_doc_path.write_text(tech_design, encoding="utf-8")
        self._write_design_cache_metadata(tech_doc_path, tech_design)

        self.context.tech_design_content = tech_design
        self.context.generated_files.append(tech_doc_path)

        # M2: Also write to change directory if it exists
        self._write_design_to_change_dir(tech_design)

        self.log(f"  [OK] 技术设计文档生成: {tech_doc_path} ({len(tech_design)} chars)")
        return PhaseResult.ok(
            "技术设计文档生成成功",
            file_path=str(tech_doc_path),
            content_length=len(tech_design),
            llm_calls=client.usage.calls,
        )

    def _load_cached_design(self):
        if getattr(self.context, "force_regenerate_design", False):
            return None
        tech_doc_path = self.context.project_dir / "docs" / "技术实现文档.md"
        metadata_path = self._design_cache_metadata_path()
        if not tech_doc_path.exists() or not metadata_path.exists():
            return None
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception:
            return None
        if metadata.get("requirements_hash") != self._requirements_hash():
            return None
        if metadata.get("language") != self.context.language:
            return None
        if metadata.get("project_type") != self.context.project_type:
            return None
        if metadata.get("features") != list(self.context.features or []):
            return None
        tech_design = tech_doc_path.read_text(encoding="utf-8")
        if not tech_design.strip():
            return None
        return tech_design, tech_doc_path

    def _write_design_cache_metadata(self, tech_doc_path, tech_design: str) -> None:
        metadata_path = self._design_cache_metadata_path()
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata = {
            "requirements_hash": self._requirements_hash(),
            "language": self.context.language,
            "project_type": self.context.project_type,
            "features": list(self.context.features or []),
            "design_path": tech_doc_path.as_posix(),
            "content_hash": hashlib.sha256(tech_design.encode("utf-8")).hexdigest(),
            "content_length": len(tech_design),
        }
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    def _design_cache_metadata_path(self):
        return self.context.project_dir / ".spec" / "tech_design_cache.json"

    def _requirements_hash(self) -> str:
        return hashlib.sha256(self.context.requirements_content.encode("utf-8")).hexdigest()

    def _update_usage_stats(self, client) -> None:
        """Sync LLM usage stats from client to context."""
        ctx = self.context
        ctx.llm_calls = client.usage.calls
        ctx.llm_input_tokens = client.usage.input_tokens
        ctx.llm_output_tokens = client.usage.output_tokens
        ctx.llm_cache_read_tokens = client.usage.cache_read_tokens
        ctx.llm_cache_creation_tokens = client.usage.cache_creation_tokens

    def _write_design_to_change_dir(self, design_content: str):
        """Write design to change directory if it exists (M2 implementation)"""
        if not self.context.current_change_dir:
            return

        design_path = self.context.current_change_dir / "design.md"
        design_path.write_text(design_content, encoding="utf-8")
        self.context.generated_files.append(design_path)
        self.log(f"  [M2] Design written to change directory: openspec/changes/{self.context.current_change_id}/design.md")
