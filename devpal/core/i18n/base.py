# -*- coding: utf-8 -*-
"""
i18n base classes and utilities
"""

from enum import Enum
from typing import Dict, Optional, Any
from pathlib import Path


class Locale(Enum):
    """Supported locales"""
    EN = "en"  # English
    ZH = "zh"  # Chinese (Simplified)
    JA = "ja"  # Japanese
    KO = "ko"  # Korean


class MessageCatalog:
    """Message catalog for a specific locale"""

    def __init__(self, locale: Locale, messages: Dict[str, str]):
        self.locale = locale
        self.messages = messages

    def get(self, key: str, **kwargs) -> str:
        """Get translated message with optional formatting"""
        message = self.messages.get(key, key)
        if kwargs:
            try:
                return message.format(**kwargs)
            except KeyError:
                return message
        return message

    def has(self, key: str) -> bool:
        """Check if message key exists"""
        return key in self.messages


class I18nContext:
    """i18n context for template rendering"""

    def __init__(self, locale: Locale = Locale.EN):
        self.locale = locale
        self._catalogs: Dict[Locale, MessageCatalog] = {}
        self._load_catalogs()

    def _load_catalogs(self):
        """Load message catalogs for all locales"""
        from .locales import en, zh, ja, ko

        self._catalogs[Locale.EN] = MessageCatalog(Locale.EN, en.MESSAGES)
        self._catalogs[Locale.ZH] = MessageCatalog(Locale.ZH, zh.MESSAGES)
        self._catalogs[Locale.JA] = MessageCatalog(Locale.JA, ja.MESSAGES)
        self._catalogs[Locale.KO] = MessageCatalog(Locale.KO, ko.MESSAGES)

    def t(self, key: str, **kwargs) -> str:
        """Translate message key to current locale"""
        catalog = self._catalogs.get(self.locale)
        if not catalog:
         # Fallback to English
            catalog = self._catalogs.get(Locale.EN)

        if catalog:
            return catalog.get(key, **kwargs)
        return key

    def set_locale(self, locale: Locale):
        """Change current locale"""
        self.locale = locale

    def get_locale(self) -> Locale:
        """Get current locale"""
        return self.locale


# Global i18n context instance
_global_i18n_context: Optional[I18nContext] = None


def get_i18n_context(locale: Optional[Locale] = None) -> I18nContext:
    """Get or create global i18n context"""
    global _global_i18n_context

    if _global_i18n_context is None:
        _global_i18n_context = I18nContext(locale or Locale.EN)
    elif locale is not None:
        _global_i18n_context.set_locale(locale)

    return _global_i18n_context
