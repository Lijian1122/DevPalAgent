# DevPalAgent Skill 注入流程详解

## 概述

DevPalAgent 中的 Skill 是通过 **System Prompt 注入** 的方式告知 LLM 的，而不是作为 Tool Schema 注入。这是一个关键的架构设计决策。

## 核心架构对比

### Tool vs Skill

| 维度 | Tool | Skill |
|------|------|-------|
| **抽象层级** | 低层级原子操作 | 高层级任务编排 |
| **注入方式** | Tool Schema (JSON) | System Prompt (文本描述) |
| **LLM 调用** | 直接 function calling | 推荐建议 + 路由决策 |
| **执行方式** | LLM 直接调用 | SkillRouter 路由执行 |
| **示例** | `file_reader`, `git_tool` | `OpenSpecSkill`, `InstallerSkill` |

## 完整注入流程

```
用户查询
    ↓
AgentEngine.run()
    ↓
1. Skill 路由阶段
    ├─ SkillRouter.route(context)
    │   ├─ 遍历所有 Skill
    │   ├─ 调用 skill.can_handle(context)
    │   └─ 返回最高置信度 Skill
    │
    ├─ 如果 confidence >= 0.8
    │   └─ 直接执行 skill.execute()
    │
    └─ 如果 confidence < 0.8
        └─ Fallback 到 Plan-Act-Reflect
            ↓
2. System Prompt 构建阶段
    ├─ _build_base_system_prompt()
    │   ├─ _format_skills_for_prompt()  ← 关键！
    │   │   ├─ 遍历 skill_router.skills
    │   │   ├─ 提取 skill.name, description, triggers
    │   │   └─ 格式化为文本描述
    │   │
    │   └─ registry.list_tool_names()
    │       └─ 获取所有 Tool 名称列表
    │
    └─ 生成完整 System Prompt
        ├─ Skills 信息（文本描述）
        └─ Tools 信息（名称列表）
         ↓
3. LLM 调用阶段
    ├─ client.messages.create()
    │   ├─ system: System Prompt（包含 Skill 描述）
    │   ├─ tools: Tool Schemas（JSON 格式）
    │   └─ messages: 对话历史
    │
    └─ LLM 响应
        ├─ 文本输出（可能推荐 Skill）
        └─ Tool Calls（直接调用 Tool）
            ↓
4. 响应处理阶段
    ├─ 如果 LLM 推荐 Skill
    │   └─ 重新路由到 SkillRouter
  │
    └─ 如果 LLM 调用 Tool
        └─ ToolRegistry.execute_tool()
```

## 关键代码路径

### 1. Skill 注册（AgentEngine 初始化）

```python
# devpal/core/agent_engine.py:156-165
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
```

### 2. Skill 信息格式化为 System Prompt

```python
# devpal/core/agent_engine.py:345-391
def _format_skills_for_prompt(self) -> str:
    """将 Skill 信息格式化为 LLM System Prompt"""
    
    skills_lines = []
    skills_lines.append("## Available Skills (High-Level Task Capabilities)")
    skills_lines.append("")
    skills_lines.append("Skills are specialized workflows that orchestrate multiple tools and phases.")
    
    for skill in self.skill_router.skills:
        skills_lines.append(f"**{skill.name}**:")
        skills_lines.append(f"  - Description: {skill.description}")
        
        if skill.triggers:
            trigger_examples = ", ".join(f'"{t}"' for t in skill.triggers[:3])
            skills_lines.append(f"  - Triggered by keywords: {trigger_examples}")
        
        if skill.required_tools:
            tools_str = ", ".join(skill.required_tools)
        skills_lines.append(f"  - Requires tools: {tools_str}")
        skills_lines.append("")
    
    return "\n".join(skills_lines)
```

### 3. Tool Schema 生成（对比）

