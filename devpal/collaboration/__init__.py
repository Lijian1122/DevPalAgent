# -*- coding: utf-8 -*-
"""AI-agnostic collaboration module for DevPalAgent.

This module provides modes and policies for collaborating with external
AI coding tools (Claude Code, Cursor, Cline) in a spec-first workflow.
"""

__version__ = "1.0.0"

from .modes import RunMode, ModePolicy, MODE_POLICIES

__all__ = ["RunMode", "ModePolicy", "MODE_POLICIES"]
