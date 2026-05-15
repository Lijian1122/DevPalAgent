# -*- coding: utf-8 -*-
"""
OpenSpec Phase  -

"""

import time
import json
import signal
from pathlib import Path
from typing import Dict, Optional
from contextlib import contextmanager

#
PHASE_TIMEOUTS = {
    1: 30,   # Phase 1:
    2: 10,   # Phase 2:
    3: 120,  # Phase 3: AI
    4: 180,  # Phase 4: AI
    5: 30,   # Phase 5:
    6: 10,   # Phase 6:  CMakeLists
    7: 10,   # Phase 7:
    8: 10,   # Phase 8:  README
    9: 60,   # Phase 9:
    10: 600,  # Phase 10:  +  + AI  (10)
    11: 30,  # Phase 11:
}

#
RETRY_CONFIG = {
    3: 2,    # Phase 3: AI  -  2
    4: 2,    # Phase 4: AI  -  2
    10: 1,   # Phase 10:  -  1
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
    if platform.system() == 'Windows':
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
        self.phase_times[phase_num] = {'start': time.time(), 'name': phase_name}
        elapsed = time.time() - self.start_time
        progress = ((phase_num - 1) / self.total_phases) * 100
        remaining = self.estimate_remaining_time()
        print(f"\n{'='*70}")
        print(f" : {progress:.1f}% ({phase_num}/{self.total_phases})")
        print(f" : Phase {phase_num} - {phase_name}")
        print(f"  : {elapsed:.1f}s | : {remaining:.1f}s")
        print(f"{'='*70}\n")

    def end_phase(self, phase_num: int, success: bool):
        """"""
        if phase_num in self.phase_times:
            self.phase_times[phase_num]['end'] = time.time()
            self.phase_times[phase_num]['success'] = success
            duration = self.phase_times[phase_num]['end'] - self.phase_times[phase_num]['start']
            status = "[OK] " if success else "[FAIL] "
            print(f" [{status}] Phase {phase_num}  (: {duration:.2f}s)")

    def estimate_remaining_time(self) -> float:
        """"""
        if self.current_phase <= 1:
            #
            return sum(PHASE_TIMEOUTS.values())

        completed_phases = [p for p in self.phase_times.values() if 'end' in p]
        if not completed_phases:
            return 0.0

        avg_time = sum(p['end'] - p['start'] for p in completed_phases) / len(completed_phases)
        remaining_phases = self.total_phases - self.current_phase + 1
        return avg_time * remaining_phases


class CheckpointManager:
    """"""

    def __init__(self, checkpoint_file: Path):
        self.checkpoint_file = checkpoint_file
        self.checkpoint = self._load()

    def _load(self) -> dict:
        """"""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save(self, phase_num: int, success: bool):
        """"""
        self.checkpoint['last_phase'] = phase_num
        self.checkpoint['last_success'] = success
        if 'completed_phases' not in self.checkpoint:
            self.checkpoint['completed_phases'] = []
        if success and phase_num not in self.checkpoint['completed_phases']:
            self.checkpoint['completed_phases'].append(phase_num)
        self.checkpoint['timestamp'] = time.time()
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(self.checkpoint, f, indent=2)

    def clear(self):
        """"""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
        self.checkpoint = {}

    def get_resume_phase(self) -> int:
        """"""
        last_phase = self.checkpoint.get('last_phase', 0)
        last_success = self.checkpoint.get('last_success', False)
        if last_success:
            return last_phase + 1
        else:
            return last_phase

    def is_phase_completed(self, phase_num: int) -> bool:
        """"""
        return phase_num in self.checkpoint.get('completed_phases', [])


# 1:
def should_retry_error(result) -> bool:
    """"""
    #  errors
    if not hasattr(result, 'errors') or not result.errors:
        return False

    retry_keywords = [
        'timeout',
        'connection',
        'rate limit',
        'temporary',
        'network',
        'unavailable',
        'retry'
    ]

    #
    error_text = ' '.join(str(e) for e in result.errors).lower()
    return any(keyword in error_text for keyword in retry_keywords)


class EnhancedOpenSpecScheduler:
    """ OpenSpec
    :
    -
    -
    -
    -
    -
    """

    def __init__(self, requirements_file: str, tool_registry,
                 enable_timeout: bool = True,
                 enable_retry: bool = True,
                 enable_checkpoint: bool = True,
                 enable_progress: bool = True,
                 abort_on_critical_failure: bool = True):
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

        #
        self.enable_timeout = enable_timeout
        self.enable_retry = enable_retry
        self.enable_checkpoint = enable_checkpoint
        self.enable_progress = enable_progress

        #
        self.progress = ProgressMonitor() if enable_progress else None

        #
        checkpoint_file = Path(".spec/checkpoint.json")
        self.checkpoint = CheckpointManager(checkpoint_file) if enable_checkpoint else None

    def run_all_phases(self, resume: bool = True) -> Dict:
        """"""

        start_phase = 1
        if self.checkpoint and not resume:
            self.checkpoint.clear()
        elif resume and self.checkpoint:
            resume_phase = self.checkpoint.get_resume_phase()
            if resume_phase > 1:
                start_phase = resume_phase
                print(f"\n[RESUME]  Phase {start_phase} \n")

        return self._run_phases_with_enhancements(start_phase)

    def _run_phases_with_enhancements(self, start_phase: int) -> Dict:
        """"""
        context = self.context
        tool_registry = self.base_scheduler.tool_registry

        # --- 2:  ---
        #
        from .phase1_parse_requirements import Phase1ParseRequirements
        from .phase2_create_structure import Phase2CreateStructure
        from .phase3_technical_design import Phase3TechnicalDesign
        from .phase4_generate_code import Phase4GenerateCode
        from .phase5_generate_tests import Phase5GenerateTests
        from .phase6_cmake_config import Phase6CMakeConfig
        from .phase7_test_docs import Phase7TestDocs
        from .phase8_readme import Phase8Readme
        from .phase9_code_review import Phase9CodeReview
        from .phase10_run_tests import Phase10RunTests
        from .phase11_final_report import Phase11FinalReport
        from .logger import OpenSpecLogger

        print()
        print("=" * 70)
        print(" OpenSpec - Requirements-Driven Development Workflow (Enhanced)")
        print("=" * 70)
        print(f"  Requirements: {context.requirements_file}")
        print(f"  Language: {'C++' if context.is_cpp else 'Python'}")
        print(f"   : {'' if self.enable_timeout else ''}")
        print(f" : {'' if self.enable_retry else ''}")
        print(f" : {'' if self.enable_checkpoint else ''}")
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
            Phase9CodeReview(context, tool_registry),
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

            #
            if self.checkpoint and self.checkpoint.is_phase_completed(i):
                print(f"[SKIP] Phase {i} ")
                continue

            #
            if self.progress:
                self.progress.start_phase(i, phase.phase_name)

            # --- 4:  Phase 2  ---
            #  context.logger  Phase 2
            if i == 2:
                result, duration = self._execute_phase(i, phase)
                context.set_phase_result(i, result)

                #  Phase 2  project_dir
                if result.success and context.project_dir:
                    try:
                        #
                        context.project_dir.mkdir(parents=True, exist_ok=True)
                        context.logger = OpenSpecLogger(context.project_name, context.project_dir)
                        context.log_file = context.logger.log_file
                        print(f"[INFO] : {context.log_file}")
                    except Exception as exc:
                        print(f"[WARN] : {exc}")
                else:
                    print("[WARN] Phase 2 ")

                # Phase 2
                if self.progress:
                    self.progress.end_phase(i, result.success)
                if self.checkpoint:
                    self.checkpoint.save(i, result.success)

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
            context.set_phase_result(i, result)

            #
            if context.logger:
                context.logger.phase_end(i, result.success, duration)

            #
            if self.progress:
                self.progress.end_phase(i, result.success)

            #
            if self.checkpoint:
                self.checkpoint.save(i, result.success)

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
                else:
                    warning_msg = f"Phase {i} ..."
                    if context.logger:
                        context.logger.warning(warning_msg)
                    else:
                        print(f"[WARN] {warning_msg}")

        # ---  ---
        #
        if self.checkpoint:
            self.checkpoint.clear()

        #
        return {
            'success': True,
            'project_dir': str(context.project_dir),
            'project_name': context.project_name,
            'test_passed': getattr(context, 'test_passed', 0),
            'test_failed': getattr(context, 'test_failed', 0),
            'test_total': getattr(context, 'test_total', 0),
            'log_file': str(context.log_file) if context.log_file else None,
            'phases': context.phase_results
        }

    def _execute_phase(self, phase_num: int, phase) -> tuple:
        """"""
        max_retries = RETRY_CONFIG.get(phase_num, 0) if self.enable_retry else 0
        timeout = PHASE_TIMEOUTS.get(phase_num, 60) if self.enable_timeout else None

        for attempt in range(max_retries + 1):
            try:
                if timeout and self.enable_timeout:
                    #
                    with timeout_context(timeout):
                        result, duration = phase.execute_with_timing()
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
                    time.sleep(2) #  2
                    continue
                else:
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

    def _build_failure_response(self, phase_num: int, phase, result) -> Dict:
        """"""
        context = self.context
        return {
            'success': False,
            'failed_phase': phase_num,
            'failed_phase_name': phase.phase_name,
            'error_message': result.message,
            'errors': result.errors,
            'project_dir': str(context.project_dir) if context.project_dir else None,
            'log_file': str(context.log_file) if context.log_file else None,
            'phases': context.phase_results
        }
