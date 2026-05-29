# -*- coding: utf-8 -*-
"""
OpenSpec Phase  -

"""

import json
import signal
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Dict

from ...config import get_config
from ..schema.eventbus_integration import EventBusIntegration
from .base import PhaseResult, infer_openspec_project_name, validate_phase_success

#
PHASE_TIMEOUTS = {
    1: 30,  # Phase 1:
    2: 10,  # Phase 2:
    3: 120,  # Phase 3: AI
    4: 180,  # Phase 4: AI
    5: 30,  # Phase 5:
    6: 10,  # Phase 6:  CMakeLists
    7: 10,  # Phase 7:
    8: 10,  # Phase 8:  README
    9: 60,  # Phase 9:
    10: 600,  # Phase 10:  +  + AI  (10)
    11: 30,  # Phase 11:
}

#
RETRY_CONFIG = {
    3: 2,  # Phase 3: AI  -  2
    4: 2,  # Phase 4: AI  -  2
    10: 1,  # Phase 10:  -  1
}

#
CRITICAL_PHASES = [1, 2, 3, 4, 10]


class TimeoutError(Exception):
    """"""

    pass


@contextmanager
def timeout_context(seconds: int):
    """"""
    import platform

    if platform.system() == "Windows":
        # Windows:  threading.Timer
        import threading

        timed_out = [False]

        def timeout_handler():
            timed_out[0] = True

        timer = threading.Timer(seconds, timeout_handler)
        timer.daemon = True
        timer.start()
        try:
            yield
            if timed_out[0]:
                raise TimeoutError(f"Operation timeout after {seconds} seconds")
        finally:
            timer.cancel()
    else:
        # Unix/Linux/Mac:  signal
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Operation timeout after {seconds} seconds")

        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)


class ProgressMonitor:
    """"""

    def __init__(self, total_phases: int = 11):
        self.total_phases = total_phases
        self.current_phase = 0
        self.start_time = time.time()
        self.phase_times = {}

    def start_phase(self, phase_num: int, phase_name: str):
        """"""
        self.current_phase = phase_num
        self.phase_times[phase_num] = {"start": time.time(), "name": phase_name}
        elapsed = time.time() - self.start_time
        progress = ((phase_num - 1) / self.total_phases) * 100
        remaining = self.estimate_remaining_time()
        print(f"\n{'=' * 70}")
        print(f" : {progress:.1f}% ({phase_num}/{self.total_phases})")
        print(f" : Phase {phase_num} - {phase_name}")
        print(f"  : {elapsed:.1f}s | : {remaining:.1f}s")
        print(f"{'=' * 70}\n")

    def end_phase(self, phase_num: int, success: bool):
        """"""
        if phase_num in self.phase_times:
            self.phase_times[phase_num]["end"] = time.time()
            self.phase_times[phase_num]["success"] = success
            duration = (
                self.phase_times[phase_num]["end"]
                - self.phase_times[phase_num]["start"]
            )
            status = "[OK] " if success else "[FAIL] "
            print(f" [{status}] Phase {phase_num}  (: {duration:.2f}s)")

    def estimate_remaining_time(self) -> float:
        """"""
        if self.current_phase <= 1:
            #
            return sum(PHASE_TIMEOUTS.values())

        completed_phases = [p for p in self.phase_times.values() if "end" in p]
        if not completed_phases:
            return 0.0

        avg_time = sum(p["end"] - p["start"] for p in completed_phases) / len(
            completed_phases
        )
        remaining_phases = self.total_phases - self.current_phase + 1
        return avg_time * remaining_phases


