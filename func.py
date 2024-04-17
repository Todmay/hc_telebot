from datetime import datetime
import time

import settings_bot
import db_sqlite
from db_sqlite import *

##################### подключение к БД ######################
import httplib2
#import apiclient
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

# Библиотека для работы с Google Sheets API
import gspread

spreadsheet_id_name = settings_bot.spreadsheet_id_name

spreadsheet_id = '1KF_qiRYirnwIQrW-jJp9WlcIcq12suEvsCJjtlXnxZA' # googlesheet id
CREDENTIALS_FILE = 'creds.json'


credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets',
                                                                                  'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = build('sheets', 'v4', http=httpAuth)



def validate_phone_number(phone_number):
    # Шаблон для распознавания номера телефона
    pattern = re.compile(r'^\+?\d{1,3}[-. ]?\(?\d{2,3}\)?[-. ]?\d{3}[-. ]?\d{2,3}[-. ]?\d{2,3}$')
    # Проверка соответствия шаблону
    if pattern.match(phone_number):
        return True
    else:
        return False


def validate_telegram_username(username):
    # Шаблон для распознавания имени пользователя в Telegram
    pattern = re.compile(r'^@([A-Za-z0-9_]{5,32})$')
    # Проверка соответствия шаблону
    if pattern.match(username):
        return True
    else:
        return False

def validate_telegram_id(telegram_id):
    # Шаблон для распознавания Telegram ID (цифры без символа @)
    pattern = re.compile(r'^\d+$')
    # Проверка соответствия шаблону
    if pattern.match(telegram_id):
        return True
    else:
        return False

def validate_any_int(idd):
    try:
        int_value = int(idd)
        return -1000 <= int_value <= 1000
    except ValueError:
        return False


def send_message_telegram(text, chat_id = settings_bot.chat_id_tg_for_mg_alerts):
    # Добавляем заголовки для обхода защиты от ДДОС
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'}
    purl = f'https://api.telegram.org/bot{settings_bot.bot_token_log}/sendMessage'
    params = {"chat_id": chat_id, "text": text }
    r = requests.post(purl, params = params, headers=headers, verify=False)
    print(text)
    return


##################### конец подключение к БД ######################

def register_check_ligth(username: str):

    check_reg = False
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    gc = gspread.authorize(credentials)
    # Открытие документа
    sheet = gc.open(spreadsheet_id_name)
    # Выбор листа
    worksheet = sheet.get_worksheet(0)    
    # получаем список всех строк
    rows_reg = worksheet.get_all_values()
    # считаем количество строк с непустыми значениями
    for row_reg in rows_reg:
        if username in row_reg and 'Регистрация' in row_reg:
            check_reg = True

    return check_reg


def register_check(username: str):

    char_name = db_sqlite.db_get_character_name_by_player_name(username)

    if char_name:
        check = True 
    else:
        check = False

    return check


def register_check_from_doc(username: str):

### для работы импортировать конфиг, два способа, использую второй
#credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
#httpAuth = credentials.authorize(httplib2.Http())
#service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)

    check_reg = False
    check_all = False

    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    gc = gspread.authorize(credentials)
    # Открытие документа
    sheet = gc.open(spreadsheet_id_name)
    # Выбор листа
    worksheet = sheet.get_worksheet(0)

    # получаем список всех строк
    rows_reg = worksheet.get_all_values()

    check_reg = register_check_ligth(username)

    if not check_reg:
        worksheet_all = sheet.get_worksheet(2)
        rows_all = worksheet_all.get_all_values()
        for row_all in rows_all:
            if not (row_all[0].find(username) == -1):
                check_all = True
                check_reg = check_all

    check = check_reg

    return check

##### функция регистрации пользоватея

def success_reg(message):

    now = datetime.now().strftime("%Y.%m.%d %H:%M")
    values = (now, message.from_user.id, message.from_user.username, 'Регистрация', message.text)

    # Подключаемся к базе данных SQLite
    connection, cursor = db_sqlite.connect_to_database()

    # Добавляем данные в таблицу registrations
    cursor.execute('''INSERT INTO registrations 
                      (registration_time, telegram_id, username, registration_reason, command_used)
                      VALUES (?, ?, ?, ?, ?)''', values)
    connection.commit()

    connection.close()

    return None

