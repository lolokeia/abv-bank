from server import db, tokens
from shared import comms, codes
import bcrypt
import re

BANNED_LOGINS = {
    "admin", "administrator", "root", "superuser",
    "support", "help", "tech", "techsupport",
    "system", "server", "bot", "moderator", "mod",
    "billing", "finance", "payment", "test", "tester",
    "login", "logout", "register", "auth", "api",
    "null", "undefined", "none", "select", "drop", "con"
}

def isdigit(num):
    try: num = int(num); return True
    except ValueError: return False

def hash_pin(pin: str) -> str:
    return bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode() #хеширпует пин код

def check_pin(pin: str, stored_hash: str) -> bool:
    return bcrypt.checkpw(pin.encode(), stored_hash.encode()) # проверяет пин, возвращает T or F


def register(login, name, pin_input, name_bypass=False):
    """Регистрирует пользователя, проверяет правила и обращается к БД."""
    if pin_input is None: 
        return comms.error(codes.PIN_EMPTY)

    if len(pin_input) != 4:
         return comms.error(codes.PIN_LENGTH)

    if isdigit(pin_input) is False:
        return comms.error(codes.PIN_CHAR)
    
    if not login.strip(): # проверки на наличие ввода
        return comms.error(codes.LOGIN_EMPTY)
    
    if not name.strip():
        return comms.error(codes.NAME_EMPTY)
    
    if len(login) > 32 or len(name) > 32:
        return comms.error(codes.LOGIN_LENGTH)

    if not re.match(r"^[a-zA-Z0-9_а-яА-ЯёЁ\-]+$", login):
        return comms.error(codes.LOGIN_CHAR)

    if not re.match(r"^[a-zA-Z0-9_а-яА-ЯёЁ\-]+$", name):
        return comms.error(codes.NAME_CHAR)
    
    clean_login = login.strip().lower()

    if clean_login in BANNED_LOGINS and name_bypass == False:
        return comms.error(codes.LOGIN_FORBIDDEN)
    
    if db.get_user_by_login(login) is not None:
        return comms.error(codes.LOGIN_TAKEN)
    
    pin_hash = hash_pin(pin_input)
    user_uuid = db.create_user(login, name, pin_hash)

    if user_uuid is None:
            return comms.error(codes.USER_CANNOT_CREATE)

    account = db.create_account(user_uuid, "Счет по-умолчанию", "RUB")


    token = db.create_token(user_uuid)
    return comms.ok(data={"token": token, "account": account, "name": name})



def login(login_input, pin_input):
    """логинит пользователя, проверяет существование пользователя."""

    user_uuid = db.get_user_by_login(login_input)

    if user_uuid is None:
        return comms.error(codes.USER_NOT_FOUND)
    
    if pin_input is None:
        return comms.error(codes.PIN_EMPTY)
    
    pin_hash = db.get_pin_hash(user_uuid)
    if not check_pin(pin_input, pin_hash):
         return comms.error(codes.PIN_WRONG)
    
    name = db.get_name_from_id(user_uuid)

    token = db.create_token(user_uuid)

    return comms.ok(data={"token": token, "name": name, "login": login_input})



def change_login(user_uuid, new_login):
    """Проверяет возможность смены логина, отправляет новый логин в БД"""
    if not new_login:
         return comms.error(codes.LOGIN_EMPTY)
    if db.get_user_by_login(new_login) is not None:
        return comms.error(codes.LOGIN_TAKEN)
    
    if not new_login.strip(): # проверки на наличие ввода
        return comms.error(codes.LOGIN_EMPTY)
        

        
    if len(new_login) > 32:
        return comms.error(codes.LOGIN_LENGTH)
    
    if not re.match(r"^[a-zA-Z0-9_а-яА-ЯёЁ\-]+$", new_login):
        return comms.error(codes.LOGIN_CHAR)
    
        
    db.update_login(user_uuid, new_login)
    return comms.ok(data={})



def change_pin(user_uuid, old_pin, new_pin):
    """Проверяет возможность смены пина, отправляет новый пин в БД"""
    if not old_pin:
        return comms.error(codes.PIN_EMPTY)
    pin_hash = db.get_pin_hash(user_uuid)
    if not check_pin(old_pin, pin_hash):
        return comms.error(codes.PIN_WRONG)
    if len(new_pin) != 4:
        return comms.error(codes.PIN_LENGTH)
    if isdigit(new_pin) is False:
        return comms.error(codes.PIN_CHAR)
    new_hash = hash_pin(new_pin)
    db.update_pin_hash(user_uuid, new_hash)
    tokens.revoke_all(user_uuid)
    return comms.ok()



def change_name(user_uuid, new_name):
    if not new_name:
        return comms.error(codes.NAME_EMPTY)
    if len(new_name) > 32:
            return comms.error(codes.LOGIN_LENGTH)
    if not re.match(r"^[a-zA-Z0-9_а-яА-ЯёЁ\-]+$", new_name):
        return comms.error(codes.NAME_CHAR)
    db.update_name(user_uuid, new_name)
    return comms.ok()