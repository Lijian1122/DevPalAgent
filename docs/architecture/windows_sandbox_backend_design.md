# Windows 进程级沙箱后端设计说明（最新版）

> 更新时间：2026-07-06
> 适用范围：DevPalAgent Phase 10 编译、测试、运行命令的受控执行。
> 当前状态：已落地 `windows_process` 后端 MVP，并补上 `SandboxManager`、low integrity 启动、restricted token 降权、实际执行目录 ACL hardening 钩子、Windows Firewall network deny PoC、Job Object 内存上限和 copy-out hash gate。同时新增 `windows_container` 后端接口骨架（HCS / Hyper-V 强隔离目标），当前为 fail-closed skeleton，详见 `docs/architecture/windows_container_backend_design.md`。它仍不是 HCS、Hyper-V、AppContainer 或 VM 级强隔离边界。

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
- `SandboxManager` 统一负责 backend 选择、EventBus audit、runner result 汇总和 reaper 入口。
- 可选 low integrity token 进程启动。
- 可选 workspace low integrity label hardening。
- 可选 Windows Firewall 出站阻断 PoC。

当前不具备：

- 不提供 HCS / Hyper-V container 隔离。
- 不提供 AppContainer 隔离。
- 不创建完整 restricted token；当前实现是 low integrity primary token。
- low integrity / ACL / network deny 默认关闭，需要显式启用。
- workspace ACL hardening 依赖当前 Windows 权限；权限不足时 fail closed。
- network deny 是 Windows Firewall 规则 PoC，不是完整 WFP callout driver。
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
| 沙箱执行协调 | `devpal/core/sandbox/manager.py` |
| manifest v2 | `devpal/core/sandbox/manifest.py` |
| backend 抽象 | `devpal/core/sandbox/backends/base.py` |
| policy backend | `devpal/core/sandbox/backends/policy.py` |
| Windows process backend | `devpal/core/sandbox/backends/windows_process.py` |
| runner schema 校验 | `devpal/core/sandbox/runner_schema.py` |
| runner JSON Schema 资产 | `devpal/core/sandbox/schemas/runner_request.schema.json`、`devpal/core/sandbox/schemas/runner_result.schema.json` |
| 环境变量 profile | `devpal/core/sandbox/env_profiles.py` |
| workspace copy-in/copy-out | `devpal/core/sandbox/workspace.py` |
| stale sandbox 清理 | `devpal/core/sandbox/reaper.py` |
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
  -> SandboxManager.execute_command(...)
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
python run_ai_flow.py -r requirements/simple_calculator.md --sandbox-backend windows_process --phase10-workspace-execution
python run_ai_flow.py -r requirements/simple_calculator.md --sandbox-backend windows_process --sandbox-low-integrity --sandbox-harden-workspace-acl
python run_ai_flow.py -r requirements/simple_calculator.md --sandbox-backend windows_process --sandbox-network-deny
```

也可以在 `config/config.yaml` 中配置默认值。CLI 参数优先于配置文件：

```yaml
sandbox:
  backend: "windows_process"
  level: "staging"
  phase10_workspace_execution: true
  low_integrity: false
  harden_workspace_acl: false
  network_deny: false
  backend_options: {}
```

支持的 backend：

| backend | 说明 |
| --- | --- |
| `policy` | 默认路径。使用 Python policy 校验和本地命令执行。 |
| `windows_process` | Phase 10 命令委托给 C# runner 执行，并生成 request/result/manifest/EventBus 审计。 |
| `windows_container` | HCS / Hyper-V 强隔离后端接口骨架。复用同一套 `SandboxRequest -> runner_request.json -> runner_result.json -> manifest.v2` 协议，但当前 `execute_command` fail-closed，返回 `CONTAINER_BACKEND_NOT_IMPLEMENTED`，不做静默降级。详见第 15 节与 `windows_container_backend_design.md`。 |

## 5. 数据模型

核心模型在 `devpal/core/sandbox/models.py`。

### 5.1 `SandboxPolicy`

表示 policy layer 的约束：

```text
sandbox_level: staging / strict / production
allowed_paths: 允许写入或合并的相对路径
allowed_commands: 预留字段，当前主要由 legacy SandboxSession 执行命令 allowlist
denied_commands: 预留字段
network: allow / deny / restricted，默认是策略声明；开启 network_deny 时由 runner 尝试 Windows Firewall PoC
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

### 5.4 `isolation` runner 协议

`WindowsProcessSandboxBackend` 会把 `sandbox_backend_options` 中的强隔离开关写入 `runner_request.json`：

```json
{
  "isolation": {
    "low_integrity": true,
    "harden_workspace_acl": true,
    "network_deny": false
  }
}
```

C# runner 会在 `runner_result.json` 中回写审计结果：

```json
{
  "isolation": {
    "low_integrity_requested": true,
    "low_integrity_applied": true,
    "workspace_acl_requested": true,
    "workspace_acl_hardened": false,
    "workspace_acl_error": "Access is denied.",
    "network_deny_requested": false,
    "network_deny_applied": false,
    "process_launcher": "low_integrity"
  }
}
```

语义：

