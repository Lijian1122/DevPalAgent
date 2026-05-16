# -*- coding: utf-8 -*-
"""Phase 9: Quality Gate - 硬性质量检查"""

from pathlib import Path
from typing import List, Tuple
import re

from .base import PhaseInterface, PhaseResult, OpenSpecContext


class Phase9QualityGate(PhaseInterface):
    """Phase 9: 质量门禁 - 硬性检查，失败则终止流程"""

    def __init__(self, context: OpenSpecContext, tool_registry):
        super().__init__(context)
        self.phase_number = 9
        self.phase_name = "Quality Gate"
        self.tool_registry = tool_registry
        self.is_critical = True

    def execute(self) -> PhaseResult:
        self.log("Phase 9: Quality Gate - running mandatory checks...")
        
        violations = []
        warnings = []
        
        # 检查 1: CMakeLists.txt
        if not self._check_cmake_exists():
            violations.append("CMakeLists.txt not found")
        else:
            self.log("  [OK] CMakeLists.txt exists")
        
        # 检查 2: src/main.cpp
        main_check = self._check_main_cpp()
        if main_check:
            violations.append(main_check)
        else:
            self.log("  [OK] src/main.cpp exists with main()")
        
        # 检查 3: test_base.h
        test_base_check = self._check_test_base()
        if test_base_check:
            violations.append(test_base_check)
        else:
            self.log("  [OK] test_base.h API is consistent")
        
        # 检查 4: 测试数量
        if self.context.test_total == 0:
            violations.append("No tests found (test_total=0)")
        else:
            self.log("  [OK] Tests present (total={})".format(self.context.test_total))
        
        # 生成报告
        report_path = self._write_report(violations, warnings)
        
        if violations:
            self.log("  [FAIL] Quality Gate: {} violations".format(len(violations)))
            for v in violations:
                self.log("    - {}".format(v))
            return PhaseResult.fail(
                "Quality Gate failed: {} violations".format(len(violations)),
                errors=violations
            )
        
        self.log("  [OK] Quality Gate passed")
        return PhaseResult.ok(
            "Quality Gate passed",
            violations=0,
            warnings=len(warnings),
            report_path=str(report_path)
        )
    
    def _check_cmake_exists(self) -> bool:
        return (self.context.project_dir / "CMakeLists.txt").exists()
    
    def _check_main_cpp(self) -> str:
        main_path = self.context.project_dir / "src" / "main.cpp"
        if not main_path.exists():
            return "src/main.cpp not found"
        try:
            content = main_path.read_text(encoding='utf-8')
            if 'int main(' not in content:
                return "src/main.cpp has no main() function"
        except Exception as e:
            return "Cannot read src/main.cpp: {}".format(e)
        return ""
    
    def _check_test_base(self) -> str:
        test_base = self.context.project_dir / "tests" / "test_base.h"
        if not test_base.exists():
            return "tests/test_base.h not found"
        try:
            content = test_base.read_text(encoding='utf-8')
            required = [
                'ASSERT_TRUE', 
                'ASSERT_EQ', 
                'RUN_TEST', 
                'TEST_MAIN_BEGIN', 
                'TEST_MAIN_END'
            ]
            missing = [
                m for m in required 
                if '#define {}'.format(m) not in content
            ]
            if missing:
                return "test_base.h missing macros: {}".format(', '.join(missing))
        except Exception as e:
            return "Cannot read test_base.h: {}".format(e)
        return ""
    
    def _write_report(self, violations: List[str], warnings: List[str]) -> Path:
        lines = [
            "# Quality Gate Report",
            "",
            "**Status**: {}".format('FAILED' if violations else 'PASSED'),
            "",
            "## Summary",
            "",
            "- Violations: {}".format(len(violations)),
            "- Warnings: {}".format(len(warnings)),
            ""
        ]
       
        if violations:
            lines.append("## Violations")
            lines.append("")
            for i, v in enumerate(violations, 1):
                lines.append("{}. {}".format(i, v))
                lines.append("")
        
        report_path = self.context.project_dir / "docs" / "quality_gate_report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("\n".join(lines), encoding="utf-8")
        self.context.generated_files.append(report_path)
        return report_path
