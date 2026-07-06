using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.Win32.SafeHandles;

namespace DevPal.SandboxRunner;

internal static class Program
{
    internal const string RequestSchemaVersion = "devpal.sandbox.runner_request.v1";
    internal const string ResultSchemaVersion = "devpal.sandbox.runner_result.v1";
    internal const string ErrorProcessStartFailed = "PROCESS_START_FAILED";
    internal const string ErrorTimeout = "TIMEOUT";
    internal const string ErrorJobAssignFailed = "JOB_ASSIGN_FAILED";
    internal const string ErrorIsolationSetupFailed = "ISOLATION_SETUP_FAILED";
    internal const string ErrorNetworkDenyFailed = "NETWORK_DENY_FAILED";
    internal const string ErrorResourceLimitSetupFailed = "RESOURCE_LIMIT_SETUP_FAILED";

    private static readonly UTF8Encoding Utf8NoBom = new(false);
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        WriteIndented = true,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
    };

    public static async Task<int> Main(string[] args)
    {
        if (args.Length != 1)
        {
            Console.Error.WriteLine("usage: devpal-sandbox-runner <sandbox_request.json>");
            return 2;
        }

        var requestPath = Path.GetFullPath(args[0]);
        RunnerRequest? request;
        try
        {
            var json = await File.ReadAllTextAsync(requestPath, Encoding.UTF8);
            request = JsonSerializer.Deserialize<RunnerRequest>(json, JsonOptions);
            NormalizeAndValidateRequest(request, requestPath);
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine(ex.Message);
            return 2;
        }

        var validatedRequest = request!;
        Directory.CreateDirectory(validatedRequest.WorkspaceDir);
        Directory.CreateDirectory(Path.GetDirectoryName(validatedRequest.ResultPath)!);

        var result = await RunCommandAsync(validatedRequest);
        await File.WriteAllTextAsync(
            validatedRequest.ResultPath,
            JsonSerializer.Serialize(result, JsonOptions),
            Utf8NoBom);
        return result.Success ? 0 : 1;
    }

    private static async Task<RunnerResult> RunCommandAsync(RunnerRequest request)
    {
        var command = request.Command!;
        var started = Stopwatch.StartNew();
        var isolation = IsolationReport.FromRequest(request);

        if (request.Isolation?.HardenWorkspaceAcl == true)
        {
            var aclTarget = ResolveIntegrityTarget(request, command);
            isolation.WorkspaceAclPath = aclTarget;
            var acl = IntegrityLabel.TrySetLowIntegrity(aclTarget);
            isolation.WorkspaceAclHardened = acl.Success;
            isolation.WorkspaceAclError = acl.Error;
            if (!acl.Success)
            {
                started.Stop();
                return RunnerResult.SetupFailed(
                    request,
                    command,
                    command.Cwd ?? request.WorkspaceDir,
                    started.ElapsedMilliseconds,
                    acl.Error,
                    ErrorIsolationSetupFailed,
                    isolation);
            }
        }

        using var networkGuard = NetworkGuard.TryCreate(request, command);
        isolation.NetworkDenyRequested = request.Isolation?.NetworkDeny == true;
        isolation.NetworkDenyApplied = networkGuard.Applied;
        isolation.NetworkRuleName = networkGuard.RuleName;
        isolation.NetworkError = networkGuard.Error;
        if (request.Isolation?.NetworkDeny == true && !networkGuard.Applied)
        {
            started.Stop();
            return RunnerResult.SetupFailed(
                request,
                command,
                command.Cwd ?? request.WorkspaceDir,
                started.ElapsedMilliseconds,
                networkGuard.Error,
                ErrorNetworkDenyFailed,
                isolation);
        }

        using var job = JobObject.TryCreate(
            request.SandboxId,
            request.Policy?.MaxProcesses,
            request.Policy?.MaxMemoryMb);
        var jobRequired = (request.Policy?.MaxProcesses ?? 0) > 0
            || (request.Policy?.MaxMemoryMb ?? 0) > 0;
        if (jobRequired && job is null)
        {
            started.Stop();
            return RunnerResult.SetupFailed(
                request,
                command,
                command.Cwd ?? request.WorkspaceDir,
                started.ElapsedMilliseconds,
                "failed to create Windows Job Object with requested resource limits",
                ErrorResourceLimitSetupFailed,
                isolation);
        }
        if (request.Isolation?.LowIntegrity == true || request.Isolation?.RestrictedToken == true)
        {
            return await LowIntegrityProcessLauncher.RunAsync(request, command, job, isolation, started);
        }

        var psi = new ProcessStartInfo
        {
            FileName = command.Argv[0],
            WorkingDirectory = string.IsNullOrWhiteSpace(command.Cwd)
                ? request.WorkspaceDir
                : command.Cwd,
            UseShellExecute = false,
            RedirectStandardOutput = command.CaptureOutput,
            RedirectStandardError = command.CaptureOutput,
            CreateNoWindow = true
        };

        foreach (var arg in command.Argv.Skip(1))
        {
            psi.ArgumentList.Add(arg);
        }

        psi.Environment.Clear();
        if (command.Env is not null)
        {
            foreach (var item in command.Env)
            {
                psi.Environment[item.Key] = item.Value;
            }
        }

        using var process = new Process { StartInfo = psi, EnableRaisingEvents = true };
        var stdoutTask = Task.FromResult("");
        var stderrTask = Task.FromResult("");
        var jobAssigned = false;

        try
        {
            process.Start();
            jobAssigned = job?.Assign(process) ?? false;
            if (job is not null && !jobAssigned)
            {
                try
                {
                    process.Kill(entireProcessTree: true);
                }
                catch
                {
                    // Best effort cleanup. Returning a failed result is the policy decision.
                }

                started.Stop();
                return RunnerResult.JobAssignFailed(
                    request,
                    command,
                    process.Id,
                    psi.WorkingDirectory,
                    started.ElapsedMilliseconds,
                    job.Name,
                    job.MemoryLimitMb,
                    isolation);
            }

            if (command.CaptureOutput)
            {
                stdoutTask = process.StandardOutput.ReadToEndAsync();
                stderrTask = process.StandardError.ReadToEndAsync();
            }

            var timeoutMs = Math.Max(1, command.TimeoutSeconds) * 1000;
            var exited = await Task.Run(() => process.WaitForExit(timeoutMs));
            if (!exited)
            {
                try
                {
                    process.Kill(entireProcessTree: true);
                }
                catch
                {
                    // Best effort cleanup. The Job Object close path is the second guard.
                }

                started.Stop();
                return RunnerResult.Timeout(
                    request,
                    command,
                    process.Id,
                    started.ElapsedMilliseconds,
                    job?.Name,
                    jobAssigned,
                    job?.MemoryLimitMb,
                    isolation);
            }

            started.Stop();
            return new RunnerResult
            {
                SchemaVersion = ResultSchemaVersion,
                SandboxId = request.SandboxId,
                ExecutionId = request.ExecutionId,
                Status = process.ExitCode == 0 ? "completed" : "failed",
                Success = process.ExitCode == 0,
                Argv = command.Argv,
                Cwd = psi.WorkingDirectory,
                Pid = process.Id,
                ExitCode = process.ExitCode,
                Stdout = await stdoutTask,
                Stderr = await stderrTask,
                DurationMs = started.ElapsedMilliseconds,
                TimedOut = false,
                CleanupStatus = "clean",
                Isolation = isolation,
                JobObject = job?.Name,
                JobAssigned = job is null ? null : jobAssigned,
                JobMemoryLimitMb = job?.MemoryLimitMb
            };
        }
        catch (Exception ex)
        {
            started.Stop();
            return new RunnerResult
            {
                SchemaVersion = ResultSchemaVersion,
                SandboxId = request.SandboxId,
                ExecutionId = request.ExecutionId,
                Status = "failed",
                Success = false,
                Argv = command.Argv,
                Cwd = command.Cwd ?? request.WorkspaceDir,
                ExitCode = -1,
                Stdout = "",
                Stderr = "",
                DurationMs = started.ElapsedMilliseconds,
                TimedOut = false,
                CleanupStatus = "best_effort",
                Error = ex.Message,
                ErrorCode = ErrorProcessStartFailed,
                Isolation = isolation,
                JobObject = job?.Name,
                JobAssigned = job is null ? null : jobAssigned,
                JobMemoryLimitMb = job?.MemoryLimitMb
            };
        }
    }

    private static void NormalizeAndValidateRequest(RunnerRequest? request, string requestPath)
    {
        if (request is null)
        {
            throw new InvalidOperationException("request is required");
        }

        if (request.Command?.Argv is null || request.Command.Argv.Count == 0)
        {
            throw new InvalidOperationException("command.argv is required");
        }

        if (request.SchemaVersion != RequestSchemaVersion)
        {
            throw new InvalidOperationException("unsupported schema_version");
        }

        if (string.IsNullOrWhiteSpace(request.SandboxId))
        {
            throw new InvalidOperationException("sandbox_id is required");
        }

        var requestDir = Path.GetDirectoryName(requestPath)!;
        if (string.IsNullOrWhiteSpace(request.SandboxDir))
        {
            request.SandboxDir = requestDir;
        }
        request.SandboxDir = Path.GetFullPath(request.SandboxDir);

        if (string.IsNullOrWhiteSpace(request.WorkspaceDir))
        {
            request.WorkspaceDir = Path.Combine(request.SandboxDir, "workspace");
        }
        request.WorkspaceDir = Path.GetFullPath(request.WorkspaceDir);
        EnsureWithin(request.WorkspaceDir, request.SandboxDir, "workspace_dir");

        if (string.IsNullOrWhiteSpace(request.ResultPath))
        {
            throw new InvalidOperationException("result_path is required");
        }
        request.ResultPath = Path.GetFullPath(request.ResultPath);
        EnsureWithin(request.ResultPath, request.SandboxDir, "result_path");

        if (!string.IsNullOrWhiteSpace(request.ProjectDir))
        {
            request.ProjectDir = Path.GetFullPath(request.ProjectDir);
            if (!string.IsNullOrWhiteSpace(request.Command.Cwd))
            {
                request.Command.Cwd = Path.GetFullPath(request.Command.Cwd);
                EnsureWithin(request.Command.Cwd, request.ProjectDir, "command.cwd");
            }
        }
        else if (!string.IsNullOrWhiteSpace(request.Command.Cwd))
        {
            request.Command.Cwd = Path.GetFullPath(request.Command.Cwd);
        }

        if (request.Command.TimeoutSeconds <= 0)
        {
            request.Command.TimeoutSeconds = 300;
        }

        if (request.Command.Env is not null)
        {
            foreach (var item in request.Command.Env)
            {
                if (string.IsNullOrWhiteSpace(item.Key))
                {
                    throw new InvalidOperationException("command.env contains empty key");
                }
            }
        }
    }

    private static void EnsureWithin(string child, string parent, string fieldName)
    {
        var relative = Path.GetRelativePath(parent, child);
        if (relative == ".")
        {
            return;
        }
        if (
            relative == ".." ||
            relative.StartsWith(".." + Path.DirectorySeparatorChar) ||
            relative.StartsWith(".." + Path.AltDirectorySeparatorChar) ||
            Path.IsPathRooted(relative))
        {
            throw new InvalidOperationException($"{fieldName} escapes sandbox boundary");
        }
    }

    private static string ResolveIntegrityTarget(RunnerRequest request, CommandRequest command)
    {
        var target = string.IsNullOrWhiteSpace(command.Cwd)
            ? request.WorkspaceDir
            : command.Cwd;
        target = Path.GetFullPath(target);
        if (!string.IsNullOrWhiteSpace(request.ProjectDir))
        {
            EnsureWithin(target, request.ProjectDir, "integrity_target");
        }
        return target;
    }
}

