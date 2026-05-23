"""
TestGenerationSkill - 测试生成 Skill

编排完整的测试生成流程：测试文档生成 → 测试代码生成 → 测试运行。
"""

from pathlib import Path
from typing import Optional

from devpal.skills.base import BaseSkill, SkillContext, SkillResult


class TestGenerationSkill(BaseSkill):
    """测试生成 Skill - 编排完整测试流程"""

    name = "test_generation_skill"
    description = "编排完整的测试生成流程：测试文档生成 → 测试代码生成 → 测试运行"
    triggers = ["生成测试", "测试用例", "test", "test generation", "测试生成", "自动测试"]
    required_tools = ["test_orchestrator"]

    def can_handle(self, context: SkillContext) -> float:
        """判断是否能处理"""
        base_confidence = super().can_handle(context)

        # 检查是否提到测试相关关键词
        test_keywords = ["测试", "test", "用例", "case", "unittest", "pytest"]
        query_lower = context.user_query.lower()

        keyword_count = sum(1 for keyword in test_keywords if keyword in query_lower)

        if keyword_count >= 2:
            return min(base_confidence + 0.15, 1.0)

        return base_confidence

    def execute(self, context: SkillContext) -> SkillResult:
        """执行测试生成流程"""
        # 1. 检查 tool_registry
        if not context.tool_registry:
            return SkillResult(
              success=False,
                content="tool_registry 未初始化，无法执行测试生成",
                metadata={"error": "missing_tool_registry"}
          )

        # 2. 从查询中提取文件路径
        file_path = self._extract_file_path(context)
        if not file_path:
            return SkillResult(
             success=False,
             content="未能从查询中提取文件路径，请明确指定要测试的源文件",
                metadata={"error": "missing_file_path"}
         )

        # 3. 检查文件是否存在
        full_path = context.workspace_path / file_path
        if not full_path.exists():
            return SkillResult(
                success=False,
                content=f"源文件不存在: {file_path}",
                metadata={"error": "file_not_found", "file_path": str(file_path)}
         )

        # 4. 调用 test_orchestrator 工具
        try:
           result = context.tool_registry.execute_tool('test_orchestrator', {
                'file_path': str(full_path),
                'project_name': full_path.stem,
                'run_code_review': True,
                'generate_code_review_report': True,
                'run_auto_fix': True,
                'backup_before_fix': True,
                'generate_test_doc': True,
                'generate_test_code': True,
                'run_tests': True,
                'update_doc_with_results': True,
                'update_doc_with_fix_results': True,
                'auto_retry_on_test_failure': True,
                'max_retry_attempts': 3})

           if result.success:
                # 提取关键信息
                output_dir = result.metadata.get('output_dir', '')
                test_doc = result.metadata.get('test_document', '')
                test_code = result.metadata.get('test_code_file', '')
                code_review_report = result.metadata.get('code_review_report', '')

                artifacts = []
                if test_doc:
                    artifacts.append(test_doc)
                if test_code:
                 artifacts.append(test_code)
                if code_review_report:
                    artifacts.append(code_review_report)

                return SkillResult(
                    success=True,
                    content=f"测试生成流程执行成功\n\n{result.content}",
                  artifacts=artifacts,
               metadata={
                  "output_dir": output_dir,
                   "test_document": test_doc,
                    "test_code_file": test_code,
                   "code_review_report": code_review_report,
                        "results": result.metadata.get('results', {})
                    }
                )
           else:
                return SkillResult(
                    success=False,
                 content=f"测试生成流程执行失败\n\n{result.content}",
                    metadata={"error": "orchestrator_failed"}
                )
        except Exception as e:
           return SkillResult(
           success=False,
                content=f"测试生成过程出错: {str(e)}",
              metadata={"error": "exception", "exception_message": str(e)}
        )

    def _extract_file_path(self, context: SkillContext) -> Optional[str]:
        """从查询中提取文件路径"""
        import re

        query = context.user_query

        # 尝试匹配常见的文件路径模式
        patterns = [
            r'(?:文件|file|源文件|source)\s*[:：]?\s*[`"]?([^\s`"]+\.(cpp|py|java|js|ts|go|rs))[`"]?',
            r'[`"]([^\s`"]+\.(cpp|py|java|js|ts|go|rs))[`"]',
            r'(\w+/[\w/]+\.(cpp|py|java|js|ts|go|rs))',
            r'([\w]+\.(cpp|py|java|js|ts|go|rs))'
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
             return match.group(1)

        # 如果没有匹配到，检查 metadata 中是否有文件路径
        if 'file_path' in context.metadata:
          return context.metadata['file_path']

        return None