- `low_integrity`：runner 使用 Win32 token API 创建 low integrity primary token，并用该 token 启动子进程。
- `harden_workspace_acl`：需配合 `phase10_workspace_execution`；runner 调用 `icacls.exe /setintegritylevel (OI)(CI)L` 给 copy-in 实际执行目录设置低完整性标签，使 low integrity 子进程可以写 copy-in workspace，但不能向上写普通 medium integrity 项目目录。
- `network_deny`：runner 尝试创建临时 Windows Firewall 出站阻断规则，规则名为 `DevPalSandbox-<sandbox_id>`，命令结束后删除。
- 这些能力默认关闭；开启后若准备失败，会返回 `ISOLATION_SETUP_FAILED` 或 `NETWORK_DENY_FAILED`，不会静默降级成普通进程。

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

如果同时开启 `phase10_workspace_execution`：

1. 将 `pyproject.toml`、`pytest.ini`、`setup.cfg`、`setup.py`、`requirements.txt`、`src/`、`tests/` 中存在的资产 copy-in 到 `.spec/sandboxes/phase10-workspace-execution/workspace`。
2. `pytest tests -v` 的 cwd 改为 workspace。
3. `PYTHONPATH` 的第一项改为 workspace 内的 `src/`。
4. runner request 的 `project_dir` 和 `command.cwd` 均指向 workspace。

### 7.2 C++ 测试

C++ 项目会执行多类命令：

```text
cmake -G ... -S <project_dir> -B <build_dir>
cmake --build <build_dir> --config Release --target <target>
<build_test>/<test>.exe
```

如果启用 `windows_process`，这些命令都会进入 C# runner。

默认情况下，为了兼容现有 CMake 构建，命令 cwd 通常仍是项目根或 build/build_test 目录。也就是说：

- `.spec/sandboxes/<sandbox_id>/workspace` 当前主要承载沙箱会话目录和审计文件。
- Phase 10 的编译和测试不是完整 copy-in/copy-out 到 workspace 内执行。
- 因此当前实现不是文件系统强隔离，而是“项目内受控 cwd + 命令 policy + runner 审计 + 进程清理”。

如果开启 `phase10_workspace_execution`，C++ Phase 10 会进入 copy-in workspace 模式：

1. 将 `CMakeLists.txt`、`include/`、`src/`、`tests/` 复制到：
   `project/.spec/sandboxes/phase10-workspace-execution/workspace`。
2. 将 `context.sandbox_backend_options["execution_project_dir"]` 指向该 workspace。
3. CMake configure/build/test 的 `project_dir`、`tests_dir`、`cwd` 都映射到 workspace。
4. 原项目根目录仍作为 trace metadata 保留到 runner request / manifest。
5. 当前只做 copy-in 和构建产物收集能力铺垫，不自动把 build/build_test 写回项目根。

这仍然不是 OS 级强隔离，但已经避免 Phase 10 编译测试直接污染项目根目录，是后续 ACL hardening、copy-out 审批、HCS/Hyper-V backend 的更合适入口。

## 8. SandboxManager 逻辑

文件：`devpal/core/sandbox/manager.py`

`SandboxManager` 是 P0 抽象层，目标是把 Phase 10 从 backend 细节里解耦出来。现在 Phase 10 只负责：

1. 构造 `CommandSpec`。
2. 调用 `SandboxManager.execute_command(...)`。
3. 把 manager 返回的 summary 合并到 `context.parallel_execution_stats["10"]`。

Manager 负责：

- 根据 `context.sandbox_backend` 选择 backend。
- 构造 `SandboxRequest`。
- 将 `sandbox_backend_options` 里的 `low_integrity`、`harden_workspace_acl`、`network_deny`、`restricted_token` 转成 runner isolation 协议。
- 创建 backend session。
- 执行 deterministic policy 校验。
- 发 EventBus sandbox created / policy_applied / command_started / command_completed / timeout / cleanup / violation。
- 读取 runner result。
- 生成 Phase 10 需要的 parallel summary。
- 暴露 `reap_stale(...)`，统一接入 `SandboxReaper`；reaper 支持按 status、workflow_id、task_id 过滤 stale sandbox。

### 8.1 backend 分发

Manager 不再硬编码单一 backend，而是用一个 backend allowlist 和一个工厂方法做分发：

```python
SANDBOX_MANAGER_BACKENDS = ("windows_process", "windows_container")

def execute_command(self, *, task_id, command, role="test"):
    backend_name = getattr(self.context, "sandbox_backend", "policy")
    if backend_name not in SANDBOX_MANAGER_BACKENDS:
        raise ValueError(f"unsupported sandbox backend for manager: {backend_name}")
    return self._execute_backend(backend_name=backend_name, ...)

def _create_backend(backend_name, options):
    if backend_name == "windows_container":
        return WindowsContainerSandboxBackend(
            container_options=dict(options.get("container_options", {}) or {}),
        )
    return WindowsProcessSandboxBackend(
        runner_path=options.get("runner_path"),
        runner_args=list(options.get("runner_args", []) or []),
        runner_timeout_grace_seconds=int(options.get("runner_timeout_grace_seconds", 5) or 5),
    )
```

关键点：

