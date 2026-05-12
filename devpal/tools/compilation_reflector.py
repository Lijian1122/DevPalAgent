# -*- coding: utf-8 -*-
"""
编译错误反思修复引擎
自动分析编译错误，生成修复方案，并自动应用修复后重新编译
"""
import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime

from .base import BaseTool, ToolResult
from pydantic import BaseModel, Field
from .compiler_analyzer import CompilationAnalyzer


@dataclass
class CompilationError:
    """编译错误信息"""
    error_code: str
    message: str
    file: str
    line: int
    column: int = 0
    compiler: str = 'msvc'


@dataclass
class FixAction:
    """修复动作"""
    action_type: str
    file: str
    line: Optional[int] = None
    description: str = ''
    code_snippet: Optional[str] = None
    applied: bool = False
    success: bool = False


@dataclass
class FixStrategy:
    """修复策略"""
    name: str
    description: str
    error_patterns: List[str]
    confidence: float = 0.0
    actions: List[FixAction] = field(default_factory=list)


class ErrorPatternMatcher:
    """错误模式匹配器"""

    # MSVC 错误代码修复模式映射
    MSVC_ERROR_FIXES = {
        'C4819': {
            'name': '编码错误',
            'description': '代码页问题，中文乱码',
            'strategy': 'convert_to_utf8_bom',
            'confidence': 0.95,
        },
        'C2065': {
            'name': '未声明标识符',
            'description': '变量或函数未声明',
            'strategy': 'add_missing_include',
            'confidence': 0.85,
        },
        'C3861': {
            'name': '找不到标识符',
            'description': '标识符未定义或缺少头文件',
            'strategy': 'add_missing_include',
            'confidence': 0.85,
        },
        'C1083': {
            'name': '无法打开包括文件',
            'description': '头文件不存在或路径错误',
            'strategy': 'fix_include_path',
            'confidence': 0.80,
        },
        'C2039': {
            'name': '成员不存在',
            'description': '类成员不存在或未包含头文件',
            'strategy': 'check_class_member',
            'confidence': 0.75,
        },
        'C2447': {
            'name': '缺少函数头',
            'description': '大括号或函数语法错误',
            'strategy': 'fix_syntax_braces',
            'confidence': 0.70,
        },
        'C2001': {
            'name': '常量中有换行',
            'description': '字符串引号不匹配',
            'strategy': 'fix_string_quotes',
            'confidence': 0.80,
        },
        'C2143': {
            'name': '语法错误',
            'description': '缺少分号或语法错误',
            'strategy': 'fix_missing_semicolon',
            'confidence': 0.75,
        },
        'C2059': {
            'name': '语法错误',
            'description': '标识符或符号错误',
            'strategy': 'fix_syntax_error',
            'confidence': 0.60,
        },
        'LNK2019': {
            'name': '未解析外部符号',
            'description': '函数声明但未实现，或库未链接',
            'strategy': 'fix_linker_error',
            'confidence': 0.70,
        },
        'LNK1120': {
            'name': '未解析外部',
            'description': '多个链接错误',
            'strategy': 'fix_linker_error',
            'confidence': 0.65,
        },
        'LNK2001': {
            'name': '无法解析外部符号',
            'description': '符号未定义',
            'strategy': 'fix_linker_error',
            'confidence': 0.70,
        },
    }

    # GCC/Clang 错误代码
    GCC_ERROR_FIXES = {
        'undeclared': 'add_missing_include',
        'no such file': 'fix_include_path',
        'undefined reference': 'fix_linker_error',
        'syntax error': 'fix_syntax_error',
    }

    @classmethod
    def match_error(cls, error: CompilationError) -> Optional[Dict]:
        """匹配错误并返回修复策略"""
        if error.compiler == 'msvc':
            # 优先匹配完整错误代码
            if error.error_code in cls.MSVC_ERROR_FIXES:
                return cls.MSVC_ERROR_FIXES[error.error_code]

            # 降级匹配：只匹配前缀
            for code, fix in cls.MSVC_ERROR_FIXES.items():
                if code[:3] == error.error_code[:3]:
                    return fix
        else:
            # GCC 模式，匹配消息
            for pattern, strategy in cls.GCC_ERROR_FIXES.items():
                if pattern in error.message.lower():
                    return {
                        'name': pattern,
                        'description': error.message,
                        'strategy': strategy,
                        'confidence': 0.60,
                    }

        return None


