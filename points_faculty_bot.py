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
from func import success_reg
from func import failure_reg
import db_sqlite
from db_sqlite import *

#### файл настроек
import settings_bot
from datetime import datetime
import time

bot = telebot.TeleBot(settings_bot.bot_faculty_points_token, parse_mode=None)





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
    "/cancel_last_score_record",
    "/grif_score",
    "/slyze_score",
    "/rave_score",
    "/huff_score"
]

c1 = types.BotCommand(command='cancel_last_score_record', description='Отмени последнее начисление')
c2 = types.BotCommand(command='grif_score', description='Добавь очков Гриффиндору')
c3 = types.BotCommand(command='slyze_score', description='Добавь очков Слизерин')
c4 = types.BotCommand(command='rave_score', description='Добавь очков Рейвенкло')
c5 = types.BotCommand(command='huff_score', description='Добавь очков Хаффлпафф')
bot.set_my_commands([c1,c2,c3,c4,c5])

############## блок команд ####################

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
        register_player(message)
    if not reg_sign: 
        message.text = "/start"
        register_player(message)
        handle_start_other(message)

    return reg_sign_ligth

@bot.message_handler(commands=['start'])
def handle_start_other(message):
    chat = int(message.chat.id)
    print(f'Новый пользователь {chat}')
    bot.reply_to(message, 'Привет!\nЭтот бот отвечает только на личные сообщения и требует регистрации.\n\nВаша регистрация пройдет автоматически, если ваш telegram аккаунт есть в вашем профиле JoinRPG.\nДля регистрации вручную во время семестра обратитесь к МГ.')

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
         bot.reply_to(message, 'В процессе регистрации возникла ошибка, свяжитесь с МГ')

    
    return None




# обработчик не старта, строго после
@bot.message_handler(content_types=['text'], func=lambda message: user_states.get(message.chat.id) is None)
def handle_none(message):
    bot.send_message(message.chat.id, f"Начните с команды /start ")
    return None


@bot.message_handler(commands=['cancel_last_score_record'])
def cancel_record(message):

    text = db_delete_last_record_from_school_scores(message.from_user.username)
    bot.send_message(message.chat.id, text=text)
    message.text = "Вернуться в главное меню"
    main_func(message)

##### команды добавления баллов по факультетам
@bot.message_handler(commands=['grif_score'])
def grif_score(message):

    try:
        # Разбиваем текст сообщения на части по пробелу
        command_parts = message.text.split()
        
        # Проверяем, что команда имеет три части: /команда число сообщение
        if len(command_parts) == 3:
            # Получаем число и сообщение из частей команды
            number = int(command_parts[1])
            text = command_parts[2]
            chat_name = db_sqlite.db_get_character_name_by_player_name(message.from_user.username)

            print(number, text, chat_name)

            mark_write('Гриффиндор', number, text, chat_name, message.from_user.username)        
            # Отправляем ответное сообщение в чат
            bot.reply_to(message, f"Число баллов добавлено Гриффиндору: {number}\nСообщение: {text}")
        else:
            bot.reply_to(message, "Неверный формат команды. Используйте /команда число сообщение")
    except ValueError:
        bot.reply_to(message, "Ошибка. Пожалуйста, укажите корректное число.")

    message.text = "Вернуться в главное меню"
    main_func(message)

@bot.message_handler(commands=['slyze_score'])
def slyze_score(message):
    try:
        # Разбиваем текст сообщения на части по пробелу
        command_parts = message.text.split()
        
        # Проверяем, что команда имеет три части: /команда число сообщение
        if len(command_parts) == 3:
            # Получаем число и сообщение из частей команды
            number = int(command_parts[1])
            text = command_parts[2]
            chat_name = db_sqlite.db_get_character_name_by_player_name(message.from_user.username)

            print(number, text, chat_name)

            mark_write('Слизерин', number, text, chat_name, message.from_user.username)        
            # Отправляем ответное сообщение в чат
            bot.reply_to(message, f"Число баллов добавлено Слизерин: {number}\nСообщение: {text}")
        else:
            bot.reply_to(message, "Неверный формат команды. Используйте /команда число сообщение")
    except ValueError:
        bot.reply_to(message, "Ошибка. Пожалуйста, укажите корректное число.")

    message.text = "Вернуться в главное меню"
    main_func(message)

