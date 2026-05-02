# -*- coding: utf-8 -*-
"""
代码搜索工具
"""
import os
import re
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field
from .base import BaseTool, ToolResult, retry


class CodeSearchTool(BaseTool):
    """在代码库中搜索代码内容"""

    name = "code_search"
    description = "在指定目录中搜索代码，支持按文件名、内容搜索，支持正则表达式"

    class Parameters(BaseModel):
        pattern: str = Field(description="要搜索的内容模式，可以是普通字符串或正则表达式")
        path: str = Field(default=".", description="搜索的起始目录，默认为当前目录")
        file_pattern: Optional[str] = Field(default="*.py,*.cpp,*.h,*.hpp,*.c", description="文件名过滤模式，逗号分隔")
        is_regex: bool = Field(default=False, description="是否使用正则表达式搜索")
        max_results: int = Field(default=50, description="最多返回多少条结果")
        context_lines: int = Field(default=2, description="匹配行前后显示多少行上下文")

    @retry(max_retries=2, delay=0.5)
    def _execute(self, params: Parameters) -> ToolResult:
        try:
            base_path = Path(params.path)
            if not base_path.exists():
                return ToolResult.error(f"路径不存在: {params.path}")

            # 构建文件名过滤器
            file_extensions = [ext.strip() for ext in params.file_pattern.split(",")]

            matches: List[str] = []
            files_searched = 0

            for root, dirs, files in os.walk(base_path):
                # 跳过常见的不需要搜索的目录
                dirs[:] = [d for d in dirs if d not in [
                    '__pycache__', '.git', 'node_modules', 'build', 'dist',
                    'venv', '.venv', 'x64', 'x86', 'Debug', 'Release'
                ]]

                for filename in files:
                    # 文件名过滤
                    if not any(filename.endswith(ext.replace('*', '')) for ext in file_extensions):
                        continue

                    filepath = os.path.join(root, filename)
                    files_searched += 1

                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                            lines = f.readlines()

                        for line_num, line in enumerate(lines, 1):
                            # 搜索匹配
                            if params.is_regex:
                                found = re.search(params.pattern, line, re.IGNORECASE)
                            else:
                                found = params.pattern.lower() in line.lower()

                            if found:
                                # 收集上下文
                                start_line = max(1, line_num - params.context_lines)
                                end_line = min(len(lines), line_num + params.context_lines)

                                context_lines = []
                                for ctx_line in range(start_line, end_line + 1):
                                    marker = "-> " if ctx_line == line_num else "   "
                                    context_lines.append(f"{marker}{ctx_line}: {lines[ctx_line - 1].rstrip()}")

                                rel_path = os.path.relpath(filepath, base_path)
                                matches.append(f" {rel_path}:{line_num}\n" + "\n".join(context_lines))

                                if len(matches) >= params.max_results:
                                    break

                        if len(matches) >= params.max_results:
                            break

                    except (IOError, OSError):
                        continue

                if len(matches) >= params.max_results:
                    break

            if not matches:
                return ToolResult.ok(
                    content=f"搜索完成，未找到匹配。\n搜索模式: {params.pattern}\n搜索文件数: {files_searched}",
                    files_searched=files_searched,
                    match_count=0
                )

            result_content = f"找到 {len(matches)} 个匹配项（搜索了 {files_searched} 个文件）：\n\n"
            result_content += "\n\n".join(matches)

            if len(matches) >= params.max_results:
                result_content += f"\n\n️ 已达到最大结果限制 {params.max_results} 条，可能还有更多匹配"

            return ToolResult.ok(
                content=result_content,
                files_searched=files_searched,
                match_count=len(matches)
            )

        except Exception as e:
            return ToolResult.error(f"搜索失败: {str(e)}")
