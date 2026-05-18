# -*- coding: utf-8 -*-
"""
Phase 9 安全测试：路径遍历攻击防护
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from devpal.core.openspec_phases.phase9_quality_gate import Phase9QualityGate
from devpal.core.openspec_phases.base import OpenSpecContext


class TestPhase9Security:
    """测试 Phase 9 的安全防护机制"""

    @pytest.fixture
    def temp_project(self):
        """创建临时项目目录"""
        temp_dir = Path(tempfile.mkdtemp())
        project_dir = temp_dir / "test_project"
        project_dir.mkdir()

        # 创建基本结构
        (project_dir / "src").mkdir()
        (project_dir / "include").mkdir()
        (project_dir / "tests").mkdir()

        # 创建测试文件
        (project_dir / "src" / "test.cpp").write_text("int main() { return 0; }")
        (project_dir / "include" / "test.h").write_text("#ifndef TEST_H\n#define TEST_H\n#endif")

        yield project_dir

        # 清理
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def context(self, temp_project):
      """创建测试上下文"""
      requirements_file = temp_project / "requirements.md"
      requirements_file.write_text("# Test Requirements")

      return OpenSpecContext(
            requirements_file=requirements_file,
            project_dir=temp_project
        )

    def test_path_traversal_attack_absolute_path(self, context, temp_project):
        """测试路径遍历攻击：绝对路径"""
        phase9 = Phase9QualityGate(context)

        # 构造恶意修复计划：尝试修改项目外的文件
        malicious_plan = {
            'analysis': {
             'root_cause': 'test',
                'issue_validity': 'test',
                'fix_strategy': 'test',
                'risk_assessment': 'test'
            },
            'fixes': [
              {
            'file': '/etc/passwd',  # 绝对路径，项目外
                    'line': 1,
                    'issue_category': 'test',
                    'old_code': 'root:',
                    'new_code': 'hacked:',
               'reason': 'malicious fix'
                }
            ]
        }

        # 执行修复计划（应该被拒绝）
        result = phase9._execute_fix_plan(malicious_plan)

        # 验证：修复应该失败
        assert result is False, "Should reject absolute path outside project"

    def test_valid_path_within_project(self, context, temp_project):
        """测试合法路径：项目内的文件"""
        phase9 = Phase9QualityGate(context)

        # 创建测试文件
        test_file = temp_project / "src" / "test.cpp"
        test_file.write_text("int main() { return 0; }")

        # 构造合法修复计划
        valid_plan = {
            'analysis': {
                'root_cause': 'test',
             'issue_validity': 'test',
                'fix_strategy': 'test',
              'risk_assessment': 'test'
            },
            'fixes': [
              {
                    'file': 'src/test.cpp',
               'line': 1,
                    'issue_category': 'test',
                'old_code': 'int main() { return 0; }',
                    'new_code': 'int main() { return 1; }',
                    'reason': 'valid fix'
              }
          ]
        }

        # 执行修复计划（应该成功）
        result = phase9._execute_fix_plan(valid_plan)

        # 验证：修复应该成功
        assert result is True, "Should accept valid path within project"

        # 验证文件内容被修改
        actual_content = test_file.read_text()
        assert 'return 1' in actual_content, "File should be modified"

    def test_nonexistent_file(self, context, temp_project):
        """测试不存在的文件"""
        phase9 = Phase9QualityGate(context)

        # 构造修复计划：文件不存在
        plan = {
            'analysis': {
                'root_cause': 'test',
                'issue_validity': 'test',
              'fix_strategy': 'test',
         'risk_assessment': 'test'
      },
            'fixes': [
             {
                    'file': 'src/nonexistent.cpp',
                'line': 1,
                    'issue_category': 'test',
                'old_code': 'old',
           'new_code': 'new',
              'reason': 'test'
              }
            ]
        }

        # 执行修复计划（应该失败）
        result = phase9._execute_fix_plan(plan)

        # 验证：修复应该失败
        assert result is False, "Should reject nonexistent file"

    def test_suspicious_fix_reason(self, context):
        """测试可疑的修复原因"""
        phase9 = Phase9QualityGate(context)

        # 测试各种可疑关键词
        suspicious_reasons = [
            'comment out the validation',
          'ignore the error',
        'suppress the warning',
          'relax validation rules',
            'reduce validation',
            'weaken validation',
            'disable validation',
            'skip validation'
        ]

        for reason in suspicious_reasons:
            fix = {
            'file': 'src/test.cpp',
         'line': 1,
                'issue_category': 'test',
                'old_code': 'old',
              'new_code': 'new',
             'reason': reason
      }

        # 验证：应该被拒绝
            result = phase9._is_fix_safe(fix)
            assert result is False, f"Should reject suspicious reason: {reason}"

    def test_unsafe_security_fix(self, context):
        """测试不安全的安全修复"""
        phase9 = Phase9QualityGate(context)

        # 测试：安全修复中仍然包含不安全函数
        fix = {
        'file': 'src/test.cpp',
        'line': 1,
            'issue_category': 'security',
            'old_code': 'strcpy(buffer, input);',
          'new_code': 'strcpy(buffer2, input);',  # 仍然使用 strcpy
            'reason': 'fix security issue'
        }

        # 验证：应该被拒绝
        result = phase9._is_fix_safe(fix)
        assert result is False, "Should reject security fix that still contains unsafe function"

    def test_fix_with_unfinished_markers(self, context):
        """测试包含未完成标记的修复"""
        phase9 = Phase9QualityGate(context)

        # 测试各种未完成标记
        unfinished_markers = ['TODO', 'FIXME', 'HACK', 'temporary workaround']

        for marker in unfinished_markers:
            fix = {
                'file': 'src/test.cpp',
          'line': 1,
                'issue_category': 'test',
                'old_code': 'old',
                'new_code': f'new // {marker}: finish this later',
        'reason': 'test'
            }

            # 验证：应该被拒绝
            result = phase9._is_fix_safe(fix)
            assert result is False, f"Should reject fix with unfinished marker: {marker}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
