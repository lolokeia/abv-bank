from server import auth, db, tokens, transactions
from shared import comms, protocol
from config import HOST, DB_PATH, PORT
from shared import log
import sys
import traceback


def _excepthook(exc_type, exc_value, exc_tb):
    log.error(f"НЕОБРАБОТАННОЕ ИСКЛЮЧЕНИЕ: {exc_type.__name__}: {exc_value}")
    log.error(traceback.format_exception(exc_type, exc_value, exc_tb))


sys.excepthook = _excepthook


def handle(request):
    try:
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
        log.error(e)
        return comms.error(f"Ошибка при выполнении запроса: {e}", "bad_request")













if __name__ == "__main__":
    try:
        log.logo()
        log.info("Запуск сервера...")
        db.connect("test.db")
        db.init()
        log.info("Сервер запущен!")

        # --- Регистрация ---
        r = handle({"action": "register", "data": {"login": "a", "name": "A", "pin": "0000"}})
        if r["status"] == "ok":
            log.info(f"register: ok, login={r['data']['login']}")
            token = r["data"]["token"]           # токен не в лог
        else:
            log.warn(f"register: {r['code']}")
            token = None

        if token is None:
            log.error("нет токена, дальше идти нельзя")
            db.close()
            sys.exit(1)

        # --- Депозит ---
        r = handle({"action": "deposit", "token": token, "data": {"amount": 500}})
        if r["status"] == "ok":
            log.info(f"deposit: ok, balance={r['data']['new_balance']}")
        else:
            log.warn(f"deposit: {r['code']}")

        # --- Снятие ---
        r = handle({"action": "withdraw", "token": token, "data": {"amount": 100}})
        if r["status"] == "ok":
            log.info(f"withdraw: ok, balance={r['data']['new_balance']}")
        else:
            log.warn(f"withdraw: {r['code']}")

        # --- История ---
        r = handle({"action": "get_history", "token": token, "data": {"isrecent": True}})
        if r["status"] == "ok":
            count = len(r["data"]["transactions"])
            log.info(f"get_history: ok, {count} транзакций")
        else:
            log.warn(f"get_history: {r['code']}")

        # --- Logout ---
        r = handle({"action": "logout", "token": token})
        if r["status"] == "ok":
            log.info("logout: ok")
        else:
            log.warn(f"logout: {r['code']}")

        # --- После logout токен должен быть мёртв ---
        r = handle({"action": "deposit", "token": token, "data": {"amount": 100}})
        if r["status"] == "error" and r["code"] == "session_expired":
            log.info("после logout: session_expired — правильно")
        else:
            log.error(f"после logout ожидался session_expired, получено {r}")

        db.close()
    except Exception as e:
        log.error(f"{type(e).__name__}: {e}")