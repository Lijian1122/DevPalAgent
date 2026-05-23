"""""
内置 Skills

提供开箱即用的 Skill 实现。
"""

from .installer import InstallerSkill
from .code_review import CodeReviewSkill
from .multi_agent import MultiAgentSkill
from .test_generation import TestGenerationSkill
from .openspec import OpenSpecSkill

__all__ = [
    "InstallerSkill",
    "CodeReviewSkill",
    "MultiAgentSkill",
    "TestGenerationSkill",
    "OpenSpecSkill",
]
