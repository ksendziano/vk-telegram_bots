import threading
from bots import bot_teleg, bot_vk
from repository import data_base
from system import constants
from sqlalchemy import or_
from repository.entities.quest_model import Quest
from repository.entities.user_model import User


# При старте сервера создаются потоки с экземплярами ботов
def main():
    first_bot_thread = threading.Thread(target=bot_teleg.Bot)
    second_bot_thread = threading.Thread(target=bot_vk.Bot)

    first_bot_thread.start()
    second_bot_thread.start()

    first_bot_thread.join()
    second_bot_thread.join()


# Метод get_answer_from_server возвращает ответ на сообщение пользователя
# new_str - новое сообщение от пользователя, id - id пользователя, type_of_messenger - тип мессенджера.
def get_answer_from_server(new_str, id, type_of_messenger):
    if new_str == constants.START_COMMAND:
        # save_user_id() возвращает либо True, либо False в зависимости от наличия id в БД
        if save_user_id(id, type_of_messenger):
            return constants.STR_NEW_USER
        # Если зареганный пользователь опять написал /start
        else:
            return constants.STR_START_AGAIN

    # Если пользователь написал команду /(h)Help
    elif new_str == constants.HELP_COMMAND:
        return constants.ANSWER_FOR_HELP_COMMAND

    # Если введена цифра выбора мессенджера при смене канала коммуникации
    elif (new_str == constants.VK_MESSENGER['messenger_choice'] or new_str == constants.TELEGRAM_MESSENGER[
        'messenger_choice']):
        # Для оптимизации проверяем, написал ли пользователь цифру просто так или нужна смена платформы
        return check_in_db_ready_to_change(new_str, id, type_of_messenger)

    # срабатывает при вводе сообщений из цифр, ожидает ввод id
    elif cast_to_int(new_str) is not None:
        return send_message_in_new_platform(new_str, id, type_of_messenger)
    else:
        # Если ранее ответ не был получен, пытаемся получить его из БД
        return get_answer_from_data_base(new_str, id)


# Функция проверяет, есть ли необходимость смены платформы при вводе 1 или 2
def check_in_db_ready_to_change(new_str, id, type_of_messenger):
    session = data_base.get_sqlachemy_session()
    for row in session.query(User.ready_to_change).filter(or_(User.id_vk == id, User.id_teleg == id)):
        if row.ready_to_change == 'true':
            return change_platform(new_str, id, type_of_messenger)
    return constants.STR_NO_ANSWER


# Метод проверяет возможность для смены канала: если имеется нужный id - отправляет сообщение и меняет канал,
# если нет id, то просит его ввести.
def change_platform(new_str, id, type_of_messenger):
    session = data_base.get_sqlachemy_session()
    for row in session.query(User).filter(or_(User.id_vk == id, User.id_teleg == id)):
        # защита от дурака: пользователь был в том же мессенджере, который выбрал
        if (type_of_messenger == constants.VK_MESSENGER['messenger_name'] and
                new_str == constants.VK_MESSENGER['messenger_choice'] or
                type_of_messenger == constants.TELEGRAM_MESSENGER['messenger_name'] and
                new_str == constants.TELEGRAM_MESSENGER['messenger_choice']):
            row.ready_to_change = 'false'
            session.commit()
            return constants.STR_RIGHT_CHANNEL

        # если были в вк и уходим в телегу
        elif type_of_messenger == constants.VK_MESSENGER['messenger_name'] and \
                new_str == constants.TELEGRAM_MESSENGER['messenger_choice']:
            # при наличии id teleg
            if row.id_teleg is not None:
                # изменяем состояние пользователя
                row.ready_to_change = 'false'
                session.commit()
                # отправляем сообщение в выбранной платформе
                bot_teleg.Bot.send_new_mes(bot_teleg.Bot, row.id_teleg)
                return constants.STR_CHANGED_FROM_VK_TO_TELEG
            else:
                # при отсутствии id teleg запрашиваем ввод id
                row.id_last_message = constants.SYSTEM_CONSTANT_CHANGING_TO_TELEGRAM
                session.commit()
                return constants.STR_INPUT_ID_TELEG

        # если были в телеге и уходим в вк
        elif type_of_messenger == constants.TELEGRAM_MESSENGER['messenger_name'] and \
                new_str == constants.VK_MESSENGER['messenger_choice']:
            # при наличии id vk
            if row.id_vk is not None:
                # изменяем состояние пользователя
                row.ready_to_change = 'false'
                session.commit()
                # отправляем сообщение в выбранной платформе
                bot_vk.Bot.send_new_mes(bot_vk.Bot, row.id_vk)
                return constants.STR_CHANGE_FROM_TELEG_TO_VK
            else:
                # при отсутствии id vk запрашиваем ввод id
                row.id_last_message = constants.SYSTEM_CONSTANT_CHANGING_TO_VK
                session.commit()
                return constants.STR_INPUT_ID_VK


