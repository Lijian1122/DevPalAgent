# -*- coding: utf-8 -*-
"""
Tests for installation script generator
"""

import pytest
from pathlib import Path
from devpal.core.templates import InstallScriptGenerator
from devpal.core.i18n import Locale


class TestInstallScriptGenerator:
    """Test installation script generator"""

    @pytest.fixture
    def generator(self):
        """Create generator instance"""
        return InstallScriptGenerator(locales=[Locale.EN, Locale.ZH])

    def test_generator_initialization(self, generator):
        """Test generator initialization"""
        assert len(generator.locales) == 2
        assert Locale.EN in generator.locales
        assert Locale.ZH in generator.locales
        assert len(generator.i18n_contexts) == 2

    def test_generate_bash_script(self, generator):
        """Test Bash script generation"""
        script = generator.generate_bash_script()
        assert script.startswith('#!/usr/bin/env bash')
        assert 'Claude Code CLI Installation Script' in script
        assert 'msg()' in script
        assert 'check_node()' in script

    def test_bash_script_skips_when_claude_already_installed(self, generator):
        script = generator.generate_bash_script()
        main_index = script.index('main()')
        claude_check_index = script.index('if command_exists claude; then', main_index)
        node_check_index = script.index('if ! check_node; then', main_index)
        assert claude_check_index < node_check_index
        assert 'install.already_installed' in script
        assert 'claude --version' in script

    def test_generate_batch_script(self, generator):
        """Test Batch script generation"""
        script = generator.generate_batch_script()
        script = generator.generate_batch_script()
        assert script.startswith('@echo off')
        # Simplified version for now
        assert 'Batch' in script or '@echo off' in script

    def test_generate_python_script(self, generator):
        """Test Python script generation"""
        script = generator.generate_python_script()
        assert script.startswith('#!/usr/bin/env python3')
        # Simplified version for now
        assert 'Python' in script or 'python3' in script
        assert 'Python' in script or 'python3' in script

        """Test message collection"""
        messages = generator._collect_messages()
        assert 'en' in messages
        assert 'zh' in messages
        assert 'install.welcome' in messages['en']
        assert '欢迎' in messages['zh']['install.welcome']

    def test_collect_messages_includes_already_installed(self, generator):
        messages = generator._collect_messages()
        assert 'install.already_installed' in messages['en']
        assert 'install.already_installed' in messages['zh']

    def test_generate_all(self, generator, tmp_path):
        """Test generating all scripts"""
        output_dir = tmp_path / 'scripts'
        generated_files = generator.generate_all(output_dir)
        assert len(generated_files) == 3
        assert (output_dir / 'install_claude_cli.sh').exists()
        assert (output_dir / 'install_claude_cli.bat').exists()
        assert (output_dir / 'install_claude_cli.py').exists()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
