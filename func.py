import settings_bot

##################### подключение к БД ######################
import httplib2
import apiclient
from oauth2client.service_account import ServiceAccountCredentials

# Библиотека для работы с Google Sheets API
import gspread

spreadsheet_id = '1KF_qiRYirnwIQrW-jJp9WlcIcq12suEvsCJjtlXnxZA' # googlesheet id
CREDENTIALS_FILE = 'creds.json'


credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets',
                                                                                  'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)


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
    sheet = gc.open('Test_table')
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
    sheet = gc.open('Test_table')
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

################ поиск на сайте ########################

import requests


def search_text_ehp(search_text):

    answer = 'Ищи правила на сайте http://hp-ekb.ru/'

    return answer


################ поиск на сайте ########################