```python
# devpal/tools/registry.py:114-116
def get_tool_descriptions(self) -> List[dict]:
    """获取所有工具的描述（用于 LLM）"""
    return [tool.to_function_call_format() for tool in self._tools.values()]

# devpal/tools/base.py:163-185
def to_function_call_format(self) -> Dict[str, Any]:
    """从 Pydantic 模型自动生成 Claude Tool 格式"""
    schema = self.Parameters.model_json_schema()
    
    return {
        "name": self.name,
        "description": self.description,
      "input_schema": {
            "type": "object",
            "properties": properties,
         "required": schema.get("required", [])
        }
    }
```

### 4. LLM 调用时的参数

```python
# devpal/core/llm_providers/anthropic.py:136-143
kwargs = {
    "model": self.model,
    "max_tokens": max_tokens,
    "system": system_blocks,      # ← Skill 信息在这里（文本）
    "messages": messages,
}
if tools:
    kwargs["tools"] = tools       # ← Tool Schema 在这里（JSON）

response = self._client.messages.create(**kwargs)
```

## 实际 System Prompt 示例

```
You are DevPal, a professional C++/Python development assistant.

## Available Skills (High-Level Task Capabilities)

Skills are specialized workflows that orchestrate multiple tools and phases.
When planning complex tasks, consider suggesting these Skills:

**OpenSpecSkill**:
  - Description: Execute complete OpenSpec 11-phase workflow from requirements to production
  - Triggered by keywords: "implement requirements", "generate project", "openspec"
  - Requires tools: spec_tool, project_generator, test_runner

**InstallerSkill**:
  - Description: Generate cross-platform installation scripts
  - Triggered by keywords: "install script", "setup script", "installer"
  - Requires tools: file_writer, command_executor

**CodeReviewSkill**:
  - Description: Perform comprehensive code review with quality metrics
  - Triggered by keywords: "code review", "review code", "check quality"
  - Requires tools: static_analyzer, code_review_tool

**When to suggest Skills**:
- For end-to-end workflows (requirements → code → tests)
- For complex multi-phase tasks
- When user query matches skill triggers
- When orchestrating multiple tools would be complex

## Available Tools (Low-Level Operations)

You can use the following tools for direct operations: file_reader, file_writer, 
command_executor, code_search, git_tool, test_runner, ...

CRITICAL GUIDELINES FOR TOOL CALLS:
1. ALWAYS extract actual parameter values from user query
2. Each tool call must have ALL required parameters filled
...
```

## 为什么 Skill 不用 Tool Schema？

### 设计理由

1. **抽象层级不同**
   - Tool: 原子操作，需要精确参数（JSON Schema 适合）
   - Skill: 任务编排，需要意图理解（自然语言描述更好）

2. **调用方式不同**
   - Tool: LLM 直接 function calling（需要严格 Schema）
   - Skill: LLM 推荐 → SkillRouter 路由（需要语义理解）

3. **灵活性需求**
   - Tool: 固定参数，确定性执行
   - Skill: 动态编排，上下文感知

4. **LLM 能力匹配**
   - Tool Schema: 利用 LLM 的 function calling 能力
   - Skill Description: 利用 LLM 的语义理解能力

### 实际效果

```python
# 用户查询: "帮我实现 requirements/login.md 的需求"

# Skill 路由阶段
skill_context = SkillContext(
    user_query="帮我实现 requirements/login.md 的需求",
    workspace_path=Path.cwd(),
    tool_registry=self.tool_registry,
)

skill, confidence = self.skill_router.route(skill_context)
# → OpenSpecSkill, confidence=0.9

# 直接执行 Skill（不需要 LLM 调用）
skill_result = skill.execute(skill_context)
# → 执行 11 阶段 OpenSpec 流程
```

## Skill 路由机制

### 置信度计算

