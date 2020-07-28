import vk_api
import server
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from system.constants import VK_BOT_TOKEN, STR_HELLO_IN_CHOSEN_CHANEL, STR_ERROR_SEND_MESSAGE_TO_ID, VK_MESSENGER

keyboard = VkKeyboard(one_time=False)
keyboard.add_button('Сменить канал коммуникации', color=VkKeyboardColor.PRIMARY)


class Bot(object):
    vk_session = vk_api.VkApi(
        token=VK_BOT_TOKEN)
    longpoll = VkLongPoll(vk_session)
    vk = vk_session.get_api()

    def __init__(self):
        # Если пришло новое сообщение боту
        for event in self.longpoll.listen():
            #А если объединить ifы???
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    new_message_from_user = event.text.lower()  # сохраняем полученное сообщение
                    id = event.user_id  # сохраняем id # id является builtin, переименую и почитай почему так не хорошо.

                    # отправляем сообщение, id, тип платформы серверу на обработку
                    answer = server.get_answer_from_server(new_message_from_user, id, VK_MESSENGER['messenger_name']) # Тут точно все ок??
                    self.vk_session.method('messages.send', {'user_id': id, 'message': answer, 'random_id': 0,
                                                             'keyboard': keyboard.get_keyboard()})

    # Метод для вызова отправки сообщения ботом в VK из других платформ
    def send_new_mes(self, user_id):
        try:
            self.vk_session.method('messages.send',
                                   {'user_id': user_id, 'message': STR_HELLO_IN_CHOSEN_CHANEL,
                                    'random_id': 0, 'keyboard': keyboard.get_keyboard()})
        except vk_api.exceptions.ApiError:
            return STR_ERROR_SEND_MESSAGE_TO_ID


def main():
    pass


if __name__ == '__main__':
    main()
