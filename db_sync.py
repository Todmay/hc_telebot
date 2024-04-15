#### файл настроек
import settings_bot
import db_sqlite
from db_sqlite import *


import threading
import time


from func import send_message_telegram
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials


def check_matching_rows(df_db, df_sheet):
    """
    Функция для проверки совпадения строк между DataFrame из базы данных и DataFrame из Google Документа по всем колонкам.
    
    Аргументы:
    df_db (DataFrame): DataFrame из базы данных.
    df_sheet (DataFrame): DataFrame из Google Документа.
    
    Возвращает:
    bool: True, если есть совпадение строк хотя бы по одной колонке, иначе False.
    """
    for col in df_db.columns:
        merged_df = pd.merge(df_db, df_sheet, left_on=col, right_on=df_sheet.columns[0], how='inner')
        if not merged_df.empty:
            return True
    return False

# Пример использования функции
# df_db - DataFrame из базы данных, df_sheet - DataFrame из Google Документа
# Если есть хотя бы одно совпадение строк по одной из колонок, то matching=True, иначе False
#matching = check_matching_rows(df_db, df_sheet)
#print(matching)

def google_sheet_connect_points():
    # Подключаемся к Google Sheets
    spreadsheet_id = settings_bot.spreadsheet_id_points_doc
    CREDENTIALS_FILE = settings_bot.CREDENTIALS_FILE
    credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
    return spreadsheet_id, credentials


def google_sheet_connect_req():
    # Подключаемся к Google Sheets
    spreadsheet_id = settings_bot.spreadsheet_id
    CREDENTIALS_FILE = settings_bot.CREDENTIALS_FILE
    credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
    return spreadsheet_id, credentials

def sync_google_sheet_to_school_scores():
    # Открываем нужный лист
    spreadsheet_id, credentials = google_sheet_connect_points()
    gc = gspread.authorize(credentials)
    sheet_name = 'ШкольныеБаллы'
    worksheet = gc.open_by_key(spreadsheet_id).worksheet(sheet_name)

    # Получаем данные из Google Документов в виде списка списков
    data_from_sheet = worksheet.get_all_values()


    # Подключаемся к БД и получаем данные
    connection, cursor = connect_to_database()
    
    # Обновляем данные в базе данных на основе данных из Google Документа
    for row in data_from_sheet:
  

        id_value = int(row[0])
        date_time = row[1]
        house = row[2]
        score = row[3]
        reason = row[4]
        teacher_name = row[5]
        telegram_username = row[6]

        # Обновляем данные в базе данных
        update_query = """
        UPDATE school_scores
        SET date_time=?, house=?, score=?, reason=?, teacher_name=?, telegram_username=?
        WHERE id=?
        """
        cursor.execute(update_query, (date_time, house, score, reason, teacher_name, telegram_username, id_value))
        connection.commit()


    connection.close()

    # а после обновляем гуглдок
    sync_school_scores_to_google_sheet()

    return None

def sync_school_scores_to_google_sheet():

    spreadsheet_id, credentials = google_sheet_connect_points()

    gc = gspread.authorize(credentials)
    sheet = gc.open_by_key(spreadsheet_id).worksheet('ШкольныеБаллы')  # Открываем нужный лист
    
    # Подключаемся к БД и получаем данные
    connection, cursor = db_sqlite.connect_to_database()
    query = "SELECT * FROM school_scores"
    df = pd.read_sql_query(query, connection)
    
    # Очищаем лист перед записью новых данных
    sheet.clear()
    
    # Записываем данные на лист
    sheet.insert_rows(df.values.tolist())

    return None

def sync_registrations_to_google_sheet():
    spreadsheet_id, credentials = google_sheet_connect_req()         
    gc = gspread.authorize(credentials)
    sheet = gc.open_by_key(spreadsheet_id).worksheet('Регистрация')  # Открываем нужный лист

    # Очищаем лист перед записью новых данных
    sheet.clear()
    
    # Получаем данные из таблицы "registrations" базы данных
    connection, cursor = db_sqlite.connect_to_database()
    query = "SELECT * FROM registrations"
    df = pd.read_sql_query(query, connection)
    connection.close()
    
    # Получаем данные с листа Google Документа для определения, куда добавлять новые данные
    existing_data = sheet.get_all_values()
    num_existing_rows = len(existing_data)
    
    # Добавляем новые данные в Google Документ
    if not df.empty:
        new_values = df.values.tolist()
        sheet.add_rows(len(new_values))  # Добавляем строки для новых данных
        for i, row in enumerate(new_values):
            sheet.insert_row(row, num_existing_rows + i + 1)  # Добавляем данные в конец таблицы
    
    return None

