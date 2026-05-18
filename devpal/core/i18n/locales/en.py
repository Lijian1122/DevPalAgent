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
    "install.welcome": "Welcome to Claude Code CLI One-Click Installer",
    "install.checking_node": "Checking Node.js installation...",
    "install.node_found": "Node.js {version} found",
    "install.node_not_found": "Node.js not found. Please install Node.js first.",
    "install.node_version_low": "Node.js version too old (requires >= {min_version})",
    "install.checking_npm": "Checking npm installation...",
    "install.npm_found": "npm {version} found",
    "install.npm_missing": "npm not found",
    "install.installing": "Installing @anthropic-ai/claude-code...",
    "install.install_success": "Installation completed successfully!",
    "install.install_failed": "Installation failed: {error}",
    "install.verifying": "Verifying installation...",
    "install.verify_success": "Claude Code CLI is ready to use!",
    "install.verify_failed": "Verification failed",
    "install.config_api_key_prompt": "Configure API Key now? (y/n)",
    "install.enter_api_key": "Enter your Anthropic API Key",
    "install.api_key_saved": "API Key saved to environment",
    "install.done": "Installation complete! Run 'claude' to start",
    "install.download_node": "Opening Node.js download page...",
    "install.manual_install": "Please install Node.js manually and re-run this script",
    "install.permission_denied": "Permission denied, run as administrator",
    "install.network_error": "Network error, check your connection",
    "install.already_installed": "Claude CLI already installed: {version}",
    "install.upgrade_prompt": "New version available ({new_version}), upgrade? (y/n)",
    "install.usage": "Usage: {script_name} [--lang=zh|en]",

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
