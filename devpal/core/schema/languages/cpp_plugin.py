# -*- coding: utf-8 -*-
"""
OpenSpec C/C++ 语言插件 - Phase 6: 多语言支持

实现:
1. 基础版本: 正则表达式 + 简单解析 (无需外部依赖)
2. Clang 版本: libclang 绑定 (可选，需要 clang 安装)

自动检测可用的后端并使用最佳方案。
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from pathlib import Path
import re
import json
import subprocess
import sys

from .base import (
    LanguagePlugin,
    FileAnalysisResult,
    SymbolInfo,
    SymbolKind,
    DependencyInfo,
    Diagnostic,
    DiagnosticSeverity,
    SourceLocation,
    SourceRange,
    ASTNode,
    ASTNodeType,
    TypeInfo,
    AccessSpecifier,
)


class CppLanguagePlugin(LanguagePlugin):
    """C/C++ 语言插件"""

    def __init__(self):
        self._use_clang = False
        self._clang_index = None
        self._init_clang()

        # 正则表达式模式
        self._patterns = {
            'include': re.compile(r'#\s*include\s*([<"])([^>"]+)[>"]'),
            'define': re.compile(r'#\s*define\s+(\w+)(?:\s*\(([^)]*)\))?'),
            'class': re.compile(r'\bclass\s+(\w+)(?:\s*:\s*(public|protected|private)\s*(\w+))?'),
            'struct': re.compile(r'\bstruct\s+(\w+)(?:\s*:\s*(public|protected|private)\s*(\w+))?'),
            'union': re.compile(r'\bunion\s+(\w+)'),
            'enum': re.compile(r'\benum\s+(?:class|struct)?\s*(\w+)'),
            'typedef': re.compile(r'\btypedef\s+(.+?)\s+(\w+)\s*;'),
            'function': re.compile(
                r'\b(?:(inline|static|virtual|constexpr|explicit)\s+)*'
                r'([\w:<>,\s&*]+?)\s+'
                r'(\w+)\s*\(([^)]*)\)\s*'
                r'(?:\s*(const|override|final|noexcept|=0|=default|=delete))*\s*'
                r'(?:\s*:\s*\w+\([^)]*\))?\s*[;{]'
            ),
            'namespace': re.compile(r'\bnamespace\s+(\w+)'),
            'member_var': re.compile(r'\b(\w+(?:\s*[*&])?)\s+(\w+)\s*(?:\[[^\]]*\])?\s*;'),
        }

    def _init_clang(self):
        """尝试初始化 Clang 绑定"""
        try:
            # 优先尝试系统安装的 clang 库
            # 注意：clang.cindex 需要 libclang.so / libclang.dylib / libclang.dll
            from clang import cindex

            # 尝试设置库路径（常见位置）
            try:
                # Windows 常见路径
                if sys.platform == 'win32':
                    possible_paths = [
                        r'C:\Program Files\LLVM\bin\libclang.dll',
                        r'C:\Program Files (x86)\LLVM\bin\libclang.dll',
                    ]
                    for path in possible_paths:
                        if Path(path).exists():
                            cindex.Config.set_library_file(path)
                            break
                # Linux/Mac 常见路径（clang 通常在标准路径）
            except Exception:
                pass

            # 测试是否能创建 Index
            self._clang_index = cindex.Index.create()
            self._use_clang = True
        except Exception:
            # Clang 不可用，降级到正则解析
            self._use_clang = False

    def get_language_id(self) -> str:
        return "cpp"

    def get_language_name(self) -> str:
        return "C/C++"

    def get_supported_extensions(self) -> List[str]:
        return ['.cpp', '.cxx', '.cc', '.c', '.h', '.hpp', '.hxx', '.hh', '.inl']

    def is_available(self) -> bool:
        # 基础版本总是可用
        return True

    def is_clang_available(self) -> bool:
        """检查 Clang 绑定是否可用"""
        return self._use_clang

    def analyze_file(self, file_path: Path, options: Optional[Dict[str, Any]] = None) -> FileAnalysisResult:
        """分析 C/C++ 文件"""
        options = options or {}

        # 如果可用且启用，使用 Clang 分析
        if self._use_clang and options.get('use_clang', True):
            return self._analyze_with_clang(file_path, options)

        # 否则使用正则表达式基础分析
        return self._analyze_with_regex(file_path)

    def _analyze_with_regex(self, file_path: Path) -> FileAnalysisResult:
        """使用正则表达式基础分析（无外部依赖）"""
        result = FileAnalysisResult(file_path=file_path, language="cpp")

        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            result.line_count = len(lines)

            # 分析 includes
            self._parse_includes(content, result)

            # 分析符号
            self._parse_symbols(content, lines, result)

            # 基础统计
            result.function_count = sum(1 for s in result.symbols if s.kind == SymbolKind.FUNCTION)
            result.class_count = sum(1 for s in result.symbols if s.kind in {SymbolKind.CLASS, SymbolKind.STRUCT})
            result.comment_count = content.count('//') + content.count('/*')

            # 构建简单的 AST 根节点
            result.ast_root = ASTNode(
                node_id="root",
                node_type=ASTNodeType.ROOT,
                location=SourceLocation(file_path=str(file_path), line=1, column=1),
                range=SourceRange(
                    start=SourceLocation(file_path=str(file_path), line=1, column=1),
                    end=SourceLocation(file_path=str(file_path), line=len(lines), column=1),
                ),
                text=file_path.name,
            )

        except Exception as e:
            result.success = False
            result.error_message = str(e)

        return result

    def _parse_includes(self, content: str, result: FileAnalysisResult):
        """解析 #include 指令"""
        for match in self._patterns['include'].finditer(content):
            quote_type = match.group(1)
            include_path = match.group(2).strip()

            # 计算行号
            line_num = content.count('\n', 0, match.start()) + 1

            dep = DependencyInfo(
                kind="include",
                target=include_path,
                is_system=(quote_type == '<'),
                is_relative=(quote_type == '"'),
                location=SourceLocation(
                    file_path=str(result.file_path),
                    line=line_num,
                    column=match.start() - content.rfind('\n', 0, match.start())
                )
            )

            # 尝试解析路径
            if not dep.is_system:
                # 相对路径搜索
                candidate = result.file_path.parent / include_path
                if candidate.exists():
                    dep.path = candidate
                    dep.resolved = True

            result.dependencies.append(dep)

    def _parse_symbols(self, content: str, lines: List[str], result: FileAnalysisResult):
        """解析符号"""
        # Class
        for line_num, line in enumerate(lines, 1):
            for match in self._patterns['class'].finditer(line):
                class_name = match.group(1)
                access = match.group(2) or 'public'
                parent = match.group(3)

                symbol = SymbolInfo(
                    name=class_name,
                    kind=SymbolKind.CLASS,
                    location=SourceLocation(
                        file_path=str(result.file_path),
                        line=line_num,
                        column=match.start() + 1
                    ),
                    qualified_name=class_name,
                    metadata={'parent_class': parent} if parent else {}
                )
                result.symbols.append(symbol)
                result.symbol_map[class_name] = symbol

        # Struct
        for line_num, line in enumerate(lines, 1):
            for match in self._patterns['struct'].finditer(line):
                struct_name = match.group(1)
                symbol = SymbolInfo(
                    name=struct_name,
                    kind=SymbolKind.STRUCT,
                    location=SourceLocation(
                        file_path=str(result.file_path),
                        line=line_num,
                        column=match.start() + 1
                    ),
                    qualified_name=struct_name,
                )
                result.symbols.append(symbol)
                result.symbol_map[struct_name] = symbol

        # Enum
        for line_num, line in enumerate(lines, 1):
            for match in self._patterns['enum'].finditer(line):
                enum_name = match.group(1)
                symbol = SymbolInfo(
                    name=enum_name,
                    kind=SymbolKind.ENUM,
                    location=SourceLocation(
                        file_path=str(result.file_path),
                        line=line_num,
                        column=match.start() + 1
                    ),
                    qualified_name=enum_name,
                )
                result.symbols.append(symbol)
                result.symbol_map[enum_name] = symbol

        # Function (简化)
        for line_num, line in enumerate(lines, 1):
            for match in self._patterns['function'].finditer(line):
                modifiers = match.group(1) or ''
                return_type = match.group(2).strip()
                func_name = match.group(3)
                params = match.group(4)
                qualifiers = match.group(5) or ''

                # 跳过常见的非函数
                if func_name in {'if', 'for', 'while', 'switch', 'return', 'sizeof'}:
                    continue

                # 跳过看起来不像函数的模式
                if not return_type or len(return_type) > 50:
                    continue

                symbol = SymbolInfo(
                    name=func_name,
                    kind=SymbolKind.FUNCTION,
                    location=SourceLocation(
                        file_path=str(result.file_path),
                        line=line_num,
                        column=match.start() + 1
                    ),
                    qualified_name=func_name,
                    type_info=TypeInfo(name=return_type),
                    is_static=('static' in modifiers),
                    is_virtual=('virtual' in modifiers),
                    is_override=('override' in qualifiers),
                    is_final=('final' in qualifiers),
                    is_const=('const' in qualifiers),
                    is_pure_virtual=('=0' in qualifiers),
                    is_inline=('inline' in modifiers),
                    metadata={'parameters': params} if params else {}
                )
                result.symbols.append(symbol)
                result.symbol_map[func_name] = symbol

    def _analyze_with_clang(self, file_path: Path, options: Dict[str, Any]) -> FileAnalysisResult:
        """使用 Clang AST 进行深度分析"""
        from clang import cindex

        result = FileAnalysisResult(file_path=file_path, language="cpp")

        try:
            # 编译参数
            args = options.get('compile_args', [])

            # 尝试加载编译数据库
            compdb_path = options.get('compilation_database')
            if not compdb_path:
                # 尝试在当前目录或父目录查找
                for parent in [file_path.parent] + list(file_path.parents):
                    candidate = parent / 'compile_commands.json'
                    if candidate.exists():
                        compdb_path = candidate
                        break

            if compdb_path and Path(compdb_path).exists():
                try:
                    compdb = cindex.CompilationDatabase.fromDirectory(str(Path(compdb_path).parent))
                    commands = compdb.getCompileCommands(str(file_path))
                    if commands:
                        cmd = list(commands)[0]
                        args = [a for a in cmd.arguments if not a.endswith(('.cpp', '.c', '.cc'))]
                except Exception:
                    pass

            # 默认参数
            if not args:
                args = ['-x', 'c++' if file_path.suffix in {'.cpp', '.cxx', '.cc'} else 'c',
                        '-std=c++17', '-I.', '-I/usr/include', '-I/usr/local/include']

            # 解析文件
            tu = self._clang_index.parse(
                str(file_path),
                args=args,
                options=cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_REMARKS |
                        cindex.TranslationUnit.PARSE_SKIP_FUNCTION_BODIES
            )

            # 收集诊断
            for diag in tu.diagnostics:
                severity_map = {
                    cindex.Diagnostic.Ignored: DiagnosticSeverity.NOTE,
                    cindex.Diagnostic.Note: DiagnosticSeverity.NOTE,
                    cindex.Diagnostic.Warning: DiagnosticSeverity.WARNING,
                    cindex.Diagnostic.Error: DiagnosticSeverity.ERROR,
                    cindex.Diagnostic.Fatal: DiagnosticSeverity.ERROR,
                }
                result.diagnostics.append(Diagnostic(
                    severity=severity_map.get(diag.severity, DiagnosticSeverity.NOTE),
                    message=diag.spelling,
                    location=SourceLocation(
                        file_path=str(diag.location.file.name) if diag.location.file else None,
                        line=diag.location.line,
                        column=diag.location.column,
                        offset=diag.location.offset,
                    ),
                    diagnostic_id=diag.option or '',
                ))

            # 遍历 AST 收集符号
            self._visit_clang_cursor(tu.cursor, result)

            # 统计
            result.line_count = sum(1 for _ in file_path.open('rb'))
            result.function_count = sum(1 for s in result.symbols if s.kind == SymbolKind.FUNCTION)
            result.class_count = sum(1 for s in result.symbols if s.kind in {SymbolKind.CLASS, SymbolKind.STRUCT})

        except Exception as e:
            # Clang 分析失败，降级到正则
            if options.get('fallback_to_regex', True):
                return self._analyze_with_regex(file_path)
            result.success = False
            result.error_message = str(e)

        return result

    def _visit_clang_cursor(self, cursor, result: FileAnalysisResult, parent_name: str = ""):
        """遍历 Clang AST 收集符号"""
        from clang import cindex

        kind = cursor.kind
        spelling = cursor.spelling

        if not spelling:
            # 跳过匿名符号
            if kind not in {cindex.CursorKind.UNION_DECL, cindex.CursorKind.STRUCT_DECL}:
                for child in cursor.get_children():
                    self._visit_clang_cursor(child, result, parent_name)
                return

        # 构建限定名
        qualified_name = f"{parent_name}::{spelling}" if parent_name else spelling

        # 位置信息
        loc = cursor.location
        location = SourceLocation(
            file_path=str(loc.file.name) if loc.file else str(result.file_path),
            line=loc.line,
            column=loc.column,
            offset=loc.offset,
        )

        # 处理不同类型的声明
        if kind == cindex.CursorKind.FUNCTION_DECL:
            result_type = cursor.result_type
            symbol = SymbolInfo(
                name=spelling,
                kind=SymbolKind.FUNCTION,
                location=location,
                qualified_name=qualified_name,
                type_info=TypeInfo(
                    name=result_type.spelling,
                    is_pointer=result_type.kind == cindex.TypeKind.POINTER,
                    is_reference=result_type.kind == cindex.TypeKind.LVALUEREFERENCE,
                ),
                is_static=cursor.is_static_method(),
                is_virtual=cursor.is_virtual_method(),
                is_const=result_type.is_const_qualified(),
                is_inline=cursor.is_inline_function(),
                parent=parent_name,
            )
            result.symbols.append(symbol)
            result.symbol_map[qualified_name] = symbol

        elif kind == cindex.CursorKind.CXX_METHOD:
            result_type = cursor.result_type
            symbol = SymbolInfo(
                name=spelling,
                kind=SymbolKind.METHOD,
                location=location,
                qualified_name=qualified_name,
                type_info=TypeInfo(
                    name=result_type.spelling,
                    is_const=result_type.is_const_qualified(),
                ),
                is_static=cursor.is_static_method(),
                is_virtual=cursor.is_virtual_method(),
                is_pure_virtual=cursor.is_pure_virtual_method(),
                access_specifier=self._get_access_specifier(cursor.access_specifier),
                parent=parent_name,
            )
            result.symbols.append(symbol)
            result.symbol_map[qualified_name] = symbol

        elif kind == cindex.CursorKind.CLASS_DECL:
            symbol = SymbolInfo(
                name=spelling,
                kind=SymbolKind.CLASS,
                location=location,
                qualified_name=qualified_name,
                parent=parent_name,
            )
            result.symbols.append(symbol)
            result.symbol_map[qualified_name] = symbol

        elif kind == cindex.CursorKind.STRUCT_DECL:
            symbol = SymbolInfo(
                name=spelling,
                kind=SymbolKind.STRUCT,
                location=location,
                qualified_name=qualified_name,
                parent=parent_name,
            )
            result.symbols.append(symbol)
            result.symbol_map[qualified_name] = symbol

        elif kind == cindex.CursorKind.UNION_DECL:
            symbol = SymbolInfo(
                name=spelling or "(anonymous_union)",
                kind=SymbolKind.UNION,
                location=location,
                qualified_name=qualified_name,
                parent=parent_name,
            )
            result.symbols.append(symbol)
            result.symbol_map[qualified_name] = symbol

        elif kind == cindex.CursorKind.ENUM_DECL:
            symbol = SymbolInfo(
                name=spelling or "(anonymous_enum)",
                kind=SymbolKind.ENUM,
                location=location,
                qualified_name=qualified_name,
                parent=parent_name,
            )
            result.symbols.append(symbol)
            result.symbol_map[qualified_name] = symbol

        elif kind == cindex.CursorKind.FIELD_DECL:
            field_type = cursor.type
            symbol = SymbolInfo(
                name=spelling,
                kind=SymbolKind.FIELD,
                location=location,
                qualified_name=qualified_name,
                type_info=TypeInfo(
                    name=field_type.spelling,
                    is_pointer=field_type.kind == cindex.TypeKind.POINTER,
                    is_reference=field_type.kind == cindex.TypeKind.LVALUEREFERENCE,
                    is_const=field_type.is_const_qualified(),
                ),
                access_specifier=self._get_access_specifier(cursor.access_specifier),
                parent=parent_name,
            )
            result.symbols.append(symbol)
            result.symbol_map[qualified_name] = symbol

        elif kind == cindex.CursorKind.PARM_DECL:
            # 函数参数（可选收集）
            pass

        elif kind == cindex.CursorKind.NAMESPACE:
            symbol = SymbolInfo(
                name=spelling,
                kind=SymbolKind.NAMESPACE,
                location=location,
                qualified_name=qualified_name,
                parent=parent_name,
            )
            result.symbols.append(symbol)
            result.symbol_map[qualified_name] = symbol

        elif kind == cindex.CursorKind.TYPEDEF_DECL:
            symbol = SymbolInfo(
                name=spelling,
                kind=SymbolKind.TYPEDEF,
                location=location,
                qualified_name=qualified_name,
                parent=parent_name,
            )
            result.symbols.append(symbol)
            result.symbol_map[qualified_name] = symbol

        elif kind == cindex.CursorKind.MACRO_DEFINITION:
            symbol = SymbolInfo(
                name=spelling,
                kind=SymbolKind.MACRO,
                location=location,
                qualified_name=qualified_name,
                parent=parent_name,
            )
            result.symbols.append(symbol)
            result.symbol_map[qualified_name] = symbol

        # 处理 INCLUDE
        elif kind == cindex.CursorKind.INCLUSION_DIRECTIVE:
            include_file = cursor.include_file
            if include_file:
                dep = DependencyInfo(
                    kind="include",
                    target=include_file.name,
                    path=Path(include_file.name) if include_file.name else None,
                    is_system=cursor.displayname.startswith('<'),
                    location=location,
                    resolved=True,
                )
                result.dependencies.append(dep)

        # 递归遍历子节点
        # 注意：对于类/命名空间，传递其名称作为父级
        new_parent = qualified_name if kind in {
            cindex.CursorKind.CLASS_DECL,
            cindex.CursorKind.STRUCT_DECL,
            cindex.CursorKind.NAMESPACE,
        } else parent_name

        for child in cursor.get_children():
            self._visit_clang_cursor(child, result, new_parent)

    def _get_access_specifier(self, clang_access) -> AccessSpecifier:
        """转换 Clang 访问修饰符"""
        from clang import cindex
        access_map = {
            cindex.AccessSpecifier.PUBLIC: AccessSpecifier.PUBLIC,
            cindex.AccessSpecifier.PROTECTED: AccessSpecifier.PROTECTED,
            cindex.AccessSpecifier.PRIVATE: AccessSpecifier.PRIVATE,
        }
        return access_map.get(clang_access, AccessSpecifier.NONE)

    def get_symbols(self, file_path: Path) -> List[SymbolInfo]:
        """获取文件中的所有符号"""
        result = self.analyze_file(file_path)
        return result.symbols if result else []

    def get_dependencies(self, file_path: Path) -> List[DependencyInfo]:
        """获取文件的所有依赖"""
        result = self.analyze_file(file_path)
        return result.dependencies if result else []

    def run_cppcheck(self, file_path: Path) -> List[Diagnostic]:
        """运行 cppcheck 静态分析（如果可用）"""
        diagnostics = []
        try:
            proc = subprocess.run(
                ['cppcheck', '--enable=all', '--output-format=json', str(file_path)],
                capture_output=True,
                text=True,
                timeout=60
            )

            for line in proc.stdout.split('\n'):
                if line.strip():
                    try:
                        data = json.loads(line)
                        if data.get('type') == 'error':
                            sev_map = {
                                'error': DiagnosticSeverity.ERROR,
                                'warning': DiagnosticSeverity.WARNING,
                                'style': DiagnosticSeverity.NOTE,
                                'performance': DiagnosticSeverity.WARNING,
                                'portability': DiagnosticSeverity.NOTE,
                                'information': DiagnosticSeverity.NOTE,
                            }
                            diagnostics.append(Diagnostic(
                                severity=sev_map.get(data.get('severity'), DiagnosticSeverity.NOTE),
                                message=data.get('message', ''),
                                location=SourceLocation(
                                    file_path=data.get('file'),
                                    line=data.get('line', 0),
                                    column=0,
                                ),
                                diagnostic_id=data.get('id', ''),
                            ))
                    except json.JSONDecodeError:
                        pass

        except Exception:
            pass

        return diagnostics

    def get_code_smells(self, file_path: Path) -> List[Dict[str, Any]]:
        """检测 C/C++ 代码异味"""
        result = self.analyze_file(file_path)
        if not result:
            return []

        smells = []
        content = file_path.read_text(encoding='utf-8', errors='ignore')

        # 检测过长函数
        for symbol in result.symbols:
            if symbol.kind == SymbolKind.FUNCTION and symbol.location.line > 0:
                # 简单估算函数长度（不精确）
                patterns = [
                    (rf'\b{symbol.name}\s*\([^)]*\)\s*\{{', 1),  # 定义
                ]
                for pattern, offset in patterns:
                    match = re.search(pattern, content)
                    if match:
                        start = content.count('\n', 0, match.start())
                        # 查找匹配的 }
                        brace_count = 0
                        in_string = False
                        for i, c in enumerate(content[match.start():]):
                            if c == '"' and content[match.start() + i - 1] != '\\':
                                in_string = not in_string
                            if not in_string and c == '{':
                                brace_count += 1
                            elif not in_string and c == '}' and brace_count > 0:
                                brace_count -= 1
                                if brace_count == 0:
                                    end_line = content.count('\n', 0, match.start() + i)
                                    length = end_line - start
                                    if length > 50:
                                        smells.append({
                                            'kind': 'long_function',
                                            'severity': 'warning',
                                            'message': f'函数 "{symbol.name}" 过长 ({length} 行)',
                                            'location': symbol.location,
                                            'threshold': 50,
                                        })
                                    break

        # 检测魔法数字
        magic_numbers = set(re.findall(r'\b\d{4,}\b', content))
        for num in magic_numbers:
            if int(num) not in {2020, 2021, 2022, 2023, 2024, 2025, 1000, 1024}:
                smells.append({
                    'kind': 'magic_number',
                    'severity': 'info',
                    'message': f'魔法数字: {num}',
                    'threshold': 3,
                })

        # 检测嵌套过深
        max_nesting = 0
        current_nesting = 0
        in_comment = False
        in_string = False

        for i, line in enumerate(content.split('\n'), 1):
            # 简单的注释/字符串处理
            j = 0
            while j < len(line):
                c = line[j]
                if c == '"' and (j == 0 or line[j-1] != '\\'):
                    in_string = not in_string
                elif c == '/' and not in_string:
                    if j + 1 < len(line) and line[j+1] == '/':
                        break
                    if j + 1 < len(line) and line[j+1] == '*':
                        in_comment = True
                        j += 1
                elif c == '*' and j + 1 < len(line) and line[j+1] == '/':
                    in_comment = False
                    j += 1
                elif not in_string and not in_comment:
                    if c in '{(':
                        current_nesting += 1
                        max_nesting = max(max_nesting, current_nesting)
                    elif c in ')}':
                        current_nesting -= 1
                j += 1

        if max_nesting > 4:
            smells.append({
                'kind': 'deep_nesting',
                'severity': 'warning',
                'message': f'代码嵌套过深 (深度: {max_nesting})',
                'threshold': 4,
            })

        return smells
