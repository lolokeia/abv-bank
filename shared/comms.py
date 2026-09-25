def ok(message, data=None):
    """Успешный ответ."""
    result = {"status": "ok", "message": message}
    if data:
        result["data"] = data
    return result

def error(message, code="error"):
    """Ответ с ошибкой."""
    return {"status": "error", "code": code, "message": message}

def request(action, data=None):
    result = {"action": action}
    if data:
        result["data"] = data
    return result