# -*- coding: utf-8 -*-
"""
Tool 基类
自动生成 JSON Schema + 参数校验
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel


class ToolResult(BaseModel):
    """工具执行结果"""
    success: bool
    content: str
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}


class BaseTool(ABC):
    """所有工具的基类 - 自动从 Pydantic 模型生成 Schema"""

    # 子类需要定义参数模型
    class Parameters(BaseModel):
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称，必须是唯一的"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述，告诉 LLM 这个工具是干什么的"""
        pass

    @abstractmethod
    def execute(self, params: Parameters) -> ToolResult:
        """执行工具的具体逻辑"""
        pass

    def to_function_call_format(self) -> Dict[str, Any]:
        """从 Pydantic 模型自动生成 Claude Tool 格式"""
        schema = self.Parameters.model_json_schema()
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": schema.get("properties", {}),
                "required": schema.get("required", [])
            }
        }

    def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, Optional[str], Optional[Parameters]]:
        """用 Pydantic 自动校验，返回 (是否合法, 错误信息, 解析后的参数对象)"""
        try:
            params = self.Parameters(**parameters)
            return True, None, params
        except Exception as e:
            return False, str(e), None

    def execute_with_validation(self, parameters: Dict[str, Any]) -> ToolResult:
        """带校验的执行入口"""
        valid, error, params = self.validate_parameters(parameters)
        if not valid:
            return ToolResult(
                success=False,
                content="",
                error_message=f"参数校验失败: {error}"
            )
        return self.execute(params)
