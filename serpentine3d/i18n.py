"""Interface language: English text is the key, a catalogue supplies the rest.

``tr("Save As...")`` returns the English text unchanged unless the chosen
language has an entry for it, so a string nobody has translated yet is
shown in English rather than broken. Catalogues are JSON objects in
``serpentine3d/locales/<code>.json`` mapping the English text to its
translation. Command names, aliases and the scripting API are never run
through ``tr``.

The language is read once, before the windows are built; changing it in
Settings applies at the next start.

This module imports nothing from Qt, so the catalogues can be checked
without a display.
"""

from __future__ import annotations

import json
import os

DEFAULT_LANGUAGE = "en"

# The name each language shows for itself in the Settings list.
LANGUAGE_NAMES = {
    "en": "English",
    "ja": "日本語",
}

_LOCALES_DIR = os.path.join(os.path.dirname(__file__), "locales")

_language = DEFAULT_LANGUAGE
_catalogue: dict[str, str] = {}


def available_languages() -> list[str]:
    """Language codes that can be chosen: English plus every catalogue."""
    codes = {DEFAULT_LANGUAGE}
    try:
        for name in os.listdir(_LOCALES_DIR):
            if name.endswith(".json"):
                codes.add(name[:-5])
    except OSError:
        pass
    return sorted(codes, key=lambda c: (c != DEFAULT_LANGUAGE, c))


def language_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code, code)


def load_catalogue(code: str) -> dict[str, str]:
    """The catalogue for ``code``; empty for English or when unreadable."""
    if code == DEFAULT_LANGUAGE:
        return {}
    path = os.path.join(_LOCALES_DIR, f"{code}.json")
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items()
            if isinstance(k, str) and isinstance(v, str) and v}


def set_language(code: str | None) -> str:
    """Switch to ``code``; an unknown or missing code means English.

    Returns the language actually in use.
    """
    global _language, _catalogue
    if not code or code not in available_languages():
        code = DEFAULT_LANGUAGE
    _language = code
    _catalogue = load_catalogue(code)
    return _language


def current_language() -> str:
    return _language


def tr(text: str) -> str:
    """``text`` in the current language, or ``text`` itself."""
    return _catalogue.get(text, text)


def init_from_config(cfg) -> str:
    """Pick the language the settings name. Call before building windows."""
    try:
        code = cfg.get("language", default=DEFAULT_LANGUAGE)
    except Exception:           # a damaged settings file must not stop launch
        code = DEFAULT_LANGUAGE
    return set_language(code if isinstance(code, str) else None)
