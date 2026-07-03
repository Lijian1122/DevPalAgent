# Windows 进程级沙箱后端设计说明（最新版）

> 更新时间：2026-07-03
> 适用范围：DevPalAgent Phase 10 编译、测试、运行命令的受控执行。
> 当前状态：已落地 `windows_process` 后端 MVP。它是进程级执行沙箱，不是 HCS、Hyper-V、AppContainer 或 VM 级强隔离边界。

## 1. 为什么要加这个沙箱

DevPalAgent 原本已经有一层 policy sandbox，用于约束 multi-agent 写文件、路径、命令、manifest 和 production merge gate。那一层对 Agent 生成代码很有价值，但 Phase 10 与 Phase 4 不一样：Phase 10 会真正执行生成后的代码、CMake、测试二进制和 pytest。

因此新增 `windows_process` 后端的目标不是“一步到位做强隔离”，而是先把执行链路从普通 `subprocess.run` 升级为可审计、可替换、可继续下沉到 Windows 原生隔离能力的后端协议。

新增沙箱的核心原因：

1. **把 policy 和 execution 拆开**
   - policy layer 负责判断“能不能做”：命令白名单、cwd 限制、production 禁止执行、路径规范化。
   - backend layer 负责决定“在哪里执行”：当前支持 `policy` 和 `windows_process`，后续可以接 HCS / Hyper-V / Remote Worker。

2. **让 Phase 10 命令可追踪**
   - 每个命令都有 `sandbox_id`、`runner_request.json`、`runner_result.json`、`manifest.v2.json`。
   - EventBus 会记录 sandbox created / policy applied / command started / command completed / timeout / cleanup。
   - Phase 11 final report 会汇总 sandbox backend、隔离等级、manifest、runner result、timeout 和 cleanup。

3. **控制进程生命周期**
   - 生成代码可能卡死、超时、产生子进程。
   - C# runner 使用 Windows Job Object，配合 `Kill(entireProcessTree: true)`，在 timeout 或 runner 退出时尽量清理进程树。

4. **为 Windows 强隔离演进铺路**
   - 当前是 process-level MVP。
   - 后续可在同一套 `SandboxRequest -> runner_result -> manifest.v2` 协议后面接 restricted token、low integrity、AppContainer、WFP、ETW、HCS / Hyper-V container。

## 2. 当前沙箱的准确边界

当前 `windows_process` 后端具备：

- deterministic policy 校验。
- 不走 shell，按 argv list 执行。
- Phase 10 命令统一进入 Windows runner。
- runner request/result 持久化。
- manifest v2 审计。
- EventBus 沙箱事件。
- final report 沙箱摘要。
- timeout。
- Windows Job Object 进程树清理。

当前不具备：

- 不提供 HCS / Hyper-V container 隔离。
- 不提供 AppContainer 隔离。
- 不创建 restricted token。
- 不降低 integrity level。
- 不对整个项目目录做 ACL 限制。
- 不通过 WFP / Firewall 做网络隔离。
- 不隔离 IPC、COM、named pipe、registry、localhost。
- 不应被当成能抵御恶意 native code 的强安全边界。

一句话定义：

> 当前后端是“策略约束 + 进程生命周期管理 + 全链路审计”的 Windows process sandbox MVP，不是强隔离容器。它解决 Phase 10 可控执行和可观测性问题，并为后续 Windows 原生强隔离后端提供接口基础。

## 3. 实现文件地图

| 模块 | 文件 |
| --- | --- |
| CLI 参数 | `run_ai_flow.py` |
| 运行选项 | `devpal/core/openspec_executor.py` |
| 上下文字段和 checkpoint | `devpal/core/openspec_phases/base.py` |
| Scheduler 参数传递 | `devpal/core/openspec_phases/enhanced_scheduler.py` |
| Phase 10 接入点 | `devpal/core/openspec_phases/phase10_run_tests.py` |
| 沙箱数据模型 | `devpal/core/sandbox/models.py` |
| manifest v2 | `devpal/core/sandbox/manifest.py` |
| backend 抽象 | `devpal/core/sandbox/backends/base.py` |
| policy backend | `devpal/core/sandbox/backends/policy.py` |
| Windows process backend | `devpal/core/sandbox/backends/windows_process.py` |
| 旧 policy 兼容层 | `devpal/core/multi_agent/sandbox.py` |
| C# runner | `runners/windows/devpal-sandbox-runner/Program.cs` |
| C# 项目 | `runners/windows/devpal-sandbox-runner/DevPalSandboxRunner.csproj` |
| EventBus 事件模型 | `devpal/core/schema/workflow_events.py` |
| EventBus emit helper | `devpal/core/schema/eventbus_integration.py` |
| Final report 汇总 | `devpal/core/openspec_phases/phase11_final_report.py` |

