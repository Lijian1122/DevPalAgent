# EnhancedScheduler Run Mode Integration Design

## Overview
Integrate AI-agnostic collaboration run modes into EnhancedScheduler to support propose-only, apply-only, and validate-only workflows.

## Changes Required

### 1. EnhancedScheduler.__init__
Add new parameters:
```python
def __init__(
    self,
    requirements_file: str,
    tool_registry,
    # ... existing params ...
    run_mode: RunMode = RunMode.FULL,  # NEW
    change_id: str | None = None,      # NEW for apply/validate modes
):
```

### 2. Import and Store Mode Policy
```python
from ...collaboration.modes import RunMode, get_mode_policy
from ...collaboration.change_loader import ChangeLoader
from ...collaboration.context_restorer import ContextRestorer

self.run_mode = run_mode
self.mode_policy = get_mode_policy(run_mode)
self.change_id = change_id
```

### 3. Context Restoration (for APPLY/VALIDATE modes)
In `run_all_phases()`, before phase loop:
```python
if self.mode_policy.require_existing_change:
    if not self.change_id:
        raise ValueError(f"{self.run_mode} requires --change-id")
    
    loader = ChangeLoader(self.context.project_dir.parent)
    artifacts = loader.load_change(self.change_id)
    
    restorer = ContextRestorer()
    restorer.restore_context(
        self.context.project_dir.parent,
        artifacts,
        self.context
    )
    print(f"[INFO] Context restored from change: {self.change_id}")
```

### 4. Phase Skip Logic
In `_run_phases_with_enhancements()`, add check after line 577:
```python
for i in range(start_phase, len(phases) + 1):
    phase = phases[i - 1]
    
    # NEW: Check run mode policy
  if not self.mode_policy.should_run_phase(i):
        skip_msg = f"[SKIP] Phase {i} - outside run mode range ({self.run_mode})"
      print(skip_msg)
        if context.logger:
            context.logger.info(skip_msg)
        
        skip_data = {"skipped": True, "skip_reason": f"run_mode={self.run_mode}"}
        result = PhaseResult.ok(f"Skipped by run mode", **skip_data)
      context.set_phase_result(i, result)
        if self.checkpoint:
          self.checkpoint.save(i, True, context)
        continue
    
    # Check checkpoint first (existing code)
    if self.checkpoint and self.checkpoint.is_phase_completed(i):
      ...
```

### 5. Early Termination (for PROPOSE_ONLY)
After each phase completes:
```python
# After line that sets phase result
if self.mode_policy.stop_after_phase and i == self.mode_policy.stop_after_phase:
    if self.mode_policy.generate_rule_pack:
        # Generate Rule Pack
        from ...collaboration.rule_pack_generator import RulePackGenerator
        generator = RulePackGenerator(context.project_dir.parent, self.change_id)
        generator.generate_all()
        print("[INFO] Rule Pack generated for collaboration")
    
    print(f"[INFO] {self.run_mode} mode completed at Phase {i}")
    break
```

### 6. Banner Update
Update the workflow banner to show run mode:
```python
print(f"  Run Mode: {self.run_mode.value}")
print(f"  Phase Range: {self.mode_policy.start_phase} - {self.mode_policy.stop_after_phase or 11}")
```

## Integration Points

### Phase-Specific Adjustments

#### Phase 4/5: Code/Test Generation
Check `mode_policy.allow_code_writes` / `allow_test_writes`:
```python
if not self.mode_policy.allow_code_writes:
    # Skip actual file writes, keep planning/design only
    pass
```

#### Phase 11: Archive Option
```python
if self.mode_policy.allow_archive and should_archive:
    from ...openspec.archive import ArchiveChangeService
    archiver = ArchiveChangeService()
    archiver.archive_change(context.project_dir.parent, self.change_id)
```
## Testing Strategy

1. **Unit Tests**: Test mode policy application
2. **Integration Tests**: 
   - PROPOSE_ONLY: Generates change, stops at Phase 3
   - APPLY_ONLY: Loads change, runs Phase 4-11
   - VALIDATE_ONLY: Loads change, runs Phase 9-11

## Rollout Plan

1. ✅ Create collaboration modules (DONE)
2. → Integrate into EnhancedScheduler (THIS)
3. → Add CLI parameters
4. → Test end-to-end
