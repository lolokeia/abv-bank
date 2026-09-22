"""
Автотесты для transactions.py.
Формат ответов: response.ok() / response.error()
Баланс проверяется через db.get_bal() — не зависит от ключа в data.
Запуск: python test_transactions.py
"""
import os
import datetime
from server import db, auth, transactions

TEST_DB = "test_transactions.db"
LOG_FILE = "test_transactions_log.txt"


# ============================================================
# СЧЁТЧИКИ И ЛОГИРОВАНИЕ
# ============================================================
class TestStats:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.crashed = 0
        self.log_lines = []
        self.start_time = datetime.datetime.now()

    def log(self, message):
        print(message)
        self.log_lines.append(message)

    def check(self, name, condition):
        if condition:
            self.passed += 1
            self.log(f"✅ {name}")
        else:
            self.failed += 1
            self.log(f"❌ {name} — НЕ ПРОШЁЛ")

    def try_call(self, description, func, *args, **kwargs):
        try:
            result = func(*args, **kwargs)
            self.passed += 1
            self.log(f"✅ {description} → {result!r}")
            return result
        except Exception as e:
            self.crashed += 1
            self.log(f"💥 {description} → УПАЛ: {type(e).__name__}: {e}")
            return None

    def section(self, title):
        self.log(f"\n{'=' * 50}")
        self.log(title)
        self.log('=' * 50)

    def summary(self):
        total = self.passed + self.failed + self.crashed
        self.log(f"\n{'=' * 50}")
        self.log("ИТОГИ")
        self.log('=' * 50)
        self.log(f"✅ Пройдено:   {self.passed}")
        self.log(f"❌ Провалено:  {self.failed}")
        self.log(f"💥 Упало:      {self.crashed}")
        self.log(f"📊 Всего:      {total}")
        if total > 0:
            percent = (self.passed / total) * 100
            self.log(f"📈 Успешность: {percent:.1f}%")
        elapsed = datetime.datetime.now() - self.start_time
        self.log(f"⏱  Время:      {elapsed.total_seconds():.2f} сек")

    def write_log(self):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(f"Лог тестов от {self.start_time:%Y-%m-%d %H:%M:%S}\n")
            f.write("\n".join(self.log_lines))
        print(f"\n📝 Лог записан в {LOG_FILE}")


stats = TestStats()


# ============================================================
# ВСПОМОГАТЕЛЬНОЕ
# ============================================================
def cleanup():
    db.close()
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except PermissionError:
            print(f"⚠ Не удалось удалить {TEST_DB}")


def is_ok(response):
    return isinstance(response, dict) and response.get("status") == "ok"


def is_error(response):
    return isinstance(response, dict) and response.get("status") == "error"


def get_uuid(response):
    return response["data"]["uuid"]


def setup_user(login, name="Тест", pin="1234", balance=0):
    """Создаёт пользователя и возвращает uuid. Опционально начисляет баланс."""
    response = auth.register(login, name, pin)
    if not is_ok(response):
        return None
    uid = get_uuid(response)
    if balance > 0:
        db.update_bal(uid, balance)
    return uid


# ============================================================
# ТЕСТЫ DEPOSIT
# ============================================================
def test_deposit():
    stats.section("ТЕСТЫ: DEPOSIT (Пополнение)")

    uid = setup_user("dep_user", "Деп", "1111")
    if uid is None:
        stats.check("setup_user", False)
        return

    # 1. Успешное пополнение
    response = transactions.deposit(uid, 5000)
    stats.check("deposit 5000 → ok", is_ok(response))
    stats.check("баланс в БД = 5000", db.get_bal(uid) == 5000)

    # 2. Второе пополнение
    response = transactions.deposit(uid, 3000)
    stats.check("deposit 3000 → ok", is_ok(response))
    stats.check("баланс в БД = 8000", db.get_bal(uid) == 8000)

    # 3. Отрицательная сумма
    response = transactions.deposit(uid, -100)
    stats.check("deposit -100 → error", is_error(response))
    stats.check("баланс не изменился", db.get_bal(uid) == 8000)

    # 4. Ноль
    response = transactions.deposit(uid, 0)
    stats.check("deposit 0 → error", is_error(response))

    # 5. Не число
    response = transactions.deposit(uid, "abc")
    stats.check("deposit 'abc' → error", is_error(response))

    # 6. None
    response = transactions.deposit(uid, None)
    stats.check("deposit None → error", is_error(response))

    # 7. inf / nan
    response = transactions.deposit(uid, float("inf"))
    stats.check("deposit inf → error", is_error(response))

    response = transactions.deposit(uid, float("nan"))
    stats.check("deposit nan → error", is_error(response))

    # 8. Дробное
    response = transactions.deposit(uid, 100.5)
    stats.check("deposit 100.5 → ok", is_ok(response))
    stats.check("баланс в БД = 8100.5", db.get_bal(uid) == 8100.5)

    # 9. Проверка истории
    history = db.tr_get_all(uid)
    deposits = [tr for tr in history if tr[0] == "deposit"]
    stats.check("в истории 3 deposit", len(deposits) == 3)


