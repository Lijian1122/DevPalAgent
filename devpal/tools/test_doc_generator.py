# -*- coding: utf-8 -*-
"""
测试用例文档生成工具
生成专业的测试用例文档，包含测试分析、覆盖范围、边界条件检查等
"""
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult


class TestDocGeneratorTool(BaseTool):
    """专业测试用例文档生成工具"""

    name = "test_doc_generator"
    description = "生成专业的测试用例文档，包含测试分析、覆盖范围、边界条件检查、合理性评估"

    class Parameters(BaseModel):
        file_path: str = Field(description="要测试的源代码文件路径")
        test_file: Optional[str] = Field(
            default=None,
            description="已存在的测试文件路径（可选，不传则自动生成）"
        )
        output_doc: Optional[str] = Field(
            default=None,
            description="输出的测试文档路径（默认: test_{filename}_doc.md）"
        )
        include_coverage_analysis: bool = Field(
            default=True,
            description="是否包含测试覆盖分析"
        )
        include_boundary_analysis: bool = Field(
            default=True,
            description="是否包含边界条件分析"
        )
        include_quality_assessment: bool = Field(
            default=True,
            description="是否包含测试用例质量评估"
        )

    def _execute(self, params: Parameters) -> ToolResult:
        file_path = Path(params.file_path)
        if not file_path.exists():
            return ToolResult.error(f"文件不存在: {params.file_path}")

        source_code = file_path.read_text(encoding='utf-8')
        language = self._detect_language(file_path.name)

        # 1. 分析代码结构
        code_structure = self._analyze_code_structure(source_code, language)

        # 2. 生成测试用例设计
        test_cases = self._generate_test_cases(code_structure, language)

        # 3. 分析边界条件
        boundary_analysis = self._analyze_boundary_conditions(code_structure, language)

        # 4. 评估测试用例质量
        quality_assessment = self._assess_test_quality(test_cases, code_structure)

        # 5. 生成完整文档
        doc_content = self._generate_documentation(
            source_file=str(file_path),
            language=language,
            code_structure=code_structure,
            test_cases=test_cases,
            boundary_analysis=boundary_analysis,
            quality_assessment=quality_assessment,
            params=params
        )

        # 6. 保存文档
        output_doc = params.output_doc or f"test_{file_path.stem}_doc.md"
        Path(output_doc).write_text(doc_content, encoding='utf-8')

        return ToolResult.ok(
            self._generate_summary(
                str(file_path), output_doc, code_structure,
                test_cases, quality_assessment
            ),
            source_file=str(file_path),
            test_doc_file=output_doc,
            functions_analyzed=len(code_structure.get('functions', [])),
            classes_analyzed=len(code_structure.get('classes', [])),
            test_cases_generated=len(test_cases),
            quality_score=quality_assessment.get('overall_score', 0),
            overall_score=quality_assessment.get('overall_score', 0),
            overall_grade=quality_assessment.get('overall_grade', '')
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

    def _analyze_code_structure(self, source_code: str, language: str) -> Dict[str, Any]:
        """深入分析代码结构"""
        if language == 'cpp':
            return self._analyze_cpp_structure(source_code)
        elif language == 'python':
            return self._analyze_python_structure(source_code)
        return {'functions': [], 'classes': [], 'variables': []}

    def _analyze_cpp_structure(self, source_code: str) -> Dict[str, Any]:
        """深入分析C++代码结构"""
        functions = []
        classes = []
        member_variables = []

        # 分析类
        class_pattern = r'class\s+(\w+)\s*{'
        for match in re.finditer(class_pattern, source_code):
            class_name = match.group(1)
            class_start = match.end()

            # 找到类结束
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

            # 提取成员变量
            var_pattern = r'(?:public|private|protected):[^}]*?(\w+(?:\s*[*&])?)\s+(\w+)\s*;'
            for var_match in re.finditer(var_pattern, class_body):
                member_variables.append({
                    'class': class_name,
                    'type': var_match.group(1),
                    'name': var_match.group(2)
                })

            # 提取方法
            public_matches = list(re.finditer(r'public\s*:', class_body))
            methods = []
            for i, pub_match in enumerate(public_matches):
                pub_start = pub_match.end()
                next_controls = []
                for m in re.finditer(r'(?:private|protected)\s*:', class_body):
                    if m.start() > pub_start:
                        next_controls.append(m.start())
                pub_end = min(next_controls) if next_controls else len(class_body)
                public_section = class_body[pub_start:pub_end]

                method_pattern = r'(?:virtual\s+)?(?:\w+\s+)+(?:[\w&*]+\s+)*(\w+)\s*\(([^)]*)\)'
                for m in re.finditer(method_pattern, public_section):
                    method_name = m.group(1)
                    # 排除C++关键字（如 for/while/if 等，避免误识别
                    if method_name in ['for', 'while', 'if', 'else', 'switch', 'catch', 'try']:
                        continue
                    params_str = m.group(2).strip()
                    params = self._parse_params(params_str)
                    methods.append({
                        'name': method_name,
                        'params': params,
                        'params_str': params_str
                    })

            classes.append({
                'name': class_name,
                'methods': methods,
                'member_variables': [v for v in member_variables if v['class'] == class_name]
            })

        # 分析函数
        func_pattern = r'(?:^|\n)(?:\w+\s+)+\**(\w+)\s*\(([^)]*)\)\s*(?:const)?\s*\{'
        for match in re.finditer(func_pattern, source_code):
            func_name = match.group(1)
            if func_name not in ['if', 'for', 'while', 'switch', 'catch', 'class', 'struct']:
                params_str = match.group(2).strip()
                params = self._parse_params(params_str)
                functions.append({
                    'name': func_name,
                    'params': params,
                    'params_str': params_str
                })

        return {
            'classes': classes,
            'functions': functions,
            'member_variables': member_variables
        }

    def _analyze_python_structure(self, source_code: str) -> Dict[str, Any]:
        """分析Python代码结构"""
        import ast
        functions = []
        classes = []

        try:
            tree = ast.parse(source_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    args = [a.arg for a in node.args.args]
                    functions.append({
                        'name': node.name,
                        'params': args,
                        'params_str': ', '.join(args)
                    })
                elif isinstance(node, ast.ClassDef):
                    methods = []
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            args = [a.arg for a in item.args.args]
                            methods.append({
                                'name': item.name,
                                'params': args,
                                'params_str': ', '.join(args)
                            })
                    classes.append({
                        'name': node.name,
                        'methods': methods
                    })
        except:
            pass

        return {'classes': classes, 'functions': functions}

    def _parse_params(self, params_str: str) -> List[Dict[str, str]]:
        """解析函数参数"""
        params = []
        if not params_str or params_str == 'void':
            return params

        for param in params_str.split(','):
            param = param.strip()
            if param in ['void', '']:
                continue

            # 分离类型和名称
            parts = param.split()
            if len(parts) >= 2:
                name = parts[-1].replace('*', '').replace('&', '')
                type_ = ' '.join(parts[:-1])
                params.append({'type': type_, 'name': name})
            elif len(parts) == 1:
                params.append({'type': 'unknown', 'name': parts[0]})

        return params

    def _generate_test_cases(self, structure: Dict, language: str) -> List[Dict]:
        """生成详细的测试用例"""
        test_cases = []
        test_id = 1

        # 生成类的测试用例
        for cls in structure.get('classes', []):
            class_name = cls['name']

            # 1. 对象创建测试
            test_cases.append({
                'id': f'TC-{test_id:03d}',
                'category': '对象创建',
                'target': f'{class_name} 构造函数',
                'description': f'测试 {class_name} 对象正常创建',
                'preconditions': '无',
                'test_steps': [
                    f'创建 {class_name} 实例对象',
                    '验证对象不为null/None'
                ],
                'expected_result': '对象创建成功，无异常抛出',
                'priority': 'High',
                'test_type': '功能测试'
            })
            test_id += 1

            # 2. 每个方法的测试
            for method in cls.get('methods', []):
                method_name = method['name']
                if method_name == class_name:  # 跳过构造函数
                    continue

                # 功能测试
                test_cases.append({
                    'id': f'TC-{test_id:03d}',
                    'category': '方法调用',
                    'target': f'{class_name}.{method_name}()',
                    'description': f'测试 {method_name} 方法正常调用',
                    'preconditions': f'{class_name} 对象已创建',
                    'test_steps': [
                        '准备测试数据',
                        f'调用 obj.{method_name}({method.get("params_str", "")})',
                        '验证返回值/对象状态'
                    ],
                    'expected_result': '方法调用成功，返回符合预期的值',
                    'priority': 'High',
                    'test_type': '功能测试'
                })
                test_id += 1

                # 参数边界测试
                params = method.get('params', [])
                if params:
                    test_cases.append({
                        'id': f'TC-{test_id:03d}',
                        'category': '边界条件',
                        'target': f'{class_name}.{method_name}() - 参数边界',
                        'description': f'测试 {method_name} 方法参数边界值',
                        'preconditions': f'{class_name} 对象已创建',
                        'test_steps': [
                            '使用最小值/空值调用',
                            '使用最大值调用',
                            '使用非法值调用（如适用）'
                        ],
                        'expected_result': '边界值处理正确，无崩溃/异常',
                        'priority': 'Medium',
                        'test_type': '边界测试'
                    })
                    test_id += 1

        # 3. 自由函数测试
        for func in structure.get('functions', []):
            if func['name'] == 'main':
                continue

            test_cases.append({
                'id': f'TC-{test_id:03d}',
                'category': '函数测试',
                'target': f'{func["name"]}()',
                'description': f'测试 {func["name"]} 函数功能正确性',
                'preconditions': '无',
                'test_steps': [
                    '准备测试输入',
                    f'调用 {func["name"]}({func.get("params_str", "")})',
                    '验证返回值'
                ],
                'expected_result': '函数返回正确结果，无异常',
                'priority': 'High',
                'test_type': '功能测试'
            })
            test_id += 1

        # 4. 异常/错误处理测试
        test_cases.append({
            'id': f'TC-{test_id:03d}',
            'category': '异常处理',
            'target': '异常/错误处理',
            'description': '测试异常情况下程序的健壮性',
            'preconditions': '无',
            'test_steps': [
                '传入空指针/None',
                '传入非法参数值',
                '调用不存在的方法（如适用）'
            ],
            'expected_result': '程序优雅处理错误，无崩溃/未处理异常',
            'priority': 'Medium',
            'test_type': '异常测试'
        })
        test_id += 1

        # 5. 内存泄漏测试（针对C++）
        if language == 'cpp':
            test_cases.append({
                'id': f'TC-{test_id:03d}',
                'category': '内存安全',
                'target': '内存管理',
                'description': '测试内存分配/释放正确性',
                'preconditions': '支持内存检测工具（Valgrind/ASAN）',
                'test_steps': [
                    '多次创建/销毁对象',
                    '执行涉及动态内存的操作',
                    '使用内存检测工具验证'
                ],
                'expected_result': '无内存泄漏，无野指针访问',
                'priority': 'High',
                'test_type': '内存测试'
            })
            test_id += 1

        # 6. 并发测试（针对线程池）
        if any('thread' in cls['name'].lower() for cls in structure.get('classes', [])):
            test_cases.append({
                'id': f'TC-{test_id:03d}',
                'category': '并发安全',
                'target': '线程安全',
                'description': '测试多线程并发访问的安全性',
                'preconditions': '多线程环境',
                'test_steps': [
                    '多个线程同时调用对象方法',
                    '验证数据一致性',
                    '检查竞态条件/死锁'
                ],
                'expected_result': '并发执行正确，无数据竞争，无死锁',
                'priority': 'High',
                'test_type': '并发测试'
            })
            test_id += 1

        return test_cases

    def _analyze_boundary_conditions(self, structure: Dict, language: str) -> Dict[str, Any]:
        """分析边界条件"""
        boundaries = {
            'input_boundaries': [],
            'edge_cases': [],
            'error_conditions': []
        }

        # 基于函数参数的边界分析
        all_params = []
        for func in structure.get('functions', []):
            all_params.extend(func.get('params', []))
        for cls in structure.get('classes', []):
            for method in cls.get('methods', []):
                all_params.extend(method.get('params', []))

        # 数值类型边界
        numeric_types = ['int', 'size_t', 'long', 'float', 'double', 'unsigned']
        for param in all_params:
            type_ = param.get('type', '')
            name = param.get('name', '')

            if any(nt in type_ for nt in numeric_types):
                boundaries['input_boundaries'].append({
                    'parameter': name,
                    'type': type_,
                    'boundaries': [
                        '最小值 (如 0, INT_MIN)',
                        '最大值 (如 UINT_MAX, INT_MAX)',
                        '负值 (如适用)',
                        '零值'
                    ]
                })

        # 通用边界情况
        boundaries['edge_cases'] = [
            '空输入 / 空字符串',
            '单个元素',
            '重复元素',
            '已排序 / 逆序输入',
            '极大数据量（性能考虑）'
        ]

        # 错误情况
        boundaries['error_conditions'] = [
            '空指针 / nullptr',
            '无效索引 / 越界访问',
            '非法参数值',
            '资源耗尽（内存不足）',
            '并发竞态条件'
        ]

        return boundaries

    def _assess_test_quality(self, test_cases: List[Dict], structure: Dict) -> Dict[str, Any]:
        """评估测试用例质量"""
        assessment = {
            'categories': set(),
            'coverage': {},
            'issues': [],
            'recommendations': []
        }

        # 统计测试类别
        categories = {}
        types = {}
        priorities = {}
        for tc in test_cases:
            cat = tc.get('category', '')
            t_type = tc.get('test_type', '')
            prio = tc.get('priority', '')
            categories[cat] = categories.get(cat, 0) + 1
            types[t_type] = types.get(t_type, 0) + 1
            priorities[prio] = priorities.get(prio, 0) + 1

        assessment['by_category'] = categories
        assessment['by_type'] = types
        assessment['by_priority'] = priorities

        # 覆盖率评估
        total_funcs = len(structure.get('functions', []))
        total_classes = len(structure.get('classes', []))
        total_methods = sum(len(c.get('methods', [])) for c in structure.get('classes', []))

        functional_tests = sum(1 for tc in test_cases if tc.get('test_type') == '功能测试')
        coverage_score = min(100, int((functional_tests / max(1, total_funcs + total_methods)) * 100))

        assessment['coverage'] = {
            'total_functions': total_funcs,
            'total_classes': total_classes,
            'total_methods': total_methods,
            'functional_tests': functional_tests,
            'coverage_score': coverage_score
        }

        # 质量评分
        score = 0
        max_score = 100

        # 覆盖率 (40分)
        score += min(40, int(coverage_score * 0.4))

        # 测试类型多样性 (20分)
        type_count = len(types)
        score += min(20, type_count * 4)

        # 边界测试 (20分)
        if '边界条件' in categories or '边界测试' in types:
            score += 20

        # 异常/错误处理 (20分)
        if '异常处理' in categories or '异常测试' in types:
            score += 20

        # 问题和建议
        assessment['overall_score'] = score
        assessment['overall_grade'] = self._score_to_grade(score)

        if score >= 80:
            assessment['issues'].append('✅ 测试覆盖良好，涵盖主要功能点')
        elif score >= 60:
            assessment['issues'].append('⚠️ 测试覆盖基本足够，但可以更全面')
            assessment['recommendations'].append('建议增加更多边界条件测试')
        else:
            assessment['issues'].append('❌ 测试覆盖不足，需要补充更多测试')
            assessment['recommendations'].append('必须补充功能测试和边界测试')

        if '并发测试' not in types and total_classes > 0:
            assessment['recommendations'].append('建议添加并发/线程安全测试')

        if '内存测试' not in types:
            assessment['recommendations'].append('建议添加内存泄漏/安全测试')

        return assessment

    def _score_to_grade(self, score: int) -> str:
        """分数转等级"""
        if score >= 90:
            return 'A (优秀)'
        elif score >= 80:
            return 'B (良好)'
        elif score >= 70:
            return 'C (一般)'
        elif score >= 60:
            return 'D (及格)'
        else:
            return 'F (需要改进)'

    def _generate_documentation(self, source_file: str, language: str,
                                code_structure: Dict, test_cases: List[Dict],
                                boundary_analysis: Dict, quality_assessment: Dict,
                                params: Parameters) -> str:
        """生成完整的测试文档"""
        from datetime import datetime

        doc_lines = []

        # 标题
        doc_lines.append(f'# 测试用例文档 - {Path(source_file).name}')
        doc_lines.append('')
        doc_lines.append(f'> 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        doc_lines.append(f'> 源文件: `{source_file}`')
        doc_lines.append(f'> 语言: {language.upper()}')
        doc_lines.append('')

        # 目录
        doc_lines.append('## 目录')
        doc_lines.append('- [1. 测试对象概述](#1-测试对象概述)')
        doc_lines.append('- [2. 代码结构分析](#2-代码结构分析)')
        doc_lines.append('- [3. 测试用例详情](#3-测试用例详情)')
        doc_lines.append('- [4. 边界条件分析](#4-边界条件分析)')
        doc_lines.append('- [5. 测试质量评估](#5-测试质量评估)')
        doc_lines.append('- [6. 改进建议](#6-改进建议)')
        doc_lines.append('')

        # 1. 测试对象概述
        doc_lines.append('## 1. 测试对象概述')
        doc_lines.append('')
        doc_lines.append(f'本测试文档针对 `{Path(source_file).name}` 文件中的代码模块设计测试用例。')
        doc_lines.append('')

        # 测试对象统计表格
        doc_lines.append('| 统计项 | 数量 |')
        doc_lines.append('|--------|------|')
        doc_lines.append(f'| 待测试的类数量 | {len(code_structure.get("classes", []))} 个 |')
        doc_lines.append(f'| 待测试的方法数量 | {sum(len(c.get("methods", [])) for c in code_structure.get("classes", []))} 个 |')
        doc_lines.append(f'| 待测试的函数数量 | {len(code_structure.get("functions", []))} 个 |')
        doc_lines.append(f'| **总测试用例数量** | **{len(test_cases)} 个** |')
        doc_lines.append('')

        # 2. 代码结构分析
        doc_lines.append('## 2. 代码结构分析')
        doc_lines.append('')

        for cls in code_structure.get('classes', []):
            doc_lines.append(f'### 2.1 类: `{cls["name"]}`')
            doc_lines.append('')
            if cls.get('member_variables'):
                doc_lines.append('#### 成员变量')
                for var in cls['member_variables']:
                    doc_lines.append(f'- `{var["type"]} {var["name"]}`')
                doc_lines.append('')
            if cls.get('methods'):
                doc_lines.append('#### 公共方法')
                for method in cls['methods']:
                    doc_lines.append(f'- `{method["name"]}({method["params_str"]})`')
                doc_lines.append('')

        if code_structure.get('functions'):
            doc_lines.append('### 2.2 自由函数')
            doc_lines.append('')
            for func in code_structure['functions']:
                if func['name'] != 'main':
                    doc_lines.append(f'- `{func["name"]}({func["params_str"]})`')
            doc_lines.append('')

        # 3. 测试用例详情 - 表格形式
        doc_lines.append('## 3. 测试用例详情')
        doc_lines.append('')

        # 按测试类型分组显示表格
        by_type = {}
        for tc in test_cases:
            t_type = tc.get('test_type', '其他')
            if t_type not in by_type:
                by_type[t_type] = []
            by_type[t_type].append(tc)

        # 测试类型的优先级顺序
        type_order = ['功能测试', '边界测试', '异常测试', '并发测试', '内存测试']
        sorted_types = sorted(by_type.keys(), key=lambda x: (type_order.index(x) if x in type_order else 99, x))

        for i, t_type in enumerate(sorted_types, 1):
            tcs = by_type[t_type]
            doc_lines.append(f'### 3.{i} {t_type}')
            doc_lines.append('')

            # 表格表头
            doc_lines.append('| 测试ID | 测试目标 | 优先级 | 前置条件 | 测试步骤 | 预期结果 |')
            doc_lines.append('|--------|----------|--------|----------|----------|----------|')

            for tc in tcs:
                # 格式化步骤为多行
                steps = '<br>'.join([f'{i+1}. {s}' for i, s in enumerate(tc['test_steps'])])
                # 转义管道符
                target = tc['target'].replace('|', '\\|')
                precond = tc['preconditions'].replace('|', '\\|')
                expected = tc['expected_result'].replace('|', '\\|')

                doc_lines.append(f'| {tc["id"]} | `{target}` | {tc["priority"]} | {precond} | {steps} | {expected} |')

            doc_lines.append('')

        # 测试用例统计表格
        doc_lines.append(f'### 3.{len(sorted_types)+1} 测试用例统计')
        doc_lines.append('')
        doc_lines.append('| 测试类型 | 用例数量 | 占比 |')
        doc_lines.append('|----------|----------|------|')
        total = len(test_cases)
        for t_type, tcs in sorted(by_type.items()):
            pct = int(len(tcs) / total * 100) if total > 0 else 0
            doc_lines.append(f'| {t_type} | {len(tcs)} | {pct}% |')
        doc_lines.append(f'| **合计** | **{total}** | **100%** |')
        doc_lines.append('')

        # 4. 边界条件分析
        doc_lines.append('## 4. 边界条件分析')
        doc_lines.append('')

        if boundary_analysis.get('input_boundaries'):
            doc_lines.append('### 4.1 输入参数边界')
            doc_lines.append('')
            for ib in boundary_analysis['input_boundaries']:
                doc_lines.append(f'#### 参数: `{ib["parameter"]}` ({ib["type"]})')
                for b in ib['boundaries']:
                    doc_lines.append(f'- [ ] {b}')
                doc_lines.append('')

        doc_lines.append('### 4.2 通用边界情况')
        doc_lines.append('')
        for ec in boundary_analysis.get('edge_cases', []):
            doc_lines.append(f'- [ ] {ec}')
        doc_lines.append('')

        doc_lines.append('### 4.3 错误/异常条件')
        doc_lines.append('')
        for ec in boundary_analysis.get('error_conditions', []):
            doc_lines.append(f'- [ ] {ec}')
        doc_lines.append('')

        # 5. 测试质量评估
        doc_lines.append('## 5. 测试质量评估')
        doc_lines.append('')

        qa = quality_assessment
        doc_lines.append('### 5.1 总体评分')
        doc_lines.append('')
        doc_lines.append('| 评估项 | 结果 |')
        doc_lines.append('|--------|------|')
        doc_lines.append(f'| **总体得分** | **{qa["overall_score"]}/100** |')
        doc_lines.append(f'| **评级** | **{qa["overall_grade"]}** |')
        doc_lines.append('')

        doc_lines.append('### 5.2 测试覆盖率分析')
        doc_lines.append('')
        cov = qa.get('coverage', {})
        doc_lines.append('| 指标 | 数值 |')
        doc_lines.append('|------|------|')
        doc_lines.append(f'| 类数量 | {cov.get("total_classes", 0)} 个 |')
        doc_lines.append(f'| 方法数量 | {cov.get("total_methods", 0)} 个 |')
        doc_lines.append(f'| 函数数量 | {cov.get("total_functions", 0)} 个 |')
        doc_lines.append(f'| 功能测试数 | {cov.get("functional_tests", 0)} 个 |')
        doc_lines.append(f'| **覆盖率估算** | **{cov.get("coverage_score", 0)}%** |')
        doc_lines.append('')

        doc_lines.append('### 5.3 测试用例分布统计')
        doc_lines.append('')
        doc_lines.append('| 测试类型 | 用例数量 |')
        doc_lines.append('|----------|----------|')
        for t_type, count in sorted(qa.get('by_type', {}).items()):
            doc_lines.append(f'| {t_type} | {count} 个 |')
        doc_lines.append('')

        # 6. 改进建议
        doc_lines.append('## 6. 改进建议')
        doc_lines.append('')

        doc_lines.append('### 6.1 质量评估结论')
        doc_lines.append('')
        for issue in qa.get('issues', []):
            doc_lines.append(f'- {issue}')
        doc_lines.append('')

        if qa.get('recommendations'):
            doc_lines.append('### 6.2 具体改进建议')
            doc_lines.append('')
            for rec in qa['recommendations']:
                doc_lines.append(f'- [ ] {rec}')
            doc_lines.append('')

        # 结尾
        doc_lines.append('---')
        doc_lines.append('')
        doc_lines.append('*本文档由 DevPalAgent TestDocGeneratorTool 自动生成*')

        return '\n'.join(doc_lines)

    def _generate_summary(self, source_file: str, output_doc: str,
                          code_structure: Dict, test_cases: List[Dict],
                          quality_assessment: Dict) -> str:
        """生成执行摘要"""
        qa = quality_assessment
        cov = qa.get('coverage', {})

        summary = '=' * 60 + '\n'
        summary += '🧪 测试用例文档生成完成\n'
        summary += '=' * 60 + '\n\n'

        summary += f'📄 源文件: {source_file}\n'
        summary += f'📁 输出文档: {output_doc}\n\n'

        summary += '📊 代码结构分析:\n'
        summary += f'  - 类数量: {len(code_structure.get("classes", []))}\n'
        summary += f'  - 方法数量: {cov.get("total_methods", 0)}\n'
        summary += f'  - 函数数量: {cov.get("total_functions", 0)}\n\n'

        summary += '✅ 测试用例生成:\n'
        summary += f'  - 总测试用例: {len(test_cases)} 个\n'
        summary += f'  - 功能测试: {qa.get("by_type", {}).get("功能测试", 0)} 个\n'
        summary += f'  - 边界测试: {qa.get("by_type", {}).get("边界测试", 0)} 个\n'
        summary += f'  - 异常测试: {qa.get("by_type", {}).get("异常测试", 0)} 个\n\n'

        summary += '📈 质量评估结果:\n'
        summary += f'  - 总体得分: {qa["overall_score"]}/100\n'
        summary += f'  - 评级: {qa["overall_grade"]}\n'
        summary += f'  - 覆盖率估算: {cov.get("coverage_score", 0)}%\n\n'

        if qa.get('recommendations'):
            summary += '[建议] 改进建议:\n'
            for rec in qa['recommendations'][:3]:
                summary += f'  - {rec}\n'

        return summary
