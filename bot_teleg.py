import telebot
from server import find_quest, change_platform
from telebot import types

markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
change_channel_btn = types.KeyboardButton('Сменить канал коммуникации')
markup.add(change_channel_btn)

class Bot(object):
    bot = telebot.TeleBot('TOKEN')

    def send_new_mes(self, user_id):
        self.bot.send_message(user_id, 'Приветствую в выбранном канале коммуникации!', reply_markup=markup)

    def __init__(self):
        # Создание бота через токен
        @self.bot.message_handler(content_types=['text'])
        def send_message(message):
            answer = find_quest(message.text.lower(), message.from_user.id, 'teleg') #Если find_quest() что-то вернул из БД, то ответ
            if answer:
                self.bot.send_message(message.from_user.id, answer, reply_markup=markup)
            else:                                                                    #иначе...
                self.bot.send_message(message.from_user.id, "Я тебя не понимаю, не могу ответить на твой вопрос. Напиши /help.",reply_markup=markup)           

        self.bot.polling()



def main():
    pass

if __name__ == '__main__':
    main()