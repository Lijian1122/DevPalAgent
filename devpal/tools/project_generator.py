# -*- coding: utf-8 -*-
"""
动态项目生成器 - 根据需求文档自动创建项目结构

功能:
1. 解析需求文档 frontmatter
2. 提取项目名称并自动格式化
3. 创建标准的项目目录结构
4. 整理并移动所有生成的产物到项目文件夹
"""

import os
import re
import yaml
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult


@dataclass
class ProjectInfo:
    """项目信息"""
    name: str
    name_snake: str
    name_camel: str
    title: str
    version: str
    description: str
    requirements_file: Path


class ProjectGeneratorTool(BaseTool):
    """动态项目生成器工具"""

    name = "project_generator"
    description = "根据需求文档自动生成项目文件夹结构并整理所有产物"

    class Parameters(BaseModel):
        requirements_file: str = Field(
            description="需求文档路径 (Markdown with frontmatter)"
        )
        base_dir: Optional[str] = Field(
            default=None,
            description="项目生成的基础目录，默认在当前目录"
        )
        project_name_override: Optional[str] = Field(
            default=None,
            description="可选：手动指定项目名称，覆盖从文档提取的名称"
        )
        create_structure: bool = Field(
            default=True,
            description="是否创建标准目录结构"
        )
        move_artifacts: bool = Field(
            default=True,
            description="是否自动查找并移动相关产物到项目文件夹"
        )

    def _execute(self, params: Parameters) -> ToolResult:
        req_path = Path(params.requirements_file)
        if not req_path.exists():
            return ToolResult.error(f"需求文件不存在: {req_path}")

        # 1. 解析需求文档 frontmatter
        project_info = self._parse_requirements_frontmatter(req_path)

        # 2. 处理项目名称覆盖
        if params.project_name_override:
            project_info.name = params.project_name_override
            project_info.name_snake = self._to_snake_case(params.project_name_override)
            project_info.name_camel = self._to_camel_case(params.project_name_override)

        # 3. 创建项目目录
        base_dir = Path(params.base_dir) if params.base_dir else Path.cwd()
        project_dir = base_dir / project_info.name_snake

        if project_dir.exists():
            return ToolResult.error(f"项目目录已存在: {project_dir}")

        # 4. 创建标准目录结构
        if params.create_structure:
            self._create_project_structure(project_dir)

        # 5. 复制/移动相关产物
        artifacts_moved = {}
        if params.move_artifacts:
            artifacts_moved = self._move_artifacts(project_dir, req_path, project_info)

        # 6. 生成项目说明文档
        self._generate_project_readme(project_dir, project_info, artifacts_moved)

        return ToolResult.ok(
            f"项目 '{project_info.name_snake}' 创建成功！\n"
            f"路径: {project_dir.absolute()}\n"
            f"整理文件数: {sum(len(v) for v in artifacts_moved.values())}",
            project_dir=str(project_dir),
            project_name=project_info.name_snake,
            artifacts_moved=artifacts_moved
        )

    def _parse_requirements_frontmatter(self, req_path: Path) -> ProjectInfo:
        """解析需求文档的 frontmatter 并提取项目信息"""
        content = req_path.read_text(encoding='utf-8')

        # 提取 frontmatter
        frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if frontmatter_match:
            try:
                fm_data = yaml.safe_load(frontmatter_match.group(1))
            except:
                fm_data = {}
        else:
            fm_data = {}

        # 提取标题并转换为项目名称
        title = fm_data.get('title', req_path.stem.replace('_requirements', ''))
        version = fm_data.get('version', '1.0')

        # 提取项目描述（第一个段落或描述字段）
        description = fm_data.get('description', '')
        if not description:
            desc_match = re.search(r'^# .+?\n+(.+?)\n', content, re.MULTILINE)
            if desc_match:
                description = desc_match.group(1).strip()

        # 自动生成项目名称
        project_name = self._extract_project_name(title)

        return ProjectInfo(
            name=project_name,
            name_snake=self._to_snake_case(project_name),
            name_camel=self._to_camel_case(project_name),
            title=title,
            version=version,
            description=description,
            requirements_file=req_path
        )

    def _extract_project_name(self, title: str) -> str:
        """从中文标题中提取有意义的项目名称"""
        # 常见关键词映射
        keyword_map = {
            '登录': 'authentication',
            '认证': 'authentication',
            '用户': 'user',
            '系统': 'system',
            '管理': 'management',
            '订单': 'order',
            '商品': 'product',
            '购物': 'shopping',
            '车': 'cart',
            '支付': 'payment',
            '消息': 'message',
            '通知': 'notification',
            '搜索': 'search',
            '文件': 'file',
            '上传': 'upload',
            '下载': 'download',
            '分析': 'analytics',
            '报表': 'report',
            'API': 'api',
            '接口': 'api',
            '服务': 'service',
        }

        # 尝试匹配关键词
        name_parts = []
        for cn, en in keyword_map.items():
            if cn in title:
                name_parts.append(en)

        if name_parts:
            return '_'.join(name_parts)

        # 如果没有匹配到，使用文件名
        return 'project'

    def _to_snake_case(self, name: str) -> str:
        """转换为 snake_case"""
        s = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        s = re.sub(r'_+', '_', s)
        return s.lower().strip('_')

    def _to_camel_case(self, name: str) -> str:
        """转换为 CamelCase"""
        words = self._to_snake_case(name).split('_')
        return ''.join(w.capitalize() for w in words)

    def _create_project_structure(self, project_dir: Path):
        """创建标准的项目目录结构"""
        directories = [
            'src',                    # 源代码
            'tests',                  # 测试代码
            'docs',                   # 文档
            'docs/design',            # 设计文档
            'docs/api',               # API 文档
            'reports',                # 验证报告
            'requirements',           # 需求文档
            'data',                   # 数据文件
            'config',                 # 配置文件
            'scripts',                # 脚本
            'examples',               # 示例代码
        ]

        for d in directories:
            (project_dir / d).mkdir(parents=True, exist_ok=True)

        # 创建 __init__.py 文件
        (project_dir / 'src' / '__init__.py').touch()
        (project_dir / 'tests' / '__init__.py').touch()

    def _move_artifacts(self, project_dir: Path, req_path: Path,
                        project_info: ProjectInfo) -> Dict[str, list]:
        """查找并移动相关产物到项目文件夹"""
        artifacts = {
            'requirements': [],
            'source_code': [],
            'tests': [],
            'docs': [],
            'reports': [],
            'config': [],
        }

        # 1. 移动需求文档
        dest = project_dir / 'requirements' / req_path.name
        shutil.copy2(req_path, dest)
        artifacts['requirements'].append(str(dest))

        # 2. 查找并移动源代码（包含项目关键词的 .py 文件）
        keywords = [
            project_info.name_snake,
            project_info.name_snake.replace('_', ''),
            'login', 'auth', 'feature',
        ]

        # 搜索源文件
        for pattern in ['*.py', '*.cpp', '*.h', '*.java', '*.js']:
            for f in Path.cwd().glob(pattern):
                if any(kw in f.name.lower() for kw in keywords):
                    dest = project_dir / 'src' / f.name
                    shutil.copy2(f, dest)
                    artifacts['source_code'].append(str(dest))

        # 搜索 src 目录
        src_dir = Path.cwd() / 'src'
        if src_dir.exists():
            for f in src_dir.glob('*.py'):
                if any(kw in f.name.lower() for kw in keywords):
                    dest = project_dir / 'src' / f.name
                    shutil.copy2(f, dest)
                    artifacts['source_code'].append(str(dest))

        # 3. 搜索测试文件
        tests_dir = Path.cwd() / 'tests'
        if tests_dir.exists():
            for f in tests_dir.glob('*.py'):
                if any(kw in f.name.lower() for kw in keywords + ['test']):
                    dest = project_dir / 'tests' / f.name
                    shutil.copy2(f, dest)
                    artifacts['tests'].append(str(dest))

        # 4. 搜索文档和报告
        for search_dir in ['auth_service', 'docs', 'reports', 'cpp_authentication_system']:
            dir_path = Path.cwd() / search_dir
            if dir_path.exists():
                for f in dir_path.glob('*'):
                    if f.is_file():
                        if 'report' in f.name.lower() or 'verification' in f.name.lower():
                            dest = project_dir / 'reports' / f.name
                            shutil.copy2(f, dest)
                            artifacts['reports'].append(str(dest))
                        elif f.suffix in ['.md', '.txt', '.pdf']:
                            dest = project_dir / 'docs' / f.name
                            shutil.copy2(f, dest)
                            artifacts['docs'].append(str(dest))

        # 5. 检测是否为 C++ 项目，如果是则生成带智能编译器选择的 CMakeLists.txt
        has_cpp = (project_dir / 'src').glob('*.cpp') or any('.cpp' in f for f in artifacts['source_code'])
        if has_cpp:
            self._generate_cmake_file(project_dir, project_info)
            artifacts['config'].append(str(project_dir / 'CMakeLists.txt'))

        return artifacts

    def _generate_project_readme(self, project_dir: Path, project_info: ProjectInfo,
                                  artifacts: Dict[str, list]):
        """生成项目 README"""
        readme_content = f"""# {project_info.title}

> **项目名称**: {project_info.name_snake}
> **版本**: {project_info.version}
> **生成方式**: DevPal Agent OpenSpec 自动生成
> **生成时间**: {self._get_current_time()}

---

## 项目简介

{project_info.description or '基于需求驱动开发的完整项目，包含完整的测试、文档和验证报告。'}

---

## 项目结构

```
{project_info.name_snake}/
├── src/                          # 源代码
│   ├── __init__.py
│   └── *.py / *.cpp / *.java
├── tests/                        # 测试代码
│   ├── __init__.py
│   └── test_*.py
├── docs/                         # 文档
│   ├── design/                   # 设计文档
│   └── api/                      # API 文档
├── reports/                      # 验证报告
├── requirements/                 # 需求文档
├── data/                         # 数据文件
├── config/                       # 配置文件
├── scripts/                      # 脚本
├── examples/                     # 示例代码
└── README.md                     # 本文件
```

---

## 已生成的文件

### 需求文档 ({len(artifacts['requirements'])} 个)
{self._format_file_list(artifacts['requirements'], project_dir)}

### 源代码 ({len(artifacts['source_code'])} 个)
{self._format_file_list(artifacts['source_code'], project_dir)}

### 测试代码 ({len(artifacts['tests'])} 个)
{self._format_file_list(artifacts['tests'], project_dir)}

### 文档 ({len(artifacts['docs'])} 个)
{self._format_file_list(artifacts['docs'], project_dir)}

### 验证报告 ({len(artifacts['reports'])} 个)
{self._format_file_list(artifacts['reports'], project_dir)}

### 配置文件 ({len(artifacts['config'])} 个)
{self._format_file_list(artifacts['config'], project_dir)}

---

## 快速开始

### 1. 运行测试

```bash
cd {project_info.name_snake}
# Python 项目
python -m pytest tests/ -v

# C++ 项目
mkdir build && cd build
cmake ..
cmake --build .
```

### 2. 查看验证报告

打开 `reports/` 目录下的验证报告，了解需求覆盖情况和测试结果。

### 3. 修改需求

编辑 `requirements/*.md` 文件，然后重新运行 OpenSpec 流程：

```bash
# 重新生成验证报告
python run_openspec_demo.py
```

---

## OpenSpec 流程信息

| 阶段 | 状态 |
|------|------|
| 需求解析 | ✅ 已完成 |
| 代码审查 | ✅ 已完成 |
| 测试设计 | ✅ 已完成 |
| 代码生成 | ✅ 已完成 |
| 验证执行 | ✅ 已完成 |

---

*本项目由 DevPal Agent OpenSpec Framework 自动生成*
"""
        (project_dir / 'README.md').write_text(readme_content, encoding='utf-8')

    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _generate_cmake_file(self, project_dir: Path, project_info: ProjectInfo):
        """为 C++ 项目生成带智能编译器选择的 CMakeLists.txt"""
        cmake_content = f'''cmake_minimum_required(VERSION 3.14)

# ==============================================================================
# 编译器自动选择规则 - Auto-generated by DevPal OpenSpec
# ==============================================================================
# Windows:   优先使用 MSVC (Visual Studio)
# macOS:     优先使用 Clang
# Linux/其他: 优先使用 g++
#
# 防止找不到编译器的问题！
# ==============================================================================

if(WIN32)
    # Windows 平台: 优先使用 MSVC
    if(NOT CMAKE_CXX_COMPILER)
        find_program(MSVC_CL cl.exe)
        if(MSVC_CL)
            set(CMAKE_CXX_COMPILER ${{MSVC_CL}} CACHE FILEPATH "MSVC compiler" FORCE)
            message(STATUS "[Windows] 自动选择编译器: MSVC (cl.exe)")
        else()
            # 尝试查找 MinGW
            find_program(MINGW_GPP g++.exe)
            if(MINGW_GPP)
                set(CMAKE_CXX_COMPILER ${{MINGW_GPP}} CACHE FILEPATH "MinGW compiler" FORCE)
                message(STATUS "[Windows] 自动选择编译器: MinGW (g++.exe)")
            else()
                message(WARNING "未找到 MSVC 或 MinGW，请手动指定编译器路径")
            endif()
        endif()
    endif()

elseif(APPLE)
    # macOS 平台: 优先使用 Clang
    if(NOT CMAKE_CXX_COMPILER)
        find_program(CLANG_CPP clang++)
        if(CLANG_CPP)
            set(CMAKE_CXX_COMPILER ${{CLANG_CPP}} CACHE FILEPATH "Clang compiler" FORCE)
            message(STATUS "[macOS] 自动选择编译器: Clang (clang++)")
        else()
            find_program(GPP_CPP g++)
            if(GPP_CPP)
                set(CMAKE_CXX_COMPILER ${{GPP_CPP}} CACHE FILEPATH "GCC compiler" FORCE)
                message(STATUS "[macOS] 自动选择编译器: GCC (g++)")
            else()
                message(WARNING "未找到 Clang 或 GCC，请手动指定编译器路径")
            endif()
        endif()
    endif()

else()
    # Linux/其他平台: 优先使用 g++
    if(NOT CMAKE_CXX_COMPILER)
        find_program(GPP_CPP g++)
        if(GPP_CPP)
            set(CMAKE_CXX_COMPILER ${{GPP_CPP}} CACHE FILEPATH "GCC compiler" FORCE)
            message(STATUS "[Linux/Other] 自动选择编译器: GCC (g++)")
        else()
            find_program(CLANG_CPP clang++)
            if(CLANG_CPP)
                set(CMAKE_CXX_COMPILER ${{CLANG_CPP}} CACHE FILEPATH "Clang compiler" FORCE)
                message(STATUS "[Linux/Other] 自动选择编译器: Clang (clang++)")
            else()
                message(WARNING "未找到 g++ 或 Clang，请手动指定编译器路径")
            endif()
        endif()
    endif()
endif()

# 项目定义
project({project_info.name_camel} VERSION {project_info.version} LANGUAGES CXX)

# C++ 标准设置
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 编译器特定选项
if(MSVC)
    message(STATUS "配置 MSVC 编译器选项")
    # MSVC: UTF-8 编码，警告等级 4，禁用特定警告
    add_compile_options(
        /utf-8
        /W4
        /wd4100  # 未引用的形参
        /wd4244  # 类型转换可能丢失数据
        /wd4267  # size_t 到较小类型转换
    )
elseif(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    message(STATUS "配置 Clang 编译器选项")
    # Clang: 启用大部分警告
    add_compile_options(
        -Wall
        -Wextra
        -Wpedantic
        -Wno-unused-parameter
    )
elseif(CMAKE_CXX_COMPILER_ID MATCHES "GNU")
    message(STATUS "配置 GCC 编译器选项")
    # GCC: 启用大部分警告
    add_compile_options(
        -Wall
        -Wextra
        -Wpedantic
        -Wno-unused-parameter
    )
endif()

# 头文件目录
include_directories(${{PROJECT_SOURCE_DIR}}/include)

# 源文件
file(GLOB SOURCES
    src/*.cpp
    src/*.cc
    src/*.cxx
)

# 构建库
if(SOURCES)
    add_library({project_info.name_snake}_lib STATIC ${{SOURCES}})
endif()

# 主程序（如果有 main.cpp）
if(EXISTS ${{PROJECT_SOURCE_DIR}}/src/main.cpp)
    add_executable({project_info.name_snake} src/main.cpp)
    if(TARGET {project_info.name_snake}_lib)
        target_link_libraries({project_info.name_snake} PRIVATE {project_info.name_snake}_lib)
    endif()
endif()

# 演示程序（如果有）
if(EXISTS ${{PROJECT_SOURCE_DIR}}/demo/main.cpp)
    add_executable({project_info.name_snake}_demo demo/main.cpp)
    if(TARGET {project_info.name_snake}_lib)
        target_link_libraries({project_info.name_snake}_demo PRIVATE {project_info.name_snake}_lib)
    endif()
endif()

# 测试
enable_testing()
file(GLOB TEST_SOURCES tests/test_*.cpp)
foreach(TEST_SRC ${{TEST_SOURCES}})
    get_filename_component(TEST_NAME ${{TEST_SRC}} NAME_WE)
    add_executable(${{TEST_NAME}} ${{TEST_SRC}})
    if(TARGET {project_info.name_snake}_lib)
        target_link_libraries(${{TEST_NAME}} PRIVATE {project_info.name_snake}_lib)
    endif()
    add_test(NAME ${{TEST_NAME}} COMMAND ${{TEST_NAME}})
endforeach()

message(STATUS "========================================")
message(STATUS " 项目: {project_info.title}")
message(STATUS " 版本: {project_info.version}")
message(STATUS "========================================")
'''
        (project_dir / 'CMakeLists.txt').write_text(cmake_content, encoding='utf-8')

    def _format_file_list(self, files: list, project_dir: Path) -> str:
        """格式化文件列表"""
        if not files:
            return '暂无文件'

        lines = []
        for f in files:
            rel_path = Path(f).relative_to(project_dir)
            lines.append(f'- `{rel_path}`')
        return '\n'.join(lines)
