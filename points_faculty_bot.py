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
from func import validate_any_int
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

#c1 = types.BotCommand(command='cancel_last_score_record', description='Отмени последнее начисление')
c2 = types.BotCommand(command='grif_score', description='Добавь очков Гриффиндору')
c3 = types.BotCommand(command='slyze_score', description='Добавь очков Слизерин')
c4 = types.BotCommand(command='rave_score', description='Добавь очков Рейвенкло')
c5 = types.BotCommand(command='huff_score', description='Добавь очков Хаффлпафф')
bot.set_my_commands([c2,c3,c4,c5])

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
        message.text = "Начать использовать!"
    else:
        failure_reg(message)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Попробовать пройти регистрацию еще раз")
        markup.add(btn1)
        bot.send_message(message.chat.id, text="Регистрация не удалась, так как пользователь не найден в базе ОТ".format(message.from_user), reply_markup=markup)

    return None

## функция проверки оценки 

def check_num_mark(message, mark):


    role_name = db_sqlite.db_get_teacher_role_by_telegram_name(message.from_user.username)
    from_value = db_sqlite.db_get_teacher_from_value_by_role(role_name)
    to_value = db_sqlite.db_get_teacher_to_value_by_role(role_name)

    if mark < from_value or mark > to_value:
        bot.reply_to(message, 'Твои баллы не соответствуют твоей роли, укажи верно или я донесу куда надо')
        return True
    else:
        return False




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
    bot.reply_to(message, 'Привет!\nЭтот бот отвечает только на личные сообщения и требует регистрации.\n\nВаша регистрация пройдет автоматически, если ваш telegram аккаунт добавлен в специальный файл.\nДля регистрации вручную во время семестра обратитесь к МГ.')

    ### сначала проверяем по локальной БД ###



    try:
        if db_sqlite.db_get_teacher_name_by_telegram_name(message.from_user.username):
            #### задаем состояние чата ####
            user_states[message.chat.id] = "registrated"
            #### задаем состояние чата ####
            message.text = "Вернуться в главное меню"
            main_func(message)

            return None
        else:
            bot.reply_to(message, 'В процессе регистрации возникла ошибка, вас нет в списке преподавателей')
    except:
        pass

    '''# для всех остальных пользователей временно отключено            

        if db_check_registration_in_db(chat):
            #### задаем состояние чата ####
            user_states[message.chat.id] = "registrated"
            #### задаем состояние чата ####
            message.text = "Вернуться в главное меню"
            main_func(message)

            return None

    '''



    '''

    if is_private_and_unregistered(message):
        #### задаем состояние чата ####
        user_states[message.chat.id] = "registrated"
        #### задаем состояние чата ####
        db_insert_user_into_db(chat)
        message.text = "Вернуться в главное меню"
        main_func(message)
    else:
        bot.reply_to(message, 'В процессе регистрации возникла ошибка, свяжитесь с МГ')

    '''
    return None




# обработчик не старта, строго после
@bot.message_handler(content_types=['text'], func=lambda message: user_states.get(message.chat.id) is None)
def handle_none(message):
    bot.send_message(message.chat.id, f"Начните с команды /start , не работает в групповых чатах")
    return None


@bot.message_handler(commands=['cancel_last_score_record'])
def cancel_record(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("ДА")        
    btn2 = types.KeyboardButton("НЕТ")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, text="Вы уверены что хотите отменить свое прошлое начисление?".format(message.from_user), reply_markup=markup) 
    bot.register_next_step_handler(message, cancel_record_end)

def cancel_record_end(message):

    if message.text == 'ДА':
        text = db_delete_last_record_from_school_scores(message.from_user.username)
        bot.send_message(message.chat.id, text=text)
    else:
        pass

    message.text = "Вернуться в главное меню"
    main_func(message)

