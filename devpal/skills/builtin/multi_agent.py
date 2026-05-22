"""
MultiAgentSkill - 多 Agent 协作 Skill

演示多 Agent 协作模式：需求分析 → 代码生成 → 测试验证。
面试演示用。
"""

from pathlib import Path
from datetime import datetime

from devpal.skills.base import BaseSkill, SkillContext, SkillResult
from devpal.core.llm_client import get_llm_client


class MultiAgentSkill(BaseSkill):
    """多 Agent 协作 Skill（面试演示用）"""

    name = "multi_agent_skill"
    description = "演示多 Agent 协作模式：需求分析 → 代码生成 → 测试验证"
    triggers = ["多 Agent", "协作", "并行", "multi-agent", "multi agent"]
    required_tools = []

    def can_handle(self, context: SkillContext) -> float:
        """判断是否能处理"""
        base_confidence = super().can_handle(context)

        # 检查是否明确要求多 Agent
        query_lower = context.user_query.lower()
        if "多" in context.user_query or "multi" in query_lower or "协作" in context.user_query:
            return min(base_confidence + 0.2, 1.0)

        return base_confidence

    def execute(self, context: SkillContext) -> SkillResult:
        """执行多 Agent 协作"""
        llm_client = get_llm_client()

        # Agent A: 需求分析
        agent_a_result = self._agent_a_analyze(context, llm_client)

        # Agent B: 代码生成
        agent_b_result = self._agent_b_generate(context, llm_client, agent_a_result)

        # Agent C: 测试验证
        agent_c_result = self._agent_c_validate(context, llm_client, agent_b_result)

        # 生成协作报告
        report = self._generate_collaboration_report(
            agent_a_result, agent_b_result, agent_c_result
        )

        report_path = context.workspace_path / "docs" / "multi_agent_report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding='utf-8')

        return SkillResult(
            success=True,
            content="多 Agent 协作完成",
          artifacts=[str(report_path)],
            metadata={"agents": ["A", "B", "C"], "report": str(report_path)},
        sub_results=[agent_a_result, agent_b_result, agent_c_result]
        )

    def _agent_a_analyze(self, context: SkillContext, llm_client) -> SkillResult:
        """Agent A: 需求分析"""
        system_prompt = """你是需求分析专家 Agent A。
你的职责是：
1. 分析用户需求
2. 识别核心功能点
3. 列出技术要求
4. 输出结构化的需求文档

请用简洁的语言输出分析结果。"""

        user_message = f"""请分析以下需求：

{context.user_query}

请输出：
1. 核心功能（3-5 个要点）
2. 技术要求（2-3 个要点）
3. 实现建议（2-3 个要点）"""

        try:
            analysis = llm_client.generate(
                system=system_prompt,
                user_message=user_message
            )
            return SkillResult(
                success=True,
                content=analysis,
         metadata={"agent": "A", "role": "需求分析", "timestamp": self._get_timestamp()}
          )
        except Exception as e:
         return SkillResult(
                success=False,
                content=f"Agent A 分析失败: {str(e)}",
            metadata={"agent": "A", "role": "需求分析", "error": str(e)}
        )

    def _agent_b_generate(self, context: SkillContext, llm_client, agent_a_result: SkillResult) -> SkillResult:
        """Agent B: 代码生成"""
        if not agent_a_result.success:
            return SkillResult(
                success=False,
                content="Agent A 分析失败，无法生成代码",
             metadata={"agent": "B", "role": "代码生成"}
            )

        system_prompt = """你是代码生成专家 Agent B。
你的职责是：
1. 根据需求分析生成代码
2. 遵循最佳实践
3. 添加必要的注释
4. 确保代码可读性

请生成简洁、可运行的代码示例。"""

        user_message = f"""根据以下需求分析生成代码：

{agent_a_result.content}

请生成：
1. 核心代码实现（Python 或伪代码）
2. 关键函数说明
3. 使用示例"""

        try:
          code = llm_client.generate(
          system=system_prompt,
                user_message=user_message
          )
          return SkillResult(
        success=True,
              content=code,
                metadata={"agent": "B", "role": "代码生成", "timestamp": self._get_timestamp()}
            )
        except Exception as e:
            return SkillResult(
                success=False,
       content=f"Agent B 生成失败: {str(e)}",
                metadata={"agent": "B", "role": "代码生成", "error": str(e)}
            )

    def _agent_c_validate(self, context: SkillContext, llm_client, agent_b_result: SkillResult) -> SkillResult:
        """Agent C: 测试验证"""
        if not agent_b_result.success:
            return SkillResult(
                success=False,
                content="Agent B 生成失败，无法验证",
                metadata={"agent": "C", "role": "测试验证"}
            )

        system_prompt = """你是测试验证专家 Agent C。
你的职责是：
1. 审查代码质量
2. 识别潜在问题
3. 提出改进建议
4. 验证功能完整性

请提供专业的验证报告。"""

        user_message = f"""请验证以下代码：

{agent_b_result.content}

请输出：
1. 代码质量评估（优点和缺点）
2. 潜在问题（2-3 个）
3. 改进建议（2-3 个）
4. 测试建议（2-3 个测试用例）"""

        try:
         validation = llm_client.generate(
           system=system_prompt,
                user_message=user_message
            )
         return SkillResult(
           success=True,
                content=validation,
                metadata={"agent": "C", "role": "测试验证", "timestamp": self._get_timestamp()}
            )
        except Exception as e:
          return SkillResult(
          success=False,
                content=f"Agent C 验证失败: {str(e)}",
                metadata={"agent": "C", "role": "测试验证", "error": str(e)}
        )

    def _generate_collaboration_report(
        self,
        agent_a: SkillResult,
        agent_b: SkillResult,
        agent_c: SkillResult
    ) -> str:
        """生成协作报告"""
        report = f"""# Multi-Agent 协作报告

生成时间: {self._get_timestamp()}

---

## Agent A: 需求分析

**状态**: {'✅ 成功' if agent_a.success else '❌ 失败'}

{agent_a.content}
---

## Agent B: 代码生成

**状态**: {'✅ 成功' if agent_b.success else '❌ 失败'}

{agent_b.content}

---

## Agent C: 测试验证

**状态**: {'✅ 成功' if agent_c.success else '❌ 失败'}

{agent_c.content}

---

## 协作总结

### 工作流程
1. **Agent A** 完成需求分析，识别核心功能和技术要求
2. **Agent B** 基于分析结果生成代码实现
3. **Agent C** 验证代码质量并提出改进建议

### 协作模式
- **串行协作**: Agent B 依赖 Agent A 的输出，Agent C 依赖 Agent B 的输出
- **职责分离**: 每个 Agent 专注于自己的领域
- **结果传递**: 通过 SkillResult 传递中间结果

### 技术亮点
- 多 Agent 任务分解
- 结构化结果传递
- 错误处理和容错机制

---

*生成工具: DevPalAgent MultiAgentSkill*
"""
        return report

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
