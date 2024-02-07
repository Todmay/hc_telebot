import telebot
# для разделения потоков
import threading

from telebot import types # для указание типов
import pandas as pd
import requests
import re

#### доп функции
from func import register_check
from func import register_check_ligth
from func import search_text_ehp
from func import send_message_telegram
from func import mark_write
from func import marks_all
from func import teacher_check
from func import marks_read

#### файл настроек
import settings_bot
from datetime import datetime
import time

bot = telebot.TeleBot(settings_bot.bot_token, parse_mode=None)

##################### подключение к БД ######################
import httplib2
#import apiclient
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

spreadsheet_id = settings_bot.spreadsheet_id
CREDENTIALS_FILE = settings_bot.CREDENTIALS_FILE
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets',
                                                                                  'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = build('sheets', 'v4', http=httpAuth)

##################### конец подключение к БД ######################



# Функция для проверки, является ли сообщение личным и не требует регистрации
def is_private_and_unregistered(message):
    return message.chat.type == 'private' and is_registered_user(message.from_user, message)



# Функция для проверки, зарегистрирован ли пользователь
def is_registered_user(user, message):
    # логика проверки регистрации пользователя
    # Верните True, если пользователь зарегистрирован, и False в противном случае

 ################ здесь сделать запрос в БД по реге
    try:
        reg_sign_ligth = register_check_ligth(user.username)    
        reg_sign = register_check(user.username)
    except:
        bot.reply_to(message, 'Слишком частые запросы, никак не успеть обработать, теперь придется долго ждать.')
        reg_sign = False
        reg_sign_ligth = False


    if reg_sign and not reg_sign_ligth:
        register_api_token(message)
    if not reg_sign: 
        message.text = "/start"
        register_api_token(message)
        handle_start_other(message)

    return reg_sign_ligth

@bot.message_handler(commands=['start'])
def handle_start_other(message):
    seller_telegram_id = message.from_user.id
    seller_telegram_name = message.from_user.username
    chat = message.chat.id
    print(chat)
    bot.reply_to(message, 'Привет! Это бот отвечает только на личные сообщения и требует регистрации.')
    bot.reply_to(message, 'Ваша регистрация пройдет автоматически, если ваш telegram аккаунт есть в вашем профиле allrpg.')
    bot.reply_to(message, 'Во время семестра для регистрации вручную обратитесь в Отдел Тайн')
    bot.reply_to(message, 'Если вы точно зарегистрированы, а меню вдруг пропало, то отправьте боту любой текст.')
    
    return None


