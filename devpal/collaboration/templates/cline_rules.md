# Cline Spec-first Rules

## Overview

This project uses DevPalAgent's OpenSpec workflow. All changes must align with OpenSpec Change artifacts.

## Workflow

### 1. Read Change Artifacts

```bash
# Navigate to change directory
cd openspec/changes/<change-id>/

# Read artifacts
- proposal.md    # High-level proposal
- specs/spec.md  # Detailed specification
- tasks.md       # Task breakdown
- design.md      # Technical design
- metadata.json  # Change metadata
```

### 2. Implement

- Follow tasks in `tasks.md` exactly
- Add requirement IDs in comments: `// REQ-001: User login`
- Keep changes minimal
- Do not modify files outside change scope

### 3. Validate

```bash
python run_ai_flow.py --validate-change <change-id>
```

### 4. Archive

```bash
python -m devpal.openspec archive <change-id>
```

## Best Practices

✅ **Do**:
- Read all change artifacts before coding
- Ask before modifying files outside scope
- Preserve traceability
- Run validation before archiving

❌ **Don't**:
- Skip reading change artifacts
- Introduce unrelated changes
- Archive without validation
- Modify OpenSpec artifacts manually

## Commands

- `python run_ai_flow.py --propose-only -r <requirements>` - Generate change
- `python run_ai_flow.py --apply-change <change-id>` - Implement change
- `python run_ai_flow.py --validate-change <change-id>` - Validate
- `python -m devpal.openspec archive <change-id>` - Archive