- `policy` backend 不走 manager；它由 legacy `SandboxSession` 路径处理，manager 只接管 `windows_process` 和 `windows_container` 这类需要 request/result/audit 全链路的 backend。
- 所有走 manager 的 backend 共享同一套 `SandboxRequest` 构造、policy 注入、EventBus 事件、summary 生成和 ACL fail-closed 校验逻辑。因此新增一个走 manager 的 backend，只需在 allowlist 里加名字，并在 `_create_backend` 里加一个分支，不需要改事件、manifest、summary 或 final report。

这样后续如果加入 AppContainer、HCS、remote worker 或更复杂 fallback 策略，Phase 10 不需要继续知道每个 backend 的 request/result/audit 细节。Phase 10 侧的 backend 判定也从 `_is_windows_process_backend_enabled()` 泛化为 `_is_manager_backend_enabled()`，命令统一经 `SandboxManager.execute_command` 分发。

## 9. WindowsProcessSandboxBackend 逻辑

文件：`devpal/core/sandbox/backends/windows_process.py`

### 9.1 runner 路径选择

优先级：

1. `sandbox_backend_options["runner_path"]`
2. 环境变量 `DEVPAL_SANDBOX_RUNNER`
3. 默认 release 路径：

```text
runners/windows/devpal-sandbox-runner/bin/Release/net8.0/devpal-sandbox-runner.exe
```

### 9.2 session 初始化

`WindowsProcessSandboxSession` 会：

1. 把 request policy 的 `backend` 设置为 `windows_process`。
2. 把 `isolation_level` 设置为 `process`。
3. 创建 legacy `SandboxSession` 作为 policy 兼容层。
4. 复用 legacy sandbox id / sandbox_dir / workspace_dir / manifest_path。

### 9.3 写 runner_request

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

### 9.4 执行 runner

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

## 10. C# runner 逻辑

文件：`runners/windows/devpal-sandbox-runner/Program.cs`

### 10.1 入口

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

### 10.2 ProcessStartInfo

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
- Python 侧在写 request 前会按命令推断环境 profile：`cpp-msvc`、`python-pytest`、`generic-build`、`generic-minimal`。
- 每个 profile 都是 allowlist，额外会拒绝环境变量名中包含 `API`、`AUTH`、`CLAUDE`、`CODEX`、`CREDENTIAL`、`KEY`、`OPENAI`、`PASSWORD`、`SECRET`、`TOKEN` 的项。
- `cpp-msvc` 会保留 `PATH`、`SystemRoot`、`INCLUDE`、`LIB`、`VCToolsInstallDir`、`WindowsSdkDir` 等 MSVC/CMake 构建所需变量。
- `python-pytest` 会保留 `PATH`、`SystemRoot`、`PYTHONPATH`、`VIRTUAL_ENV` 等 Python 测试所需变量，不会把 MSVC `INCLUDE/LIB` 混入 pytest request。
- 如果 `CommandSpec.env is None`，request 会从当前进程环境按 profile 过滤；如果显式传入空 dict，则子进程环境为空。

### 10.3 Job Object

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
- 如果 Job Object 创建失败（例如非 Windows 平台），runner 会继续以 process backend 的普通进程模式运行。
- 如果 Job Object 已创建但进程无法加入 job，runner 会立刻 kill 进程树并返回 `JOB_ASSIGN_FAILED`，避免命令在失去生命周期控制时继续运行。

### 10.4 low integrity / ACL / network deny

当 `runner_request.json` 中 `isolation.low_integrity=true` 时，runner 会：

1. `OpenProcessToken(GetCurrentProcess())`。
2. `DuplicateTokenEx(...)` 复制 primary token。
3. `ConvertStringSidToSid("S-1-16-4096")` 获取 Low Mandatory Level SID。
4. `SetTokenInformation(TokenIntegrityLevel, ...)` 将 token 降为 low integrity。
5. `CreateProcessAsUser(...)` 启动子进程。
6. 继续把子进程加入 Job Object。

当 `isolation.harden_workspace_acl=true` 时，runner 会：

```text
icacls.exe <acl_target> /setintegritylevel (OI)(CI)L
```

`acl_target` 优先取 `command.cwd`，缺省时取 `workspace_dir`，并且必须位于 `project_dir` 内。这样 Phase 10 copy-in workspace 模式下，低完整性进程可以写真实构建/测试目录，而不是只给审计目录打标签。runner 会在 `runner_result.isolation.workspace_acl_path` 中记录实际打标签路径。当前 Codex 执行环境对该操作返回 Access denied，因此实现会结构化返回 `ISOLATION_SETUP_FAILED`。

产品层还有一道保护：`SandboxManager` 要求 `harden_workspace_acl` 的 `execution_project_dir` 必须位于原项目 `.spec/sandboxes` 下。也就是说，Phase 10 未开启 workspace execution 时不会给真实项目根目录打低完整性标签，而是 fail closed。

当 `isolation.network_deny=true` 时，runner 会：

```text
netsh.exe advfirewall firewall add rule name=DevPalSandbox-<sandbox_id> dir=out action=block program=<resolved executable> enable=yes profile=any
```

命令结束后删除同名规则。这是 Firewall PoC，用来证明网络阻断不依赖命令黑名单。创建规则通常需要管理员权限；权限不足时返回 `NETWORK_DENY_FAILED`。

### 10.5 Timeout

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