```python
# devpal/skills/base.py:49-67
def can_handle(self, context: SkillContext) -> float:
    """判断是否能处理该任务
    
    Returns:
        float: 置信度 0.0-1.0
    """
    query_lower = context.user_query.lower()
    for trigger in self.triggers:
        if trigger.lower() in query_lower:
            return 0.8  # 匹配触发词 → 高置信度
    return 0.0  # 不匹配 → 零置信度
```

### 路由决策

```python
# devpal/skills/router.py:34-80
def route(self, context: SkillContext) -> Tuple[Optional[BaseSkill], float]:
    """路由到最匹配的 Skill"""
    
    best_skill = None
    best_confidence = 0.0
    
    # 计算每个 Skill 的置信度
    for skill in self.skills:
        confidence = skill.can_handle(context)
        if confidence > best_confidence:
            best_confidence = confidence
         best_skill = skill
    
    # 判断是否达到阈值
    if best_confidence >= self.confidence_threshold:  # 0.8
        return best_skill, best_confidence
  else:
        # Fallback 到 Planner（LLM 决策）
        return None, best_confidence
```

## Skill 与 Tool 的协同

### 执行流程

```
用户查询: "帮我生成登录功能的测试"
    ↓
SkillRouter 评估
    ├─ TestGenerationSkill: confidence=0.8 ✓
    ├─ OpenSpecSkill: confidence=0.0
    └─ InstallerSkill: confidence=0.0
    ↓
执行 TestGenerationSkill
    ├─ 调用 code_search (Tool)
    ├─ 调用 test_generator (Tool)
    ├─ 调用 file_writer (Tool)
    └─ 调用 test_runner (Tool)
    ↓
返回结果
```

### Skill 内部使用 Tool

```python
# devpal/skills/builtin/test_generation.py (示例)
class TestGenerationSkill(BaseSkill):
    name = "TestGenerationSkill"
    description = "Generate comprehensive test suites"
    triggers = ["generate tests", "create tests", "test generation"]
    required_tools = ["code_search", "test_generator", "file_writer"]
    
    def execute(self, context: SkillContext) -> SkillResult:
        # 1. 搜索源代码
        search_result = context.tool_registry.execute_tool(
         "code_search",
            {"pattern": "*.py", "path": context.workspace_path}
        )
     
        # 2. 生成测试
        test_result = context.tool_registry.execute_tool(
            "test_generator",
            {"source_files": search_result.content}
        )
        
        # 3. 写入文件
        write_result = context.tool_registry.execute_tool(
       "file_writer",
            {"path": "tests/test_generated.py", "content": test_result.content}
        )
    
        return SkillResult(
            success=True,
            content="Test suite generated successfully",
        artifacts=["tests/test_generated.py"]
        )
```

## 总结

### Skill 注入流程

1. **注册阶段**: AgentEngine 初始化时注册所有 Skill 到 SkillRouter
2. **格式化阶段**: `_format_skills_for_prompt()` 将 Skill 信息转为文本描述
3. **注入阶段**: 文本描述作为 System Prompt 的一部分传给 LLM
4. **路由阶段**: SkillRouter 基于触发词匹配决定是否执行 Skill
5. **执行阶段**: Skill 内部编排多个 Tool 完成复杂任务

### 关键特点

- **Skill 不是 Tool**: Skill 是任务编排器，Tool 是原子操作
- **文本描述 vs JSON Schema**: Skill 用自然语言描述，Tool 用结构化 Schema
- **推荐 vs 调用**: LLM 推荐 Skill，直接调用 Tool
- **路由决策**: SkillRouter 基于置信度决定是否执行 Skill
- **协同工作**: Skill 内部使用 Tool 完成具体操作

### 优势
1. **灵活性**: Skill 可以动态调整执行策略
2. **可扩展性**: 新增 Skill 不需要修改 LLM 接口
3. **语义理解**: 利用 LLM 的自然语言理解能力
4. **任务编排**: Skill 封装复杂的多步骤流程
5. **降低复杂度**: LLM 只需推荐 Skill，不需要理解内部实现
