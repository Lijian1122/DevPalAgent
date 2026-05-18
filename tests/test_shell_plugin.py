# -*- coding: utf-8 -*-
"""
Tests for Shell language plugin
"""

import pytest
from devpal.core.schema.languages.shell_plugin import ShellLanguagePlugin


class TestShellLanguagePlugin:
    """Test Shell language plugin"""

    @pytest.fixture
    def plugin(self):
        """Create plugin instance"""
        return ShellLanguagePlugin()

    def test_language_id(self, plugin):
        """Test language ID"""
        assert plugin.get_language_id() == "shell"

    def test_language_name(self, plugin):
        """Test language name"""
        assert plugin.get_language_name() == "Shell Script"
    def test_supported_extensions(self, plugin):
        """Test supported file extensions"""
        extensions = plugin.get_supported_extensions()
        assert '.sh' in extensions
        assert '.bash' in extensions
        assert '.bat' in extensions
        assert '.cmd' in extensions
        assert '.ps1' in extensions

    def test_build_command(self, plugin):
        """Test build command (should be empty for shell scripts)"""
        assert plugin.get_build_command() == []

    def test_test_command(self, plugin):
        """Test test command"""
        cmd = plugin.get_test_command()
        assert "bats" in cmd

    def test_file_structure(self, plugin):
        """Test file structure"""
        structure = plugin.get_file_structure()
        assert "scripts" in structure
        assert "tests" in structure
        assert "lib" in structure

    def test_package_manager(self, plugin):
        """Test package manager"""
        assert plugin.get_package_manager() == "none"

    def test_config_file(self, plugin):
        """Test config file"""
        assert plugin.get_config_file() == "config.sh"

    def test_test_framework(self, plugin):
        """Test test framework"""
        assert plugin.get_test_framework() == "bats"

    def test_validate_syntax_valid(self, plugin):
        """Test syntax validation with valid code"""
        valid_code = """
#!/bin/bash
echo "Hello, World!"
"""
        assert plugin.validate_syntax(valid_code) is True

    def test_validate_syntax_unbalanced_parens(self, plugin):
        """Test syntax validation with unbalanced parentheses"""
        invalid_code = "if [ test ( ]; then"
        assert plugin.validate_syntax(invalid_code) is False

    def test_validate_syntax_unbalanced_braces(self, plugin):
        """Test syntax validation with unbalanced braces"""
        invalid_code = "function test { echo 'test'"
        assert plugin.validate_syntax(invalid_code) is False

    def test_validate_syntax_unbalanced_brackets(self, plugin):
        """Test syntax validation with unbalanced brackets"""
        invalid_code = "if [ test ]; then"
        assert plugin.validate_syntax(invalid_code) is True  # This is valid

    def test_bash_template(self, plugin):
        """Test Bash script template"""
        template = plugin.get_bash_template()
        assert "#!/usr/bin/env bash" in template
        assert "set -euo pipefail" in template
        assert "log_info" in template
        assert "log_error" in template

    def test_batch_template(self, plugin):
        """Test Batch script template"""
        template = plugin.get_batch_template()
        assert "@echo off" in template
        assert "setlocal" in template
        assert ":main" in template

    def test_powershell_template(self, plugin):
        """Test PowerShell script template"""
        template = plugin.get_powershell_template()
        assert "[CmdletBinding()]" in template
        assert "$ErrorActionPreference" in template
        assert "Write-Info" in template

    def test_template(self, plugin):
        """Test bats test template"""
        template = plugin.get_test_template()
        assert "#!/usr/bin/env bats" in template
        assert "setup()" in template
        assert "@test" in template

    def test_is_available_windows(self, plugin):
        """Test is_available on Windows"""
        import platform
        if platform.system() == "Windows":
          # On Windows, should check for cmd or powershell
            assert plugin.is_available() is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
