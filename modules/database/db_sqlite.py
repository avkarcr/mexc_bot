import logging
import datetime as dt
import time

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


Base = declarative_base()


class Token(Base):
    __tablename__ = 'tokens'
    id = Column(Integer, primary_key=True)
    record_creation_time = Column(DateTime, default=dt.datetime.now())
    user = Column(String)
    token_name = Column(String)
    trade_start_time = Column(String)
    status = Column(String)

engine = create_engine('sqlite:///tokens.db')
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def fetch_new_tokens():
    # Здесь должен быть код для запроса к API MEXC
    return []

def add_new_tokens_to_db(tokens, tokens_on_hold=[]):
    session = Session()
    for token_info in tokens:
        token = session.query(Token).filter_by(token_name=token_info).first()
        if not token:
            status = 'sell'
            if token_info in tokens_on_hold:
                status = 'hold'
            new_token = Token(
                user="avkar",
                token_name=token_info,
                trade_start_time="unknown",
                status=status,
            )
            session.add(new_token)
            logging.info(f'Token {token_info} has been added to DB')
    session.commit()
    session.close()

async def get_tokens_list() -> list:
    session = Session()
    try:
        tokens = session.query(Token.token_name).filter_by(status='sell').all()
        token_list = [token[0] for token in tokens]
        return token_list
    finally:
        session.close()