## 4. 总体调用链

```text
run_ai_flow.py
  -> OpenSpecRunOptions(sandbox_backend="windows_process")
  -> EnhancedOpenSpecScheduler
  -> OpenSpecContext.sandbox_backend
  -> Phase10RunTests._run_phase10_command(...)
  -> Phase10RunTests._run_windows_process_backend_command(...)
  -> WindowsProcessSandboxBackend.create_session(...)
  -> WindowsProcessSandboxSession.validate_command(...)
  -> WindowsProcessSandboxSession.write_runner_request(...)
  -> devpal-sandbox-runner.exe runner_request.json
  -> runner_result.json
  -> manifest.v2.json
  -> EventBus sandbox events
  -> context.parallel_execution_stats["10"]
  -> Phase11 final_report.md sandbox summary
```

CLI 使用方式：

```powershell
python run_ai_flow.py -r requirements/simple_calculator.md --sandbox-backend windows_process --sandbox-level staging
```

支持的 backend：

| backend | 说明 |
| --- | --- |
| `policy` | 默认路径。使用 Python policy 校验和本地命令执行。 |
| `windows_process` | Phase 10 命令委托给 C# runner 执行，并生成 request/result/manifest/EventBus 审计。 |

## 5. 数据模型

核心模型在 `devpal/core/sandbox/models.py`。

### 5.1 `SandboxPolicy`

表示 policy layer 的约束：

```text
sandbox_level: staging / strict / production
allowed_paths: 允许写入或合并的相对路径
allowed_commands: 预留字段，当前主要由 legacy SandboxSession 执行命令 allowlist
denied_commands: 预留字段
network: allow / deny / restricted，当前是策略声明，还没有 OS 级网络拦截
timeout_seconds: 命令超时
max_processes: Job Object ActiveProcessLimit
max_memory_mb: 预留字段，当前未落地内存限制
backend: policy / windows_process
isolation_level: policy / process
metadata: 扩展信息
```

### 5.2 `SandboxRequest`

表示一次沙箱任务请求：

```text
project_dir: 项目根目录
task_id: Phase 10 命令任务 id
phase_number: 10
role: test
policy: SandboxPolicy
execution_id: 可选执行 id
trace_id: workflow id
metadata: workflow_id、event_log 等
```

### 5.3 `CommandSpec`

来自 multi-agent 层的命令结构：

```text
argv: 命令数组，不接受 shell string
cwd: 工作目录
timeout_seconds: 超时
env: 环境变量
capture_output: 是否捕获输出
text / encoding / errors: 输出解码策略
```

## 6. Policy 校验逻辑

当前 command policy 复用 `devpal/core/multi_agent/sandbox.py` 的 `SandboxSession`。

### 6.1 sandbox level

| level | 行为 |
| --- | --- |
| `staging` | 可执行允许命令；写入仍走 sandbox/manifest 约束。 |
| `strict` | 需要明确 allowed_paths；命令仍必须通过 allowlist/cwd 校验。 |
| `production` | 禁止本地命令执行，只允许生成待 merge 的产物，不直接跑命令。 |

### 6.2 命令入口校验

`validate_command(command)` 会检查：

1. `sandbox_level` 必须是 `staging`、`strict`、`production`。
2. `production` 直接拒绝本地命令执行。
3. `argv` 必须是 list，不能是 shell 字符串。
4. `argv[0]` 不能为空。
5. `cwd` 必须在项目根目录内。
6. `cwd` 只能是项目根、`build/` 或 `build_test/`。
7. 可执行文件必须满足 allowlist 或位于项目内构建目录。
8. `cmake -S/-B/--build` 的路径必须在项目根或 build/build_test 下。

当前允许的常见工具：

```text
pytest
python
python.exe
cmake
```

当前拒绝的高风险入口：

