import json
import os

class Translator:
    def __init__(self, locale_dir, default_lang="zh"):
        self.locale_dir = locale_dir
        self.current_lang = default_lang
        self.translations = {}
        self.load_translations(default_lang)

    def load_translations(self, lang):
        file_path = os.path.join(self.locale_dir, f"{lang}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
            self.current_lang = lang
        else:
            print(f"Translation file for {lang} not found.")

    def translate(self, key, default=None):
        return self.translations.get(key, default if default is not None else key)

    def set_language(self, lang):
        self.load_translations(lang)

# Global translator instance
import sys
if getattr(sys, 'frozen', False):
    _base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # type: ignore
else:
    _base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_locale_dir = os.path.join(_base_dir, "i18n")
tr = Translator(_locale_dir)
