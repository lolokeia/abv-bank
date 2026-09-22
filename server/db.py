import sqlite3
import uuid

connection = None
cursor = None


def connect(path):
    global connection, cursor
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    cursor = connection.cursor()
    return(connection, cursor)



def init():
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
    uuid TEXT PRIMARY KEY,
    login TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    balance REAL,
    pin_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    role TEXT DEFAULT 'user'
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_uuid TEXT NOT NULL,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        balance_after REAL NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_uuid) REFERENCES Users(uuid)
    )
    ''')
    connection.commit()

def create_user(login, name, pin_hash):
    usr_uuid = str(uuid.uuid4())
    bal = 0
    cursor.execute("SELECT 1 FROM Users WHERE login = ?", (login,))
    if cursor.fetchone():
        return None
            
    cursor.execute("""INSERT INTO Users (uuid, login, name, pin_hash, balance)
    VALUES (?, ?, ?, ?, ?)""", (usr_uuid, login, name, pin_hash, bal))
    connection.commit()
    return usr_uuid




# Получение данных
def get_user(id):
    cursor.execute("SELECT * FROM Users WHERE uuid = ?", (id,))
    return cursor.fetchone() 

def get_user_by_login(login):
    cursor.execute("SELECT uuid FROM Users WHERE login = ?", (login,))
    row = cursor.fetchone()
    return row[0] if row else None

def get_name_from_id(id):
    cursor.execute("SELECT name FROM Users WHERE uuid = ?", (id,))
    row = cursor.fetchone()
    return row[0] if row else "Пользователь"


def get_bal(id):
    cursor.execute("SELECT balance FROM Users WHERE uuid = ?", (id,))
    row = cursor.fetchone()
    return row[0] if row else 0

def get_users_count():
    cursor.execute("SELECT COUNT(*) FROM Users")
    return cursor.fetchone()[0]

def get_pin_hash(id):
    cursor.execute("SELECT pin_hash FROM Users WHERE uuid = ?", (id,))
    row = cursor.fetchone()
    return row[0] if row else None

def get_login_by_uuid(id):
    cursor.execute("SELECT login FROM Users WHERE uuid = ?", (id,))
    row = cursor.fetchone()
    return row[0] if row else None

def get_role_by_uuid(id):
    cursor.execute("SELECT role FROM Users WHERE uuid = ?", (id,))
    return cursor.fetchone() 

 # Обновление данных
def update_bal(id, new_bal):
    cursor.execute("UPDATE Users SET balance = ? WHERE uuid = ?", (new_bal, id))
    connection.commit()

def update_name(id, new_name):
    cursor.execute("UPDATE Users SET name = ? WHERE uuid = ?", (new_name, id))
    connection.commit()

def update_login(id, new_login):
    cursor.execute("UPDATE Users SET login = ? WHERE uuid = ?", (new_login, id))
    connection.commit()

def update_pin_hash(id, new_pin_hash):
    cursor.execute("UPDATE Users SET pin_hash = ? WHERE uuid = ?", (new_pin_hash, id))
    connection.commit()




# транзакции
def tr_add(uuid, type, amount, balance_after, description):
    cursor.execute("""INSERT INTO Transactions (user_uuid, type, amount, balance_after, description)
    VALUES (?, ?, ?, ?, ?)""", (uuid, type, amount, balance_after, description))
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
def delete_user(id):
    cursor.execute("DELETE FROM Transactions WHERE user_uuid = ?", (id,))
    cursor.execute("DELETE FROM Users WHERE uuid = ?", (id,))
    connection.commit()



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