def send_message_in_new_platform(new_str, id, type_of_messenger):
    new_id = cast_to_int(new_str)
    session = data_base.get_sqlachemy_session()
    # Прислали из вк айди на телегу
    if type_of_messenger == constants.VK_MESSENGER['messenger_name']:
        rows = session.query(User.id_last_message, User.ready_to_change, User.id_teleg).filter(User.id_vk == id)
        for row in rows:
            if row.ready_to_change == 'true' and row.id_last_message == constants.SYSTEM_CONSTANT_CHANGING_TO_TELEGRAM:
                row.id_teleg = new_id
                row.ready_to_change = 'false'
                session.commit()
                bot_teleg.Bot.send_new_mes(bot_teleg.Bot, new_id)
                return constants.STR_ID_WAS_SAVED

    # Прислали из телеги айди на вк
    elif type_of_messenger == constants.TELEGRAM_MESSENGER['messenger_name']:
        rows = session.query(User).filter(User.id_teleg == id)
        for row in rows:
            if row.ready_to_change == 'true' and row.id_last_message == constants.SYSTEM_CONSTANT_CHANGING_TO_VK:
                bot_vk.Bot.send_new_mes(bot_vk.Bot, new_id)
                row.id_vk = new_id
                row.ready_to_change = 'false'
                session.commit()
                return constants.STR_ID_WAS_SAVED
    return constants.STR_NO_ANSWER


def get_answer_from_data_base(new_str, id):
    session = data_base.get_sqlachemy_session()
    rows = session.query(Quest.id_quest, Quest.text_quest, Quest.text_quest_answer)
    for row in rows:
        # Получаем массив элементов из строки text_quest, варианты которой разделены / и ищем сходства
        for i in range(len(row.text_quest.split('/'))):
            if row.text_quest.split('/')[i].startswith(new_str):
                id_quest = row.id_quest
                save_quest_id(id, id_quest)
                return row.text_quest_answer
            i += 1
    return constants.STR_NO_ANSWER


def cast_to_int(new_str):  # Метод необходим для проверки корректности введеного id при смене платформы
    try:
        if new_id := int(new_str):
            return new_id
        else:
            return None
    except ValueError:
        print("error - message is not int")


# Сохранение id нового пользователя: возвращает True, если пользователь новый
def save_user_id(user_id, type_of_messenger):
    session = data_base.get_sqlachemy_session()
    rows = session.query(User.id_teleg, User.id_vk)
    i = 0  # индекс для перебора строк
    rowcount = rows.count()  # количество строк из БД

    # Если пришло сообщение из ВК
    if type_of_messenger == constants.VK_MESSENGER['messenger_name']:
        for row in rows:
            if row.id_vk != user_id:
                i += 1
            # Если совпадений не нашлось (rowcount == i) , то пользователь новый: возвращаем True и записываем id в БД
            if rowcount - i == 0:
                session.add(User(id_vk=user_id, ready_to_change='false'))
                session.commit()
                return True

    # Если пришло сообщение из Телеги
    elif type_of_messenger == constants.TELEGRAM_MESSENGER['messenger_name']:
        for row in rows:
            if row.id_teleg != user_id:
                i += 1
            # Если совпадений не нашлось (rowcount == i) , то пользователь новый: возвращаем True и записываем id в БД
            if rowcount - i == 0:
                session.add(User(id_teleg=user_id, ready_to_change='false'))
                session.commit()
                return True
    # Если id уже есть в базе, и пользователь просто так написал /start, то возвращаем False
    return False


# Метод сохраняет id сообщений от пользователей, включая QUEST_ID_TO_START_CHANGE_PLATFORM при смене платформы
def save_quest_id(user_id, quest_id):
    session = data_base.get_sqlachemy_session()
    # Если запрос на смену платформы
    if quest_id == constants.QUEST_ID_TO_START_CHANGE_PLATFORM:
        users = session.query(User).filter(or_(User.id_teleg == user_id, User.id_vk == user_id))
        for user in users:
            user.id_last_message = quest_id
            user.ready_to_change = 'true'
        session.commit()
    else:
        users = session.query(User).filter(or_(User.id_teleg == user_id, User.id_vk == user_id))
        for user in users:
            user.id_last_message = quest_id
            user.ready_to_change = 'false'
        session.commit()


if __name__ == '__main__':
    main()
