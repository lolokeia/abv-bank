import json


def build(message: dict) -> bytes:
    """dict → JSON-байты."""
    json_str = json.dumps(message, ensure_ascii=False)
    return json_str.encode("utf-8")


def parse(data: bytes) -> dict:
    """JSON-байты → dict."""
    json_str = data.decode("utf-8")
    return json.loads(json_str)