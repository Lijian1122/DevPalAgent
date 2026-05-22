"""
SkillRegistry - Skill 注册表

管理 Skill 的注册、查找和生命周期。
"""

import logging
from typing import Dict, List, Optional

from .base import BaseSkill


class SkillRegistry:
    """Skill 注册表"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化 SkillRegistry

        Args:
            logger: 日志记录器
        """
        self._skills: Dict[str, BaseSkill] = {}
        self.logger = logger or logging.getLogger(__name__)
    def register(self, skill: BaseSkill):
        """
        注册 Skill

        Args:
          skill: 要注册的 Skill

        Raises:
            ValueError: 如果 Skill 名称已存在
        """
        if skill.name in self._skills:
         raise ValueError(f"Skill '{skill.name}' already registered")

        self._skills[skill.name] = skill
        self.logger.info(f"Registered skill: {skill.name}")

    def unregister(self, skill_name: str):
        """
        注销 Skill

        Args:
            skill_name: Skill 名称

        Raises:
            KeyError: 如果 Skill 不存在
        """
        if skill_name not in self._skills:
            raise KeyError(f"Skill '{skill_name}' not found")

        del self._skills[skill_name]
        self.logger.info(f"Unregistered skill: {skill_name}")

    def get(self, skill_name: str) -> Optional[BaseSkill]:
        """
        根据名称获取 Skill

        Args:
            skill_name: Skill 名称

        Returns:
            Optional[BaseSkill]: Skill 实例，如果不存在返回 None
        """
        return self._skills.get(skill_name)

    def has(self, skill_name: str) -> bool:
        """
        检查 Skill 是否存在

        Args:
          skill_name: Skill 名称

        Returns:
            bool: 是否存在
        """
        return skill_name in self._skills

    def list_all(self) -> List[BaseSkill]:
        """
        列出所有已注册的 Skill

        Returns:
            List[BaseSkill]: Skill 列表
      """
        return list(self._skills.values())

    def list_names(self) -> List[str]:
        """
        列出所有已注册的 Skill 名称

        Returns:
            List[str]: Skill 名称列表
        """
        return list(self._skills.keys())

    def clear(self):
        """清空所有已注册的 Skill"""
        count = len(self._skills)
        self._skills.clear()
        self.logger.info(f"Cleared {count} skills")

    def __len__(self) -> int:
        """返回已注册的 Skill 数量"""
        return len(self._skills)

    def __contains__(self, skill_name: str) -> bool:
        """支持 'skill_name in registry' 语法"""
        return skill_name in self._skills