### 10.6 runner_result

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
  "isolation": {
    "low_integrity_requested": true,
    "low_integrity_applied": true,
    "workspace_acl_requested": false,
    "workspace_acl_hardened": false,
    "network_deny_requested": false,
    "network_deny_applied": false,
    "process_launcher": "low_integrity"
  },
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
error_code = PROCESS_START_FAILED / TIMEOUT / JOB_ASSIGN_FAILED / ISOLATION_SETUP_FAILED / NETWORK_DENY_FAILED
```

### 10.7 runner schema 与错误码

Python wrapper 在写入 `runner_request.json` 前会调用 `validate_runner_request()`，校验：

- `schema_version` 必须是 `devpal.sandbox.runner_request.v1`。
- `command.argv` 必须是非空字符串数组。
- `command.timeout_seconds` 必须是正整数。
- `command.env` 必须是字符串键值对象。
- `workspace_dir` 和 `result_path` 必须在 `sandbox_dir` 内。

仓库同时提供两份 JSON Schema 资产，作为跨语言协议定义的来源：

- `devpal/core/sandbox/schemas/runner_request.schema.json`
- `devpal/core/sandbox/schemas/runner_result.schema.json`

当前运行时仍使用轻量 Python 校验函数，避免引入额外依赖；后续可以把这两份 schema 接入正式 JSON Schema validator，或生成 Python/C# 类型。

C# runner 启动后会再次校验 request schema version、sandbox id、路径边界、command argv、timeout 和 env key。

Python wrapper 读取 `runner_result.json` 后会调用 `validate_runner_result()`，校验：

- `schema_version` 必须是 `devpal.sandbox.runner_result.v1`。
- `sandbox_id`、`execution_id`、`status`、`success`、`argv`、`cwd`、`exit_code`、`stdout`、`stderr`、`duration_ms`、`timed_out`、`cleanup_status` 必须存在且类型正确。
- 如果 result 不合法，会写入 `manifest.v2.json(status="failed", error_code="INVALID_RUNNER_RESULT")`。

当前 wrapper 会写入这些 Python 侧错误码：

| error_code | 含义 |
| --- | --- |
| `INVALID_RUNNER_REQUEST` | request 未通过 schema 或 runner 因 request 校验失败退出。 |
| `INVALID_RUNNER_RESULT` | runner 写出了 result，但字段不满足协议。 |
| `NO_RESULT_WRITTEN` | runner 进程退出但没有写 result 文件。 |
| `RUNNER_TIMEOUT` | Python wrapper 等待 runner 超时。 |

## 11. manifest v2

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
| `metadata` | runner_executable_path / runner_args / runner_invocation / runner_request_path / runner_result_path / command_result / runner_result |

## 12. EventBus 事件

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

## 13. Final Report 展示

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

## 14. 当前实现审查结论

### 14.1 已经做对的点

- CLI 可选择 `--sandbox-backend windows_process`。
- `OpenSpecRunOptions`、scheduler、context、checkpoint 都能保存 backend 配置。
- `OpenSpecRunOptions.phase10_workspace_execution`、CLI 和 `config.sandbox` 都能开启 C++/Python workspace 执行模式。
- `OpenSpecRunOptions`、CLI 和 `config.sandbox` 都能显式开启 `low_integrity`、`harden_workspace_acl`、`network_deny`。
- Phase 10 的 Windows backend 细节已下沉到 `SandboxManager`，Phase 10 不再直接组装 runner audit。
- Phase 10 所有命令统一走 `_run_phase10_command`。
- `windows_process` 进入前会先跑 deterministic policy。
- production sandbox 不允许本地执行。
- runner request/result/manifest v2 都落盘。
- runner request/result 已有 Python 侧 schema 校验，C# runner 也会校验 request schema 和路径边界。
- runner request/result 已有 JSON Schema 资产，为后续跨语言生成和正式 validator 做准备。
- EventBus 与 final report 已接入。
- C# runner 不走 shell，使用 argv。
- C# runner 有 timeout 和 Job Object cleanup。
- C# runner 清空父进程环境，只注入 request 里按 profile allowlist 过滤后的 env。
- Job Object 分配失败时 fail closed，runner 会 kill 进程树并返回 `JOB_ASSIGN_FAILED`。
- C# runner 可选使用 low integrity token 启动子进程，并在 runner result 中回写 `low_integrity_applied`。
- C# runner 可选给实际执行目录设置低完整性标签；权限不足时返回 `ISOLATION_SETUP_FAILED`。
- C# runner 可选创建临时 Windows Firewall 出站阻断规则；权限不足时返回 `NETWORK_DENY_FAILED`。
- C# runner 已校验 `sandbox_dir`、`workspace_dir`、`result_path` 和 `command.cwd` 基本边界。
- 缺 runner 时 fail closed，不静默回退到普通 subprocess。
- 已有 `SandboxReaper` 可 dry-run 或 apply 清理 stale failed/timeout/running/created 沙箱目录。
- `SandboxReaper` 支持按 status、workflow_id、task_id 做精确清理。
- manifest v2 记录 runner executable path、runner args 和 runner invocation。

### 14.2 需要明确的限制

1. **workspace 执行模式仍是可选**
   - 默认模式仍兼容旧路径：C++/Python Phase 10 命令 cwd 在项目根或 build/build_test 目录。
   - 开启 `phase10_workspace_execution` 后，C++ 编译测试和 Python pytest 都会在 copy-in workspace 中运行。

2. **OS 级文件系统隔离默认不开启**
   - policy 能限制 cwd 和命令入口。
   - 默认模式下，被允许执行的进程仍以当前用户权限运行。
   - 开启 `low_integrity + harden_workspace_acl` 后，runner 会尝试以 low integrity token 启动子进程，并给实际执行目录设置低完整性可写标签。
   - 当前环境验证中，low integrity 启动成功；workspace ACL hardening 因当前执行权限限制返回 Access denied，并按 fail closed 处理。

3. **network deny 是 Firewall PoC，不是完整 WFP**
   - 开启 `network_deny` 后，runner 会尝试创建临时 Windows Firewall 出站 block rule。
   - 创建 firewall rule 通常需要管理员权限；权限不足时返回 `NETWORK_DENY_FAILED`。
   - 它证明网络隔离不再依赖命令黑名单，但还不是完整 per-token/per-container WFP 隔离。

4. **Job Object 只管生命周期**
   - Job Object 不是安全边界。
   - 它主要用于进程树和 timeout 清理。

5. **env profile 是工程 allowlist，不是系统密钥保险箱**
   - 当前已经按命令 profile 保留必要环境变量并过滤 key/token/password 类变量。
   - 仍建议在生产执行环境里从源头避免把真实云 API key 注入 runner 进程。

6. **schema validation 是轻量协议校验，不是完整 JSON Schema 引擎**
   - 当前覆盖必要字段、类型和路径边界。
   - 后续可以升级为正式 JSON Schema 文件，并让 C# runner 与 Python wrapper 使用同一份协议定义生成代码。

### 14.3 建议优先修复

短期：

1. 在管理员环境运行 `scripts/validate_windows_sandbox_elevated.py --include-network`，沉淀 low integrity + ACL + network deny 的真实机器验收记录。
2. 给 runner schema 资产增加正式 JSON Schema validator 依赖后的强校验。
3. Python wrapper 在 manifest v2 中记录更多 runner runtime 信息，例如 dotnet runtime version。
4. 给 reaper 增加保留最近 N 次成功沙箱的策略。
5. 为 final report 增加 sandbox copy-out artifact hash gate 摘要。

中期：

1. WFP per-sandbox network deny。
2. copy-out 审批与产物 hash gate。
3. restricted token（在 low integrity 基础上进一步删权限）。
4. AppContainer PoC。
5. Windows EventLog / ETW。

长期：

1. AppContainer backend。
2. WFP / Firewall network deny。
3. HCS / Hyper-V backend。
4. Sandbox resource pool 和 warm pool。

## 15. WindowsContainerSandboxBackend 逻辑（HCS / Hyper-V interface skeleton）

文件：`devpal/core/sandbox/backends/windows_container.py`
详细设计：[`windows_container_backend_design.md`](windows_container_backend_design.md)

### 15.1 当前状态

`windows_container` 是 P3 强隔离演进的目标 backend，当前落地为 **interface skeleton**：

- 后端名 `windows_container`，`isolation_level = "container"`。
- 结构完全对齐 `WindowsProcessSandboxSession`：相同的 `sandbox_id`、`sandbox_dir`、`workspace_dir`、`manifest_v2_path`、`runner_request_path`、`runner_result_path` 属性，相同的 `validate_command` / `build_manifest_v2` / `write_manifest_v2` 接口。
- `execute_command` **不会启动真实容器**，而是 fail closed：返回 `returncode=-1`，`error_code=CONTAINER_BACKEND_NOT_IMPLEMENTED`。
- 关键点：fail closed 前仍会写 `runner_request.json` 和 `manifest.v2.json(status="failed")`，所以审计链、EventBus、final report 都会看到一次「被明确拒绝的容器后端尝试」，而不是静默降级到更弱的 backend。

选择这种做法的原因：真实 Hyper-V / HCS 容器无法在当前 dev / CI 环境启动（无 Hyper-V、镜像体积大、冷启动慢）。skeleton 先把协议、接线、审计层全部固定下来，等真实 launcher 就绪时，只需替换 `execute_command` 一个方法，OpenSpec、EventBus、manifest、final report、CLI 都不需要改。

### 15.2 container 请求协议

`WindowsContainerSandboxSession.container_spec()` 会把容器启动参数写进 `runner_request.json` 的 `container` 字段，供未来 HCS/Hyper-V launcher 消费：

```json
{
  "container": {
    "image": "mcr.microsoft.com/windows/nanoserver:ltsc2022",
    "isolation": "hyperv",
    "runtime": "docker",
    "container_workspace": "C:\\workspace",
    "network": "none",
    "max_memory_mb": null,
    "max_processes": null,
    "mounts": [
      {
        "host_path": ".../.spec/sandboxes/<id>/workspace",
        "container_path": "C:\\workspace",
        "read_only": false
      }
    ]
  }
}
```

- `image` / `isolation` / `runtime` / `container_workspace` 从 `sandbox_backend_options["container_options"]` 读取，可让 operator 在不改代码的前提下 pin 镜像和隔离模式。
- `network` 由 policy 推导：`policy.network == "deny"` 时为 `none`，否则 `default`。
- `max_memory_mb` / `max_processes` 复用 `SandboxPolicy`，与 `windows_process` 的 Job Object 限制同源。
- `mounts` 默认把 sandbox workspace 以读写方式挂到容器内 `container_workspace`，为 copy-in / copy-out 铺路。

### 15.3 backend 演进路线

```text
SandboxBackend
  -> PolicySandboxBackend            # low   风险：policy 校验 + 本地执行
  -> WindowsProcessSandboxBackend    # medium 风险：low integrity / restricted token / ACL / firewall
  -> WindowsContainerSandboxBackend  # high  风险：Hyper-V isolated container（当前为 skeleton）
  -> RemoteWorkerSandboxBackend      # critical 风险：远程隔离 VM / worker（规划中）