internal sealed class RunnerRequest
{
    public string SchemaVersion { get; set; } = "";
    public string SandboxId { get; set; } = "";
    public string ExecutionId { get; set; } = "";
    public string ProjectDir { get; set; } = "";
    public string SandboxDir { get; set; } = "";
    public string WorkspaceDir { get; set; } = "";
    public string ResultPath { get; set; } = "";
    public CommandRequest? Command { get; set; }
    public PolicyRequest? Policy { get; set; }
    public IsolationRequest? Isolation { get; set; }
}

internal sealed class CommandRequest
{
    public List<string> Argv { get; set; } = [];
    public string? Cwd { get; set; }
    public int TimeoutSeconds { get; set; } = 300;
    public Dictionary<string, string>? Env { get; set; }
    public bool CaptureOutput { get; set; } = true;
}

internal sealed class PolicyRequest
{
    public int? MaxProcesses { get; set; }
    public int? MaxMemoryMb { get; set; }
}

internal sealed class IsolationRequest
{
    public bool LowIntegrity { get; set; }
    public bool HardenWorkspaceAcl { get; set; }
    public bool NetworkDeny { get; set; }
    public bool RestrictedToken { get; set; }
}

internal sealed class IsolationReport
{
    public bool LowIntegrityRequested { get; set; }
    public bool LowIntegrityApplied { get; set; }
    public string? LowIntegrityError { get; set; }
    public bool WorkspaceAclRequested { get; set; }
    public bool WorkspaceAclHardened { get; set; }
    public string? WorkspaceAclPath { get; set; }
    public string? WorkspaceAclError { get; set; }
    public bool NetworkDenyRequested { get; set; }
    public bool NetworkDenyApplied { get; set; }
    public string? NetworkRuleName { get; set; }
    public string? NetworkError { get; set; }
    public bool RestrictedTokenRequested { get; set; }
    public bool RestrictedTokenApplied { get; set; }
    public string? RestrictedTokenError { get; set; }
    public string ProcessLauncher { get; set; } = "process";

