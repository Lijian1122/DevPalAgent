# -*- coding: utf-8 -*-
"""
Shell script language plugin for DevPalAgent
"""

from typing import List, Dict, Optional
from pathlib import Path
from .base import LanguagePlugin


class ShellLanguagePlugin(LanguagePlugin):
    """Shell script language plugin (Bash/Batch/PowerShell)"""

    def get_language_id(self) -> str:
        return "shell"

    def get_language_name(self) -> str:
        return "Shell Script"

    def get_supported_extensions(self) -> List[str]:
        return [".sh", ".bash", ".bat", ".cmd", ".ps1"]

    def get_build_command(self) -> List[str]:
        """Shell scripts don't require compilation"""
        return []

    def get_test_command(self) -> List[str]:
        """Shell script testing (bats or shunit2)"""
        return ["bats", "tests/"]

    def get_file_structure(self) -> Dict[str, str]:
        """Shell script project structure"""
        return {
            "scripts": "Shell scripts directory",
            "tests": "Test scripts directory",
            "docs": "Documentation directory",
            "lib": "Library scripts directory",
            ".spec": "OpenSpec artifacts",
        }

    def get_package_manager(self) -> str:
        return "none"  # Shell scripts typically don't use package managers

    def get_config_file(self) -> str:
        return "config.sh"

    def get_test_framework(self) -> str:
        return "bats"  # Bash Automated Testing System

    def validate_syntax(self, code: str) -> bool:
        """Basic shell script syntax validation"""
        # Check for common syntax errors
        if code.count("(") != code.count(")"):
            return False
        if code.count("{") != code.count("}"):
            return False
        if code.count("[") != code.count("]"):
            return False
        return True

    def get_bash_template(self) -> str:
        """Get Bash script template"""
        return """#!/usr/bin/env bash
# {script_name} - {description}
#
# Usage: {script_name} [options]

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'  # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Main function
main() {
    log_info "Starting {script_name}..."

    # Your code here

    log_info "Completed successfully!"
    return 0
}

# Run main function
main "$@"
"""

    def get_batch_template(self) -> str:
        """Get Windows Batch script template"""
        return """@echo off
REM {script_name} - {description}
REM
REM Usage: {script_name} [options]

setlocal enabledelayedexpansion

REM Script directory
set "SCRIPT_DIR=%~dp0"

REM Main function
:main
    echo [INFO] Starting {script_name}...

    REM Your code here

    echo [INFO] Completed successfully!
    exit /b 0

REM Run main
call :main %*
"""

    def get_powershell_template(self) -> str:
        """Get PowerShell script template"""
        return """# {script_name} - {description}
#
# Usage: {script_name} [options]

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

# Script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Logging functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-ErrorMsg {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-WarningMsg {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

# Main function
function Main {
    Write-Info "Starting {script_name}..."

    # Your code here

    Write-Info "Completed successfully!"
    return 0
}

# Run main function
try {
    $exitCode = Main
    exit $exitCode
}
catch {
    Write-ErrorMsg $_.Exception.Message
    exit 1
}
"""

    def get_test_template(self) -> str:
        """Get bats test template"""
        return """#!/usr/bin/env bats
# Test suite for {script_name}

setup() {
    # Setup test environment
    export TEST_DIR="$(cd "$(dirname "$BATS_TEST_FILENAME")" && pwd)"
    export SCRIPT_DIR="$TEST_DIR/../scripts"
}

teardown() {
    # Cleanup after tests
    :
}

@test "{script_name}: basic functionality" {
    run bash "$SCRIPT_DIR/{script_name}"
    [ "$status" -eq 0 ]
}

@test "{script_name}: handles errors gracefully" {
    run bash "$SCRIPT_DIR/{script_name}" --invalid-option
    [ "$status" -ne 0 ]
}
"""
    def is_available(self) -> bool:
        """Check if shell is available"""
        import shutil
        import platform

        # On Windows, check for cmd.exe or PowerShell
        if platform.system() == "Windows":
            return shutil.which("cmd") is not None or shutil.which("powershell") is not None

        # On Unix-like systems, check for bash or sh
        return shutil.which("bash") is not None or shutil.which("sh") is not None
    def analyze_file(self, file_path: Path) -> Dict:
        """Analyze shell script file (basic implementation)"""
        return {
            "path": str(file_path),
        "language": "shell",
         "symbols": [],
          "dependencies": []
        }

    def get_symbols(self, file_path: Path) -> List[str]:
        """Get symbols from shell script (basic implementation)"""
        return []

    def get_dependencies(self, file_path: Path) -> List[str]:
        """Get dependencies from shell script (basic implementation)"""
        return []
