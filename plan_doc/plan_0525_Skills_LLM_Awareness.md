# Plan: Expose Skills Information to LLM in Plan-Act-Reflect Mode

## Context

**Problem**: When the SkillRouter falls back to Plan-Act-Reflect mode (confidence < 0.8), the LLM has no awareness of available Skills. The system prompt only exposes tool names, not high-level capabilities (Skills). This creates two critical issues:

1. **LLM doesn't know Skills exist**: When planning, the LLM cannot reason about or suggest using high-level capabilities like "OpenSpecSkill" or "TestGenerationSkill"
2. **LLM cannot guide users**: The LLM cannot recommend appropriate Skills for complex tasks that would benefit from orchestrated workflows

**Why this matters**: Skills represent task-level capabilities that orchestrate multiple tools and phases. For example:
- `OpenSpecSkill`: Executes complete 11-phase workflow (requirements → code → tests → docs)
- `TestGenerationSkill`: Orchestrates test generation flow (docs → code → execution)
- `CodeReviewSkill`: Reviews code quality and generates reports

Without Skills awareness, the LLM may attempt to manually orchestrate what a Skill already handles, or miss opportunities to suggest better approaches.

**Current Architecture**:
```
User Query → SkillRouter.route() → Confidence Check
                        ↓
                         ≥ 0.8: Execute Skill directly
                              < 0.8: Fallback to Plan-Act-Reflect
                                ↓
                    LLM sees only: tool_names (comma-separated)
                      LLM doesn't see: Skills metadata
```

**Goal**: Inject Skills information into the LLM's system prompt so it can:
- Understand available high-level capabilities
- Suggest appropriate Skills in Plans
- Guide users toward better task orchestration
- Make informed decisions about when to use Skills vs. direct tool calls

---

## Implementation Plan

### Phase 1: Create Skills Formatting Method

**File**: `devpal/core/agent_engine.py`

**Add new method** after `_build_base_system_prompt()` (around line 413):

```python
def _format_skills_for_prompt(self) -> str:
    """
    Format Skills information for LLM system prompt
    
    Returns:
        Formatted string describing available Skills with metadata
    """
    if not self.skill_router or not self.skill_router.skills:
        return ""
    
    skills_lines = []
    skills_lines.append("## Available Skills (High-Level Task Capabilities)")
    skills_lines.append("")
    skills_lines.append("Skills are specialized workflows that orchestrate multiple tools and phases.")
    skills_lines.append("When planning complex tasks, consider suggesting these Skills:")
    skills_lines.append("")
    
    for skill in self.skill_router.skills:
    # Format: **skill_name**: description
        skills_lines.append(f"**{skill.name}**:")
        skills_lines.append(f"  - Description: {skill.description}")
        
        # Add triggers as usage hints
        if skill.triggers:
            trigger_examples = ", ".join(f'"{t}"' for t in skill.triggers[:3])
            skills_lines.append(f"  - Triggered by keywords: {trigger_examples}")
     
        # Add required tools if any
        if skill.required_tools:
            tools_str = ", ".join(skill.required_tools)
            skills_lines.append(f"  - Requires tools: {tools_str}")
        
        skills_lines.append("")
    
    skills_lines.append("**When to suggest Skills**:")
    skills_lines.append("- For end-to-end workflows (requirements → code → tests)")
    skills_lines.append("- For complex multi-phase tasks")
    skills_lines.append("- When user query matches skill triggers")
    skills_lines.append("- When orchestrating multiple tools would be complex")
    skills_lines.append("")
    
    return "\n".join(skills_lines)
```

**Why this approach**:
- Provides structured, readable format for LLM
- Includes actionable metadata (triggers, required tools)
- Explains when Skills are appropriate
- Maintains separation of concerns (formatting logic separate from prompt building)

---

### Phase 2: Inject Skills into System Prompt

**File**: `devpal/core/agent_engine.py`

**Modify** `_build_base_system_prompt()` method (lines 391-412):