    public static IsolationReport FromRequest(RunnerRequest request)
    {
        return new IsolationReport
        {
            LowIntegrityRequested = request.Isolation?.LowIntegrity == true,
            WorkspaceAclRequested = request.Isolation?.HardenWorkspaceAcl == true,
            NetworkDenyRequested = request.Isolation?.NetworkDeny == true,
            RestrictedTokenRequested = request.Isolation?.RestrictedToken == true,
        };
    }
}

internal sealed class RunnerResult
{
    public string SchemaVersion { get; set; } = "";
    public string SandboxId { get; set; } = "";
    public string ExecutionId { get; set; } = "";
    public string Status { get; set; } = "";
    public bool Success { get; set; }
    public List<string> Argv { get; set; } = [];
    public string Cwd { get; set; } = "";
    public int Pid { get; set; }
    public int ExitCode { get; set; }
    public string Stdout { get; set; } = "";
    public string Stderr { get; set; } = "";
    public long DurationMs { get; set; }
    public bool TimedOut { get; set; }
    public string CleanupStatus { get; set; } = "";
    public string? Error { get; set; }
    public string? ErrorCode { get; set; }
    public IsolationReport? Isolation { get; set; }
    public string? JobObject { get; set; }
    public bool? JobAssigned { get; set; }
    public int? JobMemoryLimitMb { get; set; }

    public static RunnerResult Timeout(
        RunnerRequest request,
        CommandRequest command,
        int pid,
        long durationMs,
        string? jobObject,
        bool? jobAssigned,
        int? jobMemoryLimitMb = null)
    {
        return new RunnerResult
        {
            SchemaVersion = Program.ResultSchemaVersion,
            SandboxId = request.SandboxId,
            ExecutionId = request.ExecutionId,
            Status = "timeout",
            Success = false,
            Argv = command.Argv,
            Cwd = command.Cwd ?? request.WorkspaceDir,
            Pid = pid,
            ExitCode = -1,
            Stdout = "",
            Stderr = "",
            DurationMs = durationMs,
            TimedOut = true,
            CleanupStatus = "killed",
            Error = $"timeout after {command.TimeoutSeconds}s",
            ErrorCode = Program.ErrorTimeout,
            JobObject = jobObject,
            JobAssigned = jobAssigned,
            JobMemoryLimitMb = jobMemoryLimitMb
        };
    }

    public static RunnerResult Timeout(
        RunnerRequest request,
        CommandRequest command,
        int pid,
        long durationMs,
        string? jobObject,
        bool? jobAssigned,
        int? jobMemoryLimitMb,
        IsolationReport isolation)
    {
        var result = Timeout(request, command, pid, durationMs, jobObject, jobAssigned, jobMemoryLimitMb);
        result.Isolation = isolation;
        return result;
    }

    public static RunnerResult JobAssignFailed(
        RunnerRequest request,
        CommandRequest command,
        int pid,
        string cwd,
        long durationMs,
        string jobObject,
        int? jobMemoryLimitMb,
        IsolationReport isolation)
    {
        return new RunnerResult
        {
            SchemaVersion = Program.ResultSchemaVersion,
            SandboxId = request.SandboxId,
            ExecutionId = request.ExecutionId,
            Status = "failed",
            Success = false,
            Argv = command.Argv,
            Cwd = cwd,
            Pid = pid,
            ExitCode = -1,
            Stdout = "",
            Stderr = "",
            DurationMs = durationMs,
            TimedOut = false,
            CleanupStatus = "killed",
            Error = "failed to assign process to job object",
            ErrorCode = Program.ErrorJobAssignFailed,
            Isolation = isolation,
            JobObject = jobObject,
            JobAssigned = false,
            JobMemoryLimitMb = jobMemoryLimitMb
        };
    }

    public static RunnerResult SetupFailed(
        RunnerRequest request,
        CommandRequest command,
        string cwd,
        long durationMs,
        string? error,
        string errorCode,
        IsolationReport isolation)
    {
        return new RunnerResult
        {
            SchemaVersion = Program.ResultSchemaVersion,
            SandboxId = request.SandboxId,
            ExecutionId = request.ExecutionId,
            Status = "failed",
            Success = false,
            Argv = command.Argv,
            Cwd = cwd,
            ExitCode = -1,
            Stdout = "",
            Stderr = "",
            DurationMs = durationMs,
            TimedOut = false,
            CleanupStatus = "not_started",
            Error = error,
            ErrorCode = errorCode,
            Isolation = isolation
        };
    }
}

