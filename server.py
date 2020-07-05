import data_base
import bot_teleg
import bot_vk
import threading

#При старте сервера создаются потоки с экземплярами ботов
def main():
    t1 = threading.Thread(target = bot_teleg.Bot)
    t2 = threading.Thread(target = bot_vk.Bot)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

#Метод возвращает ответ на вопрос, если было найдено сходство с БД. 
#Params: new_str - само сообщение, id пользователя и тип мессенджера передаются в классах ботов.
def find_quest(new_str, id, type_of_messenger):
    #Если новый пользователь написал /(s)Start, то сохраняем его id из мессенджера в качестве нового пользователя,
    #Иначе происходит подключение к БД с базой вопросов и ответов, и в случае совпадения возвращается ответ из БД.
    #data_base.save_user_id() возвращает либо True, либо False в зависимости от наличия id в БД
    if(new_str == '/start' or new_str == '/Start'): 
        if(data_base.save_user_id(id, type_of_messenger)): 
            new__str = "Ура! Новый пользователь!"
            return new__str
        else: #Если зареганный пользователь опять написал /start
            new__str = "Я тебя уже знаю, что за шутки:D"
            return new__str
    elif(new_str == 'start' or new_str == 'Start'): 
        new__str = "Пиши /Start или /start"
        return new__str
    elif(new_str == '/help' or new_str == '/Help'): 
        new__str = "Я - бот, который умеет писать в Вконтакте и в Телеграм мотивационные цитатки! Да прибудет с тобой сила!"
        return new__str
    elif(new_str == 'help' or new_str == 'Help'): 
        new__str = "Пиши /Help или /help"
        return new__str
    elif(new_str == '1' or new_str == '2'): 
        conn = data_base.get_connection()
        cursor = conn.cursor()  
        cursor.execute("SELECT id_teleg, id_vk, ready_to_change FROM users WHERE id_teleg = ? OR id_vk = ?", (id, id)) 
        rows = cursor.fetchall()

        for row in rows:
            
            if(row[2] == 'true'):

                if(type_of_messenger == 'vk' and new_str == '1' or type_of_messenger == 'teleg' and new_str == '2'): #защита от дурака
                    new_str = 'Вы уже в нужном канале общения'
                    cursor.execute("UPDATE users set ready_to_change = ? WHERE id_vk = ? or id_teleg = ?", ('false', id, id))
                    conn.commit() 
                    return new_str

                elif(type_of_messenger == 'vk' and new_str == '2' and row[0] != None): #если были в вк и уходим в телегу при наличии id teleg
                    new_str = 'Платформа изменена с вк на телегу' 
                    cursor.execute("UPDATE users set ready_to_change = ? WHERE id_vk = ?", ('false', id))
                    conn.commit() 
                    #ДОЛЖНО ПРИХОДИТЬ СООБЩЕНИЕ ОТ БОТА В ТЕЛЕГУ, ЧТО КАНАЛ ИЗМЕНЕН
                    
                    return new_str

                elif(type_of_messenger == 'vk' and new_str == '2' and row[0] == None): #если были в вк и уходим в телегу при отсутствии id teleg
                    new_str = 'Введите ваш id в Telegram'
                    cursor.execute("UPDATE users set id_last_message = ? WHERE id_vk = ?", (32, id))
                    conn.commit() 
                    return new_str

                elif(type_of_messenger == 'teleg' and new_str == '1' and row[1] != None): #если были в телеге и уходим в вк при наличии id vk
                    new_str = 'Платформа изменена с телеги на вк' 
                    cursor.execute("UPDATE users set ready_to_change = ? WHERE id_teleg = ?", ('false', id))
                    conn.commit()
                    #ДОЛЖНО ПРИХОДИТЬ СООБЩЕНИЕ ОТ БОТА В ВК, ЧТО КАНАЛ ИЗМЕНЕН
                    bot_vk.Bot.send_new_mes(bot_vk.Bot, row[1])
                    return new_str

                elif(type_of_messenger == 'teleg' and new_str == '1' and row[1] == None): #если были в телеге и уходим в вк при отсутствии id vk
                    new_str = 'Введите ваш id в VK'
                    cursor.execute("UPDATE users set id_last_message = ? WHERE id_teleg = ?", (31, id))
                    conn.commit()
                    return new_str     

    elif(change_platform(new_str) != None and change_platform(new_str) > 3): #срабатывает после ввода id (МОЖНО ОРГАНИЗОВАТЬ ОТДЕЛЬНОМ ФУНКЦИЕЙ В data_base)
        new_id = change_platform(new_str)
        conn = data_base.get_connection()
        cursor = conn.cursor()

        if(type_of_messenger == 'vk'): #Прислали из вк айди на телегу
            cursor.execute("SELECT id_vk, id_last_message, ready_to_change FROM users WHERE id_vk = ?", (id,)) 
            rows = cursor.fetchall()
            for row in rows:
                if(row[2] == 'true' and row[1] == 32):
                    cursor.execute('UPDATE users set id_teleg = ?, ready_to_change = ? WHERE id_vk = ?', (new_id, 'false', id))
                    conn.commit()
                    #ДОЛЖНО ПРИХОДИТЬ СООБЩЕНИЕ ОТ БОТА В ТЕЛЕГУ, ЧТО КАНАЛ ИЗМЕНЕН
                    bot_teleg.Bot.send_new_mes(bot_teleg.Bot, new_id)
                    return 'ID успешно сохранен'

        elif(type_of_messenger == 'teleg'): #Прислали из телеги айди на вк
            cursor.execute("SELECT id_teleg, id_last_message, ready_to_change FROM users WHERE id_teleg = ?", (id,)) 
            rows = cursor.fetchall()  
            for row in rows:
                if(row[2] == 'true' and row[1] == 31):
                    cursor.execute('UPDATE users set id_vk = ?, ready_to_change = ?  WHERE id_teleg = ?', (new_id, 'false', id)) 
                    conn.commit()
                    #ДОЛЖНО ПРИХОДИТЬ СООБЩЕНИЕ ОТ БОТА В ВК, ЧТО КАНАЛ ИЗМЕНЕН
                    bot_vk.Bot.send_new_mes(bot_vk.Bot, new_id)
                    return 'ID успешно сохранен'
    else:
        conn = data_base.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_quest, text_quest, text_quest_answer FROM questions")
        rows = cursor.fetchall()
        #Т.к. fetchall вернул все строки вопросов и ответов tuple`ом, пробегаем по каждой части кортежа по всем строкам на поиск сравнений с БД.
        j = 0
        i = 0
        for i in range(len(rows)):
            for j in range(len(str(rows[i][1]).split('/'))):
                if((str(rows[i][1]).split('/')[j]).startswith(new_str)):#Если сообщение пользователя нашлось в БД - вовзращаем ответ
                    #Сохранение id вопроса, если нашелся ответ
                    id_quest = rows[i][0]
                    data_base.save_quest_id(id, id_quest)

                    return rows[i][2]
                j += 1
            i += 1
            j = 0
    
def change_platform(new_str): #Метод необходим для проверки корректности введеного номера при смене платформы
    try:
        new_id = int(new_str)
        if(new_id > 2):
            return new_id
        else:
            return None
    except ValueError:
        print("error")
    

if __name__ == '__main__':
    main()