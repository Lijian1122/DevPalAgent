# -*- coding: utf-8 -*-
"""Environment allowlist profiles for sandboxed command execution."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Iterable, Mapping, Optional


SENSITIVE_ENV_TOKENS = (
    "API",
    "AUTH",
    "CLAUDE",
    "CODEX",
    "CREDENTIAL",
    "KEY",
    "OPENAI",
    "PASSWORD",
    "SECRET",
    "TOKEN",
)

_COMMON_ENV_KEYS = {
    "ALLUSERSPROFILE",
    "APPDATA",
    "COMSPEC",
    "COMMONPROGRAMFILES",
    "COMMONPROGRAMFILES(X86)",
    "COMMONPROGRAMW6432",
    "HOMEDRIVE",
    "HOMEPATH",
    "LOCALAPPDATA",
    "NUMBER_OF_PROCESSORS",
    "OS",
    "PATH",
    "PATHEXT",
    "PROCESSOR_ARCHITECTURE",
    "PROCESSOR_IDENTIFIER",
    "PROCESSOR_LEVEL",
    "PROCESSOR_REVISION",
    "PROGRAMDATA",
    "PROGRAMFILES",
    "PROGRAMFILES(X86)",
    "PROGRAMW6432",
    "SYSTEMDRIVE",
    "SYSTEMROOT",
    "TEMP",
    "TMP",
    "USERDOMAIN",
    "USERNAME",
    "USERPROFILE",
    "WINDIR",
}

_PYTHON_ENV_KEYS = {
    "PYTHONHOME",
    "PYTHONPATH",
    "PYTHONIOENCODING",
    "PYTHONUTF8",
    "VIRTUAL_ENV",
}

_CPP_MSVC_ENV_KEYS = {
    "__DOTNET_ADD_64BIT",
    "__DOTNET_PREFERRED_BITNESS",
    "__VSCMD_PREINIT_PATH",
    "COMMANDPROMPTTYPE",
    "DEVENVDIR",
    "EXTERNAL_INCLUDE",
    "FRAMEWORK40VERSION",
    "FRAMEWORKDIR",
    "FRAMEWORKDIR64",
    "FRAMEWORKVERSION",
    "FRAMEWORKVERSION64",
    "INCLUDE",
    "LIB",
    "LIBPATH",
    "NETFXSDKDIR",
    "PLATFORM",
    "UCRTVERSION",
    "UNIVERSALCRTSDKDIR",
    "VCIDEINSTALLDIR",
    "VCINSTALLDIR",
    "VCPKG_ROOT",
    "VCTOOLSINSTALLDIR",
    "VCTOOLSREDISTDIR",
    "VCTOOLSVERSION",
    "VISUALSTUDIOVERSION",
    "VSAPPIDDIR",
    "VSAPPIDNAME",
    "VSINSTALLDIR",
    "VSCMD_ARG_APP_PLAT",
    "VSCMD_ARG_HOST_ARCH",
    "VSCMD_ARG_TGT_ARCH",
    "VSCMD_VER",
    "WINDOWSLIBPATH",
    "WINDOWSSDKDIR",
    "WINDOWSSDKLIBVERSION",
    "WINDOWSSDKVERSION",
}

_CPP_MSVC_PREFIXES = (
    "VS",
    "VSCMD_",
    "VC",
    "VCTOOLS",
    "WINDOWSSDK",
)

_SAFE_PREFIXES = (
    "CMAKE_",
    "DEVPAL_",
)


def infer_env_profile(argv: Iterable[str], env: Optional[Mapping[str, str]] = None) -> str:
    argv_list = [str(item) for item in argv]
    executable = Path(argv_list[0]).name.lower() if argv_list else ""
    env_upper = {str(key).upper(): str(value) for key, value in dict(env or {}).items()}

    if executable in {"cmake", "cmake.exe", "cl", "cl.exe", "nmake", "nmake.exe"}:
        return "cpp-msvc" if _looks_like_msvc_env(env_upper) else "generic-build"
    if executable in {"python", "python.exe", "pytest", "pytest.exe"}:
        return "python-pytest"
    return "generic-minimal"


def build_env_profile(
    argv: Iterable[str],
    env: Optional[Mapping[str, str]] = None,
    *,
    base_env: Optional[Mapping[str, str]] = None,
    profile: Optional[str] = None,
) -> Dict[str, str]:
    source = dict((base_env or os.environ) if env is None else env)
    selected_profile = profile or infer_env_profile(argv, source)
    allowed = _allowed_keys_for_profile(selected_profile)
    result: Dict[str, str] = {}

    for key, value in source.items():
        key_text = str(key)
        key_upper = key_text.upper()
        if _is_sensitive_env_key(key_upper):
            continue
        if value is None:
            continue
        if key_upper in allowed or _has_allowed_prefix(key_upper, selected_profile):
            result[key_text] = str(value)
    return result


def _allowed_keys_for_profile(profile: str) -> set[str]:
    if profile == "cpp-msvc":
        return set(_COMMON_ENV_KEYS | _CPP_MSVC_ENV_KEYS)
    if profile == "python-pytest":
        return set(_COMMON_ENV_KEYS | _PYTHON_ENV_KEYS)
    if profile == "generic-build":
        return set(_COMMON_ENV_KEYS | {"CMAKE_GENERATOR", "CMAKE_BUILD_PARALLEL_LEVEL"})
    return set(_COMMON_ENV_KEYS)


def _has_allowed_prefix(key_upper: str, profile: str) -> bool:
    if key_upper.startswith(_SAFE_PREFIXES):
        return True
    if profile == "cpp-msvc" and key_upper.startswith(_CPP_MSVC_PREFIXES):
        return True
    return False


def _is_sensitive_env_key(key_upper: str) -> bool:
    return any(token in key_upper for token in SENSITIVE_ENV_TOKENS)


def _looks_like_msvc_env(env_upper: Mapping[str, str]) -> bool:
    return bool(
        env_upper.get("VCTOOLSINSTALLDIR")
        or env_upper.get("VCINSTALLDIR")
        or env_upper.get("VSINSTALLDIR")
        or env_upper.get("INCLUDE") and env_upper.get("LIB")
    )


def build_current_env_profile(argv: Iterable[str]) -> Dict[str, str]:
    return build_env_profile(argv, env=os.environ)
