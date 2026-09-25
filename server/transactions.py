from server import db, auth
from shared import comms
import math
import random





def deposit(user_uuid, amount):
    balance = db.get_bal(user_uuid)

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return comms.error("Сумма не является числом!", "wrong_amount")
    if amount <= 0:
        return comms.error("Сумма пополнения должна быть больше 0!", "wrong_amount")
    if not math.isfinite(amount):
        return comms.error("Сумма должна быть конечным числом", "wrong_amount")
    
    new_balance = balance + amount
    db.update_bal(user_uuid, new_balance)
    db.tr_add(user_uuid, "deposit", amount, new_balance, "Пополнение баланса")
    return comms.ok(f"Пополнение на {amount}Р, баланс: {new_balance}", {"new_balance": new_balance})





def withdraw(user_uuid, amount):
    balance = db.get_bal(user_uuid)

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return comms.error("Сумма не является числом!", "wrong_amount")
    if amount <= 0:
        return comms.error("Сумма вывода должна быть больше 0!", "wrong_amount")
    if amount % 100:
        return comms.error("Сумма вывода должна быть кратна 100!", "wrong_amount")
    if not math.isfinite(amount):
        return comms.error("Сумма должна быть конечным числом", "wrong_amount")
    
    if amount > balance:
        return comms.error(f"Сумма больше, чем есть на балансе! Не хватает {amount-balance}Р", "insufficient_funds")
    new_balance = balance - amount
    db.update_bal(user_uuid, new_balance)
    db.tr_add(user_uuid, "withdraw", -amount, new_balance, "Снятие наличных")
    return comms.ok(f"Снятие {amount}Р, баланс: {new_balance}", {"new_balance": new_balance})





def payment(user_uuid, amount=None):
    balance = db.get_bal(user_uuid)
    if amount is None:
        amount = round(random.uniform(1, balance * 1.5 ), 2)

    try: amount = float(amount)
    except ValueError: return comms.error("Сумма не является числом, оплата невозможна", "wrong_amount")

    if balance <= 0:
        return comms.error("Ваш баланс нулевой, оплата невозможна", "insufficient funds")
    if amount <= 0:
            return comms.error("Сумма оплаты отрицательна, оплата невозможна", "wrong_amount")

    if amount > balance:
        return comms.error(f"Сумма больше, чем есть на балансе! Не хватает {amount-balance}Р", "insufficient funds")
    new_balance = balance - amount
    db.update_bal(user_uuid, new_balance)
    db.tr_add(user_uuid, "payment", -amount, new_balance, "Оплата картой")
    return comms.ok(f"Оплата на {amount}Р, баланс: {new_balance}", {"new_balance": new_balance})





def transfer(user_uuid, recv_login, amount):
    sender_balance = db.get_bal(user_uuid)
    reciver_uuid = db.get_user_by_login(recv_login)

    if reciver_uuid is None:
        return comms.error(f"Получатель '{recv_login}' не найден", "user_not_found")

    reciver_balance = db.get_bal(reciver_uuid)
    sender_login = db.get_login_by_uuid(user_uuid) or "неизвестно"


    if user_uuid == reciver_uuid:
        return comms.error("Вы не можете перевести деньги самому себе!", "self_transfer")
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return comms.error("Сумма не является числом!", "wrong_amount")
    if amount <= 0:
        return comms.error("Сумма вывода должна быть больше 0!", "wrong_amount")
    if amount % 100:
         return comms.error("Сумма вывода должна быть кратна 100!", "wrong_amount")
    if not math.isfinite(amount):
         return comms.error("Сумма должна быть конечным числом", "wrong_amount")

    
    if amount > sender_balance:
        return comms.error(f"Сумма больше, чем есть на балансе! Не хватает {amount-sender_balance}Р", "insufficient funds")

    new_sender_balance = sender_balance - amount
    db.update_bal(user_uuid, new_sender_balance)
    db.tr_add(user_uuid, "transfer_send", -amount, new_sender_balance, f"Отправлено {recv_login}")

    new_reciver_balance = reciver_balance + amount
    db.update_bal(reciver_uuid, new_reciver_balance)
    db.tr_add(reciver_uuid, "transfer_recv", amount, new_reciver_balance, f"Получено от {sender_login}")
    return comms.ok(f"Отправлено {amount}Р на баланс {recv_login}, баланс: {new_sender_balance}")


def burn(user_uuid, pin_input):
    db_hash = db.get_pin_hash(user_uuid)
    if pin_input is None:
        return comms.error("Пин не введён", "pin_is_empty")
    if not auth.check_pin(pin_input, db_hash):
        return comms.error("Неверный пин-код", "wrong_pin")
    balance = db.get_bal(user_uuid)
    db.update_bal(user_uuid, 0)
    db.tr_add(user_uuid, "burn", -balance, 0, "Сжигание")
    return comms.ok("Баланс обнулен", {"new_balance": 0})

def get_history(user_uuid, get_recent: bool):
    if not user_uuid:
        return comms.error("Пользователь не найден", "user_not_found")
    if get_recent == True:
        transactions = db.tr_get_recent(user_uuid, 10)
        return comms.ok("история последних 10 операций: ",{"transactions": transactions})
    else:
        transactions = db.tr_get_all(user_uuid)
        return comms.ok("история операций: ",{ "transactions": transactions})