# ============================================================
# ТЕСТЫ WITHDRAW
# ============================================================
def test_withdraw():
    stats.section("ТЕСТЫ: WITHDRAW (Снятие)")

    uid = setup_user("with_user", "Вит", "2222", balance=10000)

    # 1. Успешное снятие
    response = transactions.withdraw(uid, 1000)
    stats.check("withdraw 1000 → ok", is_ok(response))
    stats.check("баланс = 9000", db.get_bal(uid) == 9000)

    # 2. Снятие 500
    response = transactions.withdraw(uid, 500)
    stats.check("withdraw 500 → ok", is_ok(response))
    stats.check("баланс = 8500", db.get_bal(uid) == 8500)

    # 3. Не кратно 100
    response = transactions.withdraw(uid, 150)
    stats.check("withdraw 150 → error", is_error(response))
    stats.check("баланс не изменился", db.get_bal(uid) == 8500)

    # 4. Больше баланса
    response = transactions.withdraw(uid, 100000)
    stats.check("withdraw 100000 → error", is_error(response))
    stats.check("баланс не изменился", db.get_bal(uid) == 8500)

    # 5. Отрицательная
    response = transactions.withdraw(uid, -100)
    stats.check("withdraw -100 → error", is_error(response))

    # 6. Ноль
    response = transactions.withdraw(uid, 0)
    stats.check("withdraw 0 → error", is_error(response))

    # 7. Не число
    response = transactions.withdraw(uid, "abc")
    stats.check("withdraw 'abc' → error", is_error(response))

    # 8. Ровно весь баланс
    response = transactions.withdraw(uid, 8500)
    stats.check("withdraw 8500 → ok", is_ok(response))
    stats.check("баланс = 0", db.get_bal(uid) == 0)

    # 9. Снятие с нулевого баланса
    response = transactions.withdraw(uid, 100)
    stats.check("withdraw с 0 → error", is_error(response))

    # 10. История содержит 3 withdraw
    history = db.tr_get_all(uid)
    withdraws = [tr for tr in history if tr[0] == "withdraw"]
    stats.check("в истории 3 withdraw", len(withdraws) == 3)


# ============================================================
# ТЕСТЫ PAYMENT
# ============================================================
def test_payment():
    stats.section("ТЕСТЫ: PAYMENT (Оплата картой)")

    uid = setup_user("pay_user", "Пей", "3333", balance=10000)

    # 1. Первая оплата
    response = transactions.payment(uid)
    stats.check("payment → ok", is_ok(response))
    if is_ok(response):
        stats.check("баланс уменьшился", db.get_bal(uid) < 10000)

    # 2. С нулевым балансом
    uid_zero = setup_user("pay_zero", "Зеро", "4444", balance=0)
    response = transactions.payment(uid_zero)
    stats.check("payment с 0 → error", is_error(response))

    # 3. Очень маленький баланс
    uid_small = setup_user("pay_small", "Смол", "5555", balance=0.5)
    response = transactions.payment(uid_small)
    stats.check("payment с 0.5 → error или ok",
                is_ok(response) or is_error(response))


