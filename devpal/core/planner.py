# -*- coding: utf-8 -*-
"""
Planner
Task decomposition, feasibility evaluation, and dynamic plan adjustment
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class PlanStep:
    """A single step in an execution plan"""

    step_number: int
    description: str
    tool_needed: Optional[str] = None  # Name of tool needed for this step
    expected_output: Optional[str] = None  # Expected output
    importance: int = 5  # Importance level 1-10
    completed: bool = False
    success: bool = False
    result_summary: str = ""
    error_message: Optional[str] = None


@dataclass
class Plan:
    """Complete execution plan"""

    original_query: str
    steps: List[PlanStep] = field(default_factory=list)
    overall_goal: str = ""
    complexity: str = "medium"  # simple, medium, complex
    # NEW: Skill recommendation from planner
    recommended_skill: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    current_step_index: int = 0
    feasibility_score: float = 0.8  # Feasibility score 0-1

    @property
    def current_step(self) -> Optional[PlanStep]:
        """Get current executing step"""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    @property
    def is_complete(self) -> bool:
        """Check if all steps are completed"""
        return all(step.completed for step in self.steps)

    @property
    def success_count(self) -> int:
        """Count of successfully completed steps"""
        return sum(1 for step in self.steps if step.completed and step.success)

    def mark_step_complete(
        self,
        step_index: int,
        success: bool,
        result_summary: str = "",
        error_message: Optional[str] = None,
    ) -> None:
        """Mark a step as completed"""
        if 0 <= step_index < len(self.steps):
            self.steps[step_index].completed = True
            self.steps[step_index].success = success
            self.steps[step_index].result_summary = result_summary
            self.steps[step_index].error_message = error_message

    def insert_step(self, after_index: int, step: PlanStep) -> None:
        """Insert a step after the specified index"""
        step.step_number = after_index + 2
        for i in range(after_index + 1, len(self.steps)):
            self.steps[i].step_number += 1
        self.steps.insert(after_index + 1, step)

    def get_progress(self) -> Dict[str, Any]:
        """Get execution progress information"""
        total = len(self.steps)
        completed = sum(1 for s in self.steps if s.completed)
        successful = sum(1 for s in self.steps if s.completed and s.success)
        return {
            "total": total,
            "completed": completed,
            "successful": successful,
            "progress_pct": (completed / total * 100) if total > 0 else 0,
            "current_step": self.current_step_index + 1 if self.current_step else 0,
        }


class Planner:
    """Task planner - decomposes queries, evaluates feasibility, adjusts plans"""

    # Safety/risk keywords
    DANGEROUS_KEYWORDS = {
        "delete",
        "remove",
        "rm -rf",
        "format",
        "del",
        "deltree",
        "sudo",
        "admin",
        "root",
        "chmod 777",
        "chown",
        "drop",
        "truncate",
        "alter",
        "delete from",
        "poweroff",
        "shutdown",
        "reboot",
    }

    def __init__(self, llm_client=None, system_prompt: str = "", tool_registry=None):
        self.llm = llm_client
        self.tool_registry = tool_registry  # Must be set before calling _default_system_prompt()
        self.system_prompt = system_prompt or self._default_system_prompt()
        # 延迟导入避免循环依赖
        self._hallucination_detector = None

    @property
    def hallucination_detector(self):
        """懒加载幻觉检测器"""
        if self._hallucination_detector is None:
            from devpal.tools.hallucination_detector import HallucinationDetectorTool

            self._hallucination_detector = HallucinationDetectorTool()
        return self._hallucination_detector

    def _default_system_prompt(self) -> str:
        # Get available tools and skills info
        tool_names = []
        if self.tool_registry:
            tool_names = self.tool_registry.list_tool_names()

        tools_str = (
            ", ".join(tool_names) if tool_names else "standard development tools"
        )

        return f"""You are a professional software development planning expert.
Your job is to decompose user requirements into clear, executable steps.

