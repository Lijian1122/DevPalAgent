# Windows Process Sandbox Backend Design

> Status: updated on 2026-07-02.
> Scope: DevPalAgent Phase 10 command execution sandbox. Current implementation is a Windows process backend MVP, not an HCS/Hyper-V strong isolation backend.

## 1. Why This Sandbox Was Added

DevPalAgent originally had a policy-level sandbox around multi-agent writes and command execution. That layer is still useful: it validates paths, command allow/deny rules, sandbox levels, manifest output, and production merge gates. However, Phase 10 is different from static code generation because it actually runs generated code and test commands.

The new `windows_process` backend was added for four reasons:

1. **Separate policy from execution**
   The old `SandboxSession` mixed policy checks and local execution behavior. The new backend split keeps deterministic policy in Python while allowing the execution engine to be swapped: `policy` today, `windows_process` for Phase 10, and HCS/Hyper-V later.

2. **Make test execution auditable**
   Phase 10 now writes runner request/result files and `manifest.v2.json`, emits EventBus sandbox execution events, and surfaces the backend summary in the final report. A failed or timed-out command can be traced through `workflow_id -> phase -> task_id -> sandbox_id -> runner_result`.

3. **Control process lifecycle better than raw `subprocess.run`**
   Test commands can hang or spawn child processes. The C# runner uses Windows Job Object support where available so the process tree can be cleaned up more reliably on timeout or runner shutdown.

4. **Create a bridge toward real Windows isolation**
   This is intentionally a process-level MVP. It does not claim container or VM isolation. Its value is that the OpenSpec workflow now talks to a backend-neutral request/result protocol, so future restricted token, AppContainer, WFP, ETW, HCS, or Hyper-V work can reuse the same Phase 10 integration.

## 2. Current Architecture

```text
run_ai_flow.py
  -> OpenSpecRunOptions(sandbox_backend="windows_process")
  -> EnhancedOpenSpecScheduler
  -> OpenSpecContext
  -> Phase10RunTests
  -> WindowsProcessSandboxBackend
  -> runner_request.json
  -> devpal-sandbox-runner.exe
  -> runner_result.json
  -> manifest.v2.json
  -> EventBus sandbox events
  -> Phase 11 final_report.md sandbox summary
```

Important implementation files:

| Area | File |
| --- | --- |
| CLI switch | `run_ai_flow.py` |
| Options facade | `devpal/core/openspec_executor.py` |
| Context/checkpoint fields | `devpal/core/openspec_phases/base.py` |
| Scheduler propagation | `devpal/core/openspec_phases/enhanced_scheduler.py` |
| Phase 10 integration | `devpal/core/openspec_phases/phase10_run_tests.py` |
| Python backend wrapper | `devpal/core/sandbox/backends/windows_process.py` |
| C# runner | `runners/windows/devpal-sandbox-runner/Program.cs` |
| Event models | `devpal/core/schema/workflow_events.py` |
| Event emit helpers | `devpal/core/schema/eventbus_integration.py` |
| Final report summary | `devpal/core/openspec_phases/phase11_final_report.py` |

## 3. Backend Selection

The CLI exposes:

```powershell
python run_ai_flow.py -r requirements/simple_login.md --sandbox-backend windows_process
```

Supported values:

| Backend | Meaning |
| --- | --- |
| `policy` | Default behavior. Python policy checks and local command execution path. |
| `windows_process` | Phase 10 commands are delegated to the Windows process runner. |

Programmatic configuration:

```python
OpenSpecRunOptions(
    sandbox_level="strict",
    sandbox_backend="windows_process",
    sandbox_backend_options={
        "runner_path": r"C:\code\DevPalAgent\runners\windows\devpal-sandbox-runner\bin\Release\net8.0\devpal-sandbox-runner.exe",
        "runner_timeout_grace_seconds": 5,
    },
)
```

If `runner_path` is not provided, the Python backend looks at `DEVPAL_SANDBOX_RUNNER`, then falls back to the Release build path under `runners/windows/devpal-sandbox-runner/bin/Release/net8.0/`.

## 4. Python Side Logic

`Phase10RunTests` decides whether a command should go through the new backend:

```text
_run_phase10_command(...)
  if context.sandbox_backend == "windows_process":
      _run_windows_process_backend_command(...)
  elif multi-agent execution enabled:
      MultiAgentCoordinator.execute_test_tasks(...)
  else:
      subprocess.run(...)
```

For `windows_process`, Phase 10 does the following:

1. Builds a `CommandSpec` from the Phase 10 command.
2. Builds a `SandboxRequest` with:
   - `project_dir`
   - `task_id`
   - `phase_number=10`
   - `role="test"`
   - `sandbox_level`
   - timeout and trace metadata
