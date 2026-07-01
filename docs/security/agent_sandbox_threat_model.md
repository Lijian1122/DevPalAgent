# Agent Sandbox Threat Model

> Scope: DevPalAgent sandbox Phase 0 baseline. This document defines the initial threat model for Agent code execution and artifact merge governance. It is intentionally conservative: current DevPalAgent sandbox is a policy-level boundary, not an OS/container/VM strong isolation boundary.

## 1. Assets

Protected assets:

- Project source code, tests, docs, and OpenSpec artifacts.
- Local secrets such as API keys, shell history, SSH keys, cloud credentials, and `.env` files.
- User files outside the project workspace.
- Git history and remote repository state.
- Event logs, manifests, final reports, and archive metadata.
- Host machine integrity, including processes, network, and filesystem.

## 2. Trust Boundaries

Current DevPalAgent boundaries:

- LLM output is untrusted.
- Tool call requests from the model are untrusted until checked by deterministic policy.
- Sandbox workspace is a controlled staging area.
- `SandboxMergeService` is the explicit boundary for writing sandbox artifacts into the project.
- EventBus and manifest files are audit assets and should not be treated as enforcement by themselves.

Current non-boundaries:

- The current policy sandbox is not a kernel security boundary.
- The current policy sandbox does not prevent malicious native code from escaping the Python process.
- The current policy sandbox does not provide per-process network isolation, IPC isolation, or OS-level filesystem ACL enforcement.

## 3. Threats

| Threat | Example | Current Control | Remaining Gap |
| --- | --- | --- | --- |
| Path traversal | Agent writes `../secret.py` | Relative path normalization and allowed roots | No OS-level ACL isolation yet |
| Unauthorized project write | Agent writes `docs/` when only `src/foo.py` is allowed | `allowed_paths` and merge gate | Policy only; direct external writes are out of scope |
| Dangerous command execution | Agent requests `powershell`, `cmd`, `curl`, `ssh` | command deny list and production command block | Deny list is not a complete security boundary |
| Network exfiltration | Generated code posts files to remote server | command deny list for common network tools | Needs Windows Firewall/WFP/container network policy |
| Secret leakage | Agent reads `.env` or SSH key | allowed project roots and future secret scanning | Needs secret detector and OS-level access control |
| IPC abuse | Generated code connects to named pipe or COM object | Not covered today | Needs Windows token/AppContainer/container isolation |
| Sandbox escape | Malicious binary exploits host process | Not covered today | Needs process/container/VM backend |
| Prompt injection | Requirement tells Agent to ignore policy and leak files | Policy is deterministic and outside model control | Needs red-team tests and approval gates |
| Manifest tampering | Artifact hash is changed after generation | merge hash validation | Manifest signing is not implemented |
| Resource exhaustion | Agent starts many processes or hangs | command timeout in runner paths | Needs Job Object/resource quota/reaper |

## 4. Security Goals

Phase 0/1 goals:

- Keep all existing `SandboxSession` path and command policy behavior compatible.
- Define a backend abstraction so stronger execution backends can be added without changing OpenSpec phases.
- Define manifest v2 with explicit policy, backend, isolation level, workspace, artifacts, violations, and trace fields.
- Add schema validation for manifest v2 read/write.
- Document current limitations clearly.

Future goals:

- Add Windows process backend using Job Object, timeout cleanup, and reduced process privileges.
- Add optional restricted token / low integrity / AppContainer support.
- Add Windows EventLog or ETW audit sink.
- Add HCS / Hyper-V container backend for high-risk execution.
- Add network and IPC policy controls.

## 5. Non-goals

Phase 0/1 does not attempt to:

- Provide strong isolation against malicious native code.
- Implement Windows-HCS, Hyper-V, AppContainer, WFP, ETW, or WDF.
- Replace the existing production merge gate.
- Allow sandbox artifacts to bypass human or CLI confirmation in production mode.
- Claim multi-tenant security.

## 6. Policy Principles

- Default deny for writes outside allowed project roots.
- Production mode must not execute local commands.
- The model can request a tool call, but deterministic policy decides whether it runs.
- Sandbox artifacts must be auditable before they merge into the project.
- A stronger backend should be a runtime choice, not a rewrite of OpenSpec phases.

## 7. Minimal Acceptance

Phase 0/1 is considered complete when:

- Threat model and backend design docs exist.
- `SandboxPolicy`, `SandboxRequest`, `SandboxResult`, and manifest v2 schema exist.
- manifest v2 can be written, read, and schema-validated by tests.
- `PolicySandboxBackend` wraps the existing `SandboxSession`.
- Existing strict and production sandbox behavior stays compatible.
