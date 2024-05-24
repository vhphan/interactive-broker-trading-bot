import datetime
import random
from enum import Enum
from shutil import get_terminal_size

import numpy as np
import pandas as pd
from ibapi.common import BarData
from ibapi.contract import Contract
from loguru import logger
from retry import retry

from bots.my_ib.client import IBClient
from bots.my_ib.config import Config
from bots.my_ib.contracts import MyContracts
from bots.my_ib.strategy import SimpleStrategy


class Platform(Enum):
    TWS = 'tws'
    IB = 'ib'


# create a request id generator
def gen_req_id():
    req_id = 1
    while True:
        yield req_id
        req_id += 1


class Trader:

    def __init__(self, is_paper: bool, tws_or_ib: Platform, contract: Contract, warmup_period: int = 30):
        self.warmup_period = warmup_period
        self.strategy = None
        self.paper = is_paper
        self.tws_or_ib = tws_or_ib
        self.client_id = random.randint(0, 1000)
        self.client = IBClient(self.port,
                               self.client_id,
                               real_time_bar_func=self.real_time_bar_event,
                               historical_data_func=self.historical_data_event,
                               historical_data_end_func=self.historical_data_end_event,
                               historical_data_update_func=self.historical_data_update_event
                               )

        self.contract = contract
        # self.req_id = gen_req_id()
        self.requests = {

        }
        self.hist_df: pd.DataFrame = (
            pd.DataFrame(
                columns=['symbol', 'date', 'open', 'high', 'low', 'close', 'volume', 'wap', 'count']
            )
            .astype({'open': np.float64, 'high': np.float64,
                     'low': np.float64, 'close': np.float64, 'volume': np.int64,
                     'wap': np.float64, 'count': np.float64,
                     'symbol': str})
            .assign(**{'date': lambda x: pd.to_datetime(x['date'])})
            .set_index(['symbol', 'date'])
        )

        self.client.run_in_thread()

    def get_realtime_data(self):
        logger.info('Getting realtime data')
        print('isConnected', self.client.isConnected())
        if not self.client.isConnected():
            raise Exception('Connection to IBKR is not established. Please check your connection.')
        req_id = next(gen_req_id())
        self.client.reqRealTimeBars(req_id, self.contract, 5, 'trades',
                                    True,  # True for stock data, False for forex/crypto data
                                    [])

    @retry(tries=3, delay=5, backoff=2, logger=logger)
    def get_historical_data(self):

        print('Getting historical data')
        print('isConnected', self.client.isConnected())

        logger.info('Getting historical data')

        if not self.client.isConnected():
            raise Exception('Connection to IBKR is not established. Please check your connection.')

        #  client.reqHistoricalData(
        #         2, contract, '', '30 D', '5 mins', what_to_show, True, 2, False, []
        #     )
        req_id = next(gen_req_id())
        req_params = {
            'reqId': req_id,
            'contract': self.contract,
            'endDateTime': '',
            'durationStr': '1 D',
            'barSizeSetting': '5 mins',
            'whatToShow': 'TRADES',
            'useRTH': 1,
            'formatDate': 2,
            'keepUpToDate': True,
            'chartOptions': []
        }
        self.client.reqHistoricalData(**req_params)
        self.requests[req_id] = req_params

    @staticmethod
    def convert_one_bar_to_dict(bar: BarData):
        return {
            'date': datetime.datetime.utcfromtimestamp(int(bar.date)).strftime('%Y-%m-%d %H:%M:%S'),
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': int(bar.volume),
            'wap': bar.wap,
            'count': bar.barCount,
        }

    def convert_bars_to_df(self, bars):
        formatted_bars = [
            self.convert_one_bar_to_dict(bar)
            for bar in bars
        ]
        return pd.DataFrame(formatted_bars)

    def historical_data_end_event(self, reqId, list_of_bars):
        logger.info('Trader Historical data end')
        symbol = self.requests[reqId]['contract'].symbol
        df = (self.convert_bars_to_df(list_of_bars)
              .assign(symbol=symbol)
              .set_index(['symbol', 'date'])
              )

        self.hist_df = pd.concat([self.hist_df, df])
        logger.info(self.hist_df.head())
        logger.info(self.hist_df.tail())
        logger.info(f'shape {self.hist_df.shape}')

    def historical_data_update_event(self, reqId, bar: BarData):
        logger.info('Trader Historical data update')
        new_bar = self.convert_one_bar_to_dict(bar)
        logger.debug(new_bar)
        symbol = self.requests[reqId]['contract'].symbol

        # Create a new DataFrame from the new bar
        new_df = (
            pd.DataFrame([new_bar])
            .assign(symbol=symbol)
            .set_index(['symbol', 'date'])
        )

        # Update the existing rows in the DataFrame
        self.hist_df.update(new_df)

        # Append any new rows
        # self.hist_df = self.hist_df.append(new_df[~new_df.index.isin(self.hist_df.index)])
        self.hist_df = pd.concat([self.hist_df, new_df[~new_df.index.isin(self.hist_df.index)]])
        logger.info(self.hist_df.tail())
        logger.info(f'shape {self.hist_df.shape}')
        # latest bar may not be complete, hence the last is not included in the strategy
        if len(self.hist_df) - 1 > self.warmup_period:
            self.strategy.run()

    def historical_data_event(self, reqId, bar: BarData):
        logger.info('Trader Historical data event')
        logger.debug(self.convert_one_bar_to_dict(bar))

    def stop_realtime_data(self):
        self.client.cancelRealTimeBars(1)

    def stop_historical_data(self):
        self.client.cancelHistoricalData(1)

    def real_time_bar_event(self, reqId, time, open_, high, low, close, volume, wap, count):
        time_utc = datetime.datetime.utcfromtimestamp(time)
        time_str = time_utc.strftime('%Y-%m-%d %H:%M:%S')
        # self.df.loc[len(self.df)] = [time_str, open_, high, low, close, volume, wap, count]
        # with pd.option_context('display.max_rows', None,
        #                        'display.max_columns', None,
        #                        'display.width', get_terminal_size()[0] + 100
        #                        ):
        #     print(self.df)

    @property
    def port(self):
        port_map = {
            (True, Platform.TWS): Config.TWS_PAPER_PORT,
            (True, Platform.IB): Config.IBGW_PAPER_PORT,
            (False, Platform.TWS): Config.TWS_LIVE_PORT,
            (False, Platform.IB): Config.IBGW_LIVE_PORT
        }
        return port_map[(self.paper, self.tws_or_ib)]

    def set_strategy(self, strategy):
        self.strategy = strategy

    def buy(self):
        logger.info('Buying')
        # TODO: Implement buy

    def sell(self):
        logger.info('Selling')
        # TODO: Implement sell

    def do_nothing(self):
        logger.info('Do nothing')




