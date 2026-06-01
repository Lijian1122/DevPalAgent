# Archive + Traceability Lifecycle Guide

## Overview

The Archive + Traceability system provides a complete lifecycle for OpenSpec changes, from proposal to implementation to archival. It ensures that every requirement, code file, test, and report maintains a traceable connection throughout the project's evolution.

## Architecture

### Components

1. **ArchiveChangeService** (`devpal/openspec/archive.py`)
   - Orchestrates the archive process
   - Updates metadata and artifact graph
   - Generates coverage matrix

2. **SpecMerger** (`devpal/openspec/spec_merge.py`)
   - Merges change specs into `openspec/specs/main.md`
   - Maintains idempotency with change markers

3. **CoverageMatrixBuilder** (`devpal/openspec/coverage.py`)
   - Generates Requirement → Code → Test → Report matrix
   - Calculates coverage percentages

4. **ArtifactGraph** (`.spec/artifact_graph.json`)
   - Maintains traceability between all artifacts
   - Stores archive metadata on nodes

## Workflow

### 1. Change Creation

During OpenSpec execution (Phases 1-11), a change is created:
```
project/
├── openspec/
│   └── changes/
│       └── <change-id>/
│           ├── metadata.json          # Change metadata
│           ├── proposal.md            # Initial proposal
│           ├── tasks.md             # Task breakdown
│           ├── design.md              # Technical design
│       └── specs/
│               └── spec.md            # Detailed specification
```

**metadata.json** structure:
```json
{
  "change_id": "feature-001",
  "status": "IMPLEMENTED",
  "requirements": ["REQ-001", "REQ-002"],
  "created_at": "2026-06-01T10:00:00Z"
}
```

### 2. Archive Command

After implementation is complete, archive the change:

```bash
python -m devpal.openspec archive <change-id> --project-dir <path>
```

**What happens:**

1. **Preflight Check**
   - Verifies all required files exist:
     - `metadata.json`
     - `proposal.md`
     - `tasks.md`
     - `design.md`
     - `specs/spec.md`

2. **Spec Merge**
   - Merges `specs/spec.md` into `openspec/specs/main.md`
   - Adds change markers for idempotency:
     ```markdown
     <!-- change:feature-001 -->
     ## Change: feature-001
     
     ### REQ-001
     Feature description...
     
     <!-- /change:feature-001 -->
     ```

3. **Metadata Update**
   - Updates change status to `ARCHIVED`
   - Records `archived_at` timestamp
   - Records `merged_into` path

4. **Coverage Matrix Generation**
   - Scans project for code, tests, and reports
   - Maps requirements to artifacts
   - Generates `.spec/coverage_matrix.md`:
     ```markdown
     # Coverage Matrix
   
     Change: `feature-001`
     
     | Requirement | Code | Tests | Report | Status |
     |-------------|------|-------|--------|------|
     | REQ-001 | src/feature.cpp | tests/test_feature.cpp | docs/final_report.md | VERIFIED |
     ```

5. **ArtifactGraph Update**
   - Adds archive metadata to all nodes:
     ```json
     {
       "id": "file:src/feature.cpp",
     "type": "code",
       "metadata": {
         "change_id": "feature-001",
         "introduced_by": "openspec/changes/feature-001",
         "archived_at": "2026-06-01T12:00:00Z",
         "requirement_ids": ["REQ-001", "REQ-002"]
       }
     }
     ```
   - Adds archive section:
     ```json
     {
       "archive": {
         "feature-001": {
         "status": "ARCHIVED",
           "archived_at": "2026-06-01T12:00:00Z",
           "introduced_by": "openspec/changes/feature-001"
         }
    }
     }
     ```