```

真实 HCS / Hyper-V launcher 目标：

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

推荐策略：按任务风险等级选择 backend。

| 风险等级 | backend |
| --- | --- |
| low | policy |
| medium | windows_process |
| high | windows_container（skeleton，待真实 launcher） |
| critical | remote isolated VM / worker |

## 16. 验收测试建议

单元测试：

```powershell
python -m pytest -p no:cacheprovider --basetemp .tmp\pytest_sandbox `
  tests/security/test_sandbox_escape_attempts.py `
  tests/openspec/test_sandbox_manifest_v2.py `
  tests/openspec/test_sandbox_policy_backend.py `
  tests/openspec/test_sandbox_windows_process_backend.py `
  tests/openspec/test_sandbox_windows_container_backend.py `
  tests/openspec/test_sandbox_manager.py `
  tests/openspec/test_sandbox_env_profiles.py `
  tests/openspec/test_sandbox_workspace.py `
  tests/openspec/test_sandbox_reaper.py `
  tests/openspec/test_sandbox_runner_schema.py `
  tests/openspec/test_openspec_executor.py `
  tests/openspec/test_run_ai_flow_sandbox_config.py `
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
  --phase10-workspace-execution `
  --no-abort `
  --verbose `
  --resume
```

可选强隔离 smoke：

```powershell
python run_ai_flow.py `
  -r requirements/simple_calculator.md `
  --sandbox-backend windows_process `
  --sandbox-level staging `
  --phase10-workspace-execution `
  --sandbox-low-integrity `
  --sandbox-harden-workspace-acl
