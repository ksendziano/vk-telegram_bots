import telebot
from Server import server
from telebot import types
from System.constants import TELEGRAM_BOT_TOKEN

markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
change_channel_btn = types.KeyboardButton('Сменить канал коммуникации')
markup.add(change_channel_btn)


class Bot(object):
    bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

    # Метод для вызова отправки сообщения ботом в VK из других платформ
    def send_new_mes(self, user_id):
        self.bot.send_message(user_id, 'Приветствую в выбранном канале коммуникации!', reply_markup=markup)

    def __init__(self):
        # Создание бота через токен
        @self.bot.message_handler(content_types=['text'])
        def send_message(message):
            answer = server.get_answer_from_server(message.text.lower(), message.from_user.id, 'teleg')
            self.bot.send_message(message.from_user.id, answer, reply_markup=markup)

        self.bot.polling()


def main():
    pass


if __name__ == '__main__':
    main()