def failure_reg(message):

    now = datetime.now().strftime("%Y.%m.%d %H:%M")
    values = (now, message.from_user.id, message.from_user.username, 'Попытка регистрации, нет в игроках', message.text)

    # Подключаемся к базе данных SQLite
    connection, cursor = db_sqlite.connect_to_database()

    # Добавляем данные в таблицу registrations
    cursor.execute('''INSERT INTO registrations 
                      (registration_time, telegram_id, username, registration_reason, command_used)
                      VALUES (?, ?, ?, ?, ?)''', values)
    connection.commit()

    connection.close()

    return None


def register_api_token(message):

    now = datetime.now()
    now = now.strftime("%Y.%m.%d %H:%M")

   # Задайте значение для сравнения
    telegram_username = message.from_user.username

    reg_sign = register_check(telegram_username) 

    if reg_sign:
        success_reg(message)

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Начать использовать!")
        markup.add(btn1)
        bot.send_message(message.chat.id, text="Регистрация успешна!".format(message.from_user), reply_markup=markup)
        message.text = "Информация"
    else:
        failure_reg(message)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Попробовать пройти регистрацию еще раз")
        markup.add(btn1)
        bot.send_message(message.chat.id, text="Регистрация не удалась, так как пользователь не найден в базе ОТ".format(message.from_user), reply_markup=markup)

    return None

################ обновления гугл дока ########################

from oauth2client.service_account import ServiceAccountCredentials

spreadsheet_id = settings_bot.spreadsheet_id
CREDENTIALS_FILE = settings_bot.CREDENTIALS_FILE
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets',
                                                                                  'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = build('sheets', 'v4', http=httpAuth)


### работа с баллами ###

def teacher_check_from_doc(username: str):

    check = False

    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    gc = gspread.authorize(credentials)
    # Открытие документа
    sheet = gc.open(spreadsheet_id_name)
    # Выбор листа
    worksheet_all = sheet.get_worksheet(5)
    # 5 это лист по счету где лежат логины преподавателей школы
    rows_all = worksheet_all.get_all_values()
    for row_all in rows_all:
        if not (row_all[0].find(username) == -1):
            check = True


    return check

def teacher_check(username: str):
    # Подключаемся к базе данных SQLite
    connection, cursor = db_sqlite.connect_to_database()

    # Проверяем наличие преподавателя в таблице prepodavali
    cursor.execute("SELECT COUNT(*) FROM prepodavali WHERE telegram_name = ?", (username,))
    count = cursor.fetchone()[0]

    # Если count больше 0, значит преподаватель найден
    check = count > 0

    connection.close()

    return check

def mark_write_to_doc(faculty : str, mark : int, comm : str, chat_name : str, telegram_id : str):

    now = datetime.now()
    now = now.strftime("%Y.%m.%d %H:%M")

    values = service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range="ШкольныеБаллы!A1",
        valueInputOption="USER_ENTERED",
        body={
            "values": [['id', now, faculty, mark, comm, chat_name, telegram_id]]
        }
    ).execute()

    # Получаем номер строки, в которую произошла вставка
    inserted_row_number = values['updates']['updatedRange'].split('!')[1].split(':')[0][1:]

    # Обновляем значение в колонке "A" для соответствующей строки
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"ШкольныеБаллы!A{inserted_row_number}",
        valueInputOption="USER_ENTERED",
        body={
            "values": [[inserted_row_number]]
        }
    ).execute()


    return None

def mark_write(faculty: str, mark: int, comm: str, chat_name: str, telegram_id: str):
    # Установка соединения с базой данных SQLite
    connection, cursor = db_sqlite.connect_to_database()

    # Получаем текущую дату и время
    now = datetime.now()
    date_time = now.strftime("%Y.%m.%d %H:%M")

    # Вставляем новую запись в таблицу school_scores
    cursor.execute('''INSERT INTO school_scores (date_time, house, score, reason, teacher_name, telegram_username)
                      VALUES (?, ?, ?, ?, ?, ?)''', (date_time, faculty, mark, comm, chat_name, telegram_id))
    connection.commit()

    connection.close()

    return None