@bot.message_handler(func=is_private_and_unregistered)
def main_func(message):

    ##### только кнопка назад ####
    markup_back = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("Вернуться в главное меню")
    markup_back.add(btn)
    #####

    if (message.text == "Новый запрос"):
        markup_new_req = types.ReplyKeyboardMarkup(resize_keyboard=True)
        catalog = put_req_catalog()
        for req in catalog:
            btn_req = types.KeyboardButton(req)
            markup_new_req.add(btn_req)
        btn = types.KeyboardButton("Отменить создание запроса")
        markup_new_req.add(btn)
        bot.send_message(message.chat.id,
                         text="Сначала выберите категорию запроса", reply_markup=markup_new_req)
        bot.register_next_step_handler(message, put_request_cat)

    elif (message.text == "Вернуться в главное меню") or (message.text == "Начать использовать!"):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Новый запрос")
        btn2 = types.KeyboardButton("Уточнение по запросу")
        btn3 = types.KeyboardButton("Открытые запросы")
        btn4 = types.KeyboardButton("Информация")
        btn5 = types.KeyboardButton("Закрыть запрос")
        btn6 = types.KeyboardButton("Мои закрытые запросы")
        btn7 = types.KeyboardButton("Школьные баллы")
        markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7)
        bot.send_message(message.chat.id,
                         text="Привет, Волшебник(-ца)! Рад снова видеть, что делаем?".format(message.from_user),
                         reply_markup=markup)

    elif (message.text == "Школьные баллы"):
        marks = marks_all()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=False,  one_time_keyboard = True)
        btn1 = types.KeyboardButton("Вернуться в главное меню")
        btn2 = types.KeyboardButton("Детали школьных баллов")
        btn3 = types.KeyboardButton("Внести школьные баллы")
        markup.add(btn1, btn2, btn3)
        bot.send_message(message.chat.id, text=f"Здесь вы можете посмотреть актуальные школьные баллы. \n\n{marks}".format(message.from_user), reply_markup=markup)

    elif (message.text == "Детали школьных баллов"):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn4 = types.KeyboardButton("Вернуться в главное меню")
        markup.add(btn4)
        last_five_marks = marks_read()
        #sorted_data = sorted(last_five_marks, key=lambda x: int(x[3]))
        sorted_data = sorted(last_five_marks, key=lambda x: int(x[3]) if x[3].isdigit() else float('inf'))
        output = "Последние пять изменений баллов:\n"
        for item in sorted_data:
            output += f"Номер изменения сначала года: {item[0]}, Когда: {item[1]}, Факультет: {item[2]}, Какие изменения: {item[3]}, За что: {item[4]}, Кто: {item[5]}\n"
        bot.send_message(message.chat.id, text=f"{output}".format(message.from_user), reply_markup=markup)
    
    elif (message.text == "Внести школьные баллы"):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn = types.KeyboardButton("Вернуться в главное меню")
        markup.add(btn)
        if (teacher_check(message.from_user.username)): 
            btn1 = types.KeyboardButton("Гриффиндор")
            btn2 = types.KeyboardButton("Хаффлпафф")
            btn3 = types.KeyboardButton("Слизерин")
            btn4 = types.KeyboardButton("Рейвенкло")
            markup.add(btn1, btn2, btn3, btn4)
            bot.send_message(message.chat.id, text="Выберите факультет, для которого вы хотите провести изменение текущих школьных баллов", reply_markup=markup)
            bot.register_next_step_handler(message, mark_req_start)
        else:
            bot.send_message(message.chat.id, text="А вы кто такой вообще?".format(message.from_user), reply_markup=markup) 



    elif (message.text == "Информация"):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Вернуться в главное меню")
        bot.send_message(message.chat.id, text="""Общая информация об игре \n
        Правила одним файлом - https://docs.google.com/document/d/15MHAG55Yj9iJkaWxoS0Dcc2YF5EQwEJVy8HWqVy9Qgs/edit?usp=sharing \n
        Общие сюжетные тексты - https://docs.google.com/document/d/1EhT6-PJa28-UV4VYLXuSU-GQkko_weii3LbdS-ZjALI/edit?usp=sharing \n
        Сетка ролей - https://joinrpg.ru/1173/roles/27647 \n
        """, reply_markup=markup)

    elif (message.text == "Закрыть запрос"):
        markup_req = types.ReplyKeyboardMarkup(resize_keyboard=True)
        list_of_req = user_ask_num(message.from_user.username)
        for req in list_of_req:
            btn_req = types.KeyboardButton(req)
            markup_req.add(btn_req)
        btn = types.KeyboardButton("Вернуться в главное меню")
        markup_req.add(btn)
        if bool(list_of_req):
            bot.send_message(message.chat.id, text="Выберите ваш запрос или введите число руками, закрытый запрос нельзя открыть заново, нужно будет создать новый".format(message.from_user), reply_markup=markup_req) 
            bot.register_next_step_handler(message, close_req)
        else:
            bot.send_message(message.chat.id, text="У вас нет запросов. Сделайте новый запрос".format(message.from_user), reply_markup=markup_req) 


    elif (message.text == "Мои закрытые запросы"):
        markup_req = types.ReplyKeyboardMarkup(resize_keyboard=True)
        list_of_req = user_ask_num(message.from_user.username, False)
        for req in list_of_req:
            btn_req = types.KeyboardButton(req)
            markup_req.add(btn_req)
        btn = types.KeyboardButton("Вернуться в главное меню")
        markup_req.add(btn)
        if bool(list_of_req):
            bot.send_message(message.chat.id, text="Выберите ваш запрос или введите число руками".format(message.from_user), reply_markup=markup_req) 
            bot.register_next_step_handler(message, put_request_text_to_user)
        else:
            bot.send_message(message.chat.id, text="У вас нет запросов. Сделайте новый запрос".format(message.from_user), reply_markup=markup_req) 

    elif (message.text == "Уточнение по запросу"):
        markup_req = types.ReplyKeyboardMarkup(resize_keyboard=True)
        list_of_req = user_ask_num(message.from_user.username)
        for req in list_of_req:
            btn_req = types.KeyboardButton(req)
            markup_req.add(btn_req)
        btn = types.KeyboardButton("Вернуться в главное меню")
        markup_req.add(btn)
        if bool(list_of_req):
            bot.send_message(message.chat.id, text="Выберите ваш запрос или введите число руками, уточнение можно добавить только по запросу, где нет ответа от МГ".format(message.from_user), reply_markup=markup_req) 
            bot.register_next_step_handler(message, put_request_add_ask)
        else:
            bot.send_message(message.chat.id, text="У вас нет запросов. Сделайте новый запрос".format(message.from_user), reply_markup=markup_req) 


    elif (message.text == "Открытые запросы"):
        markup_req = types.ReplyKeyboardMarkup(resize_keyboard=True)
        list_of_req = user_ask_num(message.from_user.username)
        for req in list_of_req:
            btn_req = types.KeyboardButton(req)
            markup_req.add(btn_req)
        btn = types.KeyboardButton("Вернуться в главное меню")
        markup_req.add(btn)
        if bool(list_of_req):
            bot.send_message(message.chat.id, text="Выберите ваш запрос или введите число руками".format(message.from_user), reply_markup=markup_req) 
            bot.register_next_step_handler(message, put_request_text_to_user)
        else:
            bot.send_message(message.chat.id, text="У вас нет запросов. Сделайте новый запрос".format(message.from_user), reply_markup=markup_req) 


