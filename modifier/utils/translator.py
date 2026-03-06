# Load translation resources and provide lookup helpers for localized UI text.
import json

import os

# Define the translator type used by this module.
# It supports application startup, packaging, or project tooling workflows.
class Translator:

    LANGUAGE_LABELS = {
        "en": "English",
        "zh": "简体中文",
    }

    def __init__(self, locale_dir, default_lang="en"):

        self.locale_dir = locale_dir

        self.default_lang = default_lang

        self.current_lang = default_lang

        self.default_translations = {}

        self.translations = {}

        self.default_translations = self._read_translation_file(default_lang)

        self.load_translations(default_lang)

    # Return the translations loaded from a locale file.
    # It supports application startup, packaging, or project tooling workflows.
    def _read_translation_file(self, lang):

        file_path = os.path.join(self.locale_dir, f"{lang}.json")

        if not os.path.exists(file_path):

            return {}

        with open(file_path, 'r', encoding='utf-8') as f:

            return json.load(f)

    # Load the translations.
    # It supports application startup, packaging, or project tooling workflows.
    def load_translations(self, lang):

        resolved_lang = self.resolve_language_code(lang)

        loaded = self._read_translation_file(resolved_lang)

        if loaded:

            self.translations = loaded

            self.current_lang = resolved_lang

        else:

            print(f"Translation file for {resolved_lang} not found.")

            self.translations = dict(self.default_translations)

            self.current_lang = self.default_lang

    # Return the translated string for the requested UI key.
    # It supports application startup, packaging, or project tooling workflows.
    def translate(self, key, default=None):

        if key in self.translations:

            return self.translations[key]

        if key in self.default_translations:

            return self.default_translations[key]

        return default if default is not None else key

    # Return the available language codes discovered in the locale directory.
    # It supports application startup, packaging, or project tooling workflows.
    def get_available_languages(self):

        if not os.path.isdir(self.locale_dir):

            return [self.default_lang]

        languages = []

        for file_name in os.listdir(self.locale_dir):

            if file_name.endswith(".json"):

                languages.append(os.path.splitext(file_name)[0])

        if self.default_lang not in languages:

            languages.append(self.default_lang)

        return sorted(set(languages))

    # Return the display label for the requested language code.
    # It supports application startup, packaging, or project tooling workflows.
    def get_language_label(self, lang):

        resolved_lang = self.resolve_language_code(lang)

        return self.LANGUAGE_LABELS.get(resolved_lang, resolved_lang.upper())

    # Return the language code for a display label or code.
    # It supports application startup, packaging, or project tooling workflows.
    def resolve_language_code(self, lang_or_label):

        if not lang_or_label:

            return self.default_lang

        normalized = str(lang_or_label).strip()

        if normalized in self.get_available_languages():

            return normalized

        for code, label in self.LANGUAGE_LABELS.items():

            if normalized == label:

                return code

        return self.default_lang

    # Set the language.
    # It supports application startup, packaging, or project tooling workflows.
    def set_language(self, lang):

        self.load_translations(self.resolve_language_code(lang))

import sys

_base_dir = getattr(
    sys,
    '_MEIPASS',
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)

_locale_dir = os.path.join(_base_dir, "i18n")

tr = Translator(_locale_dir)
