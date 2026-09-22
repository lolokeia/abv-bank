from server import db
import bcrypt

def hash_pin(pin: str) -> str:
    return bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()

def check_pin(pin: str, stored_hash: str) -> bool:
    return bcrypt.checkpw(pin.encode(), stored_hash.encode())



def register(login, name, pin_input):
    if pin_input is None:
        return None
    if not login.strip():
        return None
    if not name.strip():
        return None
    if len(login) > 32 and len(name) > 32:
        return None
    pin_hash = hash_pin(pin_input)
    user_uuid = db.create_user(login, name, pin_hash)
    return user_uuid



def login(login_input, pin_input):
    user_uuid = db.get_user_by_login(login_input)
    if user_uuid is None:
        return None
    
    if pin_input is None:
                return None
    
    pin_hash = db.get_pin_hash(user_uuid)
    if not check_pin(pin_input, pin_hash):
         return None
    return user_uuid



def change_login(user_uuid, new_login):
    if db.get_user_by_login(new_login) is not None:
        return {"status": "error", "message": "Логин занят"}
    db.update_login(user_uuid, new_login)
    return {"status": "ok"}



def change_pin(user_uuid, old_pin, new_pin):
    stored_hash = db.get_pin_hash(user_uuid)
    if not check_pin(old_pin, stored_hash):
        return {"status": "error", "message": "Старый пин неверный"}
    new_hash = hash_pin(new_pin)
    db.update_pin_hash(user_uuid, new_hash)
    return {"status": "ok"}