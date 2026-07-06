# Windows 容器隔离后端设计说明（HCS / Hyper-V）

> 更新时间：2026-07-06
> 适用范围：DevPalAgent Phase 10 高风险任务的强隔离执行演进路线。
> 当前状态：`windows_container` 后端为**接口骨架（interface skeleton）**。它已经接入 backend 选择、`SandboxManager` 调度、CLI/config 白名单、runner request 与 manifest v2 审计链，但**尚未实现真正的 HCS/Hyper-V 容器启动**。`execute_command` 目前 fail closed，返回结构化错误码 `CONTAINER_BACKEND_NOT_IMPLEMENTED`，不会静默降级到更弱的后端。

## 1. 为什么需要容器后端

`windows_process` 后端已经把 Phase 10 从裸 `subprocess.run` 升级为“策略约束 + 进程生命周期管理 + 可选权限降级（low integrity / restricted token）+ 网络阻断 PoC + 全链路审计”。但它本质上仍是**同主机、同内核**的进程级隔离：

- Job Object 管的是生命周期和资源上限，不是安全边界。
- low integrity / restricted token 收紧了权限，但仍共享主机文件系统、注册表、内核对象。
- network deny 是 Firewall 规则 PoC，不是 per-container 网络命名空间。

对于**高风险任务**（不可信代码、需要真正内核边界、需要独立文件系统与网络栈），需要一个更强的隔离后端。Windows 上的答案是 **HCS（Host Compute System）/ Hyper-V isolated Windows container**：每个容器有独立的内核实例，主机内核不直接暴露给容器内进程。

设计原则：**不替换 `windows_process`，而是作为按风险等级路由的更强后端。**

```text
SandboxBackend
  -> PolicySandboxBackend          (low risk)
  -> WindowsProcessSandboxBackend  (medium risk，当前 MVP)
  -> WindowsContainerSandboxBackend(high risk，本文档，HCS/Hyper-V)
  -> RemoteWorkerSandboxBackend    (critical risk，隔离 VM/worker)
```

| 风险等级 | backend |
| --- | --- |
| low | `policy` |
| medium | `windows_process` |
| high | `windows_container` (HCS / Hyper-V) |
| critical | remote isolated VM / worker |

## 2. 协议复用：为什么切换后端不需要重写上层

容器后端的核心价值在于**复用现有协议**。整条链路已经是 backend-neutral 的：

```text
SandboxRequest
  -> runner_request.json   (新增 container 段)
  -> runner_result.json    (schema 复用 v1)
  -> manifest.v2.json      (backend=windows_container, isolation_level=container)
  -> EventBus sandbox 事件
  -> Phase 11 final report
```

因此接入一个新后端只需要：

1. 实现 `SandboxBackend` / `SandboxSessionHandle` 协议（`devpal/core/sandbox/backends/base.py`）。
2. 在 `backends/__init__.py` 导出。
3. 在 `SandboxManager._create_backend` 增加分支（`devpal/core/sandbox/manager.py`）。
4. 在 CLI/config 白名单加入 backend 名（`run_ai_flow.py`）。
5. 在 Phase 10 的 `_is_sandbox_manager_backend_enabled` 中纳入（`phase10_run_tests.py`）。

**OpenSpec、EventBus、manifest、final report、copy-out gate 都不需要改动。** 这正是接口先行、协议稳定的收益。

## 3. 实现文件地图

| 模块 | 文件 |
| --- | --- |
| 容器后端骨架 | `devpal/core/sandbox/backends/windows_container.py` |
| backend 抽象协议 | `devpal/core/sandbox/backends/base.py` |
| backend 导出 | `devpal/core/sandbox/backends/__init__.py` |
| 后端调度 | `devpal/core/sandbox/manager.py`（`_create_backend`、`SANDBOX_MANAGER_BACKENDS`） |
| Phase 10 路由 | `devpal/core/openspec_phases/phase10_run_tests.py`（`_is_sandbox_manager_backend_enabled`） |
| CLI/config 白名单 | `run_ai_flow.py`（`--sandbox-backend` choices） |
| runner request/result schema | `devpal/core/sandbox/runner_schema.py` |
| manifest v2 | `devpal/core/sandbox/manifest.py` |
| 骨架测试 | `tests/openspec/test_sandbox_windows_container_backend.py` |

