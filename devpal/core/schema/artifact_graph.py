from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable, Iterator
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import sqlite3
import hashlib
from datetime import datetime

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    # Fallback: simple DAG implementation if networkx is not available
    class SimpleDiGraph:
        def __init__(self):
            self._nodes: Set[str] = set()
            self._edges: Dict[str, List[Tuple[str, Dict]]] = {}  # from -> list of (to, data)
            self._in_edges: Dict[str, List[Tuple[str, Dict]]] = {}  # to -> list of (from, data)

        def add_node(self, node_id: str, **attrs):
            self._nodes.add(node_id)
            if node_id not in self._edges:
                self._edges[node_id] = []
            if node_id not in self._in_edges:
                self._in_edges[node_id] = []

        def add_edge(self, from_node: str, to_node: str, **attrs):
            if from_node not in self._nodes:
                self.add_node(from_node)
            if to_node not in self._nodes:
                self.add_node(to_node)
            self._edges[from_node].append((to_node, attrs))
            self._in_edges[to_node].append((from_node, attrs))

        def has_node(self, node_id: str) -> bool:
            return node_id in self._nodes

        def nodes(self, data: bool = False):
            if data:
                return [(n, {}) for n in self._nodes]
            return list(self._nodes)

        def edges(self, data: bool = False):
            all_edges = []
            for from_node, edges in self._edges.items():
                for to_node, attrs in edges:
                    if data:
                        all_edges.append((from_node, to_node, attrs))
                    else:
                        all_edges.append((from_node, to_node))
            return all_edges

        def out_edges(self, node_id: str, data: bool = False):
            edges = self._edges.get(node_id, [])
            if data:
                return [(node_id, to_node, attrs) for to_node, attrs in edges]
            return [(node_id, to_node) for to_node, _ in edges]

        def in_edges(self, node_id: str, data: bool = False):
            edges = self._in_edges.get(node_id, [])
            if data:
                return [(from_node, node_id, attrs) for from_node, attrs in edges]
            return [(from_node, node_id) for from_node, _ in edges]

        def descendants(self, node_id: str) -> Set[str]:
            visited: Set[str] = set()
            stack = [node_id]
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                for next_node, _ in self._edges.get(current, []):
                    if next_node not in visited:
                        stack.append(next_node)
            visited.discard(node_id)
            return visited


class ArtifactType(Enum):
    REQUIREMENT = "requirement"  # 需求文档
    CODE = "code"                # 源代码
    TEST = "test"                # 测试代码
    DOC = "doc"                  # 文档
    CONFIG = "config"            # 配置文件
    SPEC = "spec"                # 规范文件
    ASSET = "asset"              # 静态资源


class DependencyType(Enum):
    IMPLEMENTS = "implements"    # 代码实现需求
    TESTS = "tests"              # 测试验证代码
    REFERENCES = "references"    # 文档引用代码
    DEPENDS_ON = "depends_on"    # 代码依赖其他代码
    INCLUDES = "includes"        # 头文件包含
    EXTENDS = "extends"          # 继承关系
    IMPORTS = "imports"          # 导入关系
    GENERATES = "generates"      # 从模板生成


@dataclass
class ArtifactNode:
    """工件节点 - 代表项目中的一个文件或模块"""
    id: str  # 唯一标识符，如 "file:src/main.cpp" 或 "req:login"
    type: ArtifactType
    path: Optional[Path] = None
    name: str = ""
    description: str = ""
    version: str = "1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.type.value,
            'path': str(self.path) if self.path else None,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArtifactNode':
        return cls(
            id=data['id'],
            type=ArtifactType(data['type']),
            path=Path(data['path']) if data.get('path') else None,
            name=data.get('name', ''),
            description=data.get('description', ''),
            version=data.get('version', '1.0'),
            metadata=data.get('metadata', {})
        )


