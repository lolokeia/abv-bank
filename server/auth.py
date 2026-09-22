from server import db
from shared import response
import bcrypt

def hash_pin(pin: str) -> str:
    return bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode() #хеширпует пин код

def check_pin(pin: str, stored_hash: str) -> bool:
    return bcrypt.checkpw(pin.encode(), stored_hash.encode()) # проверяет пин, возвращает T or F



def register(login, name, pin_input):
    """Регистрирует пользователя, проверяет правила и обращается к БД."""
    if pin_input is None: 
        return response.error("Пин не введен")

    if len(pin_input) != 4:
         return response.error("Пин может состоять только из 4 цифр")
    
    if not login.strip(): # проверки на наличие ввода
        return response.error("Логин не может быть пустым")
    
    if not name.strip():
        return response.error("Имя не может быть пустым")
    
    if len(login) > 32 and len(name) > 32:
        return response.error("Логин или имя превышают лимит символов в 32 символа")
    
    if db.get_user_by_login(login) is not None:
        return response.error("Такой логин уже занят")
    
    pin_hash = hash_pin(pin_input)
    user_uuid = db.create_user(login, name, pin_hash)

    if user_uuid is None:
            return response.error("Ошибка при создании пользователя")

    return response.ok(f"Регистрация успешна, {name}.", {"login": login, "name": name, "uuid": user_uuid})



def login(login_input, pin_input):
    """логинит пользователя, проверяет существование пользователя."""

    user_uuid = db.get_user_by_login(login_input)

    if user_uuid is None:
        return response.error("Пользователя не существует")
    
    if pin_input is None:
        return response.error("Пин не может быть пустым")
    
    pin_hash = db.get_pin_hash(user_uuid)
    if not check_pin(pin_input, pin_hash):
         return response.error("Неправильный пин-код")
    
    name = db.get_name_from_id(user_uuid)

    return response.ok(f"Доброе утро, {name}", {"uuid": user_uuid, "name": name, "login": login_input})



def change_login(user_uuid, new_login):
    """Проверяет возможность смены логина, отправляет новый логин в БД"""
    if db.get_user_by_login(new_login) is not None:
        return response.error("Логин уже занят")
    if len(new_login) > 32:
                return response.error("Логин превышает лимит символов в 32 символа")
    db.update_login(user_uuid, new_login)
    return response.ok(f"Логин успешно изменен на {new_login}")



def change_pin(user_uuid, old_pin, new_pin):
    """Проверяет возможность смены пина, отправляет новый пин в БД"""
    pin_hash = db.get_pin_hash(user_uuid)
    if not check_pin(old_pin, pin_hash):
        return response.error("Старый пин неверен")
    if len(new_pin) != 4:
        return response.error("Пин должен состоять из 4 цифр")
    new_hash = hash_pin(new_pin)
    db.update_pin_hash(user_uuid, new_hash)
    return response.ok(f"Пин успешно изменен на {new_pin}")



def change_name(user_uuid, new_name):
    if not new_name:
        return response.error("Новое имя не может быть пустым!")
    if len(new_name) > 32:
            return response.error("Имя превышает лимит символов в 32 символа")
    db.update_name(user_uuid, new_name)
    return response.ok(f"Имя успешно изменено на {new_name}")