## 4. `container` runner 协议（当前已落地）

`WindowsContainerSandboxSession.build_runner_request` 在标准 runner request 基础上新增 `container` 段：

```json
{
  "schema_version": "devpal.sandbox.runner_request.v1",
  "backend": "windows_container",
  "isolation_level": "container",
  "command": { "argv": ["pytest", "tests", "-v"], "cwd": "...", "env": {} },
  "container": {
    "image": "mcr.microsoft.com/windows/nanoserver:ltsc2022",
    "isolation": "hyperv",
    "runtime": "docker",
    "container_workspace": "C:\\workspace",
    "network": "none",
    "max_memory_mb": 256,
    "max_processes": 4,
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

语义：

- `image`：容器基础镜像，可通过 `sandbox_backend_options.container_options.image` 覆盖。
- `isolation`：`hyperv`（默认，强隔离）或 `process`（进程隔离容器，弱一档）。
- `runtime`：容器运行时 CLI（`docker`；后续可换 HCS API 直连）。
- `network`：当 policy `network=deny` 时映射为 `none`（无网络命名空间），否则 `default`。
- `max_memory_mb` / `max_processes`：从 `SandboxPolicy` 透传，容器层用 `--memory` / 资源上限落地。
- `mounts`：copy-in workspace 作为唯一挂载点，容器内 cwd 指向 `container_workspace`。

`container_options` 走 `sandbox_backend_options.container_options`（dict），使运维可以固定镜像与隔离模式而无需改代码。

## 5. Fail-closed 语义（当前行为）

`execute_command` 当前**故意不启动容器**，而是：

1. 校验命令（复用 legacy `SandboxSession` 的 deterministic policy）。
2. 写 `runner_request.json`（含 `container` 段）——审计链保留。
3. 写 `manifest.v2.json`，`status=failed`，`metadata.error_code=CONTAINER_BACKEND_NOT_IMPLEMENTED`。
4. 返回 `CommandResult(returncode=-1, error="CONTAINER_BACKEND_NOT_IMPLEMENTED: ...")`。

这是**有意的 fail closed**：选择了 `windows_container` 却尚未实现真实启动时，绝不静默回退到 `windows_process` 或裸 subprocess——否则会造成“以为在强隔离里跑，其实在主机上跑”的安全误判。final report 会明确显示这是一次被拒绝的容器后端尝试。

## 6. 最小 HCS / Hyper-V 启动方案（后续实现）

当把骨架升级为可运行 PoC 时，只需替换 `execute_command` 的执行段，推荐分两步：

### 6.1 第一步：docker CLI + Hyper-V 隔离（最小可运行）

```text
docker run --rm ^
  --isolation=hyperv ^
  --name devpal-<sandbox_id> ^
  --memory <max_memory_mb>m ^
  --network none            (当 network=none) ^
  -v <host_workspace>:C:\workspace ^
  -w C:\workspace ^
  <image> ^
  <argv...>
