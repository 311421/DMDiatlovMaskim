import logging
import math

import psycopg2
import telebot
from telebot import types

conn = psycopg2.connect(
    database="telebot", user='postgres', password='1234', host='localhost', port='5432'
)
conn.autocommit = True
cursor = conn.cursor()
sql = 'select * from item'
cursor.execute("SELECT * FROM item;")
result = cursor.fetchall()
print(result)
page_count = math.ceil(len(result) / 2)

bot = telebot.TeleBot('тут токен, я поленился делать энв')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

users = dict()

class UserData:
    id: int = None
    cart: list[int] = []
    message_ids = {}

    def __init__(self, id: int):
        self.id = id


def start_buttons():
    buttons = types.InlineKeyboardMarkup()
    page_button = types.InlineKeyboardButton(f"К магазину", callback_data="shop_to 1")
    right_button = types.InlineKeyboardButton("К корзине", callback_data=f"cart-refresh")
    righter_button = types.InlineKeyboardButton("Связаться с нами", callback_data=f"contact")
    righterer_button = types.InlineKeyboardButton("Условия доставки", callback_data=f"tos")
    buttons.add(page_button, right_button, righter_button, righterer_button)
    return buttons


def cart_buttons():
    buttons = types.InlineKeyboardMarkup()
    page_button = types.InlineKeyboardButton(f"К магазину", callback_data="shop_to 1")
    right_button = types.InlineKeyboardButton("Обновить корзину", callback_data=f"cart-refresh")
    righter_button = types.InlineKeyboardButton("К оплате", callback_data=f"payment")
    righterer_button = types.InlineKeyboardButton("На старт", callback_data=f"start")
    buttons.add(page_button, right_button, righter_button, righterer_button)
    return buttons

def shop_buttons(message, page):
    cursor = conn.cursor()
    sql = 'select * from item'
    cursor.execute(f"SELECT * FROM item LIMIT 2 OFFSET {(page - 1) * 2};")
    result = cursor.fetchall()
    curUser: UserData = users[message.chat.id]
    print(curUser.id)
    left = page - 1 if page != 1 else page_count
    right = page + 1 if page != page_count else 1
    buttons = types.InlineKeyboardMarkup()
    left_button = types.InlineKeyboardButton("←", callback_data=f"shop_to {left}")
    page_button = types.InlineKeyboardButton(f"{page}/{page_count}", callback_data="None")
    right_button = types.InlineKeyboardButton("→", callback_data=f"shop_to {right}")
    buy_button = types.InlineKeyboardButton("К корзине", callback_data="cart-refresh")
    righterer_button = types.InlineKeyboardButton("На старт", callback_data=f"start")
    buttons.add(left_button, page_button, right_button, buy_button, righterer_button)
    return buttons
# команда /start
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.id not in users.keys():
        print(message.chat.id not in users.keys())
        users[message.chat.id] = UserData(message.chat.id)
    cur_message = bot.send_message(message.chat.id,
                                   "Здравствуйте! Я бот-помощник сервиса Hand-made Things. Я помогу Вам познакомиться с нашим магазином и с тем, что здесь есть. Далее Вас перенаправит в меню.",
                                   reply_markup=start_buttons()).message_id
    users[message.chat.id].message_ids[message.chat.id] = [cur_message]


@bot.message_handler(commands=['cart'])
def cart_refresh(message):
    cursor = conn.cursor()
    result = []
    for item in users[message.chat.id].cart:
        cursor.execute(f"SELECT * FROM item WHERE product_id = {item};")
        result.append(cursor.fetchall()[0])
    curUser = users[message.chat.id]
    cur_message = bot.send_message(message.chat.id, "----------------Корзина----------------").message_id
    curUser.message_ids[message.chat.id] = [cur_message]
    sum = 0
    for item in result:
        msg = f"Название: {item[1]}\nОписание: {item[2]}\nЦена: {item[3]} руб."
        sum += int(item[3])
        photo_path = item[4]
        photo = open(photo_path, 'rb')
        buttons_mini = types.InlineKeyboardMarkup()
        buy_button = types.InlineKeyboardButton("Удалить из корзины", callback_data=f"from_cart {item[0]}")
        buttons_mini.add(buy_button)
        cur_message = bot.send_photo(message.chat.id, photo=photo, caption=msg, reply_markup=buttons_mini).message_id
        curUser.message_ids[message.chat.id].append(cur_message)

    cur_message = bot.send_message(message.chat.id,
                                   f"Цена товаров: {sum} руб.\nЦена доставки: 300 руб. \n Итого: {sum + 300} руб.",
                                   ).message_id
    curUser.message_ids[message.chat.id].append(cur_message)
    cur_message = bot.send_message(message.chat.id, "----------------Меню----------------",
                                   reply_markup=cart_buttons()).message_id
    curUser.message_ids[message.chat.id].append(cur_message)


@bot.message_handler(commands=['shop'])
def shop(message, page=1):
    buttons = shop_buttons(message, page)
    cur_message = bot.send_message(message.chat.id, "----------------Список товаров----------------").message_id
    cur_user: UserData = users[message.chat.id]
    cur_user.message_ids[message.chat.id] = [cur_message]

    for item in result:
        msg = f"Название: {item[1]}\nОписание: {item[2]}\nЦена: {item[3]} руб."
        photo_path = item[4]
        photo = open(photo_path, 'rb')
        buttons_mini = types.InlineKeyboardMarkup()
        buy_button = types.InlineKeyboardButton("В корзину", callback_data=f"to_cart {item[0]}")
        buttons_mini.add(buy_button)
        cur_message = bot.send_photo(message.chat.id, photo=photo, caption=msg, reply_markup=buttons_mini).message_id
        cur_user.message_ids[message.chat.id].append(cur_message)

    cur_message = bot.send_message(message.chat.id, "----------------Выбор страницы----------------",
                                   reply_markup=buttons).message_id
    cur_user.message_ids[message.chat.id].append(cur_message)


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    bot.send_message(message.from_user.id, "Я не понимаю шаманскую мову:( \n Пожалуйста, напишите /start!")


