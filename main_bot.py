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
from db_sqlite import *
from func import success_reg
from func import failure_reg
import db_sqlite
from db_sqlite import *

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

############### блок констант и кнопок ##########################

# Словарь для хранения состояний пользователей
user_states = {}

############### блок констант и кнопок ##########################


############## блок навигации ####################



############## блок навигации ####################

############## блок команд ####################
# Список команд
commands_list = [
    "/start",
    "/small_request"
]

c1 = types.BotCommand(command='small_request', description='Быстрый запрос в ОТ')

bot.set_my_commands([c1])

############## блок команд ####################




# Функция для проверки, является ли сообщение личным и не требует регистрации
def is_private_and_unregistered(message):
    return message.chat.type == 'private' and is_registered_user(message.from_user, message)

def is_private(message):
    return message.chat.type == 'private'

# Функция для проверки, зарегистрирован ли пользователь
def is_registered_user(user, message):
    # логика проверки регистрации пользователя
    # Верните True, если пользователь зарегистрирован, и False в противном случае

    try:
        #reg_sign_ligth = register_check_ligth(user.username)    
        reg_sign = register_check(user.username)
    except:
        bot.reply_to(message, 'Слишком частые запросы, никак не успеть обработать, теперь придется долго ждать.')
        reg_sign = False
        #reg_sign_ligth = False

    return reg_sign

@bot.message_handler(commands=['start'], func= is_private)
def handle_start_other(message):
    chat = int(message.chat.id)
    print(f'Новый пользователь {chat}')
    bot.reply_to(message, 'Привет!\nЭтот бот отвечает только на личные сообщения и требует регистрации.\n\nВаша регистрация пройдет автоматически, если ваш telegram аккаунт есть в вашем профиле JoinRPG.\nДля регистрации вручную во время семестра обратитесь к ОТ.')

### сначала проверяем по локальной БД ###

    try:
        if db_check_registration_in_db(chat):
            #### задаем состояние чата ####
            user_states[message.chat.id] = "registrated"
            #### задаем состояние чата ####
            message.text = "Вернуться в главное меню"
            main_func(message)

            return None
    except:
        pass

    if is_private_and_unregistered(message):
        #### задаем состояние чата ####
        user_states[message.chat.id] = "registrated"
        #### задаем состояние чата ####
        db_insert_user_into_db(chat)
        message.text = "Вернуться в главное меню"
        main_func(message)
    else:
         bot.reply_to(message, 'В процессе регистрации возникла ошибка, свяжитесь с ОТ')

    
    return None

# обработчик не старта, строго после
@bot.message_handler(content_types=['text'], func=lambda message: user_states.get(message.chat.id) is None)
def handle_none(message):
    bot.send_message(message.chat.id, f"Начните с команды /start , не работает в групповых чата")
    return None

@bot.message_handler(commands=['small_request'])
def small_request(message):

    if message.text == '/small_request':
        bot.send_message(message.chat.id, text=f"После команды нужно ввести текст, а не просто пустую команду")
        message.text = "Вернуться в главное меню"
        main_func(message)
        return None

    inserted_row_number = put_request_to_doc(message, 'БЫСТРЫЙ ЗАПРОС')
    bot.send_message(message.chat.id, text=f"Вашему запросу присвоен номер {inserted_row_number}, сохраните его, если вам потребуется уточнение, ответ ОТ будет здесь же после обработки запроса.")
    message.text = "Вернуться в главное меню"
    main_func(message)
    return None


@bot.message_handler(content_types=['text'], func=lambda message: user_states.get(message.chat.id) == "registrated")
def main_func(message):

    ##### только кнопка назад ####
    markup_back = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("Вернуться в главное меню")
    markup_back.add(btn)
    #####

    if (message.text == "Новый запрос"):
        markup_new_req = types.ReplyKeyboardMarkup(resize_keyboard=True)
        catalog = db_sqlite.db_get_catalog()
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
        markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
        bot.send_message(message.chat.id,
                         text="Привет, Волшебник(-ца)! Рад снова видеть, что делаем?".format(message.from_user),
                         reply_markup=markup)

    elif (message.text == "Информация"):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Вернуться в главное меню")
        bot.send_message(message.chat.id, text="""Общая информация об игре \n
        Группа - https://vk.com/study_seasons \n
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
            bot.send_message(message.chat.id, text="Выберите ваш запрос или введите число руками, уточнение можно добавить только по запросу, где нет ответа от ОТ".format(message.from_user), reply_markup=markup_req) 
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
def register_player(message):

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

    mtext = db_sqlite.db_get_category_id(req_type)

    if mtext:
        pass
    else:
        mtext = "Напишите запрос одним сообщением"
    
    bot.send_message(message.chat.id, text=mtext, reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, put_request, req_type)

    return None


def put_request_to_doc(message, req_type):

    now = datetime.now()
    now = now.strftime("%Y.%m.%d %H:%M")

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

    return inserted_row_number

def put_request(message, req_type):


    if len(message.text) > 1000:
        bot.send_message(message.chat.id, 'Слишком длинный запрос, сформулируйте как-нибудь покороче.')
        message.text = "Вернуться в главное меню"
        main_func(message)
        return None

    inserted_row_number = put_request_to_doc(message, req_type)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Вернуться в главное меню")
    markup.add(btn1)
    bot.send_message(message.chat.id,
                         text=f"Вашему запросу присвоен номер {inserted_row_number}, сохраните его, если вам потребуется уточнение, ответ ОТ будет здесь же после обработки запроса.".format(message.from_user),
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
