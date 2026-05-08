# -*- coding: utf-8 -*-
"""
测试运行工具
编译和运行测试用例，收集测试结果并生成报告
"""
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult


class TestRunnerTool(BaseTool):
    """测试运行工具 - 编译、运行、收集结果"""

    name = "test_runner"
    description = "编译和运行测试用例，收集测试结果，验证修复效果"

    class Parameters(BaseModel):
        test_file: str = Field(description="测试文件路径")
        source_file: Optional[str] = Field(
            default=None,
            description="源代码文件路径（用于编译）"
        )
        language: Optional[str] = Field(
            default=None,
            description="语言（自动检测：cpp, python, js）"
        )
        output_binary: Optional[str] = Field(
            default=None,
            description="输出可执行文件路径（用于编译语言）"
        )
        timeout: int = Field(
            default=30,
            description="测试运行超时时间（秒）"
        )
        extra_compile_flags: str = Field(
            default="",
            description="额外的编译标志"
        )
        generate_report: bool = Field(
            default=True,
            description="是否生成详细测试报告"
        )

    def _execute(self, params: Parameters) -> ToolResult:
        test_path = Path(params.test_file)
        if not test_path.exists():
            return ToolResult.error(f"测试文件不存在: {params.test_file}")

        # 检测语言
        language = params.language or self._detect_language(test_path.name)

        # 运行测试
        if language == 'cpp':
            result = self._run_cpp_test(params, test_path)
        elif language == 'python':
            result = self._run_python_test(params, test_path)
        elif language == 'js':
            result = self._run_js_test(params, test_path)
        else:
            return ToolResult.error(f"不支持的语言: {language}")

        return result

    def _detect_language(self, filename: str) -> str:
        """检测文件语言"""
        ext = Path(filename).suffix.lower()
        if ext in ('.cpp', '.cxx', '.cc', '.c', '.h', '.hpp'):
            return 'cpp'
        elif ext in ('.py',):
            return 'python'
        elif ext in ('.js', '.ts', '.jsx', '.tsx'):
            return 'js'
        return 'unknown'

    def _find_msvc_compiler(self) -> Optional[List[str]]:
        """查找 MSVC 编译器路径（支持 VS2019/VS2022 各种版本）"""
        import os
        from pathlib import Path

        # 常见的 VS 安装路径
        vs_paths = [
            # VS2022 Community/Professional/Enterprise
            r'C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC',
            r'C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Tools\MSVC',
            r'C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Tools\MSVC',
            # VS2019 Community/Professional/Enterprise
            r'C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC',
            r'C:\Program Files (x86)\Microsoft Visual Studio\2019\Professional\VC\Tools\MSVC',
            r'C:\Program Files (x86)\Microsoft Visual Studio\2019\Enterprise\VC\Tools\MSVC',
            # Build Tools (独立安装)
            r'C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Tools\MSVC',
            r'C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC',
        ]

        for base_path in vs_paths:
            if not os.path.exists(base_path):
                continue
            # 查找版本号目录（例如 14.29.30133）
            try:
                versions = sorted([d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))], reverse=True)
                if versions:
                    latest_version = versions[0]
                    cl_path = os.path.join(base_path, latest_version, 'bin', 'Hostx64', 'x64', 'cl.exe')
                    if os.path.exists(cl_path):
                        return [cl_path]
            except Exception:
                continue

        # 尝试通过环境变量查找
        vs_tools = os.environ.get('VCToolsInstallDir')
        if vs_tools and os.path.exists(vs_tools):
            cl_path = os.path.join(vs_tools, 'bin', 'Hostx64', 'x64', 'cl.exe')
            if os.path.exists(cl_path):
                return [cl_path]

        return None

    def _detect_cpp_compiler(self) -> Optional[List[str]]:
        """检测可用的 C++ 编译器"""
        # 1. 尝试使用 vswhere 查找 VS 安装位置（VS2017+ 自带）
        try:
            vswhere_paths = [
                r'C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe',
                r'C:\Program Files\Microsoft Visual Studio\Installer\vswhere.exe'
            ]
            for vswhere in vswhere_paths:
                if os.path.exists(vswhere):
                    result = subprocess.run(
                        [vswhere, '-latest', '-products', '*', '-requires', 'Microsoft.VisualStudio.Component.VC.Tools.x86.x64', '-property', 'installationPath'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        install_path = result.stdout.strip()
                        # 查找 MSVC 版本目录
                        msvc_base = os.path.join(install_path, 'VC', 'Tools', 'MSVC')
                        if os.path.exists(msvc_base):
                            versions = sorted([d for d in os.listdir(msvc_base) if os.path.isdir(os.path.join(msvc_base, d))], reverse=True)
                            if versions:
                                cl_path = os.path.join(msvc_base, versions[0], 'bin', 'Hostx64', 'x64', 'cl.exe')
                                if os.path.exists(cl_path):
                                    return [cl_path]
        except Exception:
            pass

        # 2. 尝试直接查找已知的 MSVC 路径
        msvc_compiler = self._find_msvc_compiler()
        if msvc_compiler:
            return msvc_compiler

        # 3. 尝试直接运行 cl（在 VS Developer Command Prompt 环境中）
        try:
            result = subprocess.run(
                ['cl'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 or 'Microsoft' in result.stdout or 'Microsoft' in result.stderr:
                return ['cl']
        except Exception:
            pass

        # 4. 尝试检测 g++/MinGW
        try:
            result = subprocess.run(
                ['g++', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return ['g++']
        except Exception:
            pass

        return None

    def _setup_msvc_env(self, cl_path: str) -> dict:
        """设置 MSVC 编译需要的环境变量"""
        env = os.environ.copy()

        # 从 cl.exe 路径推断 VC Tools 根目录
        # 例如: C:\Program Files (x86)\...\14.29.30133\bin\Hostx64\x64\cl.exe
        cl_path = Path(cl_path)
        # 向上找 4 级到 MSVC 版本目录
        msvc_version_dir = cl_path.parent.parent.parent.parent

        # 找到 Windows SDK 版本
        windows_sdk_includes = [
            r'C:\Program Files (x86)\Windows Kits\10\Include',
            r'C:\Program Files\Windows Kits\10\Include'
        ]

        sdk_include = None
        for sdk_path in windows_sdk_includes:
            if os.path.exists(sdk_path):
                versions = sorted([d for d in os.listdir(sdk_path) if os.path.isdir(os.path.join(sdk_path, d))], reverse=True)
                if versions:
                    sdk_include = os.path.join(sdk_path, versions[0])
                    break

        # 构建 INCLUDE 环境变量
        include_paths = [
            os.path.join(msvc_version_dir, 'include'),
            os.path.join(msvc_version_dir, 'atlmfc', 'include'),
        ]
        if sdk_include:
            include_paths.extend([
                os.path.join(sdk_include, 'ucrt'),
                os.path.join(sdk_include, 'um'),
                os.path.join(sdk_include, 'shared'),
                os.path.join(sdk_include, 'winrt'),
                os.path.join(sdk_include, 'cppwinrt'),
            ])

        # 构建 LIB 环境变量
        lib_paths = [
            os.path.join(msvc_version_dir, 'lib', 'x64'),
            os.path.join(msvc_version_dir, 'atlmfc', 'lib', 'x64'),
        ]
        if sdk_include:
            sdk_lib = sdk_include.replace('Include', 'Lib')
            lib_paths.extend([
                os.path.join(sdk_lib, 'ucrt', 'x64'),
                os.path.join(sdk_lib, 'um', 'x64'),
            ])

        # 构建 PATH 环境变量
        path_additions = [
            str(cl_path.parent),  # cl.exe 所在目录
            str(msvc_version_dir / 'bin' / 'Hostx64' / 'x64'),
        ]

        env['INCLUDE'] = ';'.join([p for p in include_paths if os.path.exists(p)]) + ';' + env.get('INCLUDE', '')
        env['LIB'] = ';'.join([p for p in lib_paths if os.path.exists(p)]) + ';' + env.get('LIB', '')
        env['PATH'] = ';'.join(path_additions) + ';' + env.get('PATH', '')

        return env

    def _run_cpp_test(self, params: Parameters, test_path: Path) -> ToolResult:
        """编译并运行 C/C++ 测试（支持多编译器检测）"""
        output_bin = params.output_binary or f"test_{test_path.stem}.exe"
        compile_errors = []

        # 检测可用的编译器（支持 g++ 和 MSVC cl）
        compiler = self._detect_cpp_compiler()
        if compiler is None:
            # 没有可用编译器，降级模式：只生成测试文件不运行
            report = self._generate_report(
                test_file=str(test_path),
                compile_success=False,
                run_success=False,
                exit_code=-1,
                passed=0,
                total=0,
                output=["未检测到可用编译器（g++ 或 cl）"],
                errors=["请安装 g++ (MinGW) 或 MSVC 编译器以运行测试"]
            )
            report += "\n已降级模式：测试文件已生成但无法编译运行\n"
            report += "提示：请手动编译运行测试，或安装可用编译器\n"
            return ToolResult.ok(
                report,
                test_file=str(test_path),
                compile_success=False,
                compile_skipped=True,
                run_success=False,
                note="降级模式：测试文件已生成，需手动编译运行"
            )

        # 1. 编译准备
        is_msvc = 'cl.exe' in compiler[0].lower() or compiler[0] == 'cl'
        compile_cmd = compiler.copy()
        env = None

        # 使用绝对路径以避免 cwd 导致的路径问题
        test_path_abs = str(test_path.absolute())
        output_bin_abs = str(Path(test_path.parent, output_bin).absolute())
        # 添加测试目录和父目录到 include 路径，以便找到 #include 的源文件
        include_paths = [
            str(test_path.parent.absolute()),
            str(test_path.parent.parent.absolute())
        ]

        if is_msvc:
            # MSVC 编译参数
            if '\\' in compiler[0] or '/' in compiler[0]:  # 完整路径
                env = self._setup_msvc_env(compiler[0])
            compile_cmd.extend(['/EHsc', '/std:c++17', '/nologo'])
            for ip in include_paths:
                compile_cmd.append(f'/I{ip}')
            if params.extra_compile_flags:
                compile_cmd.extend(params.extra_compile_flags.split())
            compile_cmd.extend([test_path_abs, f'/Fe:{output_bin_abs}'])
        else:
            # GCC/MinGW 编译参数
            compile_cmd.extend(['-std=c++17'])
            for ip in include_paths:
                compile_cmd.append(f'-I{ip}')
            if params.extra_compile_flags:
                compile_cmd.extend(params.extra_compile_flags.split())
            compile_cmd.extend(['-o', output_bin_abs, test_path_abs])

        # 如果有源文件且不是 C/C++：添加编译
        # 注意：C/C++ 测试文件通过 #include 直接包含源文件，不需要额外编译
        if params.source_file and Path(params.source_file).exists():
            src_ext = Path(params.source_file).suffix.lower()
            if src_ext not in ('.cpp', '.cxx', '.cc', '.c'):
                source_file_abs = str(Path(params.source_file).absolute())
                if not is_msvc:
                    compile_cmd.insert(-2, source_file_abs)

        try:
            compile_result = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=params.timeout,
                cwd=test_path.parent,
                env=env
            )

            if compile_result.returncode != 0:
                compile_errors = compile_result.stderr.split('\n') if compile_result.stderr else compile_result.stdout.split('\n')
                # 编译失败但测试文件已生成，也算部分成功
                report = self._generate_report(
                    test_file=str(test_path),
                    compile_success=False,
                    run_success=False,
                    exit_code=compile_result.returncode,
                    passed=0,
                    total=0,
                    output=[],
                    errors=compile_errors[:10]
                )
                report += "\n测试文件已生成但编译失败\n"
                report += "提示：可能需要手动调整编译参数或添加头文件\n"
                return ToolResult.ok(
                    report,
                    test_file=str(test_path),
                    compile_success=False,
                    run_success=False,
                    note="测试文件已生成，编译失败需手动检查"
                )

        except subprocess.TimeoutExpired:
            return ToolResult.error(
                "编译超时！",
                compile_success=False
            )

        # 2. 运行测试
        try:
            run_result = subprocess.run(
                [output_bin_abs],
                capture_output=True,
                text=True,
                timeout=params.timeout,
                cwd=test_path.parent
            )

            run_output = run_result.stdout.split('\n')
            run_errors = run_result.stderr.split('\n')

            # 解析测试结果
            passed, total = self._parse_test_output(run_output)

            report = self._generate_report(
                test_file=str(test_path),
                compile_success=True,
                run_success=run_result.returncode in [0, 1],
                exit_code=run_result.returncode,
                passed=passed,
                total=total,
                output=run_output[:50],  # 限制输出行数
                errors=run_errors if run_result.stderr else None
            )

            detailed_results = self._parse_detailed_test_results(run_output)

            return ToolResult.ok(
                report,
                test_file=str(test_path),
                compile_success=True,
                run_success=run_result.returncode in [0, 1],
                exit_code=run_result.returncode,
                tests_passed=passed,
                tests_total=total,
                tests_failed=total - passed if total else 0,
                pass_rate=f"{(passed/total*100):.1f}%" if total else "N/A",
                detailed_results=detailed_results,
                test_output=run_output
            )

        except subprocess.TimeoutExpired:
            return ToolResult.error(
                "测试运行超时！",
                compile_success=True,
                run_success=False
            )

    def _run_python_test(self, params: Parameters, test_path: Path) -> ToolResult:
        """运行 Python 测试"""
        try:
            result = subprocess.run(
                ['python', str(test_path.name)],
                capture_output=True,
                text=True,
                timeout=params.timeout,
                cwd=test_path.parent
            )

            # unittest 将输出打印到 stderr
            output = result.stdout.split('\n') + result.stderr.split('\n')
            errors = result.stderr.split('\n')

            # 解析 unittest 输出
            passed = 0
            failed = 0
            total = 0

            for line in output:
                # unittest 格式: "test_xxx (...) ... ok/FAIL/ERROR"
                if line.strip().endswith(' ... ok'):
                    passed += 1
                elif line.strip().endswith(' ... FAIL') or line.strip().endswith(' ... ERROR'):
                    failed += 1
                # 最后一行汇总: "Ran X tests"
                elif line.startswith('Ran ') and 'tests' in line:
                    try:
                        total = int(line.split()[1])
                    except:
                        pass

            # 如果解析到总数，用总数
            if total == 0:
                total = passed + failed

            report = self._generate_report(
                test_file=str(test_path),
                compile_success=True,
                run_success=True,
                exit_code=result.returncode,
                passed=passed,
                total=total,
                output=output[:50],
                errors=errors if result.stderr else None
            )

            return ToolResult.ok(
                report,
                test_file=str(test_path),
                compile_success=True,  # Python 不需要编译，默认为成功
                run_success=True,
                tests_passed=passed,
                tests_total=total,
                tests_failed=failed,
                pass_rate=f"{(passed/total*100):.1f}%" if total else "N/A",
                test_output=output
            )

        except subprocess.TimeoutExpired:
            return ToolResult.error("测试运行超时！")

    def _run_js_test(self, params: Parameters, test_path: Path) -> ToolResult:
        """运行 JavaScript 测试"""
        try:
            result = subprocess.run(
                ['node', str(test_path.name)],
                capture_output=True,
                text=True,
                timeout=params.timeout,
                cwd=test_path.parent
            )

            output = result.stdout.split('\n')

            report = self._generate_report(
                test_file=str(test_path),
                compile_success=True,
                run_success=True,
                exit_code=result.returncode,
                passed=0,
                total=0,
                output=output[:50]
            )

            return ToolResult.ok(
                report,
                test_file=str(test_path),
                output=output[:50]
            )

        except subprocess.TimeoutExpired:
            return ToolResult.error("测试运行超时！")

    def _parse_test_output(self, output: List[str]) -> tuple:
        """解析测试输出，统计通过数和总数"""
        passed = 0
        total = 0

        for line in output:
            if '[PASS]' in line or 'OK' in line or '✅' in line:
                passed += 1
                total += 1
            elif '[FAIL]' in line or 'FAILED' in line or '❌' in line:
                total += 1
            elif 'SUMMARY:' in line and 'tests total' in line:
                # 解析 "SUMMARY: 23 tests total, 23 passed" 格式
                try:
                    parts = line.split('SUMMARY:')[1].strip().split(',')
                    total_str = parts[0].strip()
                    passed_str = parts[1].strip() if len(parts) > 1 else ''
                    total = int(total_str.split()[0])
                    passed = int(passed_str.split()[0]) if 'passed' in passed_str else 0
                except:
                    pass
            elif 'passed' in line.lower() and '/' in line:
                # 解析 "1/2 passed" 格式
                parts = line.replace('passed', '').strip().split('/')
                if len(parts) == 2:
                    try:
                        passed = int(parts[0])
                        total = int(parts[1])
                    except:
                        pass

        return passed, total

    def _parse_detailed_test_results(self, output: List[str]) -> List[Dict[str, Any]]:
        """解析详细的测试用例结果"""
        test_results = []
        current_test = None

        # 首先收集所有测试名称
        test_names = []
        for line in output:
            if line.strip().startswith('[TEST]'):
                test_name = line.strip().split('[TEST]')[1].strip()
                test_names.append(test_name)

        # 然后收集所有结果
        test_idx = 0
        for line in output:
            line = line.strip()
            if not line:
                continue

            if '[PASS]' in line:
                test_name = test_names[test_idx] if test_idx < len(test_names) else f'Test_{test_idx}'
                test_idx += 1
                test_results.append({
                    'name': test_name,
                    'status': 'PASS',
                    'reason': '测试执行成功，断言通过',
                    'impact': '无'
                })
            elif '[FAIL]' in line:
                test_name = test_names[test_idx] if test_idx < len(test_names) else f'Test_{test_idx}'
                test_idx += 1
                test_results.append({
                    'name': test_name,
                    'status': 'FAIL',
                    'reason': '测试执行失败',
                    'impact': self._assess_impact(test_name)
                })

        return test_results

    def _assess_impact(self, test_name: str) -> str:
        """评估测试失败的影响范围"""
        test_name_lower = test_name.lower()
        if 'thread' in test_name_lower or 'pool' in test_name_lower:
            return '高 - 影响并发任务执行能力，可能导致系统卡死或任务丢失'
        elif 'enqueue' in test_name_lower or 'submit' in test_name_lower:
            return '高 - 影响任务提交功能，新任务无法加入队列'
        elif 'count' in test_name_lower or 'size' in test_name_lower:
            return '中 - 影响状态查询，可能导致监控和调试信息不准确'
        elif 'leak' in test_name_lower or 'memory' in test_name_lower:
            return '中 - 内存泄漏，长时间运行可能导致内存耗尽'
        elif 'init' in test_name_lower or 'constructor' in test_name_lower:
            return '高 - 初始化失败，整个模块无法使用'
        elif 'function' in test_name_lower:
            return '中 - 单个功能函数失败，影响相关业务逻辑'
        else:
            return '中 - 需进一步分析失败原因'


    def _generate_report(self, test_file: str, compile_success: bool,
                        run_success: bool, exit_code: int,
                        passed: int, total: int, output: List[str],
                        errors: Optional[List[str]] = None) -> str:
        """生成测试报告"""
        report = "=" * 60 + "\n"
        report += "🧪 TestRunnerTool - 测试运行报告\n"
        report += "=" * 60 + "\n\n"

        report += f"📄 测试文件: {test_file}\n"
        report += f"🔧 编译状态: {'✅ 成功' if compile_success else '❌ 失败'}\n"

        if compile_success:
            report += f"🏃 运行状态: {'✅ 完成' if run_success else '❌ 异常'}\n"
            report += f"📊 退出码: {exit_code}\n\n"

            if total > 0:
                pass_rate = (passed / total * 100) if total else 0
                report += "📈 测试结果统计:\n"
                report += f"  - 总测试数: {total}\n"
                report += f"  - 通过: {passed} ✅\n"
                report += f"  - 失败: {total - passed} ❌\n"
                report += f"  - 通过率: {pass_rate:.1f}%\n\n"

                if pass_rate >= 80:
                    report += "✅ 测试结果良好！\n\n"
                elif pass_rate >= 50:
                    report += "⚠️ 部分测试失败，建议检查\n\n"
                else:
                    report += "❌ 多数测试失败，需要重点检查修复！\n\n"
            else:
                report += "ℹ️  未检测到测试统计信息\n\n"

            if output and any(line.strip() for line in output[:20]):
                report += "📝 测试输出（前20行）:\n"
                for line in output[:20]:
                    if line.strip():
                        report += f"  {line}\n"
                report += "\n"

            if errors and any(line.strip() for line in errors):
                report += "⚠️ 错误输出:\n"
                for line in errors[:10]:
                    if line.strip():
                        report += f"  {line}\n"
                report += "\n"

        return report
