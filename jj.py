import time
import socket
from client import logic, session as se
import client_config as config
from shared import log

log.log_init()

def generate_100_accounts():
    print("=== СТАРТ ГЕНЕРАЦИИ 100 АККАУНТОВ ===")

    # 1. Подключаемся к серверу (как в client_main)
    print("[1/3] Подключение к серверу...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((config.HOST, config.PORT))
        se.state['sock'] = sock
        print("      Успешно подключено!")
    except Exception as e:
        print(f"      [ОШИБКА] Не удалось подключиться: {e}")
        return

    # 2. Авторизация (ОБЯЗАТЕЛЬНО замени на свой логин и пин от тестового аккаунта!)
    print("[2/3] Авторизация...")
    test_login = "my"  # <-- ВПИШИ СВОЙ ЛОГИН
    test_pin = "1234"        # <-- ВПИШИ СВОЙ ПИН

    resp = logic.login(test_login, test_pin)
    
    if resp and resp.get("status") == "ok":
        se.state['token'] = resp['data'].get('token')
        se.state['login'] = test_login
        se.state['pin'] = test_pin
        se.state['name'] = resp['data'].get('name')
        print(f"      Успешный вход. Привет, {se.state['name']}!")
    else:
        print(f"      [ОШИБКА] Не удалось войти. Ответ сервера: {resp}")
        return

    # 3. Генерация
    print("[3/3] Начинаем создание аккаунтов...")
    success_count = 0
    
    for i in range(1, 1001):
        acc_name = f"Stress_Test_{i}"
        
        # Вызываем функцию логики (предполагается, что она называется create_acc)
        # Если у тебя она называется по-другому — замени здесь
        resp = logic.create_acc(acc_name)
        
        if resp and resp.get("status") == "ok":
            success_count += 1
            print(f"  [+] Создан: {acc_name}")
        else:
            print(f"  [-] Ошибка при создании {acc_name}: {resp}")

        # Небольшая пауза, чтобы не забить канал и не словить таймаут
        time.sleep(0.1)

    print("=== ЗАВЕРШЕНО ===")
    print(f"Успешно создано аккаунтов: {success_count} / 100")
    print("Теперь можешь зайти в клиент и нажать 'Обновить' на главном экране.")

if __name__ == "__main__":
    generate_100_accounts()