# -*- coding: utf-8 -*-
"""
Phase 10: 编译并运行测试
"""

import os
import subprocess
from pathlib import Path
from .base import PhaseInterface, PhaseResult, OpenSpecContext
from ..compiler_detector import find_vcvarsall
from ..test_result_parser import parse_test_results


class Phase10RunTests(PhaseInterface):
    """Phase 10: 编译并运行测试"""

    def __init__(self, context: OpenSpecContext, tool_registry):
        super().__init__(context)
        self.phase_number = 10
        self.phase_name = "编译并运行测试"
        self.tool_registry = tool_registry

    def execute(self) -> PhaseResult:
        """执行 Phase 10"""
        self.log("开始编译并运行测试...")

        project_dir = self.context.project_dir
        build_dir = project_dir / "build_test"
        build_dir.mkdir(exist_ok=True)
        self.context.build_dir = build_dir

        vcvars_path = find_vcvarsall()
        if not vcvars_path:
            self.log("[WARN] 未找到 MSVC 编译器，跳过编译测试")
            return PhaseResult.fail(
                "MSVC 编译器未找到",
                errors=["未找到 vcvarsall.bat，跳过编译测试"]
            )

        self.log(f"  使用 MSVC: {Path(vcvars_path).name}")

        try:
            # 10.1 CMake 配置
            self.log("  CMake 配置...")
            configure_cmd = (
                f'"{vcvars_path}" x64 && '
                f'cmake -G "Visual Studio 16 2019" -A x64 '
                f'-S "{project_dir}" -B "{build_dir}"'
            )
            result = subprocess.run(
                configure_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode != 0:
                self.log(f"    [FAIL] CMake 配置失败: {result.stderr[:200]}")
                return PhaseResult.fail(
                    f"CMake 配置失败",
                    errors=[result.stderr[:500]]
                )
            self.log("    [OK] CMake 配置完成")

            # 10.2 编译
            self.log("  编译项目...")
            build_cmd = f'"{vcvars_path}" x64 && cmake --build "{build_dir}" --config Release'
            result = subprocess.run(
                build_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode != 0:
                self.log(f"    [FAIL] 编译失败: {result.stderr[:200]}")
                return PhaseResult.fail(
                    f"编译失败",
                    errors=[result.stderr[:500]]
                )
            self.log("    [OK] 编译完成")

            # 10.3 运行测试
            self.log("  运行测试...")
            test_exe = build_dir / "tests" / "Release" / "test_auth.exe"
            if not test_exe.exists():
                test_exe = build_dir / "Release" / "test_auth.exe"
            if not test_exe.exists():
                test_exe = build_dir / "test_auth.exe"

            if test_exe.exists():
                test_result = subprocess.run(
                    str(test_exe),
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                self.context.test_output = test_result.stdout + test_result.stderr

                stats = parse_test_results(self.context.test_output)
                self.context.test_passed = stats["passed"]
                self.context.test_total = stats["total"]

                self.log(f"    [OK] 测试完成: {stats['passed']}/{stats['total']} 通过")
            else:
                self.log("    [WARN] 未找到测试可执行文件")
                self.context.test_output = "未找到测试可执行文件"

            self.log("[OK] 编译测试阶段完成")
            return PhaseResult.ok(
                "编译测试完成",
                build_dir=str(build_dir),
                test_passed=self.context.test_passed,
                test_total=self.context.test_total
            )

        except subprocess.TimeoutExpired:
            self.log("  [FAIL] 操作超时")
            return PhaseResult.fail(
                "编译测试超时",
                errors=["操作超时，可能是编译问题或系统资源不足"]
            )
        except Exception as e:
            self.log(f"  [FAIL] 异常: {str(e)}")
            return PhaseResult.fail(
                f"编译测试阶段异常: {str(e)}",
                errors=[str(e)]
            )
