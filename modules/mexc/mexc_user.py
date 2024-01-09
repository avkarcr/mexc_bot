import datetime as dt
import asyncio
import inspect

from loguru import logger
from modules.mexc.mexc_toolkit import (
    TOOL,
    mexc_account,
    mexc_trade,
    mexc_capital,
    mexc_market,
)
from utils.decorators import async_retry
from utils.exceptions import MexcAPIException


class MexcAccount(TOOL):
    def __init__(self, mexc_host, api_key, secret_key, tokens_on_hold):
        self.mexc_account = mexc_account(mexc_host, api_key, secret_key)
        self.mexc_trade = mexc_trade(mexc_host, api_key, secret_key)
        self.mexc_capital = mexc_capital(mexc_host, api_key, secret_key)
        self.mexc_market = mexc_market(mexc_host)
        self.current_balance = []
        self.tokens_to_sell = []
        self.tokens_on_hold = tokens_on_hold

    def set_megabot(self, megabot_instance):
        self.megabot = megabot_instance

    @async_retry(10, 1)
    async def update_balance(self):
        f_name = inspect.currentframe().f_code.co_name
        logger.debug(f'START {f_name}()')
        account = await self.mexc_account.get_account_info()
        self.current_balance = account['balances']
        all_tokens = [item['asset'] for item in self.current_balance]
        self.tokens_to_sell = [_ for _ in all_tokens if _ not in self.tokens_on_hold]
        return

    async def get_balance(self):
        return self.current_balance

    async def convert_to_mx(self, token):
        try:
            params = {'asset': token}
            self.mexc_capital.post_smallAssets_convert(params=params)  # todo отметить в БД, как SOLD
            return True  # todo вернуть детали транзакции
        except:
            raise MexcAPIException

    async def is_symbol_api_available(self, symbol):
        available_symbols = await self.mexc_market.get_defaultSymbols()
        # return symbol in available_symbols['data']
        result = symbol in available_symbols['data']
        if result:
            await self.megabot.bot.send_message(self.megabot.admin_id, text=f'Символ {symbol} стал доступен!')
            return True
        return False

    async def get_tokens_to_convert_mx(self):
        tokens_to_convert = await self.mexc_capital.get_smallAssets_list()
        if tokens_to_convert:
            await self.megabot.bot.send_message(self.megabot.admin_id, text=f'Доступно для конвертации: {tokens_to_convert}')
            return True
        return False
