# -*- coding: utf-8 -*-
import os

from devpal.config import Config


def _write_config(path, text):
    path.write_text(text, encoding="utf-8")


def test_provider_config_prefers_config_yaml_over_environment(tmp_path, monkeypatch):
    config_file = tmp_path / "config.yaml"
    _write_config(
        config_file,
        """
llm:
  default_provider: anthropic
  anthropic:
    auth_token: config-anthropic-token
    base_url: https://api.code-tab.com
    model: claude-opus-4-7
  openai:
    api_key: config-openai-key
    base_url: https://api.openai.example/v1
    model: gpt-config
anthropic:
  auth_token: legacy-config-token
  base_url: https://legacy.config
  model: legacy-model
""",
    )

    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "env-anthropic-token")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://env-anthropic.example")
    monkeypatch.setenv("OPENAI_API_KEY", "env-openai-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://env-openai.example/v1")
    monkeypatch.setenv("OPENSPEC_MODEL", "env-model")

    config = Config(str(config_file))

    anthropic = config.get_provider_config("anthropic")
    assert anthropic["auth_token"] == "config-anthropic-token"
    assert anthropic["base_url"] == "https://api.code-tab.com"
    assert anthropic["model"] == "claude-opus-4-7"
    assert config.anthropic_auth_token == "config-anthropic-token"
    assert config.anthropic_base_url == "https://api.code-tab.com"
    assert config.anthropic_model == "claude-opus-4-7"

    openai = config.get_provider_config("openai")
    assert openai["api_key"] == "config-openai-key"
    assert openai["base_url"] == "https://api.openai.example/v1"
    assert openai["model"] == "gpt-config"


def test_provider_config_uses_environment_only_when_config_is_missing(
    tmp_path, monkeypatch
):
    config_file = tmp_path / "config.yaml"
    _write_config(
        config_file,
        """
llm:
  default_provider: anthropic
  anthropic: {}
""",
    )

    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "env-anthropic-token")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://env-anthropic.example")
    monkeypatch.setenv("OPENSPEC_MODEL", "env-model")

    config = Config(str(config_file))
    anthropic = config.get_provider_config("anthropic")

    assert anthropic["auth_token"] == "env-anthropic-token"
    assert anthropic["base_url"] == "https://env-anthropic.example"
    assert anthropic["model"] == "env-model"


def test_run_ai_flow_aligns_process_env_to_config_yaml(
    tmp_path, monkeypatch
):
    config_file = tmp_path / "config.yaml"
    _write_config(
        config_file,
        """
llm:
  default_provider: anthropic
  anthropic:
    auth_token: config-anthropic-token
    base_url: https://api.code-tab.com
    model: claude-opus-4-7
""",
    )

    import devpal.config as config_module
    import run_ai_flow

    monkeypatch.setattr(config_module, "_config_instance", Config(str(config_file)))
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "stale-env-token")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "stale-env-token")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://stale.example")
    monkeypatch.setenv("OPENSPEC_MODEL", "stale-model")

    run_ai_flow._apply_env_overrides()

    assert os.environ["ANTHROPIC_AUTH_TOKEN"] == "config-anthropic-token"
    assert os.environ["ANTHROPIC_API_KEY"] == "config-anthropic-token"
    assert os.environ["ANTHROPIC_BASE_URL"] == "https://api.code-tab.com"
    assert os.environ["OPENSPEC_MODEL"] == "claude-opus-4-7"