class FixActionApplier:
    """修复动作应用器"""

    # 常见标识符对应的头文件
    IDENTIFIER_TO_HEADER = {
        # 标准库
        'cout': '#include <iostream>',
        'cin': '#include <iostream>',
        'cerr': '#include <iostream>',
        'endl': '#include <iostream>',
        'std::cout': '#include <iostream>',
        'std::cin': '#include <iostream>',
        'string': '#include <string>',
        'std::string': '#include <string>',
        'vector': '#include <vector>',
        'std::vector': '#include <vector>',
        'map': '#include <map>',
        'std::map': '#include <map>',
        'unordered_map': '#include <unordered_map>',
        'std::unordered_map': '#include <unordered_map>',
        'set': '#include <set>',
        'std::set': '#include <set>',
        'list': '#include <list>',
        'std::list': '#include <list>',
        'queue': '#include <queue>',
        'std::queue': '#include <queue>',
        'stack': '#include <stack>',
        'std::stack': '#include <stack>',
        'algorithm': '#include <algorithm>',
        'std::sort': '#include <algorithm>',
        'std::find': '#include <algorithm>',
        'memory': '#include <memory>',
        'shared_ptr': '#include <memory>',
        'std::shared_ptr': '#include <memory>',
        'unique_ptr': '#include <memory>',
        'std::unique_ptr': '#include <memory>',
        'make_shared': '#include <memory>',
        'mutex': '#include <mutex>',
        'std::mutex': '#include <mutex>',
        'lock_guard': '#include <mutex>',
        'std::lock_guard': '#include <mutex>',
        'thread': '#include <thread>',
        'std::thread': '#include <thread>',
        'atomic': '#include <atomic>',
        'std::atomic': '#include <atomic>',
        'chrono': '#include <chrono>',
        'std::chrono': '#include <chrono>',
        'fstream': '#include <fstream>',
        'std::fstream': '#include <fstream>',
        'ifstream': '#include <fstream>',
        'ofstream': '#include <fstream>',
        'sstream': '#include <sstream>',
        'std::stringstream': '#include <sstream>',
        'iomanip': '#include <iomanip>',
        'std::setw': '#include <iomanip>',
        'functional': '#include <functional>',
        'std::function': '#include <functional>',
        'std::bind': '#include <functional>',
        'tuple': '#include <tuple>',
        'std::tuple': '#include <tuple>',
        'any': '#include <any>',
        'std::any': '#include <any>',
        'optional': '#include <optional>',
        'std::optional': '#include <optional>',
        'variant': '#include <variant>',
        'std::variant': '#include <variant>',
        'filesystem': '#include <filesystem>',
        'std::filesystem': '#include <filesystem>',

        # C 标准库
        'size_t': '#include <cstddef>',
        'NULL': '#include <cstddef>',
        'nullptr': '#include <cstddef>',
        'printf': '#include <cstdio>',
        'fopen': '#include <cstdio>',
        'fclose': '#include <cstdio>',
        'fread': '#include <cstdio>',
        'fwrite': '#include <cstdio>',
        'memset': '#include <cstring>',
        'memcpy': '#include <cstring>',
        'strcpy': '#include <cstring>',
        'strcmp': '#include <cstring>',
        'strlen': '#include <cstring>',
        'malloc': '#include <cstdlib>',
        'free': '#include <cstdlib>',
        'exit': '#include <cstdlib>',
        'atoi': '#include <cstdlib>',
        'atof': '#include <cstdlib>',
        'time': '#include <ctime>',
        'std::time': '#include <ctime>',
        'time_t': '#include <ctime>',
        'errno': '#include <cerrno>',

        # 数学函数
        'sqrt': '#include <cmath>',
        'pow': '#include <cmath>',
        'sin': '#include <cmath>',
        'cos': '#include <cmath>',
        'tan': '#include <cmath>',
        'abs': '#include <cmath>',
        'fabs': '#include <cmath>',
        'floor': '#include <cmath>',
        'ceil': '#include <cmath>',
        'round': '#include <cmath>',
        'min': '#include <algorithm>',
        'max': '#include <algorithm>',
        'std::min': '#include <algorithm>',
        'std::max': '#include <algorithm>',

        # 输入输出
        'std::ifstream': '#include <fstream>',
        'std::ofstream': '#include <fstream>',
        'getline': '#include <string>',
        'std::getline': '#include <string>',
    }

    def __init__(self, source_root: Path):
        self.source_root = source_root
        self.actions_applied: List[FixAction] = []

    def apply_strategy(self, strategy_name: str, error: CompilationError) -> bool:
        """应用修复策略"""
        strategy_methods = {
            'convert_to_utf8_bom': self._convert_to_utf8_bom,
            'add_missing_include': self._add_missing_include,
            'fix_include_path': self._fix_include_path,
            'check_class_member': self._check_class_member,
            'fix_syntax_braces': self._fix_syntax_braces,
            'fix_string_quotes': self._fix_string_quotes,
            'fix_missing_semicolon': self._fix_missing_semicolon,
            'fix_syntax_error': self._fix_syntax_error,
            'fix_linker_error': self._fix_linker_error,
        }

        method = strategy_methods.get(strategy_name)
        if method:
            return method(error)
        return False

    def _convert_to_utf8_bom(self, error: CompilationError) -> bool:
        """转换为 UTF-8 BOM 编码"""
        file_path = self._resolve_file(error.file)
        if not file_path or not file_path.exists():
            return False

        try:
            # 尝试多种编码读取
            content = None
            encodings = ['gbk', 'gb2312', 'gb18030', 'utf-8', 'latin1']

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                return False

            # 写入 UTF-8 with BOM
            with open(file_path, 'w', encoding='utf-8-sig') as f:
                f.write(content)

            self.actions_applied.append(FixAction(
                action_type='encoding_fix',
                file=str(file_path),
                description=f'转换文件编码为 UTF-8 BOM: {file_path.name}',
                applied=True,
                success=True
            ))
            return True

        except Exception as e:
            return False

    def _add_missing_include(self, error: CompilationError) -> bool:
        """添加缺失的头文件"""
        file_path = self._resolve_file(error.file)
        if not file_path or not file_path.exists():
            return False

        # 从错误消息中提取标识符
        identifier = self._extract_identifier(error.message)
        if not identifier:
            return False

        # 查找对应的头文件
        header = None
        for ident, h in self.IDENTIFIER_TO_HEADER.items():
            if ident.lower() == identifier.lower() or ident.endswith('::' + identifier):
                header = h
                break

        if not header:
            return False

        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()

            # 检查头文件是否已存在
            content = ''.join(lines)
            if header in content:
                return False  # 已存在

            # 找到插入位置（在第一个非注释非空行之前）
            insert_pos = 0
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped and not stripped.startswith('//') and not stripped.startswith('/*'):
                    if not stripped.startswith('#include') and not stripped.startswith('#define'):
                        insert_pos = i
                        break
                    insert_pos = i + 1

            lines.insert(insert_pos, header + '\n')

            with open(file_path, 'w', encoding='utf-8-sig') as f:
                f.writelines(lines)

            self.actions_applied.append(FixAction(
                action_type='add_include',
                file=str(file_path),
                line=insert_pos,
                description=f'添加头文件: {header}',
                applied=True,
                success=True
            ))
            return True

        except Exception as e:
            return False

    def _fix_include_path(self, error: CompilationError) -> bool:
        """修复 include 路径"""
        # 提取缺失的头文件名
        match = re.search(r"'(.+?)'", error.message)
        if not match:
            return False

        header_name = match.group(1)
        header_basename = os.path.basename(header_name)

        # 在源代码树中查找这个头文件
        found_files = list(self.source_root.rglob(header_basename))

        if found_files:
            # 找到文件，可能需要调整 CMakeLists.txt 的 include 路径
            cmake_file = self.source_root / 'CMakeLists.txt'
            if cmake_file.exists():
                try:
                    with open(cmake_file, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()

                    header_dir = found_files[0].parent
                    rel_path = os.path.relpath(header_dir, self.source_root)

                    if 'include_directories' not in content.lower():
                        # 添加 include_directories
                        new_content = content.replace(
                            'project(',
                            f'include_directories({rel_path})\n\nproject('
                        )
                        with open(cmake_file, 'w', encoding='utf-8-sig') as f:
                            f.write(new_content)

                        self.actions_applied.append(FixAction(
                            action_type='cmake_include',
                            file=str(cmake_file),
                            description=f'添加 include_directories: {rel_path}',
                            applied=True,
                            success=True
                        ))
                        return True
                except Exception:
                    pass

        return False

    def _check_class_member(self, error: CompilationError) -> bool:
        """检查类成员错误"""
        # 简化实现：暂时不处理这类复杂错误
        return False

    def _fix_syntax_braces(self, error: CompilationError) -> bool:
        """修复大括号语法错误"""
        return False

    def _fix_string_quotes(self, error: CompilationError) -> bool:
        """修复字符串引号错误"""
        return False

    def _fix_missing_semicolon(self, error: CompilationError) -> bool:
        """修复缺失分号错误"""
        file_path = self._resolve_file(error.file)
        if not file_path or not file_path.exists() or error.line <= 0:
            return False

        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()

            line_idx = error.line - 1
            if line_idx >= len(lines):
                return False

            line = lines[line_idx]

            # 检查上一行是否缺少分号
            if line_idx > 0:
                prev_line = lines[line_idx - 1].rstrip()
                if prev_line and not prev_line.endswith(';') and not prev_line.endswith('{') and not prev_line.endswith('}'):
                    if not prev_line.endswith(',') and not prev_line.endswith('('):
                        lines[line_idx - 1] = prev_line + ';\n'

                        with open(file_path, 'w', encoding='utf-8-sig') as f:
                            f.writelines(lines)

                        self.actions_applied.append(FixAction(
                            action_type='add_semicolon',
                            file=str(file_path),
                            line=line_idx,
                            description=f'在第 {line_idx} 行添加分号',
                            applied=True,
                            success=True
                        ))
                        return True

        except Exception:
            pass

        return False

    def _fix_syntax_error(self, error: CompilationError) -> bool:
        """修复语法错误"""
        return False

    def _fix_linker_error(self, error: CompilationError) -> bool:
        """修复链接错误"""
        # 从错误消息中提取函数名
        func_match = re.search(r'"(.+?)"', error.message)
        if not func_match:
            func_match = re.search(r'`(.+?)\'', error.message)

        if not func_match:
            return False

        function_name = func_match.group(1)

        # 简化函数名（去掉命名空间等）
        if '::' in function_name:
            function_name = function_name.split('::')[-1]

        # 在源代码树中查找实现文件
        cpp_files = list(self.source_root.rglob('*.cpp'))
        for cpp_file in cpp_files:
            try:
                with open(cpp_file, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                    if function_name in content:
                        # 检查 CMakeLists.txt 是否包含这个文件
                        cmake_file = self.source_root / 'CMakeLists.txt'
                        if cmake_file.exists():
                            with open(cmake_file, 'r', encoding='utf-8', errors='replace') as f:
                                cmake_content = f.read()
                                if cpp_file.name not in cmake_content:
                                    # 这个文件没有被包含，需要添加
                                    # 简化处理：报告问题但不自动修改
                                    self.actions_applied.append(FixAction(
                                        action_type='linker_warning',
                                        file=str(cpp_file),
                                        description=f'文件 {cpp_file.name} 可能未添加到 CMakeLists.txt',
                                        applied=False,
                                        success=False
                                    ))
                                    return False
            except Exception:
                pass

        return False

    def _resolve_file(self, file_path: str) -> Optional[Path]:
        """解析文件路径"""
        if not file_path:
            return None

        path = Path(file_path)
        if path.exists():
            return path

        # 尝试在源目录中查找
        found = list(self.source_root.rglob(path.name))
        if found:
            return found[0]

        return None

    def _extract_identifier(self, message: str) -> Optional[str]:
        """从错误消息中提取标识符"""
        # 匹配 'identifier' 格式
        match = re.search(r"'(.+?)'", message)
        if match:
            return match.group(1)

        # 匹配 `identifier` 格式
        match = re.search(r'`(.+?)\'', message)
        if match:
            return match.group(1)

        return None


class CompilationReflector:
    """编译错误反思器"""

    def __init__(self, source_root: Path):
        self.source_root = source_root
        self.matcher = ErrorPatternMatcher()
        self.applier = FixActionApplier(source_root)
        self.error_history: List[CompilationError] = []
        self.fix_history: List[List[FixAction]] = []

    def analyze_and_fix(self, compiler_output: str) -> Dict[str, Any]:
        """分析编译输出并自动修复

        Returns:
            {
                'errors_found': int,
                'errors_fixed': int,
                'fixes_applied': List[FixAction],
                'can_retry': bool,
            }
        """
        # 解析编译输出
        parsed_errors = CompilationAnalyzer.parse_output(compiler_output)

        if not parsed_errors:
            return {
                'errors_found': 0,
                'errors_fixed': 0,
                'fixes_applied': [],
                'can_retry': False,
            }

        # 转换为内部格式
        errors = []
        for pe in parsed_errors:
            err = CompilationError(
                error_code=pe.get('error_code', ''),
                message=pe.get('message', ''),
                file=pe.get('file', ''),
                line=pe.get('line', 0),
                column=pe.get('column', 0),
                compiler=pe.get('compiler', 'msvc')
            )
            errors.append(err)
            self.error_history.append(err)

        # 尝试修复每个错误
        fixes_applied = []
        for error in errors:
            strategy_info = self.matcher.match_error(error)
            if strategy_info:
                strategy_name = strategy_info['strategy']
                if self.applier.apply_strategy(strategy_name, error):
                    fixes_applied.extend(self.applier.actions_applied[-1:])

        # 记录修复历史
        if fixes_applied:
            self.fix_history.append(fixes_applied)

        return {
            'errors_found': len(errors),
            'errors_fixed': len(fixes_applied),
            'fixes_applied': fixes_applied,
            'can_retry': len(fixes_applied) > 0,
        }

    def get_summary(self) -> str:
        """获取修复摘要"""
        total_errors = len(self.error_history)
        total_fixed = sum(len(fixes) for fixes in self.fix_history)

        summary = [
            "=" * 60,
            "编译错误反思修复摘要",
            "=" * 60,
            f"发现错误总数: {total_errors}",
            f"已应用修复数: {total_fixed}",
            f"修复成功率: {total_fixed / max(total_errors, 1) * 100:.1f}%",
        ]

        if self.applier.actions_applied:
            summary.extend(["", "已应用的修复:"])
            for i, action in enumerate(self.applier.actions_applied[-10:], 1):
                summary.append(f"  {i}. [{action.action_type}] {action.description}")

        summary.append("=" * 60)
        return '\n'.join(summary)


class CompilationReflectorTool(BaseTool):
    """编译错误反思修复工具"""

    name = "compilation_reflector"
    description = "自动分析编译错误，生成修复方案，并自动应用修复后重新编译"

    class Parameters(BaseModel):
        source_dir: str
        compiler_output: str
        auto_apply: bool = True
        max_fix_attempts: int = 3

    def _execute(self, params: Parameters) -> ToolResult:
        source_path = Path(params.source_dir).resolve()

        if not source_path.exists():
            return ToolResult.error(f"源目录不存在: {source_path}")

        reflector = CompilationReflector(source_path)
        result = reflector.analyze_and_fix(params.compiler_output)

        if result['can_retry']:
            output = reflector.get_summary()
            output += "\n\n[OK] 已应用修复，可以重新编译！"

            return ToolResult.ok(
                content=output,
                **result
            )
        elif result['errors_found'] > 0:
            output = reflector.get_summary()
            output += "\n\n[WARN] 发现错误但无法自动修复，请手动检查代码。"

            return ToolResult.ok(
                content=output,
                **result
            )
        else:
            return ToolResult.ok(
                content="[OK] 未发现编译错误，无需修复。",
                **result
            )