####
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn4 = types.KeyboardButton("Вернуться в главное меню")
        markup.add(btn4)
        bot.send_message(message.chat.id, text="На такую команду я не запрограммирован", reply_markup=markup)


##### функция регистрации пользоватея
def register_api_token(message):

    now = datetime.now()
    now = now.strftime("%Y.%m.%d %H:%M")

   # Задайте значение для сравнения
    telegram_username = message.from_user.username

    reg_sign = register_check(telegram_username) 

    if reg_sign:
        values = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range="Регистрация!A1",
            valueInputOption="USER_ENTERED",
            body={
                "values": [[now, message.from_user.id, message.from_user.username, message.chat.id, 'Регистрация', message.text]]
            }
        ).execute()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Начать использовать!")
        markup.add(btn1)
        bot.send_message(message.chat.id, text="Регистрация успешна!".format(message.from_user), reply_markup=markup)
        message.text = "Информация"
    else:
        values = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range="Регистрация!A1",
            valueInputOption="USER_ENTERED",
            body={
                "values": [[now, message.from_user.id, message.from_user.username, message.chat.id, 'Попытка регистрации, нет в allrpg', message.text]]
            }
        ).execute()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Попробовать пройти регистрацию еще раз")
        markup.add(btn1)
        bot.send_message(message.chat.id, text="Регистрация не удалась, так как пользователь не найден в базе ОТ".format(message.from_user), reply_markup=markup)

    return None

def check_request_of_user(req_id, user_id):
    check = False

    response = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range="Запросы!A:E"  # Обновите диапазон ИД - ник
    ).execute()

    values = response.get('values', [])
    for i, row in enumerate(values):
        if row and str(row[0]) == str(req_id) and str(row[3]) == str(user_id):
            check = True
            break

    return check

def put_request_cat(message):

    if message.text == "Отменить создание запроса":
        message.text = "Вернуться в главное меню"
        main_func(message)
        return None
    
    req_type = message.text

    mtext = get_category_value(req_type)

    if mtext:
        pass
    else:
        mtext = "Напишите запрос одним сообщением"
    
    bot.send_message(message.chat.id, text=mtext, reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, put_request, req_type)

    return None

