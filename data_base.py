import sqlite3

#Singleton
__connection = None

#Подключение к БД по имени
def get_connection():
    global __connection
    if __connection is None:
        __connection = sqlite3.connect('users_and_quests.db', check_same_thread=False) 
    return __connection


def init_db(force: bool = False):

    conn = get_connection()
    c = conn.cursor()

    if force:
        #c.execute('DROP TABLE IF EXISTS questions')
        c.execute('DROP TABLE IF EXISTS users')

    #Создание таблицы вопросов и ответов
    c.execute('''CREATE TABLE IF NOT EXISTS questions (
        id_quest INTEGER, 
        text_quest TEXT, 
        text_quest_answer TEXT
        )''')
    conn.commit()

    #Создание таблицы id пользователей
    c.execute('''CREATE TABLE IF NOT EXISTS users(
        id_teleg INTEGER, 
        id_vk INTEGER, 
        id_last_message INTEGER,
        ready_to_change TEXT
        )''')
    conn.commit()    


#Сохранение id вк или телеги нового пользователя: возвращает True, если пользователь новый
def save_user_id(user_id, type_of_messenger):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id_teleg, id_vk from users')  
    rows = c.fetchall()
    i = 0
    if(type_of_messenger == 'vk'):                        #Если ни в одной строке таблицы не нашлось такого id,  
        while (i < len(rows) and rows[i][1] != user_id):  #то пользователь новый, возвращаем True
            i += 1
        if(len(rows) - i == 0):
            c.execute('INSERT INTO users (id_vk, ready_to_change) VALUES (?, ?)', (user_id, 'false')) #Выставляем новым пользователям поле таблицы ready_to_change
            conn.commit()                                                                             #по умолчанию false и возвращаем True, т.к. был добавлен 
            return True                                                                               #новый пользователь
    elif(type_of_messenger == 'teleg'):                   #Если ни в одной строке таблицы не нашлось такого id, то пользователь новый
        while (i < len(rows) and rows[i][0] != user_id):  #то пользователь новый, возвращаем True
            i += 1
        if(len(rows) - i == 0):
            c.execute('INSERT INTO users (id_teleg, ready_to_change) VALUES (?, ?)', (user_id, 'false'))
            conn.commit()
            return True
    return False                                           #Если id уже есть в базе, и пользователь просто так написал /start,
                                                           #то возвращаем False

def save_quest_id(user_id, quest_id):
    conn = get_connection()
    c = conn.cursor()
    if(quest_id == 3):
        c.execute('UPDATE users set id_last_message = ?, ready_to_change = ?  WHERE id_teleg = ? OR id_vk = ?', (quest_id, 'true', user_id, user_id))
    else:  
        c.execute('UPDATE users set id_last_message = ?, ready_to_change = ?  WHERE id_teleg = ? OR id_vk = ?', (quest_id, 'false', user_id, user_id)) 
    conn.commit()

if __name__ == '__main__':
    init_db()