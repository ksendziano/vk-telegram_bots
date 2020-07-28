from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


# Подключение к БД
def get_connection():
    engine = create_engine('postgresql+psycopg2://postgres:123456789@localhost/postgres')
    return engine


def get_sqlachemy_session():
    Session = sessionmaker(bind=get_connection()) # naming convention, Саня
    session = Session()
    return session


if __name__ == '__main__':
    pass