class ArtifactGraph:
    """工件依赖图 - 管理项目中所有工件的依赖关系

    典型依赖链:
    REQUIREMENT (req:login)
        ↳ IMPLEMENTS → CODE (file:src/login.cpp)
                           ↳ TESTS → TEST (file:tests/test_login.cpp)
                           ↳ REFERENCES → DOC (file:docs/login.md)
    """

    def __init__(self):
        if NETWORKX_AVAILABLE:
            self._graph = nx.DiGraph()
        else:
            self._graph = SimpleDiGraph()
        self._nodes: Dict[str, ArtifactNode] = {}

    def add_node(self, node: ArtifactNode):
        """添加工件节点"""
        self._nodes[node.id] = node
        self._graph.add_node(node.id, **node.to_dict())

    def get_node(self, node_id: str) -> Optional[ArtifactNode]:
        """获取节点"""
        return self._nodes.get(node_id)

    def add_dependency(self, from_id: str, to_id: str, dep_type: DependencyType,
                      metadata: Dict[str, Any] = None):
        """添加依赖关系: from_id --dep_type--> to_id"""
        if from_id not in self._nodes or to_id not in self._nodes:
            raise ValueError(f"节点不存在: {from_id} 或 {to_id}")

        edge_data = {
            'type': dep_type.value,
            **(metadata or {})
        }
        self._graph.add_edge(from_id, to_id, **edge_data)

    def get_affected_artifacts(self, changed_id: str) -> List[ArtifactNode]:
        """获取变更影响的所有工件（正向传播）

        当某个工件变更时，找出所有受影响的工件
        例如: 修改代码 → 受影响的测试、文档都需要更新
        """
        if changed_id not in self._nodes:
            return []

        # 所有可达节点 = 受影响的工件
        if NETWORKX_AVAILABLE:
            affected_ids = nx.descendants(self._graph, changed_id)
        else:
            affected_ids = self._graph.descendants(changed_id)
        return [self._nodes[id] for id in affected_ids]

    def get_impact_chain(self, changed_id: str) -> List[Tuple[ArtifactNode, DependencyType]]:
        """获取完整的影响链"""
        if changed_id not in self._nodes:
            return []

        chain = []
        visited = set()
        queue = [(changed_id, None)]

        while queue:
            node_id, dep_type = queue.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)

            if node_id in self._nodes:
                chain.append((self._nodes[node_id], dep_type))

            # 遍历所有出边
            for _, to_id, data in self._graph.out_edges(node_id, data=True):
                if to_id not in visited:
                    edge_type = DependencyType(data.get('type', 'depends_on'))
                    queue.append((to_id, edge_type))

        return chain

    def get_dependencies(self, node_id: str) -> List[Tuple[ArtifactNode, DependencyType]]:
        """获取节点的所有依赖（该节点依赖于什么）"""
        if node_id not in self._nodes:
            return []

        result = []
        for _, to_id, data in self._graph.out_edges(node_id, data=True):
            dep_type = DependencyType(data.get('type', 'depends_on'))
            result.append((self._nodes[to_id], dep_type))
        return result

    def get_dependents(self, node_id: str) -> List[Tuple[ArtifactNode, DependencyType]]:
        """获取所有依赖于该节点的节点（谁依赖它）"""
        if node_id not in self._nodes:
            return []

        result = []
        for from_id, _, data in self._graph.in_edges(node_id, data=True):
            dep_type = DependencyType(data.get('type', 'depends_on'))
            result.append((self._nodes[from_id], dep_type))
        return result

    def find_by_type(self, type_filter: ArtifactType) -> List[ArtifactNode]:
        """按类型查找节点"""
        return [n for n in self._nodes.values() if n.type == type_filter]

    def find_by_path(self, path_pattern: str) -> List[ArtifactNode]:
        """按路径模式查找"""
        results = []
        for node in self._nodes.values():
            if node.path and path_pattern in str(node.path):
                results.append(node)
        return results

    def discover_from_directory(self, root_dir: Union[str, Path]):
        """从项目目录自动发现工件并构建依赖图"""
        root = Path(root_dir)

        # 发现源代码文件
        code_extensions = {'.py', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.c', '.java', '.js', '.ts'}
        for ext in code_extensions:
            for code_file in root.rglob(f'*{ext}'):
                if code_file.is_file() and 'test' not in code_file.name.lower():
                    rel_path = code_file.relative_to(root)
                    node = ArtifactNode(
                        id=f"file:{rel_path}",
                        type=ArtifactType.CODE,
                        path=code_file,
                        name=code_file.name,
                        description=f"源代码文件 {ext}"
                    )
                    self.add_node(node)

        # 发现测试文件
        test_patterns = ['test_', '_test.', 'tests/', 'spec/']
        for ext in code_extensions:
            for test_file in root.rglob(f'*{ext}'):
                if test_file.is_file() and any(p in test_file.name.lower() or p in str(test_file).lower() for p in test_patterns):
                    rel_path = test_file.relative_to(root)
                    node = ArtifactNode(
                        id=f"file:{rel_path}",
                        type=ArtifactType.TEST,
                        path=test_file,
                        name=test_file.name,
                        description=f"测试代码文件 {ext}"
                    )
                    self.add_node(node)

                    # 推断对应的代码文件
                    base_name = test_file.stem.replace('test_', '').replace('_test', '')
                    for code_file in root.rglob(f'{base_name}.*'):
                        if code_file != test_file and code_file.suffix in code_extensions:
                            code_rel = code_file.relative_to(root)
                            code_id = f"file:{code_rel}"
                            if code_id in self._nodes:
                                self.add_dependency(node.id, code_id, DependencyType.TESTS)

        # 发现需求文档
        for doc_file in root.rglob("docs/req_*.md"):
            rel_path = doc_file.relative_to(root)
            req_id = f"req:{doc_file.stem.replace('req_', '')}"
            node = ArtifactNode(
                id=req_id,
                type=ArtifactType.REQUIREMENT,
                path=doc_file,
                name=doc_file.stem,
                description=f"需求文档 {doc_file.name}"
            )
            self.add_node(node)

        # 发现文档文件
        doc_extensions = {'.md', '.rst', '.txt', '.rst'}
        for ext in doc_extensions:
            for doc_file in root.rglob(f'*{ext}'):
                if doc_file.is_file() and not doc_file.name.startswith('req_'):
                    rel_path = doc_file.relative_to(root)
                    node_id = f"file:{rel_path}"
                    if node_id not in self._nodes:
                        node = ArtifactNode(
                            id=node_id,
                            type=ArtifactType.DOC,
                            path=doc_file,
                            name=doc_file.name,
                            description=f"文档文件 {ext}"
                        )
                        self.add_node(node)

        # 发现配置文件
        config_extensions = {'.json', '.yaml', '.yml', '.ini', '.toml', '.conf'}
        for ext in config_extensions:
            for config_file in root.rglob(f'*{ext}'):
                if config_file.is_file():
                    rel_path = config_file.relative_to(root)
                    node = ArtifactNode(
                        id=f"file:{rel_path}",
                        type=ArtifactType.CONFIG,
                        path=config_file,
                        name=config_file.name,
                        description=f"配置文件 {ext}"
                    )
                    self.add_node(node)

    def auto_detect_dependencies(self):
        """自动检测文件间的依赖关系"""
        for node_id, node in self._nodes.items():
            if not node.path or not node.path.exists():
                continue

            try:
                content = node.path.read_text(encoding='utf-8', errors='ignore')
            except:
                continue

            # Python imports
            if node.path.suffix == '.py':
                import re
                imports = re.findall(r'(?:from|import)\s+(\w+)', content)
                for imp in imports:
                    for other_id, other_node in self._nodes.items():
                        if other_id != node_id and other_node.path:
                            if other_node.path.stem == imp or other_node.path.name in (f'{imp}.py', f'{imp}.pyc'):
                                self.add_dependency(node_id, other_id, DependencyType.IMPORTS)

            # C/C++ includes
            elif node.path.suffix in {'.cpp', '.cc', '.c', '.h', '.hpp', '.cxx'}:
                import re
                includes = re.findall(r'#include\s*["<]([^">]+)[">]', content)
                for inc in includes:
                    inc_path = Path(inc)
                    for other_id, other_node in self._nodes.items():
                        if other_id != node_id and other_node.path:
                            if other_node.path.name == inc_path.name or other_node.path.match(f'**/{inc}'):
                                self.add_dependency(node_id, other_id, DependencyType.INCLUDES)

    def link_requirements_to_code(self, req_patterns: Optional[List[str]] = None):
        """需求 → 代码 双向关联

        在代码文件中查找需求 ID 引用，自动建立:
        - 代码 → 需求 (IMPLEMENTS 关系)
        - 测试 → 需求 (TESTS 关系)

        Args:
            req_patterns: 需求 ID 匹配模式列表，默认支持 REQ-XXX、RXX 格式
        """
        import re

        default_patterns = [
            r'REQUIREMENT\s*[:=]\s*([A-Z0-9-]+)',
            r'REQS?\s*[:=]\s*([A-Z0-9-,\s]+)',
            r'REQUIREMENT_ID\s*[:=]\s*([A-Z0-9-]+)',
            r'IMPLEMENTS\s*[:=]\s*([A-Z0-9-]+)',
        ]

        patterns = req_patterns or default_patterns
        compiled_patterns = [re.compile(p, re.IGNORECASE) for p in patterns]

        # 找出所有需求节点
        req_nodes = {
            node.id.replace('req:', ''): node.id
            for node in self._nodes.values()
            if node.type == ArtifactType.REQUIREMENT
        }

        # 遍历代码文件，查找需求引用
        for node_id, node in self._nodes.items():
            if node.type not in {ArtifactType.CODE, ArtifactType.TEST}:
                continue

            if not node.path or not node.path.exists():
                continue

            try:
                content = node.path.read_text(encoding='utf-8', errors='ignore')
            except:
                continue

            # 查找需求 ID 引用
            matched_reqs = set()
            for pattern in compiled_patterns:
                for match in pattern.finditer(content):
                    # 如果有捕获组，使用第一个；否则使用整个匹配
                    if match.groups():
                        req_id = match.group(1).strip().upper()
                    else:
                        req_id = match.group(0).strip().upper()
                    matched_reqs.add(req_id)

            # 查找内联需求编号 (如 // REQ-001: 或 // #REQ-001)
            inline_pattern = re.compile(r'(?:#|//|/\*|\*)?\s*(REQ-[A-Z0-9-]+)\b', re.IGNORECASE)
            for match in inline_pattern.finditer(content):
                matched_reqs.add(match.group(1).strip().upper())

            # 建立关联
            for req_id in matched_reqs:
                # 精确匹配
                if req_id in req_nodes:
                    target_req_id = req_nodes[req_id]
                    if node.type == ArtifactType.TEST:
                        self.add_dependency(node_id, target_req_id, DependencyType.TESTS)
                    else:
                        self.add_dependency(node_id, target_req_id, DependencyType.IMPLEMENTS)
                    continue

                # 前缀匹配 (查找最接近的需求 ID)
                for req_key, target_req_id in req_nodes.items():
                    if req_id in req_key or req_key in req_id:
                        if node.type == ArtifactType.TEST:
                            self.add_dependency(node_id, target_req_id, DependencyType.TESTS)
                        else:
                            self.add_dependency(node_id, target_req_id, DependencyType.IMPLEMENTS)
                        break

    def get_requirements_for_code(self, code_node_id: str) -> List[ArtifactNode]:
        """获取某段代码实现的所有需求

        用于: 代码变更时，找出对应的需求验证项
        """
        req_list = []
        for dep, dep_type in self.get_dependencies(code_node_id):
            if dep_type == DependencyType.IMPLEMENTS and dep.type == ArtifactType.REQUIREMENT:
                req_list.append(dep)
        return req_list

    def get_code_for_requirement(self, req_node_id: str) -> List[ArtifactNode]:
        """获取实现某个需求的所有代码文件

        用于: 需求变更时，找出需要更新的代码文件
        """
        code_list = []
        for dependent, dep_type in self.get_dependents(req_node_id):
            if dep_type == DependencyType.IMPLEMENTS and dependent.type == ArtifactType.CODE:
                code_list.append(dependent)
        return code_list

    def get_tests_for_requirement(self, req_node_id: str) -> List[ArtifactNode]:
        """获取测试某个需求的所有测试文件

        用于: 需求变更时，找出需要更新/运行的测试
        """
        test_list = []
        for dependent, dep_type in self.get_dependents(req_node_id):
            if dep_type == DependencyType.TESTS and dependent.type == ArtifactType.TEST:
                test_list.append(dependent)
        return test_list

    def analyze_requirement_change_impact(self, changed_req_ids: List[str]) -> Dict[str, List[ArtifactNode]]:
        """分析需求变更的影响范围

        Returns:
            {
                'affected_code': [...],  受影响的代码文件
                'affected_tests': [...], 受影响的测试文件
                'affected_docs': [...],  受影响的文档 (如果有关联)
            }
        """
        result = {
            'affected_code': [],
            'affected_tests': [],
            'affected_docs': [],
        }

        for req_id in changed_req_ids:
            if req_id not in self._nodes:
                continue

            # 获取直接依赖
            for dependent, dep_type in self.get_dependents(req_id):
                if dependent.type == ArtifactType.CODE:
                    result['affected_code'].append(dependent)
                elif dependent.type == ArtifactType.TEST:
                    result['affected_tests'].append(dependent)
                elif dependent.type == ArtifactType.DOC:
                    result['affected_docs'].append(dependent)

            # 找出受影响的其他工件（间接依赖）
            for dependent, dep_type in self.get_dependents(req_id):
                if dependent.type == ArtifactType.CODE:
                    # 代码变更可能影响其他依赖它的代码
                    for further, _ in self.get_affected_artifacts(dependent.id):
                        if further not in result['affected_code']:
                            result['affected_code'].append(further)

        # 去重
        result['affected_code'] = list({n.id: n for n in result['affected_code']}.values())
        result['affected_tests'] = list({n.id: n for n in result['affected_tests']}.values())
        result['affected_docs'] = list({n.id: n for n in result['affected_docs']}.values())

        return result

    def analyze_code_change_impact(self, changed_code_ids: List[str]) -> Dict[str, Any]:
        """分析代码变更的影响范围

        Returns:
            {
                'affected_requirements': [...],  受影响的需求
                'affected_tests': [...],         受影响的测试
                'test_coverage_impact': [...],   受影响的测试覆盖率项
            }
        """
        result = {
            'affected_requirements': [],
            'affected_tests': [],
            'test_coverage_impact': [],
        }

        for code_id in changed_code_ids:
            if code_id not in self._nodes:
                continue

            # 找出代码实现的需求
            for req, dep_type in self.get_dependencies(code_id):
                if dep_type == DependencyType.IMPLEMENTS and req.type == ArtifactType.REQUIREMENT:
                    result['affected_requirements'].append(req)

            # 找出测试该代码的测试文件
            for dependent, dep_type in self.get_dependents(code_id):
                if dep_type == DependencyType.TESTS and dependent.type == ArtifactType.TEST:
                    result['affected_tests'].append(dependent)

            # 获取所有受影响的工件（正向传播）
            affected = self.get_affected_artifacts(code_id)
            for node in affected:
                if node.type == ArtifactType.TEST and node not in result['affected_tests']:
                    result['affected_tests'].append(node)

        # 去重
        result['affected_requirements'] = list({n.id: n for n in result['affected_requirements']}.values())
        result['affected_tests'] = list({n.id: n for n in result['affected_tests']}.values())

        return result

    def get_traceability_matrix(self) -> Dict[str, Any]:
        """生成需求-代码-测试 可追溯矩阵

        Returns:
            完整的可追溯矩阵，包含:
            - requirements: 需求列表
            - code_files: 代码文件列表
            - test_files: 测试文件列表
            - matrix: 关联矩阵 [req_index][code_index] = bool
            - test_matrix: 测试关联矩阵 [req_index][test_index] = bool
        """
        req_nodes = [n for n in self._nodes.values() if n.type == ArtifactType.REQUIREMENT]
        code_nodes = [n for n in self._nodes.values() if n.type == ArtifactType.CODE]
        test_nodes = [n for n in self._nodes.values() if n.type == ArtifactType.TEST]

        req_id_to_idx = {n.id: i for i, n in enumerate(req_nodes)}
        code_id_to_idx = {n.id: i for i, n in enumerate(code_nodes)}
        test_id_to_idx = {n.id: i for i, n in enumerate(test_nodes)}

        # 需求 → 代码 矩阵
        req_code_matrix = [[False] * len(code_nodes) for _ in range(len(req_nodes))]
        req_test_matrix = [[False] * len(test_nodes) for _ in range(len(req_nodes))]

        for code_node in code_nodes:
            for req, dep_type in self.get_dependencies(code_node.id):
                if dep_type == DependencyType.IMPLEMENTS and req.id in req_id_to_idx:
                    req_idx = req_id_to_idx[req.id]
                    code_idx = code_id_to_idx[code_node.id]
                    req_code_matrix[req_idx][code_idx] = True

        for test_node in test_nodes:
            for req, dep_type in self.get_dependencies(test_node.id):
                if dep_type == DependencyType.TESTS and req.id in req_id_to_idx:
                    req_idx = req_id_to_idx[req.id]
                    test_idx = test_id_to_idx[test_node.id]
                    req_test_matrix[req_idx][test_idx] = True

        # 计算覆盖率
        coverage = {
            'requirements_with_code': sum(1 for row in req_code_matrix if any(row)),
            'requirements_with_test': sum(1 for row in req_test_matrix if any(row)),
            'code_coverage_percent': 0,
            'test_coverage_percent': 0,
        }

        if len(req_nodes) > 0:
            coverage['code_coverage_percent'] = int(
                coverage['requirements_with_code'] / len(req_nodes) * 100
            )
            coverage['test_coverage_percent'] = int(
                coverage['requirements_with_test'] / len(req_nodes) * 100
            )

        result = {
            'requirements': [
                {'id': n.id, 'name': n.name, 'description': n.description}
                for n in req_nodes
            ],
            'code_files': [
                {'id': n.id, 'name': n.name, 'path': str(n.path) if n.path else None}
                for n in code_nodes
            ],
            'test_files': [
                {'id': n.id, 'name': n.name, 'path': str(n.path) if n.path else None}
                for n in test_nodes
            ],
            'req_code_matrix': req_code_matrix,
            'req_test_matrix': req_test_matrix,
            'coverage': coverage,
            # 兼容性字段
            'total_requirements': len(req_nodes),
            'requirements_covered_by_code': coverage['requirements_with_code'],
            'requirements_covered_by_test': coverage['requirements_with_test'],
            'coverage_percentage': coverage['code_coverage_percent'],
        }
        return result

    def to_dict(self) -> Dict[str, Any]:
        """导出图结构"""
        return {
            'nodes': [n.to_dict() for n in self._nodes.values()],
            'edges': [
                {
                    'from': u,
                    'to': v,
                    'type': d.get('type')
                }
                for u, v, d in self._graph.edges(data=True)
            ]
        }

    def save_to_file(self, file_path: Union[str, Path]):
        """保存到文件"""
        Path(file_path).write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding='utf-8')

    @classmethod
    def load_from_file(cls, file_path: Union[str, Path]) -> 'ArtifactGraph':
        """从文件加载"""
        data = json.loads(Path(file_path).read_text(encoding='utf-8'))
        graph = cls()
        for node_data in data['nodes']:
            graph.add_node(ArtifactNode.from_dict(node_data))
        for edge_data in data['edges']:
            graph.add_dependency(
                edge_data['from'],
                edge_data['to'],
                DependencyType(edge_data['type'])
            )
        return graph

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return len(list(self._graph.edges()))

    def __len__(self) -> int:
        return len(self._nodes)


