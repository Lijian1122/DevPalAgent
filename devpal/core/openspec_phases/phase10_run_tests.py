# -*- coding: utf-8 -*-
"""Phase 10: 编译、运行测试并更新测试文档

流程：
1. 编译测试代码
2. 运行测试
3. 解析测试结果
4. 将测试结果更新到测试文档（Phase 5 生成的）
5. 如果测试失败，尝试自愈（可选）
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from devpal.core.multi_agent.models import CommandResult
from devpal.core.schema.languages.cpp_plugin import CppLanguagePlugin
from devpal.core.schema.languages.python_plugin import PythonLanguagePlugin
from devpal.core.schema.languages.shell_plugin import ShellLanguagePlugin

from ..compiledb import CompileDB
from ..compiler_detector import check_mingw_compiler, find_visual_studio_compiler
from ..llm_client import get_llm_client
from ..schema.event_bus import get_global_event_bus
from ..schema.workflow_events import (
    ToolCalledEvent,
    ToolCompletedEvent,
    ToolFailedEvent,
)
from .base import OpenSpecContext, PhaseInterface, PhaseResult
from .enhanced_test_self_healer import EnhancedTestSelfHealer
from .test_self_healer import TestSelfHealer


class CommandPolicyViolation(Exception):
    pass


class Phase10RunTests(PhaseInterface):
    """Phase 10: 编译运行测试并更新文档"""

    def __init__(self, context: OpenSpecContext, tool_registry):
        super().__init__(context)
        self.phase_number = 10
        self.phase_name = "Compile + test + update docs"
        self.tool_registry = tool_registry
        self.compiledb = CompileDB()
        # 新增：初始化自愈器
        self.self_healer = None  # 延迟初始化，需要 LLM client
        # EventBus integration
        self.event_bus = get_global_event_bus()
        self.workflow_id = getattr(context, "workflow_id", "")
        self._phase10_command_results: List[Dict] = []

    def should_skip(self) -> tuple:
        """判断是否应该跳过当前阶段"""
        from .phase_skip_rules import should_skip_for_non_cpp_project

        return should_skip_for_non_cpp_project(self.phase_number, self.context)

    def execute(self) -> PhaseResult:
        self.log(
            "Phase 10 start: compile + run tests + update docs (AI self-heal enabled)"
        )

        # 确保 project_dir 是绝对路径，避免多Agent模式下的路径问题
        project_dir = Path(self.context.project_dir).resolve()
        tests_dir = project_dir / "tests"

        if not tests_dir.exists():
            self.log("  [FAIL] tests/ directory not found")
            return PhaseResult.fail(
                "No tests to run", errors=["tests/ directory not found"]
            )

        # Check for test files based on language using LanguagePlugin
        language = self.context.language

        # Try to use LanguagePlugin to get test file patterns
        try:
            if language == "python":
                plugin = PythonLanguagePlugin()
            elif language == "shell":
                plugin = ShellLanguagePlugin()
            else:  # cpp
                plugin = CppLanguagePlugin()

            # Get test file extension from plugin
            extensions = plugin.get_supported_extensions()
            test_pattern = f"test_*{extensions[0]}" if extensions else "test_*"
            test_files = list(tests_dir.glob(test_pattern))

            self.log(
                f"  [LanguagePlugin] Using {language} plugin, pattern: {test_pattern}"
            )
        except Exception as e:
            self.log(f"  [WARNING] Failed to use LanguagePlugin: {e}, using fallback")
            # Fallback to hardcoded patterns
            if language == "cpp":
                test_files = list(tests_dir.glob("test_*.cpp"))
                test_pattern = "test_*.cpp"
            elif language == "python":
                test_files = list(tests_dir.glob("test_*.py"))
                test_pattern = "test_*.py"
            elif language == "shell":
                test_files = list(tests_dir.glob("test_*.sh"))
                test_pattern = "test_*.sh"
            else:
                test_files = []
                test_pattern = "test_*"
        if not test_files:
            self.log(f"  [FAIL] no test files found (pattern: {test_pattern})")
            return PhaseResult.fail(
                "No tests to run", errors=[f"no {test_pattern} files found"]
            )

        # Branch based on language
        if language == "python":
            if bool(getattr(self.context, "enable_multi_agent", False)):
                return self._try_run_python_tests_multi_agent(project_dir, tests_dir, test_files)
            return self._run_python_tests(project_dir, tests_dir, test_files)
        elif language == "cpp":
            return self._run_cpp_tests(project_dir, tests_dir, test_files)
        else:
            self.log(f"  [WARN] Unsupported language for testing: {language}")
            return PhaseResult.ok("Tests skipped (unsupported language)", skipped=True)

    def _build_python_test_env(self, project_dir: Path) -> Dict[str, str]:
        env = os.environ.copy()
        src_dir = project_dir / "src"
        if src_dir.exists():
            pythonpath = str(src_dir)
            if "PYTHONPATH" in env:
                pythonpath = f"{pythonpath}{os.pathsep}{env['PYTHONPATH']}"
            env["PYTHONPATH"] = pythonpath
        return env

    def _try_run_python_tests_multi_agent(
        self, project_dir: Path, tests_dir: Path, test_files: List[Path]
    ) -> PhaseResult:
        from devpal.core.multi_agent import AgentPolicy, CommandSpec, MultiAgentCoordinator
        from devpal.core.openspec_phases.parallel_executor import ParallelTask

        self.log(f"  [MULTI-AGENT TEST] Running {len(test_files)} Python test files with pytest...")
        env = self._build_python_test_env(project_dir)
        command = CommandSpec(
            argv=["pytest", "tests", "-v"],
            cwd=project_dir,
            timeout_seconds=300,
            env=env,
        )
        task = ParallelTask(
            task_id="phase10:python:pytest",
            phase_number=self.phase_number,
            task_type="test_run",
            input_payload={
                "project_dir": project_dir,
                "language": "python",
                "test_files": [path.as_posix() for path in test_files],
                "commands": [command],
            },
        )
        policy = AgentPolicy(
            enabled=True,
            sandbox_level=getattr(self.context, "sandbox_level", "staging"),
            max_concurrency=1,
            retry_limit=0,
            allowed_tools=["execute_command"],
            timeout_seconds=300,
        )
        coordinator = MultiAgentCoordinator(
            policy=policy,
            log=self.log,
            event_integration=getattr(self.context, "event_integration", None),
        )
        try:
            results, summary = coordinator.execute_test_tasks([task])
        except Exception as exc:
            return PhaseResult.fail("Python tests failed", errors=[str(exc)])

        self.context.parallel_execution_stats[str(self.phase_number)] = summary
        result = results[0]
        output = str(result.metadata.get("output") or "")
        self.context.test_output = output
        test_total = len(test_files)
        if result.success:
            self.context.test_passed = test_total
            self.context.test_failed = 0
            self.context.test_total = test_total
            self.log("  [OK] All Python tests passed (multi-agent)")
            return PhaseResult.ok(
                "Python tests passed",
                test_passed=test_total,
                test_failed=0,
                test_total=test_total,
                multi_agent=True,
                parallel_summary=summary,
            )

        self.context.test_passed = 0
        self.context.test_failed = test_total
        self.context.test_total = test_total
        self.log("  [FAIL] Some Python tests failed (multi-agent)")
        error = result.error or str(result.metadata.get("stderr") or "Python tests failed")
        return PhaseResult.fail("Python tests failed", errors=[error])

    def _is_multi_agent_command_execution_enabled(self) -> bool:
        return bool(getattr(self.context, "enable_multi_agent", False))

    def _run_phase10_command(
        self,
        task_id: str,
        argv: List[str],
        timeout_seconds: int,
        env: Optional[Dict] = None,
        legacy_cwd: Optional[Path] = None,
        agent_cwd: Optional[Path] = None,
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
    ) -> CommandResult:
        if not self._is_multi_agent_command_execution_enabled():
            try:
                completed = subprocess.run(
                    argv,
                    cwd=legacy_cwd,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    env=env,
                    encoding=encoding,
                    errors=errors,
                )
                return CommandResult(
                    argv=list(argv),
                    cwd=legacy_cwd or "",
                    returncode=completed.returncode,
                    stdout=completed.stdout or "",
                    stderr=completed.stderr or "",
                )
            except subprocess.TimeoutExpired as exc:
                return CommandResult(
                    argv=list(argv),
                    cwd=legacy_cwd or "",
                    stdout=exc.stdout or "",
                    stderr=exc.stderr or "",
                    timed_out=True,
                    error=f"timeout after {timeout_seconds}s",
                )
            except Exception as exc:
                return CommandResult(
                    argv=list(argv),
                    cwd=legacy_cwd or "",
                    error=str(exc),
                )

        from devpal.core.multi_agent import AgentPolicy, CommandSpec, MultiAgentCoordinator
        from devpal.core.openspec_phases.parallel_executor import ParallelTask

        command = CommandSpec(
            argv=list(argv),
            cwd=agent_cwd or legacy_cwd or self.context.project_dir,
            timeout_seconds=timeout_seconds,
            env=env,
            encoding=encoding,
            errors=errors,
        )
        task = ParallelTask(
            task_id=task_id,
            phase_number=self.phase_number,
            task_type="test_run",
            input_payload={
                "project_dir": self.context.project_dir,
                "language": self.context.language,
                "commands": [command],
            },
        )
        policy = AgentPolicy(
            enabled=True,
            sandbox_level=getattr(self.context, "sandbox_level", "staging"),
            max_concurrency=1,
            retry_limit=0,
            allowed_tools=["execute_command"],
            timeout_seconds=timeout_seconds,
        )
        coordinator = MultiAgentCoordinator(
            policy=policy,
            log=self.log,
            event_integration=getattr(self.context, "event_integration", None),
        )
        results, summary = coordinator.execute_test_tasks([task])
        result = results[0]
        self._record_phase10_command_result(summary)
        if result.metadata.get("policy_violations"):
            raise CommandPolicyViolation(str(result.metadata["policy_violations"]))
        return CommandResult(
            argv=list(argv),
            cwd=command.cwd,
            returncode=0 if result.success else 1,
            stdout=str(result.metadata.get("stdout") or ""),
            stderr=str(result.metadata.get("stderr") or ""),
            duration_ms=result.duration_ms,
            timed_out=bool(result.metadata.get("commands", [{}])[-1].get("timed_out", False)) if result.metadata.get("commands") else False,
            error=result.error,
        )

    def _record_phase10_command_result(self, summary: Dict[str, object]) -> None:
        self._phase10_command_results.extend(summary.get("results", []))
        total_duration = sum(int(item.get("duration_ms", 0) or 0) for item in self._phase10_command_results)
        failed_count = sum(1 for item in self._phase10_command_results if not item.get("success"))
        self.context.parallel_execution_stats[str(self.phase_number)] = {
            "total_tasks": len(self._phase10_command_results),
            "success_count": len(self._phase10_command_results) - failed_count,
            "failed_count": failed_count,
            "retry_count": 0,
            "max_concurrency": 1,
            "fallback_used": False,
            "total_task_duration_ms": total_duration,
            "results": list(self._phase10_command_results),
        }

    def _run_python_tests(
        self, project_dir: Path, tests_dir: Path, test_files: List[Path]
    ) -> PhaseResult:
        """Run Python tests using pytest"""
        self.log(f"  [TEST] Running {len(test_files)} Python test files with pytest...")

        try:
            env = self._build_python_test_env(project_dir)

            # Use relative path "tests" instead of absolute path
            result = subprocess.run(
                ["pytest", "tests", "-v"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=300,
                env=env,
            )

            output = (result.stdout or "") + (
                "\n" + result.stderr if result.stderr else ""
            )
            self.context.test_output = output
            test_total = len(test_files)

            if result.returncode == 0:
                self.context.test_passed = test_total
                self.context.test_failed = 0
                self.context.test_total = test_total
                self.log("  [OK] All Python tests passed")
                return PhaseResult.ok(
                    "Python tests passed",
                    test_passed=test_total,
                    test_failed=0,
                    test_total=test_total,
                )
            else:
                self.context.test_passed = 0
                self.context.test_failed = test_total
                self.context.test_total = test_total
                self.log("  [FAIL] Some Python tests failed")
                self.log(f"  [OUTPUT] {result.stdout}")
                self.log(f"  [ERROR] {result.stderr}")
                return PhaseResult.fail("Python tests failed", errors=[result.stderr])
        except FileNotFoundError:
            self.log("  [WARN] pytest not found, skipping tests")
            return PhaseResult.ok("Tests skipped (pytest not installed)", skipped=True)
        except subprocess.TimeoutExpired:
            self.log("  [FAIL] Tests timed out after 300s")
            return PhaseResult.fail("Tests timed out", errors=["timeout after 300s"])
        except Exception as exc:
            self.log(f"  [FAIL] Test execution failed: {exc}")
            return PhaseResult.fail("Test execution failed", errors=[str(exc)])

    def _run_cpp_tests(
        self, project_dir: Path, tests_dir: Path, test_files: List[Path]
    ) -> PhaseResult:
        """Run C++ tests (original logic)"""
        try:
            return self._run_cpp_tests_impl(project_dir, tests_dir, test_files)
        except CommandPolicyViolation as exc:
            self.log(f"  [SECURITY] Command policy violation: {exc}")
            return PhaseResult.fail("Command policy violation", errors=[str(exc)])

    def _run_cpp_tests_impl(
        self, project_dir: Path, tests_dir: Path, test_files: List[Path]
    ) -> PhaseResult:
        # 检测编译器
        compiler_cmd, compiler_env = self._detect_compiler()
        if not compiler_cmd:
            self.log("  [FAIL] no compiler found (MSVC/g++)")
            return PhaseResult.fail(
                "No compiler available", errors=["MSVC/g++ compiler not found"]
            )

        # 初始化自愈器（带错误处理）
        # 支持增强模式（集成根因分析）
        use_enhanced_healer = getattr(self.context, "use_enhanced_self_healer", True)

        try:
            llm_client = get_llm_client()

            if use_enhanced_healer:
                self.log(
                    "  [INFO] Initializing Enhanced Self-Healer (with Root Cause Analysis)"
                )
                try:
                    self.self_healer = EnhancedTestSelfHealer(
                        project_dir=project_dir,
                        llm_client=llm_client,
                        context=self.context,
                        artifact_graph=getattr(self.context, "artifact_graph", None),
                        logger=self.log,
                    )
                    self.log("  [OK] Enhanced Self-Healer initialized successfully")
                except Exception as e:
                    self.log(f"  [WARN] Failed to initialize Enhanced Self-Healer: {e}")
                    self.log("  [INFO] Falling back to standard Self-Healer")
                    self.self_healer = TestSelfHealer(
                        project_dir=project_dir,
                        llm_client=llm_client,
                        logger=self.log,
                        context=self.context,
                    )
            else:
                self.log("  [INFO] Initializing standard Self-Healer")
                self.self_healer = TestSelfHealer(
                    project_dir=project_dir,
                    llm_client=llm_client,
                    logger=self.log,
                    context=self.context,
                )
        except Exception as exc:
            self.log(f"  [WARN] Failed to initialize self-healer: {exc}")
            self.log("  [INFO] Self-healing will be disabled for this run")
            self.self_healer = None

        # 编译主程序（如果存在）
        main_cpp = project_dir / "src" / "main.cpp"
        if main_cpp.exists():
            self.log("  [BUILD] Compiling main program...")

            # 尝试编译主程序，失败时使用自愈
            MAX_MAIN_HEAL_ATTEMPTS = 2
            main_success = False

            for attempt in range(MAX_MAIN_HEAL_ATTEMPTS + 1):
                attempt_label = (
                    f"attempt {attempt + 1}/{MAX_MAIN_HEAL_ATTEMPTS + 1}"
                    if attempt > 0
                    else "initial"
                )
                main_success, main_compile_output = self._compile_main_program(
                    project_dir, compiler_cmd, compiler_env
                )

                if main_success:
                    self.log(
                        f"  [OK] Main program compiled successfully ({attempt_label})"
                    )
                    break
                else:
                    self.log(
                        f"  [FAIL] Main program compilation failed ({attempt_label})"
                    )
                    self._log_compile_error_summary(main_compile_output)

                    # 如果还有尝试机会，使用 AI 修复编译错误
                    if attempt < MAX_MAIN_HEAL_ATTEMPTS and self.self_healer:
                        # 第一次尝试使用默认模型，第二次尝试使用 Opus
                        use_fallback = attempt > 0
                        if self.self_healer.heal_compile_error(
                            main_cpp, main_compile_output, use_fallback=use_fallback
                        ):
                            self.context.self_heal_attempts += 1
                            continue  # 重新编译
                    else:
                        self.log(f"  [HEAL] Attempt {attempt + 1} failed")
                    if attempt < MAX_MAIN_HEAL_ATTEMPTS - 1:
                        self.log(
                            "  [HEAL] Will retry with different model in next attempt"
                        )
                    # 不break，让循环继续尝试下一次
            if not main_success:
                self.log(
                    "  [ERROR] Main program compilation failed after all heal attempts"
                )
                return PhaseResult.fail(
                    "Main program compilation failed",
                    errors=["main.cpp compilation failed after self-healing attempts"],
                )

        # 编译和运行测试
        build_dir = project_dir / "build_test"
        build_dir.mkdir(exist_ok=True)

        total_passed = 0
        total_failed = 0
        test_results = []

        MAX_HEAL_ATTEMPTS = 2  # 每个测试最多尝试 2 次自愈

        for test_file in test_files:
            self.log(f"  === Testing {test_file.name} ===")

            # 尝试编译、测试、自愈的循环
            final_result = None
            for attempt in range(MAX_HEAL_ATTEMPTS + 1):
                attempt_label = (
                    f"attempt {attempt + 1}/{MAX_HEAL_ATTEMPTS + 1}"
                    if attempt > 0
                    else "initial"
                )

                # 编译（自愈后需要强制重新编译）
                exe_path, compile_success, compile_output = self._compile_test(
                    test_file,
                    project_dir,
                    build_dir,
                    compiler_cmd,
                    compiler_env,
                    force_rebuild=(attempt > 0),
                )

                if not compile_success:
                    self.log(f"  [FAIL] compile failed ({attempt_label})")
                    self._log_compile_error_summary(compile_output)

                    # 如果还有尝试机会，使用 AI 修复编译错误
                    if attempt < MAX_HEAL_ATTEMPTS and self.self_healer:
                        # 第一次尝试使用默认模型，第二次尝试使用 Opus
                        use_fallback = attempt > 0
                        if self.self_healer.heal_compile_error(
                            test_file, compile_output, use_fallback=use_fallback
                        ):
                            self.context.self_heal_attempts += 1
                            continue  # 重新编译
                        else:
                            self.log("  [HEAL] Failed to fix compile error, giving up")

                    # 记录最终失败结果
                    final_result = {
                        "test_file": str(test_file),
                        "compile_success": False,
                        "run_success": False,
                        "passed": 0,
                        "total": 0,
                        "output": compile_output,
                    }
                    break

                self.log(f"  [OK] compile succeeded ({attempt_label})")

                # 运行测试
                run_success, test_output, passed, total = self._run_test(exe_path)

                # 检查测试是否全部通过
                if passed == total and total > 0:
                    self.log(f"  [OK] tests: {passed}/{total} passed ({attempt_label})")
                    final_result = {
                        "test_file": str(test_file),
                        "compile_success": True,
                        "run_success": True,
                        "passed": passed,
                        "total": total,
                        "output": test_output,
                    }
                    break  # 成功，退出循环

                self.log(f"  [FAIL] tests: {passed}/{total} passed ({attempt_label})")

                # 如果还有尝试机会，使用 AI 修复测试失败
                if attempt < MAX_HEAL_ATTEMPTS and self.self_healer:
                    # 第一次尝试使用默认模型，第二次尝试使用 Opus
                    use_fallback = attempt > 0
                    if self.self_healer.heal_test_failure(
                        test_file, test_output, passed, total, use_fallback=use_fallback
                    ):
                        self.context.self_heal_attempts += 1
                        continue  # 重新编译和测试
                    else:
                        self.log("  [HEAL] Failed to fix test failures, giving up")

                # 记录最终结果（部分通过或全部失败）
                final_result = {
                    "test_file": str(test_file),
                    "compile_success": True,
                    "run_success": run_success,
                    "passed": passed,
                    "total": total,
                    "output": test_output,
                }
                break

            # 累计统计
            if final_result:
                test_results.append(final_result)
                total_passed += final_result["passed"]
                total_failed += final_result["total"] - final_result["passed"]

        # 更新测试文档
        if hasattr(self.context, "test_docs") and self.context.test_docs:
            self.log("  === Updating test documentation with results ===")

            for i, test_doc in enumerate(self.context.test_docs):
                if i < len(test_results):
                    result = test_results[i]
                    self._update_test_doc(test_doc, result)
                    self.log(f"  [OK] Updated {Path(test_doc).name}")

        # 更新 context
        total_all = total_passed + total_failed
        self.context.test_passed = total_passed
        self.context.test_failed = total_failed
        self.context.test_total = total_all
        # P2.3: update requirement statuses based on test outcome
        final_status = "VERIFIED" if total_all > 0 and total_failed == 0 else "FAILED"
        for req in self.context.structured_requirements or []:
            self.context.update_requirement_status(req.get("id", ""), final_status)

        # 更新 ArtifactGraph 中的测试结果
        self._update_artifact_graph_test_results(test_results)

        # 判断是否有测试运行
        if total_all == 0:
            # 编译失败或没有测试
            return PhaseResult.fail(
                "Compilation failed: no tests were run",
                errors=["Compilation failed or no test files found"],
            )

        # 判断测试是否全部通过
        if total_passed < total_all:
            # 有测试失败
            return PhaseResult.fail(
                f"Tests failed: {total_passed}/{total_all} passed",
                errors=[f"{total_failed} test(s) failed"],
            )

        # 所有测试通过
        return PhaseResult.ok(
            f"All tests passed: {total_passed}/{total_all}",
            test_passed=total_passed,
            test_failed=total_failed,
            test_total=total_all,
            test_results=test_results,
        )

    def _detect_compiler(self) -> Tuple[Optional[str], Optional[Dict]]:
        """检测可用的编译器，返回 (compiler_type, env)"""
        # Windows 优先检测 MSVC
        if os.name == "nt":
            found, message, msvc_env = find_visual_studio_compiler()
            if found:
                self.log(f"  [OK] {message}")
                return "msvc", msvc_env
            else:
                self.log(f"  [INFO] MSVC not found: {message}")

        # 检测 MinGW g++
        available, message = check_mingw_compiler()
        if available:
            self.log(f"  [OK] {message}")
            return "g++", None
        else:
            self.log(f"  [INFO] g++ not found: {message}")

        return None, None

    def _compile_test(
        self,
        test_file: Path,
        project_dir: Path,
        build_dir: Path,
        compiler: str,
        compiler_env: Optional[Dict] = None,
        force_rebuild: bool = False,
    ) -> Tuple[Optional[Path], bool, str]:
        """使用 CMake 编译测试文件

        Args:
            test_file: 测试源文件路径
            project_dir: 项目根目录
            build_dir: 构建输出目录
            compiler: 编译器类型 (msvc/g++)
            compiler_env: 编译器环境变量
            force_rebuild: 是否强制重新编译

        Returns:
            (exe_path, success, output)
        """
        exe_name = f"{test_file.stem}.exe"

        # CMake 生成的可执行文件位置
        if compiler == "msvc":
            exe_path = build_dir / "Release" / exe_name
        else:
            exe_path = build_dir / exe_name

        # 增量编译检查
        if not force_rebuild and exe_path.exists():
            test_mtime = test_file.stat().st_mtime
            exe_mtime = exe_path.stat().st_mtime

            if exe_mtime >= test_mtime:
                self.log(f"  [SKIP] {exe_name} is up-to-date, skipping compilation")
                return exe_path, True, "Skipped: executable is up-to-date"

        output_lines = []

        try:
            # Step 1: CMake 配置（只在第一次或强制重建时执行）
            cmake_cache = build_dir / "CMakeCache.txt"
            if force_rebuild or not cmake_cache.exists():
                self.log("  [CMAKE] Configuring...")

                if compiler == "msvc":
                    # MSVC: 使用 Visual Studio generator
                    configure_cmd = [
                        "cmake",
                        "-G",
                        "Visual Studio 16 2019",  # 或 "Visual Studio 16 2019"
                        "-A",
                        "x64",
                        "-S",
                        str(project_dir),
                        "-B",
                        str(build_dir),
                    ]
                else:
                    # MinGW: 使用 Unix Makefiles
                    configure_cmd = [
                        "cmake",
                        "-G",
                        "Unix Makefiles",
                        "-S",
                        str(project_dir),
                        "-B",
                        str(build_dir),
                    ]

                result = self._run_phase10_command(
                    task_id=f"phase10:cpp:test:{test_file.stem}:configure",
                    argv=configure_cmd,
                    timeout_seconds=120,
                    env=compiler_env,
                    agent_cwd=project_dir,
                )

                output_lines.append("=== CMake Configure ===")
                output_lines.append(result.stdout)
                output_lines.append(result.stderr)

                if result.returncode != 0:
                    return None, False, "\n".join(output_lines)

            # Step 2: CMake 编译
            self.log(f"  [CMAKE] Building {test_file.stem}...")

            build_cmd = [
                "cmake",
                "--build",
                str(build_dir),
                "--config",
                "Release",
                "--target",
                test_file.stem,
            ]

            result = self._run_phase10_command(
                task_id=f"phase10:cpp:test:{test_file.stem}:build",
                argv=build_cmd,
                timeout_seconds=120,
                env=compiler_env,
                agent_cwd=project_dir,
            )

            output_lines.append("=== CMake Build ===")
            output_lines.append(result.stdout)
            output_lines.append(result.stderr)

            if exe_path.exists():
                return exe_path, True, "\n".join(output_lines)
            else:
                return None, False, "\n".join(output_lines)

        except CommandPolicyViolation:
            raise
        except Exception as e:
            output_lines.append(f"Exception: {str(e)}")
            return None, False, "\n".join(output_lines)

    def _extract_compile_error_summary(
        self, compile_output: str, limit: int = 8
    ) -> List[str]:
        patterns = [
            r"fatal error",
            r"error C\d+",
            r"undefined reference",
            r"No such file or directory",
            r"cannot find",
            r"无法打开包括文件",
            r"error:",
        ]
        matches = []
        for line in compile_output.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if any(re.search(pattern, stripped, re.IGNORECASE) for pattern in patterns):
                matches.append(stripped)
                if len(matches) >= limit:
                    break
        return matches

    def _log_compile_error_summary(self, compile_output: str) -> None:
        summary = self._extract_compile_error_summary(compile_output)
        if not summary:
            return
        self.log("  [ERROR SUMMARY] compiler reported:")
        for line in summary:
            self.log(f"    {line}")

    def _run_test(self, exe_path: Path) -> Tuple[bool, str, int, int]:
        """运行测试并解析结果"""
        try:
            result = self._run_phase10_command(
                task_id=f"phase10:cpp:test:{exe_path.stem}:run",
                argv=[str(exe_path)],
                timeout_seconds=60,
                legacy_cwd=exe_path.parent,
                agent_cwd=exe_path.parent,
                encoding="utf-8",
                errors="replace",
            )

            output = (result.stdout or "") + "\n" + (result.stderr or "")

            # 解析测试结果
            passed, total = self._parse_test_output(output)

            success = result.returncode == 0 or (total > 0 and passed == total)

            return success, output, passed, total

        except CommandPolicyViolation:
            raise
        except Exception as e:
            return False, f"Run exception: {str(e)}", 0, 0

    def _parse_test_output(self, output: str) -> Tuple[int, int]:
        """解析测试输出，返回 (passed, total)"""
        # 首先尝试从 "Results: X/Y passed" 格式解析
        results_pattern = r"Results:\s*(\d+)/(\d+)\s+passed"
        match = re.search(results_pattern, output)
        if match:
            passed = int(match.group(1))
            total = int(match.group(2))
            return passed, total

        # 如果没有找到 Results 行，则统计 [PASS] 和 [FAIL] 标记
        passed = 0
        failed = 0

        lines = output.split("\n")
        for line in lines:
            if "[PASS]" in line or "[OK]" in line or "✓" in line:
                passed += 1
            elif "[FAIL]" in line or "✗" in line:
                failed += 1

        total = passed + failed
        return passed, total

    def _update_test_doc(self, doc_path: str, test_result: Dict):
        """将测试结果更新到测试文档"""
        doc_file = Path(doc_path)
        if not doc_file.exists():
            return

        try:
            content = doc_file.read_text(encoding="utf-8")

            # 移除旧的测试结果部分
            if "## 测试执行结果" in content or "## 测试运行结果" in content:
                content = re.sub(
                    r"##\s+(测试执行结果|测试运行结果)[\s\S]*?(?=\n##\s|\Z)",
                    "",
                    content,
                ).rstrip()

            # 生成新的测试结果部分
            result_section = self._generate_result_section(test_result)

            # 追加到文档末尾
            content = content + "\n\n" + result_section

            doc_file.write_text(content, encoding="utf-8")

        except Exception as e:
            self.log(f"  [WARN] Failed to update doc {doc_file.name}: {e}")

    def _generate_result_section(self, test_result: Dict) -> str:
        """生成测试结果章节"""
        from datetime import datetime

        compile_success = test_result.get("compile_success", False)
        run_success = test_result.get("run_success", False)
        passed = test_result.get("passed", 0)
        total = test_result.get("total", 0)
        output = test_result.get("output", "")

        pass_rate = f"{(passed / total * 100):.1f}%" if total > 0 else "N/A"

        status_icon = (
            "✅" if passed == total and total > 0 else "⚠️" if passed > 0 else "❌"
        )

        section = f"""## 测试执行结果