```text
cmd
cmd.exe
powershell
powershell.exe
bash
sh
curl
wget
ssh
scp
rm
del
```

注意：这仍是 deterministic policy，不是 OS 级强制访问控制。真正恶意代码若已经被允许执行，仍可能通过自身能力尝试读写系统资源。因此后续需要 restricted token、AppContainer、ACL、WFP 或 Hyper-V。

## 7. Phase 10 接入逻辑

核心函数：

```text
Phase10RunTests._run_phase10_command(...)
```

决策顺序：

```text
if context.sandbox_backend == "windows_process":
    _run_windows_process_backend_command(...)
elif enable_multi_agent:
    MultiAgentCoordinator.execute_test_tasks(...)
else:
    subprocess.run(...)
```

### 7.1 Python 测试

Python 项目会执行：

```text
pytest tests -v
```

如果启用 `windows_process`：

1. 构造 `CommandSpec(argv=["pytest", "tests", "-v"], cwd=project_dir)`。
2. 构造 `SandboxRequest(phase_number=10, role="test")`。
3. 创建 Windows process session。
4. policy 校验。
5. runner 执行。
6. stdout/stderr 写入 `context.test_output`。
7. 根据 returncode 更新测试结果。

### 7.2 C++ 测试

C++ 项目会执行多类命令：

```text
cmake -G ... -S <project_dir> -B <build_dir>
cmake --build <build_dir> --config Release --target <target>
<build_test>/<test>.exe
```

如果启用 `windows_process`，这些命令都会进入 C# runner。

为了兼容现有 CMake 构建，当前命令 cwd 通常仍是项目根或 build/build_test 目录。也就是说：

- `.spec/sandboxes/<sandbox_id>/workspace` 当前主要承载沙箱会话目录和审计文件。
- Phase 10 的编译和测试不是完整 copy-in/copy-out 到 workspace 内执行。
- 因此当前实现不是文件系统强隔离，而是“项目内受控 cwd + 命令 policy + runner 审计 + 进程清理”。

这点是当前 MVP 最重要的安全边界说明。

## 8. WindowsProcessSandboxBackend 逻辑

文件：`devpal/core/sandbox/backends/windows_process.py`

### 8.1 runner 路径选择

优先级：

1. `sandbox_backend_options["runner_path"]`
2. 环境变量 `DEVPAL_SANDBOX_RUNNER`
3. 默认 release 路径：

```text
runners/windows/devpal-sandbox-runner/bin/Release/net8.0/devpal-sandbox-runner.exe
```

### 8.2 session 初始化

`WindowsProcessSandboxSession` 会：

1. 把 request policy 的 `backend` 设置为 `windows_process`。
2. 把 `isolation_level` 设置为 `process`。
3. 创建 legacy `SandboxSession` 作为 policy 兼容层。
4. 复用 legacy sandbox id / sandbox_dir / workspace_dir / manifest_path。

### 8.3 写 runner_request

`write_runner_request(command)` 顺序：

1. 调用 `validate_command(command)`。
2. 调用 `build_runner_request(command)`。
3. 创建 `.spec/sandboxes/<sandbox_id>/runner_request.json`。
4. 用 UTF-8 写入 JSON。

request 关键字段：

```json
{
  "schema_version": "devpal.sandbox.runner_request.v1",
  "sandbox_id": "phase10-test-...",
  "execution_id": "...",
  "backend": "windows_process",
  "isolation_level": "process",
  "project_dir": "...",
  "sandbox_dir": ".../.spec/sandboxes/<id>",
  "workspace_dir": ".../.spec/sandboxes/<id>/workspace",
  "result_path": ".../.spec/sandboxes/<id>/runner_result.json",
  "command": {
    "argv": ["cmake", "--build", "..."],
    "cwd": "...",
    "timeout_seconds": 120,
    "env": {
      "PATH": "...",
      "SystemRoot": "..."
    },
    "capture_output": true,
    "text": true,
    "encoding": "utf-8",
    "errors": "replace"
  },
  "policy": {},
  "trace": {},
  "metadata": {}
}
```

### 8.4 执行 runner

Python wrapper 用 `subprocess.run` 启动 runner：

```text
devpal-sandbox-runner.exe runner_request.json
```

wrapper 自身设置：

