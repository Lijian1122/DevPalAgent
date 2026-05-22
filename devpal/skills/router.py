"""
SkillRouter - Skill 路由器

负责意图识别、置信度评分和路由决策。
"""

import logging
from typing import List, Optional, Tuple

from .base import BaseSkill, SkillContext


class SkillRouter:
    """Skill 路由器"""

    def __init__(
        self,
        skills: Optional[List[BaseSkill]] = None,
        confidence_threshold: float = 0.8,
        logger: Optional[logging.Logger] = None
    ):
        """
      初始化 SkillRouter

        Args:
            skills: Skill 列表
            confidence_threshold: 置信度阈值（低于此值会 fallback）
            logger: 日志记录器
        """
        self.skills = skills or []
        self.confidence_threshold = confidence_threshold
        self.logger = logger or logging.getLogger(__name__)

    def route(self, context: SkillContext) -> Tuple[Optional[BaseSkill], float]:
        """
        路由到最匹配的 Skill

        Args:
            context: Skill 执行上下文 
        Returns:
            Tuple[Optional[BaseSkill], float]: (选中的 Skill, 置信度)
              如果置信度 < threshold，返回 (None, best_confidence)
        """
        best_skill = None
        best_confidence = 0.0

        # 计算每个 Skill 的置信度
        scores = []
        for skill in self.skills:
          try:
                confidence = skill.can_handle(context)
                scores.append((skill, confidence))

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_skill = skill
          except Exception as e:
             self.logger.warning(
             f"Error calculating confidence for {skill.name}: {e}"
              )
             scores.append((skill, 0.0))

        # 日志记录
        self.logger.info(f"SkillRouter: query='{context.user_query}'")
        for skill, confidence in sorted(scores, key=lambda x: x[1], reverse=True):
            self.logger.info(f"  - {skill.name}: {confidence:.2f}")

        # 判断是否达到阈值
        if best_confidence >= self.confidence_threshold:
           self.logger.info(
           f"  → Routed to: {best_skill.name} "
           f"(confidence={best_confidence:.2f})"
            )
           return best_skill, best_confidence
        else:
            self.logger.info(
                f"  → Fallback to Planner "
                f"(best_confidence={best_confidence:.2f} < {self.confidence_threshold})"
            )
        return None, best_confidence

    def register_skill(self, skill: BaseSkill):
        """注册新 Skill"""
        self.skills.append(skill)
        self.logger.info(f"Registered skill: {skill.name}")

    def unregister_skill(self, skill_name: str):
        """注销 Skill"""
        self.skills = [s for s in self.skills if s.name != skill_name]
        self.logger.info(f"Unregistered skill: {skill_name}")

    def get_skill(self, skill_name: str) -> Optional[BaseSkill]:
        """根据名称获取 Skill"""
        for skill in self.skills:
            if skill.name == skill_name:
                return skill
        return None

    def list_skills(self) -> List[str]:
        """列出所有已注册的 Skill 名称"""
        return [skill.name for skill in self.skills]