# ============================================================
# ТЕСТЫ TRANSFER
# ============================================================
def test_transfer():
    stats.section("ТЕСТЫ: TRANSFER (Перевод)")

    sender = setup_user("tr_sender", "Отправитель", "6666", balance=10000)
    reciver = setup_user("tr_reciver", "Получатель", "7777", balance=5000)

    # 1. Успешный перевод
    response = transactions.transfer(sender, "tr_reciver", 2000)
    stats.check("transfer 2000 → ok", is_ok(response))
    stats.check("баланс отправителя 8000", db.get_bal(sender) == 8000)
    stats.check("баланс получателя 7000", db.get_bal(reciver) == 7000)

    # 2. Перевод несуществующему
    response = transactions.transfer(sender, "no_such_user", 1000)
    stats.check("transfer несуществующему → error", is_error(response))

    # 3. Перевод себе
    response = transactions.transfer(sender, "tr_sender", 500)
    stats.check("transfer себе → error", is_error(response))

    # 4. Больше баланса
    response = transactions.transfer(sender, "tr_reciver", 100000)
    stats.check("transfer 100000 → error", is_error(response))
    stats.check("балансы не изменились",
                db.get_bal(sender) == 8000 and db.get_bal(reciver) == 7000)

    # 5. Отрицательный
    response = transactions.transfer(sender, "tr_reciver", -500)
    stats.check("transfer -500 → error", is_error(response))

    # 6. Ноль
    response = transactions.transfer(sender, "tr_reciver", 0)
    stats.check("transfer 0 → error", is_error(response))

    # 7. Не кратно 100
    response = transactions.transfer(sender, "tr_reciver", 150)
    stats.check("transfer 150 → error", is_error(response))

    # 8. Не число
    response = transactions.transfer(sender, "tr_reciver", "abc")
    stats.check("transfer 'abc' → error", is_error(response))

    # 9. Проверка истории отправителя
    sender_history = db.tr_get_all(sender)
    out = [tr for tr in sender_history if tr[0] == "transfer_send"]
    stats.check("у отправителя 1 transfer_send", len(out) == 1)

    # 10. Проверка истории получателя
    reciver_history = db.tr_get_all(reciver)
    inc = [tr for tr in reciver_history if tr[0] == "transfer_recv"]
    stats.check("у получателя 1 transfer_recv", len(inc) == 1)

    # 11. Сумма в истории правильная
    if out and inc:
        stats.check("transfer_send сумма -2000", out[0][1] == -2000)
        stats.check("transfer_recv сумма 2000", inc[0][1] == 2000)


# ============================================================
# ИСТОРИЯ
# ============================================================
def test_history():
    stats.section("ТЕСТЫ: ИСТОРИЯ")

    uid = setup_user("hist_user", "Ист", "8888", balance=1000)

    # Пустая история
    stats.check("пустая история = []", db.tr_get_all(uid) == [])

    # После операций
    transactions.deposit(uid, 1000)
    transactions.withdraw(uid, 500)
    transactions.deposit(uid, 500)

    history = db.tr_get_all(uid)
    stats.check("история = 3 записи", len(history) == 3)

    # Типы правильные
    types = [tr[0] for tr in history]
    stats.check("deposit в истории", "deposit" in types)
    stats.check("withdraw в истории", "withdraw" in types)

    # tr_get_recent
    recent = db.tr_get_recent(uid, 2)
    stats.check("tr_get_recent limit=2", len(recent) == 2)

    # Последняя транзакция — самая свежая
    stats.check("последняя — deposit 500", recent[0][1] == 500)


# ============================================================
# ГЛАВНАЯ
# ============================================================
def main():
    cleanup()

    try:
        db.connect(TEST_DB)
        db.init()

        test_deposit()
        test_withdraw()
        test_payment()
        test_transfer()
        test_history()
    except AssertionError as e:
        stats.log(f"\n💥 ТЕСТ УПАЛ С ASSERT: {e}")
    except Exception as e:
        stats.log(f"\n💥 НЕОЖИДАННАЯ ОШИБКА: {type(e).__name__}: {e}")
    finally:
        stats.summary()
        stats.write_log()
        cleanup()


if __name__ == "__main__":
    main()