```text
capture_output=True
text=True
encoding=<command.encoding or utf-8>
errors=<command.errors or replace>
timeout=command.timeout_seconds + runner_timeout_grace_seconds
```

如果 runner 超时：

- 生成 `CommandResult(timed_out=True)`。
- 写 `manifest.v2.json(status="timeout")`。
- 让 Phase 10 发 `sandbox.timeout` 事件。

如果 runner 没有写 `runner_result.json`：

- 生成失败 `CommandResult`。
- 写 `manifest.v2.json(status="failed")`。

如果 runner 正常写 result：

- 读取 `runner_result.json`。
- 转成 `CommandResult`。
- 根据 returncode/timed_out/error 写 manifest v2 状态。

## 9. C# runner 逻辑

文件：`runners/windows/devpal-sandbox-runner/Program.cs`

### 9.1 入口

```text
devpal-sandbox-runner <sandbox_request.json>
```

主流程：

1. 校验参数数量。
2. 读取 request JSON。
3. 反序列化为 `RunnerRequest`。
4. 校验 `command.argv` 非空。
5. 创建 workspace 目录。
6. 创建 result_path 父目录。
7. 调用 `RunCommandAsync(request)`。
8. 写 `runner_result.json`。
9. 成功返回 0，失败返回 1。

### 9.2 ProcessStartInfo

runner 构造：

```text
FileName = argv[0]
ArgumentList = argv[1:]
WorkingDirectory = command.cwd or request.workspace_dir
UseShellExecute = false
RedirectStandardOutput = command.capture_output
RedirectStandardError = command.capture_output
CreateNoWindow = true
```

重要点：

- 不通过 `cmd.exe`。
- 不通过 PowerShell。
- 不拼接 shell 字符串。
- 参数逐个进入 `ArgumentList`，减少 shell quoting 风险。
- runner 会先清空 `ProcessStartInfo.Environment`，避免继承 runner 进程里的 token。
- 然后只注入 `runner_request.json` 中的 `command.env`。
- Python 侧在写 request 前会过滤环境变量名中包含 `API`、`AUTH`、`CLAUDE`、`CODEX`、`CREDENTIAL`、`KEY`、`OPENAI`、`PASSWORD`、`SECRET`、`TOKEN` 的项。
- 如果 `CommandSpec.env is None`，request 会使用过滤后的当前环境，保留 `PATH`、`SystemRoot` 等工具链所需变量；如果显式传入空 dict，则子进程环境为空。

### 9.3 Job Object

runner 会尝试创建 Job Object：

```text
Name = DevPalSandbox-<sandbox_id>
LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
Optional: JOB_OBJECT_LIMIT_ACTIVE_PROCESS
```

作用：

- runner 进程关闭 Job Object handle 时，Windows 尝试清理 job 内进程。
- 如果设置了 `policy.max_processes`，会设置 ActiveProcessLimit。
- timeout 时先 `process.Kill(entireProcessTree: true)`，Job Object 是第二道清理保障。

边界：

- 当前没有设置内存限制。
- 当前没有设置 CPU 限制。
- 当前没有创建 restricted token。
- 如果进程无法加入 job，当前实现没有强制失败，只是 best-effort。

### 9.4 Timeout

timeout 逻辑：

1. 启动进程。
2. 分配到 Job Object。
3. 启动 stdout/stderr 异步读取。
4. `WaitForExit(timeoutMs)`。
5. 未退出则：
   - `Kill(entireProcessTree: true)`
   - 返回 `status="timeout"`
   - `exit_code=-1`
   - `timed_out=true`
   - `cleanup_status="killed"`

### 9.5 runner_result

成功示例：

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

异常时仍返回结构化结果：

```text
status = failed
success = false
exit_code = -1
cleanup_status = best_effort
error = <exception message>
```

## 10. manifest v2

文件：`devpal/core/sandbox/manifest.py`

schema version：

```text
devpal.sandbox.manifest.v2
```

关键字段：

