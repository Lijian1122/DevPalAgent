## Spec-first Collaboration Rules

### Working with OpenSpec Changes

This project uses DevPalAgent's OpenSpec workflow for spec-first development.
All code changes should be aligned with OpenSpec Change artifacts.

#### Reading a Change

Before implementing, always read the change artifacts:

```bash
# List available changes
ls openspec/changes/

# Read change artifacts
cat openspec/changes/<change-id>/proposal.md
cat openspec/changes/<change-id>/tasks.md
cat openspec/changes/<change-id>/design.md
cat openspec/changes/<change-id>/specs/spec.md
```

#### Implementation Guidelines

1. **Follow tasks.md**: Only implement tasks listed in `tasks.md`
2. **Preserve traceability**: Add requirement IDs in comments when available
3. **Minimal scope**: Do not introduce unrelated refactors
4. **Test coverage**: Ensure tests cover all requirements

#### Validation
After implementation, run DevPalAgent validation:

```bash
# Validate your changes
python run_ai_flow.py --validate-change <change-id>

# If validation passes, archive the change
python -m devpal.openspec archive <change-id>
```

#### Collaboration Commands

- `/opsx:propose <requirements-file>` - Generate OpenSpec Change
- `/opsx:apply <change-id>` - Implement based on change artifacts
- `/opsx:validate <change-id>` - Validate implementation
- `/opsx:archive <change-id>` - Archive completed change

### Do Not

- ❌ Modify code without reading change artifacts
- ❌ Archive changes manually (use DevPalAgent)
- ❌ Skip validation before archiving
- ❌ Introduce features not in tasks.md
