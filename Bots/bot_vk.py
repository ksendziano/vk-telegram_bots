import vk_api
from Server import server
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from System.constants import VK_BOT_TOKEN

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
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    message = event.text.lower()  # сохраняем полученное сообщение
                    id = event.user_id  # сохраняем id

                    # отправляем сообщение, id, тип платформы серверу на обработку
                    answer = server.get_answer_from_server(message, id, 'vk')
                    self.vk_session.method('messages.send', {'user_id': id, 'message': answer, 'random_id': 0,
                                                             'keyboard': keyboard.get_keyboard()})

    # Метод для вызова отправки сообщения ботом в VK из других платформ
    def send_new_mes(self, user_id):
        self.vk_session.method('messages.send',
                               {'user_id': user_id, 'message': 'Приветствую в выбранном канале коммуникации!',
                                'random_id': 0, 'keyboard': keyboard.get_keyboard()})


def main():
    pass


if __name__ == '__main__':
    main()
