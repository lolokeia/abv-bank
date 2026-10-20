import sqlite3
import uuid
import secrets
from server import luhn
from datetime import datetime, timedelta, timezone
from config import TOKEN_EXPIRE_MINUTES
import threading
import random

import time
from shared import collibry

db_lock = threading.Lock()

connection = None
cursor = None

token_expire_time = TOKEN_EXPIRE_MINUTES



def connect(path):
    global connection, cursor
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.execute("PRAGMA foreign_keys = ON")
    cursor = connection.cursor()
    return(connection, cursor)



def init():
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
    uuid TEXT PRIMARY KEY UNIQUE,
    login TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    pin_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    role TEXT DEFAULT 'user',
    has_premium TEXT DEFAULT '0'
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Accounts (
        acc_uuid TEXT PRIMARY KEY UNIQUE NOT NULL,
        acc_num TEXT UNIQUE NOT NULL,
        owner_uuid TEXT NOT NULL,
        name TEXT NOT NULL,
        currency TEXT NOT NULL,
        balance INTEGER NOT NULL,
        is_frozen INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (owner_uuid) REFERENCES Users(uuid)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_uuid TEXT NOT NULL,
        acc_uuid TEXT NOT NULL,
        type TEXT NOT NULL,
        amount INTEGER NOT NULL,
        balance_after INTEGER NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_uuid) REFERENCES Users(uuid)
        FOREIGN KEY (acc_uuid) REFERENCES Accounts(acc_uuid)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Tokens (
        token TEXT NOT NULL PRIMARY KEY,
        uuid TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TEXT NOT NULL,
        FOREIGN KEY (uuid) REFERENCES Users(uuid))''')
    connection.commit()


def create_user(login, name, pin_hash):
    usr_uuid = str(uuid.uuid4())
    cursor.execute("SELECT 1 FROM Users WHERE login = ?", (login,))
    if cursor.fetchone():
        return None
            
    cursor.execute("""INSERT INTO Users (uuid, login, name, pin_hash)
    VALUES (?, ?, ?, ?)""", (usr_uuid, login, name, pin_hash))
    connection.commit()
    return usr_uuid


# Получение данных

def get_user(user_uuid):
    cursor.execute("SELECT uuid, login, name, created_at, role FROM Users WHERE uuid = ?", (user_uuid,))
    return cursor.fetchone() 


def get_user_by_login(login):
    cursor.execute("SELECT uuid FROM Users WHERE login = ?", (login,))
    row = cursor.fetchone()
    return row[0] if row else None


def get_name_from_id(user_uuid):
    cursor.execute("SELECT name FROM Users WHERE uuid = ?", (user_uuid,))
    row = cursor.fetchone()
    return row[0] if row else "Пользователь"


def get_users_count():
    cursor.execute("SELECT COUNT(*) FROM Users")
    return cursor.fetchone()[0]


def get_pin_hash(user_uuid):
    cursor.execute("SELECT pin_hash FROM Users WHERE uuid = ?", (user_uuid,))
    row = cursor.fetchone()
    return row[0] if row else None


def get_login_by_uuid(user_uuid):
    cursor.execute("SELECT login FROM Users WHERE uuid = ?", (user_uuid,))
    row = cursor.fetchone()
    return row[0] if row else None


def get_role_by_uuid(user_uuid):
    cursor.execute("SELECT role FROM Users WHERE uuid = ?", (user_uuid,))
    return cursor.fetchone()

def get_premium_by_uuid(user_uuid):
    cursor.execute("SELECT has_premium FROM Users WHERE uuid = ?", (user_uuid,))
    has_premium = cursor.fetchone()
    if not has_premium:
        return False
    if has_premium[0] == "1":
        return True
    else:
        return False

def grant_premium(user_uuid, premium=True):
    if premium:
        has = 1
    else: has = 0

    cursor.execute("UPDATE Users SET has_premium = ? WHERE uuid = ?", (has, user_uuid,))
    connection.commit()

def get_freeze_by_acc_uuid(acc_uuid):
    cursor.execute("SELECT is_frozen FROM Accounts WHERE acc_uuid = ?", (acc_uuid,))
    frozen = cursor.fetchone()
    if not frozen:
        return False
    if frozen[0] == 1:
        return True
    else:
        return False

def set_freeze_acc(acc_uuid, freeze=True):
    if freeze:
        has = 1
    else: has = 0
    
    cursor.execute("UPDATE Accounts SET is_frozen = ? WHERE acc_uuid = ?", (has, acc_uuid,))
    connection.commit()
 # Обновление данных


def update_name(user_uuid, new_name):
    cursor.execute("UPDATE Users SET name = ? WHERE uuid = ?", (new_name, user_uuid))
    connection.commit()


def update_login(user_uuid, new_login):
    cursor.execute("UPDATE Users SET login = ? WHERE uuid = ?", (new_login, user_uuid))
    connection.commit()


def update_pin_hash(user_uuid, new_pin_hash):
    cursor.execute("UPDATE Users SET pin_hash = ? WHERE uuid = ?", (new_pin_hash, user_uuid))
    connection.commit()






# транзакции

def tr_add(user_uuid, acc_uuid, type, amount, balance_after, description):
    cursor.execute("""INSERT INTO Transactions (user_uuid, acc_uuid, type, amount, balance_after, description)
    VALUES (?, ?, ?, ?, ?, ?)""", (user_uuid, acc_uuid, type, amount, balance_after, description))
    connection.commit()
    return cursor.lastrowid


def tr_get_all(user_uuid):
    cursor.execute("""
        SELECT type, amount, balance_after, description, created_at
        FROM Transactions
        WHERE user_uuid = ?
        ORDER BY id DESC
    """, (user_uuid,))
    return cursor.fetchall()


def tr_get_recent(user_uuid, limit=10):
    cursor.execute("""
        SELECT type, amount, balance_after, description, created_at
        FROM Transactions
        WHERE user_uuid = ?
        ORDER BY id DESC
        LIMIT ?
    """, (user_uuid, limit))
    return cursor.fetchall()

def tr_rollback():
    print("заглушка")




# Удаление пользователя

def delete_user(user_uuid):
    cursor.execute("DELETE FROM Transactions WHERE user_uuid = ?", (user_uuid,))
    cursor.execute("DELETE FROM Tokens WHERE uuid = ?", (user_uuid,))
    cursor.execute("DELETE FROM Accounts WHERE owner_uuid = ?", (user_uuid,))
    cursor.execute("DELETE FROM Users WHERE uuid = ?", (user_uuid,))
    connection.commit()


# Работа с токенами

def create_token(user_uuid):
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=token_expire_time)).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("INSERT INTO Tokens (token, uuid, expires_at) VALUES (?, ?, ?)", (token, user_uuid, expires_at))
    connection.commit()
    return token


def get_tokens_by_uuid(user_uuid):
    cursor.execute("SELECT * FROM Tokens WHERE uuid = ?", (user_uuid,))
    return cursor.fetchall()


def get_uuid_from_token(token):
    cursor.execute("SELECT uuid, expires_at FROM Tokens WHERE token = ?", (token,))
    return cursor.fetchone()


def remove_token(token):
    cursor.execute("DELETE FROM Tokens WHERE token = ?", (token,))
    connection.commit()


def remove_token_by_uuid(user_uuid):
    cursor.execute("DELETE FROM Tokens WHERE uuid = ?", (user_uuid,))
    connection.commit()


def unsafe_remove_all_tokens():
    cursor.execute("DELETE FROM Tokens")
    connection.commit()


def remove_expired_tokens(now_str):
    cursor.execute("DELETE FROM Tokens WHERE expires_at < ?", (now_str,))
    connection.commit()
    return cursor.rowcount



def table_get_users():
    cursor.execute("SELECT uuid, login, name, created_at, role FROM Users")
    return cursor.fetchall()


def table_get_tr():
    cursor.execute("SELECT * FROM Transactions")
    return cursor.fetchall()


def table_get_tokens():
    cursor.execute("SELECT * FROM Tokens")
    return cursor.fetchall()

def table_get_accounts():
    cursor.execute("SELECT * FROM Accounts")
    return cursor.fetchall()


def unsafe_set_balance_admin(acc_uuid, amount):
    user_uuid = get_user_by_acc_uuid(acc_uuid)
    old_bal = get_bal(acc_uuid)
    cursor.execute("UPDATE Accounts SET balance = ? WHERE acc_uuid = ?", (amount, acc_uuid))
    bal = get_bal(acc_uuid)
    tr_add(user_uuid, acc_uuid, "set", bal - old_bal, amount, "Установлено администратором")
    connection.commit()






# Счета




def update_bal(acc_uuid, new_bal):
    cursor.execute("UPDATE Accounts SET balance = ? WHERE acc_uuid = ?", (new_bal, acc_uuid))
    connection.commit()

def get_bal(acc_uuid):
    cursor.execute("SELECT balance FROM Accounts WHERE acc_uuid = ?", (acc_uuid,))
    row = cursor.fetchone()
    return row[0] if row else 0

def create_account(user_uuid, name, currency):
    acc_uuid = str(uuid.uuid4())
    bal = 0
    num_payload = str(random.randint(1000000, 9999999))
    checksum = luhn.checksum_create(num_payload)

    acc_num = str(num_payload) + str(checksum)

    cursor.execute("INSERT INTO Accounts (acc_uuid, acc_num, owner_uuid, name, currency, balance, is_frozen) VALUES (?, ?, ?, ?, ?, ?, ?)", (acc_uuid, acc_num, user_uuid, name, currency, bal, 0))
    connection.commit()
    return acc_uuid

def get_accounts_by_user(user_uuid):
    cursor.execute("SELECT * FROM Accounts WHERE owner_uuid = ?", (user_uuid,))
    return cursor.fetchall()

def get_account_by_uuid(acc_uuid):
    cursor.execute("SELECT * FROM Accounts WHERE acc_uuid = ?", (acc_uuid,))
    row = cursor.fetchone()
    return row if row else None

def get_account_by_num(acc_num):
    cursor.execute("SELECT * FROM Accounts WHERE acc_num = ?", (acc_num,))
    row = cursor.fetchone()
    return row if row else None

def get_user_by_acc_uuid(acc_uuid):
    cursor.execute("SELECT owner_uuid FROM Accounts WHERE acc_uuid = ?", (acc_uuid,))
    row = cursor.fetchone()
    return row[0] if row else None

def get_num_by_uuid(acc_uuid):
    cursor.execute("SELECT acc_num FROM Accounts WHERE acc_uuid = ?", (acc_uuid,))
    row = cursor.fetchone()
    return row[0] if row else None

def get_uuid_by_num(acc_num):
    cursor.execute("SELECT acc_uuid FROM Accounts WHERE acc_num = ?", (acc_num,))
    row = cursor.fetchone()
    return row[0] if row else None




def close():
    global connection, cursor
    try:
        if connection:
            connection.close()
    except Exception as e:
        print(f"Ошибка закрытия БД: {e}")
    finally:
        connection = None
        cursor = None

