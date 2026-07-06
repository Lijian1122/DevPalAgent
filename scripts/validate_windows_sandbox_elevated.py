# -*- coding: utf-8 -*-
"""Run elevated Windows sandbox smoke checks.

This script validates the real DevPal Windows process backend path:

Python wrapper -> C# runner -> runner_result.json -> manifest.v2.json.

It is intentionally separate from the normal pytest suite because ACL hardening
and firewall rules are Windows-specific and usually require an elevated shell.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import socket
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from devpal.core.multi_agent import CommandSpec  # noqa: E402
from devpal.core.sandbox import SandboxRequest  # noqa: E402
from devpal.core.sandbox.backends import WindowsProcessSandboxBackend  # noqa: E402


def is_windows() -> bool:
    return os.name == "nt"


def is_admin() -> bool:
    if not is_windows():
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def yes_no(value: Any) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return ""


def relpath(path_value: Any, root: Path) -> str:
    if not path_value:
        return ""
    path = Path(str(path_value))
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return str(path_value)


def reset_medium_integrity(path: Path) -> str:
    if not is_windows():
        return "skipped: non-Windows"
    try:
        completed = subprocess.run(
            ["icacls.exe", str(path), "/setintegritylevel", "(OI)(CI)M"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
        )
        output = (completed.stderr or completed.stdout or "").strip()
        return "ok" if completed.returncode == 0 else f"failed: {output}"
    except Exception as exc:
        return f"failed: {exc}"


def run_backend_case(
    *,
    project_dir: Path,
    task_name: str,
    code: str,
    isolation_features: Dict[str, bool],
    timeout_seconds: int,
    runner_path: str = "",
    runner_args: List[str] | None = None,
    max_memory_mb: int | None = None,
) -> Dict[str, Any]:
    request = SandboxRequest.from_legacy(
        project_dir=project_dir,
        task_id=f"elevated:{task_name}",
        phase_number=10,
        role="validation",
        sandbox_level="staging",
        timeout_seconds=timeout_seconds,
    )
    request.policy.max_processes = 4
    if max_memory_mb is not None:
        request.policy.max_memory_mb = max_memory_mb
    request.policy.metadata["isolation_features"] = dict(isolation_features)
    backend = WindowsProcessSandboxBackend(
        runner_path=runner_path or None,
        runner_args=list(runner_args or []),
        runner_timeout_grace_seconds=5,
    )
    session = backend.create_session(request)
    command = CommandSpec(
        argv=["python", "-c", code],
        cwd=project_dir,
        timeout_seconds=timeout_seconds,
    )
    result = session.execute_command(command)
    runner_result = read_json(session.runner_result_path)
    manifest_v2 = read_json(session.manifest_v2_path)
    return {
        "task_name": task_name,
        "success": result.returncode == 0 and not result.error and not result.timed_out,
        "returncode": result.returncode,
        "timed_out": result.timed_out,
        "error": result.error,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "sandbox_id": session.sandbox_id,
        "sandbox_dir": str(session.sandbox_dir),
        "runner_request_path": str(session.runner_request_path),
        "runner_result_path": str(session.runner_result_path),
        "manifest_v2_path": str(session.manifest_v2_path),
        "runner_status": runner_result.get("status", ""),
        "runner_error_code": runner_result.get("error_code", ""),
        "isolation": runner_result.get("isolation", {}),
        "job_assigned": runner_result.get("job_assigned"),
        "job_memory_limit_mb": runner_result.get("job_memory_limit_mb"),
        "manifest_status": manifest_v2.get("status", ""),
    }


def local_tcp_probe_code(port: int) -> str:
    return (
        "import socket; "
        f"s=socket.create_connection(('127.0.0.1',{port}),2); "
        "s.sendall(b'devpal'); "
        "s.close(); "
        "print('connected')"
    )


def start_local_tcp_server() -> Tuple[int, Dict[str, Any], threading.Thread]:
    state: Dict[str, Any] = {"accepted": False, "error": ""}
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = int(server.getsockname()[1])
    server.settimeout(8)

    def serve() -> None:
        try:
            conn, _addr = server.accept()
            with conn:
                conn.recv(32)
                state["accepted"] = True
        except Exception as exc:
            state["error"] = str(exc)
        finally:
            server.close()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    return port, state, thread


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate DevPal Windows sandbox isolation features from an elevated shell."
    )
    parser.add_argument(
        "--project-dir",
        default=str(REPO_ROOT / ".tmp" / "sandbox_elevated_validation" / timestamp()),
        help="Temporary project directory used for validation.",
    )
    parser.add_argument("--runner-path", default="", help="Optional runner executable path.")
    parser.add_argument(
        "--runner-arg",
        action="append",
        default=[],
        help="Extra argument passed before runner_request.json. Repeatable.",
    )
    parser.add_argument(
        "--include-network",
        action="store_true",
        help="Also validate the temporary Windows Firewall network deny PoC.",
    )
    parser.add_argument(
        "--include-memory",
        action="store_true",
        help="Also validate Job Object memory limit with an expected failing allocation.",
    )
    parser.add_argument(
        "--allow-non-admin",
        action="store_true",
        help="Run admin-sensitive checks even when the current shell is not elevated.",
    )
    parser.add_argument(
        "--report-path",
        default="",
        help="Optional JSON report path. Defaults to <project-dir>/.spec/sandbox_elevated_validation_report.json.",
    )
    parser.add_argument(
        "--markdown-report-path",
        default="",
        help="Optional Markdown report path. Defaults to <project-dir>/.spec/sandbox_elevated_validation_report.md.",
    )
    return parser


def build_markdown_report(report: Dict[str, Any], *, project_dir: Path, json_report_path: Path) -> str:
    lines = [
        "# DevPal Windows Sandbox Elevated Validation",
        "",
        f"- Project dir: `{project_dir}`",
        f"- JSON report: `{relpath(json_report_path, project_dir)}`",
        f"- Windows: {yes_no(report.get('is_windows'))}",
        f"- Admin shell: {yes_no(report.get('is_admin'))}",
        "",
        "## Cases",
        "",
        "| Case | Success | Low Integrity | Restricted Token | Workspace ACL | Network Deny | Launcher | Job | Memory MB | Error Code | Runner Result | Manifest v2 |",
        "|------|---------|---------------|------------------|---------------|--------------|----------|-----|-----------|------------|---------------|-------------|",
    ]
    for case in report.get("cases", []):
        isolation = case.get("isolation", {}) if isinstance(case.get("isolation"), dict) else {}
        lines.append(
            "| {case} | {success} | {low} | {restricted} | {acl} | {network} | `{launcher}` | {job} | `{memory}` | `{error}` | `{runner}` | `{manifest}` |".format(
                case=case.get("task_name", ""),
                success=yes_no(case.get("success")),
                low=yes_no(isolation.get("low_integrity_applied")),
                restricted=yes_no(isolation.get("restricted_token_applied")),
                acl=yes_no(isolation.get("workspace_acl_hardened")),
                network=yes_no(isolation.get("network_deny_applied")),
                launcher=isolation.get("process_launcher", ""),
                job=yes_no(case.get("job_assigned")),
                memory=case.get("job_memory_limit_mb", "") or "",
                error=case.get("runner_error_code", "") or "",
                runner=relpath(case.get("runner_result_path"), project_dir),
                manifest=relpath(case.get("manifest_v2_path"), project_dir),
            )
        )
    lines.append("")
    notes = list(report.get("notes", []) or [])
    if notes:
        lines.extend(["## Notes", ""])
        for note in notes:
            lines.append(f"- {note}")
        lines.append("")
    lines.extend([
        "## Interpretation",
        "",
        "- `Low Integrity` proves the runner can launch the child process with a lower Windows integrity level.",
        "- `Restricted Token` proves the runner can remove most privileges and disable high-risk built-in SIDs before launch.",
        "- `Workspace ACL` should be validated from an elevated shell because `icacls /setintegritylevel` often requires permissions.",
        "- `Network Deny` is a Windows Firewall PoC and should be treated as evidence for the current MVP, not as a full WFP/AppContainer boundary.",
        "",
    ])
    return "\n".join(lines)


def main(argv: List[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    project_dir = Path(args.project_dir).resolve()
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "README.md").write_text("DevPal sandbox elevated validation\n", encoding="utf-8")

    admin = is_admin()
    report: Dict[str, Any] = {
        "project_dir": str(project_dir),
        "is_windows": is_windows(),
        "is_admin": admin,
        "runner_path": args.runner_path,
        "runner_args": list(args.runner_arg),
        "cases": [],
        "notes": [],
    }

    if not is_windows():
        report["notes"].append("Skipped: Windows sandbox runner isolation checks require Windows.")
    else:
        report["cases"].append(
            run_backend_case(
                project_dir=project_dir,
                task_name="low_integrity",
                code="print('low integrity smoke')",
                isolation_features={
                    "low_integrity": True,
                    "harden_workspace_acl": False,
                    "network_deny": False,
                    "restricted_token": False,
                },
                timeout_seconds=20,
                runner_path=args.runner_path,
                runner_args=args.runner_arg,
            )
        )
        report["cases"].append(
            run_backend_case(
                project_dir=project_dir,
                task_name="restricted_low_integrity",
                code="print('restricted low integrity smoke')",
                isolation_features={
                    "low_integrity": True,
                    "harden_workspace_acl": False,
                    "network_deny": False,
                    "restricted_token": True,
                },
                timeout_seconds=20,
                runner_path=args.runner_path,
                runner_args=args.runner_arg,
            )
        )

        if admin or args.allow_non_admin:
            acl_case = run_backend_case(
                project_dir=project_dir,
                task_name="low_integrity_acl_write",
                code=(
                    "from pathlib import Path; "
                    "Path('acl_write_probe.txt').write_text('ok', encoding='utf-8'); "
                    "print('wrote acl probe')"
                ),
                isolation_features={
                    "low_integrity": True,
                    "harden_workspace_acl": True,
                    "network_deny": False,
                    "restricted_token": True,
                },
                timeout_seconds=20,
                runner_path=args.runner_path,
                runner_args=args.runner_arg,
            )
            acl_case["acl_probe_exists"] = (project_dir / "acl_write_probe.txt").exists()
            acl_case["integrity_reset"] = reset_medium_integrity(project_dir)
            report["cases"].append(acl_case)
        else:
            report["notes"].append("Skipped ACL hardening smoke: run from an elevated shell or pass --allow-non-admin.")

        if args.include_network:
            if admin or args.allow_non_admin:
                port, server_state, server_thread = start_local_tcp_server()
                network_case = run_backend_case(
                    project_dir=project_dir,
                    task_name="network_deny_local_tcp",
                    code=local_tcp_probe_code(port),
                    isolation_features={
                        "low_integrity": False,
                        "harden_workspace_acl": False,
                        "network_deny": True,
                        "restricted_token": False,
                    },
                    timeout_seconds=20,
                    runner_path=args.runner_path,
                    runner_args=args.runner_arg,
                )
                server_thread.join(timeout=1)
                network_case["local_server_accepted_connection"] = bool(server_state.get("accepted"))
                network_case["local_server_error"] = str(server_state.get("error", ""))
                network_case["expected_command_failure"] = network_case["returncode"] != 0
                report["cases"].append(network_case)
            else:
                report["notes"].append("Skipped network deny smoke: run from an elevated shell or pass --allow-non-admin.")

        if args.include_memory:
            memory_case = run_backend_case(
                project_dir=project_dir,
                task_name="job_memory_limit",
                code=(
                    "blocks=[]\n"
                    "for _ in range(128):\n"
                    "    blocks.append(bytearray(1024 * 1024))\n"
                    "print('allocated')\n"
                ),
                isolation_features={
                    "low_integrity": False,
                    "harden_workspace_acl": False,
                    "network_deny": False,
                    "restricted_token": False,
                },
                timeout_seconds=20,
                runner_path=args.runner_path,
                runner_args=args.runner_arg,
                max_memory_mb=32,
            )
            memory_case["expected_command_failure"] = memory_case["returncode"] != 0
            report["cases"].append(memory_case)

    report_path = Path(args.report_path).resolve() if args.report_path else project_dir / ".spec" / "sandbox_elevated_validation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path = (
        Path(args.markdown_report_path).resolve()
        if args.markdown_report_path
        else project_dir / ".spec" / "sandbox_elevated_validation_report.md"
    )
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(
        build_markdown_report(report, project_dir=project_dir, json_report_path=report_path),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\nReport: {report_path}")
    print(f"Markdown: {markdown_path}")

    failed_cases = [
        case for case in report["cases"]
        if case.get("task_name") not in {"network_deny_local_tcp", "job_memory_limit"}
        and not case.get("success")
    ]
    failed_network = [
        case for case in report["cases"]
        if case.get("task_name") == "network_deny_local_tcp"
        and not (
            case.get("isolation", {}).get("network_deny_applied") is True
            and case.get("expected_command_failure") is True
        )
    ]
    failed_memory = [
        case for case in report["cases"]
        if case.get("task_name") == "job_memory_limit"
        and not (
            case.get("job_memory_limit_mb") == 32
            and case.get("expected_command_failure") is True
        )
    ]
    return 1 if failed_cases or failed_network or failed_memory else 0


if __name__ == "__main__":
    raise SystemExit(main())
