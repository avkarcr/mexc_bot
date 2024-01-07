import datetime as dt
import asyncio
import inspect

from loguru import logger
from modules.mexc.mexc_toolkit import (
    TOOL,
    mexc_account,
    mexc_trade,
    mexc_capital,
)
from utils.decorators import async_retry
from utils.exceptions import MexcAPIException


class MexcAccount(TOOL):
    def __init__(self, mexc_host, api_key, secret_key, tokens_on_hold):
        self.mexc_account = mexc_account(mexc_host, api_key, secret_key)
        self.mexc_trade = mexc_trade(mexc_host, api_key, secret_key)
        self.mexc_capital = mexc_capital(mexc_host, api_key, secret_key)
        self.current_balance = []
        self.tokens_to_sell = []
        self.tokens_on_hold = tokens_on_hold

    def set_megabot(self, megabot_instance):
        self.megabot = megabot_instance

    @async_retry(10, 1)
    async def update_balance(self):
        f_name = inspect.currentframe().f_code.co_name
        logger.debug(f'START {f_name}()')
        account = ''
        while True:
            try:
                account = await self.mexc_account.get_account_info()
                self.current_balance = account['balances']
                all_tokens = [item['asset'] for item in self.current_balance]
                self.tokens_to_sell = [_ for _ in all_tokens if _ not in self.tokens_on_hold]
                break
            except KeyError:
                logger.warning(f'Error in key \'balances\'. Account_info: {account}')
                raise MexcAPIException
        logger.debug(f'FINISH {f_name}()')
        return

    async def get_balance(self):
        return self.current_balance

    async def convert_to_mx(self, token):
        try:
            params = {'asset': token}
            self.mexc_capital.post_smallAssets_convert(params=params)  # todo отметить в БД, как SOLD
            return True
        except KeyError:
            logger.warning(f'Error in key \'balances\'. Token: {token}')
        except Exception as e:
            logger.warning(f'Error : {e}')
        return False

    # async def schedule_mexc_task(self, running_time: dt, coro):
    #     while True:
    #         current_time = dt.datetime.now()
    #         if current_time >= running_time:
    #             await coro()
    #             return
    #         await asyncio.sleep(60)
