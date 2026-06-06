#!/usr/bin/env python3
"""Simple i18n module for the ocserv Web Manager backend.

Detects language from the Accept-Language header and loads JSON
translation files. Falls back to English when a key is missing.
"""

import json
import os

LOCALES_DIR = os.path.join(os.path.dirname(__file__), "locales")

# In-memory cache of loaded translation files
_translations: dict[str, dict[str, str]] = {}


def _load_locale(lang: str) -> dict[str, str]:
    """Load a locale JSON file, caching it in memory."""
    if lang in _translations:
        return _translations[lang]
    path = os.path.join(LOCALES_DIR, f"{lang}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            _translations[lang] = json.load(f)
    else:
        _translations[lang] = {}
    return _translations[lang]


def get_locale() -> str:
    """Detect the best locale from the Flask request's Accept-Language header."""
    # Avoid circular import by importing here (lazy)
    from flask import request
    lang = request.headers.get("Accept-Language", "en")
    # Parse the first language tag: e.g. "zh-CN,zh;q=0.9,en;q=0.8" -> "zh-CN"
    lang = lang.split(",")[0].split(";")[0].strip()
    if lang.lower().startswith("zh"):
        return "zh_CN"
    return "en"


def _(key: str, **kwargs) -> str:
    """Translate a message key into the current locale.

    Supports Python ``str.format()``-style interpolation via kwargs.
    If the key is missing from the locale file the key itself is returned.
    """
    lang = get_locale()
    translations = _load_locale(lang)
    text = translations.get(key)
    if text is None:
        # Fall back to English
        en = _load_locale("en")
        text = en.get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text