6. **Manifest Creation**
   - Creates `.spec/archive/<change-id>.json`:
     ```json
     {
       "change_id": "feature-001",
       "status": "ARCHIVED",
       "archived_at": "2026-06-01T12:00:00Z",
       "metadata": {...},
       "merged_spec_path": "openspec/specs/main.md",
       "spec_merged": true,
     "coverage": {
         "path": ".spec/coverage_matrix.md",
         "total_requirements": 2,
         "covered_requirements": 2,
         "coverage_percent": 100
       }
     }
     ```

### 3. Phase 11 Integration

Phase 11 (Final Report) automatically includes archive information:

```markdown
### Archive Summary

| Change | Status | Archived At | Coverage |
|--------|--------|-------------|----------|
| feature-001 | ARCHIVED | 2026-06-01T12:00:00Z | 100% |

Coverage matrix: `.spec/coverage_matrix.md`
```

## Traceability Chain

The archive system maintains complete traceability:

```
Requirement (REQ-001)
    ↓ implements
Code (src/feature.cpp)
    ↓ tests
Test (tests/test_feature.cpp)
    ↓ documents
Report (docs/final_report.md)
```

All connections are preserved in:
- **ArtifactGraph edges**: Explicit relationships
- **Node metadata**: `change_id`, `requirement_ids`, `introduced_by`
- **Coverage matrix**: Requirement → Code → Test → Report mapping

## State Transitions

```
PROPOSED → IN_PROGRESS → IMPLEMENTED → ARCHIVED
```

- **PROPOSED**: Change created, not yet started
- **IN_PROGRESS**: Implementation underway
- **IMPLEMENTED**: Code complete, ready to archive
- **ARCHIVED**: Merged to main spec, traceability locked

## Idempotency

Running archive multiple times is safe:
- Spec merge checks for existing markers
- Metadata updates are idempotent
- Coverage matrix regenerates with same results
- Artifact graph updates are additive

## EventBus Integration

Archive operations emit events:
- `archive.started`
- `archive.preflight_completed`
- `archive.spec_merged`
- `archive.coverage_generated`
- `archive.completed`
- `archive.failed`

Events are logged to `.spec/events.jsonl` for observability.

## CLI Usage

### Archive a change
```bash
python -m devpal.openspec archive feature-001
```

### Archive with custom project directory
```bash
python -m devpal.openspec archive feature-001 --project-dir /path/to/project
```

### Output format
```json
{
  "change_id": "feature-001",
  "success": true,
  "status": "ARCHIVED",
  "archived_at": "2026-06-01T12:00:00Z",
  "merged_spec_path": "/path/to/openspec/specs/main.md",
  "coverage_matrix_path": "/path/to/.spec/coverage_matrix.md",
  "manifest_path": "/path/to/.spec/archive/feature-001.json",
  "errors": [],
  "metadata": {
    "merged": true,
    "coverage_percent": 100,
    "total_requirements": 2,
    "covered_requirements": 2
  }
}
```

## Testing

### Unit Tests
```bash
python -m pytest tests/openspec/test_archive_lifecycle.py -v
```

### End-to-End Tests
```bash
python -m pytest tests/e2e/test_archive_e2e.py -v
```

## Best Practices

1. **Archive after implementation**: Only archive when code, tests, and docs are complete
2. **Verify coverage**: Check coverage matrix before archiving
3. **Review main spec**: Ensure merged spec is correct
4. **Preserve change directory**: Don't delete `openspec/changes/<change-id>` after archiving
5. **Use EventBus**: Monitor archive events for debugging

## Future Enhancements

- **Archive validation**: Pre-archive checks for code quality
- **Archive rollback**: Undo archive operation
- **Archive search**: Query archived changes by requirement
- **Archive analytics**: Trend analysis of coverage over time
- **Multi-change archive**: Archive multiple changes at once

## Related Documentation

- [OpenSpec Workflow](../doc3.0/agent_architecture.md)
- [ArtifactGraph](../doc3.0/artifact_graph.md)
- [EventBus](../doc3.0/eventbus.md)
- [Phase 11 Final Report](../doc3.0/phase11.md)
