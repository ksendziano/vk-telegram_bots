from sqlalchemy import Column, Integer, String
from repository.data_base import Base, get_connection


class Quest(Base):
    __tablename__ = 'quests_db'

    id = Column(Integer, primary_key=True)
    id_quest = Column(Integer)
    text_quest = Column(String)
    text_quest_answer = Column(String)


Base.metadata.create_all(get_connection())
