# -*- coding: utf-8 -*-
"""
MSVC 编译器工具
支持 AddressSanitizer 检测堆破坏和内存泄漏
"""
import subprocess
from typing import Optional
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult, ToolSecurity, retry
from .compiler_analyzer import CompilationAnalyzer


class MsvcAsanCompilerTool(BaseTool):
    """MSVC 编译器工具，支持 AddressSanitizer"""

    name = "msvc_asan_compiler"
    description = "使用 MSVC 编译器编译 C/C++ 代码并启用 AddressSanitizer 检测堆破坏和内存泄漏"

    class Parameters(BaseModel):
        source_files: str = Field(
            description="源文件列表，用空格分隔"
        )
        output_exe: str = Field(
            description="输出可执行文件名"
        )
        additional_flags: str = Field(
            default="",
            description="额外的编译标志"
        )
        include_dirs: str = Field(
            default="",
            description="包含目录，空格分隔，每个前面加/I 或自动添加"
        )
        lib_dirs: str = Field(
            default="",
            description="库目录，空格分隔，每个前面加/LIBPATH: 或自动添加"
        )
        libraries: str = Field(
            default="",
            description="链接库，空格分隔"
        )
        cwd: Optional[str] = Field(
            default=None,
            description="工作目录"
        )
        timeout: int = Field(
            default=60,
            description="编译超时时间，单位秒"
        )
        enable_asan: bool = Field(
            default=True,
            description="是否启用 AddressSanitizer"
        )
        run_after_build: bool = Field(
            default=False,
            description="编译成功后是否运行程序"
        )
        run_timeout: int = Field(
            default=30,
            description="程序运行超时时间，单位秒"
        )

    @retry(max_retries=2, delay=1.0)
    def _execute(self, params: Parameters) -> ToolResult:
        # 构建编译命令
        command_parts = ['cl']

        # AddressSanitizer 标志
        if params.enable_asan:
            asan_flags = [
                '/fsanitize=address',  # 启用 AddressSanitizer
                '/Zi',  # 生成完整调试信息
                '/Od',  # 禁用优化，便于调试
                '/EHsc',  # C++ 异常处理
                '/MDd',  # 使用调试版本运行时库
            ]
            command_parts.extend(asan_flags)
        else:
            # 普通调试编译
            command_parts.extend(['/Zi', '/Od', '/EHsc'])

        # 包含目录
        if params.include_dirs:
            for inc_dir in params.include_dirs.split():
                if inc_dir.strip():
                    if not inc_dir.startswith('/I'):
                        command_parts.append(f'/I{inc_dir.strip()}')
                    else:
                        command_parts.append(inc_dir.strip())

        # 库目录
        if params.lib_dirs:
            for lib_dir in params.lib_dirs.split():
                if lib_dir.strip():
                    if not lib_dir.startswith('/LIBPATH:'):
                        command_parts.append(f'/LIBPATH:{lib_dir.strip()}')
                    else:
                        command_parts.append(lib_dir.strip())

        # 额外编译标志
        if params.additional_flags:
            command_parts.extend(params.additional_flags.split())

        # 输出文件
        command_parts.append(f'/Fe:{params.output_exe}')

        # 源文件
        command_parts.append(params.source_files)

        # 链接库
        if params.libraries:
            command_parts.extend(params.libraries.split())

        command = ' '.join(command_parts)

        # 安全检查
        safe, reason = ToolSecurity.check_command_safety(command)
        if not safe:
            return ToolResult.error(f"命令安全检查失败: {reason}", command=command)

        # 检查编译器是否可用
        try:
            check_result = subprocess.run(
                'cl.exe /?',
                shell=True,
                capture_output=True,
                timeout=5
            )
            if check_result.returncode != 0:
                return ToolResult.error(
                    "MSVC 编译器不可用。请在 Visual Studio Developer Command Prompt 中运行，"
                    "或运行 vcvarsall.bat 配置环境变量。",
                    command=command
                )
        except Exception:
            return ToolResult.error(
                "MSVC 编译器不可用。请安装 Visual Studio 并在 Developer Command Prompt 中运行。",
                command=command
            )

        # 执行编译
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=params.timeout,
                cwd=params.cwd
            )

            # 解析编译输出
            output_lines = []
            if result.stdout:
                output_lines.append(result.stdout.strip())
            if result.stderr:
                output_lines.append(result.stderr.strip())

            full_output = '\n'.join(output_lines)

            if result.returncode == 0:
                # 编译成功
                output = [
                    "✅ 编译成功！",
                    f"📄 输出文件: {params.output_exe}",
                    f"🔧 AddressSanitizer: {'已启用' if params.enable_asan else '未启用'}",
                    "",
                    "编译输出:",
                    full_output
                ]

                # 如果需要运行程序
                if params.run_after_build:
                    run_result = self._run_program(params.output_exe, params.run_timeout, params.cwd)
                    output.extend(["", "=" * 60, "程序运行结果:", "=" * 60, run_result])

                return ToolResult.ok(
                    '\n'.join(output),
                    return_code=result.returncode,
                    output_exe=params.output_exe,
                    compile_success=True,
                    asan_enabled=params.enable_asan
                )
            else:
                # 编译失败 - 分析错误
                errors = CompilationAnalyzer.parse_output(full_output)
                error_count = len([e for e in errors if e['type'] == 'error'])
                warning_count = len([e for e in errors if e['type'] == 'warning'])

                return ToolResult.error(
                    f"❌ 编译失败！\n错误数: {error_count}, 警告数: {warning_count}\n\n{full_output}",
                    return_code=result.returncode,
                    error_count=error_count,
                    warning_count=warning_count,
                    compile_success=False,
                    errors=errors
                )

        except subprocess.TimeoutExpired:
            return ToolResult.error(
                f"⏱️ 编译超时（{params.timeout}秒）",
                command=command
            )
        except Exception as e:
            return ToolResult.error(
                f"❌ 编译过程中发生错误: {str(e)}",
                command=command
            )

    def _run_program(self, exe_path: str, timeout: int, cwd: Optional[str] = None) -> str:
        """运行编译后的程序"""
        try:
            result = subprocess.run(
                exe_path,
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=timeout,
                cwd=cwd
            )

            output = []
            if result.returncode == 0:
                output.append("✅ 程序正常退出")
            else:
                output.append(f"⚠️  程序异常退出，返回码: {result.returncode}")

            if result.stdout:
                output.extend(["", "标准输出:", result.stdout.strip()])
            if result.stderr:
                output.extend(["", "标准错误:", result.stderr.strip()])

            return '\n'.join(output)

        except subprocess.TimeoutExpired:
            return f"⏱️ 程序运行超时（{timeout}秒）"
        except Exception as e:
            return f"❌ 运行失败: {str(e)}"
