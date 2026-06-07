# -*- coding: utf-8 -*-
"""Multi-agent execution primitives for OpenSpec."""

from .adapters import agent_result_to_parallel_task_result, parallel_task_to_agent_task
from .backend import LocalThreadBackend
from .codegen_agent import CodegenAgent
from .coordinator import MultiAgentCoordinator
from .models import AgentPolicy, AgentResult, AgentTask, CommandResult, CommandSpec
from .review_agent import ReviewAgent
from .sandbox import SandboxSession
from .test_agent import TestAgent

__all__ = [
    "AgentPolicy",
    "AgentResult",
    "AgentTask",
    "CodegenAgent",
    "CommandResult",
    "CommandSpec",
    "LocalThreadBackend",
    "MultiAgentCoordinator",
    "ReviewAgent",
    "SandboxSession",
    "TestAgent",
    "agent_result_to_parallel_task_result",
    "parallel_task_to_agent_task",
]
