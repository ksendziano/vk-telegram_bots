import threading
from Bots import bot_teleg, bot_vk
from DataBase import data_base
from System import constants
from sqlalchemy import select, or_


# При старте сервера создаются потоки с экземплярами ботов
def main():
    t1 = threading.Thread(target=bot_teleg.Bot)
    t2 = threading.Thread(target=bot_vk.Bot)
    t1.start()
    t2.start()
    t1.join()
    t2.join()


# Метод get_answer_from_server возвращает ответ на вопрос, если было найдено сходство с БД.
# Params передаются в классах ботов: new_str - новое сообщение от пользователя, id - id пользователя,
# type_of_messenger - тип мессенджера.
def get_answer_from_server(new_str, id, type_of_messenger):
    # Если новый пользователь написал /(s)Start, то сохраняем его id из мессенджера в качестве нового пользователя,
    # Иначе подключаемся к БД с базой вопросов и ответов и возвращаем ответ из БД в случае совпадения.
    if new_str == constants.START_COMMAND:
        # data_base.save_user_id() возвращает либо True, либо False в зависимости от наличия id в БД
        if data_base.save_user_id(id, type_of_messenger):
            return constants.STR_NEW_USER
        # Если зареганный пользователь опять написал /start
        else:
            return constants.STR_START_AGAIN

    # Если пользователь написал команду /(h)Help
    elif new_str == constants.HELP_COMMAND:
        return constants.ANSWER_FOR_HELP_COMMAND

    # Если введена цифра выбора мессенджера при смене канала коммуникации
    elif (new_str == constants.VK_MESSENGER['messenger_choice'] or
          new_str == constants.TELEGRAM_MESSENGER['messenger_choice']):
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
    engine = data_base.get_connection()
    users_table = data_base.get_users_table()
    rows = engine.execute(
        select([users_table.c.ready_to_change]).where(
            or_(users_table.c.id_teleg == id, users_table.c.id_vk == id)))
    # Params: row[0] == bool: ready_to_change
    for row in rows:
        if row[0] == 'true':
            return change_platform(new_str, id, type_of_messenger)


def send_message_in_new_platform(new_str, id, type_of_messenger):
    new_id = cast_to_int(new_str)
    engine = data_base.get_connection()
    users_table = data_base.get_users_table()
    # Params: row[0] == id_last_message, row[1] == bool: ready_to_change
    # Прислали из вк айди на телегу
    if type_of_messenger == constants.VK_MESSENGER['messenger_name']:
        rows = engine.execute(
            select([users_table.c.id_last_message, users_table.c.ready_to_change]).where(users_table.c.id_vk == id))
        for row in rows:
            if row[1] == 'true' and row[0] == 32:
                engine.execute(users_table.update().where(users_table.c.id_vk == id).values(
                    id_teleg=new_id, ready_to_change='false'))
                bot_teleg.Bot.send_new_mes(bot_teleg.Bot, new_id)
                return constants.STR_ID_WAS_SAVED

    # Прислали из телеги айди на вк
    elif type_of_messenger == constants.TELEGRAM_MESSENGER['messenger_name']:
        engine = data_base.get_connection()
        users_table = data_base.get_users_table()
        rows = engine.execute(
            select([users_table.c.id_last_message, users_table.c.ready_to_change]).where(users_table.c.id_teleg == id))
        for row in rows:
            if row[1] == 'true' and row[0] == 31:
                engine.execute(users_table.update().where(users_table.c.id_teleg == id).values(
                    id_vk=new_id, ready_to_change='false'))
                bot_vk.Bot.send_new_mes(bot_vk.Bot, new_id)
                return constants.STR_ID_WAS_SAVED


def get_answer_from_data_base(new_str, id):
    engine = data_base.get_connection()
    quests_table = data_base.get_quest_table()
    rows = engine.execute(
        select([quests_table.c.id_quest, quests_table.c.text_quest, quests_table.c.text_quest_answer]))
    # Params: row[0] == id_quest, row[1] == text_quest, row[2] == text_quest_answer
    for row in rows:
        # Получаем массив элементов из строки text_quest, варианты которой разделены / и ищем сходства
        for i in range(len(row[1].split('/'))):
            if row[1].split('/')[i].startswith(new_str):
                id_quest = row[0]
                data_base.save_quest_id(id, id_quest)
                return row[2]
            i += 1


# Метод проверяет возможность для смены канала: если имеется нужный id - отправляет сообщение и меняет канал,
# если нет id, то просит его ввести.
def change_platform(new_str, id, type_of_messenger):
    engine = data_base.get_connection()
    users_table = data_base.get_users_table()
    rows = engine.execute(
        select([users_table.c.id_teleg, users_table.c.id_vk, users_table.c.ready_to_change]).where(
            or_(users_table.c.id_teleg == id, users_table.c.id_vk == id)))
    # Params: row[0] == id_teleg, row[1] == id_vk, row[2] == bool: ready_to_change
    for row in rows:
        # защита от дурака: пользователь был в том же мессенджере, который выбрал
        if (type_of_messenger == constants.VK_MESSENGER['messenger_name'] and
                new_str == constants.VK_MESSENGER['messenger_choice'] or
                type_of_messenger == constants.TELEGRAM_MESSENGER['messenger_name'] and
                new_str == constants.TELEGRAM_MESSENGER['messenger_choice']):
            engine.execute(users_table.update().where(
                or_(users_table.c.id_teleg == id, users_table.c.id_vk == id)).values(
                ready_to_change='false'))
            return constants.STR_RIGHT_CHANNEL

        # если были в вк и уходим в телегу
        elif type_of_messenger == constants.VK_MESSENGER['messenger_name'] and \
                new_str == constants.TELEGRAM_MESSENGER['messenger_choice']:
            # при наличии id teleg
            if row[0] is not None:
                # изменяем состояние пользователя
                engine.execute(
                    users_table.update().where(users_table.c.id_vk == id).values(ready_to_change='false'))
                # отправляем сообщение в выбранной платформе
                bot_teleg.Bot.send_new_mes(bot_teleg.Bot, row[0])
                return constants.STR_CHANGED_FROM_VK_TO_TELEG
            else:
                # при отсутствии id teleg запрашиваем ввод id
                engine.execute(users_table.update().where(users_table.c.id_vk == id).values(id_last_message=32))
                return constants.STR_INPUT_ID_TELEG

        # если были в телеге и уходим в вк
        elif type_of_messenger == constants.TELEGRAM_MESSENGER['messenger_name'] and \
                new_str == constants.VK_MESSENGER['messenger_choice']:
            # при наличии id vk
            if row[1] is not None:
                # изменяем состояние пользователя
                engine.execute(users_table.update().where(users_table.c.id_teleg == id).values(
                    ready_to_change='false'))
                # отправляем сообщение в выбранной платформе
                bot_vk.Bot.send_new_mes(bot_vk.Bot, row[1])
                return constants.STR_CHANGE_FROM_TELEG_TO_VK
            else:
                # при отсутствии id vk запрашиваем ввод id
                engine.execute(users_table.update().where(users_table.c.id_teleg == id).values(
                    id_last_message=31))
                return constants.STR_INPUT_ID_VK


def cast_to_int(new_str):  # Метод необходим для проверки корректности введеного id при смене платформы
    try:
        if new_id := int(new_str):
            return new_id
        else:
            return None
    except ValueError:
        print("error - message is not int")


if __name__ == '__main__':
    main()