@bot.callback_query_handler(func=lambda c: True)
def callback(c):
    if 'shop_to' in c.data:
        page = c.data.split(' ')[1]
        print(type(users[c.message.chat.id].message_ids))
        for chat_id, mes_id in users[c.message.chat.id].message_ids.items():
            for i in mes_id:
                bot.delete_message(chat_id, i)
        users[c.message.chat.id].message_ids = {}
        shop(c.message, page=int(page))
    elif 'to_cart' in c.data:
        users[c.message.chat.id].cart.append(c.data.split(' ')[1])
        print(users[c.message.chat.id].cart)
        cur_message = bot.send_message(c.message.chat.id, "Товар добавлен в корзину!").message_id
        users[c.message.chat.id].message_ids[c.message.chat.id].append(cur_message)
    elif 'from_cart' in c.data:
        users[c.message.chat.id].cart.remove(c.data.split(' ')[1])
        print(users[c.message.chat.id].cart)
        cur_message = bot.send_message(c.message.chat.id, "Товар удалён из корзины!").message_id
        users[c.message.chat.id].message_ids[c.message.chat.id].append(cur_message)
    elif 'cart-refresh' in c.data:
        for chat_id, mes_id in users[c.message.chat.id].message_ids.items():
            for i in mes_id:
                bot.delete_message(chat_id, i)
        users[c.message.chat.id].message_ids = {}
        cart_refresh(c.message)
    elif 'payment' in c.data:
        for chat_id, mes_id in users[c.message.chat.id].message_ids.items():
            try:
                for i in mes_id:
                    bot.delete_message(chat_id, i)
            except:
                pass
        users[c.message.chat.id].message_ids = {}
        buttons = types.InlineKeyboardMarkup()
        buy_button = types.InlineKeyboardButton("На главную", callback_data="start")
        buttons.add(buy_button)
        cursor = conn.cursor()
        sql = f"INSERT INTO public.orders (username, cart) VALUES ('{c.message.from_user.id}', '{', '.join(users[c.message.chat.id].cart)}') RETURNING order_id"
        cursor.execute(sql)
        oid = cursor.fetchone()[0]
        bot.send_message(c.message.chat.id,
                         f"Оплата при помощи кошелька в данный момент не доступна, мы работаем на этим. \nПожалуйста,свяжитесь с @tegrasgt для оплаты и дополнительной информации\n Номер вашего заказа: {oid}",
                         reply_markup=buttons)
        users[c.message.chat.id].cart = []
    if 'start' in c.data:
        for chat_id, mes_id in users[c.message.chat.id].message_ids.items():
            for i in mes_id:
                print(chat_id, i)
                bot.delete_message(chat_id, i)

            users[c.message.chat.id].message_ids[c.message.chat.id] = []
        start(c.message)
    if 'tos' in c.data:
        try:
            for chat_id, mes_id in users[c.message.chat.id].message_ids.items():
                for i in mes_id:
                    print(chat_id, i)
                    bot.delete_message(chat_id, i)
        except:
            pass
        buttons = types.InlineKeyboardMarkup()
        buy_button = types.InlineKeyboardButton("На главную", callback_data="start")
        buttons.add(buy_button)
        cur_message = bot.send_message(c.message.chat.id,
                                       "Доставка осуществляется только по Санкт-Петербургу \n \n Важная информация о доставке: \n \nСрок доставки: Ваш заказ будет доставлен в течение 1-7 дней. \n Ответственность за доставку: Обращаем ваше внимание, что мы не несем ответственности за процесс доставки. Все вопросы, связанные с доставкой, пожалуйста, адресуйте курьерской службе. \n Благодарим вас за понимание и уверены, что вы останетесь довольны покупкой! Если у вас возникнут вопросы, не стесняйтесь обращаться к нам. \nС наилучшими пожеланиями, команда <Hand-made Things>!",
                                       reply_markup=buttons).message_id
        try:
            users[c.message.chat.id].message_ids[c.message.chat.id] = [cur_message]
        except:
            users[c.message.chat.id].message_ids[c.message.chat.id] = [cur_message]
    if 'contact' in c.data:
        try:
            for chat_id, mes_id in users[c.message.chat.id].message_ids.items():
                for i in mes_id:
                    bot.delete_message(chat_id, i)
        except:
            pass
        buttons = types.InlineKeyboardMarkup()
        buy_button = types.InlineKeyboardButton("На главную", callback_data="start")
        buttons.add(buy_button)
        cur_message = bot.send_message(c.message.chat.id,
                                       "Если у вас возникли вопросы или нужна помощь, не стесняйтесь обращаться к нашему специалисту. Мы всегда готовы помочь вам разобраться с любыми нюансами, связанными с вашим заказом или нашим интернет-магазином."
                                       "\nКак связаться с нами:"
                                       "\nДля получения оперативной поддержки, пожалуйста, напишите нашему сотруднику @tegrasgt"
                                       "\nМы ценим каждого клиента и стремимся сделать ваш опыт покупки максимально комфортным!",
                                       reply_markup=buttons).message_id
        users[c.message.chat.id].message_ids[c.message.chat.id] = [cur_message]


bot.polling(none_stop=True, interval=0)