def put_request(message, req_type):

    now = datetime.now()
    now = now.strftime("%Y.%m.%d %H:%M")


    if len(message.text) > 1000:
        bot.send_message(message.chat.id, 'Слишком длинный запрос, сформулируйте как-нибудь покороче.')
        message.text = "Вернуться в главное меню"
        main_func(message)
        return None

    values = service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range="Запросы!A1",
        valueInputOption="USER_ENTERED",
        body={
            "values": [['id', now, now, message.from_user.id, message.from_user.username, req_type, message.text, 'У: ', '', 'нет', 'НОВЫЙ']]
        }
    ).execute()

    # Получаем номер строки, в которую произошла вставка
    inserted_row_number = values['updates']['updatedRange'].split('!')[1].split(':')[0][1:]

    # Обновляем значение в колонке "A" для соответствующей строки
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"Запросы!A{inserted_row_number}",
        valueInputOption="USER_ENTERED",
        body={
            "values": [[inserted_row_number]]
        }
    ).execute()

    

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Вернуться в главное меню")
    markup.add(btn1)
    bot.send_message(message.chat.id,
                         text=f"Вашему запросу присвоен номер {inserted_row_number}, сохраните его, если вам потребуется уточнение, ответ МГ будет здесь же после обработки запроса.".format(message.from_user),
                         reply_markup=markup)


    return None

def put_request_text_to_user(message):

    if message.text == "Вернуться в главное меню":
        main_func(message)
        return None

    if not message.text.isdigit:
        bot.send_message(message.chat.id, 'В качестве номера заявки могут быть только цифры.')
        message.text = "Вернуться в главное меню"
        main_func(message)
        return None

    if not check_request_of_user(message.text, message.from_user.id):
        bot.reply_to(message, f'Введенный номер запроса не является вашим!')
        message.text = "Вернуться в главное меню"
        main_func(message)
        return None


    # Задайте число для поиска
    search_number = message.text

    # Получите данные из таблицы
    response = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range="Запросы!A:H"  # Обновите диапазон для соответствия вашим данным
    ).execute()

    # Найдите строку, содержащую указанное число в первом столбце
    values = response.get('values', [])
    target_row_index = None
    for i, row in enumerate(values):
        if row and (row[0]) == search_number:
            target_row_index = i + 1  # Индекс строки начинается с 1
            break

    if target_row_index:
        target_cell_range_ask = f"Запросы!G{target_row_index}"  
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=target_cell_range_ask).execute()
        ask = result.get('values', [])
        target_cell_range_cat = f"Запросы!F{target_row_index}"  
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=target_cell_range_cat).execute()
        cat = result.get('values', [])
        target_cell_range_ask_2 = f"Запросы!H{target_row_index}"  
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=target_cell_range_ask_2).execute()
        target_cell_range_answer = f"Запросы!I{target_row_index}" 
        ask_2 = result.get('values', [])
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=target_cell_range_answer).execute() 
        answer = result.get('values', [])
        bot.reply_to(message, f'Номер запроса - {target_row_index}')
        bot.reply_to(message, f'Категория запроса - {cat}')
        bot.reply_to(message, f'Ваш запрос - {ask}')
        bot.reply_to(message, f'Ваше уточнение - {ask_2}')
        #bot.reply_to(message, f'Ваш запрос - {ask}')

    message.text = "Вернуться в главное меню"
    main_func(message)

    return None

def put_req_catalog():

    # Получите данные из таблицы
    response = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range="Категории!A:A"  # Обновите диапазон для соответствия вашим данным
    ).execute()

    catalog = list()

    values = response.get('values', [])

    for row in values:
        catalog.append(row[0])

    return catalog

def get_category_value(selected_category):
    # Получите данные из таблицы
    response = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range="Категории!A:B"  # Обновите диапазон для соответствия вашим данным
    ).execute()

    values = response.get('values', [])

    for row in values:
        if row and len(row) > 1 and row[0] == selected_category:
            return row[1]

    # Если категория не найдена, вернуть None или любое другое значение по вашему выбору
    return None
    