class CheckpointManager:
    """Manage project-local OpenSpec checkpoint state."""

    SCHEMA_VERSION = 1

    def __init__(
        self,
        checkpoint_file: Path,
        requirements_file: Path,
        fallback_file: Path | None = None,
    ):
        self.checkpoint_file = Path(checkpoint_file)
        self.fallback_file = (
            Path(fallback_file)
            if fallback_file and Path(fallback_file) != self.checkpoint_file
            else None
        )
        self.loaded_from_checkpoint_file = self.checkpoint_file
        self.requirements_file = Path(requirements_file)
        self._requirements_key = self._canonical_requirements_key(
            self.requirements_file
        )
        self.checkpoint = self._load()

    @staticmethod
    def _canonical_requirements_key(path: Path) -> str:
        try:
            resolved = Path(path).resolve()
        except OSError:
            resolved = Path(path).absolute()
        return resolved.as_posix().lower()

    @staticmethod
    def _requirements_path_for_save(path: Path) -> str:
        try:
            return Path(path).resolve().as_posix()
        except OSError:
            return Path(path).as_posix()

    def _load(self) -> dict:
        for candidate in [self.checkpoint_file, self.fallback_file]:
            if not candidate or not candidate.exists():
                continue
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    self.loaded_from_checkpoint_file = candidate
                    return json.load(f)
            except Exception:
                continue
        return {}

    def is_valid_for_current_run(self) -> bool:
        if not self.checkpoint:
            return False
        if self.checkpoint.get("schema_version") != self.SCHEMA_VERSION:
            return False
        saved_req = self.checkpoint.get("requirements_file")
        if not saved_req:
            return False
        return (
            self._canonical_requirements_key(Path(saved_req)) == self._requirements_key
        )

    def save(self, phase_num: int, success: bool, context):
        completed_phases = list(self.checkpoint.get("completed_phases", []))
        if success and phase_num not in completed_phases:
            completed_phases.append(phase_num)
        self.checkpoint = {
            "schema_version": self.SCHEMA_VERSION,
            "requirements_file": self._requirements_path_for_save(
                self.requirements_file
            ),
            "project_dir": context.project_dir.as_posix()
            if context.project_dir
            else None,
            "last_phase": phase_num,
            "last_success": success,
            "completed_phases": completed_phases,
            "timestamp": time.time(),
            "context": context.to_checkpoint_dict(),
        }
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(self.checkpoint, f, indent=2, ensure_ascii=False)
        self.loaded_from_checkpoint_file = self.checkpoint_file

    def restore_context(self, context) -> bool:
        if not self.is_valid_for_current_run():
            return False
        context.restore_from_checkpoint(self.checkpoint.get("context", {}))
        return True

    def archive(self, reason: str = "completed") -> "Path | None":
        if not self.checkpoint_file.exists():
            return None
        archive_dir = self.checkpoint_file.parent / "checkpoints"
        archive_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        archive_path = archive_dir / f"{timestamp}_{reason}.json"
        try:
            archive_path.write_bytes(self.checkpoint_file.read_bytes())
        except Exception:
            return None
        return archive_path

    def clear(self, archive_reason: "str | None" = None):
        if archive_reason is not None:
            self.archive(archive_reason)
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
            self.checkpoint = {}

    def get_resume_phase(self) -> int:
        last_phase = self.checkpoint.get("last_phase", 0)
        last_success = self.checkpoint.get("last_success", False)
        return last_phase + 1 if last_success else last_phase

    def is_phase_completed(self, phase_num: int) -> bool:
        return phase_num in self.checkpoint.get("completed_phases", [])


# 1:
def should_retry_error(result) -> bool:
    """"""
    #  errors
    if not hasattr(result, "errors") or not result.errors:
        return False

    error_text = " ".join(str(e) for e in result.errors).lower()
    non_retryable_keywords = [
        "authentication failed",
        "permission denied",
        "quota or credits appear exhausted",
        "check billing/package balance",
        "request timed out",
        "apitimeouterror",
        "status_code=401",
        "status_code=403",
    ]
    if any(keyword in error_text for keyword in non_retryable_keywords):
        return False

    retry_keywords = [
        "connection failed",
        "temporarily unavailable",
        "overloaded",
        "rate limited",
        "status_code=429",
        "status_code=500",
        "status_code=502",
        "status_code=503",
        "status_code=504",
        "status_code=529",
    ]

    return any(keyword in error_text for keyword in retry_keywords)


