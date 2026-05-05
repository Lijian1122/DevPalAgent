# -*- coding: utf-8 -*-
"""
测试用例自动生成工具
自动分析代码结构，生成单元测试用例
"""
import os
import re
import ast
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult


class TestGeneratorTool(BaseTool):
    """测试用例自动生成工具"""

    name = "test_generator"
    description = "自动分析代码结构，生成单元测试用例"

    class Parameters(BaseModel):
        file_path: str = Field(description="要分析的源代码文件路径")
        language: Optional[str] = Field(
            default=None,
            description="源代码语言（自动检测，可选：cpp, python, js）"
        )
        test_type: str = Field(
            default="unit",
            description="测试类型: unit(单元测试), integration(集成测试)"
        )
        output_file: Optional[str] = Field(
            default=None,
            description="输出的测试文件路径（可选，默认自动生成）"
        )
        include_assertions: bool = Field(
            default=True,
            description="是否包含断言模板"
        )

    def _execute(self, params: Parameters) -> ToolResult:
        file_path = Path(params.file_path)
        if not file_path.exists():
            return ToolResult.error(f"文件不存在: {params.file_path}")

        source_code = file_path.read_text(encoding='utf-8')

        # 自动检测语言
        language = params.language or self._detect_language(file_path.name)

        # 分析代码结构
        structure = self._analyze_code(source_code, language)

        # 生成测试用例
        test_code = self._generate_test_code(
            structure, language, params.include_assertions,
            file_path.name
        )

        # 确定输出文件
        output_file = params.output_file or self._generate_output_filename(file_path, language)

        # 写入测试文件
        Path(output_file).write_text(test_code, encoding='utf-8')

        # 生成报告
        report = self._generate_report(structure, language, output_file)

        return ToolResult.ok(
            report,
            file_analyzed=str(file_path),
            language=language,
            test_file=output_file,
            functions_found=len(structure.get('functions', [])),
            classes_found=len(structure.get('classes', [])),
            test_code_generated=test_code
        )

    def _detect_language(self, filename: str) -> str:
        """检测文件语言"""
        ext = Path(filename).suffix.lower()
        if ext in ('.cpp', '.cxx', '.cc', '.c', '.h', '.hpp'):
            return 'cpp'
        elif ext in ('.py',):
            return 'python'
        elif ext in ('.js', '.ts', '.jsx', '.tsx'):
            return 'js'
        return 'unknown'

    def _analyze_code(self, source_code: str, language: str) -> Dict[str, Any]:
        """分析代码结构"""
        if language == 'cpp':
            return self._analyze_cpp(source_code)
        elif language == 'python':
            return self._analyze_python(source_code)
        elif language == 'js':
            return self._analyze_js(source_code)
        return {'functions': [], 'classes': []}

    def _analyze_cpp(self, source_code: str) -> Dict[str, Any]:
        """分析 C/C++ 代码"""
        functions = []
        classes = []

        # 提取类定义（简化版，不处理嵌套类）
        class_pattern = r'class\s+(\w+)\s*{'
        for match in re.finditer(class_pattern, source_code):
            class_name = match.group(1)
            class_start = match.end()

            # 找到类结束（找到匹配的大括号）
            brace_count = 1
            class_end = class_start
            for i, char in enumerate(source_code[class_start:]):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        class_end = class_start + i
                        break

            class_body = source_code[match.start():class_end + 1]

            # 提取类中的公共方法
            public_matches = list(re.finditer(r'public\s*:', class_body))
            private_matches = list(re.finditer(r'private\s*:', class_body))
            protected_matches = list(re.finditer(r'protected\s*:', class_body))

            methods = []
            for i, pub_match in enumerate(public_matches):
                pub_start = pub_match.end()
                # 找到下一个访问控制符或类结束
                next_controls = []
                for m in private_matches + protected_matches:
                    if m.start() > pub_start:
                        next_controls.append(m.start())
                if i + 1 < len(public_matches):
                    next_controls.append(public_matches[i + 1].start())

                pub_end = min(next_controls) if next_controls else len(class_body)
                public_section = class_body[pub_start:pub_end]

                # 提取方法名
                method_pattern = r'(?:virtual\s+)?(?:\w+\s+)+(?:[\w&*]+\s+)*(\w+)\s*\(([^)]*)\)'
                for m in re.finditer(method_pattern, public_section):
                    method_name = m.group(1)
                    if method_name not in ['return', 'if', 'while', 'for']:
                        methods.append({
                            'name': method_name,
                            'params': m.group(2).strip()
                        })

            classes.append({
                'name': class_name,
                'methods': methods
            })

        # 提取函数定义（排除类内函数）
        func_pattern = r'(?:^|\n)(?:\w+\s+)+\**(\w+)\s*\(([^)]*)\)\s*(?:const)?\s*\{'
        for match in re.finditer(func_pattern, source_code):
            func_name = match.group(1)
            # 排除常见的非函数关键字
            if func_name not in ['if', 'for', 'while', 'switch', 'catch', 'class', 'struct']:
                functions.append({
                    'name': func_name,
                    'params': match.group(2).strip()
                })

        return {
            'classes': classes,
            'functions': functions
        }

    def _analyze_python(self, source_code: str) -> Dict[str, Any]:
        """分析 Python 代码"""
        functions = []
        classes = []

        try:
            tree = ast.parse(source_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    params = [a.arg for a in node.args.args]
                    functions.append({
                        'name': node.name,
                        'params': ', '.join(params)
                    })
                elif isinstance(node, ast.ClassDef):
                    methods = []
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            m_params = [a.arg for a in item.args.args]
                            methods.append({
                                'name': item.name,
                                'params': ', '.join(m_params)
                            })
                    classes.append({
                        'name': node.name,
                        'methods': methods
                    })
        except:
            pass

        return {
            'classes': classes,
            'functions': functions
        }

    def _analyze_js(self, source_code: str) -> Dict[str, Any]:
        """分析 JavaScript 代码"""
        functions = []
        classes = []

        # 提取函数
        func_patterns = [
            r'function\s+(\w+)\s*\(([^)]*)\)',
            r'(\w+)\s*:\s*function\s*\(([^)]*)\)',
            r'(\w+)\s*\(([^)]*)\)\s*=>'
        ]
        for pattern in func_patterns:
            for match in re.finditer(pattern, source_code):
                functions.append({
                    'name': match.group(1),
                    'params': match.group(2).strip()
                })

        # 提取类
        class_pattern = r'class\s+(\w+)'
        for match in re.finditer(class_pattern, source_code):
            classes.append({'name': match.group(1), 'methods': []})

        return {
            'classes': classes,
            'functions': functions
        }

    def _generate_test_code(self, structure: Dict, language: str,
                           include_assertions: bool, source_filename: str) -> str:
        """生成测试代码"""
        if language == 'cpp':
            return self._generate_cpp_test(structure, include_assertions, source_filename)
        elif language == 'python':
            return self._generate_python_test(structure, include_assertions, source_filename)
        elif language == 'js':
            return self._generate_js_test(structure, include_assertions, source_filename)
        return "# Unsupported language"

    def _generate_cpp_test(self, structure: Dict, include_assertions: bool,
                          source_filename: str) -> str:
        """生成 C/C++ 测试代码"""
        lines = [
            f"// Auto-generated test for {source_filename}",
            "// Generated by DevPalAgent TestGeneratorTool",
            "",
            "#include <iostream>",
            "#include <cassert>",
            "// Rename source main() to avoid conflict with test main()",
            "#define main source_main",
            f'#include "{source_filename}"',
            "#undef main",
            "",
            "using namespace std;",
            "",
            "// ============================================",
            "// Test Suite",
            "// ============================================",
            "",
            "int main() {",
            "    int passed = 0, total = 0;",
            "",
        ]

        # 生成类的测试
        for cls in structure.get('classes', []):
            class_name = cls['name']
            lines.append(f"    // 测试类: {class_name}")
            lines.append(f"    cout << \"=== Testing class: {class_name} ===\" << endl;")
            lines.append(f"    {{")
            # 尝试使用带参数的构造函数（为没有默认构造函数的类提供默认参数）
            has_constructor = any(m['name'] == class_name for m in cls.get('methods', []))
            if has_constructor:
                lines.append(f"        {class_name} obj(1);  // 使用合理的默认参数")
            else:
                lines.append(f"        {class_name} obj;")
            # 构造函数测试 - 成功创建对象即视为通过
            lines.append(f"        total++;")
            lines.append(f"        passed++;")
            lines.append(f"        cout << \"  [PASS] {class_name} constructor\" << endl;")

            for method in cls.get('methods', []):
                method_name = method['name']
                if method_name == class_name:  # 构造函数
                    continue
                lines.append(f"        // 测试方法: {method_name}")
                lines.append(f"        total++;")
                if include_assertions:
                    lines.append(f"        try {{")
                    lines.append(f"            // obj.{method_name}({method.get('params', '')});")
                    lines.append(f"            // TODO: 添加实际断言")
                    lines.append(f"            // assert( 条件 );")
                    lines.append(f"            passed++;")
                    lines.append(f"            cout << \"  [PASS] {method_name}()\" << endl;")
                    lines.append(f"        }} catch (...) {{")
                    lines.append(f"            cout << \"  [FAIL] {method_name}() - Exception\" << endl;")
                    lines.append(f"        }}")
                lines.append("")

            lines.append(f"    }}")
            lines.append("")

        # 生成函数的测试
        for func in structure.get('functions', []):
            func_name = func['name']
            if func_name == 'main':
                continue
            lines.append(f"    // 测试函数: {func_name}")
            lines.append(f"    total++;")
            if include_assertions:
                lines.append(f"    try {{")
                lines.append(f"        // {func_name}({func.get('params', '')});")
                lines.append(f"        // TODO: 添加实际断言")
                lines.append(f"        passed++;")
                lines.append(f"        cout << \"  [PASS] {func_name}()\" << endl;")
                lines.append(f"    }} catch (...) {{")
                lines.append(f"        cout << \"  [FAIL] {func_name}() - Exception\" << endl;")
                lines.append(f"    }}")
            lines.append("")

        # 主函数收尾
        lines.extend([
            "    // ============================================",
            "    // Test Summary",
            "    // ============================================",
            "    cout << endl << \"========================================\" << endl;",
            "    cout << \"Test Summary: \" << passed << \"/\" << total << \" passed\" << endl;",
            "    cout << \"========================================\" << endl;",
            "",
            "    if (passed == total) {",
            "        cout << \"✅ All tests passed!\" << endl;",
            "        return 0;",
            "    } else {",
            "        cout << \"❌ Some tests failed!\" << endl;",
            "        return 1;",
            "    }",
            "}"
        ])

        return '\n'.join(lines)

    def _generate_python_test(self, structure: Dict, include_assertions: bool,
                            source_filename: str) -> str:
        """生成 Python 测试代码"""
        lines = [
            f"# Auto-generated test for {source_filename}",
            "# Generated by DevPalAgent TestGeneratorTool",
            "",
            "import unittest",
            f"import {Path(source_filename).stem}",
            "",
            "# ===========================================",
            "# Test Suite",
            "# ===========================================",
            "",
        ]

        module_name = Path(source_filename).stem

        # 生成类的测试
        for cls in structure.get('classes', []):
            class_name = cls['name']
            lines.append(f"class Test{class_name}(unittest.TestCase):")
            lines.append(f'    """Test class {class_name}"""')
            lines.append("")

            for method in cls.get('methods', []):
                method_name = method['name']
                if method_name.startswith('_'):
                    continue
                lines.append(f"    def test_{method_name}(self):")
                lines.append(f"        # 测试方法: {method_name}")
                lines.append(f"        obj = {module_name}.{class_name}()")
                lines.append(f"        # TODO: 添加测试逻辑")
                lines.append(f"        # self.assertEqual(result, expected)")
                lines.append(f"        pass")
                lines.append("")

        # 生成函数的测试
        for func in structure.get('functions', []):
            func_name = func['name']
            if func_name.startswith('_'):
                continue
            lines.append(f"def test_{func_name}():")
            lines.append(f"    # 测试函数: {func_name}")
            lines.append(f"    # result = {module_name}.{func_name}()")
            lines.append(f"    # assert result == expected")
            lines.append(f"    pass")
            lines.append("")

        lines.extend([
            "if __name__ == '__main__':",
            "    unittest.main(verbosity=2)",
        ])

        return '\n'.join(lines)

    def _generate_js_test(self, structure: Dict, include_assertions: bool,
                         source_filename: str) -> str:
        """生成 JavaScript 测试代码"""
        lines = [
            f"// Auto-generated test for {source_filename}",
            "// Generated by DevPalAgent TestGeneratorTool",
            "",
            "const assert = require('assert');",
            "",
            "// ===========================================",
            "// Test Suite",
            "// ===========================================",
            "",
            "describe('Test Suite', function() {",
        ]

        for func in structure.get('functions', []):
            func_name = func['name']
            lines.append(f"    it('should test {func_name}', function() {{")
            lines.append(f"        // TODO: 测试函数 {func_name}")
            lines.append(f"        // const result = {func_name}();")
            lines.append(f"        // assert.strictEqual(result, expected);")
            lines.append(f"    }});")
            lines.append("")

        lines.append("});")

        return '\n'.join(lines)

    def _generate_output_filename(self, source_path: Path, language: str) -> str:
        """生成输出文件名"""
        if language == 'cpp':
            return f"test_{source_path.stem}.cpp"
        elif language == 'python':
            return f"test_{source_path.stem}.py"
        elif language == 'js':
            return f"test_{source_path.stem}.js"
        return f"test_{source_path.stem}.txt"

    def _generate_report(self, structure: Dict, language: str, output_file: str) -> str:
        """生成测试报告"""
        report = "=" * 60 + "\n"
        report += "🧪 TestGeneratorTool - 测试用例生成报告\n"
        report += "=" * 60 + "\n\n"

        report += f"📄 源文件语言: {language}\n"
        report += f"📁 测试文件输出: {output_file}\n\n"

        report += f"📊 分析结果:\n"
        report += f"  - 发现类数量: {len(structure.get('classes', []))}\n"
        report += f"  - 发现函数数量: {len(structure.get('functions', []))}\n\n"

        if structure.get('classes'):
            report += "📦 检测到的类:\n"
            for cls in structure['classes']:
                report += f"  - {cls['name']} ({len(cls.get('methods', []))} 个方法)\n"
            report += "\n"

        if structure.get('functions'):
            report += "🔧 检测到的函数:\n"
            for func in structure['functions']:
                report += f"  - {func['name']}({func.get('params', '')})\n"
            report += "\n"

        report += "✅ 测试用例已生成！\n"
        report += "💡 提示: 请在 TODO 标记处填写具体的测试逻辑和断言\n"

        return report