def marks_read_from_doc():

#### 4 это страница с логом внесения

    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    gc = gspread.authorize(credentials)
    # Открытие документа
    sheet = gc.open(spreadsheet_id_name)
    # Выбор листа
    worksheet_all = sheet.get_worksheet(4)
    # 5 это лист по счету где лежат логины преподавателей школы
    rows_all = worksheet_all.get_all_values()

    last_five_rows = [row[:6] + row[6+1:] for row in rows_all[-5:]]

    return last_five_rows


def format_row(row):
    # Форматируем строку данных
    formatted_row = f"*Номер изменения с начала года:* {row[0]}\n" \
                    f"*Когда:* {row[1]}\n" \
                    f"*Факультет:* {row[2]}\n" \
                    f"*Какие изменения:* {row[3]}\n" \
                    f"*За что:* {row[4]}\n" \
                    f"*Кто:* {row[5]}"
    return formatted_row

def marks_read():
    # Подключаемся к БД и получаем данные
    connection, cursor = db_sqlite.connect_to_database()

    # Получаем данные из таблицы school_scores
    cursor.execute("SELECT * FROM school_scores ORDER BY id DESC LIMIT 5")  # Выбираем последние пять записей
    rows = cursor.fetchall()

    # Формируем отформатированные данные
    formatted_rows = []
    for row in rows:
        formatted_rows.append(format_row(row))

    connection.close()

    # Создаем сообщение с различными стилями форматирования
    message = "*Последние пять изменений баллов:*\n\n"
    message += "\n\n---\n\n".join(formatted_rows)  # Объединяем строки в одну строку с разделителями

    return message

def marks_all_from_doc():

    # Получаем данные из таблицы
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range="ШкольныеБаллы").execute()
    data = result.get('values', [])

    # Инициализируем словарь для суммирования баллов по факультетам
    faculty_scores = {}

    # Обрабатываем каждую запись в таблице
    for row in data:
        if len(row) >= 4:  # Проверяем, что у нас есть необходимые столбцы
            faculty = row[2]  # Индекс столбца с факультетом
            score = row[3]  # Индекс столбца с баллами

            # Проверяем, что балл - это число
            try:
                score = int(score)

                # Если факультет уже есть в словаре, добавляем балл
                if faculty in faculty_scores:
                    faculty_scores[faculty] += score
                else:
                    # Если факультета еще нет в словаре, создаем его и добавляем балл
                    faculty_scores[faculty] = score
            except ValueError:
                # Если балл не является числом, игнорируем запись
                pass

    # Формируем строку с результатами
    result_string = "\n".join([f"{faculty} - {score}" for faculty, score in faculty_scores.items()])

    return result_string  

def marks_all():

    # Подключаемся к БД и получаем данные
    connection, cursor = db_sqlite.connect_to_database()

    # Получаем данные из таблицы school_scores
    cursor.execute("SELECT house, score FROM school_scores")
    data = cursor.fetchall()

    connection.close()

    # Инициализируем словарь для суммирования баллов по факультетам
    faculty_scores = {}

    # Обрабатываем каждую запись в таблице
    for row in data:
        if len(row) >= 2:  # Проверяем, что у нас есть необходимые столбцы
            faculty = row[0]  # Индекс столбца с факультетом
            score = row[1]  # Индекс столбца с баллами

            # Проверяем, что балл - это число
            try:
                score = int(score)

                # Если факультет уже есть в словаре, добавляем балл
                if faculty in faculty_scores:
                    faculty_scores[faculty] += score
                else:
                    # Если факультета еще нет в словаре, создаем его и добавляем балл
                    faculty_scores[faculty] = score
            except ValueError:
                # Если балл не является числом, игнорируем запись
                pass

    # Формируем строку с результатами
    result_string = "\n".join([f"{faculty} - {score}" for faculty, score in faculty_scores.items()])

    return result_string  


### работа с баллами ###



################ обновления гугл дока ########################


################ поиск на сайте ########################

import requests


def search_text_ehp(search_text):

    answer = 'Ищи правила на сайте http://hp-ekb.ru/'

    return answer


################ поиск на сайте ########################
