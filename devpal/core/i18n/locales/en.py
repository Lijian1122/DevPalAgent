# -*- coding: utf-8 -*-
"""
English (en) message catalog
"""

MESSAGES = {
    # Common
    "common.yes": "Yes",
    "common.no": "No",
    "common.success": "Success",
    "common.error": "Error",
    "common.warning": "Warning",
    "common.info": "Info",

    # Installation
    "install.title": "Claude Code CLI Installation Script",
    "install.checking_node": "Checking Node.js installation...",
    "install.node_found": "Node.js {version} found",
    "install.node_not_found": "Node.js not found. Please install Node.js first.",
    "install.checking_npm": "Checking npm installation...",
    "install.npm_found": "npm {version} found",
    "install.installing": "Installing @anthropic-ai/claude-code...",
    "install.install_success": "Installation completed successfully!",
    "install.install_failed": "Installation failed: {error}",
    "install.verifying": "Verifying installation...",
    "install.verify_success": "Claude Code CLI is ready to use!",
    "install.verify_failed": "Verification failed",

    # Project generation
    "project.creating": "Creating project structure...",
    "project.created": "Project created at {path}",
    "project.generating_code": "Generating code...",
    "project.code_generated": "Code generation completed",
    "project.running_tests": "Running tests...",
    "project.tests_passed": "All tests passed ({count}/{total})",
    "project.tests_failed": "Tests failed ({failed}/{total})",

    # Errors
    "error.file_not_found": "File not found: {path}",
    "error.permission_denied": "Permission denied: {path}",
    "error.invalid_config": "Invalid configuration: {message}",
    "error.network_error": "Network error: {message}",
}
