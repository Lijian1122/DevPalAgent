# -*- coding: utf-8 -*-
"""
Phase 9.5: LLM-as-a-Judge Critique Phase
用 LLM 评审代码质量，提供多维度评分和改进建议
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import OpenSpecContext, PhaseInterface, PhaseResult

# 默认评分权重
DEFAULT_DIMENSION_WEIGHTS = {
    "readability": 0.25,  # 25%
    "architecture": 0.25,  # 25%
    "security": 0.20,  # 20%
    "performance": 0.15,  # 15%
    "maintainability": 0.15,  # 15%
}

# System Prompt for Critique
CRITIQUE_SYSTEM_PROMPT = """你是一位资深代码审查专家，拥有 15 年以上的软件开发和架构设计经验。

**你的职责**：
- 评审代码质量，提供多维度评分（0-100 分）
- 识别代码中的问题和潜在风险
- 提供具体、可操作的改进建议

**评审原则**：
1. **客观公正**：基于事实和标准，不带个人偏见
2. **具体明确**：指出具体问题，不泛泛而谈
3. **建设性**：不仅指出问题，还提供解决方案
4. **平衡性**：既看到优点，也指出不足

**评分标准**：
- 90-100：优秀，几乎无可挑剔
- 70-89：良好，有小问题但不影响整体
- 50-69：一般，有明显问题需要改进
- 30-49：较差，有严重问题
- 0-29：很差，基本不可用

**输出格式**：
严格的 JSON 格式，包含 5 个维度的评分、reasoning 和 suggestions。
"""


class Phase9_5Critique(PhaseInterface):
    """Phase 9.5: LLM-as-a-Judge Critique Phase"""

    def __init__(
        self,
        context: OpenSpecContext,
        llm_client: Optional[Any] = None,
        config: Optional[Dict] = None,
    ):
        super().__init__(context)
        self.phase_number = 9.5
        self.phase_name = "Critique Phase"
        self.is_critical = False  # 非关键阶段，失败不终止流程
        self.llm_client = llm_client
        self.config = config or {}

        # 评审维度
        self.dimensions = [
            "readability",
            "architecture",
            "security",
            "performance",
            "maintainability",
        ]

        # 评分权重
        self.weights = self.config.get("dimension_weights", DEFAULT_DIMENSION_WEIGHTS)

        # 配置选项
        self.max_files_to_review = self.config.get("max_files_to_review", 10)
        self.skip_test_files = self.config.get("skip_test_files", True)

    def execute(self) -> PhaseResult:
        """执行 Critique Phase"""
        self.log("开始 LLM-as-a-Judge 代码质量评审")

        try:
            # 1. 检查 LLM Client
            if not self.llm_client:
                self.log("警告: LLM Client 未配置，跳过 Critique Phase")
                return PhaseResult.ok(
                    "Critique Phase 已跳过：LLM Client 未配置。", skipped=True
                )

            # 2. 收集要评审的文件
            files_to_review = self._collect_files()
            if not files_to_review:
                self.log("没有找到需要评审的文件")
                return PhaseResult.ok(
                    "Critique Phase 完成（无文件需要评审）", files_reviewed=0
                )

            self.log(f"找到 {len(files_to_review)} 个文件需要评审")

            # 3. 对每个文件进行评审
            file_critiques = []
            for i, file_path in enumerate(files_to_review, 1):
                self.log(f"评审文件 {i}/{len(files_to_review)}: {file_path.name}")
                try:
                    critique = self._critique_file(file_path)
                    file_critiques.append(critique)
                except Exception as e:
                    self.log_error(f"评审文件 {file_path} 失败: {e}")
                    # 继续评审其他文件
                    continue

            if not file_critiques:
                return PhaseResult.fail("所有文件评审失败", errors=["所有文件评审失败"])

            # 4. 汇总评审结果
            overall_result = self._aggregate_results(file_critiques)

            # 5. 生成报告
            self._generate_report(overall_result)

            # 6. 保存到 context
            self.context.critique_result = overall_result
            self.log(
                f"Critique Phase 完成: Overall Score = {overall_result['overall_score']}/100"
            )

            return PhaseResult.ok(
                f"Critique Phase 完成: Overall Score = {overall_result['overall_score']}/100",
                overall_score=overall_result["overall_score"],
                files_reviewed=len(file_critiques),
                critical_issues=len(overall_result.get("critical_issues", [])),
            )

        except Exception as e:
            self.log_error(f"Critique Phase 执行失败: {e}", e)
            return PhaseResult.fail(f"Critique Phase 执行失败: {e}", errors=[str(e)])

    def _collect_files(self) -> List[Path]:
        """收集需要评审的文件"""
        files_to_review = []

        # 从 context.generated_files 获取文件列表
        if hasattr(self.context, "generated_files") and self.context.generated_files:
            for file_rel_path in self.context.generated_files:
                file_path = self.context.project_dir / file_rel_path

                # 跳过测试文件
                if self.skip_test_files and ("test" in str(file_path).lower()):
                    continue

                # 检查文件是否存在
                if file_path.exists() and file_path.is_file():
                    files_to_review.append(file_path)

        # 限制文件数量
        if len(files_to_review) > self.max_files_to_review:
            self.log(
                f"文件数量超过限制 ({self.max_files_to_review})，只评审前 {self.max_files_to_review} 个"
            )
            files_to_review = files_to_review[: self.max_files_to_review]

        return files_to_review

    def _critique_file(self, file_path: Path) -> Dict:
        """评审单个文件"""
        # 读取文件内容
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code_content = f.read()
        except Exception as e:
            self.log_error(f"读取文件 {file_path} 失败: {e}")
            raise

        # 构建 Prompt
        retrieved_context = self._build_retrieved_context_section(file_path, code_content)
        prompt = self._build_critique_prompt(file_path, code_content, retrieved_context)

        # 调用 LLM
        try:
            response = self.llm_client.create_message(
                messages=[{"role": "user", "content": prompt}],
                system=CRITIQUE_SYSTEM_PROMPT,
                max_tokens=4096,
            )

            # 解析响应
            response_text = response.content[0].text
            critique_data = self._parse_critique_response(response_text)
            critique_data["file_path"] = str(
                file_path.relative_to(self.context.project_dir)
            )
            return critique_data

        except Exception as e:
            self.log_error(f"LLM 评审失败: {e}")
            raise

    def _build_critique_prompt(
        self,
        file_path: Path,
        code_content: str,
        retrieved_context: str = "",
    ) -> str:
        """构建评审 Prompt"""
        context_section = ""
        if retrieved_context:
            context_section = f"""