def sync_categories_from_google_sheet():
    spreadsheet_id, credentials = google_sheet_connect_req()
    gc = gspread.authorize(credentials)
    sheet = gc.open_by_key(spreadsheet_id).worksheet('Категории')  # Открываем нужный лист
    
    # Получаем данные с листа Google Документа
    data = sheet.get_all_values()
    
    # Преобразуем данные в DataFrame
    df = pd.DataFrame(data[1:], columns=data[0])  # Первая строка - заголовки столбцов
    df_all_from_doc = pd.DataFrame(data)
    
    # Подключаемся к БД
    connection, cursor = db_sqlite.connect_to_database()
    query = "SELECT category_name, description FROM categories"
    df_all_from_table = pd.read_sql_query(query, connection)

    if check_matching_rows(df_all_from_table, df_all_from_doc):
        return None

    cursor.execute("DELETE FROM categories")
    connection.commit()
    
    # Записываем данные в таблицу
    df.to_sql('categories', connection, if_exists='append', index=False)
    
    connection.close()

    return None

def sync_teachers_from_google_sheet():
    spreadsheet_id, credentials = google_sheet_connect_points()
    gc = gspread.authorize(credentials)
    sheet = gc.open_by_key(spreadsheet_id).worksheet('Преподаватели')  # Открываем нужный лист
    
    # Получаем данные с листа Google Документа
    data = sheet.get_all_values()
    
    # Преобразуем данные в DataFrame
    df = pd.DataFrame(data[1:], columns=data[0])  # Первая строка - заголовки столбцов
    df_all_from_doc = pd.DataFrame(data)    
    # Подключаемся к БД
    connection, cursor = db_sqlite.connect_to_database()
    query = "SELECT telegram_name, character_name FROM prepodavali"
    df_all_from_table = pd.read_sql_query(query, connection)

    #if check_matching_rows(df_all_from_table, df_all_from_doc):
        #return None
    cursor.execute("DELETE FROM prepodavali")
    connection.commit()
    
    # Записываем данные в таблицу
    df.to_sql('prepodavali', connection, if_exists='append', index=False)
    
    connection.close()

    return None

def sync_players_from_google_sheet():
    spreadsheet_id, credentials = google_sheet_connect_req()
    gc = gspread.authorize(credentials)
    sheet = gc.open_by_key(spreadsheet_id).worksheet('Игроки')  # Открываем нужный лист
    
    # Получаем данные с листа Google Документа
    data = sheet.get_all_values()
    
    # Преобразуем данные в DataFrame
    df = pd.DataFrame(data[1:], columns=data[0])  # Первая строка - заголовки столбцов
    df_all_from_doc = pd.DataFrame(data)  
    
    # Подключаемся к БД
    connection, cursor = db_sqlite.connect_to_database()
    query = "SELECT telegram_username, character_name FROM players"
    df_all_from_table = pd.read_sql_query(query, connection)

    if check_matching_rows(df_all_from_table, df_all_from_doc):
        return None
    cursor.execute("DELETE FROM players")
    connection.commit()
    
    # Записываем данные в таблицу
    df.to_sql('players', connection, if_exists='append', index=False)
    
    connection.close()

    return None

def sync_google_sheet_to_roles():
    # Подключаемся к Google Документам
    spreadsheet_id, credentials = google_sheet_connect_points()
    gc = gspread.authorize(credentials)
    sheet_name = 'РолиБаллы'  # Название листа с данными
    worksheet = gc.open_by_key(spreadsheet_id).worksheet(sheet_name)

    # Получаем данные из Google Документов в виде списка списков
    data_from_sheet = worksheet.get_all_values()

    # Подключаемся к БД SQLite
    connection, cursor = db_sqlite.connect_to_database()

    # Очищаем таблицу перед записью новых данных
    cursor.execute("DELETE FROM roles")
    connection.commit()

    # Вставляем данные из Google Документов в таблицу
    for row in data_from_sheet[1:]:  # Пропускаем заголовки, начинаем с индекса 1
        cursor.execute("""
        INSERT INTO roles (role_name, from_value, to_value)
        VALUES (?, ?, ?)
        """, (row[0], int(row[1]), int(row[2])))
        connection.commit()

    connection.close()

