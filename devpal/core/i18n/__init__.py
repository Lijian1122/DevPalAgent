# -*- coding: utf-8 -*-
"""
i18n (Internationalization) module for DevPalAgent

Provides multilingual support for templates and generated code.
"""

from .base import Locale, MessageCatalog, I18nContext, get_i18n_context

__all__ = [
    'Locale',
    'MessageCatalog',
    'I18nContext',
    'get_i18n_context',
]