| 字段 | 说明 |
| --- | --- |
| `sandbox_id` | 由 phase、role、task_id hash 生成 |
| `execution_id` | 每次执行 id |
| `workflow_id` | OpenSpec workflow id |
| `task_id` | Phase 10 command task |
| `phase_number` | 10 |
| `role` | test |
| `backend` | windows_process |
| `isolation_level` | process |
| `status` | created / completed / failed / timeout |
| `policy` | SandboxPolicy 快照 |
| `workspace` | project_dir / sandbox_dir / workspace_dir / manifest_path |
| `artifacts` | 当前主要为空或后续 copy-out 产物 |
| `violations` | policy violation 列表 |
| `trace` | trace_id / event_log |
| `metadata` | runner_request_path / runner_result_path / command_result / runner_result |

## 11. EventBus 事件

Phase 10 当前会发：

| 事件 | 触发时机 |
| --- | --- |
| `sandbox.created` | backend session 创建完成 |
| `sandbox.policy_applied` | deterministic policy 校验通过 |
| `sandbox.command_started` | runner 开始执行 |
| `sandbox.command_completed` | runner 完成或失败 |
| `sandbox.timeout` | 命令超时 |
| `sandbox.cleanup_completed` | cleanup 状态可知 |
| `sandbox.violation` | policy 拒绝命令 |

trace 关系：

```text
workflow_id
  -> phase_number=10
  -> task_id
  -> sandbox_id
  -> runner_request.json
  -> runner_result.json
  -> manifest.v2.json
  -> final_report.md
```

## 12. Final Report 展示

Phase 11 会读取 `context.parallel_execution_stats`，生成：

```text
### Multi-Agent Sandbox Summary

- Enabled
- Sandbox level
- Agent backend
- Sandbox backend
- Agent pool size
- Sandboxed tasks
- Policy violations

| Phase | Task | Backend | Isolation | Sandbox | Success | Duration ms | Violations | Timeout | Cleanup | Manifest | Manifest v2 | Runner Result |
```

即使没有启用 multi-agent，只要 `sandbox_backend != "policy"` 或存在 sandbox rows，也会输出该节。

## 13. 当前实现审查结论

### 13.1 已经做对的点

- CLI 可选择 `--sandbox-backend windows_process`。
- `OpenSpecRunOptions`、scheduler、context、checkpoint 都能保存 backend 配置。
- Phase 10 所有命令统一走 `_run_phase10_command`。
- `windows_process` 进入前会先跑 deterministic policy。
- production sandbox 不允许本地执行。
- runner request/result/manifest v2 都落盘。
- EventBus 与 final report 已接入。
- C# runner 不走 shell，使用 argv。
- C# runner 有 timeout 和 Job Object cleanup。
- C# runner 清空父进程环境，只注入 request 里过滤后的 env。
- C# runner 已校验 `sandbox_dir`、`workspace_dir`、`result_path` 和 `command.cwd` 基本边界。
- 缺 runner 时 fail closed，不静默回退到普通 subprocess。

### 13.2 需要明确的限制

1. **workspace 不是完整执行根**
   - 当前 C++/Python Phase 10 命令 cwd 仍在项目根或 build/build_test 目录。
   - `.spec/sandboxes/<id>/workspace` 当前主要是沙箱会话目录，不是 copy-in 后的隔离工作树。

2. **没有 OS 级文件系统隔离**
   - policy 能限制 cwd 和命令入口。
   - 但被允许执行的进程仍以当前用户权限运行。

3. **网络策略只是声明**
   - `policy.network="deny"` 当前没有落到 WFP/firewall。
   - 命令黑名单不能代替网络隔离。

4. **Job Object 只管生命周期**
   - Job Object 不是安全边界。
   - 它主要用于进程树和 timeout 清理。

5. **runner 环境变量已经做敏感项过滤，但还不是严格 allowlist**
   - 当前会过滤常见 token/key/password 类变量，并阻断 C# runner 默认环境继承。
   - 后续更理想的是按 backend / language / compiler profile 做显式 env allowlist。

6. **C# runner 仍需完整 schema validation**
   - 已做基本 defensive validation。
   - 后续仍应补 JSON schema、字段类型、路径存在性、允许字段集合和更清晰的错误码。

### 13.3 建议优先修复

短期：

1. 给 `windows_process` backend 增加真实 runner smoke test。
2. 为 runner request/result 增加 JSON schema 校验。
3. 把 env 过滤从 denylist 升级为按语言/工具链 profile 的 allowlist。
4. Python wrapper 在 manifest v2 中记录 runner executable path 和 runner returncode。
5. 对 Job Object assign 失败增加更醒目的 warning / policy 处理。