class EnhancedOpenSpecScheduler:
    """OpenSpec
    :
    -
    -
    -
    -
    -
    """

    def __init__(
        self,
        requirements_file: str,
        tool_registry,
        enable_timeout: bool = True,
        enable_retry: bool = True,
        enable_checkpoint: bool = True,
        enable_progress: bool = True,
        abort_on_critical_failure: bool = True,
        force_regenerate_code: bool = True,
        vector_retrieval_enabled: bool = False,
        vector_persist_dir: str | None = None,
        vector_top_k: int = 5,
        vector_prefer_chroma: bool = True,
        max_concurrency: int = 3,
        verbose: bool = False,
        debug: bool = False,
    ):
        """"""

        #
        from .scheduler import OpenSpecPhaseScheduler

        #  context
        self.base_scheduler = OpenSpecPhaseScheduler(
            requirements_file, tool_registry, abort_on_critical_failure
        )

        #  context ( base_scheduler )
        #  base_scheduler  context
        # : from .context import Context; self.context = Context(requirements_file)
        self.context = self.base_scheduler.context
        self.context.force_regenerate_code = force_regenerate_code
        self.vector_retrieval_enabled = vector_retrieval_enabled
        self.vector_persist_dir = Path(vector_persist_dir) if vector_persist_dir else None
        self.vector_top_k = vector_top_k
        self.vector_prefer_chroma = vector_prefer_chroma
        self.max_concurrency = max(1, int(max_concurrency or 1))
        self._apply_vector_options()
        self.config = get_config()

        #
        self.enable_timeout = enable_timeout
        self.enable_retry = enable_retry
        self.enable_checkpoint = enable_checkpoint
        self.enable_progress = enable_progress
        self.verbose = verbose
        self.debug = debug

        #
        self.progress = ProgressMonitor() if enable_progress else None
        try:
            initial_project_name = self.context.project_name or infer_openspec_project_name(
                self.context.requirements_file,
                language=self.context.language,
            )
            self.event_integration = EventBusIntegration(
                requirements_file=requirements_file,
                project_name=initial_project_name,
            )
            self.context.workflow_id = self.event_integration.workflow_id
            self.context.event_integration = self.event_integration
        except Exception as e:
            print(f"[WARNING] Failed to initialize EventBus integration: {e}")
            self.event_integration = None
        #
        checkpoint_file = self._get_checkpoint_file(self.context.requirements_file)
        legacy_checkpoint_file = self._get_legacy_checkpoint_file(
            self.context.requirements_file
        )
        self.checkpoint = (
            CheckpointManager(
                checkpoint_file,
                self.context.requirements_file,
                fallback_file=legacy_checkpoint_file,
            )
            if enable_checkpoint
            else None
        )

    def _apply_vector_options(self) -> None:
        self.context.vector_retrieval_enabled = self.vector_retrieval_enabled
        self.context.vector_persist_dir = self.vector_persist_dir
        self.context.vector_top_k = self.vector_top_k
        self.context.vector_prefer_chroma = self.vector_prefer_chroma
        self.context.phase4_max_concurrency = self.max_concurrency
        self.context.phase5_max_concurrency = self.max_concurrency

    def _get_checkpoint_file(self, requirements_file: Path) -> Path:
        project_name = infer_openspec_project_name(
            requirements_file,
            language=self.context.language,
        )
        return Path(project_name) / ".spec" / "checkpoint.json"

    def _get_legacy_checkpoint_file(self, requirements_file: Path) -> Path:
        req_path = Path(requirements_file)
        project_name = req_path.stem
        if project_name.endswith("_requirements"):
            project_name = project_name.replace("_requirements", "")
        if project_name.startswith("req_"):
            project_name = project_name.replace("req_", "")
        return Path(project_name) / ".spec" / "checkpoint.json"

    def run_all_phases(self, resume: bool = True) -> Dict:
        """"""

        start_phase = 1
        if self.checkpoint and not resume:
            self.checkpoint.clear()
        elif resume and self.checkpoint:
            restored = self.checkpoint.restore_context(self.context)
            if restored:
                self._apply_vector_options()
                # Update EventBus with restored project name
                if self.event_integration and self.context.project_name:
                    try:
                        self.event_integration.update_project_name(
                            self.context.project_name
                        )
                    except Exception as exc:
                        print(
                            f"[WARN] Failed to update EventBus project name on resume: {exc}"
                        )
                    resume_phase = self.checkpoint.get_resume_phase()
                    if resume_phase > 11:
                        print(
                            "\n[RESUME] workflow already completed; nothing to resume\n"
                        )
                        self._ensure_logger_for_resume(11)
                        if self.event_integration:
                            try:
                                phases_completed = sum(
                                    1
                                    for r in self.context.phase_results.values()
                                    if r.success
                                )
                                phases_failed = sum(
                                    1
                                    for r in self.context.phase_results.values()
                                    if not r.success and not r.data.get("skipped")
                                )
                                phases_skipped = sum(
                                    1
                                    for r in self.context.phase_results.values()
                                    if r.data.get("skipped")
                                )
                                self.event_integration.emit_workflow_completed(
                                    success=True,
                                    phases_completed=phases_completed,
                                    phases_failed=phases_failed,
                                    phases_skipped=phases_skipped,
                                )
                            except Exception as e:
                                print(
                                    f"[WARNING] Failed to emit workflow completed event: {e}"
                                )
                        return self._build_success_response()
                    if resume_phase > 1:
                        start_phase = resume_phase
                        print(f"\n[RESUME]  Phase {start_phase} \n")
                        self._ensure_logger_for_resume(start_phase)
                    else:
                        self.checkpoint.checkpoint = {}
                        self.checkpoint.loaded_from_checkpoint_file = (
                            self.checkpoint.checkpoint_file
                        )
                    print(
                        "\n[RESUME] checkpoint missing or incompatible; starting from Phase 1\n"
                    )

        # Emit workflow started event
        if self.event_integration and start_phase == 1:
            try:
                self.event_integration.emit_workflow_started(
                    language=self.context.language or "unknown",
                    project_type=getattr(self.context, "project_type", "unknown"),
                )
            except Exception as e:
                print(f"[WARNING] Failed to emit workflow started event: {e}")
        return self._run_phases_with_enhancements(start_phase)

    def _ensure_logger_for_resume(self, start_phase: int) -> None:
        context = self.context
        if context.logger or not context.project_dir or not context.project_name:
            return
        try:
            from .logger import OpenSpecLogger

            context.project_dir.mkdir(parents=True, exist_ok=True)
            context.logger = OpenSpecLogger(
                context.project_name,
                context.project_dir,
                verbose=self.verbose,
                debug=self.debug,
            )
            context.log_file = context.logger.log_file
            print(f"[INFO] resume log: {context.log_file}")
            context.logger.info(f"[RESUME] start_phase={start_phase}")
            backfill_through = min(start_phase - 1, 11)
            if backfill_through >= 1:
                self._backfill_pre_logger_phases(
                    context,
                    current_phase=backfill_through + 1,
                    current_duration=0.0,
                )
        except Exception as exc:
            print(f"[WARN] failed to init resume logger: {exc}")

    def _run_phases_with_enhancements(self, start_phase: int) -> Dict:
        """"""
        context = self.context
        tool_registry = self.base_scheduler.tool_registry

        # --- 2:  ---
        #
        from .logger import OpenSpecLogger
        from .phase1_parse_requirements import Phase1ParseRequirements
        from .phase2_create_structure import Phase2CreateStructure
        from .phase3_technical_design import Phase3TechnicalDesign
        from .phase4_generate_code import Phase4GenerateCode
        from .phase5_generate_tests import Phase5GenerateTests
        from .phase6_cmake_config import Phase6CMakeConfig
        from .phase7_test_docs import Phase7TestDocs
        from .phase8_readme import Phase8Readme
        from .phase9_quality_gate import Phase9QualityGate
        from .phase10_run_tests import Phase10RunTests
        from .phase11_final_report import Phase11FinalReport

        print()
        print("=" * 70)
        print(" OpenSpec - Requirements-Driven Development Workflow (Enhanced)")
        print("=" * 70)
        print(f"  Requirements: {context.requirements_file}")
        print(f"  Language: {'C++' if context.is_cpp else 'Python'}")
        print(f"  Timeout: {'Enabled' if self.enable_timeout else 'Disabled'}")
        print(f"  Retry: {'Enabled' if self.enable_retry else 'Disabled'}")
        print(f"  Checkpoint: {'Enabled' if self.enable_checkpoint else 'Disabled'}")
        print(
            "  Force regenerate code: {}".format(
                "Enabled"
                if getattr(context, "force_regenerate_code", True)
                else "Disabled"
            )
        )
        print("=" * 70)
        print()

        # --- 3:  Phase 10  ---
        #  PHASE_TIMEOUTS  Phase 10  10
        #
        phases = [
            Phase1ParseRequirements(context, tool_registry),
            Phase2CreateStructure(context, tool_registry),
            Phase3TechnicalDesign(context),
            Phase4GenerateCode(context, tool_registry),
            Phase5GenerateTests(context, tool_registry),
            Phase6CMakeConfig(context, tool_registry),
            Phase7TestDocs(context, tool_registry),
            Phase8Readme(context, tool_registry),
            Phase9QualityGate(context, tool_registry),
            Phase10RunTests(context, tool_registry),
            Phase11FinalReport(context),
        ]

        #
        for i in CRITICAL_PHASES:
            if i <= len(phases):
                phases[i - 1].is_critical = True

        #
        for i in range(start_phase, len(phases) + 1):
            phase = phases[i - 1]

            # Check checkpoint first
            if self.checkpoint and self.checkpoint.is_phase_completed(i):
                print(f"[SKIP] Phase {i} ")
                continue

            # Check if phase should be skipped based on project type/language
            if hasattr(phase, "should_skip"):
                should_skip, skip_reason = phase.should_skip()
                if should_skip:
                    skip_msg = f"[SKIP] Phase {i} ({phase.phase_name}) - {skip_reason}"
                    print(skip_msg)
                    if context.logger:
                        context.logger.info(skip_msg)
                    # Record skipped phase as successful with explicit skip metadata
                    skip_data = {
                        "skipped": True,
                        "skip_reason": skip_reason,
                    }
                    if i == 10:
                        skip_data.update(
                            {
                                "test_skipped": True,
                                "test_status": "skipped",
                                "test_summary": f"skipped ({skip_reason})",
                            }
                        )
                    result = PhaseResult.ok(f"Skipped: {skip_reason}", **skip_data)
                    context.set_phase_result(i, result)
                    if self.checkpoint:
                        self.checkpoint.save(i, True, context)
                    continue

            #
            if self.progress:
                self.progress.start_phase(i, phase.phase_name)

            # Emit phase started event
            if self.event_integration:
                try:
                    self.event_integration.emit_phase_started(i, phase.phase_name)
                except Exception:
                    pass  # Silently ignore event errors

            # --- 4:  Phase 2  ---
            #  context.logger  Phase 2
            if i == 2:
                result, duration = self._execute_phase(i, phase)
                result = self._apply_success_policy(i, result)
                context.set_phase_result(i, result)

                #  Phase 2  project_dir
                if result.success and context.project_dir:
                    try:
                        #
                        context.project_dir.mkdir(parents=True, exist_ok=True)
                        context.logger = OpenSpecLogger(
                            context.project_name,
                            context.project_dir,
                            verbose=self.verbose,
                            debug=self.debug,
                        )
                        context.log_file = context.logger.log_file
                        print(f"[INFO] : {context.log_file}")
                        self._backfill_pre_logger_phases(
                            context, current_phase=i, current_duration=duration
                        )
                        # Update EventBus with actual project name
                        if self.event_integration and context.project_name:
                            try:
                                self.event_integration.update_project_name(
                                    context.project_name
                                )
                            except Exception as exc:
                                print(
                                    f"[WARN] Failed to update EventBus project name: {exc}"
                                )
                    except Exception as exc:
                        print(f"[WARN] : {exc}")
                else:
                    print("[WARN] Phase 2 ")

                # Phase 2
                if self.progress:
                    self.progress.end_phase(i, result.success)
                # Emit phase completed event
                if self.event_integration:
                    try:
                        self.event_integration.emit_phase_completed(
                            phase_num=i,
                            phase_name=phase.phase_name,
                            success=result.success,
                            duration_ms=int(duration * 1000),
                        )
                    except Exception:
                        pass  # Silently ignore event errors
                if self.checkpoint:
                    self.checkpoint.save(i, result.success, context)

                #  Phase 2  critical
                if not result.success:
                    if phase.is_critical and context.abort_on_critical_failure:
                        error_msg = f" Phase {i} ({phase.phase_name}) "
                        if context.logger:
                            context.logger.critical(error_msg)
                            context.logger.error(f": {result.message}")
                            for error in result.errors:
                                context.logger.error(f" - {error}")
                        else:
                            print(f"\n[CRITICAL] {error_msg}")
                            print(f"[ERROR] : {result.message}")
                        return self._build_failure_response(i, phase, result)
                    else:
                        print(f"[WARN] Phase {i} ...")
                continue

            # ---  ---
            #  ( logger )
            if context.logger:
                context.logger.phase_start(i, phase.phase_name)

            #
            result, duration = self._execute_phase(i, phase)
            result = self._apply_success_policy(i, result)
            context.set_phase_result(i, result)

            #
            if context.logger:
                context.logger.phase_end(i, result.success, duration)

            #
            if self.progress:
                self.progress.end_phase(i, result.success)

            # Emit phase completed event
            if self.event_integration:
                try:
                    self.event_integration.emit_phase_completed(
                        phase_num=i,
                        phase_name=phase.phase_name,
                        success=result.success,
                        duration_ms=int(duration * 1000),
                    )
                except Exception:
                    pass  # Silently ignore event errors

            #
            if self.checkpoint:
                self.checkpoint.save(i, result.success, context)

            if i == 9 and result.success:
                self._run_critique_phase(context)

            #
            if not result.success:
                if phase.is_critical and context.abort_on_critical_failure:
                    error_msg = f" Phase {i} ({phase.phase_name}) "
                    if context.logger:
                        context.logger.critical(error_msg)
                        context.logger.error(f": {result.message}")
                        if result.errors:
                            for error in result.errors:
                                context.logger.error(f" - {error}")
                    else:
                        print(f"\n[CRITICAL] {error_msg}")
                        print(f"[ERROR] : {result.message}")

                    return self._build_failure_response(i, phase, result)
                warning_msg = f"Phase {i} ..."
                if context.logger:
                    context.logger.warning(warning_msg)
                else:
                    print(f"[WARN] {warning_msg}")
                return self._build_failure_response(i, phase, result)

        #
        if self.checkpoint:
            self.checkpoint.archive("completed")

        phase10_result = context.get_phase_result(10)
        phase10_data = phase10_result.data if phase10_result else {}
        test_skipped = bool(
            phase10_data.get("test_skipped") or phase10_data.get("skipped")
        )
        test_status = str(
            phase10_data.get("test_status")
            or ("skipped" if test_skipped else "completed")
        )
        test_summary = str(
            phase10_data.get("test_summary")
            or (
                "skipped ({})".format(phase10_data.get("skip_reason", "not applicable"))
                if test_skipped
                else "{}/{} passed".format(
                    getattr(context, "test_passed", 0),
                    getattr(context, "test_total", 0),
                )
            )
        )

        if self.event_integration:
            try:
                phases_completed = sum(
                    1 for r in context.phase_results.values() if r.success
                )
                phases_failed = sum(
                    1
                    for r in context.phase_results.values()
                    if not r.success and not r.data.get("skipped")
                )
                phases_skipped = sum(
                    1 for r in context.phase_results.values() if r.data.get("skipped")
                )
                self.event_integration.emit_workflow_completed(
                    success=True,
                    phases_completed=phases_completed,
                    phases_failed=phases_failed,
                    phases_skipped=phases_skipped,
                )
            except Exception as e:
                print(f"[WARNING] Failed to emit workflow completed event: {e}")

        return self._build_success_response(
            test_skipped=test_skipped,
            test_status=test_status,
            test_summary=test_summary,
        )

    def _backfill_pre_logger_phases(
        self, context, current_phase: int, current_duration: float
    ) -> None:
        """Replay earlier phase records into the project logger so the on-disk log is complete."""
        if not context.logger:
            return
        for phase_num in range(1, current_phase):
            previous = context.get_phase_result(phase_num)
            if not previous:
                continue
            phase_name = self._phase_name_for(phase_num)
            context.logger.phase_start(phase_num, phase_name)
            context.logger.info("(backfilled) " + (previous.message or ""))
            context.logger.phase_end(phase_num, previous.success, 0.0)
            current_result = context.get_phase_result(current_phase)
        if current_result:
            phase_name = self._phase_name_for(current_phase)
            context.logger.phase_start(current_phase, phase_name)
            context.logger.info("(backfilled) " + (current_result.message or ""))
            context.logger.phase_end(
                current_phase, current_result.success, current_duration
            )

    def _phase_name_for(self, phase_num: int) -> str:
        return {
            1: "Parse requirements",
            2: "Create project structure",
            3: "Generate tech design",
            4: "Generate core code",
            5: "Generate test documentation",
            6: "CMake config",
            7: "Test docs",
            8: "README",
            9: "Code review",
            10: "Compile and run tests",
            11: "Final report",
        }.get(phase_num, "Phase {}".format(phase_num))

    def _run_critique_phase(self, context) -> None:
        enable_critique = self.config.get("enable_critique_phase", True)
        if not enable_critique:
            if context.logger:
                context.logger.info("Phase 9.5 Critique disabled, skipping")
            else:
                print("[INFO] Phase 9.5 Critique disabled, skipping")
            return
        try:
            if context.logger:
                context.logger.info("Starting Phase 9.5: Critique Phase")

            llm_client = getattr(self.base_scheduler, "llm_client", None)
            critique_config = self.config.get("critique_config", {})

            from .phase9_5_critique import Phase9_5Critique

            phase_9_5 = Phase9_5Critique(
                context, llm_client=llm_client, config=critique_config
            )

            if context.logger:
                context.logger.phase_start(9.5, "Critique Phase")

            critique_result, critique_duration = phase_9_5.execute_with_timing()

            if context.logger:
                context.logger.phase_end(9.5, critique_result.success, critique_duration)
            if self.event_integration:
                self.event_integration.emit_phase_completed(
                    phase_num=9.5,
                    phase_name="Critique Phase",
                    success=critique_result.success,
                    duration_ms=int(critique_duration * 1000),
                )

            context.phase_results[9.5] = critique_result
            if self.checkpoint:
                self.checkpoint.save(9.5, critique_result.success, context)

            if critique_result.success:
                if context.logger:
                    overall_score = critique_result.data.get("overall_score", "N/A")
                    context.logger.info(
                        f"Phase 9.5 completed: Overall Score = {overall_score}/100"
                    )
            else:
                if context.logger:
                    context.logger.warning(f"Phase 9.5 failed: {critique_result.message}")
                else:
                    print(f"[WARN] Phase 9.5 Critique failed: {critique_result.message}")
        except Exception as e:
            if context.logger:
                context.logger.error(f"Phase 9.5 Critique error: {e}")
            else:
                print(f"[ERROR] Phase 9.5 Critique error: {e}")

    def _apply_success_policy(self, phase_num: int, result: PhaseResult) -> PhaseResult:
        violations = validate_phase_success(phase_num, result)
        if not violations:
            return result
        message = "Phase {} success policy violation".format(phase_num)
        if self.context.logger:
            self.context.logger.error(message)
            for violation in violations:
                self.context.logger.error(" - {}".format(violation))
        else:
            print("[ERROR] {}".format(message))
            for violation in violations:
                print("[ERROR]  - {}".format(violation))
        return PhaseResult.fail(message, errors=violations)

    def _execute_phase(self, phase_num: int, phase) -> tuple:
        """"""
        max_retries = RETRY_CONFIG.get(phase_num, 0) if self.enable_retry else 0
        timeout = PHASE_TIMEOUTS.get(phase_num, 60) if self.enable_timeout else None

        for attempt in range(max_retries + 1):
            result = None
            duration = 0
            try:
                if timeout and self.enable_timeout:
                    #
                    try:
                        with timeout_context(timeout):
                            result, duration = phase.execute_with_timing()
                    except TimeoutError:
                        if result is None:
                            raise
                else:
                    #
                    result, duration = phase.execute_with_timing()

                #
                if result.success:
                    return result, duration

                #
                if attempt >= max_retries:
                    return result, duration

                #
                if should_retry_error(result):
                    print(f"[RETRY] Phase {phase_num}  {attempt + 1}/{max_retries}")
                    time.sleep(2)  #  2
                    continue
                else:
                    for err in getattr(result, "errors", []) or []:
                        print(f"[NO-RETRY] Phase {phase_num}: {err}")
                    #
                    return result, duration

            except TimeoutError as e:
                #
                if attempt < max_retries:
                    print(f"[RETRY] Phase {phase_num}  {attempt + 1}/{max_retries}")
                    time.sleep(2)
                    continue
                else:
                    #
                    from .base import PhaseResult

                    error_msg = f"Phase {phase_num}  ({timeout}s)"
                    return PhaseResult.fail(error_msg, errors=[str(e)]), timeout

        #
        from .base import PhaseResult

        return PhaseResult.fail(f"Phase {phase_num} "), 0

    def _build_success_response(
        self,
        test_skipped: bool | None = None,
        test_status: str | None = None,
        test_summary: str | None = None,
    ) -> Dict:
        context = self.context
        phase10_result = context.get_phase_result(10)
        phase10_data = phase10_result.data if phase10_result else {}
        resolved_test_skipped = (
            bool(phase10_data.get("test_skipped") or phase10_data.get("skipped"))
            if test_skipped is None
            else test_skipped
        )
        resolved_test_status = (
            str(
                phase10_data.get("test_status")
                or ("skipped" if resolved_test_skipped else "completed")
            )
            if test_status is None
            else test_status
        )
        resolved_test_summary = (
            str(
                phase10_data.get("test_summary")
                or (
                    "skipped ({})".format(
                        phase10_data.get("skip_reason", "not applicable")
                    )
                    if resolved_test_skipped
                    else "{}/{} passed".format(
                        getattr(context, "test_passed", 0),
                        getattr(context, "test_total", 0),
                    )
                )
            )
            if test_summary is None
            else test_summary
        )
        return {
            "success": True,
            "project_dir": str(context.project_dir),
            "project_name": context.project_name,
            "test_passed": getattr(context, "test_passed", 0),
            "test_failed": getattr(context, "test_failed", 0),
            "test_total": getattr(context, "test_total", 0),
            "test_skipped": resolved_test_skipped,
            "test_status": resolved_test_status,
            "test_summary": resolved_test_summary,
            "log_file": str(context.log_file) if context.log_file else None,
            "phases": context.phase_results,
        }

    def _build_failure_response(self, phase_num: int, phase, result) -> Dict:
        """"""
        context = self.context
        return {
            "success": False,
            "failed_phase": phase_num,
            "failed_phase_name": phase.phase_name,
            "error_message": result.message,
            "errors": result.errors,
            "project_dir": str(context.project_dir) if context.project_dir else None,
            "log_file": str(context.log_file) if context.log_file else None,
            "phases": context.phase_results,
        }
