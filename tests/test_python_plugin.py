# -*- coding: utf-8 -*-
"""
Tests for Python language plugin
"""

import pytest
from devpal.core.schema.languages.python_plugin import PythonLanguagePlugin


class TestPythonLanguagePlugin:
    """Test Python language plugin"""

    @pytest.fixture
    def plugin(self):
        """Create plugin instance"""
        return PythonLanguagePlugin()

    def test_language_id(self, plugin):
        """Test language ID"""
        assert plugin.get_language_id() == "python"

    def test_language_name(self, plugin):
        """Test language name"""
        assert plugin.get_language_name() == "Python"

    def test_supported_extensions(self, plugin):
        """Test supported file extensions"""
        extensions = plugin.get_supported_extensions()
        assert '.py' in extensions
        assert '.pyi' in extensions
        assert '.pyw' in extensions

    def test_build_command(self, plugin):
        """Test build command (should be empty for Python)"""
        assert plugin.get_build_command() == []

    def test_test_command(self, plugin):
        """Test test command"""
        cmd = plugin.get_test_command()
        assert "pytest" in cmd

    def test_file_structure(self, plugin):
        """Test file structure"""
        structure = plugin.get_file_structure()
        assert "src" in structure
        assert "tests" in structure
        assert "docs" in structure

    def test_package_manager(self, plugin):
        """Test package manager"""
        assert plugin.get_package_manager() == "pip"

    def test_config_file(self, plugin):
        """Test config file"""
        assert plugin.get_config_file() == "pyproject.toml"

    def test_test_framework(self, plugin):
        """Test test framework"""
        assert plugin.get_test_framework() == "pytest"

    def test_dependency_file(self, plugin):
        """Test dependency file"""
        assert plugin.get_dependency_file() == "requirements.txt"

    def test_validate_syntax_valid(self, plugin):
        """Test syntax validation with valid code"""
        valid_code = """
def hello():
    print("Hello, World!")
"""
        assert plugin.validate_syntax(valid_code) is True

    def test_validate_syntax_invalid(self, plugin):
        """Test syntax validation with invalid code"""
        invalid_code = """
def hello(
    print("Missing closing parenthesis")
"""
        assert plugin.validate_syntax(invalid_code) is False

    def test_default_imports(self, plugin):
        """Test default imports"""
        imports = plugin.get_default_imports()
        assert len(imports) > 0
        assert any("typing" in imp for imp in imports)

    def test_test_template(self, plugin):
        """Test test template"""
        template = plugin.get_test_template()
        assert "pytest" in template
        assert "class Test" in template

    def test_main_template(self, plugin):
        """Test main template"""
        template = plugin.get_main_template()
        assert "def main():" in template
        assert "if __name__ ==" in template


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
