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
    def __init__(self, token, admin_id, timing, steps, db_set, mexc_set):
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
        self.steps = steps
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

    async def start_cycle(self):
        """
        Эта функция запускает цикл продажи токена, который состоит из 3-х стадий:
        1. Продажа токена на споте - в течение timing['spot'] секунд
        2. Конвертация токена в MX - в течение timing['convert'] секунд
        3. Минимальный порог транзакции (закупка на $6 и последующая полная продажа
         актива) - в течение timing['threshold'] секунд
        """
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

    async def step_1_spot_trade(self, token):  # todo переделать под продажу
        """
        Эта функция проверяет цену токена. Если цена airdrop больше $5
        то пытается продать токен на споте. Если меньше, то ничего не делает.
        Периодичность проверки задается в TIMING['delay'].
        Длительность попытки продажи задается в конфиге параметром TIMING['spot'].
        """
        stopTimestamp = dt.datetime.now() + dt.timedelta(seconds=self.timing['spot'])
        await self.bot.send_message(self.admin_id, text=f'Starting spot trading for {token}')
        while dt.datetime.now() < stopTimestamp:
            try:
                price = await self.mexc.mexc_market.get_price(params={'symbol': token + 'USDT'})
                price = float(price['price'])
                await self.bot.send_message(self.admin_id, text=f'Проверяю цену. Цена токена {token}: {price} USDT')
                price_is_ok = (price >= 5)
                if price_is_ok:
                    logger.debug(f'Начинаем продажу токена {token}')
                    balance = await self.mexc.get_balance()
                    qty = next((item['free'] for item in balance if item['asset'] == token), None)
                    params = {
                        'symbol': token + 'USDT',
                        'side': 'SELL',
                        'type': 'MARKET',
                        'quoteOrderQty': qty,
                        'quantity': qty,
                    }
                    resp = self.mexc.mexc_trade.post_order(params)
                    await self.bot.send_message(self.admin_id, text={resp})
                    await self.bot.send_message(self.admin_id, text={resp['msg']})
                    if resp['status'] != 200:
                        logger.error(f'{token} {qty} has not been sold')
                        await self.bot.send_message(self.admin_id, text=f'{token} {qty} has not been sold')
                        continue
                    await self.bot.send_message(self.admin_id, text=f'Sold {qty} {token}')
                else:
                    await self.bot.send_message(self.admin_id, text='Minimum threshold $5 has not been met. Waiting...')
                    await asyncio.sleep(self.timing['delay'])
                    continue
                return True
            except:
                await asyncio.sleep(self.timing['delay'])

    async def step_2_convert_to_mx(self, token):
        """
        Эта функция конвертирует токен в MX.
        Периодичность проверки задается в TIMING['delay'].
        Длительность попытки продажи задается в конфиге параметром TIMING['convert'].
        """
        stopTimestamp = dt.datetime.now() + dt.timedelta(seconds=self.timing['convert'])
        await self.bot.send_message(self.admin_id, text=f'Converting token {token} to MX')
        while dt.datetime.now() < stopTimestamp:
            try:
                await self.mexc.convert_to_mx(token=token)
                await self.bot.send_message(
                    self.admin_id,
                    text=f'Токен {token} конвертирован в MX. Но это не точно...'  # todo по курсу... детали!
                )
                return True
            except:
                await asyncio.sleep(self.timing['delay'])

    async def step_3_threshold_meeting(self, token):
        """
        Эта функция закупает токен на $6 для обеспечения минимального
        порога сделки на бирже.
        После этого весь объем токена в кошельке продается по рыночной цене.
        Процедура делается TIMING['threshold'] количество раз.
        Если возникает ошибка на каждом этапе, то все прекращаем и
        пишем пользователю, что токен нуждается в ручном управлении.
        """
        pass

    async def start(self) -> None:
        await self.create_db()
        self.scheduler.add_job(
            self.check_new_tokens,
            'interval',
            minutes=self.timing['check'],
            misfire_grace_time=120
        )
        # self.scheduler.add_job(  # todo временно закомментил
        #     self.db.schedule_sell_tokens,
        #     'interval',
        #     minutes=self.timing['check'],
        #     misfire_grace_time=30
        # )
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
