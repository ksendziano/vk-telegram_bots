from System import constants
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, select, or_


# Подключение к БД
def get_connection():
    engine = create_engine('postgresql+psycopg2://postgres:123456789@localhost/postgres')
    return engine


def get_quest_table():
    engine = get_connection()
    quests_table_meta = MetaData(engine.connect())
    quests_table = Table('quests', quests_table_meta, autoload=True)
    return quests_table


def get_users_table():
    engine = get_connection()
    users_table_meta = MetaData(engine.connect())
    users_table = Table('users', users_table_meta, autoload=True)
    return users_table


def init_db():
    engine = get_connection()
    metadata = MetaData()
    quests_table = Table('quests', metadata,
                         Column('id', Integer, primary_key=True),
                         Column('id_quest', Integer),
                         Column('text_quest', String),
                         Column('text_quest_answer', String),
                         )
    users_table = Table('users', metadata,
                        Column('id', Integer, primary_key=True),
                        Column('id_teleg', Integer, ),
                        Column('id_vk', Integer),
                        Column('id_last_message', Integer),
                        Column('ready_to_change', String),
                        )
    metadata.create_all(engine)


# Сохранение id нового пользователя: возвращает True, если пользователь новый
def save_user_id(user_id, type_of_messenger):
    engine = get_connection()
    users_table = get_users_table()
    rows = engine.execute(select([users_table.columns.id_teleg, users_table.columns.id_vk]))

    i = 0  # индекс для перебора строк
    rowcount = rows.rowcount  # количество строк из БД

    # Если пришло сообщение из ВК
    if type_of_messenger == constants.VK_MESSENGER['messenger_name']:
        for row in rows:
            if row[1] != user_id:
                i += 1
            # Если совпадений не нашлось, то пользователь новый: возвращаем True и записываем id в БД
            if rowcount - i == 0:
                engine.execute(users_table.insert().values(id_vk=user_id, ready_to_change='false'))
                return True

    # Если пришло сообщение из Телеги
    elif type_of_messenger == constants.TELEGRAM_MESSENGER['messenger_name']:
        for row in rows:
            if row[0] != user_id:
                i += 1
            if rowcount - i == 0:
                engine.execute(users_table.insert().values(id_teleg=user_id, ready_to_change='false'))
                return True
    # Если id уже есть в базе, и пользователь просто так написал /start, то возвращаем False
    return False


# Метод сохраняет id сообщений от пользователей, включая QUEST_ID_TO_START_CHANGE_PLATFORM при смене платформы
def save_quest_id(user_id, quest_id):
    engine = get_connection()
    users_table = get_users_table()
    # Если запрос на смену платформы
    if quest_id == constants.QUEST_ID_TO_START_CHANGE_PLATFORM:
        engine.execute(
            users_table.update().where(or_(users_table.c.id_teleg == user_id, users_table.c.id_vk == user_id)).values(
                id_last_message=quest_id,
                ready_to_change='true'))
    else:
        engine.execute(
            users_table.update().where(or_(users_table.c.id_teleg == user_id, users_table.c.id_vk == user_id)).values(
                id_last_message=quest_id,
                ready_to_change='false'))


if __name__ == '__main__':
    init_db()
