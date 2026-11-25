import json
from client import session
import pathlib

LANG = pathlib.Path('lang')

def json_init(lang=None):
    if lang is None:
        lang = session.settings.get("language") or session.defaults["language"]

    try:
        with open(LANG / f'{lang}.json', "r", encoding="utf-8") as f:
            data = json.load(f)
        session.lang['lang'] = data
    except Exception as e:
        print("[locale handler] - Json has not been initialized. No localization will be used")
        print(f"[locale handler] - Error code: {e}")

def loc(key):
    return session.lang["lang"].get(key, key)

def clear():
    session.lang['lang'] = {}


def get_available_langs() -> dict[str, str]:
    langs_map = {}
    if not LANG.exists():
        return langs_map

    for file_path in sorted(LANG.glob("*.json")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Берем красивое имя из ключа "lang", а код из "code" (или из имени файла)
            display_name = data.get("lang", file_path.stem)
            lang_code = data.get("code", file_path.stem)
            langs_map[display_name] = lang_code
        except Exception as e:
            print(f"[locale handler] - Read Error {file_path.name}: {e}")

    return langs_map