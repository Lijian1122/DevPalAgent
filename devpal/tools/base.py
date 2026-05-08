# -*- coding: utf-8 -*-
"""
Tool 基类 - 阶段1完整版本
自动生成 JSON Schema + 参数校验 + 重试机制 + 安全沙箱
"""
import time
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable
from pydantic import BaseModel


class ToolResult(BaseModel):
    """工具执行结果 - 增强版"""
    success: bool
    content: str
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}

    @classmethod
    def ok(cls, content: str, **metadata) -> "ToolResult":
        """快捷创建成功结果"""
        return cls(success=True, content=content, metadata=metadata)

    @classmethod
    def error(cls, error_msg: str, **metadata) -> "ToolResult":
        """快捷创建失败结果"""
        return cls(success=False, content="", error_message=error_msg, metadata=metadata)


class ToolSecurity:
    """工具安全沙箱 - 白名单机制"""

    # 命令执行白名单
    SAFE_COMMANDS = {
        'ls', 'dir', 'pwd', 'cd', 'echo', 'cat', 'type',
        'find', 'grep', 'findstr', 'where',
        'git', 'git.exe',
        'python', 'python.exe', 'pip',
        'cl', 'cl.exe', 'link', 'link.exe', 'msbuild',
        'cmake', 'ninja', 'make',
        'cmd', 'cmd.exe',  # Windows 命令行
        'mkdir', 'md',  # 创建目录
    }

    # 危险命令黑名单
    DANGER_PATTERNS = [
        r'rm\s+-rf',
        r'del\s+/s/q',
        r'format\s+',
        r'mkfs',
        r'dd\s+if=',
        r':\(\)\s*\{',
        r'shred',
        r'wget\s',
        r'curl\s',
        r'nc\s',
        r'netcat',
        r'ssh\s',
        r'scp\s',
        r'ftp\s',
        r'telnet',
    ]

    @classmethod
    def check_command_safety(cls, command: str) -> tuple[bool, Optional[str]]:
        """检查命令安全性"""
        cmd_lower = command.lower()

        # 检查危险模式
        for pattern in cls.DANGER_PATTERNS:
            if re.search(pattern, cmd_lower, re.IGNORECASE):
                return False, f"检测到危险命令模式: {pattern}"

        # 提取基础命令名
        base_cmd = cmd_lower.split()[0] if cmd_lower.split() else ''

        # 如果是白名单内的命令，允许
        if base_cmd in cls.SAFE_COMMANDS:
            return True, None

        # 不在白名单，提示风险
        return False, (
            f"命令 '{base_cmd}' 不在安全白名单内。\n"
            f"如需执行，请先将其加入安全白名单。\n"
            f"当前白名单: {', '.join(sorted(cls.SAFE_COMMANDS))}"
        )

    @classmethod
    def check_path_safety(cls, path: str) -> tuple[bool, Optional[str]]:
        """检查文件路径安全性"""
        path_lower = path.lower()

        sensitive_patterns = [
            '/etc/', '/root/', '~/.ssh', '.ssh/',
            'id_rsa', 'id_dsa', 'id_ed25519',
            '.env', '.pem', '.key',
            '/password', '/secret',
        ]

        for pattern in sensitive_patterns:
            if pattern.lower() in path_lower:
                return False, f"禁止访问敏感路径: {pattern}"

        return True, None


def retry(max_retries: int = 3, delay: float = 1.0):
    """重试装饰器"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> ToolResult:
            last_error = None
            for attempt in range(max_retries):
                try:
                    result = func(*args, **kwargs)
                    if result.success or attempt == max_retries - 1:
                        result.metadata['retry_attempts'] = attempt
                        return result
                except Exception as e:
                    last_error = str(e)
                time.sleep(delay)
            return ToolResult.error(
                f"重试 {max_retries} 次后仍失败，最后错误: {last_error}",
                retries=max_retries
            )
        return wrapper
    return decorator


class BaseTool(ABC):
    """所有工具的基类 - 自动从 Pydantic 模型生成 Schema"""

    # 子类需要定义参数模型
    class Parameters(BaseModel):
        pass

    def __init__(self):
        self.tool_name = self.__class__.__name__
        self.call_count = 0

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称，必须是唯一的"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述，告诉 LLM 这 tool(s)是干什么的"""
        pass

    @abstractmethod
    def _execute(self, params: Parameters) -> ToolResult:
        """实际执行逻辑，子类实现"""
        pass

    def execute(self, params: Parameters) -> ToolResult:
        """执行工具（带统计和通用处理）"""
        self.call_count += 1
        return self._execute(params)

    def to_function_call_format(self) -> Dict[str, Any]:
        """从 Pydantic 模型自动生成 Claude Tool 格式（清理不兼容字段）"""
        schema = self.Parameters.model_json_schema()

        # 清理 properties 中的不兼容字段（移除 title、$ref 等）
        properties = {}
        for name, prop in schema.get("properties", {}).items():
            cleaned_prop = {}
            for key, value in prop.items():
                # 移除不兼容的字段，保留 Claude API 支持的字段
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
            return ToolResult.error(f"参数校验失败: {error}")
        return self.execute(params)
