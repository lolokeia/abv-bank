import json
import struct

def build(message: dict) -> bytes:
    """dict → JSON-байты."""
    json_str = json.dumps(message, ensure_ascii=False)
    return json_str.encode("utf-8")


def parse(data: bytes) -> dict:
    """JSON-байты → dict."""
    json_str = data.decode("utf-8")
    return json.loads(json_str)



def _recv_exact(sock, n):
    buffer = b""
    while len(buffer) < n:
        part = sock.recv(n - len(buffer))
        if part == b"":
            return None
        buffer += part
    return buffer


def send_message(sock, message: dict):
    body = build(message)
    length = len(body)
    header = struct.pack(">I", length)
    sock.sendall(header + body)



def recv_message(sock):
    header = _recv_exact(sock, 4)
    if header is None:
        return None
    length = struct.unpack(">I", header)[0]
    body = _recv_exact(sock, length)
    if body is None:
        return None
    return parse(body)