**相关上下文**:
{retrieved_context}
"""
        prompt = f"""
请评审以下代码文件的质量。

**文件**: `{file_path.name}`
**代码**:
{code_content}
{context_section}
**评审要求**:
请从以下 5 个维度评审代码质量，每个维度给出 0-100 分的评分：
1. **Readability** (可读性): 代码是否易读易懂，命名是否规范，注释是否充分
2. **Architecture** (架构): 代码结构是否合理，职责是否清晰，是否符合设计原则
3. **Security** (安全性): 是否存在安全漏洞，输入验证是否充分，敏感数据处理是否安全
4. **Performance** (性能): 是否有性能问题，算法是否高效，资源使用是否合理
5. **Maintainability** (可维护性): 代码是否易于维护和扩展，是否有技术债务

**输出格式** (严格的 JSON):
```json
{{
    "readability": {{
        "score": 85,
        "reasoning": "代码可读性评价...",
        "suggestions": ["建议1", "建议2"]
    }},
    "architecture": {{
        "score": 80,
        "reasoning": "架构评价...",
        "suggestions": ["建议1", "建议2"]
    }},
    "security": {{
        "score": 90,
        "reasoning": "安全性评价...",
        "suggestions": ["建议1", "建议2"]
    }},
    "performance": {{
        "score": 75,
        "reasoning": "性能评价...",
        "suggestions": ["建议1", "建议2"]
    }},
    "maintainability": {{
        "score": 82,
        "reasoning": "可维护性评价...",
        "suggestions": ["建议1", "建议2"]
    }}
}}
"""
        return prompt

    def _build_retrieved_context_section(self, file_path: Path, code_content: str) -> str:
        if not bool(getattr(self.context, "vector_retrieval_enabled", False)):
            return ""
        try:
            from devpal.vector_store.semantic_search import SemanticSearchService

            service = SemanticSearchService.from_context(self.context, log=self.log)
            service.index_context(self.context, self.context.project_name)
            query = "\n".join(
                part
                for part in [
                    "Phase 9.5 critique",
                    file_path.name,
                    code_content[:1200],
                    getattr(self.context, "requirements_content", ""),
                    getattr(self.context, "tech_design_content", ""),
                ]
                if part
            )
            retrieved_context = service.build_context(
                query=query,
                project_name=self.context.project_name,
                artifact_types=["requirements", "change", "source", "test", "report"],
                top_k=int(getattr(self.context, "vector_top_k", 5) or 5),
                event_integration=getattr(self.context, "event_integration", None),
            )
            self.context.vector_retrieval_stats = dict(service.stats)
            return retrieved_context
        except Exception as exc:
            self.log(f"  [VECTOR] Phase 9.5 retrieval context unavailable: {exc}")
            return ""

    def _parse_critique_response(self, response_text: str) -> Dict:
        """解析 LLM 响应"""
        # 尝试提取 JSON
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                self.log_error(f"JSON 解析失败: {e}")
                return self._get_default_critique()
        else:
            self.log_error("未找到 JSON 响应")
            return self._get_default_critique()

    def _get_default_critique(self) -> Dict:
        """获取默认评审结果"""
        return {
            dim: {"score": 70, "reasoning": "评审失败，使用默认评分", "suggestions": []}
            for dim in self.dimensions
        }

    def _aggregate_results(self, file_critiques: List[Dict]) -> Dict:
        """汇总多个文件的评审结果"""
        # 计算每个维度的平均分
        dimension_scores = {dim: [] for dim in self.dimensions}
        for critique in file_critiques:
            for dim in self.dimensions:
                if dim in critique:
                    score = critique[dim].get("score", 70)
                    dimension_scores[dim].append(score)

        # 计算加权总分
        overall_score = 0
        dimensions_summary = {}
        for dim in self.dimensions:
            scores = dimension_scores[dim]
            avg_score = sum(scores) / len(scores) if scores else 70
            weight = self.weights.get(dim, 0.2)
            dimensions_summary[dim] = {"score": round(avg_score, 1), "weight": weight}
            overall_score += avg_score * weight

        # 收集关键问题和建议
        critical_issues = []
        recommendations = []
        for critique in file_critiques:
            for dim in self.dimensions:
                if dim in critique:
                    dim_data = critique[dim]
                    if dim_data.get("score", 100) < 60:
                        critical_issues.append(
                            {
                                "file": critique.get("file_path", "unknown"),
                                "dimension": dim,
                                "score": dim_data.get("score"),
                                "reasoning": dim_data.get("reasoning", ""),
                            }
                        )
                    suggestions = dim_data.get("suggestions", [])
                    for suggestion in suggestions[:2]:
                        if suggestion and suggestion not in recommendations:
                            recommendations.append(suggestion)

        return {
            "overall_score": round(overall_score, 1),
            "dimensions": dimensions_summary,
            "files_reviewed": len(file_critiques),
            "critical_issues": critical_issues[:10],
            "recommendations": recommendations[:15],
            "file_details": file_critiques,
        }

    def _generate_report(self, overall_result: Dict):
        """生成 Markdown 和 JSON 报告"""
        # 1. 生成 Markdown 报告
        report_content = self._format_critique_report(overall_result)

        # 保存 Markdown 报告
        docs_dir = self.context.project_dir / "docs"
        docs_dir.mkdir(exist_ok=True)
        report_file = docs_dir / "critique_report.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_content)
        self.log(f"Critique 报告已生成: {report_file}")

        # 2. 生成 JSON 报告
        json_data = {
            "overall_score": overall_result["overall_score"],
            "dimensions": overall_result["dimensions"],
            "files_reviewed": overall_result["files_reviewed"],
            "critical_issues": overall_result.get("critical_issues", []),
            "recommendations": overall_result.get("recommendations", []),
            "timestamp": datetime.now().isoformat(),
            "phase": "9.5",
        }

        # 保存 JSON 报告
        spec_dir = self.context.project_dir / ".spec"
        spec_dir.mkdir(exist_ok=True)
        json_file = spec_dir / "critique_metrics.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        self.log(f"Critique JSON 已生成: {json_file}")

    def _format_critique_report(self, result: Dict) -> str:
        """格式化 Critique 报告"""
        lines = []
        lines.append("# Code Quality Critique Report")
        lines.append("")
        lines.append(f"**Overall Score**: {result['overall_score']}/100")
        lines.append(f"**Files Reviewed**: {result['files_reviewed']}")
        lines.append("")

        # 总体评级
        score = result["overall_score"]
        if score >= 90:
            rating = "Excellent"
            stars = "⭐⭐⭐⭐⭐"
        elif score >= 80:
            rating = "Good"
            stars = "⭐⭐⭐⭐"
        elif score >= 70:
            rating = "Fair"
            stars = "⭐⭐⭐"
        elif score >= 60:
            rating = "Poor"
            stars = "⭐⭐"
        else:
            rating = "Very Poor"
            stars = "⭐"

        lines.append(f"**Rating**: {rating} {stars}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 维度评分
        lines.append("## Dimension Scores")
        lines.append("")
        lines.append("| Dimension | Score | Weight | Contribution |")
        lines.append("|-----------|-------|--------|--------------|")

        for dim, data in result["dimensions"].items():
            score = data["score"]
            weight = data["weight"] * 100
            contribution = score * data["weight"]

            # 星级
            if score >= 90:
                dim_stars = "⭐⭐⭐⭐⭐"
            elif score >= 80:
                dim_stars = "⭐⭐⭐⭐"
            elif score >= 70:
                dim_stars = "⭐⭐⭐"
            elif score >= 60:
                dim_stars = "⭐⭐"
            else:
                dim_stars = "⭐"

            lines.append(
                f"| {dim.capitalize()} | {score}/100 {dim_stars} | {weight:.0f}% | {contribution:.1f} |"
            )

        lines.append("")
        lines.append("---")
        lines.append("")

        # 关键问题
        if result.get("critical_issues"):
            lines.append("## Critical Issues")
            lines.append("")
            for i, issue in enumerate(result["critical_issues"], 1):
                lines.append(
                    f"### {i}. {issue['dimension'].capitalize()} - {issue['file']}"
                )
                lines.append(f"**Score**: {issue['score']}/100")
                lines.append(f"**Issue**: {issue['reasoning']}")
                lines.append("")
                lines.append("---")
                lines.append("")

        # 改进建议
        if result.get("recommendations"):
            lines.append("## Recommendations")
            lines.append("")
            for i, rec in enumerate(result["recommendations"], 1):
                lines.append(f"{i}. {rec}")
            lines.append("")

        return "\n".join(lines)
