
import settings_bot
from func import send_message_telegram
from datetime import datetime
import time
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

##################### подключение к БД ######################
import httplib2
import apiclient
from oauth2client.service_account import ServiceAccountCredentials

# Библиотека для работы с Google Sheets API
import gspread

spreadsheet_id = settings_bot.spreadsheet_id
CREDENTIALS_FILE = settings_bot.CREDENTIALS_FILE
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets',
                                                                                  'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)



##################### подключение к БД ######################

def check_new():

### для работы импортировать конфиг, два способа, использую второй
#credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
#httpAuth = credentials.authorize(httplib2.Http())
#service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)

    check = False

    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    gc = gspread.authorize(credentials)
    # Открытие документа
    sheet = gc.open('Test_table')
    # Выбор листа
    worksheet = sheet.get_worksheet(1)

    # получаем список всех строк
    rows = worksheet.get_all_values()
    
    # считаем количество строк с непустыми значениями
    num = 0
    for row in rows:
        num += 1
        if row[9] == '0' or row[9] == 'Отправить ответ?' or row[10] == '1':
            pass
        elif row[9] == '1' and row[10] != '1':
            send_message_telegram(f'Ответ на вашу заявку такой - {row[8]}', int(row[3]))
            worksheet.update_cell(num, 11, '1')
        else:
            send_message_telegram(f'Заявка пришла от {row[4]}, c текстом {row[6]}')

        

    return None

############ начало программы #######################

# уведомление в консоль о запуске
print('Starting....')

try:
    while True:
        check_new()
        time.sleep(settings_bot.check_time)
except Exception as err:
    send_message_telegram('Бэк бота выплюнул ошибку - ' + err, settings_bot.chat_id_tg_for_errors)





