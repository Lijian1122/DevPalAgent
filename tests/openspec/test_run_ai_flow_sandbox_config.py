# -*- coding: utf-8 -*-

import sys

import devpal.config
import run_ai_flow


class _FakeConfig:
    def __init__(self):
        self.config = {
            "llm": {
                "default_provider": "openai",
                "openai": {"api_key": "test-key", "model": "test-model"},
            },
            "sandbox": {
                "backend": "windows_process",
                "level": "strict",
                "phase10_workspace_execution": True,
                "low_integrity": True,
                "harden_workspace_acl": True,
                "network_deny": True,
                "restricted_token": True,
                "max_memory_mb": 512,
                "backend_options": {"runner_path": "fake-runner.exe"},
            },
        }

    def get(self, key, default=None):
        value = self.config
        for part in key.split("."):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        return value

    @property
    def llm_default_provider(self):
        return self.get("llm.default_provider", "openai")

    def get_provider_config(self, provider):
        return dict(self.get(f"llm.{provider}", {}) or {})


def test_run_ai_flow_reads_sandbox_defaults_from_config(monkeypatch):
    captured = {}
    fake_config = _FakeConfig()

    class FakeExecutor:
        def __init__(self, tool_registry):
            self.tool_registry = tool_registry

        def run(self, requirements_file, options):
            captured["requirements_file"] = requirements_file
            captured["options"] = options
            return {"success": True, "log_file": ""}

    monkeypatch.setattr(devpal.config, "get_config", lambda: fake_config)
    monkeypatch.setattr(run_ai_flow, "OpenSpecWorkflowExecutor", FakeExecutor)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_ai_flow.py",
            "-r",
            "requirements/simple_calculator.md",
            "--debug",
        ],
    )

    assert run_ai_flow.main() == 0
    options = captured["options"]
    assert options.sandbox_backend == "windows_process"
    assert options.sandbox_level == "strict"
    assert options.phase10_workspace_execution is True
    assert options.sandbox_low_integrity is True
    assert options.sandbox_harden_workspace_acl is True
    assert options.sandbox_network_deny is True
    assert options.sandbox_restricted_token is True
    assert options.sandbox_max_memory_mb == 512
    assert options.sandbox_backend_options["runner_path"] == "fake-runner.exe"
