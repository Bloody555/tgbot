import telebot
import random
import threading
import sqlite3
from telebot import types

# создание соединения с базой данных
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

# создание таблицы, если её не существует
cursor.execute('''CREATE TABLE IF NOT EXISTS users
                (id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT, score INTEGER)''')
conn.commit()

# создание объекта бота
bot = telebot.TeleBot()

# обработчик команды /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    # добавляем пользователя в базу данных, если его там ещё нет
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?, ?)", (user_id, username, first_name, last_name, 0))
    conn.commit()
    # отправляем приветственное сообщение с кнопками
    markup = types.ReplyKeyboardMarkup(row_width=2)
    itembtn1 = types.KeyboardButton('Орел')
    itembtn2 = types.KeyboardButton('Решка')
    markup.add(itembtn1, itembtn2)
    bot.reply_to(message, "Привет! Давай сыграем в игру \"Орел и Решка\". Выбери, что загадаешь:", reply_markup=markup)

# обработчик сообщений с текстом "Орел" или "Решка"
@bot.message_handler(func=lambda message: message.text in ['Орел', 'Решка'])
def handle_choice(message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    # генерируем случайное число: 0 - орел, 1 - решка
    coin = random.randint(0, 1)
    choice = message.text
    if coin == 0:
        result = 'Орел'
    else:
        result = 'Решка'
    if choice == result:
        # пользователь угадал
        bot.reply_to(message, f"Ты угадал! Монетка выпала {result}.")
        cursor.execute("UPDATE users SET score=score+1 WHERE id=?", (user_id,))
        conn.commit()
    else:
        # пользователь не угадал
        bot.reply_to(message, f"Ты не угадал. Монетка выпала {result}.")
        cursor.execute("SELECT score FROM users WHERE id=?", (user_id,))
        score = cursor.fetchone()[0]
        bot.reply_to(message, f"Твой счет: {score}")
        cursor.execute("SELECT id, score FROM users WHERE id!=?", (user_id,))
        rows = cursor.fetchall()
        for row in rows:
            opponent_id, opponent_score = row
            if opponent_score > score:
                result_message = f"{first_name}, твой счет: {score}. Ты проиграл пользователю @{bot.get_chat(opponent_id).username}. Его счет: {opponent_score}."
            elif opponent_score < score:
                result_message = f"{first_name}, твой счет: {score}. Ты победил пользователем @{bot.get_chat(opponent_id).username}. Его счет: {opponent_score}."
            else:
                result_message = f"{first_name}, твой счет: {score}. Ничья с пользователем @{bot.get_chat(opponent_id).username}. Его счет: {opponent_score}."
            bot.send_message(user_id, result_message, reply_markup=hide_board)
            bot.send_message(opponent_id, result_message, reply_markup=hide_board)

cursor.close()
conn.close()

def polling_thread():
    thread_id = threading.get_ident()
    with sqlite3.connect(f"users_{thread_id}.db") as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)")
        conn.commit()
    bot.polling(none_stop=True)

thread = threading.Thread(target=polling_thread)
thread.start()