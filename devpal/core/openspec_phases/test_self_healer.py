# -*- coding: utf-8 -*-
"""
Test Self-Healer: AI-powered test failure auto-fix
"""

from pathlib import Path
from typing import Dict, List, Optional
from ..llm_client import LLMClient
import re
import os  # 导入 os 模块以处理文件路径


class TestSelfHealer:
    """测试自愈器：自动修复编译错误和测试失败"""

    def __init__(self, project_dir: Path, llm_client: LLMClient, logger=None, fallback_model: str = "claude-opus-4-7"):
        self.project_dir = project_dir
        self.llm_client = llm_client
        self.fallback_model = fallback_model  # 备用模型
        self.logger = logger or print
        self.heal_attempts = 0
        self.heal_success = 0
        self.model_switches = 0  # 模型切换次数
        self.model_switched = False  # 模型切换状态标志

    def log(self, message: str):
        if self.logger:
            self.logger(message)

    def _detect_dependency_error(self, error_output: str) -> Optional[str]:
        """检测是否是依赖缺失错误"""
        dependency_patterns = [
            (r"cannot open include file:\s*['\"](.+?)['\"]", "Missing header"),
            (r"无法打开包括文件:\s*['\"](.+?)['\"]", "Missing header"),
            (r"No such file or directory.*?['\"](.+?)['\"]", "Missing file"),
            (r"undefined reference to [`'](.+?)'", "Missing library"),
            (r"未定义的引用.*?[`'](.+?)'", "Missing library"),
        ]

        for pattern, error_type in dependency_patterns:
            match = re.search(pattern, error_output, re.IGNORECASE)
            if match:
                missing = match.group(1)
                return f"{error_type}: {missing}"

        return None

    def heal_compile_error(self, test_file: Path, error_output: str, use_fallback: bool = False) -> bool:
        self.heal_attempts += 1
        model_label = f" (using {self.fallback_model})" if use_fallback else ""
        self.log(f"  [HEAL] Attempting to fix compile error in {test_file.name} (attempt #{self.heal_attempts}){model_label}")

        # 先检测是否是依赖问题
        dependency_issue = self._detect_dependency_error(error_output)
        if dependency_issue:
            self.log(f" [HEAL] Detected dependency issue: {dependency_issue}")
            self.log(f" [HEAL] Cannot fix dependency issues through code modification")
            return False

        try:
            test_code = test_file.read_text(encoding='utf-8')
            source_files = self._find_related_source_files(test_file)
            source_code_context = ""
            for src_file in source_files:
                if src_file.exists():
                    source_code_context += f"\n// File: {src_file.name}\n"
                    source_code_context += src_file.read_text(encoding='utf-8')

            prompt = self._build_compile_error_fix_prompt(test_file.name, test_code, source_code_context, error_output)
            self.log(f" [HEAL] Calling AI to analyze and fix...")

            # Select model
            if use_fallback and not self.model_switched:
                client = LLMClient(model=self.fallback_model)
                self.model_switched = True
                self.model_switches += 1
                self.log(f" [HEAL] Switched to fallback model: {self.fallback_model}")
            elif use_fallback:
                client = LLMClient(model=self.fallback_model)
            else:
                client = self.llm_client

            # Generate fix
            response = client.generate(
                system="You are a C++ expert helping fix code issues.",
                user_message=prompt)
            fixed_code = self._extract_code_from_response(response)
        
            # 验证返回的代码
            if not fixed_code:
                self.log(f" [HEAL] Failed: AI did not return valid code")
                return False

            # Additional validation before writing
            if len(fixed_code) < 50:
                self.log(f" [HEAL] Failed: Fixed code too short ({len(fixed_code)} chars)")
                return False

            if '```' in fixed_code or '**' in fixed_code:
                self.log(f" [HEAL] Failed: Fixed code contains markdown syntax")
                return False

            test_file.write_text(fixed_code, encoding='utf-8')
            self.log(f" [HEAL] Fixed code written to {test_file.name}")
            self.heal_success += 1
            return True

        except Exception as e:
            self.log(f" [HEAL] Exception during healing: {e}")
            return False

    def heal_test_failure(self, test_file: Path, test_output: str, passed: int, total: int, use_fallback: bool = False) -> bool:
            self.heal_attempts += 1
            model_label = f" (using {self.fallback_model})" if use_fallback else ""
            self.log(f" [HEAL] Attempting to fix test failures in {test_file.name} ({passed}/{total} passed, attempt #{self.heal_attempts}){model_label}")
            try:
                test_code = test_file.read_text(encoding='utf-8')
                source_files = self._find_related_source_files(test_file)
                impl_code = ""
                header_code = ""
                impl_file = None
                header_file = None

                for src_file in source_files:
                    if src_file.exists():
                        if src_file.suffix == '.cpp':
                            impl_code = src_file.read_text(encoding='utf-8')
                            impl_file = src_file
                        elif src_file.suffix == '.h':
                            header_code = src_file.read_text(encoding='utf-8')
                            header_file = src_file

                prompt = self._build_test_failure_fix_prompt(test_file.name, test_code, impl_code, header_code, test_output, passed, total)
                self.log(f" [HEAL] Calling AI to analyze test failures...")

                if use_fallback and not self.model_switched:
                    client = LLMClient(model=self.fallback_model)
                    self.model_switched = True
                    self.model_switches += 1
                    self.log(f" [HEAL] Switched to fallback model: {self.fallback_model}")
                elif use_fallback:
                    client = LLMClient(model=self.fallback_model)
                else:
                    client = self.llm_client
                    response = client.generate(
                    system="You are a C++ expert helping fix code issues.",
                    user_message=prompt
                )
                fixed_impl = self._extract_code_from_response(response, marker="// IMPLEMENTATION")
                fixed_header = self._extract_code_from_response(response, marker="// HEADER")

                success = False
                if fixed_impl and impl_file:
                    # Validate before writing
                    if len(fixed_impl) < 50 or '```' in fixed_impl or '**' in fixed_impl:
                        self.log(f" [HEAL] Failed: Invalid implementation code")
                    else:
                        impl_file.write_text(fixed_impl, encoding='utf-8')
                        self.log(f" [HEAL] Fixed implementation written to {impl_file.name}")
                        success = True

                if fixed_header and header_file:
                    header_file.write_text(fixed_header, encoding='utf-8')
                    self.log(f" [HEAL] Fixed header written to {header_file.name}")
                    success = True

                if success:
                    self.heal_success += 1
                    return True
                else:
                    self.log(f" [HEAL] Failed: AI did not return valid fixes")
                    return False

            except Exception as e:
                self.log(f" [HEAL] Exception during healing: {e}")
                return False

    def _find_related_source_files(self, test_file: Path) -> List[Path]:
            base_name = test_file.stem.replace('test_', '')
            src_dir = self.project_dir / "src"
            include_dir = self.project_dir / "include"
            related_files = []

            cpp_file = src_dir / f"{base_name}.cpp"
            if cpp_file.exists():
                related_files.append(cpp_file)

            h_file = include_dir / f"{base_name}.h"
            if h_file.exists():
                related_files.append(h_file)

            return related_files

    def _build_compile_error_fix_prompt(self, test_filename: str, test_code: str, source_context: str, error_output: str) -> str:
            parts = []
            parts.append("You are a C++ expert. A test file has compilation errors. Please fix the test code.")
            parts.append("")
            parts.append("**Test File**: " + test_filename)
            parts.append("")
            parts.append("**Test Code**:")
            parts.append("```cpp")
            parts.append(test_code)
            parts.append("```")
            parts.append("")
            parts.append("**Related Source Files**:")
            parts.append("```cpp")
            parts.append(source_context)
            parts.append("```")
            parts.append("")
            parts.append("**Compilation Error**:")
            parts.append("```")
            parts.append(error_output)
            parts.append("```")
            parts.append("")
            parts.append("**Task**:")
            parts.append("1. Analyze the compilation error")
            parts.append("2. Fix the test code to make it compile successfully")
            parts.append("3. Return ONLY the complete fixed test code, no explanations")
            parts.append("")
            parts.append("**Output Format**:")
            parts.append("Return the complete fixed C++ test file as plain text code only.")
            parts.append("")
            parts.append("**CRITICAL RULES**:")
            parts.append("1. Return ONLY the complete fixed C++ code, starting with #include.")
            parts.append("2. Do NOT wrap the answer in markdown fences.")
            parts.append("3. Do NOT include explanations, analysis, or prose.")
            parts.append("4. Preserve the test_base.h API: ASSERT_TRUE, ASSERT_EQ, RUN_TEST, TEST_MAIN_BEGIN, TEST_MAIN_END.")
            parts.append("5. Return compilable C++ code ONLY.")
            return "\n".join(parts)

    def _build_test_failure_fix_prompt(self, test_filename: str, test_code: str, impl_code: str, header_code: str, test_output: str, passed: int, total: int) -> str:
            parts = []
            parts.append("You are a C++ expert. Tests are failing and you need to fix them.")
            parts.append("")

            # STEP 1: Mandatory Analysis (方案 3)
            parts.append("**STEP 1: MANDATORY ANALYSIS**")
            parts.append("Before fixing, you MUST answer these questions:")
            parts.append("")
            parts.append("1. **Root Cause**: Why is this specific test failing? (Be specific)")
            parts.append("2. **Test Data Validity**: Is the test data valid according to business rules?")
            parts.append("   - Check: username length (3-20), password length (8-32), password complexity")
            parts.append("3. **Implementation Correctness**: Does the implementation match requirements?")
            parts.append("   - Requirements: username 3-20 chars, password 8-32 chars with letters+digits")
            parts.append("4. **Fix Decision**: Should we fix test code or implementation? Why?")
            parts.append("")

            # STEP 2: Modification Rules (方案 2)
            parts.append("**STEP 2: MODIFICATION RULES**")
            parts.append("Follow these rules when deciding what to fix:")
            parts.append("")
            parts.append("ALLOWED:")
            parts.append("- Fix test data to match requirements (e.g., change 'pass123' to 'pass1234')")
            parts.append("- Fix implementation bugs (e.g., off-by-one errors, wrong operators)")
            parts.append("- Fix logic errors (e.g., incorrect hash comparison)")
            parts.append("- Fix infrastructure issues (e.g., create missing directories)")
            parts.append("")
            parts.append("FORBIDDEN:")
            parts.append("- Relax validation rules (e.g., reduce minimum length from 8 to 7)")
            parts.append("- Weaken security constraints (e.g., remove password complexity requirements)")
            parts.append("- Change business logic to make tests pass (e.g., skip password verification)")
            parts.append("- Replace header files with implementation code")
            parts.append("")
            parts.append("**DECISION TREE**:")
            parts.append("- Test data violates requirements → Fix test data")
            parts.append("- Implementation violates requirements → Fix implementation")
            parts.append("- Both are correct but test fails → Check for logic bugs")
            parts.append("- Infrastructure issue (missing directory/file) → Fix in implementation")
            parts.append("")
            parts.append("**INFRASTRUCTURE FIX GUIDE**:")
            parts.append("If the error is about missing directories or files:")
            parts.append("1. Add #include <filesystem> to the implementation file")
            parts.append("2. Before opening files for writing, create parent directories:")
            parts.append("   ```cpp")
            parts.append("   std::filesystem::path filePath(dbFilePath_);")
            parts.append("   std::filesystem::path parentDir = filePath.parent_path();")
            parts.append("   if (!parentDir.empty() && !std::filesystem::exists(parentDir)) {")
            parts.append("       std::error_code ec;")
            parts.append("       std::filesystem::create_directories(parentDir, ec);")
            parts.append("       if (ec) { /* handle error */ }")
            parts.append("   }")
            parts.append("   ```")
            parts.append("3. Do NOT modify test code to avoid using subdirectories")
            parts.append("")

            # Context Information
            parts.append("**Test File**: " + test_filename)
            parts.append("**Test Results**: " + str(passed) + "/" + str(total) + " tests passed")
            if passed == 0 and total == 0:
                parts.append("**WARNING**: 0/0 means no test output - likely crash or compilation issue")
            parts.append("")
            parts.append("**Test Code**:")
            parts.append("```cpp")
            parts.append(test_code)
            parts.append("```")
            parts.append("")
            parts.append("**Header File**:")
            parts.append("```cpp")
            parts.append(header_code)
            parts.append("```")
            parts.append("")
            parts.append("**Implementation File**:")
            parts.append("```cpp")
            parts.append(impl_code)
            parts.append("```")
            parts.append("")
            parts.append("**Test Output**:")
            parts.append("```")
            parts.append(test_output if test_output.strip() else "(empty - no output produced)")
            parts.append("```")
            parts.append("")

            # Output Format
            parts.append("**OUTPUT FORMAT**:")
            parts.append("")
            parts.append("First, provide your analysis (MANDATORY):")
            parts.append("```")
            parts.append("ANALYSIS:")
            parts.append("1. Root Cause: [explain why test fails]")
            parts.append("2. Test Data Validity: [valid/invalid and why]")
            parts.append("3. Implementation Correctness: [correct/incorrect and why]")
            parts.append("4. Fix Decision: [fix test/fix implementation and why]")
            parts.append("```")
            parts.append("")
            parts.append("Then provide the fixed code:")
            parts.append("```cpp")
            parts.append("// HEADER")
            parts.append("#ifndef HEADER_NAME_H")
            parts.append("... complete fixed header code ...")
            parts.append("```")
            parts.append("")
            parts.append("```cpp")
            parts.append("// IMPLEMENTATION")
            parts.append("#include \"header.h\"")
            parts.append("... complete fixed implementation code ...")
            parts.append("```")
            parts.append("")
            parts.append("**CRITICAL RULES**:")
            parts.append("1. You MUST provide the ANALYSIS section first")
            parts.append("2. Return ONLY C++ code inside ```cpp blocks with // HEADER or // IMPLEMENTATION markers")
            parts.append("3. Each code block must be complete and compilable")
            parts.append("4. Do NOT relax validation rules unless you can justify it violates requirements")
            return "\n".join(parts)

    def _extract_code_from_response(self, response: str, marker: Optional[str] = None) -> Optional[str]:
            # Extract and log analysis section if present
            analysis_match = re.search(r'ANALYSIS:\s*\n(.*?)(?=```|$)', response, re.DOTALL)
            if analysis_match:
                analysis = analysis_match.group(1).strip()
                self.log(f" [HEAL] AI Analysis:")
                for line in analysis.split('\n')[:4]:  # Log first 4 lines
                    if line.strip():
                        self.log(f"        {line.strip()}")

                # Check for suspicious modifications
                analysis_lower = analysis.lower()
                suspicious_keywords = ['relax', 'reduce', 'weaken', 'less strict', 'minimum to', 'from 8 to 7', 'from 8 to']
                for keyword in suspicious_keywords:
                    if keyword in analysis_lower:
                        self.log(f" [HEAL] ⚠️  WARNING: Detected potential validation rule relaxation: '{keyword}'")

            if marker:
                marker_pos = response.find(marker)
                if marker_pos == -1:
                    return None
                response = response[marker_pos + len(marker):]

            patterns = [
                r'```cpp\s*\n(.*?)\n```',
                r'```c\+\+\s*\n(.*?)\n```',
                r'```\s*\n(.*?)\n```',
            ]

            for pattern in patterns:
                match = re.search(pattern, response, re.DOTALL)
                if match:
                    code = match.group(1).strip()
                    lines = [
                        line for line in code.split('\n')
                        if not line.strip().startswith('// Fixed')
                        and not line.strip().startswith('// HEADER')
                        and not line.strip().startswith('// IMPLEMENTATION')
                    ]
                    extracted = '\n'.join(lines)
                    if not self._is_valid_cpp_code(extracted):
                        self.log(f" [HEAL] Warning: Extracted code contains invalid C++ syntax")
                        return None
                    return extracted

            stripped = response.strip()
            if stripped.startswith("#include") and self._is_valid_cpp_code(stripped):
                return stripped

            return None

    def _is_valid_cpp_code(self, code: str) -> bool:
            """Validate if code looks like valid C++ code"""
            if not code or len(code.strip()) < 10:
                return False

            # Check for markdown markers
            markdown_markers = ['```', '**', '##', '- [', 'This should be', 'The main issue', 'Looking at']
            for marker in markdown_markers:
                if marker in code:
                    self.log(f" [HEAL] Detected markdown marker: {marker}")
                    return False

            # Check for basic C++ syntax elements
            cpp_indicators = ['#include', 'namespace', 'class', 'struct', 'void', 'int', 'return', '{', '}', 'public:', 'private:', 'const', 'std::']
            has_cpp_syntax = any(indicator in code for indicator in cpp_indicators)
            if not has_cpp_syntax:
                self.log(f" [HEAL] No C++ syntax indicators found")
                return False

            # --- 修复开始 ---

            # 1. 获取当前正在处理的文件名（假设 TestSelfHealer 实例化时知道当前文件，或者从外部传入）
            # 这里我们假设有一个方式获取当前文件名，例如通过实例变量 self.current_file
            # 如果没有，可以考虑将此逻辑移至调用处，或者通过参数传入
            current_file_name = getattr(self, 'current_file', None)
            if current_file_name is None:
                # 如果无法获取文件名，则回退到基于内容的检查
                # 但基于内容的检查容易误判，因此最好传入文件名
                pass
            else:
                # 2. 判断是否为测试文件（基于文件名）
                is_test_file = 'test_' in current_file_name.lower() or 'TEST' in current_file_name
                if is_test_file:
                    # 3. 统计行数（使用 splitlines() 更准确）
                    line_count = len(code.splitlines())
                    # 4. 只有当代码较长（>= 100行）时才强制要求 main 函数
                    if line_count >= 100:
                        if 'int main(' not in code and 'int main (' not in code:
                            self.log(f" [HEAL] Test file missing main() function")
                            return False
                    # 如果代码较短，则跳过 main 检查
                    return True

            # --- 修复结束 ---

            # 如果不是测试文件，或者其他情况，返回 True（或者根据需要添加其他规则）
            return True

    def get_stats(self) -> Dict[str, int]:
            return {
                'attempts': self.heal_attempts,
                'success': self.heal_success,
                'failed': self.heal_attempts - self.heal_success
            }
