
import settings_bot
from func import send_message_telegram
from datetime import datetime, timedelta
import threading
import time
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

##################### подключение к БД ######################
import httplib2
#import apiclient
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

# Библиотека для работы с Google Sheets API
import gspread

spreadsheet_id_name = settings_bot.spreadsheet_id_name

spreadsheet_id = settings_bot.spreadsheet_id
spreadsheet_id_name = settings_bot.spreadsheet_id_name
CREDENTIALS_FILE = settings_bot.CREDENTIALS_FILE
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets',
                                                                                  'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = build('sheets', 'v4', http=httpAuth)



##################### подключение к БД ######################

def check_new():

### для работы импортировать конфиг, два способа, использую второй
#credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
#httpAuth = credentials.authorize(httplib2.Http())
#service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)

    check = False
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    # Преобразуем дату в строку в формате "YYYY-MM-DD"
    yesterday_str = yesterday.strftime('%Y-%m-%d')

    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    gc = gspread.authorize(credentials)
    # Открытие документа
    sheet = gc.open(spreadsheet_id_name)
    # Выбор листа
    worksheet = sheet.get_worksheet(1)

    # получаем список всех строк
    rows = worksheet.get_all_values()
    
    # считаем количество строк с непустыми значениями
    num = 0
    for row in rows:
        num += 1
        if row[10].lower() == 'статус запроса' or row[10].upper() == 'ЗАКРЫТ':
            pass
        elif row[9].upper() == 'ДА' and row[10].upper()  != 'ЗАКРЫТ':
            send_message_telegram(f'Ответ на вашу заявку номер {row[0]} такой: {row[8]}', int(row[3]))
            worksheet.update_cell(num, 11, 'ЗАКРЫТ')
            worksheet.update_cell(num, 10, 'ОТВЕТ ОТПРАВЛЕН')
        else:
            send_message_telegram(f'Заявка номер {row[0]} пришла от {row[4]}, категория запроса - {row[5]}, c текстом {row[6]} и уточнением {row[7]}')

    print(f'Отработал такт, дата {today}')        

    return None

############ начало программы #######################

# уведомление в консоль о запуске
print('Starting....')

'''
try:
    while True:
        check_new()
        time.sleep(settings_bot.check_time)
        print('Отработал такт')
except Exception as err:
    send_message_telegram('Бэк бота выплюнул ошибку - ' + err, settings_bot.chat_id_tg_for_errors)
    print('Бэк бота выплюнул ошибку - ' + err, settings_bot.chat_id_tg_for_errors)
'''

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
            check_new()
            time.sleep(settings_bot.check_time)
    except Exception as err:
        send_message_telegram('Бэк бота выплюнул ошибку', settings_bot.chat_id_tg_for_errors)
        print('Бэк бота выплюнул ошибку')
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
        print('Произошла ошибка бэка:', str(e))
        print('Перезапуск бэк части бота...')
        send_message_telegram('Произошла ошибка бэка:' + str(e), settings_bot.chat_id_tg_for_mg_alerts)
        send_message_telegram('ерезапуск бэк части бота...', settings_bot.chat_id_tg_for_mg_alerts)

        # Выполняем перезапуск бота
        restart_back()
    return None


'''
# Запуск бота в отдельном потоке
back_thread = threading.Thread(target=run_back)
back_thread.start()

# Запуск функции проверки состояния бэка
schedule_thread = threading.Thread(target=check_bot_status())
schedule_thread.start()
'''

check_new()