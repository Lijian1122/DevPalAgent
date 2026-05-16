# -*- coding: utf-8 -*-
"""Unified OpenSpec workflow execution facade."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

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
    verbose: bool = False
    debug: bool = False


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
        return EnhancedOpenSpecScheduler(
            requirements_file=str(Path(requirements_file)),
            tool_registry=self.tool_registry,
            abort_on_critical_failure=opts.abort_on_critical_failure,
            enable_timeout=opts.enable_timeout,
            enable_retry=opts.enable_retry,
            enable_checkpoint=opts.enable_checkpoint,
            enable_progress=opts.enable_progress,
            force_regenerate_code=opts.force_regenerate_code,
        )
