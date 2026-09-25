# test_atm.py

from server import db, auth
from shared import comms
from shared import protocol

def clear():
    print("\n" * 3)


def show_response(response):
    """Показывает ответ пользователю."""
    if response["status"] == "ok":
        print(f"✅ {response['message']}")
        if "data" in response:
            for key, value in response["data"].items():
                print(f"   {key}: {value}")
    else:
        print(f"❌ {response['message']}")


def menu():
    print("1. сменить логин")
    print("2. сменить пин")
    print("3. сменить имя")
    print("0. Выход из аккаунта")
def auth_menu():
    print("1. войти")
    print("2. зарегестрироваться")
    print("3. выйти из банкомата")

def main():
    # Подключение к БД
    db.connect("test_atm.db")
    db.init()

    session = {}  # здесь храним user_uuid
    print("Добро пожаловать в АБВ-БАНК!")
    while True:
        if not session:
            auth_menu()
            choice = input("Выбор: ")
            if choice == "1":
                login = input("Введите ваш логин: ")
                pin_input = input("Введите ваш пин-код: ")
                response = auth.login(login, pin_input)
                show_response(response)
                if response["status"] == "ok":
                    session["user_uuid"] = response["data"]["uuid"]
                else: 
                    response["status"] = None; continue

            elif choice == "2":
                login = input("Придумайте Логин: ")
                name = input("придумайте Имя: ")
                pin = input("придумайте Пин (4 цифры): ")
                response = auth.register(login, name, pin)
                show_response(response)
                if response["status"] == "ok":
                    session["user_uuid"] = response["data"]["uuid"]
                else: continue

            elif choice == "3":
                print("Выход...")
                db.close()
                exit()
            else:
                print("Неверный выбор!"); continue

        
        # Если залогинен — показываем баланс
        if "user_uuid" in session:
            user_uuid = session["user_uuid"]
            balance = db.get_bal(user_uuid)
            name = db.get_name_from_id(user_uuid)
            print(f"\n👤 {name} | 💰 {balance} ₽")

        menu()
        raw = protocol.build({"action": "login", "login": "pavel"})
        message = protocol.parse(raw)
        print(message, raw)
        choice = input("\nВыбор: ").strip()

        # === Пополнение ===
        if choice == "1":
            if "user_uuid" not in session:
                print("❌ Сначала войдите")
            else:
                new_login = input("введите новый логин: ")
                response = auth.change_login(session["user_uuid"], new_login)
                show_response(response)

        # === Снятие ===
        elif choice == "2":
            if "user_uuid" not in session:
                print("❌ Сначала войдите")
            else:
                old_pin = input("Введите старый пин: ")
                new_pin = input("введите новый пин: ")
                response = auth.change_pin(session["user_uuid"], old_pin, new_pin)
                show_response(response)

        # === История ===
        elif choice == "3":
            if "user_uuid" not in session:
                print("❌ Сначала войдите")
            else:
                new_name = input("введите новое имя: ")
                response = auth.change_name(session["user_uuid"], new_name)
                show_response(response)
        

        # === Выход ===
        elif choice == "0":
            session = {}
            continue

        else:
            print("❌ Неверный выбор")

        input("\nНажмите Enter...")


main()