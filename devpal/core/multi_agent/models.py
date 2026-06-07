# -*- coding: utf-8 -*-
"""Data models for local multi-agent OpenSpec execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass
class CommandSpec:
    argv: List[str]
    cwd: Union[Path, str]
    timeout_seconds: int = 300
    env: Optional[Dict[str, str]] = None
    capture_output: bool = True
    text: bool = True
    encoding: Optional[str] = "utf-8"
    errors: Optional[str] = "replace"


@dataclass
class CommandResult:
    argv: List[str]
    cwd: Union[Path, str]
    returncode: int = -1
    stdout: str = ""
    stderr: str = ""
    duration_ms: int = 0
    timed_out: bool = False
    error: Optional[str] = None


@dataclass
class AgentTask:
    task_id: str
    phase_number: int
    role: str
    task_type: str
    input_payload: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    allowed_paths: List[str] = field(default_factory=list)
    allowed_tools: List[str] = field(default_factory=list)
    timeout_seconds: int = 120
    token_budget: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    task_id: str
    success: bool
    artifacts: List[Path] = field(default_factory=list)
    artifact_path: Optional[Path] = None
    patch: Optional[str] = None
    duration_ms: int = 0
    error: Optional[str] = None
    sandbox_id: str = ""
    policy_violations: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentPolicy:
    enabled: bool = False
    sandbox_level: str = "staging"
    max_concurrency: int = 1
    retry_limit: int = 0
    allowed_write_paths: List[str] = field(default_factory=list)
    allowed_tools: List[str] = field(default_factory=lambda: ["write_file"])
    timeout_seconds: int = 120
    token_budget: Optional[int] = None
    merge_strategy: str = "delta_spec"
    backend: str = "local"
    backend_options: Dict[str, Any] = field(default_factory=dict)