**Current code**:
```python
def _build_base_system_prompt(self) -> str:
    """Build base system prompt""
    tool_names = ", ".join(self.tool_registry.list_tool_names())
    return f"""You are DevPal, a professional C++/Python development assistant.

You can use the following tools to help users: {tool_names}

CRITICAL GUIDELINES FOR TOOL CALLS:
...
```

**New code**:
```python
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
```

**Key changes**:
1. Call `_format_skills_for_prompt()` to get Skills section
2. Insert Skills section at the top (high-level capabilities first)
3. Rename "Available Tools" section to clarify hierarchy
4. Add guidance on when to suggest Skills vs. use tools directly
5. Update "How to work" section to include Skills awareness

---

### Phase 3: Update Planner System Prompt

**File**: `devpal/core/planner.py`

**Modify** `_default_system_prompt()` method (lines 115-141):

**Current code**:
```python
def _default_system_prompt(self) -> str:
    return """You are a professional software development planning expert.
Your job is to decompose user requirements into clear, executable steps.

Planning principles:
1. First understand the core need, then decompose into steps
...
```

**New code**:
```python
def _default_system_prompt(self) -> str:
    # Get available tools and skills info
    tool_names = []
    if self.tool_registry:
        tool_names = self.tool_registry.list_tool_names()
    
    tools_str = ", ".join(tool_names) if tool_names else "standard development tools"
    
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
```

**Key changes**:
1. Inject available tools list dynamically
2. Add "Available capabilities" section distinguishing Skills from Tools
3. Update planning principles to consider Skills first for complex tasks
4. Add `recommended_skill` field to JSON output format
5. Allow `tool_needed` to reference Skills, not just tools

---

### Phase 4: Update Plan Data Structure

**File**: `devpal/core/planner.py`

**Modify** `Plan` dataclass (lines 26-35):

**Add new field**:
```python
@dataclass
class Plan:
    """Complete execution plan"""
    original_query: str
    steps: List[PlanStep] = field(default_factory=list)
    overall_goal: str = ""
    complexity: str = "medium"  # simple, medium, complex
    recommended_skill: Optional[str] = None  # NEW: Skill recommendation from planner
    created_at: datetime = field(default_factory=datetime.now)
    current_step_index: int = 0
    feasibility_score: float = 0.8  # Feasibility score 0-1
```

**Why**: Allows Planner to explicitly recommend a Skill, which can be used by AgentEngine to re-route to SkillRouter.

---

### Phase 5: Handle Skill Recommendations in AgentEngine

**File**: `devpal/core/agent_engine.py`

**Modify** `run()` method (around lines 726-730):

**Current code**:
```python
plan = None
if self.config.enable_planning and self.planner:
    self._log("Generating execution plan...")
    plan = self.planner.generate_plan(user_query)
```

**New code**:
```python
plan = None
if self.config.enable_planning and self.planner:
    self._log("Generating execution plan...")
    plan = self.planner.generate_plan(user_query)
    
    # Check if Planner recommends a Skill
    if plan and plan.recommended_skill:
        self._log(f"Planner recommends Skill: {plan.recommended_skill}")
        
        # Try to get the recommended skill
        recommended_skill_obj = self.skill_router.get_skill(plan.recommended_skill)
        
        if recommended_skill_obj:
            # Re-route to the recommended Skill
            skill_context = SkillContext(
                user_query=user_query,
             workspace_path=self.workspace_path,
                tool_registry=self.tool_registry
            )
            
            try:
                self._log(f"Executing recommended Skill: {plan.recommended_skill}")
                skill_result = recommended_skill_obj.execute(skill_context)
                
            if skill_result.success:
                result_msg = f"{skill_result.content}"
               if skill_result.artifacts:
                  result_msg += "\nGenerated artifacts:\n"
                    for artifact in skill_result.artifacts:
                    result_msg += f"  - {artifact}\n"
                 return result_msg
              else:
                    self._log(f"Recommended Skill failed, continuing with Plan-Act-Reflect")
            except Exception as e:
            self._log(f"Recommended Skill error: {e}, continuing with Plan-Act-Reflect")
```

