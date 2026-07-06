# -*- coding: utf-8 -*-
"""Unified OpenSpec workflow execution facade."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from ..collaboration.modes import RunMode
from .openspec_phases.enhanced_scheduler import EnhancedOpenSpecScheduler


@dataclass(frozen=True)
class OpenSpecRunOptions:
    abort_on_critical_failure: bool = True
    enable_timeout: bool = True
    enable_retry: bool = True
    enable_checkpoint: bool = True
    enable_progress: bool = True
    resume: bool = False
    force_regenerate_code: bool = True
    vector_retrieval_enabled: bool = False
    vector_persist_dir: Optional[str] = None
    vector_top_k: int = 5
    vector_prefer_chroma: bool = True
    max_concurrency: int = 3
    enable_multi_agent: bool = False
    sandbox_level: str = "staging"
    sandbox_backend: str = "policy"
    sandbox_backend_options: Optional[Dict[str, Any]] = None
    phase10_workspace_execution: bool = False
    sandbox_low_integrity: bool = False
    sandbox_harden_workspace_acl: bool = False
    sandbox_network_deny: bool = False
    sandbox_restricted_token: bool = False
    sandbox_max_memory_mb: Optional[int] = None
    agent_pool_size: Optional[int] = None
    verbose: bool = False
    debug: bool = False
    run_mode: RunMode = RunMode.FULL
    change_id: Optional[str] = None


class OpenSpecWorkflowExecutor:
    """Single facade for running the current enhanced 11-phase OpenSpec workflow."""

    def __init__(self, tool_registry: Any):
        self.tool_registry = tool_registry

    def run(self, requirements_file: str, options: OpenSpecRunOptions | None = None) -> Dict[str, Any]:
        opts = options or OpenSpecRunOptions()
        scheduler = self.create_scheduler(requirements_file, opts)
        return scheduler.run_all_phases(resume=opts.resume)

    def create_scheduler(self, requirements_file: str, options: OpenSpecRunOptions | None = None) -> EnhancedOpenSpecScheduler:
        opts = options or OpenSpecRunOptions()
        sandbox_backend_options = dict(opts.sandbox_backend_options or {})
        if opts.phase10_workspace_execution:
            sandbox_backend_options["phase10_workspace_execution"] = True
        if opts.sandbox_low_integrity:
            sandbox_backend_options["low_integrity"] = True
        if opts.sandbox_harden_workspace_acl:
            sandbox_backend_options["harden_workspace_acl"] = True
        if opts.sandbox_network_deny:
            sandbox_backend_options["network_deny"] = True
        if opts.sandbox_restricted_token:
            sandbox_backend_options["restricted_token"] = True
        if opts.sandbox_max_memory_mb is not None:
            sandbox_backend_options["max_memory_mb"] = int(opts.sandbox_max_memory_mb)
        return EnhancedOpenSpecScheduler(
            requirements_file=str(Path(requirements_file)),
            tool_registry=self.tool_registry,
            abort_on_critical_failure=opts.abort_on_critical_failure,
            enable_timeout=opts.enable_timeout,
            enable_retry=opts.enable_retry,
            enable_checkpoint=opts.enable_checkpoint,
            enable_progress=opts.enable_progress,
            force_regenerate_code=opts.force_regenerate_code,
            vector_retrieval_enabled=opts.vector_retrieval_enabled,
            vector_persist_dir=opts.vector_persist_dir,
            vector_top_k=opts.vector_top_k,
            vector_prefer_chroma=opts.vector_prefer_chroma,
            max_concurrency=opts.max_concurrency,
            enable_multi_agent=opts.enable_multi_agent,
            sandbox_level=opts.sandbox_level,
            sandbox_backend=opts.sandbox_backend,
            sandbox_backend_options=sandbox_backend_options,
            agent_pool_size=opts.agent_pool_size,
            verbose=opts.verbose,
            debug=opts.debug,
            run_mode=opts.run_mode,
            change_id=opts.change_id,
        )
