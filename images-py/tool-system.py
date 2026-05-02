#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate Mermaid class diagram for DevPal Agent Tool System."""

import os
import subprocess
import tempfile

mermaid_content = """classDiagram
    class BaseTool {
        <<abstract>>
        +str name
        +str description
        +dict parameters
        +str schema_version
        +call(dict params) dict
        +get_openai_schema() dict
        +_validate_params(dict params) bool
    }

    class FileSystemTool {
        +read_file(path) str
        +write_file(path, content)
        +list_dir(path) list
        +search_files(pattern) list
    }

    class CommandTool {
        +SandboxConfig config
        +run_command(cmd, timeout) dict
        +_check_safety(cmd) bool
        +_enforce_timeout()
    }

    class CodeSearchTool {
        +search_code(query) list
        +find_definition(symbol) dict
        +find_references(symbol) list
        +grep_pattern(pattern) list
    }

    class CompilerTool {
        +compile_code(path) dict
        +parse_errors(output) list
        +suggest_fixes(errors) list
        +run_static_analysis(path) dict
    }

    class GitTool {
        +git_status() dict
        +git_diff() str
        +git_commit(msg)
        +git_log(n) list
    }

    class StaticAnalysisTool {
        +run_clang_tidy(path) dict
        +run_cppcheck(path) dict
        +parse_warnings(output) list
        +generate_report() dict
    }

    BaseTool <|-- FileSystemTool
    BaseTool <|-- CommandTool
    BaseTool <|-- CodeSearchTool
    BaseTool <|-- CompilerTool
    BaseTool <|-- GitTool
    BaseTool <|-- StaticAnalysisTool

    class ToolManager {
        +List~BaseTool~ tools
        +register_tool(tool)
        +get_tool(name) BaseTool
        +get_all_schemas() list
        +execute_tool(name, params) dict
    }

    ToolManager *-- BaseTool : contains >

    class SandboxConfig {
        +List~str~ allowed_commands
        +List~str~ blocked_paths
        +int default_timeout
        +bool enable_network
    }

    CommandTool *-- SandboxConfig : uses >

    note for BaseTool "所有工具的抽象基类\n定义统一接口和参数校验"
    note for ToolManager "工具注册、管理、调度中心"
"""

output_path = os.path.join(os.path.dirname(__file__), "tool-system.png")

with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False, encoding='utf-8') as f:
    f.write(mermaid_content)
    temp_mmd = f.name

try:
    cmd = [
        'C:\\NVM\\nodejs\\node.exe',
        'C:\\NVM\\nodejs\\node_modules\\@mermaid-js\\mermaid-cli\\src\\cli.js',
        '-i', temp_mmd,
        '-o', output_path,
        '-b', 'white',
        '-w', '1200',
        '-H', '900'
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Exit code: {result.returncode}")
    if result.stdout:
        print(f"stdout: {result.stdout}")
    if result.stderr:
        print(f"stderr: {result.stderr}")
    if result.returncode == 0:
        print(f"[OK] Diagram generated: {output_path}")
    else:
        raise Exception(f"Command failed with exit code {result.returncode}")

finally:
    os.unlink(temp_mmd)
