# -*- coding: utf-8 -*-
"""
CLI command to generate Claude CLI installation scripts
"""

import click
from pathlib import Path
from devpal.core.templates import InstallScriptGenerator
from devpal.core.i18n import Locale


@click.command()
@click.option('--lang', multiple=True, default=['en', 'zh'],
              type=click.Choice(['en', 'zh', 'ja', 'ko']),
              help='Target languages (default: en, zh)')
@click.option('--output-dir', default='scripts',
          type=click.Path(),
            help='Output directory (default: scripts)')
@click.option('--verbose', is_flag=True,
              help='Verbose output')
def generate_installer(lang, output_dir, verbose):
    """
    Generate Claude CLI installation scripts

    This command generates multi-language, multi-platform installation scripts
    for Claude Code CLI. The generated scripts support:

    - Bash (Linux/macOS)
    - Batch (Windows)
    - Python (cross-platform)

    Examples:

        # Generate English and Chinese scripts
        python -m devpal.cli.commands.generate_installer

        # Generate all supported languages
        python -m devpal.cli.commands.generate_installer --lang=en --lang=zh --lang=ja --lang=ko

        # Specify output directory
     python -m devpal.cli.commands.generate_installer --output-dir=dist/scripts
     """
    try:
        # Convert language codes to Locale enums
        locales = []
        for lang_code in lang:
            try:
                locales.append(Locale(lang_code))
            except ValueError:
                click.echo(f"Warning: Unsupported language '{lang_code}', skipping", err=True)

        if not locales:
            click.echo("Error: No valid languages specified", err=True)
            return 1

        if verbose:
            click.echo(f"Generating installation scripts for: {', '.join([l.value for l in locales])}")
            click.echo(f"Output directory: {output_dir}")

        # Create generator
        generator = InstallScriptGenerator(locales=locales)

        # Generate scripts
        output_path = Path(output_dir)
        generated_files = generator.generate_all(output_path)

        # Report results
        click.echo(f"\n✓ Successfully generated {len(generated_files)} installation scripts:")
        for file_path in generated_files:
            click.echo(f"  - {file_path}")

        click.echo(f"\nUsage:")
        click.echo(f"  Bash:   bash {output_path}/install_claude_cli.sh [--lang=en|zh]")
        click.echo(f"  Batch:  {output_path}\\install_claude_cli.bat [--lang=en|zh]")
        click.echo(f"  Python: python {output_path}/install_claude_cli.py [--lang=en|zh]")

        return 0

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    generate_installer()
