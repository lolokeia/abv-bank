from shared import codes
def ok(data=None):
    """Успешный ответ."""
    result = {"status": "ok"}
    if data:
        result["data"] = data
    return result

def error(code=codes.SERVER_ERROR, data=None):
    """Ответ с ошибкой."""
    result = {"status": "error", "code": code}
    if data:
        result["data"] = data
    return result

def request(action, token=None, data=None):
    result = {"action": action}
    if data:
        result["data"] = data
    if token:
        result["token"] = token
    return result