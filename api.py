from fastapi import FastAPI
import json


import settings_bot

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