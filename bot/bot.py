import asyncio
import inspect
import datetime as dt

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError, TelegramNetworkError
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.handlers.messages import msg_router
from bot.handlers.start import start_router
from bot.handlers.listing import listing_router  # todo сделать в одном handler
from modules.database.db_manager import DBHandler
from modules.mexc.mexc_user import MexcAccount
from utils.decorators import async_retry


class ExtendedBot(Bot):
    def set_megabot(self, megabot_instance):
        self.megabot = megabot_instance


class MegaBot:
    def __init__(self, token, admin_id, timing, db_set, mexc_set):
        self.db = DBHandler(db_set=db_set)
        self.db.set_megabot(self)
        self.bot = ExtendedBot(token=token, parse_mode=ParseMode.HTML)
        self.bot.set_megabot(self)
        self.mexc = MexcAccount(
            mexc_host=mexc_set['mexc_host'],
            api_key=mexc_set['api_key'],
            secret_key=mexc_set['secret_key'],
            tokens_on_hold=mexc_set['tokens_on_hold'],  # todo можно убрать задвоение, в db есть
        )
        self.mexc.set_megabot(self)
        self.scheduler = AsyncIOScheduler({'apscheduler.timezone': 'Europe/Moscow'})

        self.admin_id = admin_id
        self.timing = timing
        self.dp = Dispatcher()
        self.dp.include_routers(
            start_router,
            listing_router,
            msg_router,
        )
        listing_router.megabot = self
        start_router.megabot = self

    async def sync_database(self, set_real: set, set_stored_in_db: set) -> None:
        f_name = inspect.currentframe().f_code.co_name
        logger.debug(f'START {f_name}()')
        added = [  # todo needs improvement при первом запуске говорит, что новый токен появился!
            set_real - set_stored_in_db,
            '<b>NEW token(s): </b>',
            self.db.write_wallet_tokens_to_db,
            False,  # информировать в телеге
        ]
        removed = [
            set_stored_in_db - set_real,
            '<b>Token(s) removed: </b>',
            self.db.remove_from_db,
            False,
        ]
        for status in [added, removed]:
            if status[0]:
                status[1] += f'{", ".join(status[0])}'
                await status[2](status[0])
                logger.success(f'Данные в базе данных обновлены по токенам: {status[0]}')
                if status[3]:
                    await self.bot.send_message(self.admin_id, text=status[1])
        logger.debug(f'FINISH {f_name}()')

    async def create_db(self):
        f_name = inspect.currentframe().f_code.co_name
        logger.debug(f'START {f_name}()')
        await self.mexc.update_balance()
        balance = await self.mexc.get_balance()
        new_tokens = [item['asset'] for item in balance]
        await self.db.write_wallet_tokens_to_db(new_tokens)
        logger.debug(f'FINISH {f_name}()')

    async def check_new_tokens(self):
        f_name = inspect.currentframe().f_code.co_name
        logger.debug(f'START {f_name}()')
        await self.mexc.update_balance()
        await self.sync_database(
            set(self.mexc.tokens_to_sell),
            set(await self.db.get_tokens_list()),
        )
        logger.debug(f'FINISH {f_name}()')

    async def start_cycle(self):  # todo вторым параметром лучше сделать корутину
        end_of_cycle = dt.datetime.now() + dt.timedelta(seconds=self.timing['spot'])
        while dt.datetime.now() < end_of_cycle:
            await self.bot.send_message(self.admin_id, text='Делаем конвертацию')
            result = await self.mexc.convert_to_mx('MPR')
            if result:
                await self.bot.send_message(self.admin_id, text='Конвертация ОК')
                return
            await self.bot.send_message(self.admin_id, text='Не получилось, пробуем еще раз')
            await asyncio.sleep(self.timing['delay'])

    async def edit_last_bot_msg(self):
        pass  # todo сделать

    def schedule_task_in_time(self, coro, running_time: dt, **kwargs):
        self.scheduler.add_job(coro, 'date', run_date=running_time, kwargs=kwargs)

    @async_retry(10)
    def step_1_spot_trade(self, token):  # todo доделать
        """
        Эта функция в течение 10 сек. проверяет цену токена
        если цена больше $5, то пытается продать токен на споте
        если меньше, то ничего не делает.
        Периодичность проверки - 1 секунда
        Длительность в сек. задается в конфиге параметром TIMING['spot']
        """
        price = await self.mexc.mexc_market.get_price(params = {'asset': token})
        await self.bot.send_message(self.admin_id, text=f'Проверяю цену. Цена токена {token}: {price} USDT')

    async def start(self) -> None:
        await self.create_db()
        self.scheduler.add_job(
            self.check_new_tokens,
            'interval',
            minutes=self.timing['check'],
            misfire_grace_time=120
        )
        self.scheduler.add_job(
            self.db.schedule_sell_tokens,
            'interval',
            minutes=self.timing['check'],
            misfire_grace_time=30
        )
        self.scheduler.start()
        try:
            await self.bot.send_message(self.admin_id, text='START running')
            await self.dp.start_polling(self.bot)
            logger.debug(f'Polling has ended')
        except TelegramNetworkError:
            logger.critical('No Internet connection. Quiting.')
        except TelegramAPIError:
            logger.critical('Telegram API connection error. Quiting.')
        except Exception:
            logger.critical(f'Error: {Exception}')
        finally:
            await self.bot.send_message(self.admin_id, text='STOP running')
            await self.bot.session.close()