if __name__ == '__main__':

    # contract.symbol = 'EUR'
    # contract.secType = 'CASH'
    # contract.exchange = 'IDEALPRO'
    # contract.currency = 'USD'
    # contract.conId = 12087792
    # contract.localSymbol = 'EUR.USD'

    # contract.symbol = 'SPY'
    # contract.secType = 'STK'
    # contract.exchange = 'SMART'
    # contract.currency = 'USD'
    # contract.primaryExchange = 'ARCA'

    # contract.conId = 756733

    # symbol = "AAPL"
    # secType = "STK"
    # exchange = "SMART"
    # currency = "USD"

    # contract.symbol = "AAPL"
    # contract.secType = "STK"
    # contract.exchange = "SMART"
    # contract.currency = "USD"

    contract = MyContracts.EthUsdCrypto()

    with pd.option_context('display.max_rows', None,
                           'display.max_columns', None,
                           'display.width', get_terminal_size()[0] + 100
                           ):
        # trader.get_realtime_data()
        trader = Trader(is_paper=True, tws_or_ib=Platform.TWS, contract=contract)
        simple_strategy = SimpleStrategy(trader)
        trader.set_strategy(simple_strategy)
        try:
            trader.get_historical_data()
            while True:
                pass
        except Exception as e:
            logger.error(e)
        finally:
            trader.stop_realtime_data()
            trader.stop_historical_data()
            trader.client.disconnect()
            logger.info('Trader disconnected!!')
