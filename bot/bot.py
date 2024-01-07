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
from modules.database.db_sqlite import (
    add_new_tokens_to_db,
    get_tokens_list,
    remove_from_db,
)


class TeleBot():
    def __init__(self, token, admin_id, timing):
        self.bot = Bot(token=token, parse_mode=ParseMode.HTML)
        self.admin_id = admin_id
        self.timing = timing
        self.dp = Dispatcher()
        self.dp.include_routers(
            start_router,
            listing_router,
            msg_router,
        )
        self.dp.mexc = None

    async def sync_database(self, set_real: set, set_stored_in_db: set) -> None:
        f_name = inspect.currentframe().f_code.co_name
        logger.debug(f'START {f_name}()')
        added = [  # todo needs improvement
            set_real - set_stored_in_db,
            '<b>NEW token(s): </b>',
            add_new_tokens_to_db,
            True,  # информировать в телеге
        ]
        removed = [
            set_stored_in_db - set_real,
            '<b>Token(s) removed: </b>',
            remove_from_db,
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
        await self.dp.mexc.update_balance()
        balance = await self.dp.mexc.get_balance()
        new_tokens = [item['asset'] for item in balance]
        await add_new_tokens_to_db(new_tokens, self.dp.mexc.tokens_on_hold)
        logger.debug(f'FINISH {f_name}()')

    async def check_new_tokens(self):
        f_name = inspect.currentframe().f_code.co_name
        logger.debug(f'START {f_name}()')
        await self.dp.mexc.update_balance()
        await self.sync_database(
            set(self.dp.mexc.tokens_to_sell),
            set(await get_tokens_list()),
        )
        logger.debug(f'FINISH {f_name}()')

    async def start_trading_cycle(self):
        now = dt.datetime.now()
        while dt.datetime.now() < now + self.timing['spot']:
            await self.bot.send_message(self.admin_id, text='Делаем что-то')
            asyncio.sleep(self.timing['delay'])

    async def edit_last_bot_msg(self):
        pass

    async def start(self) -> None:
        await self.create_db()
        scheduler = AsyncIOScheduler({'apscheduler.timezone': 'Europe/Moscow'})
        scheduler.add_job(self.check_new_tokens, 'interval', minutes=30, misfire_grace_time=120)
        # scheduler.add_job(self.convert_to_mx, 'cron', hour=15, misfire_grace_time=120)
        scheduler.start()
        try:
            await self.bot.send_message(self.admin_id, text='Bot is working...')

            await self.start_trading_cycle()

            await self.dp.start_polling(self.bot)
            logger.debug(f'Polling has ended')
        except TelegramNetworkError:
            logger.critical('No Internet connection. Quiting.')
        except TelegramAPIError:
            logger.critical('Telegram API connection error. Quiting.')
        except Exception:
            logger.critical(f'Error: {Exception}')
        finally:
            await self.bot.send_message(self.admin_id, text='Bot has been stopped.')
            await self.bot.session.close()
