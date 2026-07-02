# -*- coding: utf-8 -*-
"""
配置加载模块
支持从配置文件加载配置，并在配置缺失时使用环境变量兜底
"""
import os
import yaml
from typing import Any, Optional
from pathlib import Path


class Config:
    """配置管理器"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置
        Args:
            config_path: 配置文件路径，默认查找 config/config.yaml
        """
        if config_path is None:
            # 基于当前模块路径查找，确保从任意目录运行都能找到
            base_dir = Path(__file__).resolve().parent.parent
            config_path = base_dir / "config" / "config.yaml"
        else:
            base_dir = Path(config_path).resolve().parent.parent

        self.config_path = Path(config_path)
        self.base_dir = base_dir
        self.config = self._load_config()

    @staticmethod
    def _first_configured(*values: Any, default=None) -> Any:
        """Return the first non-empty value, preserving config-before-env order."""
        for value in values:
            if value is not None and value != "":
                return value
        return default

    def _load_config(self) -> dict:
        """加载配置文件"""
        if not self.config_path.exists():
            print(f"[WARNING] 配置文件不存在: {self.config_path}")
            print(f"[INFO] 请复制 config/config.yaml.example 为 config/config.yaml 并填写配置")
            return {}

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"[ERROR] 加载配置文件失败: {e}")
            return {}

    def get(self, key: str, default=None):
        """
        获取配置值，支持点号分隔的嵌套键
        例如: get("anthropic.auth_token")
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    @property
    def anthropic_auth_token(self) -> Optional[str]:
        """获取 Anthropic API Token"""
        # 优先级：配置文件 > 环境变量兜底
        return self._first_configured(
            self.get("llm.anthropic.auth_token"),
            self.get("anthropic.auth_token"),
            os.getenv("ANTHROPIC_AUTH_TOKEN"),
            os.getenv("ANTHROPIC_API_KEY"),
        )

    @property
    def anthropic_base_url(self) -> str:
        """获取 Anthropic API 基础 URL"""
        return self._first_configured(
            self.get("llm.anthropic.base_url"),
            self.get("anthropic.base_url"),
            os.getenv("ANTHROPIC_BASE_URL"),
            default="https://api.anthropic.com",
        )

    @property
    def anthropic_model(self) -> str:
        """获取使用的模型"""
        return self._first_configured(
            self.get("llm.anthropic.model"),
            self.get("anthropic.model"),
            os.getenv("OPENSPEC_MODEL"),
            default="claude-3-sonnet-20240229",
        )

    @property
    def max_iterations(self) -> int:
        """获取最大迭代次数"""
        return int(self.get("agent.max_iterations", 5))

    @property
    def max_tokens(self) -> int:
        """获取最大 Token 数"""
        return int(self.get("agent.max_tokens", 4096))

    @property
    def temperature(self) -> float:
        """获取温度参数"""
        return float(self.get("agent.temperature", 0.7))

    @property
    def command_timeout(self) -> int:
        """获取命令执行超时时间"""
        return int(self.get("tools.command_timeout", 30))

    # ===== 新增：多 LLM Provider 配置 =====
    @property
    def llm_default_provider(self) -> str:
        """获取默认 LLM Provider"""
        return self.get("llm.default_provider", "openai")

    @property
    def llm_fallback_providers(self) -> list:
        """获取 Fallback Provider 列表"""
        return self.get("llm.fallback_providers", [])

    def get_provider_config(self, provider: str) -> dict:
        """获取指定 Provider 的配置

        Args:
            provider: Provider 名称（anthropic/openai/gemini）

        Returns:
            Provider 配置字典
        """
        config = dict(self.get(f"llm.{provider}", {}) or {})

        # 优先使用 config.yaml 中的 provider 配置；环境变量只在缺失时兜底。
        if provider == "anthropic":
            config["auth_token"] = (
                self._first_configured(
                    config.get("auth_token"),
                    self.get("anthropic.auth_token"),
                    os.getenv("ANTHROPIC_AUTH_TOKEN"),
                    os.getenv("ANTHROPIC_API_KEY"),
                )
            )
            config["base_url"] = (
                self._first_configured(
                    config.get("base_url"),
                    self.get("anthropic.base_url"),
                    os.getenv("ANTHROPIC_BASE_URL"),
                    default="https://api.anthropic.com",
                )
            )
            config["model"] = (
                self._first_configured(
                    config.get("model"),
                    self.get("anthropic.model"),
                    os.getenv("OPENSPEC_MODEL"),
                    default="claude-3-sonnet-20240229",
                )
            )
        elif provider == "openai":
            config["api_key"] = self._first_configured(
                config.get("api_key"),
                os.getenv("OPENAI_API_KEY"),
            )
            config["base_url"] = self._first_configured(
                config.get("base_url"),
                os.getenv("OPENAI_BASE_URL"),
                default="https://api.openai.com/v1",
            )
            config["model"] = self._first_configured(
                config.get("model"),
                os.getenv("OPENSPEC_MODEL"),
                default="gpt-5.5-pro",
            )
        elif provider == "gemini":
            config["api_key"] = self._first_configured(
                config.get("api_key"),
                os.getenv("GOOGLE_API_KEY"),
            )

        return config


# 全局配置实例
_config_instance = None


def get_config() -> Config:
    """获取全局配置实例（单例模式）"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