class ArtifactGraphStore:
    """ArtifactGraph 持久化存储

    支持两种后端:
    - JSON: 适合小型项目，人类可读
    - SQLite: 适合大型项目，支持增量更新和查询

    设计原则:
    1. 自动版本管理 - 每次变更都生成新版本
    2. 增量更新 - 只保存变更的部分
    3. 历史回溯 - 可以恢复到任意时间点
    """

    SCHEMA_VERSION = "1.0"

    def __init__(self, db_path: Union[str, Path]):
        self.db_path = Path(db_path)
        self.backend_type = "sqlite" if self.db_path.suffix == '.db' else "json"
        self._conn: Optional[sqlite3.Connection] = None

    def __enter__(self):
        if self.backend_type == "sqlite":
            self._conn = sqlite3.connect(str(self.db_path))
            self._init_schema()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn:
            self._conn.commit()
            self._conn.close()
            self._conn = None

    def _init_schema(self):
        """初始化数据库 schema"""
        if not self._conn:
            return

        cursor = self._conn.cursor()

        # 节点表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                path TEXT,
                name TEXT NOT NULL,
                description TEXT,
                version TEXT NOT NULL,
                metadata_json TEXT,
                content_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 边表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS edges (
                from_id TEXT NOT NULL,
                to_id TEXT NOT NULL,
                type TEXT NOT NULL,
                metadata_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (from_id, to_id),
                FOREIGN KEY (from_id) REFERENCES nodes (id) ON DELETE CASCADE,
                FOREIGN KEY (to_id) REFERENCES nodes (id) ON DELETE CASCADE
            )
        ''')

        # 版本历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS versions (
                version_id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_json TEXT NOT NULL,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 元数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')

        # 插入 schema 版本
        cursor.execute('''
            INSERT OR IGNORE INTO metadata (key, value) VALUES (?, ?)
        ''', ('schema_version', self.SCHEMA_VERSION))

        self._conn.commit()

    def save(self, graph: ArtifactGraph, version_message: str = "") -> int:
        """保存图并创建版本

        Returns:
            version_id: 新版本号
        """
        if self.backend_type == "json":
            data = graph.to_dict()
            data['version'] = str(int(datetime.now().timestamp()))
            data['version_message'] = version_message
            self.db_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
            return int(data['version'])

        # SQLite 后端
        if not self._conn:
            raise RuntimeError("SQLite 连接未初始化，请使用 with 语句")

        cursor = self._conn.cursor()

        # 开始事务
        cursor.execute("BEGIN TRANSACTION")

        try:
            # 保存/更新节点
            for node in graph._nodes.values():
                content_hash = hashlib.md5(
                    (node.id + str(node.path) + node.name).encode()
                ).hexdigest()[:16]

                cursor.execute('''
                    INSERT OR REPLACE INTO nodes
                    (id, type, path, name, description, version, metadata_json, content_hash, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    node.id,
                    node.type.value,
                    str(node.path) if node.path else None,
                    node.name,
                    node.description,
                    node.version,
                    json.dumps(node.metadata),
                    content_hash
                ))

            # 先删除旧边，再保存新边
            cursor.execute("DELETE FROM edges")
            for from_id, to_id, data in graph._graph.edges(data=True):
                cursor.execute('''
                    INSERT OR REPLACE INTO edges (from_id, to_id, type, metadata_json)
                    VALUES (?, ?, ?, ?)
                ''', (
                    from_id,
                    to_id,
                    data.get('type', 'depends_on'),
                    json.dumps({k: v for k, v in data.items() if k != 'type'})
                ))

            # 创建版本快照
            snapshot = json.dumps(graph.to_dict(), ensure_ascii=False)
            cursor.execute('''
                INSERT INTO versions (snapshot_json, message) VALUES (?, ?)
            ''', (snapshot, version_message))

            version_id = cursor.lastrowid

            self._conn.commit()
            return version_id if version_id else 0

        except Exception:
            self._conn.rollback()
            raise

    def load(self, version_id: Optional[int] = None) -> ArtifactGraph:
        """加载图，可指定版本号

        Args:
            version_id: 指定加载的版本，None 表示最新版本
        """
        if self.backend_type == "json":
            if not self.db_path.exists():
                return ArtifactGraph()
            data = json.loads(self.db_path.read_text(encoding='utf-8'))
            return ArtifactGraph.load_from_file(self.db_path)

        # SQLite 后端
        if not self._conn:
            raise RuntimeError("SQLite 连接未初始化，请使用 with 语句")

        cursor = self._conn.cursor()

        if version_id is not None:
            # 从历史版本加载
            cursor.execute('SELECT snapshot_json FROM versions WHERE version_id = ?', (version_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"版本 {version_id} 不存在")
            data = json.loads(row[0])
            graph = ArtifactGraph()
            for node_data in data['nodes']:
                graph.add_node(ArtifactNode.from_dict(node_data))
            for edge_data in data['edges']:
                graph.add_dependency(
                    edge_data['from'],
                    edge_data['to'],
                    DependencyType(edge_data['type'])
                )
            return graph
        else:
            # 从当前表加载
            graph = ArtifactGraph()

            # 加载节点
            cursor.execute('SELECT id, type, path, name, description, version, metadata_json FROM nodes')
            for row in cursor.fetchall():
                node = ArtifactNode(
                    id=row[0],
                    type=ArtifactType(row[1]),
                    path=Path(row[2]) if row[2] else None,
                    name=row[3],
                    description=row[4],
                    version=row[5],
                    metadata=json.loads(row[6]) if row[6] else {}
                )
                graph.add_node(node)

            # 加载边
            cursor.execute('SELECT from_id, to_id, type, metadata_json FROM edges')
            for row in cursor.fetchall():
                metadata = json.loads(row[3]) if row[3] else {}
                graph.add_dependency(row[0], row[1], DependencyType(row[2]), metadata)

            return graph

    def list_versions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """列出版本历史"""
        if self.backend_type == "json":
            if self.db_path.exists():
                data = json.loads(self.db_path.read_text(encoding='utf-8'))
                return [{
                    'version_id': int(data.get('version', '0')),
                    'message': data.get('version_message', ''),
                    'created_at': datetime.fromtimestamp(int(data.get('version', '0'))).isoformat()
                }]
            return []

        if not self._conn:
            raise RuntimeError("SQLite 连接未初始化，请使用 with 语句")

        cursor = self._conn.cursor()
        cursor.execute('''
            SELECT version_id, message, created_at
            FROM versions
            ORDER BY version_id DESC
            LIMIT ?
        ''', (limit,))

        return [
            {
                'version_id': row[0],
                'message': row[1],
                'created_at': row[2]
            }
            for row in cursor.fetchall()
        ]

    def get_diff(self, from_version: int, to_version: Optional[int] = None) -> Dict[str, Any]:
        """比较两个版本的差异"""
        graph1 = self.load(from_version)
        graph2 = self.load(to_version)

        nodes1 = set(graph1._nodes.keys())
        nodes2 = set(graph2._nodes.keys())

        return {
            'nodes_added': list(nodes2 - nodes1),
            'nodes_removed': list(nodes1 - nodes2),
            'nodes_modified': [
                n for n in nodes1 & nodes2
                if graph1._nodes[n].to_dict() != graph2._nodes[n].to_dict()
            ],
            'node_count_before': len(graph1),
            'node_count_after': len(graph2),
            'edge_count_before': graph1.edge_count,
            'edge_count_after': graph2.edge_count
        }

    def incremental_update(self, changed_files: List[Path], root_dir: Path) -> int:
        """增量更新，只更新变更的文件

        Args:
            changed_files: 变更文件列表
            root_dir: 项目根目录

        Returns:
            新版本号
        """
        if self.backend_type != "sqlite":
            # JSON 后端全量更新
            graph = ArtifactGraph()
            graph.discover_from_directory(root_dir)
            graph.auto_detect_dependencies()
            return self.save(graph, "Incremental update")

        graph = self.load()

        # 移除旧的变更文件节点
        for file_path in changed_files:
            rel_path = file_path.relative_to(root_dir)
            node_id = f"file:{rel_path}"
            if node_id in graph._nodes:
                # 移除相关边
                edges_to_remove = list(graph._graph.out_edges(node_id)) + list(graph._graph.in_edges(node_id))
                for from_id, to_id in edges_to_remove:
                    graph._graph.remove_edge(from_id, to_id)
                # 移除节点
                del graph._nodes[node_id]
                graph._graph.remove_node(node_id)

        # 重新发现变更文件
        code_extensions = {'.py', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.c', '.java', '.js', '.ts'}
        doc_extensions = {'.md', '.rst', '.txt', '.rst'}

        for file_path in changed_files:
            if not file_path.is_file():
                continue

            rel_path = file_path.relative_to(root_dir)
            file_type = None

            if file_path.suffix in code_extensions:
                if 'test' in file_path.name.lower():
                    file_type = ArtifactType.TEST
                else:
                    file_type = ArtifactType.CODE
            elif file_path.suffix in doc_extensions:
                if file_path.name.startswith('req_'):
                    file_type = ArtifactType.REQUIREMENT
                else:
                    file_type = ArtifactType.DOC

            if file_type:
                node = ArtifactNode(
                    id=f"file:{rel_path}",
                    type=file_type,
                    path=file_path,
                    name=file_path.name,
                    description=f"{file_type.value} file"
                )
                graph.add_node(node)

        # 重新检测依赖
        graph.auto_detect_dependencies()

        return self.save(graph, f"Incremental update: {len(changed_files)} files changed")

    def query_nodes(self, query: Dict[str, Any]) -> List[ArtifactNode]:
        """高级查询接口

        支持的查询条件:
        - type: 节点类型
        - path_contains: 路径包含字符串
        - name_contains: 名称包含字符串
        - depends_on: 依赖的节点 ID
        - depended_by: 被哪些节点依赖

        Example:
            store.query_nodes({
                'type': ArtifactType.CODE,
                'path_contains': 'src',
                'depended_by': 'file:tests/test_login.py'
            })
        """
        graph = self.load()
        results = list(graph._nodes.values())

        if 'type' in query:
            results = [n for n in results if n.type == query['type']]

        if 'path_contains' in query:
            results = [
                n for n in results
                if n.path and query['path_contains'] in str(n.path)
            ]

        if 'name_contains' in query:
            results = [n for n in results if query['name_contains'] in n.name]

        if 'depends_on' in query:
            target_id = query['depends_on']
            results = [n for n in results if any(
                dep.id == target_id for dep, _ in graph.get_dependencies(n.id)
            )]

        if 'depended_by' in query:
            source_id = query['depended_by']
            results = [n for n in results if any(
                dep.id == source_id for dep, _ in graph.get_dependents(n.id)
            )]

        return results
