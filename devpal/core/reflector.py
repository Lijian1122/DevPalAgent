# -*- coding: utf-8 -*-
"""
Reflector
Post-execution reflection, error analysis, and experience capture
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class Reflection:
    """Result of execution reflection"""
    success: bool
    goal_achieved: bool
    issues_found: List[str] = None
    improvements: List[str] = None
    need_plan_adjustment: bool = False
    adjustment_suggestion: str = ""
    lessons_learned: List[str] = None
    confidence_score: float = 0.8

    def __post_init__(self):
        if self.issues_found is None:
            self.issues_found = []
        if self.improvements is None:
            self.improvements = []
        if self.lessons_learned is None:
            self.lessons_learned = []


class Reflector:
    """Execution reflector - analyzes results, captures experience, handles errors"""

    ERROR_PATTERNS = {
        'file not found': {
            'issue': 'File does not exist',
            'improvement': 'Verify file exists using file_reader or code_search before operations',
            'lesson': 'Never assume file paths are correct; always verify existence first'
        },
        'not found': {
            'issue': 'Target does not exist',
            'improvement': 'Search and locate target before performing operations',
            'lesson': 'Validate targets before executing operations'
        },
        'permission denied': {
            'issue': 'Insufficient permissions',
            'improvement': 'Check permissions or use alternative approaches',
            'lesson': 'Some operations require specific privileges, plan accordingly'
        },
        'encoding': {
            'issue': 'Encoding problem',
            'improvement': 'Handle GBK/UTF-8 encoding conversions on Windows',
            'lesson': 'Windows console uses GBK encoding by default; handle encoding in command execution'
        },
        'syntax error': {
            'issue': 'Syntax error',
            'improvement': 'Check code syntax before executing',
            'lesson': 'Syntax validation should be done after code modifications'
        },
        'command not found': {
            'issue': 'Command not available',
            'improvement': 'Verify command availability or find alternatives',
            'lesson': 'Environment differences may affect tool availability; check first'
        },
        'timeout': {
            'issue': 'Execution timeout',
            'improvement': 'Increase timeout or split long commands',
            'lesson': 'Complex operations may require longer execution times'
        }
    }

    def __init__(self, llm_client=None, memory_manager=None):
        self.llm = llm_client
        self.memory = memory_manager
        self.execution_history = []

    def reflect_step(
        self,
        step_description: str,
        execution_result: Dict[str, Any],
        context: str = ""
    ) -> Reflection:
        """
        Reflect on single step execution result

        Args:
            step_description: Description of the step
            execution_result: Tool execution result
            context: Current context

        Returns:
            Reflection object
        """
        success = execution_result.get('success', False)
        content = execution_result.get('content', '')
        error = execution_result.get('error', '') or execution_result.get('content', '')

        reflection = Reflection(
            success=success,
            goal_achieved=success
        )

        if success:
            self._analyze_success(reflection, step_description, content)
        else:
            self._analyze_failure(reflection, step_description, error, content)

        self.execution_history.append({
            'step': step_description,
            'success': success,
            'reflection': reflection
        })

        if self.memory is not None and reflection.lessons_learned:
            for lesson in reflection.lessons_learned:
                self.memory.record_knowledge(lesson)

        if self.memory is not None and not success and reflection.issues_found:
            self.memory.record_error(
                error_type="tool_call_error",
                description=f"Step execution failed: {step_description}",
                correction="; ".join(reflection.improvements),
                context=f"Error: {error[:200]}"
            )

        return reflection

    def _analyze_success(
        self,
        reflection: Reflection,
        step_description: str,
        content: str
    ) -> None:
        """Analyze successful execution"""
        warning_signals = [
            'warning', 'warn', 'deprecated', 'note'
        ]

        content_lower = content.lower()
        for signal in warning_signals:
            if signal in content_lower:
                reflection.issues_found.append(f"Detected warning signal: {signal}")
                reflection.improvements.append("Check warning details to prevent future errors")

        if not reflection.issues_found:
            reflection.lessons_learned.append(
                f"Step '{step_description[:50]}...' executed successfully, method is effective"
            )

    def _analyze_failure(
        self,
        reflection: Reflection,
        step_description: str,
        error: str,
        content: str
    ) -> None:
        """Analyze failed execution"""
        error_lower = error.lower()
        reflection.goal_achieved = False

        matched = False
        for pattern, advice in self.ERROR_PATTERNS.items():
            if pattern in error_lower:
                matched = True
                reflection.issues_found.append(advice['issue'])
                reflection.improvements.append(advice['improvement'])
                reflection.lessons_learned.append(advice['lesson'])
                reflection.need_plan_adjustment = True
                reflection.adjustment_suggestion = advice['improvement']

        if not matched:
            reflection.issues_found.append(f"Execution error: {error[:100]}")
            reflection.improvements.append("Check input parameters or environment configuration")
            reflection.lessons_learned.append("Encountered new error type, needs analysis")
            reflection.need_plan_adjustment = True
            reflection.adjustment_suggestion = "Consider adjusting strategy or verifying environment"

        reflection.confidence_score = 0.3 if matched else 0.5

    def generate_reflection_report(self, reflection: Reflection) -> str:
        """Generate readable reflection report"""
        lines = ["\n" + "=" * 50, "  Execution Reflection", "=" * 50]

        status = "[OK] Success" if reflection.success else "[FAIL] Failed"
        lines.append(f"\nStatus: {status}")
        lines.append(f"Goal achieved: {'Yes' if reflection.goal_achieved else 'No'}")
        lines.append(f"Confidence score: {reflection.confidence_score:.1f}/1.0")

        if reflection.issues_found:
            lines.append(f"\nIssues found ({len(reflection.issues_found)}):")
            for i, issue in enumerate(reflection.issues_found, 1):
                lines.append(f"  {i}. {issue}")

        if reflection.improvements:
            lines.append(f"\nImprovement suggestions ({len(reflection.improvements)}):")
            for i, imp in enumerate(reflection.improvements, 1):
                lines.append(f"  {i}. {imp}")

        if reflection.lessons_learned:
            lines.append(f"\nLessons learned ({len(reflection.lessons_learned)}):")
            for i, lesson in enumerate(reflection.lessons_learned, 1):
                lines.append(f"  {i}. {lesson}")

        if reflection.need_plan_adjustment:
            lines.append(f"\n[!] Plan adjustment needed")
            lines.append(f"  Suggestion: {reflection.adjustment_suggestion}")

        lines.append("=" * 50 + "\n")
        return "\n".join(lines)

    def reflect_final_result(self, query: str, final_result: str, plan=None) -> Dict[str, Any]:
        """
        Final reflection after task completion, summarizes lessons learned

        Args:
            query: Original user query
            final_result: Final execution result
            plan: Execution plan (optional)

        Returns:
            Summary dictionary
        """
        summary = {
            'query': query,
            'total_steps': len(self.execution_history),
            'success_count': sum(1 for h in self.execution_history if h['success']),
            'lessons': []
        }

        for h in self.execution_history:
            ref = h['reflection']
            if ref.lessons_learned:
                summary['lessons'].extend(ref.lessons_learned)

        summary['lessons'] = list(dict.fromkeys(summary['lessons']))

        if self.memory is not None:
            for lesson in summary['lessons']:
                self.memory.record_knowledge(lesson)

            if summary['success_count'] == summary['total_steps']:
                self.memory.record_success(query, final_result[:500])

        summary['success_rate'] = (
            summary['success_count'] / summary['total_steps']
            if summary['total_steps'] > 0 else 0
        )

        return summary

    def should_continue(self, reflection: Reflection, current_step: int, max_steps: int) -> bool:
        """
        Determine if execution should continue

        Args:
            reflection: Reflection result of current step
            current_step: Current step number
            max_steps: Maximum allowed steps

        Returns:
            Whether to continue execution
        """
        if reflection.success:
            return True

        if current_step >= max_steps:
            return False

        if reflection.need_plan_adjustment:
            return True

        recent_failures = sum(
            1 for h in self.execution_history[-3:] if not h['success']
        )
        if recent_failures >= 3:
            return False

        return True

    def clear_history(self) -> None:
        """Clear execution history"""
        self.execution_history = []