```

- 捕获 stdout/stderr/exit_code，合成 `runner_result.json`（复用 `runner_result.v1` schema）。
- 运行时不可用（无 docker / 无 Hyper-V / CI 不支持）时，返回结构化错误码 `CONTAINER_RUNTIME_UNAVAILABLE`，同样 fail closed。
- 测试可注入一个 stub 运行时（指向本地脚本），使单测无需真实 docker 即可跑通执行路径。

### 6.2 第二步：HCS API 直连（去 docker 依赖）

- 通过 `computecore.dll`（HcsCreateComputeSystem / HcsStartComputeSystem）直接创建 Hyper-V isolated container。
- copy-on-write 层管理镜像与临时层。
- 容器内复用同一套 argv command 与 env profile。
- 收集 stdout/stderr/result/artifacts，写同一套 `runner_result.json` 与 `manifest.v2.json`，销毁 container 与临时层。

### 6.3 copy-in / copy-out 流程

- **copy-in**：复用 `SandboxWorkspacePlan.prepare()`（`devpal/core/sandbox/workspace.py`）把源码复制进 `.spec/sandboxes/<id>/workspace`，再作为容器挂载。
- **copy-out**：复用已实现的 copy-out hash gate（`devpal/core/sandbox/copy_out.py`）——容器产物先收集 SHA256 生成 `copy_out_manifest.json`，经 CLI `python -m devpal.openspec apply-copy-out --apply` 显式审批后才写回主项目。Agent 可以生成，但不能直接污染主项目。

## 7. 难点与权衡

- Windows 容器镜像体积大，冷启动慢（Hyper-V 隔离更慢）。
- 文件挂载与 copy-on-write 有成本。
- 容器网络策略复杂，`--network none` 是最简单的强 egress 阻断。
- 多并发 sandbox 需要资源池 / warm pool。
- CI 环境（尤其是嵌套虚拟化关闭时）可能不支持 Hyper-V——这正是 fail-closed 错误码存在的原因。

## 8. 验收测试

单元测试（当前骨架，跨平台可跑）：

```powershell
python -m pytest -p no:cacheprovider --basetemp .tmp\pytest_container `
  tests/openspec/test_sandbox_windows_container_backend.py `
  tests/openspec/test_sandbox_manager.py
```

期望：

- `windows_container` 后端实现 `SandboxBackend` 协议，session 暴露 `sandbox_id` / `runner_request_path` / `manifest_v2_path` 等 backend-neutral 字段。
- `execute_command` fail closed，返回 `CONTAINER_BACKEND_NOT_IMPLEMENTED`。
- runner request 含 `container` 段，manifest v2 `backend=windows_container`、`status=failed`、`error_code=CONTAINER_BACKEND_NOT_IMPLEMENTED`。
- `SandboxManager` 能按 `context.sandbox_backend=windows_container` 调度到容器后端并汇总 summary。
- CLI `--sandbox-backend windows_container` 被接受（choices 已包含）。

后续实现真实启动后，追加：

- 在支持 Hyper-V 的机器上跑一次真实容器执行，确认 stdout/exit_code 正确、workspace 挂载生效、`--network none` 阻断出站。
- 运行时缺失机器上确认返回 `CONTAINER_RUNTIME_UNAVAILABLE` 且 fail closed。

## 9. 面试表达版本

> 我在 DevPalAgent 里把 Agent 执行安全做成了可分层演进的 backend 体系：policy → windows_process → windows_container → remote worker，按任务风险等级路由。关键设计是协议先行——`SandboxRequest → runner_request → runner_result → manifest.v2 → EventBus → final report` 这条链路是 backend-neutral 的，所以接入更强隔离后端时，OpenSpec、审计、事件、报告都不用改。
> 目前 `windows_container`（HCS/Hyper-V）是接口骨架：它已经接入调度、CLI、审计链，`execute_command` 明确 fail closed 返回 `CONTAINER_BACKEND_NOT_IMPLEMENTED`，绝不静默降级到主机进程后端——因为“以为在强隔离里跑其实在主机上跑”是最危险的安全误判。升级为可运行 PoC 时只需替换执行段：第一步用 `docker run --isolation=hyperv` 挂载 copy-in workspace，第二步换成 HCS API 直连；copy-in 复用 workspace plan，copy-out 复用已经实现的 SHA256 hash gate 审批。这体现的是从进程级 MVP 到内核级强隔离的平滑演进路径，而不是推倒重来。
