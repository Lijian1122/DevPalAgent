# -*- coding: utf-8 -*-
"""
Python language plugin for DevPalAgent
"""

from typing import List, Dict, Optional
from pathlib import Path
from .base import LanguagePlugin


class PythonLanguagePlugin(LanguagePlugin):
    """Python language plugin"""

    def get_language_id(self) -> str:
        return "python"

    def get_language_name(self) -> str:
        return "Python"

    def get_supported_extensions(self) -> List[str]:
        return ['.py', '.pyi', '.pyw']

    def get_build_command(self) -> List[str]:
        """Python doesn't require compilation"""
        return []

    def get_test_command(self) -> List[str]:
        """Return pytest command"""
        return ["pytest", "-v", "--tb=short"]

    def get_file_structure(self) -> Dict[str, str]:
        """Python project standard structure"""
        return {
            "src": "Source code directory",
            "tests": "Test directory",
         "docs": "Documentation directory",
            "data": "Data files directory",
        ".spec": "OpenSpec artifacts",
        }

    def get_package_manager(self) -> str:
        return "pip"

    def get_config_file(self) -> str:
     return "pyproject.toml"

    def get_test_framework(self) -> str:
      return "pytest"

    def get_dependency_file(self) -> str:
        return "requirements.txt"

    def validate_syntax(self, code: str) -> bool:
        """Validate Python syntax"""
        try:
            compile(code, '<string>', 'exec')
            return True
        except SyntaxError:
            return False

    def get_default_imports(self) -> List[str]:
        """Get common Python imports"""
        return [
            "from typing import List, Dict, Optional, Any",
            "from pathlib import Path",
          "import sys",
            "import os",
        ]

    def get_test_template(self) -> str:
        """Get pytest test template"""
        return '''# -*- coding: utf-8 -*-
"""
Test module for {module_name}
"""

import pytest
from {module_name} import *


class Test{ClassName}:
    """Test class for {ClassName}"""

    def test_example(self):
        """Example test case"""
        assert True
'''

    def get_main_template(self) -> str:
        """Get Python main file template"""
        return '''# -*- coding: utf-8 -*-
"""
{project_name} - Main module
"""

import sys
from pathlib import Path

def main():
    """Main entry point"""
    print("Hello from {project_name}!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

    def is_available(self) -> bool:
        "Check if Python is available"""
        import shutil
        return shutil.which("python") is not None or shutil.which("python3") is not None

    def analyze_file(self, file_path: Path) -> Dict:
        """Analyze Python file (basic implementation)"""
        return {
            "path": str(file_path),
            "language": "python",
            "symbols": [],
            "dependencies": []
        }

    def get_symbols(self, file_path: Path) -> List[str]:
        """Get symbols from Python file (basic implementation)"""
        return []

    def get_dependencies(self, file_path: Path) -> List[str]:
        """Get dependencies from Python file (basic implementation)"""
        return []