```

network deny PoC 通常需要管理员权限：

```powershell
python run_ai_flow.py `
  -r requirements/simple_calculator.md `
  --sandbox-backend windows_process `
  --sandbox-network-deny
```

管理员/提升权限验收脚本：

```powershell
python scripts/validate_windows_sandbox_elevated.py --include-network
```

该脚本会在 `.tmp/sandbox_elevated_validation/` 下创建临时项目，复用 `WindowsProcessSandboxBackend` 真实路径，输出 low integrity、ACL hardening、network deny 的 runner result 与 manifest v2。

期望：

- Phase 3-11 完成。
- Phase 10 使用 `windows_process`。
- `.spec/sandboxes/*/runner_request.json` 存在。
- `.spec/sandboxes/*/runner_result.json` 存在。
- `.spec/sandboxes/*/manifest.v2.json` 存在。
- EventBus 中存在 sandbox created/policy_applied/command_started/command_completed/cleanup_completed。
- final report 包含 `Multi-Agent Sandbox Summary`、`Sandbox Isolation Details`、`Sandbox execution enabled` 和 `windows_process` backend。
- 如果开启 `--phase10-workspace-execution`，C++ build/test 应发生在 `.spec/sandboxes/phase10-workspace-execution/workspace` 下。

## 17. 面试表达版本

可以这样讲：

> 我在 DevPalAgent 里把 Agent 执行安全拆成 policy layer、SandboxManager 和 backend layer。policy layer 做 deterministic 校验，包括命令入口、cwd、路径、production 禁止本地执行；SandboxManager 统一 backend 选择、audit、runner result 汇总和 reaper 入口；backend layer 决定执行方式。当前已经实现 Windows process backend：Phase 10 命令会被转换成 runner_request.json，交给 C# runner 执行。runner 不走 shell，使用 argv、timeout、stdout/stderr 捕获和 Windows Job Object 清理进程树，执行结果回写 runner_result.json，并生成 manifest v2、EventBus 事件和 final report 摘要。
> 在强隔离演进上，我已经补了 low integrity token 启动、实际执行目录低完整性标签 hardening 钩子，以及 Windows Firewall 出站 deny PoC。这个版本仍不是 Hyper-V/AppContainer 级强隔离，但它已经从“只管进程生命周期”推进到了“可选权限降级 + 可审计网络阻断 PoC”。后续可以把 backend 下沉到 AppContainer、WFP 或 HCS / Hyper-V，而不需要重写 OpenSpec、EventBus、manifest 和 final report。

## 18. 当前测试记录

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
- 默认启动：如果仓库内存在 `.tmp\dotnet8\dotnet.exe` 和 runner dll，Python wrapper 会优先使用 bundled dotnet 启动 `devpal-sandbox-runner.dll`；否则回退到默认 runner exe。

