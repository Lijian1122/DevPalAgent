"""Interrupt OpenSpec right after Phase 2 and stop. No auto resume."""

from pathlib import Path
import json
import os
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT / "cpp_simple_login"
CHECKPOINT_FILE = PROJECT_DIR / ".spec" / "checkpoint.json"
ARCHIVE_DIR = PROJECT_DIR / ".spec" / "checkpoints"
PHASE2_DONE_MARKER = "Phase 2  ("


def _safe_write(line: str) -> None:
    try:
        sys.stdout.write(line)
    except UnicodeEncodeError:
        sys.stdout.write(line.encode("ascii", "replace").decode("ascii"))
    sys.stdout.flush()


def _start_workflow():
    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()

    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

    return subprocess.Popen(
        [sys.executable, "-u", "run_ai_flow.py", "-r", "requirements/simple_login.md"],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
        creationflags=creationflags,
    )


def _wait_for_phase2_done(process):
    print("[sim] waiting for Phase 2 to finish ...", flush=True)
    while True:
        line = process.stdout.readline()
        if not line:
            return False
        _safe_write(line)
        if PHASE2_DONE_MARKER in line:
            return True


def _terminate(process):
    print("[sim] Phase 2 finished, sending interrupt ...", flush=True)
    if os.name == "nt":
        process.send_signal(signal.CTRL_BREAK_EVENT)
    else:
        process.terminate()

    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _show_checkpoint():
    print("[sim] checkpoint after interrupt:", CHECKPOINT_FILE.exists(), flush=True)
    if CHECKPOINT_FILE.exists():
        size = CHECKPOINT_FILE.stat().st_size
        print(f"[sim]   path: {CHECKPOINT_FILE}", flush=True)
        print(f"[sim]   size: {size} bytes", flush=True)
        try:
            data = json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[sim]   parse error: {exc}", flush=True)
            return
        print(f"[sim]   schema_version: {data.get('schema_version')}", flush=True)
        print(f"[sim]   requirements_file: {data.get('requirements_file')}", flush=True)
        print(f"[sim]   project_dir: {data.get('project_dir')}", flush=True)
        print(f"[sim]   last_phase: {data.get('last_phase')}", flush=True)
        print(f"[sim]   last_success: {data.get('last_success')}", flush=True)
        print(f"[sim]   completed_phases: {data.get('completed_phases')}", flush=True)
    if ARCHIVE_DIR.exists():
        archives = sorted(ARCHIVE_DIR.glob("*.json"))
        print(f"[sim] archive directory: {ARCHIVE_DIR}", flush=True)
        for path in archives[-5:]:
            print(f"[sim]   archive: {path.name}", flush=True)


def main():
    process = _start_workflow()
    try:
        reached = _wait_for_phase2_done(process)
        if not reached:
            print("[sim] workflow finished before Phase 2 completed", flush=True)
            return process.returncode or 0
        time.sleep(1)
        _terminate(process)
    finally:
        if process.poll() is None:
            process.kill()

    _show_checkpoint()
    print("[sim] no auto resume; inspect the file then run:", flush=True)
    print("[sim]   python run_ai_flow.py -r requirements/simple_login.md --resume", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
