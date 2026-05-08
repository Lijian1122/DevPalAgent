# -*- coding: utf-8 -*-
"""
OpenSpec 语言插件基类 - Phase 6: 多语言支持

定义所有语言插件需要实现的统一接口。
"""

from typing import Any, Dict, List, Optional, Callable, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import abc


class ASTNodeType(Enum):
    """AST 节点类型（统一抽象）"""
    # 基础
    ROOT = "root"
    MODULE = "module"

    # 声明
    FUNCTION_DECL = "function_decl"
    CLASS_DECL = "class_decl"
    STRUCT_DECL = "struct_decl"
    UNION_DECL = "union_decl"
    ENUM_DECL = "enum_decl"
    VAR_DECL = "var_decl"
    TYPEDEF_DECL = "typedef_decl"
    NAMESPACE_DECL = "namespace_decl"
    TEMPLATE_DECL = "template_decl"

    # 语句
    COMPOUND_STMT = "compound_stmt"
    IF_STMT = "if_stmt"
    FOR_STMT = "for_stmt"
    WHILE_STMT = "while_stmt"
    DO_STMT = "do_stmt"
    SWITCH_STMT = "switch_stmt"
    CASE_STMT = "case_stmt"
    BREAK_STMT = "break_stmt"
    CONTINUE_STMT = "continue_stmt"
    RETURN_STMT = "return_stmt"
    TRY_STMT = "try_stmt"
    CATCH_STMT = "catch_stmt"

    # 表达式
    CALL_EXPR = "call_expr"
    BINARY_OPERATOR = "binary_operator"
    UNARY_OPERATOR = "unary_operator"
    MEMBER_EXPR = "member_expr"
    ARRAY_SUBSCRIPT = "array_subscript"
    CAST_EXPR = "cast_expr"
    LITERAL = "literal"
    DECL_REF_EXPR = "decl_ref_expr"

    # 其他
    INCLUDE = "include"
    COMMENT = "comment"
    UNKNOWN = "unknown"


class SymbolKind(Enum):
    """符号种类"""
    FUNCTION = "function"
    CLASS = "class"
    STRUCT = "struct"
    UNION = "union"
    ENUM = "enum"
    VARIABLE = "variable"
    TYPEDEF = "typedef"
    NAMESPACE = "namespace"
    MACRO = "macro"
    ENUM_CONSTANT = "enum_constant"
    FIELD = "field"
    METHOD = "method"
    PARAMETER = "parameter"


class AccessSpecifier(Enum):
    """访问修饰符"""
    PUBLIC = "public"
    PROTECTED = "protected"
    PRIVATE = "private"
    NONE = "none"


class DiagnosticSeverity(Enum):
    """诊断严重级别"""
    ERROR = "error"
    WARNING = "warning"
    NOTE = "note"


@dataclass
class SourceLocation:
    """源代码位置"""
    file_path: Optional[str] = None
    line: int = 0
    column: int = 0
    offset: int = 0

    def __str__(self) -> str:
        if self.file_path:
            return f"{self.file_path}:{self.line}:{self.column}"
        return f":{self.line}:{self.column}"


@dataclass
class SourceRange:
    """源代码范围"""
    start: SourceLocation = field(default_factory=SourceLocation)
    end: SourceLocation = field(default_factory=SourceLocation)


@dataclass
class TypeInfo:
    """类型信息"""
    name: str
    qualified_name: str = ""
    is_pointer: bool = False
    is_reference: bool = False
    is_const: bool = False
    is_volatile: bool = False
    is_array: bool = False
    array_size: Optional[int] = None
    underlying_type: Optional[str] = None  # 指针指向的类型或引用类型
    template_arguments: List[str] = field(default_factory=list)


@dataclass
class SymbolInfo:
    """符号信息"""
    name: str
    kind: SymbolKind
    location: SourceLocation
    qualified_name: str = ""
    type_info: Optional[TypeInfo] = None
    access_specifier: AccessSpecifier = AccessSpecifier.NONE
    is_static: bool = False
    is_virtual: bool = False
    is_override: bool = False
    is_final: bool = False
    is_const: bool = False
    is_pure_virtual: bool = False
    is_inline: bool = False
    parent: Optional[str] = None  # 父符号（如类的成员）
    children: List[str] = field(default_factory=list)  # 子符号
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DependencyInfo:
    """依赖信息"""
    kind: str  # include, import, require, etc.
    target: str
    path: Optional[Path] = None
    is_system: bool = False
    is_relative: bool = False
    location: SourceLocation = field(default_factory=SourceLocation)
    resolved: bool = False


@dataclass
class Diagnostic:
    """诊断信息"""
    severity: DiagnosticSeverity
    message: str
    location: SourceLocation
    range: Optional[SourceRange] = None
    category: str = ""
    diagnostic_id: str = ""
    suggestion: Optional[str] = None


@dataclass
class ASTNode:
    """统一 AST 节点"""
    node_id: str
    node_type: ASTNodeType
    location: SourceLocation
    range: SourceRange
    text: str = ""
    children: List['ASTNode'] = field(default_factory=list)
    parent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def walk(self) -> Callable[[], 'ASTNode']:
        """遍历所有子节点"""
        yield self
        for child in self.children:
            yield from child.walk()

    def find_by_type(self, node_type: ASTNodeType) -> List['ASTNode']:
        """按类型查找节点"""
        return [n for n in self.walk() if n.node_type == node_type]


