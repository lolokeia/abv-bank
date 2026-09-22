"""
Автотесты для db.py и auth.py.
Формат ответов: response.ok() / response.error()
Запуск: python test_autotest.py
"""
import os
import datetime
from server import db, auth

TEST_DB = "test_autotest.db"
LOG_FILE = "test_log.txt"


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
    """Проверяет, что ответ успешный."""
    return isinstance(response, dict) and response.get("status") == "ok"


def is_error(response):
    """Проверяет, что ответ с ошибкой."""
    return isinstance(response, dict) and response.get("status") == "error"


def get_uuid(response):
    """Извлекает uuid из успешного ответа."""
    return response["data"]["uuid"]


# ============================================================
# ТЕСТЫ DB
# ============================================================
def test_db():
    stats.section("ТЕСТЫ DB")

    db.connect(TEST_DB)
    db.init()
    stats.check("Подключение и init", db.get_users_count() == 0)

    uid1 = db.create_user("pavel", "Павел", "hash1")
    stats.check("create_user возвращает UUID", uid1 is not None)

    uid_dup = db.create_user("pavel", "Павел2", "hash2")
    stats.check("Дубликат логина отклонён", uid_dup is None)

    user = db.get_user(uid1)
    stats.check("get_user возвращает запись", user is not None)
    stats.check("get_user логин верный", user[1] == "pavel")
    stats.check("get_user имя верное", user[2] == "Павел")

    stats.check("get_user_by_login находит",
                db.get_user_by_login("pavel") == uid1)
    stats.check("get_user_by_login несуществующий → None",
                db.get_user_by_login("ivan") is None)

    stats.check("get_name_from_id верный",
                db.get_name_from_id(uid1) == "Павел")
    stats.check("get_name_from_id несуществующий → 'Пользователь'",
                db.get_name_from_id("fake") == "Пользователь")

    stats.check("get_bal начальный = 0", db.get_bal(uid1) == 0)
    stats.check("get_bal несуществующий = 0",
                db.get_bal("fake") == 0)

    stats.check("get_users_count = 1", db.get_users_count() == 1)

    db.update_bal(uid1, 500)
    stats.check("update_bal работает", db.get_bal(uid1) == 500)

    db.update_name(uid1, "Павел Дубов")
    stats.check("update_name работает",
                db.get_name_from_id(uid1) == "Павел Дубов")

    db.update_login(uid1, "pavel_dubov")
    stats.check("update_login работает",
                db.get_user_by_login("pavel_dubov") == uid1)
    stats.check("Старый логин освобождён",
                db.get_user_by_login("pavel") is None)

    db.update_pin_hash(uid1, "new_hash")
    stats.check("update_pin_hash работает",
                db.get_pin_hash(uid1) == "new_hash")

    db.tr_add(uid1, "deposit", 500, 1000, "Пополнение")
    db.tr_add(uid1, "withdraw", -300, 700, "Снятие")
    stats.check("tr_get_recent limit=1",
                len(db.tr_get_recent(uid1, 1)) == 1)
    stats.check("tr_get_all = 2 записи",
                len(db.tr_get_all(uid1)) == 2)

    db.delete_user(uid1)
    stats.check("delete_user удалил", db.get_user(uid1) is None)
    stats.check("delete_user освободил логин",
                db.get_user_by_login("pavel_dubov") is None)


# ============================================================
# ТЕСТЫ AUTH
# ============================================================
def test_auth():
    stats.section("ТЕСТЫ AUTH")

    # --- Утилиты ---
    h = auth.hash_pin("1234")
    stats.check("hash_pin возвращает строку", isinstance(h, str))
    stats.check("check_pin верный → True",
                auth.check_pin("1234", h) is True)
    stats.check("check_pin неверный → False",
                auth.check_pin("5678", h) is False)

    h2 = auth.hash_pin("1234")
    stats.check("Соль уникальна (h != h2)", h != h2)
    stats.check("Второй хеш тоже валиден",
                auth.check_pin("1234", h2) is True)

    # --- Регистрация ---
    response = auth.register("anna", "Анна", "9999")
    stats.check("register → status ok", is_ok(response))
    stats.check("register → есть uuid",
                is_ok(response) and response["data"]["uuid"] is not None)

    if is_ok(response):
        uid = get_uuid(response)
    else:
        uid = None

    # --- Регистрация с None пином ---
    response = auth.register("lena", "Лена", None)
    stats.check("register с None пином → error", is_error(response))

    # --- Регистрация с пустым логином ---
    response = auth.register("", "Пустой", "1234")
    stats.check("register с пустым логином → error", is_error(response))

    # --- Регистрация с пустым именем ---
    response = auth.register("some_login", "", "1234")
    stats.check("register с пустым именем → error", is_error(response))

    # --- Дубликат логина ---
    response = auth.register("anna", "Анна2", "1111")
    stats.check("Дубликат логина → error", is_error(response))

    # --- Логин успешный ---
    response = auth.login("anna", "9999")
    stats.check("login успешный → status ok", is_ok(response))
    stats.check("login успешный → uuid совпадает",
                is_ok(response) and response["data"]["uuid"] == uid)

    # --- Логин с неверным пином ---
    response = auth.login("anna", "0000")
    stats.check("login с неверным пином → error", is_error(response))

    # --- Логин несуществующий ---
    response = auth.login("ivan", "9999")
    stats.check("login несуществующий → error", is_error(response))

    # --- Логин с None пином ---
    response = auth.login("anna", None)
    stats.check("login с None пином → error", is_error(response))

    # --- Логин с пустым логином ---
    response = auth.login("", "9999")
    stats.check("login с пустым логином → error", is_error(response))


