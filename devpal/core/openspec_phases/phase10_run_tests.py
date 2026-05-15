# -*- coding: utf-8 -*-
"""Phase 10: 编译、运行测试并更新测试文档

流程：
1. 编译测试代码
2. 运行测试
3. 解析测试结果
4. 将测试结果更新到测试文档（Phase 5 生成的）
5. 如果测试失败，尝试自愈（可选）
"""

import subprocess
import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .base import PhaseInterface, PhaseResult, OpenSpecContext
from ..compiledb import CompileDB
from .test_self_healer import TestSelfHealer
from ..compiler_detector import find_visual_studio_compiler, check_mingw_compiler
from ..llm_client import get_llm_client

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

    def execute(self) -> PhaseResult:
        self.log("Phase 10 start: compile + run tests + update docs (AI self-heal enabled)")

        project_dir = self.context.project_dir
        tests_dir = project_dir / "tests"

        if not tests_dir.exists():
            self.log("  [FAIL] tests/ directory not found")
            return PhaseResult.fail("No tests to run", errors=["tests/ directory not found"])

        test_files = list(tests_dir.glob("test_*.cpp"))
        if not test_files:
            self.log("  [FAIL] no test files found")
            return PhaseResult.fail("No tests to run", errors=["no test_*.cpp files found"])

        # 检测编译器
        compiler_cmd, compiler_env = self._detect_compiler()
        if not compiler_cmd:
            self.log("  [FAIL] no compiler found (MSVC/g++)")
            return PhaseResult.fail(
                "No compiler available",
                errors=["MSVC/g++ compiler not found"]
            )

        # 初始化自愈器（带错误处理）
        try:
            llm_client = get_llm_client()
            self.self_healer = TestSelfHealer(
                project_dir=project_dir,
                llm_client=llm_client,
                logger=self.log)
        except Exception as exc:
            self.log(f"  [WARN] Failed to initialize self-healer: {exc}")
            self.log("  [INFO] Self-healing will be disabled for this run")
            self.self_healer = None

        # 编译主程序（如果存在）
        main_cpp = project_dir / "src" / "main.cpp"
        if main_cpp.exists():
            self.log("  [BUILD] Compiling main program...")
            main_success = self._compile_main_program(project_dir, compiler_cmd, compiler_env)
            if main_success:
                self.log("  [OK] Main program compiled successfully")
            else:
                self.log("  [WARN] Main program compilation failed")


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
                attempt_label = f"attempt {attempt + 1}/{MAX_HEAL_ATTEMPTS + 1}" if attempt > 0 else "initial"

                # 编译（自愈后需要强制重新编译）
                exe_path, compile_success, compile_output = self._compile_test(
                    test_file, project_dir, build_dir, compiler_cmd, compiler_env,
                    force_rebuild=(attempt > 0)
                )

                if not compile_success:
                    self.log(f"  [FAIL] compile failed ({attempt_label})")

                    # 如果还有尝试机会，使用 AI 修复编译错误
                    if attempt < MAX_HEAL_ATTEMPTS and self.self_healer:
                     # 第一次尝试使用默认模型，第二次尝试使用 Opus
                        use_fallback = (attempt > 0)
                        if self.self_healer.heal_compile_error(test_file, compile_output, use_fallback=use_fallback):
                            self.context.self_heal_attempts += 1
                            continue  # 重新编译
                        else:
                            self.log(f"  [HEAL] Failed to fix compile error, giving up")

                    # 记录最终失败结果
                    final_result = {
                        'test_file': str(test_file),
                        'compile_success': False,
                        'run_success': False,
                        'passed': 0,
                        'total': 0,
                        'output': compile_output
                    }
                    break

                self.log(f"  [OK] compile succeeded ({attempt_label})")

                # 运行测试
                run_success, test_output, passed, total = self._run_test(exe_path)

                # 检查测试是否全部通过
                if passed == total and total > 0:
                    self.log(f"  [OK] tests: {passed}/{total} passed ({attempt_label})")
                    final_result = {
                        'test_file': str(test_file),
                        'compile_success': True,
                        'run_success': True,
                        'passed': passed,
                        'total': total,
                        'output': test_output
                    }
                    break  # 成功，退出循环

                self.log(f"  [FAIL] tests: {passed}/{total} passed ({attempt_label})")

                # 如果还有尝试机会，使用 AI 修复测试失败
                if attempt < MAX_HEAL_ATTEMPTS and self.self_healer:
                    if self.self_healer.heal_test_failure(test_file, test_output, passed, total):
                        self.context.self_heal_attempts += 1
                        continue  # 重新编译和测试
                    else:
                        self.log(f"  [HEAL] Failed to fix test failures, giving up")

                # 记录最终结果（部分通过或全部失败）
                final_result = {
                    'test_file': str(test_file),
                    'compile_success': True,
                    'run_success': run_success,
                    'passed': passed,
                    'total': total,
                    'output': test_output
                }
                break

            # 累计统计
            if final_result:
                test_results.append(final_result)
                total_passed += final_result['passed']
                total_failed += (final_result['total'] - final_result['passed'])


        # 更新测试文档
        if hasattr(self.context, 'test_docs') and self.context.test_docs:
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

        # 判断是否有测试运行
        if total_all == 0:
            # 编译失败或没有测试
            return PhaseResult.fail(
           "Compilation failed: no tests were run",
             errors=["Compilation failed or no test files found"]
       )

        # 判断测试是否全部通过
        if total_passed < total_all:
            # 有测试失败
            return PhaseResult.fail(
            f"Tests failed: {total_passed}/{total_all} passed",
                errors=[f"{total_failed} test(s) failed"]
            )

        # 所有测试通过
        return PhaseResult.ok(
            f"All tests passed: {total_passed}/{total_all}",
            test_passed=total_passed,
            test_failed=total_failed,
            test_total=total_all,
          test_results=test_results
        )

    def _detect_compiler(self) -> Tuple[Optional[str], Optional[Dict]]:
        """检测可用的编译器，返回 (compiler_type, env)"""
        # Windows 优先检测 MSVC
        if os.name == 'nt':
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

    def _compile_test(self, test_file: Path, project_dir: Path,
                      build_dir: Path, compiler: str, compiler_env: Optional[Dict] = None,
                      force_rebuild: bool = False) -> Tuple[Optional[Path], bool, str]:
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
                self.log(f"  [CMAKE] Configuring...")

                if compiler == "msvc":
                    # MSVC: 使用 Visual Studio generator
                    configure_cmd = [
                        "cmake",
                        "-G", "Visual Studio 16 2019",  # 或 "Visual Studio 16 2019"
                        "-A", "x64",
                        "-S", str(project_dir),
                        "-B", str(build_dir)
                    ]
                else:
                    # MinGW: 使用 Unix Makefiles
                    configure_cmd = [
                        "cmake",
                        "-G", "Unix Makefiles",
                        "-S", str(project_dir),
                        "-B", str(build_dir)
                    ]

                result = subprocess.run(
                    configure_cmd,
                    capture_output=True,
                    text=True,
                    timeout=120,
                    env=compiler_env
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
                "--build", str(build_dir),
                "--config", "Release",
                "--target", test_file.stem
            ]

            result = subprocess.run(
                build_cmd,
                capture_output=True,
                text=True,
                timeout=120,
                env=compiler_env
            )

            output_lines.append("=== CMake Build ===")
            output_lines.append(result.stdout)
            output_lines.append(result.stderr)

            if exe_path.exists():
                return exe_path, True, "\n".join(output_lines)
            else:
                return None, False, "\n".join(output_lines)

        except Exception as e:
            output_lines.append(f"Exception: {str(e)}")
            return None, False, "\n".join(output_lines)


    def _run_test(self, exe_path: Path) -> Tuple[bool, str, int, int]:
        """运行测试并解析结果"""
        try:
            result = subprocess.run(
                [str(exe_path)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=exe_path.parent,
                encoding='utf-8',
                errors='replace'
            )

            output = (result.stdout or "") + "\n" + (result.stderr or "")


            # 解析测试结果
            passed, total = self._parse_test_output(output)

            success = result.returncode == 0 or (total > 0 and passed == total)

            return success, output, passed, total

        except Exception as e:
            return False, f"Run exception: {str(e)}", 0, 0

    def _parse_test_output(self, output: str) -> Tuple[int, int]:
        """解析测试输出，返回 (passed, total)"""
        passed = 0
        failed = 0

        lines = output.split('\n')
        for line in lines:
            if '[OK]' in line or 'PASS' in line or '✓' in line:
                passed += 1
            elif '[FAIL]' in line or 'FAIL' in line or '✗' in line:
                failed += 1

        total = passed + failed
        return passed, total

    def _update_test_doc(self, doc_path: str, test_result: Dict):
        """将测试结果更新到测试文档"""
        doc_file = Path(doc_path)
        if not doc_file.exists():
            return

        try:
            content = doc_file.read_text(encoding='utf-8')

            # 移除旧的测试结果部分
            if "## 测试执行结果" in content or "## 测试运行结果" in content:
                content = re.sub(
                    r'##\s+(测试执行结果|测试运行结果)[\s\S]*?(?=\n##\s|\Z)',
                    '',
                    content
                ).rstrip()

            # 生成新的测试结果部分
            result_section = self._generate_result_section(test_result)

            # 追加到文档末尾
            content = content + "\n\n" + result_section

            doc_file.write_text(content, encoding='utf-8')

        except Exception as e:
            self.log(f"  [WARN] Failed to update doc {doc_file.name}: {e}")

    def _generate_result_section(self, test_result: Dict) -> str:
        """生成测试结果章节"""
        from datetime import datetime

        compile_success = test_result.get('compile_success', False)
        run_success = test_result.get('run_success', False)
        passed = test_result.get('passed', 0)
        total = test_result.get('total', 0)
        output = test_result.get('output', '')

        pass_rate = f"{(passed / total * 100):.1f}%" if total > 0 else "N/A"

        status_icon = "✅" if passed == total and total > 0 else "⚠️" if passed > 0 else "❌"

        section = f"""## 测试执行结果

> **测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> **执行状态**: {status_icon} {'全部通过' if passed == total and total > 0 else '部分通过' if passed > 0 else '测试失败'}

### 结果统计

| 统计项 | 数值 |
|--------|------|
| 编译状态 | {'✅ 成功' if compile_success else '❌ 失败'} |
| 运行状态 | {'✅ 完成' if run_success else '❌ 异常'} |
| 总测试数 | {total} 个 |
| **通过数** | **{passed} 个** |
| 失败数 | {total - passed} 个 |
| **通过率** | **{pass_rate}** |

"""

        # 测试输出日志（截取前30行）
        output_lines = [l.strip() for l in output.split('\n') if l.strip()][:30]
        if output_lines:
            section += "### 测试输出日志\n\n"
            section += "```\n"
            section += '\n'.join(output_lines)
            section += "\n```\n\n"

        return section

    def _compile_main_program(self, project_dir: Path, compiler: str,
                  compiler_env: Optional[Dict] = None) -> bool:
        """Compile main program using CMake

        Args:
            project_dir: Project root directory
            compiler: Compiler type (msvc/g++)
            compiler_env: Compiler environment variables

        Returns:
            True if compilation succeeded, False otherwise
        """
        build_dir = project_dir / "build"
        build_dir.mkdir(exist_ok=True)

        try:
            # Step 1: CMake configure
            if compiler == "msvc":
                configure_cmd = [
                    "cmake",
                    "-G", "Visual Studio 16 2019",
                    "-A", "x64",
                    "-S", str(project_dir),
                    "-B", str(build_dir)
                ]
            else:
                configure_cmd = [
                    "cmake",
                    "-G", "Unix Makefiles",
                    "-S", str(project_dir),
                    "-B", str(build_dir)
                ]

            result = subprocess.run(
                configure_cmd,
                capture_output=True,
                text=True,
                timeout=120,
                env=compiler_env
            )

            if result.returncode != 0:
                self.log(f"  [FAIL] CMake configure failed: {result.stderr[:200]}")
                return False

            # Step 2: CMake build
            target_name = f"{project_dir.name}_app"
            build_cmd = [
                "cmake",
                "--build", str(build_dir),
                "--config", "Release",
                "--target", target_name
            ]

            result = subprocess.run(
                build_cmd,
                capture_output=True,
                text=True,
                timeout=120,
                env=compiler_env
            )

            if result.returncode == 0:
                return True
            else:
                self.log(f"  [FAIL] CMake build failed: {result.stderr[:200]}")
                return False

        except Exception as e:
            self.log(f"  [FAIL] Compilation exception: {e}")
            return False

    def _update_usage_stats(self, client) -> None:
        ctx = self.context
        ctx.llm_calls = client.usage.calls
        ctx.llm_input_tokens = client.usage.input_tokens
        ctx.llm_output_tokens = client.usage.output_tokens
        ctx.llm_cache_read_tokens = client.usage.cache_read_tokens
