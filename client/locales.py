import json
from client import session
import pathlib

LANG = pathlib.Path('lang')

def json_init(lang='ru_ru'):
    try:
        with open(LANG / f'{lang}.json', "r", encoding="utf-8") as f:
            data = json.load(f)
        session.state['lang'] = data
    except Exception:
        print("[locale handler] - Json has not been initialized. No localization will be used")

def loc(key):
    return session.state["lang"].get(key, key)
