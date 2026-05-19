# -*- coding: utf-8 -*-

from devpal.core.templates import TemplateContext, registry


def _paths_for(language: str) -> set[str]:
    context = TemplateContext(project_name=f"{language}_project", language=language)
    return {file.path for file in registry.generate_all(context)}


def test_cpp_python_and_shell_templates_are_registered_separately():
    cpp_paths = _paths_for("cpp")
    python_paths = _paths_for("python")
    shell_paths = _paths_for("shell")

    assert "CMakeLists.txt" in cpp_paths
    assert any(path.startswith("include/") for path in cpp_paths)

    assert "requirements.txt" in python_paths
    assert "src/__init__.py" in python_paths
    assert "CMakeLists.txt" not in python_paths

    assert ".gitignore" in shell_paths
    assert "README.md" in shell_paths
    assert "requirements.txt" not in shell_paths
    assert "CMakeLists.txt" not in shell_paths