**Why**: Enables LLM-guided Skill selection. If the Planner (powered by LLM) recognizes a task that matches a Skill, it can recommend it, and AgentEngine will execute it.

---

### Phase 6: Update Plan Parsing Logic

**File**: `devpal/core/planner.py`

**Modify** `generate_plan()` method (around line 143+):

Find the JSON parsing section and update it to extract `recommended_skill`:

```python
# After parsing JSON response
plan_data = json.loads(json_str)

# Extract recommended_skill if present
recommended_skill = plan_data.get("recommended_skill", None)

# Create Plan object
plan = Plan(
    original_query=query,
    overall_goal=plan_data.get("overall_goal", ""),
    complexity=plan_data.get("complexity", "medium"),
    recommended_skill=recommended_skill,  # NEW
    feasibility_score=feasibility_score
)
```

**Note**: Need to locate exact line numbers by reading the full `generate_plan()` method implementation.

---

## Critical Files to Modify

1. **`devpal/core/agent_engine.py`** (lines 391-412, 726-730)
   - Add `_format_skills_for_prompt()` method
   - Modify `_build_base_system_prompt()` to inject Skills
   - Modify `run()` to handle Skill recommendations

2. **`devpal/core/planner.py`** (lines 26-35, 115-141, 143+)
   - Add `recommended_skill` field to `Plan` dataclass
   - Update `_default_system_prompt()` to include Skills awareness
   - Update `generate_plan()` to parse `recommended_skill` from LLM response
---

## Verification Plan

### Test 1: Skills Visible in System Prompt
```python
# In Python REPL or test script
from devpal.core.agent_engine import AgentEngine

engine = AgentEngine()
system_prompt = engine._build_base_system_prompt()
# Verify Skills section exists
assert "Available Skills" in system_prompt
assert "openspec_skill" in system_prompt
assert "test_generation_skill" in system_prompt
print("✓ Skills are visible in system prompt")
```

### Test 2: Planner Recommends Skills
```python
from devpal.core.planner import Planner
from devpal.tools.registry import registry

planner = Planner(tool_registry=registry)
plan = planner.generate_plan("Generate a complete project from requirements/login.md")

# Check if Planner recommends OpenSpecSkill
print(f"Recommended Skill: {plan.recommended_skill}")
assert plan.recommended_skill in ["openspec_skill", None]
print("✓ Planner can recommend Skills")
```

### Test 3: End-to-End Skill Recommendation Flow
```python
from devpal.core.agent_engine import AgentEngine

engine = AgentEngine()
result = engine.run("Create a complete project from requirements/simple_login.md")

# Verify that either:
# 1. SkillRouter directly routed to OpenSpecSkill (confidence ≥ 0.8)
# 2. Planner recommended OpenSpecSkill and it was executed
# 3. Plan-Act-Reflect executed with Skills awareness

print(f"Result: {result}")
print("✓ End-to-end flow works with Skills awareness")
```

### Test 4: LLM Can Suggest Skills in Conversation
```python
# Manual test: Ask LLM about capabilities
engine = AgentEngine()
result = engine.run("What can you help me with for complex project generation?")

# Verify LLM mentions Skills in response
assert any(skill in result.lower() for skill in ["openspec", "test generation", "code review"])
print("✓ LLM can describe Skills capabilities")
```

### Test 5: Fallback Still Works
```python
# Test that simple queries still work without Skills
engine = AgentEngine()
result = engine.run("Read the file README.md")

# Should use file_reader tool directly, not route through Skills
print(f"Result: {result}")
print("✓ Simple tool calls still work without Skills overhead")
```

---

## Expected Outcomes
### Before Implementation
- LLM system prompt: Only lists tool names (comma-separated)
- Planner: No awareness of Skills, only tools
- Fallback behavior: LLM tries to manually orchestrate tools
- User experience: No guidance toward high-level capabilities

