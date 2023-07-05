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

#### файл настроек
import settings_bot
from datetime import datetime
import time

bot = telebot.TeleBot(settings_bot.bot_token, parse_mode=None)

##################### подключение к БД ######################
import httplib2
import apiclient
from oauth2client.service_account import ServiceAccountCredentials

spreadsheet_id = settings_bot.spreadsheet_id
CREDENTIALS_FILE = settings_bot.CREDENTIALS_FILE
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets',
                                                                                  'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)

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
    bot.reply_to(message, 'Если вы есть в отдельной базе МГ, то регистрация пройдет автоматически.')
    bot.reply_to(message, 'Иначе вы продолите получать эти сообщения, если так, свяжитесь с представителем ОТ.')
    
    return None


@bot.message_handler(func=is_private_and_unregistered)
def main_func(message):

    ##### только кнопка назад ####
    markup_back = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("Вернуться в главное меню")
    markup_back.add(btn)
    #####

    if (message.text == "Новый запрос"):
        bot.send_message(message.chat.id,
                         text="Пишите, что у вас там...")
        bot.register_next_step_handler(message, put_request)

    elif (message.text == "Вернуться в главное меню") or (message.text == "Начать использовать!"):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Новый запрос")
        btn2 = types.KeyboardButton("Уточнение по запросу")
        btn3 = types.KeyboardButton("Открытые заявки")
        btn4 = types.KeyboardButton("Информация")
        markup.add(btn1, btn2, btn3, btn4)
        bot.send_message(message.chat.id,
                         text="Привет, {0.first_name}! Рад снова видеть, что делаем?".format(message.from_user),
                         reply_markup=markup)

    elif (message.text == "Информация"):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Вернуться в главное меню")
        bot.send_message(message.chat.id, text="Общая информация:\n"
                                               "Я помогаю связывать с ОТ, выберите Новый запрос для создания обращения", reply_markup=markup)

    elif (message.text == "Уточнение по запросу"):
        markup_req = types.ReplyKeyboardMarkup(resize_keyboard=True)
        list_of_req = user_ask_num(message.from_user.username)
        for req in list_of_req:
            btn_req = types.KeyboardButton(req)
            markup_req.add(btn_req)
        btn = types.KeyboardButton("Вернуться в главное меню")
        markup_req.add(btn)
        if bool(list_of_req):
            bot.send_message(message.chat.id, text="Выберете ваш запрос или введите число руками, уточнение можно добавить только по запросу где нет ответа от ОТ".format(message.from_user), reply_markup=markup_req) 
            bot.register_next_step_handler(message, put_request_add_ask)
        else:
            bot.send_message(message.chat.id, text="У вас нет запросов сделайте новый запрос".format(message.from_user), reply_markup=markup_req) 


    elif (message.text == "Открытые заявки"):
        markup_req = types.ReplyKeyboardMarkup(resize_keyboard=True)
        list_of_req = user_ask_num(message.from_user.username)
        for req in list_of_req:
            btn_req = types.KeyboardButton(req)
            markup_req.add(btn_req)
        btn = types.KeyboardButton("Вернуться в главное меню")
        markup_req.add(btn)
        if bool(list_of_req):
            bot.send_message(message.chat.id, text="Выберете ваш запрос или введите число руками".format(message.from_user), reply_markup=markup_req) 
            bot.register_next_step_handler(message, put_request_text_to_user)
        else:
            bot.send_message(message.chat.id, text="У вас нет запросов сделайте новый запрос".format(message.from_user), reply_markup=markup_req) 


####
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn4 = types.KeyboardButton("Вернуться в главное меню")
        markup.add(btn4)
        bot.send_message(message.chat.id, text="На такую комманду я не запрограммирован", reply_markup=markup)


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
        bot.send_message(message.chat.id, text="Регистрация неудалась так как пользователь не найден в базе ОТ".format(message.from_user), reply_markup=markup)

    return None

def put_request(message):

    now = datetime.now()
    now = now.strftime("%Y.%m.%d %H:%M")

    if len(message.text) > 1000:
        bot.send_message(message.chat.id, 'Слишком длинный запрос, сформлируйте как нибудь покороче.')
        message.text = "Вернуться в главное меню"
        main_func(message)
        return None



    values = service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range="Запросы!A1",
        valueInputOption="USER_ENTERED",
        body={
            "values": [['id', now, now, message.from_user.id, message.from_user.username, message.chat.id, message.text, 'У: ']]
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
                         text=f"Вашему запросу присвоен номер {inserted_row_number}, сохраните его если вам потребуется уточнение, ответ ОТ будет здесь же после обработки запроса.".format(message.from_user),
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
        target_cell_range_ask_2 = f"Запросы!H{target_row_index}"  
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=target_cell_range_ask_2).execute()
        target_cell_range_answer = f"Запросы!I{target_row_index}" 
        ask_2 = result.get('values', [])
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=target_cell_range_answer).execute() 
        answer = result.get('values', [])
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

    # Задайте число для поиска
    search_number = message.text

    markup_back = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("Вернуться в главное меню")
    markup_back.add(btn)

    bot.send_message(message.chat.id, text="Что выходите добавить к заявке?".format(message.from_user), reply_markup=markup_back) 
    bot.register_next_step_handler(message, save_add, search_number)
 
    return None

def save_add(message, search_number):

    new_text = message.text
    now = datetime.now()
    now = now.strftime("%Y.%m.%d %H:%M")

    if len(message.text) > 1000:
        bot.send_message(message.chat.id, 'Слишком длинный запрос, сформлируйте как нибудь покороче.')
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

    
        #print(f"Ячейка {target_cell_range} успешно обновлена.")
    else:
        #print(f"Строка с числом {search_number} не найдена.")
        bot.send_message(message.chat.id, 'Ошибка при сохранении сообщения, придется идти ногами.')

    bot.send_message(message.chat.id, 'Уточнение сохранено.')

    message.text = "Вернуться в главное меню"
    main_func(message)

    return None


def user_ask_num(username):

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
        not_already_answer_ot = True
        if len(row) > 9:
            if (row[9]) == '1':
                not_already_answer_ot = False
        if row and row[4] == compare_value and not_already_answer_ot: 
            matching_rows.append(i + 1)  # Индекс строки начинается с 1

    return matching_rows

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