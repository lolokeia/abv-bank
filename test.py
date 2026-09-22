"""
Автотесты для db.py и auth.py.
Запуск: python test_autotest.py
Результаты пишутся в test_log.txt
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

    uid = auth.register("anna", "Анна", "9999")
    stats.check("register работает", uid is not None)

    stats.check("register с None пином → None",
                auth.register("lena", "Лена", None) is None)

    stats.check("Дубликат логина отклонён",
                auth.register("anna", "Анна2", "1111") is None)

    stats.check("login успешный", auth.login("anna", "9999") == uid)
    stats.check("login с неверным пином → None",
                auth.login("anna", "0000") is None)
    stats.check("login несуществующий → None",
                auth.login("ivan", "9999") is None)
    stats.check("login с None пином → None",
                auth.login("anna", None) is None)


# ============================================================
# ЖИЗНЕННЫЙ ЦИКЛ
# ============================================================
def test_user_lifecycle():
    stats.section("ТЕСТ: ЖИЗНЕННЫЙ ЦИКЛ ПОЛЬЗОВАТЕЛЯ")

    uid = auth.register("lifecycle", "Изначальное Имя", "1234")
    stats.check("Регистрация", uid is not None)

    stats.check("Вход", auth.login("lifecycle", "1234") == uid)

    db.update_name(uid, "Новое Имя")
    stats.check("Смена имени",
                db.get_name_from_id(uid) == "Новое Имя")

    db.update_login(uid, "new_login")
    stats.check("Смена логина (новый)",
                db.get_user_by_login("new_login") == uid)
    stats.check("Смена логина (старый)",
                db.get_user_by_login("lifecycle") is None)

    new_pin_hash = auth.hash_pin("5678")
    db.update_pin_hash(uid, new_pin_hash)
    stats.check("Старый пин не работает",
                auth.login("new_login", "1234") is None)
    stats.check("Новый пин работает",
                auth.login("new_login", "5678") == uid)

    stats.check("Начальный баланс 0", db.get_bal(uid) == 0)

    db.update_bal(uid, 5000)
    stats.check("Начислено 5000", db.get_bal(uid) == 5000)

    db.update_bal(uid, db.get_bal(uid) + 1500)
    stats.check("Начислено ещё 1500", db.get_bal(uid) == 6500)

    stats.check("Баланс сохраняется",
                db.get_bal(auth.login("new_login", "5678")) == 6500)

    db.tr_add(uid, "deposit", 5000, 5000, "Первое")
    db.tr_add(uid, "deposit", 1500, 6500, "Второе")
    stats.check("История 2 записи", len(db.tr_get_all(uid)) == 2)
    stats.check("Баланс не изменился от чтения истории",
                db.get_bal(uid) == 6500)


# ============================================================
# НОВЫЕ ТЕСТЫ
# ============================================================
def test_multiple_users_isolation():
    """Проверяет, что данные юзеров не смешиваются."""
    stats.section("ТЕСТ: ИЗОЛЯЦИЯ ПОЛЬЗОВАТЕЛЕЙ")

    uid_a = auth.register("iso_a", "A", "1111")
    uid_b = auth.register("iso_b", "B", "2222")

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


def test_pin_edge_cases():
    """Проверяет пин-код: длины, форматы, повторное использование."""
    stats.section("ТЕСТ: ГРАНИЧНЫЕ СЛУЧАИ ПИН-КОДА")

    # Пин должен быть 4 цифры (если ты добавил проверку)
    stats.check("Пин 'abcd' отклонён",
                auth.register("pin1", "X", "abcd") is None)
    stats.check("Пин '1' отклонён",
                auth.register("pin2", "X", "1") is None)
    stats.check("Пин '12345678' отклонён",
                auth.register("pin3", "X", "12345678") is None)
    stats.check("Пин '' отклонён",
                auth.register("pin4", "X", "") is None)

    # Валидный пин
    uid = auth.register("pin_ok", "X", "5555")
    stats.check("Пин '5555' принят", uid is not None)
    stats.check("Вход с '5555'",
                auth.login("pin_ok", "5555") == uid)

    # Один и тот же пин у двух юзеров
    uid2 = auth.register("pin_ok2", "Y", "5555")
    stats.check("Два юзера с одинаковым пином",
                uid2 is not None and uid2 != uid)
    stats.check("У обоих работает пин",
                auth.login("pin_ok", "5555") == uid and
                auth.login("pin_ok2", "5555") == uid2)

    # Хеши разные (соль работает)
    h1 = db.get_pin_hash(uid)
    h2 = db.get_pin_hash(uid2)
    stats.check("Хеши разные при одинаковом пине", h1 != h2)


def test_history_limits():
    """Проверяет работу LIMIT и сортировку."""
    stats.section("ТЕСТ: ИСТОРИЯ И LIMIT")

    uid = auth.register("hist_user", "H", "1234")

    # Пустая история
    stats.check("Пустая история = []",
                db.tr_get_all(uid) == [])

    # Добавляем 5 транзакций
    for i in range(5):
        db.tr_add(uid, "deposit", 100, 100 * (i + 1), f"T{i}")

    stats.check("Всего 5 записей", len(db.tr_get_all(uid)) == 5)
    stats.check("LIMIT 1 = 1", len(db.tr_get_recent(uid, 1)) == 1)
    stats.check("LIMIT 3 = 3", len(db.tr_get_recent(uid, 3)) == 3)
    stats.check("LIMIT 10 = 5", len(db.tr_get_recent(uid, 10)) == 5)
    stats.check("LIMIT 0 = 0", len(db.tr_get_recent(uid, 0)) == 0)

    # Проверка сортировки: последняя добавленная — первая
    recent = db.tr_get_recent(uid, 1)
    stats.check("Свежая транзакция первая",
                recent[0][3] == "T4")  # description


def test_login_types():
    """Проверяет, что login не падает на неверных типах."""
    stats.section("ТЕСТ: LOGIN С РАЗНЫМИ ТИПАМИ")

    stats.check("login(None, '1234') → None",
                auth.login(None, "1234") is None)
    stats.check("login('x', None) → None",
                auth.login("x", None) is None)
    stats.check("login(123, '1234') → None",
                auth.login(123, "1234") is None)
    stats.check("login('x', 1234) → None",
                auth.login("x", 1234) is None)
    stats.check("login('', '') → None",
                auth.login("", "") is None)


def test_stress():
    stats.section("СТРЕСС-ТЕСТ: ПОПЫТКА СЛОМАТЬ")

    # --- 1. Пустые данные ---
    stats.log("\n[1] Пустые данные")
    stats.check("Пустой логин отклонён",
                auth.register("", "Имя", "1234") is None)
    stats.check("Пустое имя отклонено",
                auth.register("login1", "", "1234") is None)
    stats.check("Пробельное имя отклонено",
                auth.register("login2", "   ", "1234") is None)
    stats.check("Пустой логин не занял место",
                db.get_user_by_login("") is None)

    # --- 2. Длинные строки ---
    stats.log("\n[2] Длинные строки")
    long_login = "A" * 10000
    uid_long = stats.try_call("Логин 10000 символов",
                              auth.register, long_login, "Имя", "1234")
    if uid_long is not None:
        stats.check("Длинный логин найден",
                    db.get_user_by_login(long_login) == uid_long)
    else:
        stats.check("Длинный логин отклонён (лимит)", True)

    # --- 3. Unicode ---
    stats.log("\n[3] Unicode и эмодзи")
    uid_emoji = auth.register("pavel🐍", "Павел😀", "1234")
    stats.check("Эмодзи в логине принят", uid_emoji is not None)
    if uid_emoji:
        stats.check("Эмодзи найден",
                    db.get_user_by_login("pavel🐍") == uid_emoji)

    # --- 4. SQL-инъекция ---
    stats.log("\n[4] SQL-инъекция")
    sqli = "pavel'; DROP TABLE Users; --"
    uid_sqli = stats.try_call("SQL-инъекция через логин",
                              auth.register, sqli, "Хакер", "1234")
    stats.check("Таблица Users жива", db.get_users_count() > 0)
    if uid_sqli:
        stats.check("Логин-инъекция сохранён как строка",
                    db.get_user_by_login(sqli) == uid_sqli)

    # --- 5. Дубликат ---
    stats.log("\n[5] Дубликат логина")
    auth.register("dup", "Первый", "1234")
    stats.check("Дубликат отклонён",
                auth.register("dup", "Второй", "5678") is None)

    # --- 6. Смена логина на занятый ---
    stats.log("\n[6] Смена логина на занятый")
    uid_a = auth.register("user_a", "A", "1111")
    auth.register("user_b", "B", "2222")
    stats.try_call("Смена на занятый",
                   db.update_login, uid_a, "user_b")
    stats.check("user_a не сломан", db.get_user(uid_a) is not None)

    # --- 7. Мусор в пине ---
    stats.log("\n[7] Мусор в пине")
    stats.check("Пин из букв",
                auth.register("badpin1", "X", "abcd") is None)
    stats.check("Пин из 1 цифры",
                auth.register("badpin2", "X", "1") is None)
    stats.check("Пин None",
                auth.register("badpin3", "X", None) is None)
    stats.check("Пин пустой",
                auth.register("badpin4", "X", "") is None)

    # --- 8. Мусор в логине ---
    stats.log("\n[8] Мусор в логине")
    stats.check("Логин с пробелами принят",
                auth.register("  spaces  ", "X", "1234") is not None)
    stats.try_call("null-байт в логине",
                   auth.register, "abc\x00def", "X", "1234")
    stats.check("Логин с переносом строки",
                auth.register("line\nbreak", "X", "1234") is not None)

    # --- 9. Баланс ---
    stats.log("\n[9] Баланс: экстремальные значения")
    uid_bal = auth.register("baltester", "B", "1234")
    db.update_bal(uid_bal, 0)
    stats.check("Баланс 0", db.get_bal(uid_bal) == 0)
    db.update_bal(uid_bal, -1000)
    stats.check("Отрицательный записан", db.get_bal(uid_bal) == -1000)
    db.update_bal(uid_bal, 10**18)
    stats.check("Огромный записан", db.get_bal(uid_bal) == 10**18)
    db.update_bal(uid_bal, 0.1 + 0.2)
    stats.check("Float-погрешность",
                abs(db.get_bal(uid_bal) - 0.3) < 1e-9)
    stats.try_call("inf", db.update_bal, uid_bal, float('inf'))
    stats.try_call("nan", db.update_bal, uid_bal, float('nan'))
    stats.try_call("строка", db.update_bal, uid_bal, "много")

    # --- 10. FK ---
    stats.log("\n[10] Транзакция для несуществующего юзера")
    stats.try_call("tr_add для fake-uuid",
                   db.tr_add, "fake-uuid", "deposit", 100, 100, "Фейк")

    # --- 11. Удаление с транзакциями ---
    stats.log("\n[11] Удаление с транзакциями")
    uid_del = auth.register("todelete", "D", "1234")
    db.tr_add(uid_del, "deposit", 500, 500, "До удаления")
    db.delete_user(uid_del)
    stats.check("Юзер удалён", db.get_user(uid_del) is None)
    stats.check("Транзакции удалены",
                len(db.tr_get_all(uid_del)) == 0)

    # --- 12. Пустой UUID ---
    stats.log("\n[12] Операции с None и ''")
    stats.check("get_user(None)", db.get_user(None) is None)
    stats.check("get_user('')", db.get_user("") is None)
    stats.check("get_bal(None) = 0", db.get_bal(None) == 0)
    stats.check("get_bal('') = 0", db.get_bal("") == 0)
    stats.check("get_name_from_id(None)",
                db.get_name_from_id(None) == "Пользователь")
    stats.check("get_pin_hash(None)",
                db.get_pin_hash(None) is None)

    # --- 13. Много транзакций ---
    stats.log("\n[13] Много транзакций")
    uid_many = auth.register("manytr", "M", "1234")
    for i in range(100):
        db.tr_add(uid_many, "deposit", 10, 10 * (i + 1), f"T{i}")
    stats.check("tr_get_recent limit=10",
                len(db.tr_get_recent(uid_many, 10)) == 10)
    stats.check("tr_get_all = 100",
                len(db.tr_get_all(uid_many)) == 100)

    # --- 14. Повторная init ---
    stats.log("\n[14] Повторная init")
    stats.try_call("db.init() x2", db.init)
    stats.check("Таблицы живы", db.get_users_count() > 0)

    # --- 15. Delete изоляция ---
    stats.log("\n[15] Delete не трогает других")
    uid_x = auth.register("del_x", "X", "1234")
    uid_y = auth.register("del_y", "Y", "1234")
    db.delete_user(uid_x)
    stats.check("X удалён", db.get_user(uid_x) is None)
    stats.check("Y на месте", db.get_user(uid_y) is not None)


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
        test_pin_edge_cases()
        test_history_limits()
        test_login_types()
        test_stress()
    except AssertionError as e:
        stats.log(f"\n💥 ТЕСТ УПАЛ С ASSERТ: {e}")
    except Exception as e:
        stats.log(f"\n💥 НЕОЖИДАННАЯ ОШИБКА: {type(e).__name__}: {e}")
    finally:
        stats.summary()
        stats.write_log()
        cleanup()


if __name__ == "__main__":
    main()