#### здесь надо обновлять и дописывать, пока её не трогаем ####
def sync_requests_between_db_and_sheet():
    # Подключаемся к Google Sheets
    spreadsheet_id, credentials = google_sheet_connect_req()
    gc = gspread.authorize(credentials)
    sheet = gc.open_by_key(spreadsheet_id).worksheet('Название листа')  # Укажите название листа
    
    # Получаем данные из Google Документа
    all_rows = sheet.get_all_values()
    headers = all_rows[0]
    data_rows = all_rows[1:]

    # Получаем данные из таблицы "requests" базы данных
    connection, cursor = db_sqlite.connect_to_database()
    cursor = connection.cursor()
    cursor.execute("SELECT id, response FROM requests")
    db_data = cursor.fetchall()
    
    # Обновляем данные в базе данных из Google Документа и добавляем новые строки в Google Документ
    for row in data_rows:
        cell_id = int(row[0])  # ID записи в Google Документе
        response_data = row[8]  # Данные из колонки "Ответ" в Google Документе

        # Проверяем, есть ли такая запись в базе данных
        found_in_db = False
        for db_row in db_data:
            db_id, db_response = db_row
            if db_id == cell_id:
                found_in_db = True
                # Обновляем данные в базе данных
                cursor.execute("UPDATE requests SET response = ? WHERE id = ?", (response_data, cell_id))
                conn.commit()
                break  # Выходим из цикла, если запись найдена и обновлена
        
        # Если запись не найдена в базе данных, добавляем новую строку в Google Документ
        if not found_in_db:
            sheet.append_row(row)

    connection.close()
    return None

# Вызываем функцию для синхронизации данных

###### синхронизируемся только в части регистрации и в части школьных баллов, также в части категории
###### запросы делаем потом и отдельно!!!!!



# уведомление в консоль о запуске
print('Starting....')

def start_sync():
    now = datetime.now()
    now = now.strftime("%Y.%m.%d %H:%M")

    sync_google_sheet_to_roles()
    sync_registrations_to_google_sheet()
    sync_google_sheet_to_school_scores()
    sync_categories_from_google_sheet()
    sync_teachers_from_google_sheet()
    sync_players_from_google_sheet()
    print(f'Синхронизация завершена.... Время {now}')
    return None

# Функция перезапуска бэка
def restart_back():
    # Останавливаем текущий поток
    threading.current_thread().join()

    # Запуск бота в отдельном потоке
    bot_thread = threading.Thread(target=run_back)
    bot_thread.start()


    return None

# Запуск бэка в отдельном потоке
def run_back():

    try:
        while True:
            start_sync()
            time.sleep(settings_bot.check_time*0.9)
    except Exception as err:
        send_message_telegram('Проблема с синхронизацией базы и дока', settings_bot.chat_id_tg_for_errors)
        print('Проблема с синхронизацией базы и дока')
        print(str(err))
    return None

# Функция для проверки состояния бота и перезапуска, если требуется
def check_bot_status():
    try:
            # Проверка состояния бота или выполнение других действий
            # ...

            # Если все в порядке, продолжаем выполнение
        pass
    except Exception as e:
        print('Произошла ошибка СИНХРОНИЗАЦИИ:', str(e))
        send_message_telegram('Произошла ошибка СИНХРОНИЗАЦИИ:' + str(e), settings_bot.chat_id_tg_for_mg_alerts)
        send_message_telegram('Перезапуск СИНХРОНИЗАЦИИ части бота...', settings_bot.chat_id_tg_for_mg_alerts)

        # Выполняем перезапуск бота
        restart_back()
    return None



# Запуск бота в отдельном потоке
back_thread = threading.Thread(target=run_back)
back_thread.start()

# Запуск функции проверки состояния бэка
schedule_thread = threading.Thread(target=check_bot_status())
schedule_thread.start()