def put_request_add_ask(message):

    if message.text == "Вернуться в главное меню":
        main_func(message)
        return None

    if not message.text.isdigit:
        bot.send_message(message.chat.id, 'В качестве номера заявки могут быть только цифры.')
        message.text = "Вернуться в главное меню"
        main_func(message)
        return None

    if not check_request_of_user(message.text, message.from_user.id):
        bot.reply_to(message, f'Введенный номер запроса не является вашим!')
        message.text = "Вернуться в главное меню"
        main_func(message)
        return None

    # Задайте число для поиска
    search_number = message.text

    markup_back = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("Вернуться в главное меню")
    markup_back.add(btn)

    bot.send_message(message.chat.id, text="Что вы хотите добавить к заявке?".format(message.from_user), reply_markup=markup_back) 
    bot.register_next_step_handler(message, save_add, search_number)
 
    return None

def save_add(message, search_number):

    if message.text == "Вернуться в главное меню":
        main_func(message)
        return None   

    new_text = message.text
    now = datetime.now()
    now = now.strftime("%Y.%m.%d %H:%M")

    if len(message.text) > 1000:
        bot.send_message(message.chat.id, 'Слишком длинный запрос, сформлируйте как-нибудь покороче.')
        message.text = "Вернуться в главное меню"
        main_func(message)
        return None

    # Получите данные из таблицы
    response = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range="Запросы!A:H"  # Обновите диапазон для соответствия вашим данным
    ).execute()

    # Найдите строку, содержащую указанное число в первом столбце
    values = response.get('values', [])
    target_row_index = None
    for i, row in enumerate(values):
        if row and (row[0]) == search_number:
            target_row_index = i + 1  # Индекс строки начинается с 1
            break

    # Если найдена соответствующая строка, обновите указанную ячейку
    if target_row_index:
        target_cell_range = f"Запросы!H{target_row_index}"  

        # Получите текущее значение ячейки
        current_value = values[target_row_index - 1][7]  
        # Обновите значение в целевой ячейке, добавив новый текст к существующему
        updated_value = f"{current_value} {new_text}"  
        # Обновите значение в целевой ячейке
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=target_cell_range,
            valueInputOption="USER_ENTERED",
            body={
                "values": [[updated_value]]
            }
        ).execute()

        target_cell_range_time = f"Запросы!C{target_row_index}"

        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=target_cell_range_time,
            valueInputOption="USER_ENTERED",
            body={
                "values": [[now]]
            }
        ).execute()

        target_cell_range_status = f"Запросы!K{target_row_index}"

        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=target_cell_range_status,
            valueInputOption="USER_ENTERED",
            body={
                "values": [['УТОЧНЕНО']]
            }
        ).execute()


    
        #print(f"Ячейка {target_cell_range} успешно обновлена.")
    else:
        #print(f"Строка с числом {search_number} не найдена.")
        bot.send_message(message.chat.id, 'Лучше повторить попытку. Это же и правда осмысленно попробовать еще раз?')

    bot.send_message(message.chat.id, f'Уточнение по заяке {search_number} сохранено.')

    message.text = "Вернуться в главное меню"
    main_func(message)

    return None


def user_ask_num(username, open = True):

    # Задайте значение для сравнения
    compare_value = username

    # Получите данные из таблицы
    response = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range="Запросы!A:K"
    ).execute()

    values = response.get('values', [])
    matching_rows = []

    for i, row in enumerate(values):
        show_req = True
        if len(row) > 10:
            if (row[10] == 'ЗАКРЫТ') and open:
                show_req = False
            elif (row[10] != 'ЗАКРЫТ') and not open:
                show_req = False
        else:
            if not open: show_req = False
        if row and row[4] == compare_value and show_req: 
            matching_rows.append(i + 1)  # Индекс строки начинается с 1

    return matching_rows

def close_req(message):

    if message.text == "Вернуться в главное меню":
        main_func(message)
        return None

    if not message.text.isdigit:
        bot.send_message(message.chat.id, 'В качестве номера заявки могут быть только цифры.')
        message.text = "Вернуться в главное меню"
        main_func(message)
        return None

    if not check_request_of_user(message.text, message.from_user.id):
        bot.reply_to(message, f'Введенный номер запроса не является вашим!')
        message.text = "Вернуться в главное меню"
        main_func(message)
        return None

    # Задайте число для поиска
    search_number = message.text

    # Обновляем значение в колонке "A" для соответствующей строки
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"Запросы!K{search_number}",
        valueInputOption="USER_ENTERED",
        body={
            "values": [["ЗАКРЫТ"]]
        }
    ).execute()

    bot.reply_to(message, 'Ваш запрос закрыт')

    message.text = "Вернуться в главное меню"
    main_func(message)


    return None



