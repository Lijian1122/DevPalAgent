# Windows Sandbox Backend Design

> Scope: initial DevPalAgent sandbox backend architecture. Phase 0/1 implements schema and policy backend abstraction only. Windows process and HCS/Hyper-V backends are future phases.

## 1. Design Goal

DevPalAgent currently has a policy-level sandbox implemented by `SandboxSession`. It provides path validation, command validation, sandbox workspace, legacy manifest writing, and production merge gate integration.

The next architecture step is to split sandbox behavior into two layers:

```text
Sandbox Policy Layer
  -> validates allowed paths, commands, network mode, timeout, resource limits
  -> creates a request and manifest

Sandbox Backend Layer
  -> decides where and how execution happens
  -> policy backend today
  -> Windows process backend later
  -> HCS / Hyper-V container backend later
```

This allows the OpenSpec workflow and multi-agent code path to keep using the same policy and audit model while execution isolation becomes stronger over time.

## 2. Backend Layers

```text
OpenSpec Phase / Agent Task
  -> SandboxRequest
  -> SandboxBackend
    -> PolicySandboxBackend
    -> WindowsProcessSandboxBackend
    -> WindowsContainerSandboxBackend
  -> SandboxResult
  -> Manifest v2
  -> EventBus / Final Report
  -> SandboxMergeService
```

## 3. Phase 0/1 Components

Implemented in Phase 0/1:

```text
devpal/core/sandbox/
  __init__.py
  models.py
  manifest.py
  backends/
    __init__.py
    base.py
    policy.py
```

Responsibilities:

- `models.py`: shared sandbox dataclasses such as `SandboxPolicy`, `SandboxRequest`, `SandboxResult`, and `SandboxViolation`.
- `manifest.py`: manifest v2 build/read/write/validate helpers.
- `backends/base.py`: backend and session protocols.
- `backends/policy.py`: compatibility adapter around the existing `SandboxSession`.

## 4. Compatibility Strategy

Phase 1 does not rewrite `devpal/core/multi_agent/sandbox.py`.

Instead:

- Existing `SandboxSession` remains the source of truth for current path and command policy.
- `PolicySandboxBackend` wraps `SandboxSession` and exposes a backend-shaped session handle.
- Legacy `manifest.json` remains compatible with `SandboxMergeService`.
- New `manifest.v2.json` can be written by the backend for schema, audit, and future execution backends.

This avoids breaking existing production merge behavior while enabling future backend selection.

## 5. Manifest v2

Manifest v2 is an audit schema, not an enforcement mechanism by itself.

Required top-level fields:

- `schema_version`
- `sandbox_id`
- `execution_id`
- `task_id`
- `phase_number`
- `role`
- `backend`
- `isolation_level`
- `status`
- `policy`
- `workspace`
- `artifacts`
- `violations`
- `trace`

The schema records:

- Which backend executed the task.
- Which isolation level was requested.
- Which paths and commands were allowed or denied.
- Where sandbox files were stored.
- Which artifacts were produced.
- Which violations were detected.
- Which trace id ties the manifest back to EventBus/final report.

## 6. Windows Process Backend MVP

The first stronger Windows backend uses a Python orchestrator and a small C#/.NET runner:

```text
Python SandboxManager
  -> writes sandbox_request.json
  -> starts devpal-sandbox-runner.exe
  -> reads sandbox_result.json
  -> writes manifest v2
  -> emits EventBus events
```

Phase 2 MVP implementation:

- Python wrapper: `devpal/core/sandbox/backends/windows_process.py`
- C# runner source: `runners/windows/devpal-sandbox-runner/`
- Runner request schema: `devpal.sandbox.runner_request.v1`
- Runner result schema: `devpal.sandbox.runner_result.v1`

Runner MVP responsibilities:

- Create a per-run workspace.
- Start a child process.
- Attach process tree to a Windows Job Object.
- Enforce timeout.
- Capture stdout, stderr, exit code, duration.
- Kill process tree on timeout or abnormal exit.
- Write structured result JSON.

Future hardening:

- Restricted token.
- Low integrity process.
- AppContainer.
- Windows EventLog / ETW.
- Network policy through firewall/WFP or container networking.

## 7. Future HCS / Hyper-V Backend

The HCS/Hyper-V backend should be reserved for high-risk execution:

- Untrusted generated code.
- Dependency installation.
- Browser automation.
- Native binaries.
- Tasks requiring stronger filesystem/network isolation.

Expected responsibilities:

- Create or reuse a Hyper-V isolated Windows container.
- Copy or mount workspace.
- Execute command in container.
- Enforce timeout and resource quota.
- Collect artifacts.
- Destroy container and temporary layers.
- Write the same manifest v2 shape.

## 8. Backend Selection

Initial backend selection can be policy-driven:

| Risk | Backend | Reason |
| --- | --- | --- |
| low | policy | Fastest, current behavior |
| medium | windows_process | Better lifecycle/resource cleanup |
| high | windows_container | Stronger OS/container isolation |
| critical | remote_worker | Future distributed isolation |

## 9. Acceptance for Phase 0/1

Phase 0/1 is complete when:

- The threat model and this architecture document exist.
- Shared sandbox models exist.
- manifest v2 has read/write/schema validation tests.
- `PolicySandboxBackend` can create a session that preserves existing strict and production behavior.
- Existing sandbox merge tests continue to pass.
