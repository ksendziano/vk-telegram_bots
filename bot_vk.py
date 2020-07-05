import vk_api
import server
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

keyboard = VkKeyboard(one_time=False)
keyboard.add_button('Сменить канал коммуникации', color = VkKeyboardColor.PRIMARY)

class Bot(object):
    vk_session = vk_api.VkApi(token = 'TOKEN')
    longpoll = VkLongPoll(vk_session)
    vk = vk_session.get_api()
    def __init__(self):
        #Если пришло новое сообщение боту
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:

                    message = event.text.lower() #сохраняем полученное сообщение 
                    id = event.user_id           #id
                    
                    answer = server.find_quest(message, id, 'vk') #отправляем сообщение серверу на обработку

                    if answer:                                    #Если find_quest() что-то вернул из БД, то ответ
                        self.vk_session.method('messages.send', {'user_id' : id, 'message' : answer, 'random_id' : 0, 'keyboard': keyboard.get_keyboard()})
                    else:                                         #иначе...
                        answer = 'Я тебя не понимаю, не могу ответить на твой вопрос. Напиши /help.'
                        self.vk_session.method('messages.send', {'user_id' : id, 'message' : answer, 'random_id' : 0, 'keyboard': keyboard.get_keyboard()})

    def send_new_mes(self, user_id):
        self.vk_session.method('messages.send', {'user_id' : user_id, 'message' : 'Приветствую в выбранном канале коммуникации!', 'random_id' : 0, 'keyboard': keyboard.get_keyboard()})

def main():
    pass


if __name__ == '__main__':
    main()
