# -*- coding: utf-8 -*-
"""
Agent Core Engine - Plan-Act-Reflect Architecture
Supports Plan-Act-Reflect loop, 3-tier memory system, multi-round tool calls
"""

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from devpal.config import get_config
from devpal.memory import MemoryManager
from devpal.skills import SkillContext, SkillRouter
from devpal.skills.builtin import (
    CodeReviewSkill,
    InstallerSkill,
    MultiAgentSkill,
    OpenSpecSkill,
    TestGenerationSkill,
)
from devpal.tools.registry import ToolRegistry, registry

from .openspec_workflow import OpenSpecWorkflowExecutor
from .planner import Planner
from .reflector import Reflector

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def check_mingw_compiler() -> Tuple[bool, str]:
    """检查 MinGW-w64 g++ 编译器是否可用

    Returns:
        (available: bool, message: str)
    """
    import subprocess

    try:
        result = subprocess.run(
            ["g++", "--version"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.splitlines(
            )[0] if result.stdout else "g++"
            return True, f"MinGW-w64 编译器可用: {version_line[:50]}"
        else:
            return False, "g++ 编译器已安装但执行失败"
    except FileNotFoundError:
        return False, "未找到 g++ 编译器，请安装 MinGW-w64 并添加到 PATH"
    except Exception as e:
        return False, f"g++ 编译器检查失败: {str(e)}"


@dataclass
class AgentConfig:
    """Agent runtime configuration"""

    max_iterations: int = 10
    verbose: bool = True
    show_tool_output: bool = False
    show_reflection: bool = True  # Whether to show reflection results
    enable_retry: bool = True
    enable_long_term_memory: bool = True
    enable_error_memory: bool = True
    enable_planning: bool = True  # Enable planning capability
    enable_reflection: bool = True  # Enable reflection capability
    memory_path: Optional[str] = None
    workspace_path: Optional[str] = None  # 工作目录，用于 OpenSpec 状态管理

    # OpenSpec Integration Flags
    enable_validation_engine: bool = True  # 启用 4 层验证引擎
    enable_spec_engine: bool = True  # 启用规范状态引擎
    enable_artifact_graph: bool = True  # 启用工件依赖图
    enable_delta_mode: bool = True  # 默认使用增量变更模式


class AgentEngine:
    """Core agent execution engine

    Phase 4: OpenSpec 闭环集成
    - 使用 OpenSpecContext 统一管理所有 OpenSpec 组件
    - EventBus 事件驱动通信
    - 工件依赖追踪
    - 四层验证
    - 状态快照管理
    """

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        tool_registry: Optional[ToolRegistry] = None,
        openspec_context: Optional[Any] = None,
    ):
        self.config = config or AgentConfig()
        self.config_obj = get_config()

        # 工作目录：优先使用配置，否则使用当前目录
        self.workspace_path = (
            Path(self.config.workspace_path)
            if self.config.workspace_path
            else Path.cwd()
        )

        # ============================================================
        # Phase 4: OpenSpecContext 统一上下文初始化
        # ============================================================
        self.openspec_context = openspec_context
        self._init_openspec_context()

        # 将 EventBus 绑定到 ToolRegistry
        if self.openspec_context and tool_registry is None:
            # 创建新 registry 并绑定 event_bus
            from .openspec_context import OpenSpecContext

            if isinstance(self.openspec_context, OpenSpecContext):
                tool_registry = ToolRegistry(
                    event_bus=self.openspec_context.event_bus)

        # 设置工具注册表
        self.tool_registry = tool_registry or registry

        # 如果使用全局 registry，也需要绑定 event_bus
        if self.openspec_context and self.tool_registry is registry:
            try:
                from .openspec_context import OpenSpecContext

                if isinstance(self.openspec_context, OpenSpecContext):
                    self.tool_registry.set_event_bus(
                        self.openspec_context.event_bus)
            except BaseException:
                pass

        self.memory = MemoryManager(
            enable_long_term=self.config.enable_long_term_memory,
            enable_error=self.config.enable_error_memory,
        )

        self.message_history = self.memory.short_term

        self.planner = (
            Planner(tool_registry=self.tool_registry)
            if self.config.enable_planning
            else None
        )
        self.reflector = (
            Reflector(memory_manager=self.memory)
            if self.config.enable_reflection
            else None
        )

        # =====================================
        # Skills 系统初始化
        # ====================================================
        self.skill_router = SkillRouter(
            [
                InstallerSkill(),
                CodeReviewSkill(),
                MultiAgentSkill(),
                TestGenerationSkill(),
                OpenSpecSkill(),
            ],
            confidence_threshold=0.8,
        )

        # OpenSpec 完整流程执行器 (9 阶段)
        self.openspec_workflow = OpenSpecWorkflowExecutor(self.tool_registry)

        # 从 OpenSpecContext 获取组件（向后兼容）
        self.validation_engine = None
        self.spec_engine = None
        self.artifact_graph = None

        if self.openspec_context:
            try:
                self.validation_engine = self.openspec_context.validation_engine
            except BaseException:
                pass
            try:
                self.spec_engine = self.openspec_context.spec_engine
            except BaseException:
                pass
            try:
                self.artifact_graph = self.openspec_context.artifact_graph
            except BaseException:
                pass

        # ============================================================
        # 备用初始化（当没有 OpenSpecContext 时）
        # ============================================================
        if self.validation_engine is None and self.config.enable_validation_engine:
            try:
                from devpal.core.schema.validation_engine import ValidationEngine

                self.validation_engine = ValidationEngine()
            except ImportError:
                pass

        if self.spec_engine is None and self.config.enable_spec_engine:
            try:
                from devpal.core.schema.spec import SpecEngine

                self.spec_engine = SpecEngine(self.workspace_path)
            except ImportError:
                pass

        if self.artifact_graph is None and self.config.enable_artifact_graph:
            try:
                from devpal.core.schema.artifact_graph import ArtifactGraph

                self.artifact_graph = ArtifactGraph()
                self.artifact_graph.discover_from_directory(
                    self.workspace_path)
            except ImportError:
                pass

        self.base_system_prompt = self._build_base_system_prompt()

        self._init_llm_client()

        self.stats = {
            "total_queries": 0,
            "tool_calls": 0,
            "tool_errors": 0,
            "total_tokens": 0,
            "plans_generated": 0,
            "reflections_done": 0,
            # OpenSpec metrics
            "validation_checks": 0,
            "validation_failures": 0,
            "deltas_applied": 0,
            "snapshots_created": 0,
            "events_published": 0,
        }

    @property
    def event_bus(self):
        """获取 EventBus（通过 OpenSpecContext）"""
        if self.openspec_context:
            try:
                return self.openspec_context.event_bus
            except BaseException:
                pass
        return None

    def _init_openspec_context(self):
        """初始化 OpenSpecContext，如果用户没有提供的话"""
        if self.openspec_context is None and (
            self.config.enable_validation_engine
            or self.config.enable_spec_engine
            or self.config.enable_artifact_graph
        ):
            try:
                from .openspec_context import OpenSpecContext

                self.openspec_context = OpenSpecContext.create(
                    workspace=self.workspace_path,
                    enable_event_bus=True,
                    auto_initialize=True,
                )
            except Exception as e:
                if self.config.verbose:
                    print(f"[WARN] OpenSpecContext 初始化失败: {e}")

    def get_openspec_status(self) -> Dict[str, Any]:
        """获取 OpenSpec 架构状态报告"""
        status = {"enabled": {}, "metrics": {}, "artifacts": {}}

        # 组件启用状态
        status["enabled"]["validation_engine"] = self.validation_engine is not None
        status["enabled"]["spec_engine"] = self.spec_engine is not None
        status["enabled"]["artifact_graph"] = self.artifact_graph is not None

        # 指标统计
        status["metrics"]["validation_checks"] = self.stats.get(
            "validation_checks", 0)
        status["metrics"]["validation_failures"] = self.stats.get(
            "validation_failures", 0
        )
        status["metrics"]["deltas_applied"] = self.stats.get(
            "deltas_applied", 0)

        # SpecEngine 状态
        if self.spec_engine:
            status["spec_engine"] = {
                "requirements_count": len(self.spec_engine.requirements),
                "snapshots_count": len(self.spec_engine.snapshots),
                "workspace": str(self.spec_engine.workspace),
            }

        # ArtifactGraph 状态
        if self.artifact_graph:
            status["artifact_graph"] = {
                "nodes_count": len(self.artifact_graph._nodes),
            }

        return status

    def _build_system_prompt(self, current_query: str = "") -> str:
        """Build enhanced system prompt with memory injection"""
        base = self.base_system_prompt
        if current_query and self.memory:
            memory_enhancement = self.memory.get_system_prompt_enhancement(
                current_query
            )
            if memory_enhancement:
                base = base + "\n\n" + memory_enhancement
        return base

    def _build_base_system_prompt(self) -> str:
        """Build base system prompt with Skills and Tools information"""
        tool_names = ", ".join(self.tool_registry.list_tool_names())
        skills_info = self._format_skills_for_prompt()

        base_prompt = f"""You are DevPal, a professional C++/Python development assistant.

{skills_info}

## Available Tools (Low-Level Operations)

You can use the following tools for direct operations: {tool_names}

CRITICAL GUIDELINES FOR TOOL CALLS:
1. ALWAYS extract actual parameter values from user query, NEVER use null/None as parameter values
2. For linked list operations: parse numbers mentioned in query as actual node values
3. Example: if user says "nodes 4 6 8 0", you MUST pass value=4, value=6, etc. individually
4. Each tool call must have ALL required parameters filled with actual values

How to work:
1. **For complex workflows**: Consider suggesting appropriate Skills (e.g., "I recommend using OpenSpecSkill for this end-to-end task")
2. **For simple operations**: Call tools directly (read files, execute commands, search code)
3. Get information first, then provide answers, don't fabricate non-existent information
4. Tool execution results will be returned to you; you can continue calling tools or give final answers
5. You can call multiple tools per turn, or make multiple rounds of tool calls
6. Answers should be specific and executable, with code examples and operation steps

REMEMBER:
- If unsure about information, search or read files first, don't guess!
- ALWAYS extract real parameter values from user's natural language query!
- For complex multi-phase tasks, suggest appropriate Skills instead of manually orchestrating tools!"""

        return base_prompt

    def _format_skills_for_prompt(self) -> str:
        """
        Format Skills information for LLM system prompt

        Returns:
            Formatted string describing available Skills with metadata
        """
        if not self.skill_router or not self.skill_router.skills:
            return ""

        skills_lines = []
        skills_lines.append(
            "## Available Skills (High-Level Task Capabilities)")
        skills_lines.append("")
        skills_lines.append(
            "Skills are specialized workflows that orchestrate multiple tools and phases."
        )
        skills_lines.append(
            "When planning complex tasks, consider suggesting these Skills:"
        )
        skills_lines.append("")

        for skill in self.skill_router.skills:
            skills_lines.append(f"**{skill.name}**:")
            skills_lines.append(f"  - Description: {skill.description}")

            if skill.triggers:
                trigger_examples = ", ".join(
                    f'"{t}"' for t in skill.triggers[:3])
                skills_lines.append(
                    f"  - Triggered by keywords: {trigger_examples}")

            if skill.required_tools:
                tools_str = ", ".join(skill.required_tools)
                skills_lines.append(f"  - Requires tools: {tools_str}")
            skills_lines.append("")

        skills_lines.append("**When to suggest Skills**:")
        skills_lines.append(
            "- For end-to-end workflows (requirements → code → tests)")
        skills_lines.append("- For complex multi-phase tasks")
        skills_lines.append("- When user query matches skill triggers")
        skills_lines.append(
            "- When orchestrating multiple tools would be complex")
        skills_lines.append("")

        return "\n".join(skills_lines)

    def _init_llm_client(self):
        """Initialize LLM client"""
        import anthropic

        base_url = self.config_obj.anthropic_base_url
        api_key = self.config_obj.anthropic_auth_token

        if "volces.com" in base_url or "ark.cn" in base_url:
            self.client = anthropic.Anthropic(
                api_key="",
                base_url=base_url,
                default_headers={"Authorization": f"Bearer {api_key}"},
            )
        else:
            self.client = anthropic.Anthropic(
                api_key=api_key, base_url=base_url)

        self.model = self.config_obj.anthropic_model

    def _log(self, message: str, level: str = "INFO"):
        """Print log message"""
        if self.config.verbose:
            print(f"[{level}] {message}")

    def _intelligent_param_fix(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        user_query: str,
        call_index: int,
        step_description: str = "",
    ) -> Dict[str, Any]:
        """
        Fix common LLM parameter and operation issues intelligently
        """
        if tool_name == "linked_list_tool":
            operation = tool_args.get("operation")
            value = tool_args.get("value")

            # Extract numbers ONLY from node values section, not from index specifications
            # Pattern: "节点为" or "节点" followed by numbers until next Chinese
            # keyword
            node_values_match = re.search(r"节点[为\s:：]*([\d\s]+)", user_query)
            if node_values_match:
                numbers_str = node_values_match.group(1)
                numbers = [int(n) for n in re.findall(r"\d+", numbers_str)]
            else:
                # Fallback: extract all numbers but exclude index/delete
                # related numbers
                numbers = re.findall(r"\d+", user_query)
                numbers = [int(n) for n in numbers]

            # Heuristic 0: Force consistent list name across ALL operations
            # Always use 'demo_list' regardless of what LLM generates
            forced_name = "demo_list"
            if tool_args.get("list_name") != forced_name:
                tool_args = dict(tool_args)
                tool_args["list_name"] = forced_name
                if tool_args.get(
                        "list_name"):  # Only log if it was actually different
                    self._log(
                        f"  [Name Fix] Forced consistent list_name: '{forced_name}'", "FIX", )

            # Heuristic 1: Correct wrong operation types based on step
            # description (HIGH PRIORITY)
            step_lower = step_description.lower()
            if "operation: create" in step_lower or "创建" in step_description:
                if operation != "create":
                    tool_args = dict(tool_args)
                    tool_args["operation"] = "create"
                    self._log(
                        f"  [Op Fix] Corrected operation: {operation} -> create", "FIX")
            elif "operation: append" in step_lower or "append" in step_lower:
                if operation not in ["append", "prepend"]:
                    tool_args = dict(tool_args)
                    tool_args["operation"] = "append"
                    self._log(
                        f"  [Op Fix] Corrected operation: {operation} -> append", "FIX")
            elif (
                "operation: get_list" in step_lower
                or "get_list" in step_lower
                or "display" in step_lower
                or "遍历" in step_description
            ):
                if operation != "get_list":
                    tool_args = dict(tool_args)
                    tool_args["operation"] = "get_list"
                    self._log(
                        f"  [Op Fix] Corrected operation: {operation} -> get_list", "FIX", )
            elif (
                "operation: delete_value" in step_lower
                or "delete_value" in step_lower
                or ("delete" in step_lower and "value" in step_lower)
            ):
                if operation != "delete_value":
                    tool_args = dict(tool_args)
                    tool_args["operation"] = "delete_value"
                    self._log(
                        f"  [Op Fix] Corrected operation: {operation} -> delete_value", "FIX", )
            elif (
                "operation: delete_at" in step_lower
                or "delete_at" in step_lower
                or "delete" in step_lower
            ):
                if operation != "delete_at":
                    tool_args = dict(tool_args)
                    tool_args["operation"] = "delete_at"
                    self._log(
                        f"  [Op Fix] Corrected operation: {operation} -> delete_at", "FIX", )

            # Re-get operation after possible correction
            operation = tool_args.get("operation")

            # Heuristic 2: For append operations with ALL keyword: batch append
            # ALL values
            step_lower = step_description.lower()
            if operation in ["append", "prepend"] and value is None:
                # Smart batch append: if step description contains "ALL" /
                # "所有", append all values at once
                if (
                    "all" in step_lower
                    or "所有" in step_description
                    or "全部" in step_description
                ):
                    tool_args = dict(tool_args)
                    # Pass entire list for batch append
                    tool_args["value"] = numbers
                    self._log(
                        f"  [Batch Fix] Auto-filled ALL {len(numbers)} values: {numbers}",
                        "FIX",
                    )
                elif numbers and call_index < len(numbers):
                    # Single value mode for sequential calls
                    tool_args = dict(tool_args)
                    tool_args["value"] = numbers[call_index]
                    self._log(
                        f"  [Param Fix] Auto-filled value={tool_args['value']}", "FIX"
                    )

            # Heuristic 3: Delete index auto-fill (handle None or invalid
            # indices)
            idx_val = tool_args.get("index")
            if operation == "delete_at" and (
                idx_val is None or idx_val < 0 or idx_val == -1
            ):
                # Pattern 1: "索引为N" - already 0-based, use directly
                idx_match = re.search(r"索引[为\s]*(\d+)", user_query)
                if idx_match:
                    idx = int(idx_match.group(1))
                    tool_args = dict(tool_args)
                    tool_args["index"] = idx  # already 0-based
                    self._log(
                        f"  [Param Fix] Auto-filled index={idx} (from 索引N - 0-based)", "FIX", )
                # Pattern 2: "第N个" or "N-th node" - 1-based, convert to 0-based
                else:
                    idx_match = re.search(
                        r"第(\d+)个|(\d+)(st|nd|rd|th).*node|index\s*(\d+)\s*node",
                        user_query.lower(),
                    )
                    if idx_match:
                        idx = int([g for g in idx_match.groups() if g][0])
                        tool_args = dict(tool_args)
                        # convert 1-based to 0-based
                        tool_args["index"] = idx - 1
                        self._log(
                            f"  [Param Fix] Auto-filled index={tool_args['index']} (from 第N个/N-th)",
                            "FIX",
                        )
                    # Pattern 3: Chinese ordinal word pattern matching (第N个
                    # where N is Chinese char)
                    else:
                        ordinal_map = {
                            "一": 1,
                            "二": 2,
                            "三": 3,
                            "四": 4,
                            "五": 5,
                            "六": 6,
                            "七": 7,
                            "八": 8,
                            "九": 9,
                        }
                        for word, num in ordinal_map.items():
                            if f"第{word}个" in user_query:
                                tool_args = dict(tool_args)
                                # convert 1-based to 0-based
                                tool_args["index"] = num - 1
                                self._log(
                                    f"  [Param Fix] Auto-filled index={tool_args['index']} (from 第{word}个)",
                                    "FIX",
                                )
                                break

        return tool_args

    def _check_tool_call_hallucination(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        step_description: str,
        user_query: str = "",
    ) -> Dict[str, Any]:
        """
        工具调用幻觉检测：执行前检测潜在幻觉风险

        Returns:
            {
                'has_hallucination': bool,  是否检测到幻觉
                'block_execution': bool,   是否阻止执行
                'risk_level': str,        风险等级 high/medium/low
                'reason': str,             原因
                'issues': List           问题列表
            }
        """
        result = {
            "has_hallucination": False,
            "block_execution": False,
            "risk_level": "low",
            "reason": "",
            "issues": [],
        }

        # 1. 检测工具是否存在
        available_tools = self.tool_registry.list_tool_names()
        if tool_name not in available_tools:
            result["has_hallucination"] = True
            result["risk_level"] = "high"
            result["block_execution"] = True
            result["reason"] = f"工具 {tool_name} 不存在，可用工具: {available_tools}"
            result["issues"].append("wrong_tool")
            return result

        # 2. 检测必填参数是否为 None/空（高风险幻觉）
        for key, value in tool_args.items():
            if value is None or value == "" or value == "null":
                # 特例：linked_list_tool 的 value 允许 None（表示不填参数列表）
                if tool_name == "linked_list_tool" and key == "value":
                    continue
                result["has_hallucination"] = True
                result["risk_level"] = "high"
                result["reason"] = f"参数 {key} 为空/None，这是 LLM 常见幻觉"
                result["issues"].append(f"null_param_{key}")
                # 不阻止执行，让 _intelligent_param_fix 会尝试修复，或者让工具自己处理
                result["block_execution"] = False
                return result

        # 3. 高风险操作检测（需要人工确认）
        high_risk_keywords = {
            "delete",
            "remove",
            "rm -rf",
            "format",
            "drop",
            "truncate",
        }
        step_lower = step_description.lower()
        for keyword in high_risk_keywords:
            if keyword in tool_name or keyword in step_lower:
                result["has_hallucination"] = True
                result["risk_level"] = "high"
                result["reason"] = f"检测到高风险操作: {keyword}，建议人工确认"
                result["issues"].append("high_risk_operation")
                result["block_execution"] = False  # 不强制阻止，但需要打标记
                break

        # 4. 检测参数长度异常（可能是 LLM 输出混乱）
        for key, value in tool_args.items():
            if isinstance(value, str) and len(value) > 5000:
                result["has_hallucination"] = True
                result["risk_level"] = "medium"
                result["reason"] = (
                    f"参数 {key} 过长 ({len(value)} chars)，可能是输出混乱"
                )
                result["issues"].append("param_too_long")
                break

        return result

    def _extract_response_content(self, response) -> tuple[str, List[Dict]]:
        """Parse LLM response, extract text and tool calls"""
        text_content = ""
        tool_calls = []

        for block in response.content:
            if block.type == "thinking":
                continue
            elif block.type == "text":
                text_content += block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    {"id": block.id, "name": block.name, "input": block.input}
                )

        return text_content, tool_calls

    def run(self, user_query: str) -> str:
        """
        Execute user query - complete Plan-Act-Reflect loop

        Execution flow:
        1. Plan: Decompose task into steps
        2. Evaluate: Assess plan feasibility
        3. Execute: Run current step
        4. Reflect: Reflect on execution results
        5. Adjust: Dynamically adjust plan based on reflection
        6. Finalize: Generate final summary report

        OpenSpec Integration:
        - If the query is a requirements implementation request, automatically
          trigger the 9-phase OpenSpec workflow instead of Plan-Act-Reflect loop
        """
        self.stats["total_queries"] += 1

        # ====================================================================
        # OpenSpec 流程检测 - 暂时禁用快速路径，走完整 11 阶段流程
        # ====================================================================
        # 让请求走 Plan-Act-Reflect 中的 11 阶段完整流程
        # （包含代码审查报告、测试执行报告、技术实现文档）
        is_req, req_file = self.openspec_workflow.detect_requirements_request(
            user_query
        )
        if is_req and not req_file:
            return (
                "Please provide a requirements document (.md file path).\n"
                "OpenSpec workflow is ready to execute once requirements file is specified.")

        # =================================================
        # Skills 路由 - 意图识别和任务级编排
        # =================================================
        skill_context = SkillContext(
            user_query=user_query,
            workspace_path=self.workspace_path,
            tool_registry=self.tool_registry,
        )

        skill, confidence = self.skill_router.route(skill_context)

        if skill:
            # 路由到 Skill 执行
            if self.config.verbose:
                print(f"{'=' * 60}")
                print(f" Skill Router: {skill.name}")
                print(f" Confidence: {confidence:.2f}")
                print(f"{'=' * 60}")

            try:
                skill_result = skill.execute(skill_context)

                if skill_result.success:
                    result_msg = f"{skill_result.content}"
                    if skill_result.artifacts:
                        result_msg += "\nGenerated artifacts:\n"
                        for artifact in skill_result.artifacts:
                            result_msg += f"  - {artifact}\n"
                    return result_msg
                else:
                    # Skill 执行失败，fallback 到 Plan-Act-Reflect
                    if self.config.verbose:
                        print(
                            f"[!] Skill execution failed: {
                                skill_result.content}")
                        print("[!] Falling back to Plan-Act-Reflect\n")
            except Exception as e:
                # Skill 执行异常，fallback 到 Plan-Act-Reflect
                if self.config.verbose:
                    print(f"[!] Skill execution error: {str(e)}")
                    print("[!] Falling back to Plan-Act-Reflect\n")
        else:
            # 低置信度，fallback 到 Plan-Act-Reflect
            if self.config.verbose:
                print(f"\n{'=' * 60}")
                print(" Skill Router: Fallback to Planner")
                print(f" Best confidence: {confidence:.2f} (< 0.8)")
                print(f"{'=' * 60}\n")

        if self.config.verbose:
            print(f"\n{'=' * 60}")
            print(f" DevPal received task: {user_query}")
            print(f"{'=' * 60}\n")

        plan = None
        if self.config.enable_planning and self.planner:
            self._log("Generating execution plan...")
            plan = self.planner.generate_plan(user_query)
            self.stats["plans_generated"] += 1

            # Check if Planner recommends a Skill
            if plan and plan.recommended_skill:
                self._log(
                    f"Planner recommends Skill: {
                        plan.recommended_skill}")

            # Try to get the recommended skill
            recommended_skill_obj = self.skill_router.get_skill(
                plan.recommended_skill)

            if recommended_skill_obj:
                # Re-route to the recommended Skill
                skill_context = SkillContext(
                    user_query=user_query,
                    workspace_path=self.workspace_path,
                    tool_registry=self.tool_registry,
                )

            try:
                self._log(
                    f"Executing recommended Skill: {
                        plan.recommended_skill}")
                skill_result = recommended_skill_obj.execute(skill_context)
                if skill_result.success:
                    result_msg = f"{skill_result.content}"
                if skill_result.artifacts:
                    result_msg += "\nGenerated artifacts:\n"
                    for artifact in skill_result.artifacts:
                        result_msg += f"  - {artifact}\n"
                        return result_msg
                else:
                    self._log(
                        "Recommended Skill failed, continuing with Plan-Act-Reflect"
                    )
            except Exception as e:
                self._log(
                    f"Recommended Skill error: {e}, continuing with Plan-Act-Reflect")

            feasible, issues = self.planner.evaluate_feasibility(plan)

            if self.config.verbose:
                print(f"\n{'=' * 60}")
                print(" Execution Plan")
                print(f"{'=' * 60}")
                print(f" Goal: {plan.overall_goal}")
                print(f" Complexity: {plan.complexity}")
                print(f" Feasibility: {plan.feasibility_score:.1%}")
                if issues:
                    print(f" [!] Risks: {', '.join(issues)}")
                    print()
                for step in plan.steps:
                    print(f"   {step.step_number}. {step.description}")
                    if step.tool_needed:
                        print(f"        Tool: {step.tool_needed}")
                print(f"{'=' * 60}\n")

            if not feasible:
                return f"Plan not feasible: {'; '.join(issues)}"

            self.message_history.add_user(user_query)

            current_step_idx = 0
            all_tool_results = []  # Collect all tool results for final answer

        for iteration in range(self.config.max_iterations):
            if plan and current_step_idx >= len(plan.steps):
                break

            self._log(
                f"Iteration {iteration + 1} - Step {current_step_idx + 1}/{len(plan.steps) if plan else 'N/A'}"
            )

            if plan:
                current_step = plan.steps[current_step_idx]
                self._log(f"   Executing: {current_step.description}")

            # SHORTCUT: For linked_list_tool steps, execute directly (no LLM call needed)
            # This is more reliable and faster for linked list operations
            if plan and current_step.tool_needed == "linked_list_tool":
                # Extract operation from step description
                operation = "get_list"
                if "operation:" in current_step.description:
                    operation = (
                        current_step.description.split("operation:")[1]
                        .split(")")[0]
                        .strip()
                    )

                # Build args intelligently
                args = {"list_name": "demo_list", "operation": operation}

                # AUTO-CREATE: For any operation except create, ensure the list
                # exists first
                if operation != "create":
                    create_args = {
                        "list_name": "demo_list",
                        "operation": "create"}
                    self.tool_registry.execute_tool(
                        "linked_list_tool", create_args)

                # For append: extract numbers from query, but only before any
                # delete/index keywords
                if operation == "append":
                    # Cut off the string at the first delete/index keyword
                    q = user_query.lower()
                    for keyword in ["delete", "remove", "删除", "索引"]:
                        if keyword in q:
                            q = q[: q.index(keyword)]
                    numbers = [int(n) for n in re.findall(r"\d+", q)]
                    if numbers:
                        # Batch mode: pass all values at once
                        args["value"] = numbers

                # For delete_at: extract index from query
                if operation == "delete_at":
                    # Pattern 1: "索引为N" - already 0-based, use directly
                    idx_match = re.search(r"索引[为\s]*(\d+)", user_query)
                    if idx_match:
                        args["index"] = int(idx_match.group(1))
                    else:
                        # Pattern 2: "第N个" - 1-based, convert to 0-based
                        idx_match = re.search(r"第(\d+)个", user_query)
                        if idx_match:
                            args["index"] = int(idx_match.group(1)) - 1
                        else:
                            # Pattern 3: Chinese ordinal word (一, 二, etc.)
                            ordinal_map = {
                                "一": 1, "二": 2, "三": 3, "四": 4, "五": 5}
                            for word, num in ordinal_map.items():
                                if f"第{word}个" in user_query:
                                    args["index"] = num - 1
                                    break
                            else:
                                # Default: delete the last element if not
                                # specified
                                args["index"] = -1

                # For delete_value: extract value from query
                if operation == "delete_value":
                    # Find all numbers in the query as potential delete values
                    numbers = [int(n) for n in re.findall(r"\d+", user_query)]
                    if numbers:
                        # Use the last number as delete value
                        args["value"] = numbers[-1]

                # Execute directly
                result = self.tool_registry.execute_tool(
                    "linked_list_tool", args)
                print("\n    Tool: linked_list_tool")
                print(f"      Args: {args}")
                if result.success:
                    print("      [OK] Success")
                else:
                    print(f"      [FAIL] {result.error_message}")

                # Add to tool results (for final answer)
                all_tool_results.append(
                    {
                        "tool_name": "linked_list_tool",
                        "args": args,
                        "success": result.success,
                        "content": result.content,
                        "metadata": result.metadata,
                    }
                )

                # Add a dummy message to keep history moving forward
                self.message_history.add_assistant(
                    f"Executed {operation} successfully")

                # Add tool result message (format properly)
                dummy_id = f"direct_{operation}_{iteration}"
                self.message_history.add_tool_results(
                    [{"tool_use_id": dummy_id, "content": result.content}]
                )

                # Mark step complete
                if plan:
                    plan.mark_step_complete(
                        current_step_idx,
                        success=result.success,
                        result_summary=result.content[:200],
                    )
                    current_step_idx += 1
                continue

            # SHORTCUT: For project_generator / requirement implementation
            # tasks, execute full OpenSpec flow
            if plan and current_step.tool_needed in (
                "project_generator",
                "spec_tool",
                "requirements",
            ):
                # Extract requirement file from user query
                req_file = None
                # Match common requirement file patterns
                req_match = re.search(
                    r"([\w./\\-]*requirements?[\w./\\-]*\.md|req_[\w./\\-]+\.md)",
                    user_query,
                    re.IGNORECASE,
                )
                if req_match:
                    req_file = req_match.group(1)
                else:
                    # Search for any .md file in requirements directory
                    req_dir = Path("requirements")
                    if req_dir.exists():
                        md_files = list(req_dir.glob("*.md"))
                        if md_files:
                            req_file = str(md_files[0])

                if not req_file:
                    req_file = "requirements/login_requirements.md"  # Default

                # 使用统一 OpenSpec 执行入口（带超时、重试、断点续传配置）
                from .openspec_executor import (
                    OpenSpecRunOptions,
                    OpenSpecWorkflowExecutor,
                )

                executor = OpenSpecWorkflowExecutor(self.tool_registry)
                result = executor.run(
                    req_file,
                    OpenSpecRunOptions(
                        enable_timeout=True,
                        enable_retry=True,
                        enable_checkpoint=True,
                        enable_progress=True,
                        resume=False,
                        force_regenerate_code=True,
                    ),
                )

                # 安全获取结果字段
                project_dir = result.get("project_dir", "Unknown")
                test_passed = result.get("test_passed", 0)
                test_total = result.get("test_total", 0)
                test_summary = (result.get("test_summary")
                                or f"{test_passed}/{test_total} 通过")
                success = result.get("success", False)

                if success:
                    return f"""OpenSpec 11 阶段流程已完成！

✅ **项目信息**
- 项目目录: `{project_dir}`
- 测试结果: {test_summary}

所有代码、测试、文档已生成完成，可以直接使用。"""
                else:
                    errors = result.get("errors", ["Unknown error"])
                    failed_phase = result.get("failed_phase", "Unknown")
                    return f"""OpenSpec 11 阶段流程执行失败

❌ **错误信息**
- 项目目录: `{project_dir}`
- 失败阶段: Phase {failed_phase}
- 失败原因: {", ".join(str(e) for e in errors)}

请检查日志文件获取详细信息。"""

    def chat(self):
        """Start interactive chat mode"""
        print("=" * 60)
        print(" DevPal Agent - Interactive Chat")
        print("=" * 60)
        print(
            f" Available tools: {
                ', '.join(
                    self.tool_registry.list_tool_names())}")
        print(" Enter 'quit' to exit, 'help' for tool help, 'stats' for statistics")
        print()

        while True:
            try:
                user_input = input(" You: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ["quit", "exit", "q"]:
                    print(" Goodbye!")
                    break

                if user_input.lower() == "help":
                    print("\n" + self.tool_registry.get_tool_help() + "\n")
                    continue

                if user_input.lower() == "stats":
                    print("\n Statistics:")
                    for k, v in self.stats.items():
                        print(f"   {k}: {v}")
                    print()
                    continue

                answer = self.run(user_input)

                print("\n DevPal:")
                print(answer)
                print()

            except KeyboardInterrupt:
                print("\n\n Goodbye!")
                break
            except Exception as e:
                print(f"\n Error: {e}\n")

    def clear_history(self):
        """Clear conversation history"""
        self.message_history.clear()
        if self.config.verbose:
            self._log("Conversation history cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return self.stats.copy()
