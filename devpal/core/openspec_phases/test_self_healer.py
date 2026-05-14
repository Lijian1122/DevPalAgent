# -*- coding: utf-8 -*-
"""Test Self-Healer: AI-powered test failure auto-fix"""

from pathlib import Path
from typing import Dict, List, Optional
from ..llm_client import LLMClient
import re

class TestSelfHealer:
    """测试自愈器：自动修复编译错误和测试失败"""

    def __init__(self, project_dir: Path, llm_client: LLMClient, logger=None):
        self.project_dir = project_dir
        self.llm_client = llm_client
        self.logger = logger or print
        self.heal_attempts = 0
        self.heal_success = 0

    def log(self, message: str):
        if self.logger:
            self.logger(message)

    def heal_compile_error(self, test_file: Path, error_output: str) -> bool:
        self.heal_attempts += 1
        self.log(f"  [HEAL] Attempting to fix compile error in {test_file.name} (attempt #{self.heal_attempts})")
        try:
            test_code = test_file.read_text(encoding='utf-8')
            source_files = self._find_related_source_files(test_file)
            source_code_context = ""
            for src_file in source_files:
                if src_file.exists():
                    source_code_context += f"\n// File: {src_file.name}\n"
                    source_code_context += src_file.read_text(encoding='utf-8')
            prompt = self._build_compile_error_fix_prompt(test_file.name, test_code, source_code_context, error_output)
            self.log(f"  [HEAL] Calling AI to analyze and fix...")
            response = self.llm_client.generate(
              system="You are a C++ expert helping fix code issues.",
              user_message=prompt
            )
            fixed_code = self._extract_code_from_response(response)
            if not fixed_code:
                self.log(f"  [HEAL] Failed: AI did not return valid code")
                return False
                        # Additional validation before writing
            if len(fixed_code) < 50:
                self.log(f"  [HEAL] Failed: Fixed code too short ({len(fixed_code)} chars)")
                return False
            
            if '```' in fixed_code or '**' in fixed_code:
                self.log(f"  [HEAL] Failed: Fixed code contains markdown syntax")
                return False

            test_file.write_text(fixed_code, encoding='utf-8')
            self.log(f"  [HEAL] Fixed code written to {test_file.name}")
            self.heal_success += 1
            return True
        except Exception as e:
            self.log(f"  [HEAL] Exception during healing: {e}")
            return False

    def heal_test_failure(self, test_file: Path, test_output: str, passed: int, total: int) -> bool:
        self.heal_attempts += 1
        self.log(f"  [HEAL] Attempting to fix test failures in {test_file.name} ({passed}/{total} passed, attempt #{self.heal_attempts})")
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
            self.log(f"  [HEAL] Calling AI to analyze test failures...")
            response = self.llm_client.generate(
              system="You are a C++ expert helping fix code issues.",
              user_message=prompt
            )
            fixed_impl = self._extract_code_from_response(response, marker="// IMPLEMENTATION")
            fixed_header = self._extract_code_from_response(response, marker="// HEADER")
            success = False
            if fixed_impl and impl_file:
                # Validate before writing
                if len(fixed_impl) < 50 or '```' in fixed_impl or '**' in fixed_impl:
                    self.log(f"  [HEAL] Failed: Invalid implementation code")
                else:
                    impl_file.write_text(fixed_impl, encoding='utf-8')
                    self.log(f"  [HEAL] Fixed implementation written to {impl_file.name}")
                    success = True
            if fixed_header and header_file:
                header_file.write_text(fixed_header, encoding='utf-8')
                self.log(f"  [HEAL] Fixed header written to {header_file.name}")
                success = True
            if success:
                self.heal_success += 1
                return True
            else:
                self.log(f"  [HEAL] Failed: AI did not return valid fixes")
                return False
        except Exception as e:
            self.log(f"  [HEAL] Exception during healing: {e}")
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
        parts.append("```cpp")
        parts.append("// Fixed test code here")
        parts.append("```")
        parts.append("")
        parts.append("**CRITICAL RULES**:")
        parts.append("1. Return ONLY the fixed C++ code inside ```cpp code blocks")
        parts.append("2. Do NOT include any explanations, comments, or markdown text")
        parts.append("3. Do NOT write 'This should be...' or 'The main issue...'")
        parts.append("4. Return compilable C++ code ONLY")

        return "\n".join(parts)

    def _build_test_failure_fix_prompt(self, test_filename: str, test_code: str, impl_code: str, header_code: str, test_output: str, passed: int, total: int) -> str:
        parts = []
        parts.append("You are a C++ expert. Some tests are failing. Please fix the implementation to make tests pass.")
        parts.append("")
        parts.append("**Test File**: " + test_filename)
        parts.append("**Test Results**: " + str(passed) + "/" + str(total) + " tests passed")
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
        parts.append(test_output)
        parts.append("```")
        parts.append("")
        parts.append("**Task**:")
        parts.append("1. Analyze why tests are failing")
        parts.append("2. Fix the implementation (NOT the tests) to make them pass")
        parts.append("3. Return the fixed implementation and/or header files")
        parts.append("")
        parts.append("**Output Format**:")
        parts.append("If you need to fix the header:")
        parts.append("```cpp")
        parts.append("// HEADER")
        parts.append("// Fixed header code here")
        parts.append("```")
        parts.append("")
        parts.append("If you need to fix the implementation:")
        parts.append("```cpp")
        parts.append("// IMPLEMENTATION")
        parts.append("// Fixed implementation code here")
        parts.append("```")
        parts.append("")
        parts.append("Return only the files that need changes. No explanations.")
        parts.append("")
        parts.append("**CRITICAL RULES**:")
        parts.append("1. Return ONLY the fixed C++ code inside ```cpp code blocks")
        parts.append("2. Do NOT include any explanations, comments, or markdown text")
        parts.append("3. Do NOT write 'This should be...' or 'The main issue...'")
        parts.append("4. Return compilable C++ code ONLY")

        return "\n".join(parts)

    def _extract_code_from_response(self, response: str, marker: Optional[str] = None) -> Optional[str]:
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
                lines = [line for line in code.split('\n')
                         if not line.strip().startswith('// Fixed')
                         and not line.strip().startswith('// HEADER')
                         and not line.strip().startswith('// IMPLEMENTATION')]
                extracted = '\n'.join(lines)
                
                # Validate extracted code
                if not self._is_valid_cpp_code(extracted):
                    self.log(f"  [HEAL] Warning: Extracted code contains invalid C++ syntax")
                    return None
                
                return extracted
        return None

    def _is_valid_cpp_code(self, code: str) -> bool:
        """Validate if code looks like valid C++ code"""
        if not code or len(code.strip()) < 10:
            return False
        
        # Check for markdown markers
        markdown_markers = ['```', '**', '##', '- [', 'This should be', 'The main issue', 'Looking at']
        for marker in markdown_markers:
            if marker in code:
                self.log(f"  [HEAL] Detected markdown marker: {marker}")
                return False
        
        # Check for basic C++ syntax elements
        cpp_indicators = ['#include', 'namespace', 'class', 'void', 'int', 'return', '{', '}']
        has_cpp_syntax = any(indicator in code for indicator in cpp_indicators)
        
        if not has_cpp_syntax:
            self.log(f"  [HEAL] No C++ syntax indicators found")
            return False
                # New: For test files, must contain main function
        if 'test_' in code.lower() or 'TEST' in code:
            if 'int main(' not in code and 'int main (' not in code:
                self.log(f"  [HEAL] Test file missing main() function")
                return False
        
        # New: Check minimum line count (test files should have at least 30 lines)
        line_count = len(code.split('\n'))
        if line_count < 30:
            self.log(f"  [HEAL] Code too short: {line_count} lines (expected at least 30)")
            return False
        
        return True


    def get_stats(self) -> Dict[str, int]:
        return {
            'attempts': self.heal_attempts,
            'success': self.heal_success,
            'failed': self.heal_attempts - self.heal_success
        }