单元/集成测试：
- 命令：python -m pytest -q -p no:cacheprovider --basetemp .tmp\pytest_sandbox_full_continue ...
- 覆盖：security escape attempts、manifest v2、policy backend、windows_process backend、SandboxManager、env profiles、workspace copy-in、reaper、runner schema、OpenSpec executor、run_ai_flow config、Phase 10、failure policy、compile error summary、Phase 11 final report、EventBus、sandbox merge。
- 结果：84 passed，2 warnings。
- 追加回归：Phase 10 在 cmake build 失败时，即使旧 exe 仍存在，也会返回失败，避免 stale executable 掩盖真实构建失败。
- 追加回归：`CommandSpec.env is None` 时，runner request 使用按 profile allowlist 过滤后的当前环境，不写入 key/token/password 类变量。
- 追加回归：pytest request 不混入 MSVC `INCLUDE/LIB`，CMake/MSVC request 会保留必要工具链变量。
- 追加回归：runner request/result schema 不合法时 fail closed，并把 `error_code` 写入 manifest v2。
- 追加回归：`SandboxManager` 会统一执行 windows_process backend，生成 Phase 10 summary，并透传 isolation features。
- 追加回归：CLI/config/OpenSpecRunOptions 能透传 `low_integrity`、`harden_workspace_acl`、`network_deny`。
- 追加回归：C++ Phase 10 workspace execution 会 copy-in 项目源码，并在 workspace 下执行 runner request。
- 追加回归：Python Phase 10 workspace execution 会 copy-in `src/`、`tests/` 和 Python 项目配置，并在 workspace 下执行 pytest。
- 追加回归：manifest v2 会记录 `runner_executable_path`、`runner_args`、`runner_invocation`。
- 追加回归：SandboxReaper 可以按 status、workflow_id、task_id 筛选 stale sandbox。
- 追加回归：Phase 11 final report 会展开 `Sandbox Isolation Details`，直接展示 low integrity、workspace ACL、network deny、launcher、job assigned 和 runner error code。
- 追加回归：ACL hardening 目标从审计 workspace 修正为实际执行目录，并在 `workspace_acl_path` 中记录。
- 追加回归：`SandboxManager` 会阻止未启用 workspace execution 的 `harden_workspace_acl`，避免给真实项目根目录打低完整性标签。
- 追加回归：runner request/result JSON Schema 资产存在，且 schema version 与运行时校验常量一致。
- 追加回归：默认 runner invocation 在 bundled dotnet 可用时使用 `.tmp\dotnet8\dotnet.exe devpal-sandbox-runner.dll`。
- 追加回归：SandboxReaper 可以 dry-run/apply 清理 stale failed/timeout/running/created sandbox。
- 追加回归：MSVC 编译器探测能处理 Windows 环境里同时存在 `Path` 和 `PATH` 的情况，优先选择包含 `cl.exe` 的 PATH。
- 追加回归：MSVC CMake configure 使用 `NMake Makefiles`，避免硬编码 `Visual Studio 16 2019` 与 VS 18/2026 环境不匹配。

完整流程：
- 2026-07-03 08:33 的完整流程成功：OpenSpec 11-phase pipeline complete，Phase 10 成功，14/14 passed，self-heal attempts=0，Sandboxed tasks=7，Policy violations=0。
- 2026-07-03 08:45 在环境继承修复后再次执行完整流程，失败于 Phase 4 AI code generation：Anthropic APIConnectionError / network connection failed。该失败发生在进入 Phase 10 沙箱前，不属于 sandbox backend 失败。
- 2026-07-03 21:14 在放开网络限制后重新执行完整流程成功：OpenSpec 11-phase pipeline complete，Phase 10 成功，12/12 passed，self-heal attempts=0，Sandboxed tasks=5，Policy violations=0。
- 最新完整流程日志：cpp_simple_calculator\cpp_simple_calculator_20260703_211439.log。
- 最新 final report：cpp_simple_calculator\docs\final_report.md，包含 `Sandbox execution enabled: True`、`Sandbox backend: windows_process`。
- 为验证最新沙箱代码，已绕开网络依赖直接执行 Phase 10：`OpenSpecContext(language="cpp", sandbox_backend="windows_process") -> Phase10RunTests.execute()`。
- 直接 C++ Phase 10 workspace execution 结果：成功，12/12 passed，Sandboxed tasks=7。
- workspace 路径：`cpp_simple_calculator\.spec\sandboxes\phase10-workspace-execution\workspace`。
- 直接 Phase 10 runner_result：7/7 success=true，exit_code=0，timed_out=false。
- Phase 10 CMake configure：使用 `NMake Makefiles`，request env 中包含 MSVC `PATH/INCLUDE/LIB/VCToolsInstallDir` 等必要变量。
- 直接 Python Phase 10 workspace execution 结果：成功，1/1 passed，Sandboxed tasks=1。

runner smoke：
- 普通 runner smoke：成功，`job_assigned=true`，result 包含 isolation audit 字段。
- low integrity runner smoke：成功，`low_integrity_requested=true`，`low_integrity_applied=true`，`process_launcher=low_integrity`，`job_assigned=true`。
- workspace ACL hardening smoke：当前执行环境对 `icacls /setintegritylevel` 返回 Access denied；runner 按 fail closed 写入 `ISOLATION_SETUP_FAILED` 和 `workspace_acl_error`。
- network deny PoC：实现为临时 Windows Firewall 出站 block rule，未在当前非管理员环境强行创建系统规则。

