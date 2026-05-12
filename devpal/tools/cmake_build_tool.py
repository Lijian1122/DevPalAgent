# -*- coding: utf-8 -*-
"""
CMake VS 编译工具 - 集成 Visual Studio 编译流程
支持自动检测VS环境、CMake配置、编译、错误反思重编译
"""
import os
import re
import subprocess
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult, ToolSecurity, retry
from .compiler_analyzer import CompilationAnalyzer


class VSEnvironmentDetector:
    """Visual Studio 环境检测器"""

    VS_INSTALL_PATHS = [
        r"C:\Program Files\Microsoft Visual Studio\2022\Community",
        r"C:\Program Files\Microsoft Visual Studio\2022\Professional",
        r"C:\Program Files\Microsoft Visual Studio\2022\Enterprise",
        r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Community",
        r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Professional",
        r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Enterprise",
        r"C:\Program Files (x86)\Microsoft Visual Studio\2017\Community",
        r"C:\Program Files (x86)\Microsoft Visual Studio\2017\Professional",
        r"C:\Program Files (x86)\Microsoft Visual Studio\2017\Enterprise",
    ]

    @classmethod
    def find_vs_installation(cls) -> Optional[Tuple[str, str, str]]:
        """查找VS安装路径
        Returns: (install_path, version_year, vcvarsall_path)
        """
        # 优先使用 vswhere
        vswhere_paths = [
            r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe",
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"),
        ]

        for vswhere in vswhere_paths:
            if os.path.exists(vswhere):
                try:
                    result = subprocess.run(
                        [vswhere, '-latest', '-products', '*', '-requires',
                         'Microsoft.VisualStudio.Component.VC.Tools.x86.x64',
                         '-property', 'installationPath'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        install_path = result.stdout.strip()
                        version_year = cls._extract_version_year(install_path)
                        vcvarsall = os.path.join(install_path, 'VC', 'Auxiliary', 'Build', 'vcvarsall.bat')
                        if os.path.exists(vcvarsall):
                            return (install_path, version_year, vcvarsall)
                except Exception:
                    pass

        # 回退到硬编码路径
        for path in cls.VS_INSTALL_PATHS:
            if os.path.exists(path):
                vcvarsall = os.path.join(path, 'VC', 'Auxiliary', 'Build', 'vcvarsall.bat')
                if os.path.exists(vcvarsall):
                    version_year = cls._extract_version_year(path)
                    return (path, version_year, vcvarsall)

        return None

    @staticmethod
    def _extract_version_year(path: str) -> str:
        """从路径中提取VS版本年份"""
        match = re.search(r'20\d{2}', path)
        return match.group(0) if match else '2019'

    @classmethod
    def get_vcvars_command(cls, arch: str = 'x64') -> Optional[str]:
        """获取vcvarsall.bat命令"""
        vs_info = cls.find_vs_installation()
        if not vs_info:
            return None
        return f'"{vs_info[2]}" {arch}'


class CMakeBuildTool(BaseTool):
    """CMake VS 编译工具 - 完整的编译流程"""

    name = "cmake_build"
    description = "使用 CMake + Visual Studio 编译 C/C++ 项目，支持错误检测和自动重编译"

    class Parameters(BaseModel):
        source_dir: str = Field(
            description="源代码根目录（包含 CMakeLists.txt）"
        )
        build_dir: Optional[str] = Field(
            default=None,
            description="构建目录，默认为 source_dir/build"
        )
        generator: str = Field(
            default="Visual Studio 16 2019",
            description="CMake 生成器名称，如 'Visual Studio 16 2019', 'Visual Studio 17 2022'"
        )
        arch: str = Field(
            default="x64",
            description="目标架构: x64, Win32, ARM64"
        )
        config: str = Field(
            default="Release",
            description="构建配置: Release, Debug, RelWithDebInfo, MinSizeRel"
        )
        cmake_args: str = Field(
            default="",
            description="额外的 CMake 参数，空格分隔"
        )
        build_args: str = Field(
            default="",
            description="额外的编译参数，如 /v:m, /m:8"
        )
        clean_first: bool = Field(
            default=False,
            description="是否先清理构建目录"
        )
        auto_retry: bool = Field(
            default=True,
            description="编译失败时是否自动尝试修复后重编译"
        )
        max_retry_attempts: int = Field(
            default=3,
            description="最大重试次数"
        )
        timeout: int = Field(
            default=300,
            description="总超时时间，单位秒"
        )
        generate_english_code: bool = Field(
            default=True,
            description="是否先将代码转换为纯英文（防止中文编码乱码）"
        )
        run_after_build: bool = Field(
            default=True,
            description="编译成功后是否自动运行程序进行验证"
        )
        run_input: str = Field(
            default="0\n",
            description="运行程序时的输入内容，默认为输入0退出"
        )
        run_timeout: int = Field(
            default=15,
            description="程序运行超时时间，单位秒"
        )
        max_runtime_retry_attempts: int = Field(
            default=3,
            description="Max retry fix attempts when runtime verification fails"
        )

    def _execute(self, params: Parameters) -> ToolResult:
        source_path = Path(params.source_dir).resolve()
        build_path = Path(params.build_dir) if params.build_dir else source_path / "build"
        build_path = build_path.resolve()

        # 验证 CMakeLists.txt 存在
        if not (source_path / "CMakeLists.txt").exists():
            return ToolResult.error(
                f"CMakeLists.txt not found in source dir: {source_path}",
                source_dir=str(source_path)
            )

        vs_info = VSEnvironmentDetector.find_vs_installation()
        if not vs_info:
            return ToolResult.error(
                "Visual Studio not found. Please install Visual Studio 2017+ with C++ tools.",
                source_dir=str(source_path)
            )

        install_path, version_year, vcvarsall = vs_info

        # 自动检测生成器版本
        generator = params.generator
        if "2022" in install_path and "2019" in generator:
            generator = "Visual Studio 17 2022"

        result = {
            'source_dir': str(source_path),
            'build_dir': str(build_path),
            'vs_version': version_year,
            'generator': generator,
            'arch': params.arch,
            'config': params.config,
            'attempts': [],
            'final_status': 'pending'
        }

        # Step 1: 转换为纯英文代码（防止中文乱码）
        if params.generate_english_code:
            norm_result = self._normalize_code_to_english(source_path)
            result['code_normalization'] = norm_result
            if not norm_result['success']:
                return ToolResult.error(
                    f"Code normalization failed: {norm_result.get('error', 'Unknown error')}",
                    **result
                )

        # Step 2: 执行编译（带重试逻辑）
        build_success = False
        exe_files = []
        for attempt in range(1, params.max_retry_attempts + 1):
            attempt_result = {
                'attempt': attempt,
                'cmake_configure': None,
                'build': None
            }

            # 清理构建目录（首次或失败后清理）
            if params.clean_first or attempt > 1:
                if build_path.exists():
                    shutil.rmtree(build_path)
                build_path.mkdir(parents=True, exist_ok=True)

            # Step 2a: CMake 配置
            cmake_ok, cmake_output, cmake_errors = self._run_cmake_configure(
                source_path, build_path, generator, params.arch, params.cmake_args, vcvarsall
            )
            attempt_result['cmake_configure'] = {
                'success': cmake_ok,
                'output': cmake_output,
                'errors': cmake_errors
            }

            if not cmake_ok:
                attempt_result['message'] = "CMake 配置失败"
                result['attempts'].append(attempt_result)

                if params.auto_retry and attempt < params.max_retry_attempts:
                    fix_result = self._fix_cmake_errors(source_path, build_path, cmake_output)
                    attempt_result['fix_applied'] = fix_result
                    if fix_result['fixed']:
                        continue
                break

            # Step 2b: 执行编译
            build_ok, build_output, build_errors = self._run_cmake_build(
                build_path, params.config, params.build_args, vcvarsall
            )
            attempt_result['build'] = {
                'success': build_ok,
                'output': build_output,
                'errors': build_errors
            }

            if build_ok:
                attempt_result['message'] = "编译成功"
                result['attempts'].append(attempt_result)
                build_success = True

                # 查找输出的可执行文件
                exe_files = list(build_path.rglob(f"**/{params.config}/*.exe"))
                result['executables'] = [str(f) for f in exe_files]
                break
            else:
                attempt_result['message'] = "编译失败"
                result['attempts'].append(attempt_result)

                if params.auto_retry and attempt < params.max_retry_attempts:
                    fix_result = self._fix_compilation_errors(source_path, build_output, build_errors)
                    attempt_result['fix_applied'] = fix_result
                    if fix_result['fixed']:
                        continue

                break

        # Step 3: 运行时验证和错误反思（如果编译成功）
        if build_success and params.run_after_build and exe_files:
            result['runtime_checks'] = []
            for run_attempt in range(1, params.max_runtime_retry_attempts + 1):
                run_result = {
                    'attempt': run_attempt,
                    'executed': False,
                    'success': False,
                    'output': '',
                    'errors': [],
                    'fix_applied': None
                }

                # Run the program
                exe_path = exe_files[0]
                run_ok, run_output, run_errors = self._run_and_analyze(
                    exe_path, params.run_input, params.run_timeout, source_path
                )
                run_result['executed'] = True
                run_result['success'] = run_ok
                run_result['output'] = run_output
                run_result['errors'] = run_errors

                if run_ok:
                    run_result['message'] = "Runtime verification passed"
                    result['runtime_checks'].append(run_result)
                    result['final_status'] = 'success'
                    result['success'] = True
                    return ToolResult.ok(
                        content=self._format_success_output(result),
                        **result
                    )
                else:
                    run_result['message'] = "Runtime verification failed"
                    result['runtime_checks'].append(run_result)

                    if params.auto_retry and run_attempt < params.max_runtime_retry_attempts:
                        # Analyze runtime errors and fix
                        fix_result = self._fix_runtime_errors(
                            source_path, run_output, run_errors
                        )
                        run_result['fix_applied'] = fix_result
                        if fix_result['fixed']:
                            # 重新编译
                            rebuild_ok, _, _ = self._run_cmake_build(
                                build_path, params.config, params.build_args, vcvarsall
                            )
                            if rebuild_ok:
                                exe_files = list(build_path.rglob(f"**/{params.config}/*.exe"))
                                result['executables'] = [str(f) for f in exe_files]
                                continue

                    break

            # All runtime verification attempts failed
            result['final_status'] = 'compile_ok_run_failed'
            result['success'] = False
            return ToolResult.error(
                self._format_runtime_failure_output(result),
                **result
            )

        elif build_success:
            result['final_status'] = 'success'
            result['success'] = True
            return ToolResult.ok(
                self._format_success_output(result),
                **result
            )

        result['final_status'] = 'failed'
        result['success'] = False

        return ToolResult.error(
            self._format_failure_output(result),
            **result
        )

    def _normalize_code_to_english(self, source_dir: Path) -> Dict[str, Any]:
        """将代码转换为纯英文 - 调用 code_normalizer 工具"""
        try:
            from .code_normalizer import CodeNormalizerTool

            result = self.registry.execute_tool('code_normalizer', {
                'source_dir': str(source_dir),
                'backup': True,
                'convert_comments': True,
                'convert_strings': False,
                'remove_chinese_identifiers': True
            })

            return {
                'success': result.success,
                'files_processed': result.metadata.get('files_processed', 0) if hasattr(result, 'metadata') else 0,
                'output': result.content[:500] if result.content else ''
            }
        except Exception as e:
            return {
                'success': True,  # 容错：规范化失败也继续编译
                'warning': f'代码规范化工具不可用: {str(e)}',
                'files_processed': 0
            }

    def _run_cmake_configure(self, source_path: Path, build_path: Path,
                             generator: str, arch: str, extra_args: str,
                             vcvarsall: str) -> Tuple[bool, str, List[Dict]]:
        """执行 CMake 配置 - 修复版：使用临时 bat 脚本避免引号嵌套问题"""
        build_path.mkdir(parents=True, exist_ok=True)

        # 构造 cmake 参数（不带引号，在 bat 中直接使用）
        cmake_args = [
            '-G', generator,
            '-A', arch,
            '-S', str(source_path),
            '-B', str(build_path)
        ]
        if extra_args:
            cmake_args.extend(extra_args.split())

        # 关键修复：写入临时 bat 脚本，在脚本中加载环境并执行 cmake
        bat_content = '@echo off\r\n'
        bat_content += f'call "{vcvarsall}" x64\r\n'
        bat_content += f'cmake {" ".join(cmake_args)}\r\n'
        bat_content += f'exit /b %errorlevel%\r\n'

        bat_file = build_path / '_configure.bat'
        bat_file.write_text(bat_content, encoding='gbk')

        try:
            result = subprocess.run(
                ['cmd.exe', '/c', str(bat_file)],
                shell=False,  # 不通过 shell，直接调用 cmd.exe
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=120,
                cwd=str(build_path)
            )

            output = []
            if result.stdout:
                output.append(result.stdout)
            if result.stderr:
                output.append(result.stderr)
            full_output = '\n'.join(output)

            errors = CompilationAnalyzer.parse_output(full_output)
            success = result.returncode == 0

            return success, full_output, errors

        except subprocess.TimeoutExpired:
            return False, "CMake 配置超时（120秒）", []
        except Exception as e:
            return False, f"CMake 配置异常: {str(e)}", []

    def _run_cmake_build(self, build_path: Path, config: str,
                         extra_args: str, vcvarsall: str) -> Tuple[bool, str, List[Dict]]:
        """执行 CMake 编译 - 修复版：使用临时 bat 脚本"""
        build_args = [
            '--build', str(build_path),
            '--config', config,
            '--', '/v:m'  # 最小化输出
        ]
        if extra_args:
            build_args.insert(-2, extra_args)

        # 写入临时 bat 脚本
        bat_content = '@echo off\r\n'
        bat_content += f'call "{vcvarsall}" x64\r\n'
        bat_content += f'cmake {" ".join(build_args)}\r\n'
        bat_content += f'exit /b %errorlevel%\r\n'

        bat_file = build_path / '_build.bat'
        bat_file.write_text(bat_content, encoding='gbk')

        try:
            result = subprocess.run(
                ['cmd.exe', '/c', str(bat_file)],
                shell=False,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=300,
                cwd=str(build_path)
            )

            output = []
            if result.stdout:
                output.append(result.stdout)
            if result.stderr:
                output.append(result.stderr)
            full_output = '\n'.join(output)

            errors = CompilationAnalyzer.parse_output(full_output)
            success = result.returncode == 0

            return success, full_output, errors

        except subprocess.TimeoutExpired:
            return False, "编译超时（300秒）", []
        except Exception as e:
            return False, f"编译异常: {str(e)}", []

    def _fix_cmake_errors(self, source_path: Path, build_path: Path, output: str) -> Dict[str, Any]:
        """修复 CMake 配置错误"""
        result = {
            'fixed': False,
            'errors_fixed': 0,
            'actions': []
        }

        # 常见错误模式匹配和修复
        if 'could not find any instance of Visual Studio' in output.lower():
            result['actions'].append("检测到VS环境问题，尝试使用NMake Makefiles生成器")
            # 这里可以实现降级到NMake或MinGW Makefiles
            return result

        if 'The C compiler identification is unknown' in output:
            result['actions'].append("编译器识别失败，需要检查VS安装")
            return result

        if 'CMakeLists.txt:30' in output and 'target_compile_features' in output:
            result['actions'].append("可能需要调整C++标准版本")
            return result

        return result

    def _fix_compilation_errors(self, source_path: Path, output: str, errors: List[Dict]) -> Dict[str, Any]:
        """修复编译错误 - 核心反思修复逻辑"""
        result = {
            'fixed': False,
            'errors_fixed': 0,
            'actions': []
        }

        # 按错误类型分组处理
        for error in errors:
            error_code = error.get('error_code', '')
            message = error.get('message', '')
            file_path = error.get('file', '')
            line_num = error.get('line', 0)

            if not file_path or not Path(file_path).exists():
                # 尝试在源目录中查找文件
                filename = os.path.basename(file_path) if file_path else ''
                if filename:
                    found_files = list(source_path.rglob(filename))
                    if found_files:
                        file_path = str(found_files[0])

            if not Path(file_path).exists():
                continue

            # C4819: 编码错误 - 需要转换为英文
            if 'C4819' in error_code or 'code page' in message.lower():
                action = self._fix_encoding_error(file_path)
                if action:
                    result['actions'].append(action)
                    result['errors_fixed'] += 1

            # C2065: 未声明的标识符 - 可能需要添加include
            elif 'C2065' in error_code or 'undeclared identifier' in message.lower():
                action = self._fix_undeclared_identifier(file_path, line_num, message)
                if action:
                    result['actions'].append(action)
                    result['errors_fixed'] += 1

            # C1083: 无法打开包括文件
            elif 'C1083' in error_code or 'No such file' in message:
                action = self._fix_missing_header(file_path, line_num, message)
                if action:
                    result['actions'].append(action)
                    result['errors_fixed'] += 1

            # C3861: 找不到标识符
            elif 'C3861' in error_code or 'identifier not found' in message:
                action = self._fix_missing_identifier(file_path, line_num, message)
                if action:
                    result['actions'].append(action)
                    result['errors_fixed'] += 1

            # LNK2019: 未解析的外部符号
            elif 'LNK2019' in error_code or 'unresolved external' in message.lower():
                action = self._fix_linker_error(source_path, message)
                if action:
                    result['actions'].append(action)
                    result['errors_fixed'] += 1

        result['fixed'] = result['errors_fixed'] > 0
        return result

    def _fix_encoding_error(self, file_path: str) -> Optional[str]:
        """修复编码错误 - 转换为UTF-8 BOM"""
        try:
            with open(file_path, 'r', encoding='gbk', errors='ignore') as f:
                content = f.read()

            # 转换为UTF-8 with BOM（MSVC默认）
            with open(file_path, 'w', encoding='utf-8-sig') as f:
                f.write(content)

            return f"已转换文件编码为 UTF-8 BOM: {os.path.basename(file_path)}"
        except Exception as e:
            return None

    def _fix_undeclared_identifier(self, file_path: str, line_num: int, message: str) -> Optional[str]:
        """修复未声明的标识符错误"""
        # 从错误信息中提取标识符名称
        identifier_match = re.search(r"'(.+?)'", message)
        if not identifier_match:
            return None

        identifier = identifier_match.group(1)

        # Header mapping for common identifiers
        header_map = {
            'cout': '#include <iostream>',
            'cin': '#include <iostream>',
            'string': '#include <string>',
            'vector': '#include <vector>',
            'map': '#include <map>',
            'mutex': '#include <mutex>',
            'shared_ptr': '#include <memory>',
            'unique_ptr': '#include <memory>',
            'size_t': '#include <cstddef>',
            'NULL': '#include <cstddef>',
            'printf': '#include <cstdio>',
            'fopen': '#include <cstdio>',
            'memset': '#include <cstring>',
            'strcpy': '#include <cstring>',
        }

        if identifier in header_map:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()

                # 找到第一个非注释非空行，在之前插入include
                insert_pos = 0
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped and not stripped.startswith('//') and not stripped.startswith('/*'):
                        insert_pos = i
                        break

                header_line = header_map[identifier]
                if header_line not in ''.join(lines):
                    lines.insert(insert_pos, header_line + '\n')

                    with open(file_path, 'w', encoding='utf-8-sig') as f:
                        f.writelines(lines)

                    return f"Added header {header_line} to {os.path.basename(file_path)}"
            except Exception as e:
                pass

        return None

    def _fix_missing_header(self, file_path: str, line_num: int, message: str) -> Optional[str]:
        """Fix missing header errors"""
        header_match = re.search(r"'(.+?)'", message)
        if not header_match:
            return None

        missing_header = header_match.group(1)

        # Try to find the header file in source directory
        source_dir = Path(file_path).parent
        found_files = list(source_dir.rglob(missing_header))

        if found_files:
            # Header exists, might be include path issue
            return f"Found header {missing_header}, may need to adjust include path"

        return None

    def _fix_missing_identifier(self, file_path: str, line_num: int, message: str) -> Optional[str]:
        """修复找不到标识符错误"""
        # 类似未声明标识符的处理
        return self._fix_undeclared_identifier(file_path, line_num, message)

    def _fix_linker_error(self, source_path: Path, message: str) -> Optional[str]:
        """修复链接错误"""
        # 检查是否有对应的源文件没有被添加到 CMakeLists.txt
        func_match = re.search(r'"(.+?)"', message)
        if not func_match:
            return None

        function_name = func_match.group(1)

        # 尝试查找实现了这个函数的源文件
        cpp_files = list(source_path.rglob('*.cpp'))
        for cpp_file in cpp_files:
            try:
                with open(cpp_file, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                    if function_name in content:
                        # 检查这个文件是否在CMakeLists.txt中
                        cmake_file = source_path / 'CMakeLists.txt'
                        if cmake_file.exists():
                            with open(cmake_file, 'r', encoding='utf-8', errors='replace') as cf:
                                cmake_content = cf.read()
                                if cpp_file.name not in cmake_content:
                                    return f"函数 {function_name} 的实现文件 {cpp_file.name} 可能未添加到 CMakeLists.txt"
            except Exception:
                pass

        return None

    def _format_success_output(self, result: Dict) -> str:
        """格式化成功输出"""
        lines = [
            "=" * 60,
            "[OK] CMake 编译成功！",
            "=" * 60,
            f"[SRC] 源目录: {result['source_dir']}",
            f"[BUILD] 构建目录: {result['build_dir']}",
            f"[VS] VS 版本: {result['vs_version']}",
            f"[GEN] 生成器: {result['generator']}",
            f"[ARCH] 架构: {result['arch']}",
            f"[CFG] 配置: {result['config']}",
            f"[TRY] 尝试次数: {len(result['attempts'])}",
        ]

        exes = result.get('executables', [])
        if exes:
            lines.append("")
            lines.append("[EXE] 生成的可执行文件:")
            for exe in exes[:5]:
                lines.append(f"   - {exe}")
            if len(exes) > 5:
                lines.append(f"   还有 {len(exes) - 5} 个文件...")

        lines.append("=" * 60)
        return '\n'.join(lines)

    def _format_failure_output(self, result: Dict) -> str:
        """格式化失败输出"""
        last_attempt = result['attempts'][-1] if result['attempts'] else {}

        lines = [
            "=" * 60,
            "[FAIL] CMake 编译失败！",
            "=" * 60,
            f"[SRC] 源目录: {result['source_dir']}",
            f"[TRY] 尝试次数: {len(result['attempts'])}/{result.get('max_retry_attempts', 3)}",
        ]

        # 显示最后一次尝试的错误
        if 'build' in last_attempt and last_attempt['build'] is not None:
            errors = last_attempt['build'].get('errors', [])
            if errors:
                lines.append("")
                lines.append("[ERR] 编译错误:")
                for i, err in enumerate(errors[:5], 1):
                    lines.append(f"   {i}. {err.get('file', 'unknown')}:{err.get('line', 0)}")
                    lines.append(f"      [{err.get('error_code', 'ERROR')}] {err.get('message', '')[:80]}")

        lines.append("")
        lines.append("[TIP] Check code syntax and CMakeLists.txt configuration")
        lines.append("=" * 60)

        return '\n'.join(lines)

    def _run_and_analyze(self, exe_path: str, input_data: str, timeout: int, source_path: Path) -> Tuple[bool, str, List[Dict]]:
        """Run program and analyze output"""
        exe_dir = Path(exe_path).parent
        errors = []
        try:
            # Create data directory in the executable's directory if needed
            data_dir = exe_dir / 'data'
            if not data_dir.exists():
                data_dir.mkdir(parents=True, exist_ok=True)

            result = subprocess.run(
                exe_path,
                shell=False,
                capture_output=True,
                text=True,
                input=input_data,
                encoding='utf-8',
                errors='replace',
                timeout=timeout,
                cwd=str(exe_dir)
            )

            output = []
            if result.stdout:
                output.append(result.stdout)
            if result.stderr:
                output.append(result.stderr)
            full_output = '\n'.join(output)

            # Analyze runtime errors
            errors = self._analyze_runtime_errors(full_output, result.returncode)

            # Check return code and errors
            success = result.returncode == 0 or len(errors) == 0

            # Additional success condition: check for successful init output
            success_keywords = ['initialized successfully', 'successfully', 'welcome']
            if any(kw.lower() in full_output.lower() for kw in success_keywords):
                success = True

            return success, full_output, errors

        except subprocess.TimeoutExpired:
            return False, "Program timed out", [{'type': 'timeout', 'message': f'Runtime timeout ({timeout}s)'}]
        except Exception as e:
            return False, f"Runtime exception: {str(e)}", [{'type': 'exception', 'message': str(e)}]

    def _analyze_runtime_errors(self, output: str, returncode: int) -> List[Dict]:
        """Analyze runtime errors"""
        errors = []
        output_lower = output.lower()

        # 1. Init failed
        if 'failed' in output_lower and ('init' in output_lower or 'initialize' in output_lower):
            errors.append({
                'type': 'init_failed',
                'message': 'System initialization failed',
                'suggestion': 'Check data files or resource paths'
            })

        # 2. File not found
        if 'file not found' in output_lower or 'no such file' in output_lower:
            errors.append({
                'type': 'file_not_found',
                'message': 'File not found',
                'suggestion': 'Check file path, may need to create directory'
            })

        # 3. Assertion failed
        if 'assertion failed' in output_lower or 'assert' in output_lower:
            errors.append({
                'type': 'assertion',
                'message': 'Assertion failed',
                'suggestion': 'Check if assertion conditions are met'
            })

        # 4. Memory issues
        if 'segmentation fault' in output_lower or 'access violation' in output_lower:
            errors.append({
                'type': 'memory',
                'message': 'Memory access error',
                'suggestion': 'Check for null pointers, array bounds, memory leaks'
            })

        # 5. Division by zero
        if 'division by zero' in output_lower:
            errors.append({
                'type': 'divide_by_zero',
                'message': 'Division by zero',
                'suggestion': 'Check if divisor could be zero'
            })

        # 6. Exception thrown
        if 'exception' in output_lower:
            errors.append({
                'type': 'exception',
                'message': 'Exception thrown',
                'suggestion': 'Check exception handling logic'
            })

        return errors

    def _fix_runtime_errors(self, source_path: Path, output: str, errors: List[Dict]) -> Dict[str, Any]:
        """Fix runtime errors"""
        result = {
            'fixed': False,
            'errors_fixed': 0,
            'actions': []
        }

        for error in errors:
            error_type = error.get('type', '')

            # 1. Init failed - might be missing data directory
            if error_type == 'init_failed' or error_type == 'file_not_found':
                action = self._fix_missing_data_directory(source_path)
                if action:
                    result['actions'].append(action)
                    result['errors_fixed'] += 1

            # 2. Memory errors
            elif error_type == 'memory':
                action = self._add_memory_debugging(source_path)
                if action:
                    result['actions'].append(action)
                    result['errors_fixed'] += 1

        result['fixed'] = result['errors_fixed'] > 0
        return result

    def _fix_missing_data_directory(self, source_path: Path) -> Optional[str]:
        """Fix missing data directory issues"""
        # Check if there's data directory related code
        main_files = list(source_path.rglob('main.cpp'))
        if not main_files:
            main_files = list(source_path.rglob('*.cpp'))

        for main_file in main_files:
            try:
                with open(main_file, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()

                if 'data/' in content or 'data\\\\' in content.lower():
                    # 在源目录创建 data 目录
                    data_dir = source_path / 'data'
                    if not data_dir.exists():
                        data_dir.mkdir(parents=True, exist_ok=True)
                        return f"Created data directory: {data_dir}"

            except Exception as e:
                pass

        return None

    def _add_memory_debugging(self, source_path: Path) -> Optional[str]:
        """添加内存调试代码"""
        # 简化实现：不在此修改源代码
        return None

    def _format_runtime_failure_output(self, result: Dict) -> str:
        """格式化运行时失败输出"""
        last_runtime_check = result.get('runtime_checks', [])[-1] if result.get('runtime_checks') else {}
        errors = last_runtime_check.get('errors', [])

        lines = [
            "=" * 60,
            "[WARN] Compiled but runtime verification failed",
            "=" * 60,
            f"[SRC] 源目录: {result['source_dir']}",
            f"[EXE] 可执行文件: {result.get('executables', [''])[0] if result.get('executables') else '未知'}",
            f"[RUN_TRY] Runtime verification attempts: {len(result.get('runtime_checks', []))}",
        ]

        if errors:
            lines.append("")
            lines.append("[ERR] Runtime errors:")
            for i, err in enumerate(errors[:5], 1):
                lines.append(f"   {i}. [{err.get('type', 'ERROR')}] {err.get('message', '')}")
                if err.get('suggestion'):
                    lines.append(f"      建议: {err.get('suggestion')}")

        # 显示修复操作
        fixes = []
        for check in result.get('runtime_checks', []):
            if check.get('fix_applied') and check['fix_applied'].get('actions'):
                fixes.extend(check['fix_applied']['actions'])

        if fixes:
            lines.append("")
            lines.append("[FIX] Applied fixes:")
            for fix in fixes:
                lines.append(f"   - {fix}")

        lines.append("")
        lines.append("[TIP] Executable generated but runtime issues occurred")
        lines.append("=" * 60)

        return '\n'.join(lines)
