# -*- coding: utf-8 -*-
"""
抽象 FunctionCall 模块
提供统一的函数调用抽象基类，支持链式调用、参数校验、执行追踪
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Generic, TypeVar, List
from pydantic import BaseModel
from dataclasses import dataclass, field
from datetime import datetime
import uuid


T = TypeVar('T')  # 输入参数类型
R = TypeVar('R')  # 返回结果类型


@dataclass
class ExecutionResult:
    """执行结果封装"""
    success: bool
    data: Any = None
    error_message: Optional[str] = None
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, data: Any, **metadata) -> "ExecutionResult":
        """成功结果"""
        return cls(success=True, data=data, metadata=metadata)

    @classmethod
    def fail(cls, error_msg: str, **metadata) -> "ExecutionResult":
        """失败结果"""
        return cls(success=False, error_message=error_msg, metadata=metadata)


class FunctionCallContext:
    """函数调用上下文 - 存储调用链状态"""

    def __init__(self):
        self.call_chain: List[Dict[str, Any]] = []
        self.variables: Dict[str, Any] = {}
        self.start_time: Optional[datetime] = None

    def add_call(self, func_name: str, params: Dict[str, Any], result: ExecutionResult):
        """添加调用记录"""
        self.call_chain.append({
            'function': func_name,
            'params': params,
            'result': result,
            'timestamp': datetime.now()
        })

    def set_var(self, key: str, value: Any):
        """设置变量"""
        self.variables[key] = value

    def get_var(self, key: str, default: Any = None) -> Any:
        """获取变量"""
        return self.variables.get(key, default)

    def get_call_count(self) -> int:
        """获取调用次数"""
        return len(self.call_chain)

    def get_total_duration(self) -> float:
        """获取总执行时间"""
        return sum(call['result'].duration_ms for call in self.call_chain)


class AbstractFunctionCall(ABC, Generic[T, R]):
    """抽象函数调用基类

    所有具体操作都继承此类，提供统一的执行接口
    支持：参数校验、执行追踪、错误处理、链式调用
    """

    # 子类需要定义参数模型
    class Parameters(BaseModel):
        pass

    def __init__(self, context: Optional[FunctionCallContext] = None):
        self.context = context or FunctionCallContext()
        self.func_name = self.__class__.__name__

    @property
    @abstractmethod
    def name(self) -> str:
        """函数名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """函数描述"""
        pass

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str], Optional[T]]:
        """参数校验 - 默认使用 Pydantic 模型校验

        Returns:
            (是否合法, 错误信息, 解析后的参数对象)
        """
        try:
            validated_params = self.Parameters(**params)
            return True, None, validated_params
        except Exception as e:
            return False, str(e), None

    @abstractmethod
    def do_call(self, params: T) -> R:
        """实际执行逻辑 - 子类必须实现

        Args:
            params: 校验后的参数对象

        Returns:
            执行结果数据
        """
        pass

    def __call__(self, **kwargs) -> ExecutionResult:
        """执行函数调用

        提供统一的入口，包含：
        1. 参数校验
        2. 执行计时
        3. 错误捕获
        4. 调用追踪
        """
        start_time = datetime.now()

        try:
            # 参数校验
            valid, error_msg, params = self.validate_params(kwargs)
            if not valid:
                result = ExecutionResult.fail(f"参数校验失败: {error_msg}")
                self.context.add_call(self.func_name, kwargs, result)
                return result

            # 实际执行
            data = self.do_call(params)

            # 计算耗时
            duration = (datetime.now() - start_time).total_seconds() * 1000

            # 成功结果
            result = ExecutionResult.ok(data, duration_ms=duration)
            result.duration_ms = duration

            # 记录调用
            self.context.add_call(self.func_name, kwargs, result)

            return result

        except Exception as e:
            # 错误处理
            duration = (datetime.now() - start_time).total_seconds() * 1000
            result = ExecutionResult.fail(f"执行异常: {str(e)}", duration_ms=duration)
            result.duration_ms = duration
            self.context.add_call(self.func_name, kwargs, result)
            return result

    def chain(self, next_func: "AbstractFunctionCall") -> "FunctionChain":
        """链式调用 - 将多个函数组合成执行链

        Args:
            next_func: 下一个要执行的函数

        Returns:
            函数链对象
        """
        return FunctionChain(self, next_func, context=self.context)

    def to_function_schema(self) -> Dict[str, Any]:
        """生成函数调用 Schema（用于 LLM Tool Call 格式）"""
        schema = self.Parameters.model_json_schema()

        properties = {}
        for name, prop in schema.get("properties", {}).items():
            cleaned_prop = {}
            for key, value in prop.items():
                if key not in ["title", "$ref", "$defs"]:
                    cleaned_prop[key] = value
            properties[name] = cleaned_prop

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": schema.get("required", [])
            }
        }


class FunctionChain:
    """函数链 - 支持多个函数串行执行

    前一个函数的输出可以作为后一个函数的输入
    """

    def __init__(self, *funcs: AbstractFunctionCall, context: Optional[FunctionCallContext] = None):
        self.functions = list(funcs)
        self.context = context or FunctionCallContext()
        for func in self.functions:
            func.context = self.context

    def then(self, func: AbstractFunctionCall) -> "FunctionChain":
        """添加后续函数"""
        func.context = self.context
        self.functions.append(func)
        return self

    def execute(self, **initial_params) -> List[ExecutionResult]:
        """执行整个函数链

        Args:
            initial_params: 初始参数

        Returns:
            所有执行结果的列表
        """
        results = []
        current_params = initial_params

        for func in self.functions:
            # 合并上下文变量到参数中
            params = {**self.context.variables, **current_params}

            result = func(**params)
            results.append(result)

            if not result.success:
                # 失败则中断链条
                break

            # 将结果数据存入上下文，供后续函数使用
            if result.data is not None:
                if isinstance(result.data, dict):
                    self.context.variables.update(result.data)
                else:
                    self.context.set_var(f"{func.name}_result", result.data)

            # 准备下一次的参数：初始参数 + 上一个函数的结果
            if isinstance(result.data, dict):
                current_params = {**initial_params, **result.data}
            else:
                current_params = initial_params.copy()

        return results

    def get_summary(self) -> Dict[str, Any]:
        """获取执行摘要"""
        return {
            'total_calls': self.context.get_call_count(),
            'total_duration_ms': self.context.get_total_duration(),
            'success_count': sum(1 for call in self.context.call_chain if call['result'].success),
            'call_chain': [
                {
                    'function': call['function'],
                    'success': call['result'].success,
                    'duration_ms': call['result'].duration_ms
                }
                for call in self.context.call_chain
            ]
        }
