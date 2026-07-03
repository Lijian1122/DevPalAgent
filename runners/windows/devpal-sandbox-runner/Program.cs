using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace DevPal.SandboxRunner;

internal static class Program
{
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
        using var job = JobObject.TryCreate(request.SandboxId, request.Policy?.MaxProcesses);
        var jobAssigned = false;

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

        try
        {
            process.Start();
            jobAssigned = job?.Assign(process) ?? false;

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
                    jobAssigned);
            }

            started.Stop();
            return new RunnerResult
            {
                SchemaVersion = "devpal.sandbox.runner_result.v1",
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
                JobObject = job?.Name,
                JobAssigned = job is null ? null : jobAssigned
            };
        }
        catch (Exception ex)
        {
            started.Stop();
            return new RunnerResult
            {
                SchemaVersion = "devpal.sandbox.runner_result.v1",
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
                JobObject = job?.Name,
                JobAssigned = job is null ? null : jobAssigned
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
    public string? JobObject { get; set; }
    public bool? JobAssigned { get; set; }

    public static RunnerResult Timeout(
        RunnerRequest request,
        CommandRequest command,
        int pid,
        long durationMs,
        string? jobObject,
        bool? jobAssigned)
    {
        return new RunnerResult
        {
            SchemaVersion = "devpal.sandbox.runner_result.v1",
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
            JobObject = jobObject,
            JobAssigned = jobAssigned
        };
    }
}

internal sealed class JobObject : IDisposable
{
    private const uint JobObjectExtendedLimitInformation = 9;
    private const uint JobObjectLimitKillOnJobClose = 0x00002000;
    private const uint JobObjectLimitActiveProcess = 0x00000008;

    private readonly IntPtr _handle;

    private JobObject(IntPtr handle, string name)
    {
        _handle = handle;
        Name = name;
    }

    public string Name { get; }

    public static JobObject? TryCreate(string sandboxId, int? maxProcesses)
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

        var length = Marshal.SizeOf<JOBOBJECT_EXTENDED_LIMIT_INFORMATION>();
        var ptr = Marshal.AllocHGlobal(length);
        try
        {
            Marshal.StructureToPtr(info, ptr, false);
            SetInformationJobObject(handle, JobObjectExtendedLimitInformation, ptr, (uint)length);
        }
        finally
        {
            Marshal.FreeHGlobal(ptr);
        }

        return new JobObject(handle, name);
    }

    public bool Assign(Process process)
    {
        if (_handle != IntPtr.Zero)
        {
            return AssignProcessToJobObject(_handle, process.Handle);
        }
        return false;
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
