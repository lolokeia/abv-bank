"""
Стресс-тест сервера ABV-BANK.

Запускает N клиентов, каждый делает M случайных операций.
Показывает статистику и не даёт серверу упасть.

Использование:
    python stress_test.py
    python stress_test.py --clients 20 --ops 500
    python stress_test.py --host 192.168.1.103 --port 9999
"""

import argparse
import random
import socket
import threading
import time
import sys

from shared import protocol
from client_config import HOST, PORT


# ---------- Общая статистика ----------
stats = {"ok": 0, "error": 0, "crash": 0}
stats_lock = threading.Lock()

# ---------- Операции ----------
OPERATIONS = [
    ("deposit",   lambda: {"amount": random.randint(1, 1000)}),
    ("withdraw",  lambda: {"amount": random.choice([100, 200, 300, 500])}),
    ("payment",   lambda: {"amount": random.randint(1, 200)}),
    ("get_balance", lambda: None),
    ("get_history", lambda: {"isrecent": random.choice([True, False])}),
]


def bump(key):
    with stats_lock:
        stats[key] += 1


def send_recv(sock, action, data=None, token=None):
    """Отправить запрос, получить ответ."""
    req = {"action": action}
    if data is not None:
        req["data"] = data
    if token is not None:
        req["token"] = token

    protocol.send_message(sock, req)
    return protocol.recv_message(sock)


def one_client(client_id, host, port, ops):
    """Один клиент. Регистрация → логин → N операций."""
    login = f"stress_{client_id}"
    pin = "0000"

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        sock.settimeout(15)

        # Регистрация (или логин, если уже есть)
        resp = send_recv(sock, "register",
                         {"login": login, "name": login, "pin": pin})
        if resp is None or resp.get("status") != "ok":
            resp = send_recv(sock, "login", {"login": login, "pin": pin})

        if resp is None or resp.get("status") != "ok":
            bump("crash")
            sock.close()
            return

        token = resp["data"]["token"]

        # Цикл операций
        for _ in range(ops):
            action, data_fn = random.choice(OPERATIONS)
            try:
                data = data_fn()
                resp = send_recv(sock, action, data=data, token=token)

                if resp is None:
                    bump("crash")
                    break

                if resp.get("status") == "ok":
                    bump("ok")
                else:
                    bump("error")

            except (socket.timeout, ConnectionResetError, OSError):
                bump("crash")
                break

        sock.close()

    except Exception:
        bump("crash")


def printer(stop_event, start_time):
    """Печатает статистику раз в секунду."""
    while not stop_event.is_set():
        time.sleep(1)
        with stats_lock:
            ok, err, cr = stats["ok"], stats["error"], stats["crash"]
        elapsed = time.time() - start_time
        total = ok + err + cr
        rate = total / elapsed if elapsed > 0 else 0
        print(f"[{elapsed:6.1f}s]  "
              f"ok={ok:6d}  error={err:5d}  crash={cr:3d}  "
              f"total={total:6d}  ({rate:.0f}/s)")
        sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(description="ABV-BANK stress test")
    parser.add_argument("--clients", type=int, default=10,
                        help="количество клиентов (по умолчанию 10)")
    parser.add_argument("--ops", type=int, default=200,
                        help="операций на клиента (по умолчанию 200)")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()

    print(f"Stress test: {args.clients} clients × {args.ops} ops")
    print(f"Target: {args.host}:{args.port}")
    print("-" * 60)

    stop_event = threading.Event()
    start_time = time.time()

    # Поток-принтер
    printer_thread = threading.Thread(
        target=printer, args=(stop_event, start_time), daemon=True)
    printer_thread.start()

    # Клиенты
    threads = []
    for i in range(args.clients):
        t = threading.Thread(
            target=one_client,
            args=(i, args.host, args.port, args.ops),
            daemon=True,
        )
        t.start()
        threads.append(t)
        time.sleep(0.05)   # небольшая пауза, чтобы не бить всё сразу

    # Ждём завершения
    for t in threads:
        t.join()

    stop_event.set()
    time.sleep(1.2)

    # Итог
    elapsed = time.time() - start_time
    total = stats["ok"] + stats["error"] + stats["crash"]
    print("-" * 60)
    print(f"Готово за {elapsed:.1f}с")
    print(f"  ok:    {stats['ok']}")
    print(f"  error: {stats['error']}")
    print(f"  crash: {stats['crash']}")
    print(f"  всего: {total}")
    if elapsed > 0:
        print(f"  средняя скорость: {total / elapsed:.0f} запросов/сек")


if __name__ == "__main__":
    main()