def ask_rules(message):

    answer = search_text_ehp(message.text)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Вернуться в главное меню")
    markup.add(btn1)
    bot.send_message(message.chat.id,
                         text=answer.format(message.from_user),
                         reply_markup=markup)

    return None

##### функционал баллов #######

def mark_req_start(message):

    if message.text == "Отменить создание запроса":
        message.text = "Вернуться в главное меню"
        main_func(message)
        return None

    faculty = message.text
    markup_req = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("Вернуться в главное меню")
    markup_req.add(btn)
    bot.send_message(message.chat.id, text="Напишите ваше имя, если вы хотите снять или добавить баллы. Это могут сделать только сотрудники школы или старосты. Ваше имя будет видно в истории изменения баллов.".format(message.from_user), reply_markup=markup_req) 
    bot.register_next_step_handler(message, mark_req_step_two, faculty)

    return None

def mark_req_step_two(message, faculty):

    if message.text == "Отменить создание запроса":
        message.text = "Вернуться в главное меню"
        main_func(message)
        return None

    chat_name = message.text
    markup_req = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("Вернуться в главное меню")
    markup_req.add(btn)
    bot.send_message(message.chat.id, text="Если вы хотите добавить баллы выбранному факультету, то знак перед числом ставить не требуется. Если вы хотите снять баллы, то поставьте знак -".format(message.from_user), reply_markup=markup_req) 
    bot.register_next_step_handler(message, mark_req_step_three, faculty, chat_name)

    return None

def mark_req_step_three(message, faculty, chat_name):

    if message.text == "Отменить создание запроса":
        message.text = "Вернуться в главное меню"
        main_func(message)
        return None

    mark = message.text
    markup_req = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("Вернуться в главное меню")
    markup_req.add(btn)
    bot.send_message(message.chat.id, text="Кратко в одном сообщении опишите причину изменения баллов. Она будет видна в истории изменения баллов".format(message.from_user), reply_markup=markup_req) 
    bot.register_next_step_handler(message, mark_req_step_final, faculty, chat_name, mark)

    return None

def mark_req_step_final(message, faculty, chat_name, mark):

    if message.text == "Отменить создание запроса":
        message.text = "Вернуться в главное меню"
        main_func(message)
        return None

    comm = message.text
    mark_write(faculty, mark, comm, chat_name, message.from_user.username)
    bot.send_message(message.chat.id, f"Большое спасибо! Draco dormiens nunquam titillandus! - {faculty}, {chat_name}, {mark}, {comm}")
    message.text = "Вернуться в главное меню"
    main_func(message)
    
    return None


############ проверки работоспособности #####################

# Функция перезапуска бота
def restart_bot():
    # Останавливаем текущий поток
    threading.current_thread().join()

    # Запуск бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()


    return None

# Запуск бота в отдельном потоке
def run_bot():
    bot.infinity_polling()

    return None

# Функция для проверки состояния бота и перезапуска, если требуется
def check_bot_status():
    try:
            # Проверка состояния бота или выполнение других действий
            # ...

            # Если все в порядке, продолжаем выполнение
        pass
    except Exception as e:
        print('Произошла ошибка:', str(e))
        print('Перезапуск бота...')
        send_message_telegram('Произошла ошибка:' + str(e), settings_bot.chat_id_tg_for_mg_alerts)
        send_message_telegram('Перезапуск бота...', settings_bot.chat_id_tg_for_mg_alerts)

        # Выполняем перезапуск бота
        restart_bot()
    return None

############ конецпроверки работоспособности #####################

# уведомление в консоль о запуске
print('Starting....')

# Запуск бота в отдельном потоке
bot_thread = threading.Thread(target=run_bot)
bot_thread.start()

# Запуск функции проверки состояния бота
schedule_thread = threading.Thread(target=check_bot_status())
schedule_thread.start()

# обычный запуск, если его вызывать, то нужно закомментить Thread
#run_bot()