Available capabilities:
- **Skills**: High-level workflows (e.g., openspec_skill, test_generation_skill, code_review_skill)
- **Tools**: Low-level operations ({tools_str})

Planning principles:
1. First understand the core need, then decompose into steps
2. **For complex workflows**: Consider if a Skill can handle the entire task (e.g., "Use openspec_skill for end-to-end project generation")
3. **For simple tasks**: Use tools directly in step-by-step plan
4. Each step should be clear, verifiable, with well-defined expected output
5. Complex tasks should have 3-7 steps, neither too granular nor too coarse
6. Prefer low-risk, low-side-effect solutions
7. For file modification steps, "read" first then "modify"
8. For build tasks, "check environment" first then "execute build"

Return JSON format:
{{
    "overall_goal": "Task overall goal description",
    "complexity": "simple|medium|complex",
    "recommended_skill": "skill_name|null (if a Skill can handle this task)",
    "steps": [
        {{
         "step_number": 1,
            "description": "Step description",
            "tool_needed": "tool_name|skill_name|null",
            "expected_output": "Expected output",
            "importance": 1-10
        }}
    ]
}}
"""

    def generate_plan(self, query: str, context: str = "") -> Plan:
        """
        Generate execution plan from user query

        Args:
            query: Original user query
            context: Additional context information

        Returns:
            Plan object
        """
        if self._is_simple_task(query):
            return self._generate_simple_plan(query)

        if self.llm:
            return self._generate_plan_with_llm(query, context)

        return self._generate_heuristic_plan(query)

    def _is_simple_task(self, query: str) -> bool:
        """Check if task is simple"""
        simple_patterns = ["read", "list", "cat", "directory", "dir"]
        complex_patterns = [
            "test",
            "修复",
            "审查",
            "生成",
            "compile",
            "build",
            "链表",
            "linked",
            "实现",
            "需求",
            "完整",
            "requirement",
            "spec",
            "implement",
            "flow",
        ]
        q = query.lower()

        # 如果包含复杂任务的关键词，不视为简单任务
        for cp in complex_patterns:
            if cp in q:
                return False

        # 只有纯粹的读取才是简单任务
        has_simple = sum(1 for p in simple_patterns if p in q) > 0
        # 但如果是 "read AND fix/test" 则不是简单任务
        return has_simple and not any(x in q for x in ["fix", "and fix", "并"])

    def _generate_simple_plan(self, query: str) -> Plan:
        """Generate quick plan for simple tasks"""
        return Plan(
            original_query=query,
            overall_goal=f"Simple file operation: {query}",
            complexity="simple",
            steps=[
                PlanStep(
                    step_number=1,
                    description="Read target file or directory contents",
                    tool_needed="file_reader",
                    expected_output="File content or directory listing",
                    importance=8,
                ),
                PlanStep(
                    step_number=2,
                    description="Summarize results and provide user feedback",
                    tool_needed=None,
                    expected_output="Clear response to user",
                    importance=5,
                ),
            ],
        )

    def _generate_heuristic_plan(self, query: str) -> Plan:
        """Generate plan heuristically (when no LLM available)"""
        q = query.lower()
        steps = []

        if any(k in q for k in ["compile", "build", "make", "msbuild"]):
            steps = [
                PlanStep(
                    1,
                    "Check project structure, find build files",
                    "file_reader",
                    "Project structure info",
                    9,
                ),
                PlanStep(
                    2,
                    "Verify build environment and tools available",
                    "execute_command",
                    "Environment check result",
                    8,
                ),
                PlanStep(
                    3,
                    "Execute build command",
                    "execute_command",
                    "Build output log",
                    10,
                ),
                PlanStep(
                    4,
                    "Analyze build errors and provide fixes",
                    "compiler_analyzer",
                    "Error analysis report",
                    9,
                ),
                PlanStep(5, "Summarize results for user", None, "Final report", 5),
            ]
        elif any(
            k in q
            for k in [
                "需求",
                "requirement",
                "spec",
                "实现",
                "implement",
                "完整",
                "流程",
            ]
        ):
            # 需求驱动开发任务：使用 project_generator + spec_tool 完整 OpenSpec 流程
            steps = [
                PlanStep(
                    1,
                    "运行完整 OpenSpec 需求驱动开发流程：解析需求、规范分析、代码生成、项目创建、代码审查、测试执行",
                    "project_generator",
                    "完整的项目结构、代码文件、测试报告和验证输出",
                    10,
                ),
            ]
        elif any(
            k in q
            for k in ["test", "测试", "修复", "review", "审查", "用例", "orchestrator"]
        ):
            # 测试相关任务：使用 test_orchestrator 工具一站式完成
            steps = [
                PlanStep(
                    1,
                    "使用 test_orchestrator 执行完整测试流程：代码审查、自动修复、生成测试文档、生成测试代码、运行测试",
                    "test_orchestrator",
                    "完整的测试报告和所有输出文件",
                    10,
                ),
            ]
        elif any(k in q for k in ["search", "find", "grep"]):
            steps = [
                PlanStep(
                    1,
                    "Confirm search scope and target files",
                    "file_reader",
                    "Project structure info",
                    7,
                ),
                PlanStep(2, "Execute code search", "code_search", "Search results", 9),
                PlanStep(
                    3, "Organize search results for user", None, "Structured results", 6
                ),
            ]
        elif any(k in q for k in ["链表", "linked list", "node", "节点"]):
            # Extract specific operation hints from query
            has_delete = "delete" in q or "删除" in q
            has_update = "update" in q or "修改" in q or "更新" in q
            has_create = "创建" in q or "新建" in q or "create" in q
            only_append = (
                not has_create
                and not has_delete
                and not has_update
                and ("添加" in q or "append" in q or "尾部" in q)
            )

            if only_append:
                # Simple case: just append to existing list
                steps = [
                    PlanStep(
                        1,
                        "Append node values (operation: append)",
                        "linked_list_tool",
                        "Nodes added successfully",
                        10,
                    ),
                    PlanStep(
                        2,
                        "Get and display list (operation: get_list)",
                        "linked_list_tool",
                        "Linked list contents",
                        7,
                    ),
                ]
            else:
                # 智能规划：根据查询关键词动态生成步骤
                steps = []
                step_idx = 1
                q_lower = query.lower()

                # 1. Create 步骤
                if has_create:
                    steps.append(
                        PlanStep(
                            step_idx,
                            "Create linked list (operation: create)",
                            "linked_list_tool",
                            "Linked list created successfully",
                            9,
                        )
                    )
                    step_idx += 1

                # 2. Append 步骤：仅当有添加相关关键词时才添加
                has_digits = bool(re.search(r"\d", query))
                # 纯删除操作不需要 append 步骤（数字可能是要删除的值，不是要添加的值）
                has_append = (
                    "添加" in query
                    or "append" in q_lower
                    or "尾部" in query
                    or (has_digits and not has_delete)
                )
                if has_append or (
                    not has_delete and not has_update
                ):  # 如果既不删也不改，默认是添加
                    steps.append(
                        PlanStep(
                            step_idx,
                            "Append ALL node values (operation: append)",
                            "linked_list_tool",
                            "All nodes added successfully",
                            10,
                        )
                    )
                    step_idx += 1

                # 3. 显示当前状态（删除前先显示）
                steps.append(
                    PlanStep(
                        step_idx,
                        "Get and display list (operation: get_list)",
                        "linked_list_tool",
                        "Linked list contents",
                        7,
                    )
                )
                step_idx += 1

                # 4. Delete 步骤：按值删除 vs 按索引删除
                if has_delete:
                    # 检查是否是按索引删除（第N个节点）
                    is_delete_by_index = "第" in query and (
                        "个" in query or "节点" in query
                    )
                    if is_delete_by_index:
                        steps.append(
                            PlanStep(
                                step_idx,
                                "Delete node by index (operation: delete_at)",
                                "linked_list_tool",
                                "Node deleted successfully",
                                8,
                            )
                        )
                    else:
                        steps.append(
                            PlanStep(
                                step_idx,
                                "Delete node by value (operation: delete_value)",
                                "linked_list_tool",
                                "Node deleted successfully",
                                8,
                            )
                        )
                    step_idx += 1

                # 5. Update 步骤
                if has_update:
                    steps.append(
                        PlanStep(
                            step_idx,
                            "Update the specified node (operation: update)",
                            "linked_list_tool",
                            "Node updated successfully",
                            8,
                        )
                    )
                    step_idx += 1

                # 6. 最终验证
                steps.append(
                    PlanStep(
                        step_idx,
                        "Verify final state (operation: get_list)",
                        "linked_list_tool",
                        "Final linked list state",
                        6,
                    )
                )
        else:
            steps = [
                PlanStep(
                    1,
                    "Check current state and environment",
                    "execute_command",
                    "Current environment info",
                    7,
                ),
                PlanStep(2, "Execute core operation", None, "Execution result", 9),
                PlanStep(
                    3, "Verify result correctness", None, "Verification report", 6
                ),
            ]

        return Plan(
            original_query=query,
            overall_goal=f"Complete task: {query}",
            complexity="medium",
            steps=steps,
        )

    def _generate_plan_with_llm(self, query: str, context: str) -> Plan:
        """Generate detailed plan using LLM"""
        # TODO: Implement actual LLM call here
        # For now, return heuristic plan but with recommended_skill support
        plan = self._generate_heuristic_plan(query)

        # Try to infer recommended_skill from query keywords
        query_lower = query.lower()
        if any(
            kw in query_lower
            for kw in [
                "完整项目",
                "端到端",
                "openspec",
                "full project",
                "11-phase",
                "全流程",
                "需求到代码",
            ]
        ):
            plan.recommended_skill = "openspec_skill"
        elif any(
            kw in query_lower
            for kw in [
                "生成测试",
                "测试用例",
                "test generation",
                "测试生成",
                "自动测试",
            ]
        ):
            plan.recommended_skill = "test_generation_skill"
        elif any(
            kw in query_lower
            for kw in ["代码审查", "review", "检查代码", "code review", "审查"]
        ):
            plan.recommended_skill = "code_review_skill"

        return plan

    def evaluate_feasibility(self, plan: Plan) -> tuple[bool, List[str]]:
        """
        Evaluate plan feasibility with hallucination detection

        Returns:
            (is_feasible, list_of_issues_or_risks)
        """
        issues = []

        if not plan.steps:
            issues.append("Plan contains no execution steps")

        # ========== 幻觉检测 START ==========
        # 构建计划文本用于检测
        plan_text = self._plan_to_text(plan)
        available_tools = (
            self.tool_registry.list_tool_names() if self.tool_registry else []
        )
        context = f"可用工具: {', '.join(available_tools)}"

        # 调用幻觉检测器
        detection_result = self.hallucination_detector.execute(
            self.hallucination_detector.Parameters(
                check_type="plan", content_to_check=plan_text, context=context
            )
        )

        if detection_result.success:
            hallucination_issues = detection_result.metadata.get("issues", [])
            for issue in hallucination_issues:
                issues.append(
                    f"[幻觉检测 {issue['severity'].upper()}] {issue['message']} - {issue['suggestion']}"
                )
        # ========== 幻觉检测 END ==========

        for step in plan.steps:
            step_text = step.description.lower()
            # Skip danger check for linked_list_tool operations (node deletion
            # is safe)
            if step.tool_needed == "linked_list_tool":
                continue
            dangers = [k for k in self.DANGEROUS_KEYWORDS if k in step_text]
            if dangers:
                issues.append(
                    f"Step {step.step_number} contains dangerous operations: {
                        ', '.join(dangers)
                    }"
                )

            # 额外检查：工具是否存在
            if (
                step.tool_needed
                and available_tools
                and step.tool_needed not in available_tools
            ):
                issues.append(
                    f"[幻觉] Step {step.step_number} 引用了不存在的工具: {
                        step.tool_needed
                    }"
                )

        numbers = sorted(s.step_number for s in plan.steps)
        expected = list(range(1, len(numbers) + 1))
        if numbers != expected:
            issues.append(f"Step numbering is not sequential: {numbers}")

        if not plan.overall_goal or len(plan.overall_goal) < 5:
            issues.append("Overall goal description is not clear")

        feasible = len(issues) == 0
        feasibility_score = 1.0 - (len(issues) * 0.15)
        plan.feasibility_score = max(0.0, feasibility_score)

        return feasible, issues

    def _plan_to_text(self, plan: Plan) -> str:
        """将计划转换为文本格式用于检测"""
        lines = [
            f"Overall Goal: {plan.overall_goal}",
            f"Complexity: {plan.complexity}",
            f"Feasibility: {plan.feasibility_score}",
            "",
        ]
        for step in plan.steps:
            lines.append(f"Step {step.step_number}: {step.description}")
            if step.tool_needed:
                lines.append(f"  Tool: {step.tool_needed}")
            if step.expected_output:
                lines.append(f"  Expected: {step.expected_output}")
        return "\n".join(lines)

    def adjust_plan(
        self,
        plan: Plan,
        current_step_index: int,
        execution_result: Dict[str, Any],
        feedback: str = "",
    ) -> Plan:
        """
        Dynamically adjust plan based on execution results

        Args:
            plan: Current execution plan
            current_step_index: Index of just completed step
            execution_result: Result of execution
            feedback: Reflection feedback

        Returns:
            Adjusted new plan
        """
        success = execution_result.get("success", False)

        if success:
            if current_step_index + 1 < len(plan.steps):
                plan.current_step_index = current_step_index + 1
            return plan

        error_msg = execution_result.get("error", "") or execution_result.get(
            "content", ""
        )

        if "not found" in error_msg.lower():
            plan.insert_step(
                current_step_index,
                PlanStep(
                    step_number=0,
                    description="Search and locate target file first",
                    tool_needed="code_search",
                    expected_output="Actual file path",
                    importance=9,
                ),
            )
            plan.current_step_index = current_step_index + 1
            return plan

        if "command not found" in error_msg.lower():
            plan.insert_step(
                current_step_index,
                PlanStep(
                    step_number=0,
                    description="Check available commands and tools",
                    tool_needed="execute_command",
                    expected_output="List of available tools",
                    importance=8,
                ),
            )
            plan.current_step_index = current_step_index + 1
            return plan

        if "permission" in error_msg.lower():
            plan.current_step_index = current_step_index + 1
            return plan

        plan.current_step_index = current_step_index + 1
        return plan

    def generate_final_summary(self, plan: Plan) -> str:
        """Generate final execution summary"""
        progress = plan.get_progress()

        lines = [
            "=" * 60,
            f"Execution Summary: {plan.overall_goal}",
            "=" * 60,
            "",
            f"Total Steps: {progress['total']}",
            f"Completed: {progress['completed']}",
            f"Successful: {progress['successful']}",
            f"Success Rate: {progress['progress_pct']:.1f}%",
            "",
            "Step Details:",
        ]

        for step in plan.steps:
            status = (
                "[OK]" if step.success else "[FAIL]" if step.completed else "[PENDING]"
            )
            lines.append(f"  {status} Step {step.step_number}: {step.description}")
            if step.result_summary:
                lines.append(f"      Result: {step.result_summary[:100]}...")

        lines.extend(["", "=" * 60])

        if plan.success_count == len(plan.steps):
            lines.append("All steps completed successfully!")
        elif plan.success_count > 0:
            lines.append(
                f"Partial success: {plan.success_count} of {len(plan.steps)} steps succeeded"
            )
        else:
            lines.append("[FAIL] All steps failed")

        return "\n".join(lines)
