import json
from client import session
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
FILE_NAME = "client"
FILE_PATH = ROOT_DIR / f"{FILE_NAME}.json"


def load():
    try:
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        session.settings.update(data)
        print(f"[settings handler] - loaded {len(data)} keys from file")
    except Exception as e:
        print("[settings handler] - Cannot load settings from file")
        print(f"[settings handler] - Error code: {e}")


def save():
    try:
        with open(FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(session.settings, f, indent=4, ensure_ascii=False)
            print(f"[settings handler] - saved to file")
    except Exception as e:
        print("[settings handler] - Cannot save settings to file")
        print(f"[settings handler] - Error code: {e}")


def load_defaults():
    try:
        session.settings.update(session.defaults)
        print(f"[settings handler] - loaded defaults")
        save()
        
    except Exception as e:
        print("[settings handler] - Cannot load default settings")
        print(f"[settings handler] - Error code: {e}")


def init():
    try:
        session.settings.update(session.defaults)
        print("[settings handler] - loaded defaults")

        if FILE_PATH.exists():
            load()
        else:
            save()

        print("[settings handler] - Initiated settings")
    except Exception as e:
        print("[settings handler] - Cannot initialize settings file")
        print(f"[settings handler] - Error code: {e}")
