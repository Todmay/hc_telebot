from fastapi import FastAPI
import json


#### файл настроек
import settings_bot
import db_sqlite
from db_sqlite import *
from func import send_message_telegram

import threading
import time

import httplib2
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials


spreadsheet_id_name = settings_bot.spreadsheet_id_name
spreadsheet_id =  settings_bot.spreadsheet_id
CREDENTIALS_FILE = 'creds.json'


credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets',
                                                                                  'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = build('sheets', 'v4', http=httpAuth)

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "Wizard"}


@app.get("/get-scores")
def calculate_faculty_scores():

    # Подключаемся к БД и получаем данные
    connection, cursor = db_sqlite.connect_to_database()

    # Получаем данные из таблицы school_scores
    cursor.execute("SELECT house, score FROM school_scores")
    data = cursor.fetchall()

    # Инициализируем словарь для суммирования баллов по факультетам
    faculty_scores = {}

    # Обрабатываем каждую запись в таблице
    for row in data:
        if len(row) >= 2:  # Проверяем, что у нас есть необходимые столбцы
            faculty = row[0]  # Индекс столбца с факультетом
            score = row[1]  # Индекс столбца с баллами

            # Проверяем, что балл - это число
            try:
                score = float(score)

                # Если факультет уже есть в словаре, добавляем балл
                if faculty in faculty_scores:
                    faculty_scores[faculty] += score
                else:
                    # Если факультета еще нет в словаре, создаем его и добавляем балл
                    faculty_scores[faculty] = score
            except ValueError:
                # Если балл не является числом, игнорируем запись
                pass

    # Добавляем переменную ShowPoints
    ShowPointsParam = db_sqlite.db_get_show_points_setting()
    faculty_scores["ShowPoints"] = ShowPointsParam


    # Формируем словарь с результатами
    result_dict = {faculty: score for faculty, score in faculty_scores.items()}


    # Замена значений по ключам
    result_dict = {key.replace("Гриффиндор", "Grif").replace("Слизерин", "Slyze")
                  .replace("Рейвенкло", "Rave").replace("Хаффлпафф", "Huff"): value
                  for key, value in result_dict.items()}

    # Преобразование словаря обратно в JSON строку
    updated_json = json.dumps(result_dict, ensure_ascii=False)

    return updated_json

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8050)


# уведомление в консоль о запуске
print('Starting....')

def start_api():
    if __name__ == "__main__":
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8050)

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
            start_api()
            time.sleep(settings_bot.check_time)
    except Exception as err:
        send_message_telegram('АПИ бота словаил киллед', settings_bot.chat_id_tg_for_errors)
        print('АПИ бота словаил киллед')
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
        send_message_telegram('Произошла ошибка АПИ:' + str(e), settings_bot.chat_id_tg_for_mg_alerts)
        send_message_telegram('ерезапуск бэк части бота...', settings_bot.chat_id_tg_for_mg_alerts)

        # Выполняем перезапуск бота
        restart_back()
    return None



# Запуск бота в отдельном потоке
back_thread = threading.Thread(target=run_back)
back_thread.start()

# Запуск функции проверки состояния бэка
schedule_thread = threading.Thread(target=check_bot_status())
schedule_thread.start()