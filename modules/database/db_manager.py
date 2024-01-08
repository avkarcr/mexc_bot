import logging
import datetime as dt

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from utils.exceptions import DBInteractionException

Base = declarative_base()


class TokenTable(Base):
    """
    ORM для управления таблицей, включающей в себя данные по токенам
    и времени их листинга.
    Данные по времени листинга заполняются с помощью отдельной функции класса DBHandler.
    Поле status для каждого токена может принимать следующие значения:
        hold    - держим и не трогаем с помощью бота (список в config.py)
        airdrop - появились в кошельке, но время листинга в БД еще не проставлено
        set     - еще нет в кошельке (airdrop не наступил), но время листинга в БД заполнено
        sell    - готовы к продаже: есть в кошельке и время листинга установлено
        scheduled - готовые к продаже токены отправлены в шедулер для продажи на MEXC
        sold    - продано, надо удалить из БД
        missed  - не удалось продать вовремя, требуется переход на ручное управление
    """
    # todo надо менять статус на sell с сохранением lisitng при пополнении кошелька airdrop (если мы заранее в set добавили токен)
    __tablename__ = 'tokens'
    id = Column(Integer, primary_key=True)
    record_creation_time = Column(DateTime, default=dt.datetime.now())
    user = Column(String)
    token_name = Column(String, unique=True)
    trade_start_time = Column(DateTime)
    status = Column(String)


class DBHandler():
    def __init__(self, db_set):
        self.db_set = db_set
        self.engine = create_engine(db_set['db_url'])
        if db_set['drop_db_on_start']:
            Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def set_megabot(self, megabot_instance):
        self.megabot = megabot_instance

    async def write_wallet_tokens_to_db(self, tokens):
        logging.debug(f'Saving tokens to DB: {tokens}')
        session = self.Session()
        try:
            for token_name in tokens:
                token = session.query(TokenTable).filter_by(token_name=token_name).first()
                if not token:
                    status = 'airdrop'
                    if token_name in self.db_set['tokens_on_hold']:
                        status = 'hold'
                    logging.debug(f'Token {token_name} is saving to DB with status {status}')
                    new_token = TokenTable(
                        user=self.db_set['user_id'],
                        token_name=token_name,
                        trade_start_time=None,
                        status=status,
                    )
                    session.add(new_token)
                    logging.debug(f'Token {token_name} has been saved to DB')
            session.commit()
        except Exception as e:
            logging.error(f'DB operation error with tokens: {tokens}')
            raise DBInteractionException
        finally:
            session.close()

    async def get_tokens_list(self) -> list:
        session = self.Session()
        try:
            tokens = session.query(TokenTable.token_name).filter_by(status='sell').all()
            token_list = [token[0] for token in tokens]
            logging.debug(f'Got tokens list: {token_list}')
            return token_list
        except Exception as e:
            logging.error(f'Error. Can\'t get tokens list: {e}')
            raise DBInteractionException
        finally:
            session.close()

    async def change_to_sold(self, token):
        logging.debug(f'Changing status to SOLD in DB: {token}')
        session = self.Session()
        try:
            _ = session.query(TokenTable).filter(TokenTable.token_name.in_(token)).first()
            _.status = 'sold'
            session.commit()
            logging.debug(f'Token {token} changed status to SOLD in DB.')
            return
        except Exception as e:
            logging.error(f'Error. Can\'t change status to SOLD in DB: {e}')
            raise DBInteractionException
        finally:
            session.close()

    async def remove_from_db(self, removed_tokens) -> None:
        logging.debug(f'If tokens are sold, they will be removed from DB: {removed_tokens}')
        session = self.Session()
        try:
            session.query(TokenTable).filter(
                TokenTable.token_name.in_(removed_tokens),
                TokenTable.status == 'sold').delete()  # todo статус sold надо устанавливать проданным токенам
            session.commit()
            logging.debug('Sold tokens successfully removed from DB')
            return
        except Exception as e:
            logging.error(f'Error. Can\'t remove sold tokens from DB: {e}')
            raise DBInteractionException
        finally:
            session.close()

    async def set_listing_time(self, token: str, listing_time: dt) -> None:
        logging.debug(f'Setting listing time {listing_time} for the token {token}')
        session = self.Session()
        try:
            record = session.query(TokenTable).filter(TokenTable.token_name == token).first()
            if record:
                record.trade_start_time = listing_time
                record.status = 'sell'
            else:
                new_token = TokenTable(
                    user=self.db_set['user_id'],  # todo Убрать дублирование функции или переделать под merge
                    token_name=token,
                    trade_start_time=listing_time,
                    status='set',
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

    async def get_tokens_by_status(self, status) -> list:
        """
        Функция забирает из БД токены с указанным статусом.
        Возвращает список объектов таблицы TokenTable
        """
        logging.debug(f'Getting tokens with status {status} from DB')
        session = self.Session()
        result = []
        tokens = session.query(TokenTable).filter(TokenTable.status == status).all()
        for token in tokens:
            result.append(token)
            logging.debug(f'Token {token} has benn added to result.')
        session.close()
        return result

    async def schedule_sell_tokens(self):
        """
        Эта функция просматривает БД и ищет токены со статусом sell и set.
        Это токены, по которым установлено время листинга.
        Для каждого такого токена мы запускаем в планировщик задачу
        по продаже токена четко по времени.
        После этого меняем статус этих токенов на scheduled
        """
        logging.debug('Starting schedule for tokens with sell status')
        session = self.Session()
        try:
            tokens_status_set = await self.get_tokens_by_status('set')
            tokens_status_sell = await self.get_tokens_by_status('sell')
            result = tokens_status_set + tokens_status_sell
            if not result:
                logging.debug('No tokens with \'sell\' and \'set\' status in DB.')
                return False
            logging.debug('Setting up a scheduler for selling tokens on MEXC...')
            for item in result:
                token = item.token_name
                listing = item.trade_start_time
                logging.debug(f'Scheduling task for token: {token}, listing: {listing}...')
                self.megabot.schedule_task_in_time(
                    # coro=self.megabot.mexc.convert_to_mx,
                    coro=self.megabot.bot.step_1_spot_trade,
                    running_time=listing,
                    kwargs={'asset': token},
                    # kwargs={'token': token},
                )
                logging.debug(f'{token} scheduled successfully!')
            for item in result:
                logging.debug(f'Changing status in DB for token {item.token_name} to \'scheduled\'...')
                item.status = 'scheduled'
                logging.debug(f'{item.token_name} status changed successfully!')
            session.commit()
        except:
            session.rollback()
            logging.error('There are errors while selling tokens on schedule or changing status to sold in DB')
            raise DBInteractionException
        finally:
            session.close()
        # todo Чистка БД: смотрим, есть ли sold, убеждаемся, что их нет в кошельке (иначе ошибка!) и удаляем
        # Также смотрим на missed, если их нет в кошельке, значит ручное вмешательство уже было
        # и можно удалять. Ошибка при этом не возникает
