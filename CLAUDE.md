# DevPalAgent

## Project Overview

DevPalAgent is a Spec-first Agentic SDLC Runtime that transforms requirements into verifiable, traceable, and self-healing software projects.

## Critical Development Rules

### File Writing Protocol

**IMPORTANT**: Before using the Write tool, ALWAYS follow this checklist:

1. ✅ **Prepare content completely** - Never call Write without full content ready
2. ✅ **Verify parameters** - Both `file_path` and `content` must be provided
3. ✅ **Check length** - If content > 150 lines, plan to chunk it
4. ✅ **Single call** - Call Write ONCE with complete parameters
**Reference**: `~/.claude/skills/write-file-correctly/README.md`

**Validation script**: 
```bash
python ~/.claude/skills/write-file-correctly/skill.py "<file_path>" "<content>"
```

### Common Mistakes to Avoid

❌ **NEVER do this**:
```python
Write()  # Missing parameters!
Write()  # Repeating the same error!
```

✅ **ALWAYS do this**:
```python
# Step 1: Prepare content in thinking
content = """
# Complete content here
...
"""

# Step 2: Call Write ONCE
Write(
    file_path="path/to/file.md",
    content=content
)
```

## Architecture

- **Agent Chain**: Planner → Executor → Reflector (Plan-Act-Reflect)
- **OpenSpec Runtime**: WorkflowExecutor → Scheduler → Context → Phase 1-11
- **Memory System**: Short-term / Long-term / Error Memory (3-tier)

## Core Modules

- `devpal/core/agent_engine.py` - Agent main engine
- `devpal/core/planner.py` - Task planner
- `devpal/core/reflector.py` - Reflector
- `devpal/memory/` - Memory system
- `devpal/tools/` - Tool registry
- `devpal/core/openspec_phases/` - 11-phase workflow

## Development Workflow

1. Read requirements from `requirements/*.md`
2. Run OpenSpec 11-phase workflow
3. Generate code, tests, docs
4. Quality gate validation
5. Test execution
6. Final report generation

## Testing

```bash
# Run OpenSpec flow
python run_ai_flow.py -r requirements/simple_login.md

# Run tests
python -m pytest tests/openspec/
python -m pytest tests/e2e/
```

## Documentation

- [README.md](README.md) - Main documentation
- [doc3.0/agent_architecture.md](doc3.0/agent_architecture.md) - Architecture details
- [doc3.0/interview_pitch.md](doc3.0/interview_pitch.md) - Interview guide
