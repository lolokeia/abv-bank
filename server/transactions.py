from server import db, auth
from shared import response
import math
import random





def deposit(user_uuid, amount):
    balance = db.get_bal(user_uuid)

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return response.error("Сумма не является числом!")
    if amount <= 0:
        return response.error("Сумма пополнения должна быть больше 0!")
    if not math.isfinite(amount):
        return response.error("Сумма должна быть конечным числом")
    
    new_balance = balance + amount
    db.update_bal(user_uuid, new_balance)
    db.tr_add(user_uuid, "deposit", amount, new_balance, "Пополнение баланса")
    return response.ok(f"Пополнение на {amount}Р, баланс: {new_balance}", {"uuid": user_uuid, "new_balance": new_balance})





def withdraw(user_uuid, amount):
    balance = db.get_bal(user_uuid)

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return response.error("Сумма не является числом!")
    if amount <= 0:
        return response.error("Сумма вывода должна быть больше 0!")
    if amount % 100:
        return response.error("Сумма вывода должна быть кратна 100!")
    if not math.isfinite(amount):
        return response.error("Сумма должна быть конечным числом")
    
    if amount > balance:
        return response.error(f"Сумма больше, чем есть на балансе! Не хватает {amount-balance}Р")
    new_balance = balance - amount
    db.update_bal(user_uuid, new_balance)
    db.tr_add(user_uuid, "withdraw", -amount, new_balance, "Снятие наличных", )
    return response.ok(f"Снятие {amount}Р, баланс: {new_balance}", {"uuid": user_uuid, "new_balance": new_balance})





def payment(user_uuid):
    balance = db.get_bal(user_uuid)

    if balance <= 0:
        return response.error("Ваш баланс нулевой, оплата невозможна")
    amount = round(random.uniform(1, balance * 1.5 ), 2)

    if amount > balance:
        return response.error(f"Сумма больше, чем есть на балансе! Не хватает {amount-balance}Р")
    new_balance = balance - amount
    db.update_bal(user_uuid, new_balance)
    db.tr_add(user_uuid, "payment", -amount, new_balance, "Оплата картой", )
    return response.ok(f"Оплата на {amount}Р, баланс: {new_balance}", {"uuid": user_uuid, "new_balance": new_balance})





def transfer(user_uuid, recv_login, amount):
    sender_balance = db.get_bal(user_uuid)
    reciver_uuid = db.get_user_by_login(recv_login)

    if reciver_uuid is None:
        return response.error(f"Получатель '{recv_login}' не найден")

    reciver_balance = db.get_bal(reciver_uuid)
    sender_login = db.get_login_by_uuid(user_uuid) or "неизвестно"


    if user_uuid == reciver_uuid:
        return response.error("Вы не можете перевести деньги самому себе!")
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return response.error("Сумма не является числом!")
    if amount <= 0:
        return response.error("Сумма вывода должна быть больше 0!")
    if amount % 100:
         return response.error("Сумма вывода должна быть кратна 100!")
    if not math.isfinite(amount):
         return response.error("Сумма должна быть конечным числом")

    
    if amount > sender_balance:
        return response.error(f"Сумма больше, чем есть на балансе! Не хватает {amount-sender_balance}Р")

    new_sender_balance = sender_balance - amount
    db.update_bal(user_uuid, new_sender_balance)
    db.tr_add(user_uuid, "transfer_send", -amount, new_sender_balance, f"Отправлено {recv_login}")

    new_reciver_balance = reciver_balance + amount
    db.update_bal(reciver_uuid, new_reciver_balance)
    db.tr_add(reciver_uuid, "transfer_recv", amount, new_reciver_balance, f"Получено от {sender_login}")
    return response.ok(f"Отправлено {amount}Р на баланс {recv_login}, баланс: {new_sender_balance}")


def burn(user_uuid, pin_input):
    input_hash = auth.hash_pin(pin_input)
    db_hash = db.get_pin_hash(user_uuid)
    if not auth.check_pin(pin_input, db_hash):
        return response.error("Неверный пин-код")
    balance = db.get_bal(user_uuid)
    db.update_bal(user_uuid, 0)
    db.tr_add(user_uuid, "burn", -balance, 0, "Сжигание")
    return response.ok("Баланс обнулен", {"new_balance": 0})

def get_history(user_uuid, get_recent: bool):
    if not user_uuid:
        return response.error("Пользователь не найден")
    if get_recent == True:
        transactions = db.tr_get_recent(user_uuid, 10)
        return response.ok("история последних 10 операций: ",{"transactions": transactions})
    else:
        transactions = db.tr_get_all(user_uuid)
        return response.ok("история операций: ",{ "transactions": transactions})