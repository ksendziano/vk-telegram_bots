from repository.data_base import Base, get_connection
from sqlalchemy import Column, Integer, String


class User(Base):
    __tablename__ = 'users_db'

    id = Column(Integer, primary_key=True)
    id_teleg = Column(Integer)
    id_vk = Column(Integer)
    id_last_message = Column(Integer)
    ready_to_change = Column(String)


Base.metadata.create_all(get_connection())
