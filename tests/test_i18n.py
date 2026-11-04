"""Interface language: lookup, fallback, and the Japanese catalogue."""

import ast
import json
import os
import re

import pytest

from serpentine3d import i18n

ROOT = os.path.join(os.path.dirname(__file__), "..", "serpentine3d")


@pytest.fixture(autouse=True)
def _english_after():
    yield
    i18n.set_language("en")


def _literal(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _translated_literals(relpath):
    """Plain strings the program passes to tr(), a menu action or a page."""
    with open(os.path.join(ROOT, relpath), encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    found = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = fn.id if isinstance(fn, ast.Name) else (
            fn.attr if isinstance(fn, ast.Attribute) else "")
        if name == "tr" and node.args and _literal(node.args[0]):
            found.add(_literal(node.args[0]))
        elif name == "_action" and len(node.args) > 1 and _literal(node.args[1]):
            found.add(_literal(node.args[1]))
        elif name in ("_page", "_section"):
            for arg in node.args[:2]:
                if _literal(arg):
                    found.add(_literal(arg))
    return found


def test_english_is_the_default_and_returns_the_text_unchanged():
    assert i18n.set_language("en") == "en"
    assert i18n.tr("Save As...") == "Save As..."


def test_japanese_translates_known_text():
    assert i18n.set_language("ja") == "ja"
    assert i18n.tr("Save") == "保存"
    assert i18n.tr("&File") == "ファイル(&F)"


def test_untranslated_text_falls_back_to_english():
    i18n.set_language("ja")
    assert i18n.tr("A string no catalogue has") == "A string no catalogue has"


def test_unknown_language_means_english():
    assert i18n.set_language("xx") == "en"
    assert i18n.tr("Save") == "Save"
    assert i18n.set_language(None) == "en"


def test_available_languages_lists_english_first_then_catalogues():
    langs = i18n.available_languages()
    assert langs[0] == "en"
    assert "ja" in langs


def test_init_from_config_survives_a_damaged_setting():
    class Broken:
        def get(self, *a, **k):
            raise RuntimeError("damaged settings")

    class Odd:
        def get(self, *a, **k):
            return 42

    assert i18n.init_from_config(Broken()) == "en"
    assert i18n.init_from_config(Odd()) == "en"

    class Japanese:
        def get(self, *a, **k):
            return "ja"

    assert i18n.init_from_config(Japanese()) == "ja"


def test_every_catalogue_entry_is_usable():
    for code in i18n.available_languages():
        if code == "en":
            continue
        path = os.path.join(ROOT, "locales", f"{code}.json")
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        assert isinstance(data, dict)
        for key, value in data.items():
            assert isinstance(value, str) and value.strip(), key
            # A menu mnemonic in the English text must survive translation.
            if re.match(r"^&\w", key):
                assert "(&" in value or "&" in value, key
            # Markup and format fields must match the source.
            assert re.findall(r"<[^>]+>", key) == re.findall(r"<[^>]+>", value), key
            assert sorted(re.findall(r"\{[^}]*\}", key)) == \
                sorted(re.findall(r"\{[^}]*\}", value)), key


@pytest.mark.parametrize("relpath", ["app.py", "ui/settings_dialog.py"])
def test_japanese_covers_every_translated_literal(relpath):
    catalogue = i18n.load_catalogue("ja")
    missing = sorted(s for s in _translated_literals(relpath)
                     if s not in catalogue)
    assert not missing, f"no Japanese for: {missing}"


def test_command_names_are_never_translated():
    """Scripting names and aliases stay English in every language."""
    catalogue = i18n.load_catalogue("ja")
    for word in ("loft", "sweep2", "booleanunion", "filletedge"):
        assert word not in catalogue