@bot.message_handler(commands=['rave_score'])
def rave_score(message):
    try:
        # Разбиваем текст сообщения на части по пробелу
        command_parts = message.text.split()
        
        # Проверяем, что команда имеет три части: /команда число сообщение
        if len(command_parts) == 3:
            # Получаем число и сообщение из частей команды
            number = int(command_parts[1])
            text = command_parts[2]
            chat_name = db_sqlite.db_get_character_name_by_player_name(message.from_user.username)

            print(number, text, chat_name)

            mark_write('Рейвенкло', number, text, chat_name, message.from_user.username)        
            # Отправляем ответное сообщение в чат
            bot.reply_to(message, f"Число баллов добавлено Рейвенкло: {number}\nСообщение: {text}")
        else:
            bot.reply_to(message, "Неверный формат команды. Используйте /команда число сообщение")
    except ValueError:
        bot.reply_to(message, "Ошибка. Пожалуйста, укажите корректное число.")

    message.text = "Вернуться в главное меню"
    main_func(message)

@bot.message_handler(commands=['huff_score'])
def huff_score(message):
    try:
        # Разбиваем текст сообщения на части по пробелу
        command_parts = message.text.split()
        
        # Проверяем, что команда имеет три части: /команда число сообщение
        if len(command_parts) == 3:
            # Получаем число и сообщение из частей команды
            number = int(command_parts[1])
            text = command_parts[2]
            chat_name = db_sqlite.db_get_character_name_by_player_name(message.from_user.username)

            print(number, text, chat_name)

            mark_write('Хаффлпафф', number, text, chat_name, message.from_user.username)        
            # Отправляем ответное сообщение в чат
            bot.reply_to(message, f"Число баллов добавлено Хаффлпафф: {number}\nСообщение: {text}")
        else:
            bot.reply_to(message, "Неверный формат команды. Используйте /команда число сообщение")
    except ValueError:
        bot.reply_to(message, "Ошибка. Пожалуйста, укажите корректное число.")

    message.text = "Вернуться в главное меню"
    main_func(message)


@bot.message_handler(content_types=['text'], func=lambda message: user_states.get(message.chat.id) == "registrated")
def main_func(message):

    ##### только кнопка назад ####
    markup_back = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("Вернуться в главное меню")
    markup_back.add(btn)
    #####
    #bot.set_chat_menu_button(message.chat.id, types.MenuButtonCommands('commands'))

    # Создаем клавиатуру для меню
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)

    if (message.text == "Вернуться в главное меню") or (message.text == "Начать использовать!"):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn4 = types.KeyboardButton("Информация")
        btn7 = types.KeyboardButton("Школьные баллы")
        markup.add(btn4, btn7)
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
        sorted_data = sorted(last_five_marks, key=lambda x: int(x[3]))
        #sorted_data = sorted(last_five_marks, key=lambda x: int(x[3]) if x[3].isdigit() else float('inf'))
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

####
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn4 = types.KeyboardButton("Вернуться в главное меню")
        markup.add(btn4)
        bot.send_message(message.chat.id, text="На такую команду я не запрограммирован", reply_markup=markup)

##### функционал баллов #######

def mark_req_start(message, faculty):
    


    if message.text == "Отменить создание запроса":
        message.text = "Вернуться в главное меню"
        main_func(message)
        return None

    faculty = message.text
    chat_name = db_sqlite.db_get_character_name_by_player_name(message.from_user.username)
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
