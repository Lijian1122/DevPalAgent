# -*- coding: utf-8 -*-
"""
MSVC / MinGW 编译器检测工具
"""

import os
from typing import Tuple, Dict, Optional


def find_visual_studio_compiler() -> Tuple[bool, str, Dict[str, str]]:
    """规范化查找 Visual Studio MSVC 编译器

    使用 vswhere 工具查找最新的 Visual Studio 安装路径，
    然后定位 vcvarsall.bat 并获取编译器环境变量。

    Returns:
        (found: bool, message: str, env: dict)
        - found: 是否找到可用编译器
        - message: 状态信息
        - env: 编译器环境变量字典（可用于 subprocess env）
    """
    if os.name != 'nt':
        return False, "非 Windows 平台", {}

    import subprocess

    # 常见 vswhere 路径
    vswhere_paths = [
        os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'),
                     'Microsoft Visual Studio', 'Installer', 'vswhere.exe'),
        os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'),
                     'Microsoft Visual Studio', 'Installer', 'vswhere.exe'),
    ]

    vswhere_path = None
    for path in vswhere_paths:
        if os.path.exists(path):
            vswhere_path = path
            break

    if not vswhere_path:
        return False, "未找到 vswhere.exe，请安装 Visual Studio 2017 或更高版本", {}

    # 使用 vswhere 查找最新的 VS 安装
    try:
        result = subprocess.run(
            [vswhere_path, '-latest', '-property', 'installationPath',
             '-products', '*', '-requires', 'Microsoft.VisualStudio.Component.VC.Tools.x86.x64'],
            capture_output=True,
            text=True,
            timeout=10
        )
        vs_install_path = result.stdout.strip()
        if not vs_install_path or result.returncode != 0:
            return False, "未找到包含 C++ 工具的 Visual Studio 安装", {}
    except Exception as e:
        return False, f"vswhere 执行失败: {str(e)}", {}

    # 查找 vcvarsall.bat
    vcvarsall_candidates = [
        os.path.join(vs_install_path, 'VC', 'Auxiliary', 'Build', 'vcvarsall.bat'),
        os.path.join(vs_install_path, 'VC', 'Auxiliary', 'Build', 'vcvars64.bat'),
        os.path.join(vs_install_path, 'Common7', 'Tools', 'VsDevCmd.bat'),
    ]

    vcvars_path = None
    for candidate in vcvarsall_candidates:
        if os.path.exists(candidate):
            vcvars_path = candidate
            break

    if not vcvars_path:
        return False, f"未找到 vcvarsall.bat，请检查 VS 安装: {vs_install_path}", {}

    # 执行 vcvarsall 并捕获环境变量
    try:
        # 使用 set 命令输出所有环境变量，然后解析
        arch = 'x64'  # 默认使用 x64
        result = subprocess.run(
            f'cmd /c ""{vcvars_path}" {arch} && set"',
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return False, f"vcvarsall.bat 执行失败: {result.stderr[:200]}", {}

        # 解析环境变量
        new_env = dict(os.environ)
        for line in result.stdout.splitlines():
            if '=' in line:
                key, value = line.split('=', 1)
                new_env[key.upper()] = value  # Windows 环境变量不区分大小写

        # 验证 cl.exe 是否在 PATH 中
        path_env = new_env.get('PATH', '')
        cl_found = False
        for path_dir in path_env.split(os.pathsep):
            cl_path = os.path.join(path_dir, 'cl.exe')
            if os.path.exists(cl_path):
                cl_found = True
                break

        if cl_found:
            vs_version = os.path.basename(vs_install_path)
            return True, f"MSVC 编译器已就绪 (VS {vs_version}, {arch})", new_env
        else:
            return False, "vcvarsall 已执行，但 PATH 中未找到 cl.exe", {}

    except Exception as e:
        return False, f"配置 MSVC 环境失败: {str(e)}", {}


def check_mingw_compiler() -> Tuple[bool, str]:
    """检查 MinGW-w64 g++ 编译器是否可用

    Returns:
        (available: bool, message: str)
    """
    import subprocess
    try:
        result = subprocess.run(
            ['g++', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.splitlines()[0] if result.stdout else 'g++'
            return True, f"MinGW-w64 编译器可用: {version_line[:50]}"
        else:
            return False, "g++ 编译器已安装但执行失败"
    except FileNotFoundError:
        return False, "未找到 g++ 编译器，请安装 MinGW-w64 并添加到 PATH"
    except Exception as e:
        return False, f"g++ 编译器检查失败: {str(e)}"


def find_vcvarsall() -> Optional[str]:
    """Find Visual Studio vcvarsall.bat location using vswhere and fallback search

    Returns:
        Path to vcvarsall.bat if found, None otherwise
    """
    import subprocess
    import winreg

    # Method 1: Use vswhere.exe (official VS locator)
    vswhere_paths = [
        r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe",
        r"C:\Program Files\Microsoft Visual Studio\Installer\vswhere.exe"
    ]
    vswhere_exe = None
    for p in vswhere_paths:
        if os.path.exists(p):
            vswhere_exe = p
            break

    if vswhere_exe:
        try:
            result = subprocess.run(
                [vswhere_exe, "-latest", "-products", "*",
                 "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                 "-property", "installationPath"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                vs_path = result.stdout.strip()
                vcvars = os.path.join(vs_path, "VC", "Auxiliary", "Build", "vcvars64.bat")
                if os.path.exists(vcvars):
                    return vcvars
                vcvars = os.path.join(vs_path, "VC", "Auxiliary", "Build", "vcvarsall.bat")
                if os.path.exists(vcvars):
                    return vcvars
        except Exception:
            pass

    # Method 2: Manual fallback search for common VS installations
    vs_years = ["2022", "2019", "2017"]
    vs_editions = ["Professional", "Community", "Enterprise", "BuildTools"]
    base_paths = [
        r"C:\Program Files (x86)\Microsoft Visual Studio",
        r"C:\Program Files\Microsoft Visual Studio"
    ]

    for base in base_paths:
        for year in vs_years:
            for edition in vs_editions:
                test_path = os.path.join(base, year, edition, "VC", "Auxiliary", "Build", "vcvars64.bat")
                if os.path.exists(test_path):
                    return test_path
                test_path = os.path.join(base, year, edition, "VC", "Auxiliary", "Build", "vcvarsall.bat")
                if os.path.exists(test_path):
                    return test_path

    # Method 3: Check VS 2015 via registry
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\VisualStudio\14.0", 0, winreg.KEY_READ)
        install_dir, _ = winreg.QueryValueEx(key, "InstallDir")
        winreg.CloseKey(key)
        vcvars = os.path.join(os.path.dirname(os.path.dirname(install_dir)), "VC", "vcvarsall.bat")
        if os.path.exists(vcvars):
            return vcvars
    except Exception:
        pass

    return None
