import asyncio
import time
import datetime as dt
from loguru import logger
from modules.mexc.mexc_toolkit import TOOL, mexc_account, mexc_trade
from utils.decorators import async_retry


class MexcAccount(TOOL):
    def __init__(self, mexc_host, api_key, secret_key, tokens_on_hold):
        self.mexc_account = mexc_account(mexc_host, api_key, secret_key)
        self.mexc_trade = mexc_trade(mexc_host, api_key, secret_key)
        self.current_balance = []
        self.tokens_to_sell = []
        self.tokens_on_hold = tokens_on_hold

    @async_retry(10, 1)
    async def update_balance(self):
        while True:
            try:
                account = await self.mexc_account.get_account_info()
                self.current_balance = account['balances']
                all_tokens = [item['asset'] for item in self.current_balance]
                self.tokens_to_sell = [_ for _ in all_tokens if _ not in self.tokens_on_hold]
                return
            except KeyError:
                logger.warning(f'Error in key \'balances\'. Account_info: {account}')

    async def get_balance(self):
        return self.current_balance