internal sealed class OperationResult
{
    public bool Success { get; init; }
    public string Error { get; init; } = "";
}

internal static class IntegrityLabel
{
    public static OperationResult TrySetLowIntegrity(string path)
    {
        if (!RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
        {
            return new OperationResult { Success = false, Error = "low integrity ACL is only supported on Windows" };
        }

        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = "icacls.exe",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };
            psi.ArgumentList.Add(path);
            psi.ArgumentList.Add("/setintegritylevel");
            psi.ArgumentList.Add("(OI)(CI)L");

            using var process = Process.Start(psi);
            if (process is null)
            {
                return new OperationResult { Success = false, Error = "failed to start icacls.exe" };
            }
            var stdout = process.StandardOutput.ReadToEnd();
            var stderr = process.StandardError.ReadToEnd();
            process.WaitForExit();
            if (process.ExitCode != 0)
            {
                return new OperationResult
                {
                    Success = false,
                    Error = string.IsNullOrWhiteSpace(stderr) ? stdout : stderr
                };
            }
            return new OperationResult { Success = true };
        }
        catch (Exception ex)
        {
            return new OperationResult { Success = false, Error = ex.Message };
        }
    }
}

internal sealed class NetworkGuard : IDisposable
{
    private NetworkGuard(string? ruleName, bool applied, string? error)
    {
        RuleName = ruleName;
        Applied = applied;
        Error = error;
    }

    public string? RuleName { get; }
    public bool Applied { get; }
    public string? Error { get; }

    public static NetworkGuard TryCreate(RunnerRequest request, CommandRequest command)
    {
        if (request.Isolation?.NetworkDeny != true)
        {
            return new NetworkGuard(null, false, null);
        }
        if (!RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
        {
            return new NetworkGuard(null, false, "network deny PoC is only supported on Windows");
        }

        var programPath = ResolveExecutablePath(command.Argv[0], command.Env);
        if (string.IsNullOrWhiteSpace(programPath) || !File.Exists(programPath))
        {
            return new NetworkGuard(null, false, $"cannot resolve executable for firewall rule: {command.Argv[0]}");
        }

        var ruleName = "DevPalSandbox-" + request.SandboxId;
        var result = RunNetsh(
            "advfirewall",
            "firewall",
            "add",
            "rule",
            $"name={ruleName}",
            "dir=out",
            "action=block",
            $"program={programPath}",
            "enable=yes",
            "profile=any");
        if (!result.Success)
        {
            return new NetworkGuard(ruleName, false, result.Error);
        }
        return new NetworkGuard(ruleName, true, null);
    }

    public void Dispose()
    {
        if (Applied && !string.IsNullOrWhiteSpace(RuleName))
        {
            RunNetsh(
                "advfirewall",
                "firewall",
                "delete",
                "rule",
                $"name={RuleName}");
        }
    }

    private static OperationResult RunNetsh(params string[] args)
    {
        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = "netsh.exe",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };
            foreach (var arg in args)
            {
                psi.ArgumentList.Add(arg);
            }

            using var process = Process.Start(psi);
            if (process is null)
            {
                return new OperationResult { Success = false, Error = "failed to start netsh.exe" };
            }
            var stdout = process.StandardOutput.ReadToEnd();
            var stderr = process.StandardError.ReadToEnd();
            process.WaitForExit();
            if (process.ExitCode != 0)
            {
                return new OperationResult
                {
                    Success = false,
                    Error = string.IsNullOrWhiteSpace(stderr) ? stdout : stderr
                };
            }
            return new OperationResult { Success = true };
        }
        catch (Exception ex)
        {
            return new OperationResult { Success = false, Error = ex.Message };
        }
    }

    private static string? ResolveExecutablePath(string executable, Dictionary<string, string>? env)
    {
        if (Path.IsPathRooted(executable) && File.Exists(executable))
        {
            return Path.GetFullPath(executable);
        }
        var pathValue = "";
        if (env is not null)
        {
            foreach (var item in env)
            {
                if (string.Equals(item.Key, "PATH", StringComparison.OrdinalIgnoreCase))
                {
                    pathValue = item.Value;
                    break;
                }
            }
        }
        if (string.IsNullOrWhiteSpace(pathValue))
        {
            pathValue = Environment.GetEnvironmentVariable("PATH") ?? "";
        }
        var extensions = Path.HasExtension(executable)
            ? new[] { "" }
            : new[] { ".exe", ".cmd", ".bat", "" };
        foreach (var dir in pathValue.Split(Path.PathSeparator, StringSplitOptions.RemoveEmptyEntries))
        {
            foreach (var ext in extensions)
            {
                var candidate = Path.Combine(dir.Trim(), executable + ext);
                if (File.Exists(candidate))
                {
                    return Path.GetFullPath(candidate);
                }
            }
        }
        return null;
    }
}

internal static class LowIntegrityProcessLauncher
{
    private const int WaitObject0 = 0;
    private const int WaitTimeout = 0x00000102;
    private const uint Infinite = 0xFFFFFFFF;
    private const uint CreateNoWindow = 0x08000000;
    private const uint CreateUnicodeEnvironment = 0x00000400;
    private const uint StartfUseStdHandles = 0x00000100;
    private const uint HandleFlagInherit = 0x00000001;
    private const uint TokenAssignPrimary = 0x0001;
    private const uint TokenDuplicate = 0x0002;
    private const uint TokenImpersonate = 0x0004;
    private const uint TokenQuery = 0x0008;
    private const uint TokenAdjustPrivileges = 0x0020;
    private const uint TokenAdjustDefault = 0x0080;
    private const uint TokenAdjustSessionId = 0x0100;
    private const uint DuplicateAccess = TokenAssignPrimary | TokenDuplicate | TokenQuery | TokenAdjustDefault | TokenAdjustSessionId;
    private const uint OpenTokenAccess = TokenDuplicate | TokenQuery | TokenAdjustDefault | TokenAssignPrimary | TokenImpersonate | TokenAdjustPrivileges;
    private const uint DisableMaxPrivilege = 0x00000001;
    private const uint LuaToken = 0x00000004;
    private const uint SecurityImpersonation = 2;
    private const uint TokenPrimary = 1;
    private const int TokenIntegrityLevel = 25;
    private const uint SeGroupIntegrity = 0x00000020;

