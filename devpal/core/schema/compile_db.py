# -*- coding: utf-8 -*-
"""
OpenSpec 编译数据库支持 - Phase 6: C/C++ 集成

用于加载和管理 compile_commands.json，提供:
- 编译参数解析
- 文件编译命令查找
- 宏定义解析
- 包含路径解析
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json
import shlex
import subprocess
import sys


@dataclass
class CompileCommand:
    """单个编译命令"""
    file: str
    directory: str
    command: Optional[str] = None
    arguments: Optional[List[str]] = None

    # 解析后的字段
    compiler: str = ""
    source_file: str = ""
    output_file: Optional[str] = None
    include_paths: List[Path] = field(default_factory=list)
    system_include_paths: List[Path] = field(default_factory=list)
    defines: Dict[str, Optional[str]] = field(default_factory=dict)
    undefines: Set[str] = field(default_factory=set)
    standard: Optional[str] = None  # c++11, c++17, etc.
    flags: Set[str] = field(default_factory=set)

    def parse(self):
        """解析编译命令"""
        args = []
        if self.arguments:
            args = self.arguments
        elif self.command:
            args = shlex.split(self.command)

        if not args:
            return

        # 编译器
        self.compiler = args[0] if args else ""

        i = 1
        while i < len(args):
            arg = args[i]

            # 包含路径 -I
            if arg.startswith('-I'):
                if len(arg) > 2:
                    inc_path = arg[2:]
                else:
                    i += 1
                    inc_path = args[i] if i < len(args) else ""

                if inc_path:
                    path = Path(inc_path)
                    if not path.is_absolute():
                        path = Path(self.directory) / path
                    self.include_paths.append(path.resolve())

            # 系统包含路径 -isystem
            elif arg == '-isystem':
                i += 1
                if i < len(args):
                    path = Path(args[i])
                    if not path.is_absolute():
                        path = Path(self.directory) / path
                    self.system_include_paths.append(path.resolve())

            # 宏定义 -D
            elif arg.startswith('-D'):
                if len(arg) > 2:
                    define = arg[2:]
                else:
                    i += 1
                    define = args[i] if i < len(args) else ""

                if define:
                    if '=' in define:
                        name, value = define.split('=', 1)
                        self.defines[name] = value
                    else:
                        self.defines[define] = None

            # 取消宏定义 -U
            elif arg.startswith('-U'):
                if len(arg) > 2:
                    undef = arg[2:]
                else:
                    i += 1
                    undef = args[i] if i < len(args) else ""

                if undef:
                    self.undefines.add(undef)

            # 输出文件 -o
            elif arg == '-o':
                i += 1
                if i < len(args):
                    self.output_file = args[i]

            # C++ 标准
            elif arg.startswith('-std='):
                self.standard = arg[5:]

            # 其他标志
            elif arg.startswith('-') and len(arg) > 1:
                self.flags.add(arg)

            # 源文件
            elif arg.endswith(('.cpp', '.cxx', '.cc', '.c', '.C')):
                self.source_file = arg

            i += 1

    def to_compiler_args(self) -> List[str]:
        """转换为编译器参数列表"""
        args = []

        if self.standard:
            args.append(f'-std={self.standard}')

        for inc_path in self.include_paths:
            args.append(f'-I{inc_path}')

        for inc_path in self.system_include_paths:
            args.append(f'-isystem{inc_path}')

        for name, value in self.defines.items():
            if value is not None:
                args.append(f'-D{name}={value}')
            else:
                args.append(f'-D{name}')

        for name in self.undefines:
            args.append(f'-U{name}')

        args.extend(self.flags)

        return args


class CompilationDatabase:
    """编译数据库 (compile_commands.json)"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.directory = db_path.parent
        self.commands: Dict[str, CompileCommand] = {}
        self._file_to_command: Dict[str, CompileCommand] = {}
        self._load()

    def _load(self):
        """加载 compile_commands.json"""
        with open(self.db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for entry in data:
            cmd = CompileCommand(
                file=entry.get('file', ''),
                directory=entry.get('directory', str(self.directory)),
                command=entry.get('command'),
                arguments=entry.get('arguments'),
            )
            cmd.parse()

            # 文件路径规范化
            file_path = Path(cmd.file)
            if not file_path.is_absolute():
                file_path = Path(cmd.directory) / file_path

            self.commands[str(file_path.resolve())] = cmd
            self._file_to_command[str(file_path.resolve())] = cmd

    def get_command_for_file(self, file_path: Path) -> Optional[CompileCommand]:
        """获取文件的编译命令"""
        abs_path = str(file_path.resolve())
        return self._file_to_command.get(abs_path)

    def get_all_files(self) -> List[Path]:
        """获取所有源文件"""
        return [Path(f) for f in self.commands.keys()]

    def get_include_paths(self, file_path: Optional[Path] = None) -> List[Path]:
        """获取包含路径列表"""
        paths: Set[Path] = set()

        if file_path:
            cmd = self.get_command_for_file(file_path)
            if cmd:
                paths.update(cmd.include_paths)
                paths.update(cmd.system_include_paths)
        else:
            # 收集所有文件的包含路径（去重）
            for cmd in self.commands.values():
                paths.update(cmd.include_paths)
                paths.update(cmd.system_include_paths)

        return sorted(paths)

    def get_all_defines(self) -> Dict[str, Optional[str]]:
        """获取所有宏定义"""
        defines: Dict[str, Optional[str]] = {}
        for cmd in self.commands.values():
            defines.update(cmd.defines)
        return defines

    def get_compiler_includes(self) -> List[Path]:
        """获取编译器内置的包含路径"""
        # 尝试从任意一个编译命令获取编译器
        compiler = None
        for cmd in self.commands.values():
            if cmd.compiler:
                compiler = cmd.compiler
                break

        if not compiler:
            return []

        try:
            # 尝试获取编译器内置的包含路径
            proc = subprocess.run(
                [compiler, '-E', '-x', 'c++', '-Wp,-v', '-'],
                input='',
                capture_output=True,
                text=True,
                timeout=10
            )

            includes = []
            capture = False
            for line in proc.stderr.split('\n'):
                if line.startswith('#include <...>'):
                    capture = True
                    continue
                if line.startswith('End of search'):
                    break
                if capture and line.strip():
                    path = Path(line.strip())
                    if path.exists():
                        includes.append(path)

            return includes
        except Exception:
            return []

    @classmethod
    def find(cls, start_path: Path) -> Optional['CompilationDatabase']:
        """在目录树中查找编译数据库"""
        for parent in [start_path] + list(start_path.parents):
            db_path = parent / 'compile_commands.json'
            if db_path.exists():
                return cls(db_path)
        return None

    @classmethod
    def generate_cmake(cls, source_dir: Path, build_dir: Optional[Path] = None,
                      cmake_args: Optional[List[str]] = None) -> Optional['CompilationDatabase']:
        """使用 CMake 生成编译数据库"""
        if build_dir is None:
            build_dir = source_dir / 'build'

        build_dir.mkdir(parents=True, exist_ok=True)

        # 检查是否有 CMakeLists.txt
        if not (source_dir / 'CMakeLists.txt').exists():
            return None

        try:
            # 运行 CMake 生成编译数据库
            cmd = [
                'cmake',
                '-B', str(build_dir),
                '-S', str(source_dir),
                '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',
            ]
            if cmake_args:
                cmd.extend(cmake_args)

            subprocess.run(cmd, capture_output=True, check=True, timeout=120)

            # 加载生成的数据库
            db_path = build_dir / 'compile_commands.json'
            if db_path.exists():
                return cls(db_path)

        except Exception:
            pass

        return None

    @classmethod
    def generate_bear(cls, build_command: List[str], work_dir: Path) -> Optional['CompilationDatabase']:
        """使用 Bear 生成编译数据库（需要 Bear 安装）"""
        try:
            work_dir.mkdir(parents=True, exist_ok=True)

            cmd = ['bear', '--'] + build_command

            subprocess.run(cmd, cwd=work_dir, capture_output=True, check=True, timeout=300)

            db_path = work_dir / 'compile_commands.json'
            if db_path.exists():
                return cls(db_path)

        except Exception:
            pass

        return None

    def merge(self, other: 'CompilationDatabase'):
        """合并另一个编译数据库"""
        self.commands.update(other.commands)
        self._file_to_command.update(other._file_to_command)

    def to_dict(self) -> Dict[str, Any]:
        """转换为 JSON 字典"""
        return {
            'database_path': str(self.db_path),
            'file_count': len(self.commands),
            'files': list(self.commands.keys()),
        }


class BuildSystemDetector:
    """构建系统检测器"""

    @staticmethod
    def detect(project_root: Path) -> str:
        """检测项目使用的构建系统"""
        detectors = [
            ('cmake', ['CMakeLists.txt']),
            ('make', ['Makefile', 'GNUmakefile']),
            ('meson', ['meson.build']),
            ('autotools', ['configure.ac', 'configure.in']),
            ('bazel', ['BUILD', 'BUILD.bazel']),
            ('xcode', ['*.xcodeproj']),
            ('visual_studio', ['*.sln', '*.vcxproj']),
        ]

        for name, patterns in detectors:
            for pattern in patterns:
                if '*' in pattern:
                    if list(project_root.glob(pattern)):
                        return name
                else:
                    if (project_root / pattern).exists():
                        return name

        return 'unknown'

    @staticmethod
    def get_all_build_files(project_root: Path) -> Dict[str, List[Path]]:
        """获取所有构建相关文件"""
        result = {}

        patterns = {
            'cmake': ['CMakeLists.txt', '*.cmake'],
            'make': ['Makefile', 'GNUmakefile', '*.mk'],
            'meson': ['meson.build', 'meson_options.txt'],
            'bazel': ['BUILD', 'BUILD.bazel', 'WORKSPACE'],
            'visual_studio': ['*.sln', '*.vcxproj', '*.props'],
            'xcode': ['*.xcodeproj', '*.xcworkspace'],
        }

        for system, pats in patterns.items():
            files = []
            for pat in pats:
                files.extend(project_root.glob('**/' + pat))
            if files:
                result[system] = files

        return result
