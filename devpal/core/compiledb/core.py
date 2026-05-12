# -*- coding: utf-8 -*-
"""
CompileDB 核心类

提供代码符号索引、缓存和查询功能。
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum


class SymbolType(Enum):
    """符号类型"""
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    CONSTANT = "constant"
    ENUM = "enum"
    STRUCT = "struct"
    UNION = "union"
    TYPEDEF = "typedef"
    NAMESPACE = "namespace"
    MODULE = "module"
    INTERFACE = "interface"


@dataclass
class SymbolInfo:
    """符号信息"""
    name: str
    type: SymbolType
    file_path: str
    line_start: int
    line_end: int = 0
    column: int = 0
    signature: str = ""
    docstring: str = ""
    parent: Optional[str] = None  # 父符号（如类的方法）
    modifiers: List[str] = field(default_factory=list)  # public/private/static 等

    def __post_init__(self):
        if self.line_end == 0:
            self.line_end = self.line_start

    def to_dict(self) -> dict:
        """序列化到字典"""
        data = asdict(self)
        data['type'] = self.type.value  # 枚举转字符串
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'SymbolInfo':
        """从字典反序列化"""
        data['type'] = SymbolType(data['type'])  # 字符串转枚举
        return cls(**data)


class CompileDB:
    """
    代码符号数据库

    功能:
    1. 索引项目中的所有符号
    2. 按名称、类型、文件查询符号
    3. 分析文件依赖关系
    4. 计算最佳插入位置
    5. 本地缓存索引，加速重复查询
    """

    DEFAULT_CACHE_NAME = ".compiledb_cache.json"  # 已废弃，现在按项目名存储在 .spec 目录

    def __init__(self, cache_dir: str = None):
        self._symbols: Dict[str, List[SymbolInfo]] = {}  # name -> [SymbolInfo]
        self._file_symbols: Dict[str, List[SymbolInfo]] = {}  # filepath -> [SymbolInfo]
        self._dependencies: Dict[str, List[str]] = {}  # filepath -> [dependencies]
        self._indexed_files: set = set()
        self._file_hashes: Dict[str, str] = {}  # filepath -> file hash
        self._cache_dir = Path(cache_dir) if cache_dir else None
        self._cache_loaded = False

    def index_project(self, project_path: Path, file_patterns: List[str] = None,
                       use_cache: bool = True) -> int:
        """
        索引整个项目

        Args:
            project_path: 项目根目录
            file_patterns: 文件模式列表，如 ["*.py", "*.h", "*.cpp"]
            use_cache: 是否使用本地缓存

        Returns:
            索引的符号总数
        """
        if file_patterns is None:
            file_patterns = ["*.py", "*.h", "*.hpp", "*.cpp", "*.cc", "*.cxx", "*.c"]

        project_path = Path(project_path)

        # 尝试加载缓存
        if use_cache:
            cache_loaded = self.load_cache(project_path)
            if cache_loaded:
                print(f"[CompileDB] 从缓存加载: {len(self._symbols)} 个符号")

        total_symbols = 0
        files_to_index = []

        # 收集需要索引的文件
        for pattern in file_patterns:
            for file_path in project_path.rglob(pattern):
                if file_path.is_file():
                    files_to_index.append(file_path)

        # 增量索引：只索引变化的文件
        for file_path in files_to_index:
            if use_cache and self._is_file_cached(file_path):
                continue  # 缓存命中，跳过
            total_symbols += self.index_file(file_path)

        # 保存缓存
        if use_cache and (total_symbols > 0 or not self._cache_loaded):
            self.save_cache(project_path)

        # 返回总符号数（包括缓存和新索引的
        return len(self.get_all_symbols())

    def index_file(self, file_path: Path) -> int:
        """
        索引单个文件

        Args:
            file_path: 文件路径

        Returns:
            该文件中的符号数量
        """
        file_path = Path(file_path)
        file_str = str(file_path)

        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            file_hash = self._compute_file_hash(content)

            # 如果文件未变化，使用缓存
            if file_str in self._indexed_files and \
               self._file_hashes.get(file_str) == file_hash:
                return len(self._file_symbols.get(file_str, []))

            suffix = file_path.suffix.lower()

            if suffix in ['.py']:
                from .parsers import PythonParser
                parser = PythonParser()
                symbols = parser.parse(content, file_str)
            elif suffix in ['.h', '.hpp', '.cpp', '.cc', '.cxx']:
                from .parsers import CppParser
                parser = CppParser()
                symbols = parser.parse(content, file_str)
            else:
                return 0

            # 存储符号
            self._file_symbols[file_str] = symbols
            for symbol in symbols:
                if symbol.name not in self._symbols:
                    self._symbols[symbol.name] = []
                self._symbols[symbol.name].append(symbol)

            # 分析依赖
            self._dependencies[file_str] = self._extract_dependencies(content, suffix)
            self._indexed_files.add(file_str)
            self._file_hashes[file_str] = file_hash

            return len(symbols)

        except Exception as e:
            print(f"[CompileDB] 索引文件失败 {file_path}: {e}")
            return 0

    def _compute_file_hash(self, content: str) -> str:
        """计算文件内容的哈希值"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def _is_file_cached(self, file_path: Path) -> bool:
        """检查文件是否在缓存中且未变化"""
        file_str = str(file_path)
        if file_str not in self._file_hashes:
            return False
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            current_hash = self._compute_file_hash(content)
            return current_hash == self._file_hashes[file_str]
        except:
            return False

    def save_cache(self, project_path: Path) -> bool:
        """
        保存索引到本地缓存文件

        Args:
            project_path: 项目根目录

        Returns:
            是否保存成功
        """
        try:
            cache_file = self._get_cache_path(project_path)
            cache_file.parent.mkdir(parents=True, exist_ok=True)

            cache_data = {
                'version': '1.0',
                'file_hashes': self._file_hashes,
                'indexed_files': list(self._indexed_files),
                'dependencies': self._dependencies,
                'symbols': {
                    name: [s.to_dict() for s in symbols]
                    for name, symbols in self._symbols.items()
                },
                'file_symbols': {
                    path: [s.to_dict() for s in symbols]
                    for path, symbols in self._file_symbols.items()
                }
            }

            cache_file.write_text(json.dumps(cache_data, indent=2, ensure_ascii=False),
                                  encoding='utf-8')
            print(f"[CompileDB] 缓存已保存: {cache_file}")
            return True

        except Exception as e:
            print(f"[CompileDB] 保存缓存失败: {e}")
            return False

    def load_cache(self, project_path: Path) -> bool:
        """
        从本地缓存加载索引

        Args:
            project_path: 项目根目录

        Returns:
            是否加载成功
        """
        try:
            cache_file = self._get_cache_path(project_path)
            if not cache_file.exists():
                return False

            cache_data = json.loads(cache_file.read_text(encoding='utf-8'))

            # 版本检查
            if cache_data.get('version') != '1.0':
                print(f"[CompileDB] 缓存版本不兼容，跳过加载")
                return False

            # 加载数据
            self._file_hashes = cache_data.get('file_hashes', {})
            self._indexed_files = set(cache_data.get('indexed_files', []))
            self._dependencies = cache_data.get('dependencies', {})

            # 反序列化符号
            self._symbols = {}
            for name, symbol_dicts in cache_data.get('symbols', {}).items():
                self._symbols[name] = [SymbolInfo.from_dict(d) for d in symbol_dicts]

            self._file_symbols = {}
            for path, symbol_dicts in cache_data.get('file_symbols', {}).items():
                self._file_symbols[path] = [SymbolInfo.from_dict(d) for d in symbol_dicts]

            self._cache_loaded = True
            return True

        except Exception as e:
            print(f"[CompileDB] 加载缓存失败: {e}")
            return False

    def _get_cache_path(self, project_path: Path) -> Path:
        """获取缓存文件路径"""
        project_name = project_path.name
        cache_filename = f".compiledb_{project_name}.json"

        if self._cache_dir:
            return Path(self._cache_dir) / cache_filename

        spec_dir = project_path / ".spec"
        spec_dir.mkdir(parents=True, exist_ok=True)
        return spec_dir / cache_filename

    def clear_cache(self, project_path: Path = None) -> bool:
        """
        清除本地缓存

        Args:
            project_path: 项目根目录（可选，不传则清除当前实例的内存缓存）

        Returns:
            是否清除成功
        """
        # 清除内存中的缓存
        self._symbols.clear()
        self._file_symbols.clear()
        self._dependencies.clear()
        self._indexed_files.clear()
        self._file_hashes.clear()
        self._cache_loaded = False

        # 清除磁盘缓存
        if project_path:
            try:
                cache_file = self._get_cache_path(project_path)
                if cache_file.exists():
                    cache_file.unlink()
                    print(f"[CompileDB] 缓存已清除: {cache_file}")
                return True
            except Exception as e:
                print(f"[CompileDB] 清除缓存失败: {e}")
                return False

        return True

    def find_symbol(self, name: str, exact_match: bool = True) -> List[SymbolInfo]:
        """
        查找符号

        Args:
            name: 符号名称
            exact_match: 是否精确匹配

        Returns:
            匹配的符号列表
        """
        if exact_match:
            return self._symbols.get(name, []).copy()
        else:
            results = []
            for symbol_name, symbols in self._symbols.items():
                if name.lower() in symbol_name.lower():
                    results.extend(symbols)
            return results

    def get_file_symbols(self, file_path: str, symbol_type: SymbolType = None) -> List[SymbolInfo]:
        """
        获取单个文件的所有符号

        Args:
            file_path: 文件路径
            symbol_type: 可选，按类型过滤

        Returns:
            符号列表
        """
        symbols = self._file_symbols.get(file_path, [])
        if symbol_type:
            return [s for s in symbols if s.type == symbol_type]
        return symbols.copy()

    def get_dependencies(self, file_path: str) -> List[str]:
        """
        获取文件的依赖关系

        Args:
            file_path: 文件路径

        Returns:
            依赖的文件路径列表
        """
        return self._dependencies.get(file_path, []).copy()

    def can_insert_function(self, file_path: str, func_name: str) -> bool:
        """
        检查函数是否已存在

        Args:
            file_path: 文件路径
            func_name: 函数名称

        Returns:
            True 表示可以插入（不存在），False 表示已存在
        """
        existing = self.find_symbol(func_name)
        for symbol in existing:
            if symbol.file_path == file_path and symbol.type in [SymbolType.FUNCTION, SymbolType.METHOD]:
                return False
        return True

    def get_insert_position(self, file_path: str, after: str = None, insert_type: str = "function") -> int:
        """
        获取最佳代码插入行号

        Args:
            file_path: 文件路径
            after: 在指定符号后插入
            insert_type: 插入类型 ("function", "class", "include")

        Returns:
            推荐的行号（从 1 开始）
        """
        symbols = self.get_file_symbols(file_path)

        if not symbols:
            # 空文件，在末尾插入
            try:
                content = Path(file_path).read_text(encoding='utf-8', errors='ignore')
                return len(content.splitlines()) + 1
            except:
                return 1

        if after:
            # 在指定符号后插入
            for symbol in symbols:
                if symbol.name == after:
                    return symbol.line_end + 1

        # 默认策略：在文件末尾的最后一个符号后插入
        max_line = max(s.line_end for s in symbols)
        return max_line + 1

    def get_all_files(self) -> List[str]:
        """获取所有已索引文件"""
        return list(self._indexed_files)

    def get_all_symbols(self) -> List[SymbolInfo]:
        """获取所有符号"""
        all_symbols = []
        for symbols in self._symbols.values():
            all_symbols.extend(symbols)
        return all_symbols

    def clear(self):
        """清空索引"""
        self._symbols.clear()
        self._file_symbols.clear()
        self._dependencies.clear()
        self._indexed_files.clear()

    def _extract_dependencies(self, content: str, suffix: str) -> List[str]:
        """提取文件依赖关系"""
        import re
        deps = []

        if suffix == '.py':
            # Python: import / from ... import
            for line in content.splitlines():
                line = line.strip()
                if line.startswith('import '):
                    match = re.match(r'import\s+([\w\.]+)', line)
                    if match:
                        deps.append(match.group(1))
                elif line.startswith('from '):
                    match = re.match(r'from\s+([\w\.]+)\s+import', line)
                    if match:
                        deps.append(match.group(1))

        elif suffix in ['.h', '.hpp', '.cpp', '.cc', '.cxx']:
            # C++: #include
            for line in content.splitlines():
                line = line.strip()
                if line.startswith('#include'):
                    match = re.match(r'#include\s*["<]([^">]+)[">]', line)
                    if match:
                        deps.append(match.group(1))

        return deps