@dataclass
class FileAnalysisResult:
    """文件分析结果"""
    file_path: Path
    language: str
    success: bool = True
    error_message: Optional[str] = None

    # AST
    ast_root: Optional[ASTNode] = None

    # 符号
    symbols: List[SymbolInfo] = field(default_factory=list)
    symbol_map: Dict[str, SymbolInfo] = field(default_factory=dict)

    # 依赖
    dependencies: List[DependencyInfo] = field(default_factory=list)
    reverse_dependencies: List[Path] = field(default_factory=list)

    # 诊断
    diagnostics: List[Diagnostic] = field(default_factory=list)

    # 统计
    line_count: int = 0
    function_count: int = 0
    class_count: int = 0
    comment_count: int = 0

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)


class LanguagePlugin(abc.ABC):
    """语言插件基类"""

    @abc.abstractmethod
    def get_language_id(self) -> str:
        """返回语言唯一标识，如 'cpp', 'python'"""
        pass

    @abc.abstractmethod
    def get_language_name(self) -> str:
        """返回语言显示名称"""
        pass

    @abc.abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """返回支持的文件扩展名，如 ['.cpp', '.h', '.hpp']"""
        pass

    @abc.abstractmethod
    def is_available(self) -> bool:
        """检查该语言插件是否可用（依赖是否安装等）"""
        pass

    @abc.abstractmethod
    def analyze_file(self, file_path: Path, options: Optional[Dict[str, Any]] = None) -> FileAnalysisResult:
        """分析单个文件"""
        pass

    @abc.abstractmethod
    def get_symbols(self, file_path: Path) -> List[SymbolInfo]:
        """获取文件中的所有符号"""
        pass

    @abc.abstractmethod
    def get_dependencies(self, file_path: Path) -> List[DependencyInfo]:
        """获取文件的所有依赖"""
        pass

    def find_symbol_definition(self, symbol_name: str, file_path: Optional[Path] = None) -> Optional[SymbolInfo]:
        """查找符号定义位置（可选实现）"""
        return None

    def find_symbol_references(self, symbol_name: str, file_path: Optional[Path] = None) -> List[SourceLocation]:
        """查找符号引用（可选实现）"""
        return []

    def calculate_cyclomatic_complexity(self, function_node: ASTNode) -> int:
        """计算圈复杂度（可选实现）"""
        # 默认实现：统计分支语句
        complexity = 1
        branch_types = {
            ASTNodeType.IF_STMT,
            ASTNodeType.FOR_STMT,
            ASTNodeType.WHILE_STMT,
            ASTNodeType.DO_STMT,
            ASTNodeType.CASE_STMT,
            ASTNodeType.CATCH_STMT,
        }
        for node in function_node.walk():
            if node.node_type in branch_types:
                complexity += 1
        return complexity

    def get_code_smells(self, file_path: Path) -> List[Dict[str, Any]]:
        """检测代码异味（可选实现）"""
        return []


class LanguagePluginManager:
    """语言插件管理器"""

    def __init__(self):
        self._plugins: Dict[str, LanguagePlugin] = {}
        self._extension_map: Dict[str, str] = {}  # 扩展名 -> 语言ID

    def register_plugin(self, plugin: LanguagePlugin) -> bool:
        """注册语言插件"""
        if not plugin.is_available():
            return False

        lang_id = plugin.get_language_id()
        self._plugins[lang_id] = plugin

        for ext in plugin.get_supported_extensions():
            self._extension_map[ext] = lang_id

        return True

    def unregister_plugin(self, language_id: str) -> bool:
        """注销语言插件"""
        if language_id not in self._plugins:
            return False

        plugin = self._plugins[language_id]
        for ext in plugin.get_supported_extensions():
            if ext in self._extension_map:
                del self._extension_map[ext]

        del self._plugins[language_id]
        return True

    def get_plugin(self, language_id: str) -> Optional[LanguagePlugin]:
        """根据语言 ID 获取插件"""
        return self._plugins.get(language_id)

    def get_plugin_for_file(self, file_path: Path) -> Optional[LanguagePlugin]:
        """根据文件扩展名获取插件"""
        ext = file_path.suffix.lower()
        lang_id = self._extension_map.get(ext)
        if lang_id:
            return self._plugins.get(lang_id)
        return None

    def get_available_languages(self) -> List[str]:
        """获取所有可用语言"""
        return list(self._plugins.keys())

    def get_supported_extensions(self) -> List[str]:
        """获取所有支持的扩展名"""
        return list(self._extension_map.keys())

    def analyze_file(self, file_path: Path, options: Optional[Dict[str, Any]] = None) -> Optional[FileAnalysisResult]:
        """分析文件"""
        plugin = self.get_plugin_for_file(file_path)
        if not plugin:
            return None
        return plugin.analyze_file(file_path, options)

    def analyze_directory(self, dir_path: Path, recursive: bool = True) -> Dict[Path, FileAnalysisResult]:
        """分析整个目录"""
        results = {}
        pattern = "**/*" if recursive else "*"

        for file_path in dir_path.glob(pattern):
            if file_path.is_file():
                plugin = self.get_plugin_for_file(file_path)
                if plugin:
                    result = plugin.analyze_file(file_path)
                    results[file_path] = result

        return results

    def build_dependency_graph(self, root_path: Path) -> Dict[Path, Set[Path]]:
        """构建项目依赖图"""
        graph: Dict[Path, Set[Path]] = {}
        results = self.analyze_directory(root_path)

        for file_path, result in results.items():
            deps = set()
            for dep in result.dependencies:
                if dep.path:
                    deps.add(dep.path)
            graph[file_path] = deps

        return graph

    def get_affected_files(self, changed_file: Path, root_path: Path) -> List[Path]:
        """获取受影响的文件列表"""
        graph = self.build_dependency_graph(root_path)
        affected: List[Path] = []

        for file_path, deps in graph.items():
            if changed_file in deps:
                affected.append(file_path)

        return affected
