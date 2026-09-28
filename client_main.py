from client import textlib
from shared import protocol, comms
import socket


from client_config import HOST, PORT






def response_handle(resp):
    if resp.get("status") == "ok":
        return (f"✔ - {resp.get("message")}"), resp.get("data", {})
    
    if resp.get("status") == "error":
        return (f"✖ - {resp.get("message")}"), None



def send_and_get_response(sock, action, data=None, token=None):
    request = comms.request(action, data=data, token=token,)
    protocol.send_message(sock, request)
    try:
        response = protocol.recv_message(sock)
    except socket.timeout:
        print("Время ожидания истекло")
        return None, None
    except ConnectionResetError:
        print("Хост оборвал соединение")
        return None, None

    m, r = response_handle(response)
    return m, r


    
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

token = None
balance = None

def main():
    global token
    global balance
    settings_flag = False
    sock = None
    if not sock:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((HOST, PORT))
            sock.settimeout(10)
        except socket.timeout:
            print("Истекло время ожидания")
        except Exception as e:
            print(f"Ошибка подключения к серверу: {e}")

    while True:

        if not token:
            auth_menu()
            select = input("Ввод: ")
            if select == "1":
                login_input = input("Введите логин: ")
                pin_input = input("Введите пин-код: ")
                message, r = send_and_get_response(sock, "login", {"login": login_input, "pin": pin_input})

            elif select == "2":
                login_input = input("Придумайте логин: ")
                name_input = input("Придумайте имя (или используйте своё): ")
                pin_input = input("Придумайте пин-код из четырех цифр: ")
                message, r = send_and_get_response(sock, "register", {"login": login_input, "name": name_input, "pin": pin_input})

            elif select == "0":
                sock.close()
                print("Выход...")
                exit()
            else: print("Введите корректный выбор")
            if r is not None:
                if "token" in r:
                    token = r["token"]
                if "login" in r:
                    login = r["login"]
                if "name" in r:
                    name = r["name"]
                print(message)
            else: print(message); continue


            



        message, response = send_and_get_response(sock, "get_balance", token=token)

        if response is not None:
            if "balance" in response:
                balance = response["balance"]
            else: print(message); continue

        
        print(f"Доброе время суток, {name}")
        textlib.line()
        textlib.show_balance(balance)
        main_menu()
        select = input("Ввод: ")

        if select == "1":
            amount = input("Введите сумму пополнения: ")
            message, response = send_and_get_response(sock, "deposit", {"amount": amount}, token)
            if response is not None:
                if "balance" in r:
                    balance = r["balance"]
                else: print(message); continue
            print(message)
        if select == "2":
            amount = input("Введите сумму снятия: ")
            message, response = send_and_get_response(sock, "withdraw", {"amount": amount}, token)
            if response is not None:
                if "balance" in r:
                    balance = r["balance"]
                else: print(message); continue
            print(message)
        if select == "3":
            message, response = send_and_get_response(sock, "payment", token=token)
            if response is not None:
                if "balance" in r:
                    balance = r["balance"]
                else: print(message); continue
            print(message)



        if settings_flag == True:
            settings_menu()

if __name__ == "__main__":

    main()