# -*- coding: utf-8 -*-
"""
Self Source Reader Tool
Agent 读取自己源代码的工具
"""
import os
import ast
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult


class SelfSourceReaderTool(BaseTool):
    """Agent 读取自己源代码的工具"""

    name = "self_source_reader"
    description = "读取和分析 Agent 自身的源代码，用于自我理解和改进"

    class Parameters(BaseModel):
        action: str = Field(
            default="read_file",
            description="操作类型: read_file(读取文件), list_files(列出文件), search_code(搜索代码), analyze_module(分析模块), get_structure(获取整体结构)"
        )
        file_path: Optional[str] = Field(
            default=None,
            description="要读取的文件路径（相对于 devpal 根目录），如: 'core/agent_engine.py'"
        )
        search_pattern: Optional[str] = Field(
            default=None,
            description="搜索模式（正则表达式或关键词）"
        )
        module_name: Optional[str] = Field(
            default=None,
            description="要分析的模块名"
        )
        max_results: int = Field(
            default=50,
            description="最大结果数"
        )

    def _execute(self, params: Parameters) -> ToolResult:
        base_path = Path(__file__).parent.parent

        try:
            if params.action == "list_files":
                return self._list_files(base_path)
            elif params.action == "read_file":
                return self._read_file(base_path, params.file_path)
            elif params.action == "search_code":
                return self._search_code(base_path, params.search_pattern, params.max_results)
            elif params.action == "analyze_module":
                return self._analyze_module(base_path, params.module_name)
            elif params.action == "get_structure":
                return self._get_structure(base_path)
            else:
                return ToolResult.error(f"不支持的操作类型: {params.action}")
        except Exception as e:
            return ToolResult.error(f"操作失败: {str(e)}", error_type="source_read_error")

    def _list_files(self, base_path: Path) -> ToolResult:
        """列出所有源代码文件"""
        files = []
        for f in base_path.rglob("*.py"):
            rel_path = f.relative_to(base_path)
            files.append(str(rel_path))

        files.sort()
        result = {
            "total_files": len(files),
            "files": files
        }

        content = f"DevPal Agent 源代码文件列表（共 {len(files)} 个）:\n\n"
        for f in files:
            content += f"  - {f}\n"

        return ToolResult.ok(content, **result)

    def _read_file(self, base_path: Path, file_path: Optional[str]) -> ToolResult:
        """读取指定文件的内容"""
        if not file_path:
            return ToolResult.error("请指定要读取的文件路径")

        full_path = base_path / file_path
        if not full_path.exists():
            return ToolResult.error(f"文件不存在: {file_path}")

        content = full_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        result = {
            "file_path": file_path,
            "line_count": len(lines),
            "content_length": len(content)
        }

        output = f"文件: {file_path} ({len(lines)} 行)\n"
        output += "=" * 60 + "\n\n"
        output += content

        return ToolResult.ok(output, **result)

    def _search_code(self, base_path: Path, pattern: Optional[str], max_results: int) -> ToolResult:
        """在代码库中搜索"""
        if not pattern:
            return ToolResult.error("请指定搜索模式")

        results = []
        total_matches = 0

        for py_file in base_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                rel_path = py_file.relative_to(base_path)
                lines = content.split("\n")

                for line_num, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        results.append({
                            "file": str(rel_path),
                            "line": line_num,
                            "content": line.strip()
                        })
                        total_matches += 1
                        if total_matches >= max_results:
                            break
            except Exception:
                continue

        output = f"搜索 '{pattern}' 的结果（共 {total_matches} 个匹配）:\n\n"
        for r in results:
            output += f"  [{r['file']}:{r['line']}] {r['content']}\n"

        return ToolResult.ok(output, matches=total_matches, results=results)

    def _analyze_module(self, base_path: Path, module_name: Optional[str]) -> ToolResult:
        """分析模块结构（类和函数）"""
        if not module_name:
            return ToolResult.error("请指定模块名")

        file_path = module_name.replace(".", "/") + ".py"
        full_path = base_path / file_path

        if not full_path.exists():
            # 尝试直接查找
            for f in base_path.rglob(f"{module_name}.py"):
                full_path = f
                break
            else:
                return ToolResult.error(f"找不到模块: {module_name}")

        try:
            content = full_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
        except Exception as e:
            return ToolResult.error(f"解析模块失败: {e}")

        classes = []
        functions = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                classes.append({
                    "name": node.name,
                    "line": node.lineno,
                    "methods": methods
                })
            elif isinstance(node, ast.FunctionDef) and not isinstance(node, ast.AsyncFunctionDef):
                functions.append({
                    "name": node.name,
                    "line": node.lineno
                })
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(ast.unparse(node))

        rel_path = full_path.relative_to(base_path)
        output = f"模块分析: {rel_path}\n"
        output += "=" * 60 + "\n\n"

        output += "类定义:\n"
        for cls in classes:
            output += f"  - {cls['name']} (行 {cls['line']})\n"
            for method in cls['methods']:
                output += f"      . {method}()\n"

        output += "\n函数定义:\n"
        for func in functions:
            output += f"  - {func['name']}() (行 {func['line']})\n"

        output += "\n导入:\n"
        for imp in imports[:15]:
            output += f"  - {imp}\n"
        if len(imports) > 15:
            output += f"  ... 还有 {len(imports) - 15} 个导入\n"

        return ToolResult.ok(
            output,
            module_name=module_name,
            classes=classes,
            functions=functions,
            import_count=len(imports)
        )

    def _get_structure(self, base_path: Path) -> ToolResult:
        """获取整个项目的结构概述"""
        modules = {
            "core": [],
            "tools": [],
            "memory": [],
            "web": [],
            "multimodal": [],
        }

        for py_file in base_path.rglob("*.py"):
            parts = py_file.parts
            if len(parts) >= 2:
                parent = parts[-2]
                if parent in modules:
                    modules[parent].append(py_file.stem)

        output = "DevPal Agent 整体结构:\n"
        output += "=" * 60 + "\n\n"

        for module_name, files in modules.items():
            output += f"📦 {module_name}/\n"
            for f in sorted(files):
                if f != "__init__":
                    output += f"  - {f}.py\n"
            output += "\n"

        # 统计工具数量
        from devpal.tools import registry
        tools = registry.list_tool_names()
        output += f"🔧 已注册工具: {len(tools)} 个\n"
        output += f"   {', '.join(tools)}\n"

        return ToolResult.ok(output, structure=modules, tool_count=len(tools))
