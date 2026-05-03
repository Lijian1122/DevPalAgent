# -*- coding: utf-8 -*-
"""
Agent Core Engine - Plan-Act-Reflect Architecture
Supports Plan-Act-Reflect loop, 3-tier memory system, multi-round tool calls
"""
import sys
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from devpal.config import get_config
from devpal.tools.registry import ToolRegistry, registry
from devpal.memory import MemoryManager
from .planner import Planner, Plan
from .reflector import Reflector, Reflection


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


class AgentEngine:
    """Core agent execution engine"""

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        tool_registry: Optional[ToolRegistry] = None,
    ):
        self.config = config or AgentConfig()
        self.tool_registry = tool_registry or registry
        self.config_obj = get_config()

        self.memory = MemoryManager(
            enable_long_term=self.config.enable_long_term_memory,
            enable_error=self.config.enable_error_memory
        )

        self.message_history = self.memory.short_term

        self.planner = Planner() if self.config.enable_planning else None
        self.reflector = Reflector(memory_manager=self.memory) if self.config.enable_reflection else None

        self.base_system_prompt = self._build_base_system_prompt()

        self._init_llm_client()

        self.stats = {
            "total_queries": 0,
            "tool_calls": 0,
            "tool_errors": 0,
            "total_tokens": 0,
            "plans_generated": 0,
            "reflections_done": 0,
        }

    def _build_system_prompt(self, current_query: str = "") -> str:
        """Build enhanced system prompt with memory injection"""
        base = self.base_system_prompt
        if current_query and self.memory:
            memory_enhancement = self.memory.get_system_prompt_enhancement(current_query)
            if memory_enhancement:
                base = base + "\n\n" + memory_enhancement
        return base

    def _build_base_system_prompt(self) -> str:
        """Build base system prompt"""
        tool_names = ", ".join(self.tool_registry.list_tool_names())
        return f"""You are DevPal, a professional C++/Python development assistant.

You can use the following tools to help users: {tool_names}

CRITICAL GUIDELINES FOR TOOL CALLS:
1. ALWAYS extract actual parameter values from user query, NEVER use null/None as parameter values
2. For linked list operations: parse numbers mentioned in query as actual node values
3. Example: if user says "nodes 4 6 8 0", you MUST pass value=4, value=6, etc. individually
4. Each tool call must have ALL required parameters filled with actual values

How to work:
1. If you need to read files, execute commands, or search code, call the corresponding tool directly
2. Get information first, then provide answers, don't fabricate non-existent information
3. Tool execution results will be returned to you; you can continue calling tools or give final answers
4. You can call multiple tools per turn, or make multiple rounds of tool calls
5. Answers should be specific and executable, with code examples and operation steps

REMEMBER: If unsure about information, search or read files first, don't guess!
ALWAYS: Extract real parameter values from user's natural language query!"""

    def _init_llm_client(self):
        """Initialize LLM client"""
        import anthropic

        base_url = self.config_obj.anthropic_base_url
        api_key = self.config_obj.anthropic_auth_token

        if "volces.com" in base_url or "ark.cn" in base_url:
            self.client = anthropic.Anthropic(
                api_key="",
                base_url=base_url,
                default_headers={"Authorization": f"Bearer {api_key}"}
            )
        else:
            self.client = anthropic.Anthropic(
                api_key=api_key,
                base_url=base_url
            )

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
        step_description: str = ""
    ) -> Dict[str, Any]:
        """
        Fix common LLM parameter and operation issues intelligently
        """
        if tool_name == 'linked_list_tool':
            operation = tool_args.get('operation')
            value = tool_args.get('value')

            # Extract numbers ONLY from node values section, not from index specifications
            # Pattern: "节点为" or "节点" followed by numbers until next Chinese keyword
            node_values_match = re.search(r'节点[为\s:：]*([\d\s]+)', user_query)
            if node_values_match:
                numbers_str = node_values_match.group(1)
                numbers = [int(n) for n in re.findall(r'\d+', numbers_str)]
            else:
                # Fallback: extract all numbers but exclude index/delete related numbers
                numbers = re.findall(r'\d+', user_query)
                numbers = [int(n) for n in numbers]

            # Heuristic 0: Force consistent list name across ALL operations
            # Always use 'demo_list' regardless of what LLM generates
            forced_name = 'demo_list'
            if tool_args.get('list_name') != forced_name:
                tool_args = dict(tool_args)
                tool_args['list_name'] = forced_name
                if tool_args.get('list_name'):  # Only log if it was actually different
                    self._log(f"  [Name Fix] Forced consistent list_name: '{forced_name}'", "FIX")

            # Heuristic 1: Correct wrong operation types based on step description (HIGH PRIORITY)
            step_lower = step_description.lower()
            if 'operation: create' in step_lower or '创建' in step_description:
                if operation != 'create':
                    tool_args = dict(tool_args)
                    tool_args['operation'] = 'create'
                    self._log(f"  [Op Fix] Corrected operation: {operation} -> create", "FIX")
            elif 'operation: append' in step_lower or 'append' in step_lower:
                if operation not in ['append', 'prepend']:
                    tool_args = dict(tool_args)
                    tool_args['operation'] = 'append'
                    self._log(f"  [Op Fix] Corrected operation: {operation} -> append", "FIX")
            elif 'operation: get_list' in step_lower or 'get_list' in step_lower or 'display' in step_lower or '遍历' in step_description:
                if operation != 'get_list':
                    tool_args = dict(tool_args)
                    tool_args['operation'] = 'get_list'
                    self._log(f"  [Op Fix] Corrected operation: {operation} -> get_list", "FIX")
            elif 'operation: delete_at' in step_lower or 'delete_at' in step_lower or 'delete' in step_lower:
                if operation != 'delete_at':
                    tool_args = dict(tool_args)
                    tool_args['operation'] = 'delete_at'
                    self._log(f"  [Op Fix] Corrected operation: {operation} -> delete_at", "FIX")

            # Re-get operation after possible correction
            operation = tool_args.get('operation')

            # Heuristic 2: For append operations with ALL keyword: batch append ALL values
            step_lower = step_description.lower()
            if operation in ['append', 'prepend'] and value is None:
                # Smart batch append: if step description contains "ALL" / "所有", append all values at once
                if 'all' in step_lower or '所有' in step_description or '全部' in step_description:
                    tool_args = dict(tool_args)
                    tool_args['value'] = numbers  # Pass entire list for batch append
                    self._log(f"  [Batch Fix] Auto-filled ALL {len(numbers)} values: {numbers}", "FIX")
                elif numbers and call_index < len(numbers):
                    # Single value mode for sequential calls
                    tool_args = dict(tool_args)
                    tool_args['value'] = numbers[call_index]
                    self._log(f"  [Param Fix] Auto-filled value={tool_args['value']}", "FIX")

            # Heuristic 3: Delete index auto-fill
            if operation == 'delete_at' and tool_args.get('index') is None:
                # Pattern 1: "索引为N" - already 0-based, use directly
                idx_match = re.search(r'索引[为\s]*(\d+)', user_query)
                if idx_match:
                    idx = int(idx_match.group(1))
                    tool_args = dict(tool_args)
                    tool_args['index'] = idx  # already 0-based
                    self._log(f"  [Param Fix] Auto-filled index={idx} (from 索引N - 0-based)", "FIX")
                # Pattern 2: "第N个" or "N-th node" - 1-based, convert to 0-based
                else:
                    idx_match = re.search(r'第(\d+)个|(\d+)(st|nd|rd|th).*node|index\s*(\d+)\s*node', user_query.lower())
                    if idx_match:
                        idx = int([g for g in idx_match.groups() if g][0])
                        tool_args = dict(tool_args)
                        tool_args['index'] = idx - 1  # convert 1-based to 0-based
                        self._log(f"  [Param Fix] Auto-filled index={tool_args['index']} (from 第N个/N-th)", "FIX")
                    # Pattern 3: Chinese ordinal word pattern matching (第N个 where N is Chinese char)
                    else:
                        ordinal_map = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
                        for word, num in ordinal_map.items():
                            if f'第{word}个' in user_query:
                                tool_args = dict(tool_args)
                                tool_args['index'] = num - 1  # convert 1-based to 0-based
                                self._log(f"  [Param Fix] Auto-filled index={tool_args['index']} (from 第{word}个)", "FIX")
                                break

        return tool_args

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
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })

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
        """
        self.stats["total_queries"] += 1

        enhanced_system_prompt = self._build_system_prompt(user_query)

        if self.config.verbose:
            print(f"\n{'='*60}")
            print(f" DevPal received task: {user_query}")
            print(f"{'='*60}\n")

        plan = None
        if self.config.enable_planning and self.planner:
            self._log("Generating execution plan...")
            plan = self.planner.generate_plan(user_query)
            self.stats["plans_generated"] += 1

            feasible, issues = self.planner.evaluate_feasibility(plan)

            if self.config.verbose:
                print(f"\n{'='*60}")
                print(f" Execution Plan")
                print(f"{'='*60}")
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
                print(f"{'='*60}\n")

            if not feasible:
                return f"Plan not feasible: {'; '.join(issues)}"

        self.message_history.add_user(user_query)

        current_step_idx = 0
        final_result = ""

        for iteration in range(self.config.max_iterations):
            if plan and current_step_idx >= len(plan.steps):
                break

            self._log(f"Iteration {iteration + 1} - Step {current_step_idx + 1}/{len(plan.steps) if plan else 'N/A'}")

            if plan:
                current_step = plan.steps[current_step_idx]
                self._log(f"   Executing: {current_step.description}")

            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.config_obj.max_tokens,
                system=enhanced_system_prompt,
                messages=self.message_history.get_messages(),
                tools=self.tool_registry.get_tool_descriptions()
            )

            text_content, tool_calls = self._extract_response_content(response)

            if not tool_calls:
                if plan:
                    plan.mark_step_complete(
                        current_step_idx,
                        success=True,
                        result_summary=text_content[:200]
                    )
                    current_step_idx += 1

                if not plan or current_step_idx >= len(plan.steps):
                    final_result = text_content
                    break

                self.message_history.add_assistant(text_content)
                continue

            self._log(f" Calling {len(tool_calls)} tool(s)")

            self.message_history.add_tool_use_message(text_content, tool_calls)

            tool_results = []
            step_success = True
            step_error_msg = ""

            step_desc = plan.steps[current_step_idx].description if plan else ""
            for idx, tool_call in enumerate(tool_calls):
                tool_name = tool_call["name"]
                tool_args = tool_call["input"]
                tool_id = tool_call["id"]

                self.stats["tool_calls"] += 1

                # Intelligent parameter fix for LLM hallucinations
                tool_args = self._intelligent_param_fix(tool_name, tool_args, user_query, idx, step_desc)

                print(f"\n    Tool: {tool_name}")
                print(f"      Args: {tool_args}")

                result = self.tool_registry.execute_tool(tool_name, tool_args)

                if result.success:
                    print(f"      [OK] Success")
                    if self.config.show_tool_output:
                        output = result.content[:1000].replace('\n', '\n      ')
                        truncate_msg = "..." if len(result.content) > 1000 else ""
                        print(f"      Output:\n      {output}{truncate_msg}")
                else:
                    step_success = False
                    self.stats["tool_errors"] += 1
                    error_msg = result.error_message or "Unknown error"
                    step_error_msg = error_msg
                    print(f"      [FAIL] Failed: {error_msg}")

                tool_results.append({
                    "tool_use_id": tool_id,
                    "content": result.content if result.success else f"Error: {result.error_message}"
                })

            self.message_history.add_tool_results(tool_results)

            if self.config.enable_reflection and self.reflector:
                step_desc = plan.steps[current_step_idx].description if plan else "Execute tool"
                reflection = self.reflector.reflect_step(
                    step_description=step_desc,
                    execution_result={
                        'success': step_success,
                        'error': step_error_msg,
                        'content': str(tool_results)
                    }
                )
                self.stats["reflections_done"] += 1

                if self.config.show_reflection:
                    print(self.reflector.generate_reflection_report(reflection))

                if plan and reflection.need_plan_adjustment:
                    self._log(f"Adjusting plan: {reflection.adjustment_suggestion}")
                    plan = self.planner.adjust_plan(
                        plan,
                        current_step_idx,
                        {'success': step_success, 'error': step_error_msg},
                        reflection.adjustment_suggestion
                    )

            if plan:
                plan.mark_step_complete(
                    current_step_idx,
                    success=step_success,
                    result_summary="Tool execution completed",
                    error_message=None if step_success else step_error_msg
                )
                current_step_idx += 1

        if plan and self.config.enable_planning:
            print(f"\n{'='*60}")
            print(" Task Execution Summary")
            print(f"{'='*60}")
            print(self.planner.generate_final_summary(plan))

            if self.config.enable_reflection and self.reflector:
                final_reflection = self.reflector.reflect_final_result(
                    user_query,
                    final_result or "Task completed",
                    plan
                )
                self._log(f"Gained {len(final_reflection['lessons'])} lesson(s)")

        if not final_result:
            self._log("Generating final answer...")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.config_obj.max_tokens,
                system=enhanced_system_prompt + "\nPlease provide the final answer directly, do not call any tools.",
                messages=self.message_history.get_messages(),
                tools=[]
            )
            final_result, _ = self._extract_response_content(response)

        final_result = re.sub(r'<minimax:tool_call>.*?</minimax:tool_call>', '', final_result, flags=re.DOTALL)
        final_result = re.sub(r'<invoke.*?>.*?</invoke>', '', final_result, flags=re.DOTALL)
        final_result = final_result.strip()

        if self.memory.long_term is not None:
            self.memory.long_term.add_experience(
                f"Successfully completed task: {user_query[:50]}..."
            )

        return final_result

    def chat(self):
        """Start interactive chat mode"""
        print("=" * 60)
        print(" DevPal Agent - Interactive Chat")
        print("=" * 60)
        print(f" Available tools: {', '.join(self.tool_registry.list_tool_names())}")
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
                    print(f"\n Statistics:")
                    for k, v in self.stats.items():
                        print(f"   {k}: {v}")
                    print()
                    continue

                answer = self.run(user_input)

                print(f"\n DevPal:")
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