中期：

1. env allowlist。
2. workspace copy-in / copy-out 模式。
3. sandbox workspace ACL hardening。
4. restricted token / low integrity。
5. Windows EventLog / ETW。

长期：

1. AppContainer backend。
2. WFP / Firewall network deny。
3. HCS / Hyper-V backend。
4. Sandbox resource pool 和 warm pool。

## 14. HCS / Hyper-V 后续路线

HCS / Hyper-V backend 不建议直接替换当前 process backend，而应作为高风险任务 backend：

```text
SandboxBackend
  -> PolicySandboxBackend
  -> WindowsProcessSandboxBackend
  -> WindowsContainerSandboxBackend
  -> RemoteWorkerSandboxBackend
```

HCS / Hyper-V backend 目标：

- 创建 Hyper-V isolated Windows container。
- copy-in 或挂载 sandbox workspace。
- 容器内执行同一套 argv command。
- 限制网络 egress。
- 收集 stdout/stderr/result/artifacts。
- 写同一套 `runner_result.json` 和 `manifest.v2.json`。
- 销毁 container 和临时层。

难点：

- Windows image 体积大。
- 冷启动慢。
- 文件挂载和 copy-on-write 成本。
- 容器网络策略复杂。
- 多并发 sandbox 需要资源池。
- CI 环境可能不支持 Hyper-V。

推荐策略：

| 风险等级 | backend |
| --- | --- |
| low | policy |
| medium | windows_process |
| high | HCS / Hyper-V |
| critical | remote isolated VM / worker |

## 15. 验收测试建议

单元测试：

```powershell
python -m pytest -p no:cacheprovider --basetemp .tmp\pytest_sandbox `
  tests/openspec/test_sandbox_manifest_v2.py `
  tests/openspec/test_sandbox_policy_backend.py `
  tests/openspec/test_sandbox_windows_process_backend.py `
  tests/openspec/test_phase10_run_tests.py `
  tests/openspec/test_phase11_final_report.py `
  tests/test_eventbus_integration.py
```

完整流程：

```powershell
python run_ai_flow.py `
  -r requirements/simple_calculator.md `
  --sandbox-backend windows_process `
  --sandbox-level staging `
  --no-abort `
  --verbose `
  --resume
```

期望：

- Phase 3-11 完成。
- Phase 10 使用 `windows_process`。
- `.spec/sandboxes/*/runner_request.json` 存在。
- `.spec/sandboxes/*/runner_result.json` 存在。
- `.spec/sandboxes/*/manifest.v2.json` 存在。
- EventBus 中存在 sandbox created/policy_applied/command_started/command_completed/cleanup_completed。
- final report 包含 `Multi-Agent Sandbox Summary`、`Sandbox execution enabled` 和 `windows_process` backend。

## 16. 面试表达版本

可以这样讲：

> 我在 DevPalAgent 里把 Agent 执行安全拆成 policy layer 和 backend layer。policy layer 做 deterministic 校验，包括命令入口、cwd、路径、production 禁止本地执行；backend layer 决定执行方式。当前已经实现 Windows process backend：Phase 10 命令会被转换成 runner_request.json，交给 C# runner 执行。runner 不走 shell，使用 argv、timeout、stdout/stderr 捕获和 Windows Job Object 清理进程树，执行结果回写 runner_result.json，并生成 manifest v2、EventBus 事件和 final report 摘要。
> 我也明确这个 MVP 不是强隔离，它还没有 restricted token、AppContainer、WFP 或 Hyper-V。它的价值是把 Phase 10 执行链路协议化、可审计化、可替换化，后续可以把 backend 下沉到 HCS / Hyper-V 或 remote isolated worker，而不需要重写 OpenSpec、EventBus、manifest 和 final report。

## 17. 当前测试记录

本节用于记录最近一次验证结果。每次修改沙箱逻辑后应更新。