> **测试时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> **执行状态**: {status_icon} {"全部通过" if passed == total and total > 0 else "部分通过" if passed > 0 else "测试失败"}

### 结果统计

| 统计项 | 数值 |
|--------|------|
| 编译状态 | {"✅ 成功" if compile_success else "❌ 失败"} |
| 运行状态 | {"✅ 完成" if run_success else "❌ 异常"} |
| 总测试数 | {total} 个 |
| **通过数** | **{passed} 个** |
| 失败数 | {total - passed} 个 |
| **通过率** | **{pass_rate}** |

"""

        # 测试输出日志（截取前30行）
        output_lines = [line.strip() for line in output.split("\n") if line.strip()][
            :30
        ]
        if output_lines:
            section += "### 测试输出日志\n\n"
            section += "```\n"
            section += "\n".join(output_lines)
            section += "\n```\n\n"

        return section

    def _compile_main_program(
        self, project_dir: Path, compiler: str, compiler_env: Optional[Dict] = None
    ) -> Tuple[bool, str]:
        """Compile main program using CMake

        Args:
            project_dir: Project root directory
            compiler: Compiler type (msvc/g++)
            compiler_env: Compiler environment variables

        Returns:
            Tuple of (success: bool, output: str)
        """
        build_dir = project_dir / "build"
        build_dir.mkdir(exist_ok=True)

        output_lines = []

        try:
            # Step 1: CMake configure
            if compiler == "msvc":
                configure_cmd = [
                    "cmake",
                    "-G",
                    "Visual Studio 16 2019",
                    "-A",
                    "x64",
                    "-S",
                    str(project_dir),
                    "-B",
                    str(build_dir),
                ]
            else:
                configure_cmd = [
                    "cmake",
                    "-G",
                    "Unix Makefiles",
                    "-S",
                    str(project_dir),
                    "-B",
                    str(build_dir),
                ]

            result = self._run_phase10_command(
                task_id="phase10:cpp:main:configure",
                argv=configure_cmd,
                timeout_seconds=120,
                env=compiler_env,
                agent_cwd=project_dir,
            )

            output_lines.append("=== CMake Configure ===")
            output_lines.append(result.stdout)
            output_lines.append(result.stderr)

            if result.returncode != 0:
                return False, "\n".join(output_lines)

            # Step 2: CMake build
            target_name = f"{project_dir.name}_app"
            build_cmd = [
                "cmake",
                "--build",
                str(build_dir),
                "--config",
                "Release",
                "--target",
                target_name,
            ]

            result = self._run_phase10_command(
                task_id="phase10:cpp:main:build",
                argv=build_cmd,
                timeout_seconds=120,
                env=compiler_env,
                agent_cwd=project_dir,
            )

            output_lines.append("=== CMake Build ===")
            output_lines.append(result.stdout)
            output_lines.append(result.stderr)

            if result.returncode == 0:
                return True, "\n".join(output_lines)
            else:
                return False, "\n".join(output_lines)

        except CommandPolicyViolation:
            raise
        except Exception as e:
            output_lines.append(f"Exception: {str(e)}")
            return False, "\n".join(output_lines)

    def _update_usage_stats(self, client) -> None:
        ctx = self.context
        ctx.llm_calls = client.usage.calls
        ctx.llm_input_tokens = client.usage.input_tokens
        ctx.llm_output_tokens = client.usage.output_tokens
        ctx.llm_cache_read_tokens = client.usage.cache_read_tokens
        ctx.llm_cache_creation_tokens = client.usage.cache_creation_tokens

    def _update_artifact_graph_test_results(self, test_results: List[Dict]) -> None:
        """Update ArtifactGraph with test results metadata."""
        graph = self.context.artifact_graph
        if graph is None:
            return
        try:
            from devpal.core.schema.artifact_graph import ArtifactType
        except ImportError:
            return

        project_dir_abs = self.context.project_dir.resolve()

        for result in test_results:
            test_file_path = Path(result["test_file"])
            if not test_file_path.is_absolute():
                test_file_path = (project_dir_abs / test_file_path).resolve()
            rel_path = test_file_path.relative_to(project_dir_abs).as_posix()
            file_node_id = f"file:{rel_path}"

            node = graph.get_node(file_node_id)
            if node and node.type == ArtifactType.TEST:
                # Update test result metadata
                node.metadata["test_passed"] = result["passed"]
                node.metadata["test_total"] = result["total"]
                node.metadata["test_success"] = (
                    result["compile_success"] and result["run_success"]
                )
                node.metadata["last_run"] = True

    def _get_affected_tests_from_changes(self) -> List[Path]:
        """根据代码变更确定需要运行的测试文件

        使用 ArtifactGraph 分析哪些测试受到影响

        Returns:
            受影响的测试文件列表，如果无法确定则返回空列表（表示运行所有测试）
        """
        graph = self.context.artifact_graph
        if graph is None:
            return []

        try:
            from devpal.core.schema.artifact_graph import ArtifactType
        except ImportError:
            return []

        # 获取所有 AI 生成的代码文件（这些是可能变更的文件）
        changed_files = self.context.ai_generated_files
        if not changed_files:
            return []

        affected_tests = set()

        project_dir_abs = self.context.project_dir.resolve()

        for file_path in changed_files:
            try:
                changed_path = Path(file_path)
                if not changed_path.is_absolute():
                    changed_path = (project_dir_abs / changed_path).resolve()
                rel_path = changed_path.relative_to(project_dir_abs).as_posix()
                file_node_id = f"file:{rel_path}"

                # 查找测试该文件的所有测试
                for node, dep_type in graph.get_dependents(file_node_id):
                    if node.type == ArtifactType.TEST and node.path:
                        affected_tests.add(node.path)

                # 如果这个文件本身就是测试文件，也包含它
                if rel_path.startswith("tests/") and Path(file_path).exists():
                    affected_tests.add(Path(file_path))
            except (ValueError, AttributeError):
                continue

            return sorted(list(affected_tests))

    def _emit_tool_event(
        self, tool_name: str, success: bool, duration_ms: int = 0, error: str = ""
    ) -> None:
        """Emit tool execution event to EventBus"""
        if not self.workflow_id:
            return

        try:
            # Emit tool called event
            called_event = ToolCalledEvent(
                workflow_id=self.workflow_id,
                tool_name=tool_name,
                tool_params={},
                caller=f"phase{self.phase_number}",
            )
            self.event_bus.publish(called_event)

            # Emit completion or failure event
            if success:
                completed_event = ToolCompletedEvent(
                    workflow_id=self.workflow_id,
                    tool_name=tool_name,
                    success=True,
                    duration_ms=duration_ms,
                    result_summary="Tool executed successfully",
                )
                self.event_bus.publish(completed_event)
            else:
                failed_event = ToolFailedEvent(
                    workflow_id=self.workflow_id, tool_name=tool_name, error=error
                )
                self.event_bus.publish(failed_event)
        except Exception as e:
            self.log(f"  [WARN] Failed to emit tool event: {e}")
