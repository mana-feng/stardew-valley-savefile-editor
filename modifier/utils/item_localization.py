# Keep localized item labels and save-safe English item names in sync.
from functools import lru_cache

from .translator import tr


def get_item_save_name(item_key, item_info):

    if isinstance(item_info, dict):

        return item_info.get("name", item_key)

    return str(item_info) if item_info else item_key


def _lookup_translation_value(key):

    if key in tr.translations:

        return tr.translations[key]

    if key in tr.default_translations:

        return tr.default_translations[key]

    return None


@lru_cache(maxsize=16)
def _casefold_translation_map(current_lang):

    mapping = {}

    for source in (tr.default_translations, tr.translations):

        for key, value in source.items():

            if isinstance(key, str) and isinstance(value, str):

                mapping.setdefault(key.casefold(), value)

    return mapping


def translate_item_name(name, fallback=None):

    if not name:

        return fallback if fallback is not None else ""

    candidates = [
        name,
        name.replace(" o' ", " O' "),
        name.replace(" O' ", " o' "),
        name.title(),
    ]

    seen = set()

    for candidate in candidates:

        if candidate in seen:

            continue

        seen.add(candidate)

        translated_value = _lookup_translation_value(candidate)

        if translated_value is not None:

            return translated_value

    casefold_map = _casefold_translation_map(tr.current_lang)

    translated_value = casefold_map.get(name.casefold())

    if translated_value is not None:

        return translated_value

    return fallback if fallback is not None else name


def get_localized_item_name(item_key, item_info):

    save_name = get_item_save_name(item_key, item_info)

    translated_name = translate_item_name(save_name, save_name)

    if translated_name != save_name:

        return translated_name

    return tr.translate(item_key, save_name)
