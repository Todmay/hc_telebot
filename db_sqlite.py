import sqlite3
from datetime import datetime


# Подключение к базе данных SQLite
def connect_to_database():
    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()
    return connection, cursor


# Запрос к базе данных для проверки регистрации пользователя
def db_check_registration_in_db(chat_id):
    connection, cursor = connect_to_database()
    cursor.execute("SELECT COUNT(*) FROM users WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()[0] > 0
    connection.close()
    return result


# Функция для создания базы данных SQLite и таблицы пользователей
def create_users_table():
    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()
    
    # Создание таблицы пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            registration_date TEXT
        )
    ''')
    
    connection.commit()
    connection.close()


# Функция для записи пользователя в базу данных
def db_insert_user_into_db(chat_id):
    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()
    
    # Получение текущей даты и времени
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Вставка новой записи о пользователе в таблицу
    cursor.execute("INSERT INTO users (chat_id, registration_date) VALUES (?, ?)", (chat_id, current_date))
    
    connection.commit()
    connection.close()

#############

#запуск на создание запускаем один раз, потом просто используем функции из данного файла

#############


# Вызов функции для создания таблицы пользователей
create_users_table()