import datetime as dt
import inspect

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError, TelegramNetworkError
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.handlers.messages import msg_router
from bot.handlers.start import start_router


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

    async def print_balance(self):
        f_name = inspect.currentframe().f_code.co_name
        logger.debug(f'START {f_name}()')
        balance = await self.dp.mexc.get_balance()
        await self.bot.send_message(self.admin_id, text=balance)
        logger.debug(f'FINISH {f_name}()')

    async def update_balance(self):
        f_name = inspect.currentframe().f_code.co_name
        logger.debug(f'START {f_name}()')
        await self.dp.mexc.update_balance()
        logger.debug(f'FINISH {f_name}()')

    async def start(self) -> None:
        scheduler = AsyncIOScheduler({'apscheduler.timezone': 'Europe/Moscow'})
        # scheduler.add_job(self.print_balance, 'cron', hour=14, minute=12)
        scheduler.add_job(self.print_balance, 'interval', minutes=1)
        scheduler.add_job(self.update_balance, 'interval', seconds=20)
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
