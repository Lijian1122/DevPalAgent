# -*- coding: utf-8 -*-
"""
Tests for installation script generator
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
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
        assert 'set -euo pipefail' in script
        assert 'msg()' in script
        assert 'check_node()' in script
        assert 'check_npm()' in script
        assert 'command_exists claude' in script
        assert 'claude_works()' in script
        assert 'claude --version >/dev/null 2>&1' in script
        assert 'download_lts_node()' in script
        assert 'NODE_VERSION="${NODE_VERSION:-v24.15.0}"' in script
        assert 'https://nodejs.org/dist/$NODE_VERSION/' in script
        assert 'latest/' not in script
        assert 'NPM_INSTALL_TIMEOUT_SECONDS="${NPM_INSTALL_TIMEOUT_SECONDS:-120}"' in script
        assert 'run_with_timeout npm install -g @anthropic-ai/claude-code' in script
        assert '--registry="$NPM_MIRROR_REGISTRY"' in script
        assert 'https://registry.npmmirror.com' in script
        assert 'verify_installation()' in script

    def test_bash_script_skips_when_claude_already_installed(self, generator):
        script = generator.generate_bash_script()
        main_index = script.index('main()')
        claude_check_index = script.index('if claude_works; then', main_index)
        node_check_index = script.index('if ! check_node; then', main_index)
        assert claude_check_index < node_check_index
        assert 'install.already_installed' in script
        assert 'claude --version' in script

    def test_generate_batch_script(self, generator):
        """Test Batch script generation"""
        script = generator.generate_batch_script()
        assert script.startswith('@echo off')
        assert 'setlocal' in script
        assert 'where node' in script
        assert 'where npm' in script
        assert 'where claude' in script
        assert ':claude_works' in script
        assert 'call claude --version >nul 2>nul' in script
        assert ':install_local_node' in script
        assert 'call powershell' in script
        assert 'NODE_VERSION=v24.15.0' in script
        assert "https://nodejs.org/dist/' + $version + '/'" in script
        assert 'latest/' not in script
        assert 'NPM_INSTALL_TIMEOUT_SECONDS=120' in script
        assert ':run_npm_with_timeout' in script
        assert "'--registry=' + $env:NPM_MIRROR_REGISTRY" in script
        assert 'https://registry.npmmirror.com' in script
        assert 'exit /b 1' in script
        assert 'exit /b 0' in script

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
        assert len(generated_files) == 2
        assert (output_dir / 'install_claude_cli.sh').exists()
        assert (output_dir / 'install_claude_cli.bat').exists()
        assert not (output_dir / 'install_claude_cli.py').exists()

    def test_current_platform_installer_script_runs_with_fake_tools(self, generator, tmp_path):
        output_dir = tmp_path / 'scripts'
        fake_bin = tmp_path / 'fake_bin'
        fake_bin.mkdir()
        generator.generate_all(output_dir)

        env = os.environ.copy()

        if os.name == 'nt':
            system_root = env.get('SystemRoot', r'C:\Windows')
            env['PATH'] = os.pathsep.join([
                str(fake_bin),
                str(Path(system_root) / 'System32'),
                system_root,
            ])
            (fake_bin / 'node.bat').write_text('@echo off\r\nexit /b 0\r\n', encoding='utf-8')
            (fake_bin / 'npm.bat').write_text(
                '@echo off\r\n'
                '> "%~dp0claude.bat" echo @echo off\r\n'
                '>> "%~dp0claude.bat" echo echo claude-code 1.0.0\r\n'
                'exit /b 0\r\n',
                encoding='utf-8',
            )
            (fake_bin / 'powershell.bat').write_text('@echo off\r\ncall npm install -g @anthropic-ai/claude-code\r\nexit /b %ERRORLEVEL%\r\n', encoding='utf-8')
            result = subprocess.run(
                ['cmd.exe', '/c', str(output_dir / 'install_claude_cli.bat')],
                cwd=tmp_path,
                env=env,
                text=True,
                capture_output=True,
                timeout=30,
            )
            assert result.returncode == 0, result.stdout + result.stderr
            assert 'Claude Code CLI is available' in result.stdout
            assert (fake_bin / 'claude.bat').exists()
        else:
            env['PATH'] = str(fake_bin)
            node = fake_bin / 'node'
            npm = fake_bin / 'npm'
            node.write_text('#!/usr/bin/env sh\nexit 0\n', encoding='utf-8')
            npm.write_text(
                '#!/usr/bin/env sh\n'
                'DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"\n'
                'printf "#!/usr/bin/env sh\\necho claude-code 1.0.0\\n" > "$DIR/claude"\n'
                'chmod +x "$DIR/claude"\n'
                'exit 0\n',
                encoding='utf-8',
            )
            node.chmod(0o755)
            npm.chmod(0o755)
            result = subprocess.run(
                ['bash', str(output_dir / 'install_claude_cli.sh')],
                cwd=tmp_path,
                env=env,
                text=True,
                capture_output=True,
                timeout=30,
            )
            assert result.returncode == 0, result.stdout + result.stderr
            assert (fake_bin / 'claude').exists()

    @pytest.mark.skipif(os.name != 'nt', reason='Windows batch smoke test')
    def test_windows_batch_reinstalls_when_claude_shim_is_broken(self, generator, tmp_path):
        output_dir = tmp_path / 'scripts'
        fake_bin = tmp_path / 'fake_bin'
        fake_bin.mkdir()
        generator.generate_all(output_dir)

        system_root = os.environ.get('SystemRoot', r'C:\Windows')
        env = os.environ.copy()
        env['PATH'] = os.pathsep.join([
            str(fake_bin),
            str(Path(system_root) / 'System32'),
            system_root,
        ])
        (fake_bin / 'claude.bat').write_text('@echo off\r\nexit /b 1\r\n', encoding='utf-8')
        (fake_bin / 'node.bat').write_text('@echo off\r\nexit /b 0\r\n', encoding='utf-8')
        (fake_bin / 'npm.bat').write_text(
            '@echo off\r\n'
            '> "%~dp0claude.bat" echo @echo off\r\n'
            '>> "%~dp0claude.bat" echo echo claude-code 1.0.0\r\n'
            'exit /b 0\r\n',
            encoding='utf-8',
        )
        (fake_bin / 'powershell.bat').write_text('@echo off\r\ncall npm install -g @anthropic-ai/claude-code\r\nexit /b %ERRORLEVEL%\r\n', encoding='utf-8')

        result = subprocess.run(
            ['cmd.exe', '/c', str(output_dir / 'install_claude_cli.bat')],
            cwd=tmp_path,
            env=env,
            text=True,
            capture_output=True,
            timeout=30,
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert 'already installed' not in result.stdout
        assert 'Installing Claude Code CLI' in result.stdout
        assert 'Claude Code CLI is available' in result.stdout

    @pytest.mark.skipif(os.name != 'nt', reason='Windows batch bootstrap smoke test')
    def test_windows_batch_bootstraps_local_node_and_retries_with_mirror(self, generator, tmp_path):
        output_dir = tmp_path / 'scripts'
        fake_bin = tmp_path / 'fake_bin'
        fake_bin.mkdir()
        generator.generate_all(output_dir)

        system_root = os.environ.get('SystemRoot', r'C:\Windows')
        env = os.environ.copy()
        env['PATH'] = os.pathsep.join([
            str(fake_bin),
            str(Path(system_root) / 'System32'),
            system_root,
        ])

        helper = tmp_path / 'fake_powershell.py'
        helper.write_text(
            "from pathlib import Path\n"
            "root = Path.cwd()\n"
            "current = root / '.nodejs' / 'current'\n"
            "current.mkdir(parents=True, exist_ok=True)\n"
            "(current / 'node.exe').write_text('fake node\\n', encoding='utf-8')\n"
            "(current / 'npm.bat').write_text("
            "'@echo off\\r\\n'"
            "+ 'echo %* >> \"' + str(root / 'npm_calls.txt') + '\"\\r\\n'"
            "+ 'echo %* | findstr /C:\"--registry=https://registry.npmmirror.com\" >nul\\r\\n'"
            "+ 'if errorlevel 1 exit /b 1\\r\\n'"
            "+ '> \"%~dp0claude.bat\" echo @echo off\\r\\n'"
            "+ '>> \"%~dp0claude.bat\" echo echo claude-code 1.0.0\\r\\n'"
            "+ 'exit /b 0\\r\\n', encoding='utf-8')\n",
            encoding='utf-8',
        )
        (fake_bin / 'powershell.bat').write_text(
            '@echo off\r\n'
            'echo %* | findstr /C:"nodejs.org" >nul\r\n'
            'if not errorlevel 1 (\r\n'
            f'  "{sys.executable}" "{helper}"\r\n'
            '  exit /b %ERRORLEVEL%\r\n'
            ')\r\n'
            'echo %* | findstr /C:"--registry=" >nul\r\n'
            'if errorlevel 1 (\r\n'
            '  call npm install -g @anthropic-ai/claude-code\r\n'
            '  exit /b 124\r\n'
            ')\r\n'
            'call npm install -g @anthropic-ai/claude-code --registry=https://registry.npmmirror.com\r\n'
            'exit /b %ERRORLEVEL%\r\n',
            encoding='utf-8',
        )

        result = subprocess.run(
            ['cmd.exe', '/c', str(output_dir / 'install_claude_cli.bat')],
            cwd=tmp_path,
            env=env,
            text=True,
            capture_output=True,
            timeout=30,
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert 'Node.js not found; installing Node.js v24.15.0' in result.stdout
        assert 'retrying with npm mirror' in result.stdout
        assert 'Claude Code CLI is available' in result.stdout
        assert (tmp_path / '.nodejs' / 'current' / 'node.exe').exists()
        assert (tmp_path / '.nodejs' / 'current' / 'claude.bat').exists()
        npm_calls = (tmp_path / 'npm_calls.txt').read_text(encoding='utf-8')
        assert '--registry=https://registry.npmmirror.com' in npm_calls


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
