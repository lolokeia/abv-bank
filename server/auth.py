from server import db, tokens
from shared import comms
import bcrypt

def hash_pin(pin: str) -> str:
    return bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode() #хеширпует пин код

def check_pin(pin: str, stored_hash: str) -> bool:
    return bcrypt.checkpw(pin.encode(), stored_hash.encode()) # проверяет пин, возвращает T or F



def register(login, name, pin_input):
    """Регистрирует пользователя, проверяет правила и обращается к БД."""
    if pin_input is None: 
        return comms.error("Пин не введен", "pin_is_empty")

    if len(pin_input) != 4:
         return comms.error("Пин может состоять только из 4 цифр", "invalid_pin")
    
    if not login.strip(): # проверки на наличие ввода
        return comms.error("Логин не может быть пустым", "login_is_empty")
    
    if not name.strip():
        return comms.error("Имя не может быть пустым", "name_is_empty")
    
    if len(login) > 32 or len(name) > 32:
        return comms.error("Логин или имя превышают лимит символов в 32 символа", "login_exceeds_32")
    
    if db.get_user_by_login(login) is not None:
        return comms.error("Такой логин уже занят", "login_taken")
    
    pin_hash = hash_pin(pin_input)
    user_uuid = db.create_user(login, name, pin_hash)

    if user_uuid is None:
            return comms.error("Ошибка при создании пользователя", "user_cannot_be_created")

    token = db.create_token(user_uuid)
    return comms.ok(f"Регистрация успешна, {name}.", {"login": login, "name": name, "token": token})



def login(login_input, pin_input):
    """логинит пользователя, проверяет существование пользователя."""

    user_uuid = db.get_user_by_login(login_input)

    if user_uuid is None:
        return comms.error("Пользователя не существует", "user_not_exists")
    
    if pin_input is None:
        return comms.error("Пин не может быть пустым", "pin_is_empty")
    
    pin_hash = db.get_pin_hash(user_uuid)
    if not check_pin(pin_input, pin_hash):
         return comms.error("Неправильный пин-код", "wrong_pin")
    
    name = db.get_name_from_id(user_uuid)

    token = db.create_token(user_uuid)

    return comms.ok(f"Доброе утро, {name}", {"token": token, "name": name, "login": login_input})



def change_login(user_uuid, new_login):
    """Проверяет возможность смены логина, отправляет новый логин в БД"""
    if not new_login:
         return comms.error("Логин не может быть пустым", "login_is_empty")
    if db.get_user_by_login(new_login) is not None:
        return comms.error("Логин уже занят", "login_taken")
    if len(new_login) > 32:
                return comms.error("Логин превышает лимит символов в 32 символа", "login_exceeds_32")
    db.update_login(user_uuid, new_login)
    return comms.ok(f"Логин успешно изменен на {new_login}")



def change_pin(user_uuid, old_pin, new_pin):
    """Проверяет возможность смены пина, отправляет новый пин в БД"""
    if not old_pin:
        return comms.error("Старый пин не может быть пустым", "pin_is_empty")
    pin_hash = db.get_pin_hash(user_uuid)
    if not check_pin(old_pin, pin_hash):
        return comms.error("Старый пин неверен", "wrong_pin")
    if len(new_pin) != 4:
        return comms.error("Пин должен состоять из 4 цифр", "invalid_pin")
    new_hash = hash_pin(new_pin)
    db.update_pin_hash(user_uuid, new_hash)
    tokens.revoke_all(user_uuid)
    return comms.ok(f"Пин успешно изменен, вам придется перезайти")



def change_name(user_uuid, new_name):
    if not new_name:
        return comms.error("Новое имя не может быть пустым!", "name_is_empty")
    if len(new_name) > 32:
            return comms.error("Имя превышает лимит символов в 32 символа", "login_exceeds_32")
    db.update_name(user_uuid, new_name)
    return comms.ok(f"Имя успешно изменено на {new_name}")