本轮追加验证（2026-07-05）：
- C# runner build：成功，0 warning，0 error。
- Targeted pytest：`tests/openspec/test_phase11_final_report.py`、`test_sandbox_runner_schema.py`、`test_sandbox_windows_process_backend.py`、`test_sandbox_manager.py`，17 passed，2 warnings。
- Elevated validation script syntax check：`python -m py_compile scripts/validate_windows_sandbox_elevated.py` 成功。
- 非管理员 smoke：`python scripts/validate_windows_sandbox_elevated.py --project-dir .tmp\sandbox_elevated_validation\codex_smoke` 成功，low integrity applied，ACL smoke 按脚本规则跳过。

敏感信息检查：
- 范围：cpp_simple_calculator\.spec\sandboxes 下的 runner_request.json、runner_result.json、manifest.v2.json。
- 检查项：ANTHROPIC_AUTH_TOKEN、OPENAI_API_KEY、ANTHROPIC_API_KEY、PASSWORD、SECRET、TOKEN、sk-。
- 结果：未发现敏感环境变量名或 sk- token。

已确认的问题与修复：
- 修复 runner_request.json 写入完整环境变量导致 token 泄露的风险，现在只写入按 profile allowlist 过滤后的 env。
- 修复 C# runner 默认继承父进程环境的问题，现在先清空环境，再注入 request 中过滤后的 env。
- 修复 C# runner 对 sandbox_dir/workspace_dir/result_path/cwd 缺少边界校验的问题。
- 修复默认 runner exe 依赖系统 .NET 8 runtime 的问题，本地 bundled dotnet 可用时自动启动 runner dll。
- 修复 Job Object assign 失败后命令仍可能继续运行的问题，现在 fail closed 并返回 `JOB_ASSIGN_FAILED`。
- 修复 Phase 10 build 失败但旧 exe 存在时可能误判成功的问题。
- 修复 Windows 子进程输出解码在中文/MSVC 输出下可能异常的问题。
- 修复 MSVC compiler detector 中 `Path/PATH` 覆盖导致 `cl.exe` 探测失败的问题。
- 修复 Phase 10 MSVC CMake generator 硬编码 VS2019，改为版本中性的 `NMake Makefiles`。
- 收紧 C++ 测试生成 prompt，避免生成 test_base.h 不支持的 ASSERT_THROW、ASSERT_NE、GoogleTest/Catch2 宏。

本轮追加验证（2026-07-06，windows_container backend skeleton）：
- 新增 `windows_container` backend interface skeleton（`devpal/core/sandbox/backends/windows_container.py`），backend=`windows_container`，isolation_level=`container`。
- 该 backend 复用 `WindowsProcessSandboxSession` 的会话形状、runner_request 协议和 manifest v2 结构；额外在 request/manifest 中写入 `container` 段（image、isolation、runtime、mounts、network、memory/process 限制）。
- `execute_command` 当前 fail closed：不启动真实容器，返回 `CONTAINER_BACKEND_NOT_IMPLEMENTED`，但仍写入 `runner_request.json` 和 `manifest.v2.json(status=failed)`，保证审计链完整、不静默降级到弱 backend。
- 通用化 `SandboxManager` 分派：`SANDBOX_MANAGER_BACKENDS = ("windows_process", "windows_container")`，`_create_backend(...)` 按名字选择 backend；`execute_command` 不再硬编码 `windows_process`。
- Phase 10 新增 `_is_sandbox_manager_backend_enabled()`，命令分派和 multi-agent gate 从“仅 windows_process”改为“任意 manager backend”。
- CLI 与 config allowlist：`--sandbox-backend` choices 增加 `windows_container`，`config.sandbox.backend` 校验集合同步扩展。
- 新增测试 `tests/openspec/test_sandbox_windows_container_backend.py`：backend/session 形状、fail-closed execute、runner_request + manifest 审计落盘、manager 分派，4 passed。
- 回归：新增 backend 测试 4 passed；沙箱套件 58 passed；Phase 10/11 + CLI config 套件 44 passed，无回归。
- 端到端复跑 `cpp_simple_calculator` Phase 10（windows_process + workspace execution）：12/12 passed，Sandboxed tasks=7，runner_request/runner_result/manifest.v2 各 14 份，copy-out gate pending（159 artifacts，9.05MB，requires_manual_apply=true，applied=false）。
- copy-out CLI（`python -m devpal.openspec apply-copy-out`）preview：成功，159 artifacts 全部 hash 校验通过，status=PREVIEW，未 apply。
- `windows_container` 端到端 fail-closed 复核：returncode=-1，error_code=`CONTAINER_BACKEND_NOT_IMPLEMENTED`，manifest.v2 status=failed，container spec 中 `network=none`（由 deny policy 推导）。
- 新增详细设计文档 `docs/architecture/windows_container_backend_design.md`，覆盖 backend interface、request/result 协议复用、copy-in/copy-out 流程、最小 HCS/Hyper-V 启动方案、演进路线。
```