# ============================================================
# ЖИЗНЕННЫЙ ЦИКЛ
# ============================================================
def test_user_lifecycle():
    stats.section("ТЕСТ: ЖИЗНЕННЫЙ ЦИКЛ ПОЛЬЗОВАТЕЛЯ")

    # --- Регистрация ---
    response = auth.register("lifecycle", "Изначальное Имя", "1234")
    stats.check("Регистрация → ok", is_ok(response))
    if not is_ok(response):
        return
    uid = get_uuid(response)

    # --- Вход ---
    response = auth.login("lifecycle", "1234")
    stats.check("Вход → ok", is_ok(response))
    stats.check("Вход → uuid совпадает",
                is_ok(response) and response["data"]["uuid"] == uid)

    # --- Смена имени ---
    db.update_name(uid, "Новое Имя")
    stats.check("Смена имени",
                db.get_name_from_id(uid) == "Новое Имя")

    # --- Смена логина ---
    db.update_login(uid, "new_login")
    stats.check("Смена логина (новый)",
                db.get_user_by_login("new_login") == uid)
    stats.check("Смена логина (старый)",
                db.get_user_by_login("lifecycle") is None)

    # --- Смена пина ---
    new_pin_hash = auth.hash_pin("5678")
    db.update_pin_hash(uid, new_pin_hash)

    response = auth.login("new_login", "1234")
    stats.check("Старый пин не работает", is_error(response))

    response = auth.login("new_login", "5678")
    stats.check("Новый пин работает", is_ok(response))
    stats.check("Новый пин → uuid совпадает",
                is_ok(response) and response["data"]["uuid"] == uid)

    # --- Баланс ---
    stats.check("Начальный баланс 0", db.get_bal(uid) == 0)

    db.update_bal(uid, 5000)
    stats.check("Начислено 5000", db.get_bal(uid) == 5000)

    db.update_bal(uid, db.get_bal(uid) + 1500)
    stats.check("Начислено ещё 1500", db.get_bal(uid) == 6500)

    # --- Проверка через login ---
    response = auth.login("new_login", "5678")
    if is_ok(response):
        logged_uuid = response["data"]["uuid"]
        stats.check("Баланс сохраняется после повторного входа",
                    db.get_bal(logged_uuid) == 6500)
    else:
        stats.check("Баланс сохраняется после повторного входа", False)

    # --- История ---
    db.tr_add(uid, "deposit", 5000, 5000, "Первое")
    db.tr_add(uid, "deposit", 1500, 6500, "Второе")
    stats.check("История 2 записи", len(db.tr_get_all(uid)) == 2)
    stats.check("Баланс не изменился от чтения истории",
                db.get_bal(uid) == 6500)


# ============================================================
# ИЗОЛЯЦИЯ ПОЛЬЗОВАТЕЛЕЙ
# ============================================================
def test_multiple_users_isolation():
    stats.section("ТЕСТ: ИЗОЛЯЦИЯ ПОЛЬЗОВАТЕЛЕЙ")

    response_a = auth.register("iso_a", "A", "1111")
    response_b = auth.register("iso_b", "B", "2222")

    stats.check("Регистрация A", is_ok(response_a))
    stats.check("Регистрация B", is_ok(response_b))

    if not (is_ok(response_a) and is_ok(response_b)):
        return

    uid_a = get_uuid(response_a)
    uid_b = get_uuid(response_b)

    db.update_bal(uid_a, 1000)
    db.update_bal(uid_b, 2000)

    stats.check("Баланс A = 1000", db.get_bal(uid_a) == 1000)
    stats.check("Баланс B = 2000", db.get_bal(uid_b) == 2000)

    db.tr_add(uid_a, "deposit", 1000, 1000, "Только для A")
    stats.check("История A = 1", len(db.tr_get_all(uid_a)) == 1)
    stats.check("История B = 0", len(db.tr_get_all(uid_b)) == 0)

    db.delete_user(uid_a)
    stats.check("A удалён", db.get_user(uid_a) is None)
    stats.check("B остался", db.get_user(uid_b) is not None)
    stats.check("Баланс B не тронут", db.get_bal(uid_b) == 2000)


# ============================================================
# ЛОГИН С РАЗНЫМИ ТИПАМИ
# ============================================================
def test_login_types():
    stats.section("ТЕСТ: LOGIN С РАЗНЫМИ ТИПАМИ")

    response = auth.login(None, "1234")
    stats.check("login(None, '1234') → error", is_error(response))

    response = auth.login("x", None)
    stats.check("login('x', None) → error", is_error(response))

    response = auth.login(123, "1234")
    stats.check("login(123, '1234') → error", is_error(response))

    response = auth.login("x", 1234)
    stats.check("login('x', 1234) → error", is_error(response))

    response = auth.login("", "")
    stats.check("login('', '') → error", is_error(response))


# ============================================================
# ГЛАВНАЯ
# ============================================================
def main():
    cleanup()

    try:
        test_db()
        test_auth()
        test_user_lifecycle()
        test_multiple_users_isolation()
        test_login_types()
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