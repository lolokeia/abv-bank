# test_atm.py

from server import db, auth
from shared import response


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
    print("1. Пополнить")
    print("2. Снять")
    print("3. История")
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
                else: response["status"] = None; continue

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
        choice = input("\nВыбор: ").strip()

        # # === Пополнение ===
        # elif choice == "3":
        #     if "user_uuid" not in session:
        #         print("❌ Сначала войдите")
        #     else:
        #         amount = float(input("Сумма: "))
        #         response = transactions.deposit(session["user_uuid"], amount)
        #         show_response(response)

        # # === Снятие ===
        # elif choice == "4":
        #     if "user_uuid" not in session:
        #         print("❌ Сначала войдите")
        #     else:
        #         amount = float(input("Сумма: "))
        #         response = transactions.withdraw(session["user_uuid"], amount)
        #         show_response(response)

        # === История ===
        if choice == "5":
            if "user_uuid" not in session:
                print("❌ Сначала войдите")
            else:
                history = db.tr_get_recent(session["user_uuid"], 10)
                print("\n📜 Последние операции:")
                for tr in history:
                    type_, amount, balance_after, desc, date = tr
                    sign = "+" if amount > 0 else ""
                    print(f"   {date} | {sign}{amount} ₽ | баланс: {balance_after} ₽ | {desc}")

        # === Выход ===
        elif choice == "0":
            session = None
            continue

        else:
            print("❌ Неверный выбор")

        input("\nНажмите Enter...")


main()