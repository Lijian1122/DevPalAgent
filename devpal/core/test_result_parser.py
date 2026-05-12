# -*- coding: utf-8 -*-
"""
测试结果解析工具
"""

import re
from typing import Dict


def parse_test_results(test_output: str) -> Dict[str, int]:
    """Parse test output to count passed/failed tests

    Args:
        test_output: Raw test output string

    Returns:
        Dictionary with 'passed' and 'total' counts
    """
    passed = 0
    total = 0

    # Common patterns
    for line in test_output.split('\n'):
        if re.search(r'PASS|passed|OK', line, re.IGNORECASE):
            passed += 1
        if re.search(r'passed|tests?|cases?', line, re.IGNORECASE):
            match = re.search(r'(\d+)\s*(passed|tests?|cases?)', line, re.IGNORECASE)
            if match:
                try:
                    total = max(total, int(match.group(1)))
                except ValueError:
                    pass

    if total == 0:
        total = passed

    return {"passed": passed, "total": total}


def parse_test_results_detailed(test_output: str) -> Dict[str, any]:
    """更详细的测试结果解析

    Returns:
        Dictionary with detailed test statistics
    """
    basic = parse_test_results(test_output)

    failed = basic["total"] - basic["passed"]
    failed_names = []

    # 提取失败的测试用例名
    for line in test_output.split('\n'):
        fail_match = re.search(r'(FAIL|FAILED|error).*?:?\s*(\w+)', line, re.IGNORECASE)
        if fail_match:
            failed_names.append(fail_match.group(2))

    return {
        **basic,
        "failed": failed,
        "failed_names": failed_names,
        "success_rate": basic["passed"] / basic["total"] if basic["total"] > 0 else 0.0
    }
