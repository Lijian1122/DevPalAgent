# -*- coding: utf-8 -*-

from devpal.core.sandbox.env_profiles import build_env_profile, infer_env_profile


def test_env_profile_filters_secret_like_keys():
    env = {
        "PATH": "safe-path",
        "SystemRoot": "C:\\Windows",
        "OPENAI_API_KEY": "secret",
        "ANTHROPIC_AUTH_TOKEN": "secret",
        "CUSTOM_PASSWORD": "secret",
        "DEVPAL_SAFE_ENV": "ok",
    }

    result = build_env_profile(["python", "-m", "pytest"], env=env)

    assert result["PATH"] == "safe-path"
    assert result["SystemRoot"] == "C:\\Windows"
    assert result["DEVPAL_SAFE_ENV"] == "ok"
    assert "OPENAI_API_KEY" not in result
    assert "ANTHROPIC_AUTH_TOKEN" not in result
    assert "CUSTOM_PASSWORD" not in result


def test_env_profile_keeps_msvc_toolchain_keys():
    env = {
        "PATH": "cl-path",
        "INCLUDE": "include-path",
        "LIB": "lib-path",
        "VCToolsInstallDir": "vc-tools",
        "WindowsSdkDir": "sdk",
        "OPENAI_API_KEY": "secret",
    }

    result = build_env_profile(["cmake", "--build", "build"], env=env)

    assert infer_env_profile(["cmake"], env) == "cpp-msvc"
    assert result["INCLUDE"] == "include-path"
    assert result["LIB"] == "lib-path"
    assert result["VCToolsInstallDir"] == "vc-tools"
    assert result["WindowsSdkDir"] == "sdk"
    assert "OPENAI_API_KEY" not in result


def test_generic_profile_drops_unlisted_variables():
    env = {
        "PATH": "safe-path",
        "RANDOM_APP_SETTING": "drop-me",
        "DEVPAL_TRACE": "keep-me",
    }

    result = build_env_profile(["python", "-c", "print(1)"], env=env, profile="generic-minimal")

    assert result["PATH"] == "safe-path"
    assert result["DEVPAL_TRACE"] == "keep-me"
    assert "RANDOM_APP_SETTING" not in result
