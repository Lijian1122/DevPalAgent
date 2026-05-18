# -*- coding: utf-8 -*-
"""
Tests for i18n module
"""

from pyexpat.errors import messages

import pytest
from devpal.core.i18n import Locale, MessageCatalog, I18nContext, get_i18n_context


class TestLocale:
    """Test Locale enum"""

    def test_locale_values(self):
        """Test locale enum values"""
        assert Locale.EN.value == "en"
        assert Locale.ZH.value == "zh"
        assert Locale.JA.value == "ja"
        assert Locale.KO.value == "ko"


class TestMessageCatalog:
    """Test MessageCatalog class"""

    def test_get_message(self):
        """Test getting message"""
        messages = {"test.key": "Test message"}
        catalog = MessageCatalog(Locale.EN, messages)

        assert catalog.get("test.key") == "Test message"

    def test_get_missing_key(self):
        """Test getting missing key returns key itself"""
        catalog = MessageCatalog(Locale.EN, {})

        assert catalog.get("missing.key") == "missing.key"

    def test_get_with_formatting(self):
        """Test message formatting"""
        messages = {"test.greeting": "Hello, {name}!"}
        catalog = MessageCatalog(Locale.EN, messages)

        assert catalog.get("test.greeting", name="World") == "Hello, World!"

    def test_has_key(self):
        """Test checking if key exists"""
        messages = {"test.key": "Test message"}
        catalog = MessageCatalog(Locale.EN, messages)

        assert catalog.has("test.key") is True
        assert catalog.has("missing.key") is False


class TestI18nContext:
    """Test I18nContext class"""

    def test_default_locale(self):
        """Test default locale is English"""
        ctx = I18nContext()
        assert ctx.get_locale() == Locale.EN

    def test_set_locale(self):
        """Test setting locale"""
        ctx = I18nContext()
        ctx.set_locale(Locale.ZH)
        assert ctx.get_locale() == Locale.ZH

    def test_translate_english(self):
        """Test translating to English"""
        ctx = I18nContext(Locale.EN)
        assert ctx.t("common.yes") == "Yes"
        assert ctx.t("common.no") == "No"

    def test_translate_chinese(self):
        """Test translating to Chinese"""
        ctx = I18nContext(Locale.ZH)
        assert ctx.t("common.yes") == "是"
        assert ctx.t("common.no") == "否"

    def test_translate_japanese(self):
        """Test translating to Japanese"""
        ctx = I18nContext(Locale.JA)
        assert ctx.t("common.yes") == "はい"
        assert ctx.t("common.no") == "いいえ"
        
    def test_translate_korean(self):
        """Test translating to Korean"""
        ctx = I18nContext(Locale.KO)
        assert ctx.t("common.yes") == "예"
        assert ctx.t("common.no") == "아니오"

    def test_translate_with_formatting(self):
        """Test translation with formatting"""
        ctx = I18nContext(Locale.EN)
        result = ctx.t("install.node_found", version="18.0.0")
        assert "18.0.0" in result

    def test_translate_missing_key(self):
        """Test translating missing key returns key itself"""
        ctx = I18nContext(Locale.EN)
        assert ctx.t("missing.key") == "missing.key"

    def test_fallback_to_english(self):
        """Test fallback to English for missing translations"""
        ctx = I18nContext(Locale.EN)
        # All locales should have common messages
        assert ctx.t("common.success") is not None


class TestGlobalI18nContext:
    """Test global i18n context"""

    def test_get_global_context(self):
        """Test getting global context"""
        ctx1 = get_i18n_context()
        ctx2 = get_i18n_context()
        assert ctx1 is ctx2  # Should be the same instance

    def test_set_global_locale(self):
        """Test setting global locale"""
        ctx = get_i18n_context(Locale.ZH)
        assert ctx.get_locale() == Locale.ZH


class TestInstallMessages:
    """Test installation messages"""

    def test_install_messages_english(self):
        """Test installation messages in English"""
        ctx = I18nContext(Locale.EN)

        assert "Claude Code CLI" in ctx.t("install.title")
        assert "Node.js" in ctx.t("install.checking_node")
        assert "Installing" in ctx.t("install.installing")
        assert "successfully" in ctx.t("install.install_success")

    def test_install_messages_chinese(self):
        """Test installation messages in Chinese"""
        ctx = I18nContext(Locale.ZH)

        assert "Claude Code CLI" in ctx.t("install.title")
        assert "Node.js" in ctx.t("install.checking_node")
        assert "安装" in ctx.t("install.installing")
        assert "成功" in ctx.t("install.install_success")


class TestProjectMessages:
    """Test project generation messages"""

    def test_project_messages_english(self):
        """Test project messages in English"""
        ctx = I18nContext(Locale.EN)

        assert "Creating" in ctx.t("project.creating")
        assert "Generating" in ctx.t("project.generating_code")
        assert "Running" in ctx.t("project.running_tests")

    def test_project_messages_chinese(self):
        """Test project messages in Chinese"""
        ctx = I18nContext(Locale.ZH)

        assert "创建" in ctx.t("project.creating")
        assert "生成" in ctx.t("project.generating_code")
        assert "运行" in ctx.t("project.running_tests")


class TestErrorMessages:
    """Test error messages"""

    def test_error_messages_english(self):
        """Test error messages in English"""
        ctx = I18nContext(Locale.EN)

        assert "not found" in ctx.t("error.file_not_found", path="/test/path")
        assert "denied" in ctx.t("error.permission_denied", path="/test/path")

    def test_error_messages_chinese(self):
        """Test error messages in Chinese"""
        ctx = I18nContext(Locale.ZH)

        assert "未找到" in ctx.t("error.file_not_found", path="/test/path")
        assert "拒绝" in ctx.t("error.permission_denied", path="/test/path")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