```text
验证日期：2026-07-03

环境：
- Windows 本机。
- Python 测试使用仓库当前虚拟/系统环境。
- C# runner 使用本地 .NET 8 runtime/SDK：.tmp\dotnet8。
- DOTNET_ROOT 指向 C:\code\DevPalAgent\.tmp\dotnet8。
- DOTNET_CLI_HOME 指向 C:\code\DevPalAgent\.tmp\dotnet_home，避免写入用户目录失败。

C# runner：
- 命令：dotnet build runners\windows\devpal-sandbox-runner\DevPalSandboxRunner.csproj -c Release --no-restore
- 结果：Build succeeded，0 warning，0 error。

单元/集成测试：
- 命令：python -m pytest -q -p no:cacheprovider --basetemp .tmp\pytest_sandbox_full ...
- 覆盖：manifest v2、policy backend、windows_process backend、Phase 10、failure policy、compile error summary、Phase 11 final report、EventBus、OpenSpec executor。
- 结果：47 passed，2 warnings。
- 追加回归：Phase 10 在 cmake build 失败时，即使旧 exe 仍存在，也会返回失败，避免 stale executable 掩盖真实构建失败。
- 追加回归：`CommandSpec.env is None` 时，runner request 使用过滤后的当前环境，不写入 key/token/password 类变量。
- 追加回归：MSVC 编译器探测能处理 Windows 环境里同时存在 `Path` 和 `PATH` 的情况，优先选择包含 `cl.exe` 的 PATH。
- 追加回归：MSVC CMake configure 使用 `NMake Makefiles`，避免硬编码 `Visual Studio 16 2019` 与 VS 18/2026 环境不匹配。

完整流程：
- 2026-07-03 08:33 的完整流程成功：OpenSpec 11-phase pipeline complete，Phase 10 成功，14/14 passed，self-heal attempts=0，Sandboxed tasks=7，Policy violations=0。
- 2026-07-03 08:45 在环境继承修复后再次执行完整流程，失败于 Phase 4 AI code generation：Anthropic APIConnectionError / network connection failed。该失败发生在进入 Phase 10 沙箱前，不属于 sandbox backend 失败。
- 2026-07-03 21:14 在放开网络限制后重新执行完整流程成功：OpenSpec 11-phase pipeline complete，Phase 10 成功，12/12 passed，self-heal attempts=0，Sandboxed tasks=5，Policy violations=0。
- 最新完整流程日志：cpp_simple_calculator\cpp_simple_calculator_20260703_211439.log。
- 最新 final report：cpp_simple_calculator\docs\final_report.md，包含 `Sandbox execution enabled: True`、`Sandbox backend: windows_process`。
- 为验证最新沙箱代码，已绕开网络依赖直接执行 Phase 10：`OpenSpecContext(language="cpp", sandbox_backend="windows_process") -> Phase10RunTests.execute()`。
- 直接 Phase 10 结果：成功，14/14 passed，Sandboxed tasks=7。
- 直接 Phase 10 runner_result：7/7 success=true，exit_code=0，timed_out=false，job_assigned=true。
- Phase 10 CMake configure：使用 `NMake Makefiles`，request env 中包含 MSVC `PATH/INCLUDE/LIB/VCToolsInstallDir` 等必要变量。

敏感信息检查：
- 范围：cpp_simple_calculator\.spec\sandboxes 下的 runner_request.json、runner_result.json、manifest.v2.json。
- 检查项：ANTHROPIC_AUTH_TOKEN、OPENAI_API_KEY、ANTHROPIC_API_KEY、PASSWORD、SECRET、TOKEN、sk-。
- 结果：未发现敏感环境变量名或 sk- token。

已确认的问题与修复：
- 修复 runner_request.json 写入完整环境变量导致 token 泄露的风险，现在只写入过滤后的 env。
- 修复 C# runner 默认继承父进程环境的问题，现在先清空环境，再注入 request 中过滤后的 env。
- 修复 C# runner 对 sandbox_dir/workspace_dir/result_path/cwd 缺少边界校验的问题。
- 修复 Phase 10 build 失败但旧 exe 存在时可能误判成功的问题。
- 修复 Windows 子进程输出解码在中文/MSVC 输出下可能异常的问题。
- 修复 MSVC compiler detector 中 `Path/PATH` 覆盖导致 `cl.exe` 探测失败的问题。
- 修复 Phase 10 MSVC CMake generator 硬编码 VS2019，改为版本中性的 `NMake Makefiles`。
- 收紧 C++ 测试生成 prompt，避免生成 test_base.h 不支持的 ASSERT_THROW、ASSERT_NE、GoogleTest/Catch2 宏。
```
