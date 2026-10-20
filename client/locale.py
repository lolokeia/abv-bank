import json
from client import session

JSON_PATH = "en_us.json"

def json_init():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    session.state['lang'] = data

def loc(key):
    return session.state["lang"].get(key, key)
