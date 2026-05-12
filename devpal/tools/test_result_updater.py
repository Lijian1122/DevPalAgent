# -*- coding: utf-8 -*-
"""
测试结果更新工具
运行测试并将结果更新到测试文档中
"""
import os
import subprocess
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel, Field
from datetime import datetime

from .base import BaseTool, ToolResult


class TestResultUpdaterTool(BaseTool):
    """测试结果更新工具 - 运行测试并更新文档"""

    name = "test_result_updater"
    description = "编译运行测试，将测试结果更新到测试文档中"

    class Parameters(BaseModel):
        test_file: str = Field(description="测试源文件路径")
        doc_file: str = Field(description="要更新的测试文档路径")
        source_dir: Optional[str] = Field(default=None, description="源代码目录（用于查找头文件）")
        build_dir: Optional[str] = Field(default=None, description="构建目录，默认在 test_file 父目录下的 build")
        output_binary: Optional[str] = Field(default=None, description="输出可执行文件路径")
        compiler: Optional[str] = Field(default=None, description="编译器：msvc/g++，自动检测")
        extra_compile_flags: str = Field(default="", description="额外编译标志")
        run_timeout: int = Field(default=60, description="运行超时时间（秒）")

    def _execute(self, params: Parameters) -> ToolResult:
        test_path = Path(params.test_file)
        doc_path = Path(params.doc_file)

        if not test_path.exists():
            return ToolResult.error(f"测试文件不存在: {params.test_file}")

        # 1. 设置路径配置
        source_dir = Path(params.source_dir) if params.source_dir else test_path.parent.parent
        build_dir = Path(params.build_dir) if params.build_dir else source_dir / "build"
        build_dir.mkdir(parents=True, exist_ok=True)

        # 2. 编译测试程序
        compile_success, compile_output, exe_path = self._compile_test(
            test_path, source_dir, build_dir, params
        )

        if not compile_success:
            return ToolResult.error(
                f"测试编译失败: {compile_output[:500]}",
                compile_success=False,
                compile_output=compile_output
            )

        # 3. 运行测试，捕获结果
        run_success, test_output, test_results = self._run_and_parse_test(exe_path, params.run_timeout)

        # 4. 更新测试文档
        update_success = self._update_test_document(doc_path, test_results, compile_output, test_output)

        return ToolResult.ok(
            self._format_report(test_results, compile_success, run_success, str(doc_path)),
            test_results=test_results,
            compile_success=compile_success,
            run_success=run_success,
            doc_updated=update_success,
            updated_doc=str(doc_path),
            test_output=test_output
        )

    def _compile_test(self, test_path: Path, source_dir: Path, build_dir: Path,
                      params: Parameters) -> Tuple[bool, str, Optional[str]]:
        """编译测试程序"""

        # 检测编译器
        compiler = params.compiler or self._detect_compiler()
        if not compiler:
            return self._compile_with_msvc(test_path, source_dir, build_dir, params)
        else:
            return False, "未找到可用的编译器（MSVC 或 MinGW g++）", None

    def _detect_compiler(self) -> Optional[str]:
        """检测可用编译器"""
        # 检测 MSVC
        try:
            result = subprocess.run(
                ["cl"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if "Microsoft" in result.stderr or "Microsoft" in result.stdout:
                return "msvc"
        except:
            pass

        # 检测 g++
        try:
            result = subprocess.run(
                ["g++", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return "g++"
        except:
            pass

        return None

    def _compile_with_msvc(self, test_path: Path, source_dir: Path, build_dir: Path,
                           params: Parameters) -> Tuple[bool, str, Optional[str]]:
        """使用 MSVC 编译测试"""
        include_dirs = [
            source_dir / "include",
            source_dir / "tests",
            source_dir
        ]

        exe_name = f"{test_path.stem}.exe"
        exe_path = build_dir / exe_name

        compile_cmd = [
            "cl", "/EHsc", "/std:c++17", "/nologo"
        ]

        for inc in include_dirs:
            if inc.exists():
                compile_cmd.append(f"/I{inc}")

        if params.extra_compile_flags:
            compile_cmd.extend(params.extra_compile_flags.split())

        compile_cmd.extend([
            str(test_path.absolute()),
            f"/Fe:{exe_path}"
        ])

        try:
            result = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(build_dir)
            )

            output = result.stdout + "\n" + result.stderr

            if exe_path.exists():
                return True, output, str(exe_path)
            else:
                return False, output, None

        except subprocess.TimeoutExpired:
            return False, "编译超时", None
        except Exception as e:
            return False, f"编译异常: {str(e)}", None

    def _run_and_parse_test(self, exe_path: str, timeout: int) -> Tuple[bool, str, Dict[str, Any]]:
        """运行测试并解析结果"""
        try:
            result = subprocess.run(
                [exe_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=Path(exe_path).parent
            )

            output = result.stdout + "\n" + result.stderr

            # 解析测试结果
            test_results = self._parse_test_output(output)

            success = result.returncode in [0, 1] or test_results.get("total", 0) > 0

            return success, output, test_results

        except subprocess.TimeoutExpired:
            return False, "测试运行超时", {}
        except Exception as e:
            return False, f"运行异常: {str(e)}", {}

    def _parse_test_output(self, output: str) -> Dict[str, Any]:
        """解析测试输出"""
        lines = output.replace("\r", "").split("\n")

        results = {
            "passed": 0,
            "failed": 0,
            "total": 0,
            "tests": [],
            "passed_names": [],
            "failed_names": [],
            "raw_output": lines[:100]
        }

        current_test = None

        for line in lines:
            line_stripped = line.strip()

            # 解析 [PASS] xxx 格式
            if "[PASS]" in line or "PASS:" in line or "✓" in line or "✅" in line:
                results["passed"] += 1
                results["total"] += 1
                test_name = self._extract_test_name(line)
                results["passed_names"].append(test_name)
                results["tests"].append({"name": test_name, "status": "PASS"})

            elif "[FAIL]" in line or "FAIL:" in line or "❌" in line or "Assertion failed" in line.lower():
                results["failed"] += 1
                results["total"] += 1
                test_name = self._extract_test_name(line)
                results["failed_names"].append(test_name)
                results["tests"].append({"name": test_name, "status": "FAIL"})

            # 解析 Summary 格式
            elif "tests" in line.lower() and ("passed" in line.lower() or "total" in line.lower()):
                # 如: "14 tests total, 14 passed"
                m = re.search(r'(\d+)\s+tests?\s*(?:total)?\s*(\d+)\s*passed", line, re.IGNORECASE)
                if m:
                    results["total"] = int(m.group(1))
                    results["passed"] = int(m.group(2))
                    results["failed"] = results["total"] - results["passed"]

        # 计算通过率
        if results["total"] > 0:
            results["pass_rate"] = f"{(results['passed'] / results['total'] * 100):.1f}%"
        else:
            results["pass_rate"] = "N/A"

        # 整体状态
        results["status"] = "PASS" if results["failed"] == 0 and results["total"] > 0 else "FAIL"

        return results

    def _extract_test_name(self, line: str) -> str:
        """从行中提取测试名称"""
        line = line.strip()
        # 移除标记
        for marker in ["[PASS]", "[FAIL]", "PASS:", "FAIL:", "✅", "❌", "✓"]:
            line = line.replace(marker, "")
        return line.strip() or "Unknown Test"

    def _update_test_document(self, doc_path: Path, test_results: Dict,
                              compile_output: str, test_output: str) -> bool:
        """更新测试文档"""
        if not doc_path.exists():
            return False

        try:
            content = doc_path.read_text(encoding='utf-8')

            # 生成测试结果章节
            result_section = self._generate_result_section(test_results, test_output)

            # 检查是否已有测试结果部分
            if "## 测试执行结果" in content or "## 测试结果" in content:
                # 替换已有部分
                content = re.sub(
                    r'##\s+(测试执行结果|测试结果)[\s\S]*?(?=\n##\s|\Z)',
                    result_section,
                    content
                )
            else:
                # 在文档开头（标题后插入测试结果部分
                lines = content.split('\n', 2)
                if len(lines) >= 3:
                    content = lines[0] + '\n' + lines[1] + '\n' + result_section + '\n' + lines[2]
                else:
                    content = result_section + '\n' + content

            doc_path.write_text(content, encoding='utf-8')
            return True

        except Exception as e:
            print(f"更新文档失败: {str(e)}")
            return False

    def _generate_result_section(self, test_results: Dict, test_output: str) -> str:
        """生成测试结果章节"""
        from datetime import datetime

        section = f"""
## 测试执行结果

> **测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')
> **执行状态**: {'✅ 全部通过' if test_results.get('failed', 0) == 0 and test_results.get('total', 0) > 0 else '⚠️ 部分通过' if test_results.get('passed', 0) > 0 else '❌ 测试失败'}

### 结果统计

| 统计项 | 数值 |
|--------|------|
| 总测试数 | {test_results.get('total', 0)} 个 |
| **通过数** | **{test_results.get('passed', 0)} 个** |
| 失败数 | {test_results.get('failed', 0)} 个 |
| **通过率** | **{test_results.get('pass_rate', 'N/A')}** |

"""

        # 详细测试结果
        if test_results.get('tests'):
            section += "### 详细测试结果\n\n"
            section += "| 测试名称 | 结果 |\n"
            section += "|----------|------|\n"
            for test in test_results['tests']:
                icon = "✅ PASS" if test['status'] == 'PASS' else "❌ FAIL"
                section += f"| {test['name']} | {icon} |\n"
            section += "\n"

        # 失败的测试（如果有）
        if test_results.get('failed_names'):
            section += "### 失败的测试\n\n"
            for name in test_results['failed_names'][:10:
                section += f"- ❌ {name}\n"
            section += "\n"

        # 测试输出日志
        output_lines = [l.strip() for l in test_output.split('\n') if l.strip()][:30]
        if output_lines:
            section += "### 测试输出日志\n\n"
            section += "```\n"
            section += '\n'.join(output_lines[:30])
            section += "\n```\n\n"

        return section

    def _format_report(self, test_results: Dict, compile_success: bool,
                       run_success: bool, doc_path: str) -> str:
        """格式化结果报告"""
        lines = [
            "=" * 60,
            "🧪 测试结果更新完成",
            "=" * 60,
            "",
            f"📊 编译状态: {'✅ 成功' if compile_success else '❌ 失败'}",
            f"🏃 运行状态: {'✅ 完成' if run_success else '❌ 异常'}",
            "",
            "📈 测试统计:",
            f"  - 总测试数: {test_results.get('total', 0)}",
            f"  - 通过: {test_results.get('passed', 0)} ✅",
            f"  - 失败: {test_results.get('failed', 0)} ❌",
            f"  - 通过率: {test_results.get('pass_rate', 'N/A')}",
            "",
            f"📄 测试文档已更新: {doc_path}",
            "=" * 60
        ]

        return '\n'.join(lines)
