import logging
import datetime as dt

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from utils.exceptions import DBInteractionException
from config import DROP_DB_ON_START

Base = declarative_base()


class Token(Base):
    __tablename__ = 'tokens'
    id = Column(Integer, primary_key=True)
    record_creation_time = Column(DateTime, default=dt.datetime.now())
    user = Column(String)
    token_name = Column(String, unique=True)
    trade_start_time = Column(DateTime)
    status = Column(String)

engine = create_engine('sqlite:///tokens.db')
if DROP_DB_ON_START:
    Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


async def add_new_tokens_to_db(tokens, tokens_on_hold=[]):
    session = Session()
    try:
        for token_name in tokens:
            token = session.query(Token).filter_by(token_name=token_name).first()
            if not token:
                status = 'sell'
                if token_name in tokens_on_hold:
                    status = 'hold'
                new_token = Token(
                    user="avkar",  # todo user -> config
                    token_name=token_name,
                    trade_start_time=None,
                    status=status,
                )
                session.add(new_token)
                logging.debug(f'Token {token_name} has been added to DB')
        session.commit()
    except Exception as e:
        logging.error(f'Error. No new tokens added to DB: {e}')
        raise DBInteractionException
    finally:
        session.close()

async def get_tokens_list() -> list:
    session = Session()
    try:
        tokens = session.query(Token.token_name).filter_by(status='sell').all()
        token_list = [token[0] for token in tokens]
        logging.debug(f'Got tokens list: {token_list}')
        return token_list
    except Exception as e:
        logging.error(f'Error. Can\'t get tokens list: {e}')
        raise DBInteractionException
    finally:
        session.close()

async def change_to_sold(token):
    logging.debug(f'Changing status to SOLD in DB: {token}')
    session = Session()
    try:
        _ = session.query(Token).filter(Token.token_name.in_(token)).first()
        _.status = 'sold'
        session.commit()
        logging.debug(f'Token {token} changed status to SOLD in DB.')
        return
    except Exception as e:
        logging.error(f'Error. Can\'t change status to SOLD in DB: {e}')
        raise DBInteractionException
    finally:
        session.close()

async def remove_from_db(removed_tokens) -> None:
    logging.debug(f'If tokens are sold, they will be removed from DB: {removed_tokens}')
    session = Session()
    try:
        session.query(Token).filter(
            Token.token_name.in_(removed_tokens),
            Token.status == 'sold').delete()  # todo статус sold надо устанавливать проданным токенам
        session.commit()
        logging.debug('Sold tokens successfully removed from DB')
        return
    except Exception as e:
        logging.error(f'Error. Can\'t remove sold tokens from DB: {e}')
        raise DBInteractionException
    finally:
        session.close()

async def set_listing_time(token: str, listing_time: dt) -> None:
    logging.debug(f'Setting listing time {listing_time} for the token {token}')
    session = Session()
    try:
        record = session.query(Token).filter(Token.token_name == token).first()
        if record:
            record.trade_start_time = listing_time
        else:
            new_token = Token(
                user="avkar",  # todo Убрать дублирование функции или переделать под merge
                token_name=token,
                trade_start_time=listing_time,
                status='sell',
            )
            session.add(new_token)
        session.commit()
        logging.debug(f'DB has been updated. Token: {token}, listing time: {listing_time}')
        return
    except Exception as e:
        logging.error(f'Error. Can\'t set listing time in DB: {e}')
        raise DBInteractionException
    finally:
        session.close()