    public static async Task<RunnerResult> RunAsync(
        RunnerRequest request,
        CommandRequest command,
        JobObject? job,
        IsolationReport isolation,
        Stopwatch started)
    {
        var lowIntegrityRequested = request.Isolation?.LowIntegrity == true;
        var restrictedTokenRequested = request.Isolation?.RestrictedToken == true;
        isolation.ProcessLauncher = restrictedTokenRequested && lowIntegrityRequested
            ? "restricted_low_integrity"
            : restrictedTokenRequested
                ? "restricted_token"
                : "low_integrity";
        if (!RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
        {
            var error = "reduced token process launch is only supported on Windows";
            if (lowIntegrityRequested)
            {
                isolation.LowIntegrityError = error;
            }
            if (restrictedTokenRequested)
            {
                isolation.RestrictedTokenError = error;
            }
            started.Stop();
            return RunnerResult.SetupFailed(
                request,
                command,
                command.Cwd ?? request.WorkspaceDir,
                started.ElapsedMilliseconds,
                error,
                Program.ErrorIsolationSetupFailed,
                isolation);
        }

        IntPtr primaryToken = IntPtr.Zero;
        IntPtr processHandle = IntPtr.Zero;
        IntPtr threadHandle = IntPtr.Zero;
        IntPtr envBlock = IntPtr.Zero;
        IntPtr stdoutRead = IntPtr.Zero;
        IntPtr stdoutWrite = IntPtr.Zero;
        IntPtr stderrRead = IntPtr.Zero;
        IntPtr stderrWrite = IntPtr.Zero;
        var jobAssigned = false;
        try
        {
            primaryToken = CreateReducedPrimaryToken(
                lowIntegrityRequested,
                restrictedTokenRequested,
                isolation);
            envBlock = BuildEnvironmentBlock(command.Env);
            CreatePipePair(out stdoutRead, out stdoutWrite);
            CreatePipePair(out stderrRead, out stderrWrite);

            var startup = new STARTUPINFO
            {
                cb = Marshal.SizeOf<STARTUPINFO>(),
                dwFlags = StartfUseStdHandles,
                hStdOutput = stdoutWrite,
                hStdError = stderrWrite,
                hStdInput = IntPtr.Zero
            };
            var processInfo = new PROCESS_INFORMATION();
            var commandLine = BuildCommandLine(command.Argv);
            var cwd = string.IsNullOrWhiteSpace(command.Cwd) ? request.WorkspaceDir : command.Cwd;
            var created = CreateProcessAsUser(
                primaryToken,
                null,
                commandLine,
                IntPtr.Zero,
                IntPtr.Zero,
                true,
                CreateNoWindow | CreateUnicodeEnvironment,
                envBlock,
                cwd,
                ref startup,
                out processInfo);
            if (!created)
            {
                throw new InvalidOperationException("CreateProcessAsUser failed: " + Marshal.GetLastWin32Error());
            }

            isolation.LowIntegrityApplied = lowIntegrityRequested;
            processHandle = processInfo.hProcess;
            threadHandle = processInfo.hThread;
            CloseHandle(stdoutWrite);
            stdoutWrite = IntPtr.Zero;
            CloseHandle(stderrWrite);
            stderrWrite = IntPtr.Zero;

            if (job is not null)
            {
                jobAssigned = job.Assign(processHandle);
                if (!jobAssigned)
                {
                    TryKillProcessTree((int)processInfo.dwProcessId);
                    started.Stop();
                    return RunnerResult.JobAssignFailed(
                        request,
                        command,
                        (int)processInfo.dwProcessId,
                        cwd,
                        started.ElapsedMilliseconds,
                        job.Name,
                        job.MemoryLimitMb,
                        isolation);
                }
            }

            var stdoutTask = ReadPipeAsync(stdoutRead);
            stdoutRead = IntPtr.Zero;
            var stderrTask = ReadPipeAsync(stderrRead);
            stderrRead = IntPtr.Zero;
            var wait = WaitForSingleObject(processHandle, (uint)Math.Max(1, command.TimeoutSeconds) * 1000);
            if (wait == WaitTimeout)
            {
                TryKillProcessTree((int)processInfo.dwProcessId);
                WaitForSingleObject(processHandle, Infinite);
                started.Stop();
                return RunnerResult.Timeout(
                    request,
                    command,
                    (int)processInfo.dwProcessId,
                    started.ElapsedMilliseconds,
                    job?.Name,
                    job is null ? null : jobAssigned,
                    job?.MemoryLimitMb,
                    isolation);
            }
            if (wait != WaitObject0)
            {
                throw new InvalidOperationException("WaitForSingleObject failed: " + Marshal.GetLastWin32Error());
            }

            GetExitCodeProcess(processHandle, out var exitCode);
            started.Stop();
            return new RunnerResult
            {
                SchemaVersion = Program.ResultSchemaVersion,
                SandboxId = request.SandboxId,
                ExecutionId = request.ExecutionId,
                Status = exitCode == 0 ? "completed" : "failed",
                Success = exitCode == 0,
                Argv = command.Argv,
                Cwd = cwd,
                Pid = (int)processInfo.dwProcessId,
                ExitCode = (int)exitCode,
                Stdout = await stdoutTask,
                Stderr = await stderrTask,
                DurationMs = started.ElapsedMilliseconds,
                TimedOut = false,
                CleanupStatus = "clean",
                Isolation = isolation,
                JobObject = job?.Name,
                JobAssigned = job is null ? null : jobAssigned,
                JobMemoryLimitMb = job?.MemoryLimitMb
            };
        }
        catch (Exception ex)
        {
            if (lowIntegrityRequested && string.IsNullOrWhiteSpace(isolation.LowIntegrityError))
            {
                isolation.LowIntegrityError = ex.Message;
            }
            if (restrictedTokenRequested && string.IsNullOrWhiteSpace(isolation.RestrictedTokenError))
            {
                isolation.RestrictedTokenError = ex.Message;
            }
            started.Stop();
            return new RunnerResult
            {
                SchemaVersion = Program.ResultSchemaVersion,
                SandboxId = request.SandboxId,
                ExecutionId = request.ExecutionId,
                Status = "failed",
                Success = false,
                Argv = command.Argv,
                Cwd = command.Cwd ?? request.WorkspaceDir,
                ExitCode = -1,
                Stdout = "",
                Stderr = "",
                DurationMs = started.ElapsedMilliseconds,
                TimedOut = false,
                CleanupStatus = "best_effort",
                Error = ex.Message,
                ErrorCode = Program.ErrorIsolationSetupFailed,
                Isolation = isolation,
                JobObject = job?.Name,
                JobAssigned = job is null ? null : jobAssigned,
                JobMemoryLimitMb = job?.MemoryLimitMb
            };
        }
        finally
        {
            if (stdoutRead != IntPtr.Zero) CloseHandle(stdoutRead);
            if (stdoutWrite != IntPtr.Zero) CloseHandle(stdoutWrite);
            if (stderrRead != IntPtr.Zero) CloseHandle(stderrRead);
            if (stderrWrite != IntPtr.Zero) CloseHandle(stderrWrite);
            if (threadHandle != IntPtr.Zero) CloseHandle(threadHandle);
            if (processHandle != IntPtr.Zero) CloseHandle(processHandle);
            if (envBlock != IntPtr.Zero) Marshal.FreeHGlobal(envBlock);
            if (primaryToken != IntPtr.Zero) CloseHandle(primaryToken);
        }
    }

    private static IntPtr CreateReducedPrimaryToken(
        bool lowIntegrityRequested,
        bool restrictedTokenRequested,
        IsolationReport isolation)
    {
        if (!OpenProcessToken(GetCurrentProcess(), OpenTokenAccess, out var token))
        {
            throw new InvalidOperationException("OpenProcessToken failed: " + Marshal.GetLastWin32Error());
        }
        IntPtr restrictedToken = IntPtr.Zero;
        try
        {
            var sourceToken = token;
            if (restrictedTokenRequested)
            {
                restrictedToken = CreateRestrictedTokenHandle(token, isolation);
                isolation.RestrictedTokenApplied = true;
                sourceToken = restrictedToken;
            }
            if (!DuplicateTokenEx(
                    sourceToken,
                    DuplicateAccess,
                    IntPtr.Zero,
                    SecurityImpersonation,
                    TokenPrimary,
                    out var primaryToken))
            {
                throw new InvalidOperationException("DuplicateTokenEx failed: " + Marshal.GetLastWin32Error());
            }

            if (!lowIntegrityRequested)
            {
                return primaryToken;
            }
            if (!ConvertStringSidToSid("S-1-16-4096", out var lowSid))
            {
                CloseHandle(primaryToken);
                isolation.LowIntegrityError = "ConvertStringSidToSid failed: " + Marshal.GetLastWin32Error();
                throw new InvalidOperationException("ConvertStringSidToSid failed: " + Marshal.GetLastWin32Error());
            }
            try
            {
                var label = new TOKEN_MANDATORY_LABEL
                {
                    Label = new SID_AND_ATTRIBUTES
                    {
                        Sid = lowSid,
                        Attributes = SeGroupIntegrity
                    }
                };
                var labelSize = Marshal.SizeOf<TOKEN_MANDATORY_LABEL>();
                var sidSize = GetLengthSid(lowSid);
                var ptr = Marshal.AllocHGlobal(labelSize);
                try
                {
                    Marshal.StructureToPtr(label, ptr, false);
                    if (!SetTokenInformation(
                            primaryToken,
                            TokenIntegrityLevel,
                            ptr,
                            (uint)(labelSize + sidSize)))
                    {
                        CloseHandle(primaryToken);
                        isolation.LowIntegrityError = "SetTokenInformation failed: " + Marshal.GetLastWin32Error();
                        throw new InvalidOperationException("SetTokenInformation failed: " + Marshal.GetLastWin32Error());
                    }
                    isolation.LowIntegrityApplied = true;
                }
                finally
                {
                    Marshal.FreeHGlobal(ptr);
                }
            }
            finally
            {
                LocalFree(lowSid);
            }

            return primaryToken;
        }
        finally
        {
            if (restrictedToken != IntPtr.Zero)
            {
                CloseHandle(restrictedToken);
            }
            CloseHandle(token);
        }
    }

    private static IntPtr CreateRestrictedTokenHandle(IntPtr token, IsolationReport isolation)
    {
        var sidPointers = new List<IntPtr>();
        var sidArrayPtr = IntPtr.Zero;
        try
        {
            foreach (var sid in new[] { "S-1-5-32-544", "S-1-5-32-547" })
            {
                if (ConvertStringSidToSid(sid, out var sidPtr))
                {
                    sidPointers.Add(sidPtr);
                }
            }
            var sidAttributes = sidPointers
                .Select(ptr => new SID_AND_ATTRIBUTES { Sid = ptr, Attributes = 0 })
                .ToArray();
            var sidStructSize = Marshal.SizeOf<SID_AND_ATTRIBUTES>();
            if (sidAttributes.Length > 0)
            {
                sidArrayPtr = Marshal.AllocHGlobal(sidStructSize * sidAttributes.Length);
                for (var i = 0; i < sidAttributes.Length; i++)
                {
                    Marshal.StructureToPtr(
                        sidAttributes[i],
                        IntPtr.Add(sidArrayPtr, i * sidStructSize),
                        false);
                }
            }
            if (TryCreateRestrictedToken(
                    token,
                    DisableMaxPrivilege,
                    (uint)sidAttributes.Length,
                    sidArrayPtr,
                    out var restrictedToken))
            {
                return restrictedToken;
            }

            var sidError = Marshal.GetLastWin32Error();
            if (sidAttributes.Length > 0 && TryCreateRestrictedToken(
                    token,
                    DisableMaxPrivilege,
                    0,
                    IntPtr.Zero,
                    out restrictedToken))
            {
                isolation.RestrictedTokenError = "SID disable fallback: CreateRestrictedToken failed: " + sidError;
                return restrictedToken;
            }
            var privilegeError = Marshal.GetLastWin32Error();
            if (TryCreateRestrictedToken(token, LuaToken, 0, IntPtr.Zero, out restrictedToken))
            {
                isolation.RestrictedTokenError = "LUA token fallback after DISABLE_MAX_PRIVILEGE failed: " + privilegeError;
                return restrictedToken;
            }
            throw new InvalidOperationException("CreateRestrictedToken failed: " + Marshal.GetLastWin32Error());
        }
        finally
        {
            if (sidArrayPtr != IntPtr.Zero)
            {
                Marshal.FreeHGlobal(sidArrayPtr);
            }
            foreach (var sidPtr in sidPointers)
            {
                LocalFree(sidPtr);
            }
        }
    }

    private static bool TryCreateRestrictedToken(
        IntPtr token,
        uint flags,
        uint disableSidCount,
        IntPtr sidsToDisable,
        out IntPtr restrictedToken)
    {
        return CreateRestrictedToken(
            token,
            flags,
            disableSidCount,
            sidsToDisable,
            0,
            IntPtr.Zero,
            0,
            IntPtr.Zero,
            out restrictedToken);
    }

    private static void CreatePipePair(out IntPtr readPipe, out IntPtr writePipe)
    {
        var sa = new SECURITY_ATTRIBUTES
        {
            nLength = Marshal.SizeOf<SECURITY_ATTRIBUTES>(),
            bInheritHandle = true
        };
        if (!CreatePipe(out readPipe, out writePipe, ref sa, 0))
        {
            throw new InvalidOperationException("CreatePipe failed: " + Marshal.GetLastWin32Error());
        }
        if (!SetHandleInformation(readPipe, HandleFlagInherit, 0))
        {
            throw new InvalidOperationException("SetHandleInformation failed: " + Marshal.GetLastWin32Error());
        }
    }

    private static Task<string> ReadPipeAsync(IntPtr readHandle)
    {
        return Task.Run(() =>
        {
            using var safeHandle = new SafeFileHandle(readHandle, ownsHandle: true);
            using var stream = new FileStream(safeHandle, FileAccess.Read, 4096, isAsync: false);
            using var reader = new StreamReader(stream, Encoding.UTF8);
            return reader.ReadToEnd();
        });
    }

    private static IntPtr BuildEnvironmentBlock(Dictionary<string, string>? env)
    {
        var entries = (env ?? new Dictionary<string, string>())
            .OrderBy(item => item.Key, StringComparer.OrdinalIgnoreCase)
            .Select(item => item.Key + "=" + item.Value);
        var block = string.Join('\0', entries) + "\0\0";
        return Marshal.StringToHGlobalUni(block);
    }

    private static string BuildCommandLine(IReadOnlyList<string> argv)
    {
        return string.Join(" ", argv.Select(QuoteArg));
    }

    private static string QuoteArg(string arg)
    {
        if (arg.Length == 0)
        {
            return "\"\"";
        }
        if (!arg.Any(char.IsWhiteSpace) && !arg.Contains('"'))
        {
            return arg;
        }
        var builder = new StringBuilder();
        builder.Append('"');
        var backslashes = 0;
        foreach (var ch in arg)
        {
            if (ch == '\\')
            {
                backslashes++;
                continue;
            }
            if (ch == '"')
            {
                builder.Append('\\', backslashes * 2 + 1);
                builder.Append('"');
                backslashes = 0;
                continue;
            }
            builder.Append('\\', backslashes);
            backslashes = 0;
            builder.Append(ch);
        }
        builder.Append('\\', backslashes * 2);
        builder.Append('"');
        return builder.ToString();
    }

    private static void TryKillProcessTree(int pid)
    {
        try
        {
            Process.GetProcessById(pid).Kill(entireProcessTree: true);
        }
        catch
        {
            // Best effort cleanup; Job Object close is the second guard when available.
        }
    }

    [DllImport("advapi32.dll", SetLastError = true)]
    private static extern bool OpenProcessToken(IntPtr processHandle, uint desiredAccess, out IntPtr tokenHandle);

    [DllImport("kernel32.dll")]
    private static extern IntPtr GetCurrentProcess();

    [DllImport("advapi32.dll", SetLastError = true)]
    private static extern bool DuplicateTokenEx(
        IntPtr existingTokenHandle,
        uint desiredAccess,
        IntPtr tokenAttributes,
        uint impersonationLevel,
        uint tokenType,
        out IntPtr duplicateTokenHandle);

    [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    private static extern bool ConvertStringSidToSid(string stringSid, out IntPtr sid);

    [DllImport("advapi32.dll", SetLastError = true)]
    private static extern bool CreateRestrictedToken(
        IntPtr existingTokenHandle,
        uint flags,
        uint disableSidCount,
        IntPtr sidsToDisable,
        uint deletePrivilegeCount,
        IntPtr privilegesToDelete,
        uint restrictedSidCount,
        IntPtr sidsToRestrict,
        out IntPtr newTokenHandle);

    [DllImport("advapi32.dll", SetLastError = true)]
    private static extern bool SetTokenInformation(
        IntPtr tokenHandle,
        int tokenInformationClass,
        IntPtr tokenInformation,
        uint tokenInformationLength);

    [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    private static extern bool CreateProcessAsUser(
        IntPtr token,
        string? applicationName,
        string commandLine,
        IntPtr processAttributes,
        IntPtr threadAttributes,
        bool inheritHandles,
        uint creationFlags,
        IntPtr environment,
        string currentDirectory,
        ref STARTUPINFO startupInfo,
        out PROCESS_INFORMATION processInformation);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool CreatePipe(
        out IntPtr readPipe,
        out IntPtr writePipe,
        ref SECURITY_ATTRIBUTES pipeAttributes,
        uint size);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool SetHandleInformation(IntPtr handle, uint mask, uint flags);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern uint WaitForSingleObject(IntPtr handle, uint milliseconds);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool GetExitCodeProcess(IntPtr process, out uint exitCode);

    [DllImport("kernel32.dll")]
    private static extern IntPtr LocalFree(IntPtr hMem);

    [DllImport("advapi32.dll", SetLastError = true)]
    private static extern uint GetLengthSid(IntPtr sid);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool CloseHandle(IntPtr handle);

    [StructLayout(LayoutKind.Sequential)]
    private struct SECURITY_ATTRIBUTES
    {
        public int nLength;
        public IntPtr lpSecurityDescriptor;
        [MarshalAs(UnmanagedType.Bool)]
        public bool bInheritHandle;
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct STARTUPINFO
    {
        public int cb;
        public string? lpReserved;
        public string? lpDesktop;
        public string? lpTitle;
        public uint dwX;
        public uint dwY;
        public uint dwXSize;
        public uint dwYSize;
        public uint dwXCountChars;
        public uint dwYCountChars;
        public uint dwFillAttribute;
        public uint dwFlags;
        public ushort wShowWindow;
        public ushort cbReserved2;
        public IntPtr lpReserved2;
        public IntPtr hStdInput;
        public IntPtr hStdOutput;
        public IntPtr hStdError;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct PROCESS_INFORMATION
    {
        public IntPtr hProcess;
        public IntPtr hThread;
        public uint dwProcessId;
        public uint dwThreadId;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct SID_AND_ATTRIBUTES
    {
        public IntPtr Sid;
        public uint Attributes;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct TOKEN_MANDATORY_LABEL
    {
        public SID_AND_ATTRIBUTES Label;
    }
}

internal sealed class JobObject : IDisposable
{
    private const uint JobObjectExtendedLimitInformation = 9;
    private const uint JobObjectLimitKillOnJobClose = 0x00002000;
    private const uint JobObjectLimitActiveProcess = 0x00000008;
    private const uint JobObjectLimitJobMemory = 0x00000200;

    private readonly IntPtr _handle;

    private JobObject(IntPtr handle, string name, int? memoryLimitMb)
    {
        _handle = handle;
        Name = name;
        MemoryLimitMb = memoryLimitMb;
    }

    public string Name { get; }
    public int? MemoryLimitMb { get; }

    public static JobObject? TryCreate(string sandboxId, int? maxProcesses, int? maxMemoryMb)
    {
        if (!RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
        {
            return null;
        }

        var name = "DevPalSandbox-" + sandboxId;
        var handle = CreateJobObject(IntPtr.Zero, name);
        if (handle == IntPtr.Zero)
        {
            return null;
        }

        var info = new JOBOBJECT_EXTENDED_LIMIT_INFORMATION();
        info.BasicLimitInformation.LimitFlags = JobObjectLimitKillOnJobClose;
        if (maxProcesses.HasValue && maxProcesses.Value > 0)
        {
            info.BasicLimitInformation.LimitFlags |= JobObjectLimitActiveProcess;
            info.BasicLimitInformation.ActiveProcessLimit = (uint)maxProcesses.Value;
        }
        int? memoryLimitMb = null;
        if (maxMemoryMb.HasValue && maxMemoryMb.Value > 0)
        {
            memoryLimitMb = maxMemoryMb.Value;
            info.BasicLimitInformation.LimitFlags |= JobObjectLimitJobMemory;
            var bytes = checked((ulong)maxMemoryMb.Value * 1024UL * 1024UL);
            info.JobMemoryLimit = (UIntPtr)bytes;
        }

        var length = Marshal.SizeOf<JOBOBJECT_EXTENDED_LIMIT_INFORMATION>();
        var ptr = Marshal.AllocHGlobal(length);
        try
        {
            Marshal.StructureToPtr(info, ptr, false);
            if (!SetInformationJobObject(handle, JobObjectExtendedLimitInformation, ptr, (uint)length))
            {
                CloseHandle(handle);
                return null;
            }
        }
        finally
        {
            Marshal.FreeHGlobal(ptr);
        }

        return new JobObject(handle, name, memoryLimitMb);
    }

    public bool Assign(Process process)
    {
        return Assign(process.Handle);
    }

    public bool Assign(IntPtr processHandle)
    {
        return _handle != IntPtr.Zero && AssignProcessToJobObject(_handle, processHandle);
    }

    public void Dispose()
    {
        if (_handle != IntPtr.Zero)
        {
            CloseHandle(_handle);
        }
    }

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode)]
    private static extern IntPtr CreateJobObject(IntPtr lpJobAttributes, string? lpName);

    [DllImport("kernel32.dll")]
    private static extern bool SetInformationJobObject(
        IntPtr hJob,
        uint jobObjectInfoClass,
        IntPtr lpJobObjectInfo,
        uint cbJobObjectInfoLength);

    [DllImport("kernel32.dll")]
    private static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);

    [DllImport("kernel32.dll")]
    private static extern bool CloseHandle(IntPtr hObject);

    [StructLayout(LayoutKind.Sequential)]
    private struct JOBOBJECT_BASIC_LIMIT_INFORMATION
    {
        public long PerProcessUserTimeLimit;
        public long PerJobUserTimeLimit;
        public uint LimitFlags;
        public UIntPtr MinimumWorkingSetSize;
        public UIntPtr MaximumWorkingSetSize;
        public uint ActiveProcessLimit;
        public UIntPtr Affinity;
        public uint PriorityClass;
        public uint SchedulingClass;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct IO_COUNTERS
    {
        public ulong ReadOperationCount;
        public ulong WriteOperationCount;
        public ulong OtherOperationCount;
        public ulong ReadTransferCount;
        public ulong WriteTransferCount;
        public ulong OtherTransferCount;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct JOBOBJECT_EXTENDED_LIMIT_INFORMATION
    {
        public JOBOBJECT_BASIC_LIMIT_INFORMATION BasicLimitInformation;
        public IO_COUNTERS IoInfo;
        public UIntPtr ProcessMemoryLimit;
        public UIntPtr JobMemoryLimit;
        public UIntPtr PeakProcessMemoryUsed;
        public UIntPtr PeakJobMemoryUsed;
    }
}
