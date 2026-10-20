from server import db, auth, luhn
from shared import comms, codes
import math
import random






def deposit(acc_uuid, amount):
    balance = db.get_bal(acc_uuid)
    user_uuid = db.get_user_by_acc_uuid(acc_uuid)
    try:
        amount = int(amount)
    except (ValueError, TypeError):
        return comms.error(codes.AMOUNT_NOT_DIGIT)
    if amount <= 0:
        return comms.error(codes.AMOUNT_NEGATIVE)
    
    new_balance = balance + amount
    db.update_bal(acc_uuid, new_balance)
    db.tr_add(user_uuid, acc_uuid, "deposit", amount, new_balance, "Пополнение баланса")
    return comms.ok(data={"new_balance": new_balance})





def withdraw(acc_uuid, amount):
    balance = db.get_bal(acc_uuid)
    user_uuid = db.get_user_by_acc_uuid(acc_uuid)

    try:
        amount = int(amount)
    except (ValueError, TypeError):
        return comms.error(codes.AMOUNT_NOT_DIGIT)
    if amount <= 0:
        return comms.error(codes.AMOUNT_NEGATIVE)
    if amount % 100:
        return comms.error(codes.AMOUNT_NOT_MUL_100)
    
    if amount > balance:
        return comms.error(codes.BALANCE_INSUFFICIENT, data={"balance": balance, "amount": amount})
    
    new_balance = balance - amount
    db.update_bal(acc_uuid, new_balance)
    db.tr_add(user_uuid, acc_uuid, "withdraw", -amount, new_balance, "Снятие наличных")
    return comms.ok(data={"new_balance": new_balance})





def payment(acc_uuid, amount=None):
    user_uuid = db.get_user_by_acc_uuid(acc_uuid)
    balance = db.get_bal(acc_uuid)

    if amount is None:
        amount = round(random.uniform(1, balance * 1.5 ), 2)

    try: amount = int(amount)
    except (ValueError, TypeError): return comms.error(codes.AMOUNT_NOT_DIGIT)

    if balance <= 0:
        return comms.error(codes.BALANCE_NEGATIVE)
    if amount <= 0:
            return comms.error(codes.AMOUNT_NEGATIVE)

    if amount > balance:
        return comms.error(codes.BALANCE_INSUFFICIENT)

    new_balance = balance - amount
    db.update_bal(acc_uuid, new_balance)
    db.tr_add(user_uuid, acc_uuid, "payment", -amount, new_balance, "Оплата картой")
    return comms.ok(data={"new_balance": new_balance})





def transfer(acc_uuid, recv_num, amount):

    user_uuid = db.get_user_by_acc_uuid(acc_uuid)
    sender_balance = db.get_bal(acc_uuid)

    if luhn.check_checksum(recv_num) == False:
        return comms.error(codes.TRANSFER_NUM_WRONG)
    
    recv_acc = db.get_uuid_by_num(recv_num)

    reciver_uuid = db.get_user_by_acc_uuid(recv_acc)
    if reciver_uuid is None:
        return comms.error(codes.TRANSFER_RECV_NOT_FOUND)


    recv_login = db.get_login_by_uuid(reciver_uuid)
    reciver_balance = db.get_bal(recv_acc)
    sender_login = db.get_login_by_uuid(user_uuid) or "unknown"


    if user_uuid == reciver_uuid:
        return comms.error(codes.TRANSFER_SELF)
    try:
        amount = int(amount)
    except (ValueError, TypeError):
        return comms.error(codes.AMOUNT_NOT_DIGIT)
    if amount <= 0:
        return comms.error(codes.AMOUNT_NEGATIVE)

    
    if amount > sender_balance:
        return comms.error(codes.BALANCE_INSUFFICIENT)

    new_sender_balance = sender_balance - amount
    db.update_bal(acc_uuid, new_sender_balance)
    db.tr_add(user_uuid, acc_uuid, "transfer_send", -amount, new_sender_balance, f"Отправлено {recv_login}")

    new_reciver_balance = reciver_balance + amount
    db.update_bal(recv_acc, new_reciver_balance)
    db.tr_add(reciver_uuid, recv_acc, "transfer_recv", amount, new_reciver_balance, f"Получено от {sender_login}")
    return comms.ok(data={"new_balance": new_sender_balance})


def burn(acc_uuid, pin_input):
    user_uuid = db.get_user_by_acc_uuid(acc_uuid)
    db_hash = db.get_pin_hash(user_uuid)
    if pin_input is None:
        return comms.error(codes.PIN_EMPTY)
    if not auth.check_pin(pin_input, db_hash):
        return comms.error(codes.PIN_WRONG)
    balance = db.get_bal(acc_uuid)
    db.update_bal(acc_uuid, 0)
    db.tr_add(user_uuid, acc_uuid, "burn", -balance, 0, "Сжигание")
    return comms.ok(data={"new_balance": 0})

def get_balance(acc_uuid):
    if acc_uuid is None:
        return comms.error(codes.USER_NOT_FOUND)
    bal = db.get_bal(acc_uuid)
    if bal is None:
        return comms.error(codes.USER_NOT_FOUND)
    
    return comms.ok(data={"balance": bal})

def get_accounts(user_uuid):
    if user_uuid is None:
        return comms.error(codes.USER_NOT_FOUND)
    acc = db.get_accounts_by_user(user_uuid)
    if acc is None:
        return comms.error(codes.USER_NOT_FOUND)
    
    return comms.ok(data={"accounts": acc})


def get_history(user_uuid, get_recent: bool):
    if not user_uuid:
        return comms.error(codes.USER_NOT_FOUND)
    if get_recent == True:
        transactions = db.tr_get_recent(user_uuid, 10)
        return comms.ok(data={"history": transactions, "recent": True})
    else:
        transactions = db.tr_get_all(user_uuid)
        return comms.ok(data={"history": transactions, "recent": False})