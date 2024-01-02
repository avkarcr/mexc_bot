from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError, TelegramNetworkError
from loguru import logger
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

    async def start(self) -> None:
        try:
            await self.bot.send_message(self.admin_id, text='Bot is working...')
            await self.dp.start_polling(self.bot)
        except TelegramNetworkError:
            logger.critical('No Internet connection. Quiting.')
        except TelegramAPIError:
            logger.critical('Telegram API connection error. Quiting.')
        except Exception:
            logger.critical(f'Error: {Exception}')
        finally:
            await self.bot.send_message(self.admin_id, text='Bot has been stopped.')
            await self.bot.session.close()
