import datetime as dt
import inspect

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError, TelegramNetworkError
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.handlers.messages import msg_router
from bot.handlers.start import start_router
from modules.database.db_sqlite import (
    add_new_tokens_to_db,
    get_tokens_list,
)


class TeleBot():
    def __init__(self, token, admin_id):
        self.bot = Bot(token=token, parse_mode=ParseMode.HTML)
        self.admin_id = admin_id
        self.dp = Dispatcher()
        self.dp.include_routers(
            start_router,
            msg_router,
        )
        self.dp.mexc = None

    async def get_balance(self):
        f_name = inspect.currentframe().f_code.co_name
        logger.debug(f'START {f_name}()')
        balance = await self.dp.mexc.get_balance()
        logger.debug(f'FINISH {f_name}()')
        return balance

    async def create_db(self):
        f_name = inspect.currentframe().f_code.co_name
        logger.debug(f'START {f_name}()')
        await self.dp.mexc.update_balance()
        balance = await self.dp.mexc.get_balance()
        new_tokens = [item['asset'] for item in balance]
        add_new_tokens_to_db(new_tokens, self.dp.mexc.tokens_on_hold)
        logger.debug(f'FINISH {f_name}()')

    async def check_new_tokens(self):
        f_name = inspect.currentframe().f_code.co_name
        logger.debug(f'START {f_name}()')
        await self.dp.mexc.update_balance()
        tokens_from_db = await get_tokens_list()
        added_tokens = set(self.dp.mexc.tokens_to_sell) - set(tokens_from_db)
        if added_tokens:  # TODO если список 2 меньше, значит надо токен удалить из БД
            add_new_tokens_to_db(added_tokens)
            if len(added_tokens) == 1:
                msg = f'<b>NEW TOKEN: {list(added_tokens)[0]}</b>'
            else:
                msg = f'<b>NEW TOKENS: {", ".join(added_tokens)}</b>'
            await self.bot.send_message(self.admin_id, text=msg)
        logger.debug(f'FINISH {f_name}()')

    async def edit_last_bot_msg(self):
        pass

    async def start(self) -> None:
        await self.create_db()
        scheduler = AsyncIOScheduler({'apscheduler.timezone': 'Europe/Moscow'})
        scheduler.add_job(self.check_new_tokens, 'interval', seconds=30) #, misfire_grace_time=120)
        scheduler.start()
        try:
            await self.bot.send_message(self.admin_id, text='Bot is working...')
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
