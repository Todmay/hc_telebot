import sqlite3
from datetime import datetime


# Подключение к базе данных SQLite
def connect_to_database():
    connection = sqlite3.connect('bot_main.db')
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
def create_all_table():
    connection = sqlite3.connect('bot_main.db')
    cursor = connection.cursor()
    
    # Создание таблицы пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            registration_date TEXT
        )
    ''')

    # Создаем таблицу с названием 'prepodavali' и указанными столбцами,
    # включая столбец ID с автоинкрементом
    cursor.execute('''CREATE TABLE IF NOT EXISTS prepodavali
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       telegram_name TEXT,
                       character_name TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS school_scores
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       date_time TEXT,
                       house TEXT,
                       score INTEGER,
                       reason TEXT,
                       teacher_name TEXT,
                       telegram_username TEXT)''')    
    # категории запросов
    cursor.execute('''CREATE TABLE IF NOT EXISTS categories
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       category_name TEXT,
                       description TEXT)''')

    # таблица игроков
    cursor.execute('''CREATE TABLE IF NOT EXISTS players
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       telegram_username TEXT,
                       character_name TEXT)''')


    #запросы
    cursor.execute('''CREATE TABLE IF NOT EXISTS requests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        creation_time TEXT,
                        clarification_time TEXT,
                        telegram_id INTEGER,
                        username TEXT,
                        category TEXT,
                        request TEXT,
                        player_clarification TEXT,
                        response TEXT,
                        send_response TEXT,
                        request_status TEXT
                    )''')

    # регистрации
    cursor.execute('''CREATE TABLE IF NOT EXISTS registrations (
                        registration_time TEXT,
                        telegram_id INTEGER,
                        username TEXT,
                        registration_reason TEXT,
                        command_used TEXT
                    )''')


    connection.commit()
    connection.close()

def db_delete_last_record_from_school_scores(username):
    # Подключаемся к базе данных SQLite
    connection, cursor = connect_to_database()


    # Получаем ID последней записи пользователя
    cursor.execute("SELECT id FROM school_scores WHERE telegram_username = ? ORDER BY date_time DESC LIMIT 1", (username,))
    row = cursor.fetchone()
    if row:
        last_id = row[0]
        # Удаляем последнюю запись пользователя
        cursor.execute("DELETE FROM school_scores WHERE id = ?", (last_id,))
        connection.commit()
        text = f"Последняя запись пользователя {username} успешно удалена."
    else:
        text = f"Пользователь {username} не найден в базе данных."

    connection.close()

    return text

def db_get_character_name_by_player_name(player_name):
    connection, cursor = connect_to_database()
    cursor.execute("SELECT character_name FROM prepodavali WHERE telegram_username = ?", (player_name,))
    character_name = cursor.fetchone()[0]

    return character_name

def db_get_teacher_name_by_telegram_name(player_name):
    connection, cursor = connect_to_database()
    cursor.execute("SELECT character_name FROM players WHERE telegram_username = ?", (player_name,))
    character_name = cursor.fetchone()[0]

    return character_name



def db_get_catalog():

    connection, cursor = connect_to_database()
    cursor.execute("SELECT category_name FROM categories")
    values = cursor.fetchall()
    catalog = list()

    for row in values:
        catalog.append(row[0])

    return catalog

def db_get_category_id(category_name):

    connection, cursor = connect_to_database()
    cursor.execute("SELECT description FROM categories WHERE category_name = ?", (category_name,))
    value = cursor.fetchone()

    return value

# Функция для записи пользователя в базу данных
def db_insert_user_into_db(chat_id):
    connection, cursor = connect_to_database()
    
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
create_all_table()