##### команды добавления баллов по факультетам
@bot.message_handler(commands=['grif_score'])
def grif_score(message):

    try:
        # Разбиваем текст сообщения на части по пробелу
        command_parts = message.text.split(' ')
        chat_name = db_sqlite.db_get_teacher_name_by_telegram_name(message.from_user.username)
        
        # Проверяем, что команда имеет три части: /команда число сообщение
        if len(command_parts) >= 3:
            # Получаем число и сообщение из частей команды
            number = int(command_parts[1])
            if check_num_mark(message, number):
                message.text = "Вернуться в главное меню"
                main_func(message)
                return None

            text = ' '.join(command_parts[2:])        

            print(number, text, chat_name)

            mark_write('Гриффиндор', number, text, chat_name, message.from_user.username)        
            # Отправляем ответное сообщение в чат
            bot.reply_to(message, f"Число баллов добавлено Гриффиндору: {number}\nСообщение: {text}")
        elif len(command_parts) == 2 and validate_any_int(command_parts[1]):
            number = int(command_parts[1])
            if check_num_mark(message, number):
                message.text = "Вернуться в главное меню"
                main_func(message)
                return None
            mark_write('Гриффиндор', number, 'ПУСТО', chat_name, message.from_user.username) 
            bot.reply_to(message, f"Число баллов добавлено Гриффиндору: {number}\nСообщения нет")
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
        command_parts = message.text.split(' ')
        chat_name = db_sqlite.db_get_teacher_name_by_telegram_name(message.from_user.username)
        
        # Проверяем, что команда имеет три части: /команда число сообщение
        if len(command_parts) >= 3:
            # Получаем число и сообщение из частей команды
            number = int(command_parts[1])
            text = ' '.join(command_parts[2:])
            if check_num_mark(message, number):
                message.text = "Вернуться в главное меню"
                main_func(message)
                return None
            
            print(number, text, chat_name)

            mark_write('Слизерин', number, text, chat_name, message.from_user.username)        
            # Отправляем ответное сообщение в чат
            bot.reply_to(message, f"Число баллов добавлено Слизерин: {number}\nСообщение: {text}")
        elif len(command_parts) == 2 and validate_any_int(command_parts[1]):
            number = int(command_parts[1])
            if check_num_mark(message, number):
                message.text = "Вернуться в главное меню"
                main_func(message)
                return None
            mark_write('Слизерин', number, 'ПУСТО', chat_name, message.from_user.username) 
            bot.reply_to(message, f"Число баллов добавлено Слизерин: {number}\nСообщения нет")

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
        command_parts = message.text.split(' ')
        chat_name = db_sqlite.db_get_teacher_name_by_telegram_name(message.from_user.username)
        
        # Проверяем, что команда имеет три части: /команда число сообщение
        if len(command_parts) >= 3:
            # Получаем число и сообщение из частей команды
            number = int(command_parts[1])
            text = ' '.join(command_parts[2:])
            if check_num_mark(message, number):
                message.text = "Вернуться в главное меню"
                main_func(message)
                return None

            print(number, text, chat_name)

            mark_write('Рейвенкло', number, text, chat_name, message.from_user.username)        
            # Отправляем ответное сообщение в чат
            bot.reply_to(message, f"Число баллов добавлено Рейвенкло: {number}\nСообщение: {text}")
        elif len(command_parts) == 2 and validate_any_int(command_parts[1]):
            number = int(command_parts[1])
            if check_num_mark(message, number):
                message.text = "Вернуться в главное меню"
                main_func(message)
                return None
            mark_write('Рейвенкло', number, 'ПУСТО', chat_name, message.from_user.username) 
            bot.reply_to(message, f"Число баллов добавлено Рейвенкло: {number}\nСообщения нет")
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
        command_parts = message.text.split(' ')
        chat_name = db_sqlite.db_get_teacher_name_by_telegram_name(message.from_user.username)
        
        # Проверяем, что команда имеет три части: /команда число сообщение
        if len(command_parts) >= 3:
            # Получаем число и сообщение из частей команды
            number = int(command_parts[1])
            text = ' '.join(command_parts[2:])
            if check_num_mark(message, number):
                message.text = "Вернуться в главное меню"
                main_func(message)
                return None            

            print(number, text, chat_name)

            mark_write('Хаффлпафф', number, text, chat_name, message.from_user.username)        
            # Отправляем ответное сообщение в чат
            bot.reply_to(message, f"Число баллов добавлено Хаффлпафф: {number}\nСообщение: {text}")
        elif len(command_parts) == 2 and validate_any_int(command_parts[1]):
            number = int(command_parts[1])
            if check_num_mark(message, number):
                message.text = "Вернуться в главное меню"
                main_func(message)
                return None
            mark_write('Хаффлпафф', number, 'ПУСТО', chat_name, message.from_user.username) 
            bot.reply_to(message, f"Число баллов добавлено Хаффлпафф: {number}\nСообщения нет")
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

    role_name = db_sqlite.db_get_teacher_role_by_telegram_name(message.from_user.username)
    markup_main = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Гриффиндор")        
    btn2 = types.KeyboardButton("Хаффлпафф")
    btn3 = types.KeyboardButton("Слизерин")
    btn4 = types.KeyboardButton("Рейвенкло")
    btn5 = types.KeyboardButton("Отменить мое последнее начисление")
    btn6 = types.KeyboardButton("Детали школьных баллов")
    btn7 = types.KeyboardButton("Включить колбы")
    btn8 = types.KeyboardButton("ВЫКЛЮЧИТЬ колбы")
    param = db_sqlite.db_get_show_points_setting()

    if role_name == 'Директор' or role_name == 'Помощник директора':
        if param == 1:
            markup_main.add(btn1, btn2, btn3, btn4, btn5, btn6, btn8)
        else:
            markup_main.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7)
    else:
        markup_main.add(btn1, btn2, btn3, btn4, btn5, btn6)

    # Создаем клавиатуру для меню
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)

    if (message.text == "Вернуться в главное меню") or (message.text == "Начать использовать!"):
        bot.send_message(message.chat.id,
                         text="Привет, Волшебник(-ца)! Рад снова видеть, что делаем?".format(message.from_user),
                         reply_markup=markup_main)
    elif (message.text == "Гриффиндор"):
        faculty = "Гриффиндор"
        chat_name = db_sqlite.db_get_teacher_name_by_telegram_name(message.from_user.username)
        bot.send_message(message.chat.id, text="Если вы хотите добавить баллы выбранному факультету, то знак перед числом ставить не требуется. Если вы хотите снять баллы, то поставьте знак -".format(message.from_user), reply_markup=markup_back) 
        bot.register_next_step_handler(message, mark_req_step_three, faculty, chat_name)
    elif (message.text == "Хаффлпафф"):
        faculty = "Хаффлпафф"
        chat_name = db_sqlite.db_get_teacher_name_by_telegram_name(message.from_user.username)
        bot.send_message(message.chat.id, text="Если вы хотите добавить баллы выбранному факультету, то знак перед числом ставить не требуется. Если вы хотите снять баллы, то поставьте знак -".format(message.from_user), reply_markup=markup_back) 
        bot.register_next_step_handler(message, mark_req_step_three, faculty, chat_name)
    elif (message.text == "Слизерин"):
        faculty = "Слизерин"
        chat_name = db_sqlite.db_get_teacher_name_by_telegram_name(message.from_user.username)
        bot.send_message(message.chat.id, text="Если вы хотите добавить баллы выбранному факультету, то знак перед числом ставить не требуется. Если вы хотите снять баллы, то поставьте знак -".format(message.from_user), reply_markup=markup_back) 
        bot.register_next_step_handler(message, mark_req_step_three, faculty, chat_name)
    elif (message.text == "Рейвенкло"):
        faculty = "Рейвенкло"
        chat_name = db_sqlite.db_get_teacher_name_by_telegram_name(message.from_user.username)
        bot.send_message(message.chat.id, text="Если вы хотите добавить баллы выбранному факультету, то знак перед числом ставить не требуется. Если вы хотите снять баллы, то поставьте знак -".format(message.from_user), reply_markup=markup_back) 
        bot.register_next_step_handler(message, mark_req_step_three, faculty, chat_name)
    
    elif (message.text == "Отменить мое последнее начисление"):
        cancel_record(message)

    elif (message.text == "Включить колбы"):
        db_sqlite.db_set_show_points_to_one()
        bot.send_message(message.chat.id, text=f"Колбы включены! Обновление значений произойдет в ближайший такт".format(message.from_user), reply_markup=markup_main)

    elif (message.text == "ВЫКЛЮЧИТЬ колбы"):
        db_sqlite.db_set_show_points_to_zero()
        bot.send_message(message.chat.id, text=f"Колбы ВЫКЛЮЧЕНЫ! Следующее обновление по АПИ не будет получено колбами".format(message.from_user), reply_markup=markup_main)

    elif (message.text == "Детали школьных баллов"):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn4 = types.KeyboardButton("Вернуться в главное меню")
        markup.add(btn4)
        last_five_marks = marks_read()
        #sorted_data = sorted(last_five_marks, key=lambda x: int(x[3]))
        #sorted_data = sorted(last_five_marks, key=lambda x: int(x[3]) if x[3].isdigit() else float('inf'))
        #output = "Последние пять изменений баллов:\n"
        #for item in sorted_data:
           # output += f"Номер изменения сначала года: {item[0]}, Когда: {item[1]}, Факультет: {item[2]}, Какие изменения: {item[3]}, За что: {item[4]}, Кто: {item[5]}\n"
        bot.send_message(message.chat.id, text=f"{last_five_marks}".format(message.from_user), reply_markup=markup)
        url_doc = 'https://docs.google.com/spreadsheets/d/1RSlOpb93ngc3Iwmk2L335xokX95HSVsztUBsFmCHLNo/edit?usp=sharing'
        bot.send_message(message.chat.id, text=f"Более подробно смотри в документе {url_doc}".format(message.from_user), reply_markup=markup)

    
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn4 = types.KeyboardButton("Вернуться в главное меню")
        markup.add(btn4)
        bot.send_message(message.chat.id, text="На такую команду я не запрограммирован", reply_markup=markup)

##### функционал баллов #######

def mark_req_start(message):
    if message.text == "Отменить создание запроса":
        message.text = "Вернуться в главное меню"
        main_func(message)
        return None

    faculty = message.text
    chat_name = db_sqlite.db_get_teacher_name_by_telegram_name(message.from_user.username)
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

    if not validate_any_int(message.text):
        bot.reply_to(message, 'Надо вводить ЧИСЛО')
        message.text = "Вернуться в главное меню"
        main_func(message)
        return None

    mark = message.text
    if check_num_mark(message, int(mark)):
        message.text = "Вернуться в главное меню"
        main_func(message)
        return None
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