3. Creates `WindowsProcessSandboxBackend`.
4. Creates a backend session.
5. Emits `sandbox.created`.
6. Validates the command using the existing deterministic `SandboxSession` policy.
7. Emits `sandbox.policy_applied`.
8. Emits `sandbox.command_started`.
9. Runs the command through the C# runner.
10. Reads `runner_result.json`.
11. Emits timeout/completed/cleanup events.
12. Records the result into `context.parallel_execution_stats["10"]`.
13. Phase 11 turns those stats into the final report sandbox table.

This means the new backend did not bypass the existing policy layer. It reuses it, then delegates the actual process execution to C#.

## 5. Runner Request Protocol

The Python backend writes `.spec/sandboxes/<sandbox_id>/runner_request.json`.

Current schema version:

```text
devpal.sandbox.runner_request.v1
```

Important fields:

| Field | Meaning |
| --- | --- |
| `sandbox_id` | Stable task-derived sandbox id. |
| `execution_id` | Per-run execution id. |
| `backend` | `windows_process`. |
| `isolation_level` | `process`. |
| `project_dir` | Main project directory. |
| `sandbox_dir` | `.spec/sandboxes/<sandbox_id>`. |
| `workspace_dir` | Per-sandbox workspace directory. |
| `result_path` | Where the C# runner must write `runner_result.json`. |
| `command.argv` | Command array, never shell string. |
| `command.cwd` | Working directory. Must pass Python policy validation first. |
| `command.timeout_seconds` | Command timeout. |
| `command.env` | Explicit environment overrides. |
| `policy` | Serialized sandbox policy. |
| `trace` | Trace id and EventBus log path. |
| `metadata` | Workflow metadata. |

The command is passed as an argv list to avoid shell interpolation.

## 6. C# Runner Logic

The C# runner is a small `.NET 8` console application in:

```text
runners/windows/devpal-sandbox-runner/Program.cs
```

### 6.1 Entry Point

`Main(string[] args)` expects exactly one argument:

```text
devpal-sandbox-runner <sandbox_request.json>
```

Behavior:

1. If the argument count is wrong, print usage and return `2`.
2. Read the request JSON as UTF-8.
3. Deserialize it with `JsonNamingPolicy.SnakeCaseLower`, so C# properties map to snake_case JSON.
4. Validate that `request.command.argv` exists and is non-empty.
5. Create the workspace directory.
6. Create the parent directory for `result_path`.
7. Call `RunCommandAsync(request)`.
8. Write `runner_result.json` with UTF-8 no BOM.
9. Return `0` when `result.Success == true`, otherwise return `1`.

### 6.2 Process Creation

`RunCommandAsync` creates a `ProcessStartInfo`:

```text
FileName = command.argv[0]
ArgumentList = command.argv[1:]
WorkingDirectory = command.cwd or request.workspace_dir
UseShellExecute = false
RedirectStandardOutput = command.capture_output
RedirectStandardError = command.capture_output
CreateNoWindow = true
```

If `command.env` is present, each key/value is copied into `ProcessStartInfo.Environment`.

The runner does not execute through `cmd.exe` or PowerShell. This keeps the execution model closer to deterministic tool calls and avoids shell quoting surprises.

### 6.3 Job Object

Before starting the process, the runner attempts to create a Windows Job Object:

```text
Name = DevPalSandbox-<sandbox_id>
LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
Optional: JOB_OBJECT_LIMIT_ACTIVE_PROCESS
```

`JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` is the important lifecycle guard: when the job handle is closed, processes assigned to the job are cleaned up by Windows.

If `policy.max_processes` is present and greater than zero, the runner sets `ActiveProcessLimit` to restrict the number of processes in the job.

If the runner is not on Windows, `TryCreate` returns `null`; the process still runs, but without Job Object protection. That is useful for tests, but production Windows usage should expect the Job Object path.

### 6.4 Timeout Handling

After `process.Start()`:

1. The process is assigned to the Job Object if one exists.
2. stdout/stderr async reads are started when capture is enabled.
3. The runner waits up to `command.timeout_seconds`.
4. If the process does not exit:
   - call `process.Kill(entireProcessTree: true)`.
   - return a timeout result.
   - `cleanup_status = "killed"`.
   - `timed_out = true`.
   - `exit_code = -1`.

The Job Object is a second guard after `Kill(entireProcessTree: true)`.

### 6.5 Normal Result

On normal exit, the runner writes:

```json
{
  "schema_version": "devpal.sandbox.runner_result.v1",
  "sandbox_id": "...",
  "execution_id": "...",
  "status": "completed",
  "success": true,
  "argv": ["pytest", "tests", "-v"],
  "cwd": "...",
  "pid": 1234,
  "exit_code": 0,
  "stdout": "...",
  "stderr": "...",
  "duration_ms": 123,
  "timed_out": false,
  "cleanup_status": "clean",
  "job_object": "DevPalSandbox-..."
}
```

If the command exits non-zero:

- `status = "failed"`
- `success = false`
- `exit_code` is the process exit code
- stdout/stderr are still captured

### 6.6 Exception Result

If process startup or execution throws an exception, the runner still tries to write a structured result:

```text
status = "failed"
success = false
exit_code = -1
cleanup_status = "best_effort"
error = <exception message>
```

This keeps Phase 10 and final report behavior deterministic: the Python side can parse `runner_result.json` instead of only seeing a runner crash.

## 7. Runner Result and Manifest v2

The Python backend reads `.spec/sandboxes/<sandbox_id>/runner_result.json` and converts it into the shared `CommandResult`.

It then writes `.spec/sandboxes/<sandbox_id>/manifest.v2.json` with:

- backend: `windows_process`
- isolation_level: `process`
- status: `completed`, `failed`, or `timeout`
- runner return code
- runner stdout/stderr
- command result
- runner request/result paths
- policy and trace metadata

Phase 10 also stores sandbox metadata in `context.parallel_execution_stats["10"]`, including:

- `sandbox_id`
- `backend`
- `isolation_level`
- `manifest_v2_path`
- `runner_request_path`
- `runner_result_path`
- `cleanup_status`
- `timed_out`
- command argv/cwd/return code/duration

## 8. EventBus and Final Report

The backend emits these sandbox events:

| Event | When |
| --- | --- |
| `sandbox.created` | Backend session created. |
| `sandbox.policy_applied` | Deterministic policy accepted the command. |
| `sandbox.command_started` | Runner execution starts. |
| `sandbox.command_completed` | Runner execution completes or fails. |
| `sandbox.timeout` | Command timed out. |
| `sandbox.cleanup_completed` | Cleanup status is known. |
| `sandbox.violation` | Policy rejects the command before runner execution. |

Phase 11 includes a sandbox summary table with:

- Phase
- Task id
- Backend
- Isolation
- Sandbox id
- Success
- Duration
- Policy violations
- Timeout
- Cleanup
- Manifest path
- Manifest v2 path
- Runner result path

This gives the project a real audit trail for Phase 10 execution.

## 9. Current Security Boundary

Current `windows_process` backend improves lifecycle control and auditability, but it is not a strong isolation boundary.

What it does today:

- Reuses deterministic command/path policy before execution.
- Avoids shell execution.
- Creates per-task sandbox directories.
- Captures stdout/stderr/exit code/duration.
- Enforces timeout.
- Uses Windows Job Object cleanup on Windows.
- Records request/result/manifest/EventBus/final report evidence.

What it does not do yet:

- It does not use restricted token.
- It does not lower integrity level.
- It does not use AppContainer.
- It does not apply Windows ACL lockdown to the whole project or user profile.
- It does not enforce network isolation through WFP/firewall.
- It does not block IPC, COM, named pipes, or registry access.
- It does not provide HCS/Hyper-V container isolation.
- It should not be treated as safe against malicious native code.

The correct wording is:

> Current backend is a process-level execution sandbox with deterministic policy, timeout, Job Object cleanup, and audit trail. It is a stepping stone toward stronger Windows isolation, not a replacement for HCS/Hyper-V or AppContainer.

## 10. Why C# Was Used

The runner is implemented in C# because this phase needs direct and maintainable access to Windows process primitives:

- `System.Diagnostics.Process`
- `ProcessStartInfo.ArgumentList`
- `Kill(entireProcessTree: true)`
- P/Invoke for Job Object APIs:
  - `CreateJobObject`
  - `SetInformationJobObject`
  - `AssignProcessToJobObject`
  - `CloseHandle`

C# is also easier to ship as a small `.NET` runner in the current project than adding native C++ build complexity. If later work needs lower-level token manipulation, AppContainer profile management, ETW providers, or HCS wrappers, this runner can either grow more P/Invoke code or be replaced by a C++/Rust runner behind the same request/result protocol.

## 11. Next Hardening Steps

Recommended next steps:

1. Add runner request/result schema validation tests.
2. Add restricted token support.
3. Add low integrity process option.
4. Add explicit environment allowlist.
5. Add working-directory ACL hardening for sandbox workspace.
6. Add optional network deny policy through Windows Firewall/WFP.
7. Emit Windows EventLog or ETW audit events.
8. Add HCS/Hyper-V backend for high-risk commands.
9. Add red-team tests for prompt injection, command abuse, secret read attempts, and runaway child processes.

## 12. Acceptance Evidence

The current implementation is covered by targeted tests around:

- Windows process backend request/result/manifest behavior.
- Phase 10 selection of `windows_process`.
- Python pytest execution through the backend.
- EventBus sandbox execution events.
- Phase 11 sandbox final report summary.
- OpenSpec options and checkpoint preservation.

Representative test command:

```powershell
python -m pytest -p no:cacheprovider --basetemp .tmp\pytest_sandbox_switch `
  tests/openspec/test_phase10_run_tests.py `
  tests/openspec/test_phase11_final_report.py `
  tests/test_eventbus_integration.py `
  tests/openspec/test_openspec_executor.py `
  tests/openspec/test_sandbox_windows_process_backend.py
```
