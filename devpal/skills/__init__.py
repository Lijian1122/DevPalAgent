"""
Skills 系统

Skills 是面向用户意图的任务级能力包，编排 Tool、OpenSpec、Template、LanguagePlugin。
"""

from .base import BaseSkill, SkillContext, SkillResult
from .registry import SkillRegistry
from .router import SkillRouter

__all__ = [
    "BaseSkill",
    "SkillContext",
    "SkillResult",
    "SkillRegistry",
    "SkillRouter",
]
