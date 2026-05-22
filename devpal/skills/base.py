"""
Skills 系统核心抽象

Skills 是面向用户意图的任务级能力包，编排 Tool、OpenSpec、Template、LanguagePlugin。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from devpal.tools.registry import ToolRegistry
    from devpal.core.openspec_workflow import OpenSpecWorkflowExecutor


@dataclass
class SkillContext:
    """Skill 执行上下文"""

    user_query: str              # 用户原始查询
    workspace_path: Path                   # 工作空间路径
    tool_registry: Optional['ToolRegistry'] = None  # 工具注册表
    openspec_executor: Optional['OpenSpecWorkflowExecutor'] = None  # OpenSpec 执行器
    config: Dict = field(default_factory=dict)         # 配置参数
    metadata: Dict = field(default_factory=dict)       # 元数据


@dataclass
class SkillResult:
    """Skill 执行结果"""

    success: bool                             # 是否成功
    content: str                # 结果内容
    artifacts: List[str] = field(default_factory=list)  # 生成的文件路径
    metadata: Dict = field(default_factory=dict)        # 元数据
    sub_results: List['SkillResult'] = field(default_factory=list)  # 子任务结果


class BaseSkill(ABC):
    """Skill 抽象基类"""

    # 类属性（子类需要覆盖）
    name: str = ""                 # Skill 名称
    description: str = ""             # Skill 描述
    triggers: List[str] = []          # 触发关键词
    required_tools: List[str] = []    # 依赖的工具

    def can_handle(self, context: SkillContext) -> float:
        """
        判断是否能处理该任务

        Args:
         context: Skill 执行上下文

      Returns:
            float: 置信度 0.0-1.0
             0.0 = 完全不能处理
           0.5 = 可能能处理
            1.0 = 完全确定能处理
        """
        # 默认实现：基于触发词匹配
        query_lower = context.user_query.lower()
        for trigger in self.triggers:
            if trigger.lower() in query_lower:
                return 0.8
        return 0.0

    @abstractmethod
    def execute(self, context: SkillContext) -> SkillResult:
        """
        执行 Skill

        Args:
            context: Skill 执行上下文

        Returns:
          SkillResult: 执行结果
        """
        pass

    def validate_dependencies(self, context: SkillContext) -> bool:
        """验证依赖的工具是否可用"""
        if not context.tool_registry:
            return len(self.required_tools) == 0

        for tool_name in self.required_tools:
         if not context.tool_registry.has_tool(tool_name):
                return False
        return True