### After Implementation
- LLM system prompt: Includes Skills section with descriptions, triggers, and usage guidance
- Planner: Can recommend Skills for complex tasks
- Fallback behavior: LLM suggests appropriate Skills or orchestrates tools intelligently
- User experience: Better guidance, more efficient task routing

### Example Interaction

**User**: "Generate a complete login system from requirements/login.md"

**Before**:
```
SkillRouter: confidence=0.7 (< 0.8) → Fallback to Planner
Planner: Creates 8-step plan with manual tool orchestration
Result: Executes steps one by one, may miss OpenSpec workflow benefits
```

**After**:
```
SkillRouter: confidence=0.7 (< 0.8) → Fallback to Planner
Planner: "I recommend using openspec_skill for this end-to-end task"
AgentEngine: Re-routes to OpenSpecSkill
Result: Executes complete 11-phase workflow efficiently
```

---

## Risk Assessment

### Low Risk
- Adding Skills information to system prompt (read-only, informational)
- Creating `_format_skills_for_prompt()` method (pure function)

### Medium Risk
- Modifying `_build_base_system_prompt()` (affects all LLM interactions)
  - Mitigation: Test thoroughly, ensure backward compatibility
- Adding `recommended_skill` field to Plan (schema change)
  - Mitigation: Optional field with default `None`, backward compatible

### High Risk
- Modifying `run()` method to handle Skill recommendations (execution flow change)
  - Mitigation: Add try-except blocks, fallback to original Plan-Act-Reflect if Skill fails
  - Mitigation: Extensive testing with various query types

---

## Alternative Approaches Considered

### Alternative 1: Tool-Based Skill Invocation
**Idea**: Create a special "skill_invoker" tool that LLM can call to execute Skills.

**Pros**: 
- LLM has explicit control over Skill execution
- Fits existing tool-calling paradigm

**Cons**:
- Adds complexity (tool wrapping Skills)
- Requires LLM to understand when to use tool vs. Skill
- May confuse hierarchy (Skills orchestrate tools, not the other way around)

**Decision**: Rejected. Skills are higher-level than tools; better to expose them as capabilities in system prompt.

### Alternative 2: Separate Skills Prompt Section
**Idea**: Create a dedicated "Skills Guide" that's injected only when confidence is low.

**Pros**:
- Reduces token usage when Skills aren't needed
- More targeted information

**Cons**:
- Inconsistent LLM context (sometimes sees Skills, sometimes doesn't)
- Harder to maintain (conditional prompt injection)

**Decision**: Rejected. Better to always expose Skills for consistent LLM understanding.

### Alternative 3: Dynamic Skill Loading
**Idea**: Only inject Skills that match query keywords.

**Pros**:
- Reduces prompt size
- More focused information

**Cons**:
- Requires keyword matching logic (duplicates SkillRouter logic)
- LLM may not see relevant Skills if keywords don't match perfectly

**Decision**: Rejected. All Skills should be visible for LLM to make informed decisions.

---

## Implementation Notes

1. **Token Usage**: Adding Skills information will increase system prompt size by ~200-300 tokens (5 Skills × 50 tokens each). This is acceptable given the 200K context window.

2. **Backward Compatibility**: All changes are additive (new fields, new methods). Existing code paths remain functional.

3. **Testing Strategy**: Start with unit tests for formatting methods, then integration tests for Planner, finally end-to-end tests for AgentEngine.

4. **Rollout**: Can be feature-flagged if needed (e.g., `config.enable_skills_in_prompt = True`).

---

## Success Criteria

✅ Skills information is visible in LLM system prompt  
✅ Planner can recommend Skills for complex tasks  
✅ AgentEngine can execute recommended Skills  
✅ LLM can describe Skills capabilities when asked  
✅ Simple tool calls still work without Skills overhead  
✅ End-to-end workflow (SkillRouter → Planner → Skill execution) functions correctly  
✅ No regression in existing functionality
