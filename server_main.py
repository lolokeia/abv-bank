from server import auth, db, tokens, transactions, cmd_handle
from shared import comms, protocol, log, collibry
from config import HOST, DB_PATH, PORT, API_VERSION
import socket
import threading
import time
import os
import sys

state = {
    "sock": None,
    "running": True,
    "restart": False,
    "debug": False,
    "clients": {},
    "lock": threading.Lock(),
    "requests_total": 0,
    "start_time": time.monotonic(),
    "uptime": 0,
    "api_ver": 9,
    "p_ip": ""
}

def handle(request):
    try:
        with state["lock"]:
            state["requests_total"] += 1

        if state["debug"]: log.info(f"request={request}")
        
        action = request.get("action")
        data = request.get("data", {})

        if action is None:
            return comms.error("bad request", "bad_request")

        if action == "register":
            login = data["login"]
            name = data["name"]
            pin = data["pin"]
            register_status = auth.register(login, name, pin)
            return register_status
        
        elif action == "login":
            login = data["login"]
            pin = data["pin"]
            login_status = auth.login(login, pin)
            return login_status

        
        token = request.get("token")
        user_uuid = tokens.resolve(token)
        if not user_uuid:
            return comms.error("Сессия истекла или недействительна", "session_expired")


        if action == "logout":
            tokens.revoke(token)
            return comms.ok("Выход выполнен")

        elif action == "get_balance":
            balance = transactions.get_balance(user_uuid)
            return balance
        
        elif action == "deposit":
            amount = data["amount"]
            deposit = transactions.deposit(user_uuid, amount)
            return deposit
        
        elif action == "withdraw":
            amount = data["amount"]
            withdraw = transactions.withdraw(user_uuid, amount)
            return withdraw

        elif action == "payment":
            amount = data.get("amount")
            payment = transactions.payment(user_uuid, amount)
            return payment
        
        elif action == "transfer":
            amount = data["amount"]
            recv_login = data["recv_login"]
            transfer = transactions.transfer(user_uuid, recv_login, amount)
            return transfer

        elif action == "burn":
            pin = data["pin"]
            burn = transactions.burn(user_uuid, pin)
            return burn
        
        elif action == "get_history":
            isrecent = data.get("isrecent")
            get_history = transactions.get_history(user_uuid, isrecent)
            return get_history


        elif action == "change_pin":
            old_pin = data["old_pin"]
            new_pin = data["new_pin"]
            change_pin = auth.change_pin(user_uuid, old_pin, new_pin)
            return change_pin
        
        elif action == "change_name":
            new_name = data["new_name"]
            change_name = auth.change_name(user_uuid, new_name)
            return change_name
            
        elif action == "change_login":
            new_login = data["new_login"]
            change_login = auth.change_login(user_uuid, new_login)
            return change_login

        else:
            return comms.error("Неверный запрос", "bad_request")

            
    except Exception as e:
        log.error(f"Error handling request: {e}")
        return comms.error(f"Возникла внутренняя ошибка при обработке запроса", "internal_error")


clients = state["clients"]
clients_lock = state["lock"]

def client_handle(conn, addr):
    try:
        with clients_lock:
            clients[conn] = addr
        while True:
           request = protocol.recv_message(conn)
           if not request: break
           response = handle(request)

           if response.get('status') == "error":
               log.warn(f"{addr} {response.get('login', '')} | {request.get('action')} >>> {response.get('status')} - {response.get('code', '')}")
           else:
               log.info(f"{addr} {response.get('login', '')} | {request.get('action')} >>> {response.get('status')}")

           protocol.send_message(conn, response)

    except ConnectionResetError:
        log.warn(f"Client connection reset: {addr}")
    except Exception as e:
        log.error(f"Error handling client: {e}")

    finally:
        conn.close()
        with clients_lock:
            clients.pop(conn, None)

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def main():
    try:
        log.logo()
        if API_VERSION != state["api_ver"]:
            log.warn(f"WARNING! API version {API_VERSION} detected. server is running on API version {state["api_ver"]}.")
            log.warn(f"This can cause instabilities and/or crashes.")
            log.warn(f"You need to confirm server start.")
            api_confirm = input(f"Confirm server start (Y/N): ")
            if api_confirm.lower() != "y":
                log.crit("Server start with API version mismatch is not confirmed. closing server...")
                state["running"] = False
                return
            else:
                log.warn("Server start with API version mismatch is confirmed. starting server...")

        log.info("Starting server...")
        db.connect(DB_PATH)
        db.init()
        log.info(f"{DB_PATH} database connected")
        count = tokens.cleanup()
        log.info(f"Cleaned up {count} expired tokens")
        public_ip = get_local_ip
        sock = socket.create_server((HOST, PORT))
        state["sock"] = sock
        sock.settimeout(1.0)
        log.info(f"Server started on {HOST}:{PORT}")
        log.info(f"You can connect via this ip address or type \"ip\" to copy ip to clipboard:")
        log.info(f"ip: {public_ip()}, port: {PORT}")
        state["p_ip"] = public_ip() + ":" + str(PORT)
        log.info(f"To see all supported commands, type HELP")
        threading.Thread(target=cmd_handle.handle, args=(state,), daemon=True).start()

        while state["running"]:
            try:
                conn, addr = sock.accept()
                log.info(f"Client connected: {addr}")

                threading.Thread(target=client_handle, args=(conn, addr), daemon=True).start()
            except socket.timeout:
                continue
            except OSError:
                break

    except KeyboardInterrupt:
        log.warn("ctrl+c detected, stopping server")
    except Exception as e:
        log.crit(f"{type(e).__name__}: {e}")
    finally:
        log.info("Closing server...")
        db.close()
        if state.get("restart"):
            log.info("Restarting...")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        else:
            if state["sock"]:
                state["sock"].close()
            log.info("server closed")
            sys.exit(0)



if __name__ == "__main__":
    main()