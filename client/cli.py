from client import textlib
from shared import protocol, comms, collibry
import socket


from client_config import HOST, PORT



def response_handle(resp):
    if resp.get("status") == "ok":
        return (f"✔ - {resp.get("message")}"), resp.get("data", {})
    
    if resp.get("status") == "error":
        return (f"✖ - {resp.get("message")}"), None



    
def main_menu():
    print("""
1. Пополнить счет
2. снять наличные
3. оплатить картой
4. Перевод денег
5. Сжечь все деньги
6. Настройки аккаунта
==================
0. Выйти из аккаунта
""")




def auth_menu():
    print("""
1. Войти
2. Зарегестрироваться
==================
0. Выход""")




def settings_menu():
    print("""
1. Сменить логин
2. Сменить имя
3. Сменить пин-код
==================
0. назад""")


# if __name__ == "__main__":

    # main()