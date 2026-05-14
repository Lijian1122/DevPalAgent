# -*- coding: utf-8 -*-
"""Phase 3: 调用 AI 生成技术设计文档.

输入: context.requirements_content (Phase 1 产出的需求文档)
输出: docs/技术实现文档.md  +  context.tech_design_content (供 Phase 4/10 复用)
"""

from .base import PhaseInterface, PhaseResult, OpenSpecContext
from ..llm_client import get_llm_client


_SYSTEM_PROMPT = (
    "You are a senior C++ architect. Given a software requirements document, "
    "produce a structured technical design in Markdown.\n\n"
    "CRITICAL RULES:\n"
    "1. Your FIRST character must be '#' (the start of the Markdown heading)\n"
    "2. DO NOT output ANY thinking process, analysis, or preamble\n"
    "3. DO NOT use <thinking> tags or any XML tags\n"
    "4. Start DIRECTLY with: # 技术设计文档\n\n"
    "The design MUST include the following sections in this order:\n"
    "1. 系统架构概览 (modules, layering, dataflow)\n"
    "2. 核心类清单 (one bullet per class: name, responsibility, key members/methods)\n"
    "3. 关键 API 定义 (signatures with parameter/return semantics)\n"
    "4. 数据结构与持久化\n"
    "5. 安全与并发设计\n"
    "6. 文件组织 (which .h/.cpp files map to which classes)\n"
    "7. 测试策略\n\n"
    "Constraints:\n"
    "- C++17 STL only, no third-party deps unless requirement mandates.\n"
    "- Each class lives in its own pair of include/<name>.h and src/<name>.cpp.\n"
    "- File names use snake_case; class names use PascalCase.\n"
    "- Be concrete: name actual classes, methods, file paths. No placeholders.\n"
    "- Keep total length under 3000 words.\n"
)


class Phase3TechnicalDesign(PhaseInterface):
    """Phase 3: AI 生成技术设计文档."""

    def __init__(self, context: OpenSpecContext):
        super().__init__(context)
        self.phase_number = 3
        self.phase_name = "生成技术设计文档"

    def execute(self) -> PhaseResult:
        self.log("调用 AI 生成技术设计文档...")

        if not self.context.requirements_content:
            return PhaseResult.fail(
                "requirements_content 为空,Phase 1 是否成功?",
                errors=["context.requirements_content is empty"],
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

        try:
            tech_design = client.generate(
                system=_SYSTEM_PROMPT,
                user_message=user_message,
                cached_context=cached_context,
                max_tokens=8192,
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

        self.context.tech_design_content = tech_design
        self.context.generated_files.append(tech_doc_path)

        self.log(f"  [OK] 技术设计文档生成: {tech_doc_path} ({len(tech_design)} chars)")
        return PhaseResult.ok(
            "技术设计文档生成成功",
            file_path=str(tech_doc_path),
            content_length=len(tech_design),
            llm_calls=client.usage.calls,
        )

    def _update_usage_stats(self, client) -> None:
        """Sync LLM usage stats from client to context."""
        ctx = self.context
        ctx.llm_calls = client.usage.calls
        ctx.llm_input_tokens = client.usage.input_tokens
        ctx.llm_output_tokens = client.usage.output_tokens
        ctx.llm_cache_read_tokens = client.usage.cache_read_tokens
