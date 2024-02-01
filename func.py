from datetime import datetime
import time

import settings_bot

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

################ обновления гугл дока ########################

from oauth2client.service_account import ServiceAccountCredentials

spreadsheet_id = settings_bot.spreadsheet_id
CREDENTIALS_FILE = settings_bot.CREDENTIALS_FILE
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets',
                                                                                  'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = build('sheets', 'v4', http=httpAuth)


### работа с баллами ###

def teacher_check(username: str):

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

def mark_write(faculty : str, mark : int, comm : str, chat_name : str, telegram_id : str):

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

def marks_read():

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

def marks_all():

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

### работа с баллами ###



################ обновления гугл дока ########################


################ поиск на сайте ########################

import requests


def search_text_ehp(search_text):

    answer = 'Ищи правила на сайте http://hp-ekb.ru/'

    return answer


################ поиск на сайте ########################
