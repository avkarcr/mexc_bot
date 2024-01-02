import time
import datetime
from loguru import logger
from modules.mexc.mexc_toolkit import TOOL, mexc_account, mexc_trade


class MexcAccount(TOOL):
    def __init__(self, mexc_host, api_key, secret_key, tokens_on_hold):
        self.mexc_account = mexc_account(mexc_host, api_key, secret_key)
        self.mexc_trade = mexc_trade(mexc_host, api_key, secret_key)
        self.current_balance = []
        self.tokens_to_sell = []
        self.tokens_on_hold = tokens_on_hold

    async def initial_balance(self):
        count = 0
        while True:
            try:
                count += 1
                account = self.mexc_account.get_account_info()  # TODO сделать await
                self.current_balance = account['balances']
                all_tokens = [item['asset'] for item in self.current_balance]
                self.tokens_to_sell = [_ for _ in all_tokens if _ not in self.tokens_on_hold]
                break
            except KeyError as exception:
                logger.warning(f'There are issues gettings balances: {exception}')
                # print(f'KeyError: {self.mexc_account.get_account_info()}')
            finally:
                time.sleep(1)
                if count % 10 == 0:
                    msg = 'Trying 10 times getting account info. No result!'
                    logger.error(msg)
                    exit()
        with open('bd.txt', 'w') as file:
            record_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for asset in self.current_balance:
                token = asset['asset']
                trade_start_time = 'not specified'
                file.write(f'{record_time}, {token}, {trade_start_time}\n')
