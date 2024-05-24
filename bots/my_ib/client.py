import queue
import threading
import time
from decimal import Decimal
from typing import Callable

from ibapi.client import EClient
from ibapi.common import TickerId, BarData
from ibapi.wrapper import EWrapper
from loguru import logger
from retry import retry
from setproctitle import setproctitle

from bots.my_ib.config import Config, ip_address


class IBClient(EClient, EWrapper):
    def __init__(self, port: int, client_id: int,
                 real_time_bar_func: Callable = None,
                 historical_data_func: Callable = None,
                 historical_data_end_func: Callable = None,
                 historical_data_update_func=None):
        EClient.__init__(self, self)
        self.port = port
        self.client_id = client_id
        self.real_time_bar_func = real_time_bar_func
        self.historical_data_func = historical_data_func
        self.historical_data_update_func = historical_data_update_func
        self.historical_data_end_func = historical_data_end_func
        self.data_q = queue.Queue()  # Holds the historical data in a queue
        self.bars = []  # Update the historical data in a list
        self.portfolio_updates = []  # Holds the portfolio updates
        self.account_summary = {}  # Holds the account summary
        self.next_valid_order_id = None  # Holds the next valid order ID
        self.api_thread = None

        self.run_in_thread()

    def historicalData(self, req_id, bar):
        logger.debug("HistoricalData. req_id:", req_id)
        self.data_q.put(
            [req_id, bar]
        )
        if self.historical_data_func:
            self.historical_data_func(req_id, bar)

    def historicalDataEnd(self, req_id: int, start: str, end: str):
        logger.debug(f'HistoricalDataEnd. req_id:{req_id}, Start:{start}, End:{end}')
        while not self.data_q.empty():  # Get the historical data from the queue
            self.bars.append(self.data_q.get_nowait()[1])
            logger.info("Appending bars")

        if self.historical_data_end_func:
            self.historical_data_end_func(req_id, self.bars)

    def historicalDataUpdate(self, req_id, bar):
        logger.debug(f'HistoricalDataUpdate. req_id:{req_id}')

        # self.data_q.put(
        #     [req_id, bar]
        # )
        # self.data_q, replaced = replace_in_queue(self.data_q, req_id, bar)

        if self.historical_data_update_func:
            self.historical_data_update_func(req_id, bar)

    def updatePortfolio(self, contract, position, marketPrice, marketValue, averageCost, unrealizedPNL, realizedPNL,
                        accountName):
        super().updatePortfolio(contract, position, marketPrice, marketValue, averageCost, unrealizedPNL, realizedPNL,
                                accountName)
        logger.info(
            f"Contract: {contract.symbol}, Position: {position}, Market Price: {marketPrice}, Market Value: {marketValue}, Average Cost: {averageCost}, Unrealized PNL: {unrealizedPNL}, Realized PNL: {realizedPNL}, Account Name: {accountName}")

        self.portfolio_updates.append(
            [contract.symbol, position, marketPrice, marketValue, averageCost, unrealizedPNL, realizedPNL, accountName])

    def accountSummary(
            self, req_id: int, account: str, tag: str, value: str, currency: str
    ):
        super().accountSummary(req_id, account, tag, value, currency)
        print(f"Account: {account}, Tag: {tag}, Value: {value}, Currency: {currency}")
        self.account_summary[tag] = value

    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.next_valid_order_id = orderId
        print('The next valid order ID is: ', self.next_valid_order_id)

    def nextOrderId(self):
        return self.next_valid_order_id

    def realtimeBar(
            self,
            req_id: TickerId,
            time: int,
            open_: float,
            high: float,
            low: float,
            close: float,
            volume: Decimal,
            wap: Decimal,
            count: int,
    ):
        print('Received real-time bar data', time, open_)

        self.real_time_bar_func(req_id, time, open_, high, low, close, volume, wap, count)

    def wait_for_connection(self):
        """
        Waits for the connection to be established.
        """
        logger.debug('wait_for_connection')
        setproctitle("ibkr-loop")

        slept = 0
        while not self.isConnected():
            if slept > 10:
                raise Exception('Connection to IBKR is not established. Please check your connection.')
            logger.info('Sleeping for 1 second')
            time.sleep(1)
            slept += 1
            logger.info(f'{slept} seconds slept')

    @retry(tries=3, delay=2, backoff=2, logger=logger)
    def make_connection(self):
        """
        Establishes a connection to IBKR.
        """
        logger.debug('make_connection')
        setproctitle("ibkr-loop")

        if self.isConnected():
            logger.info('Already connected to IBKR')
            return

        self.connect(ip_address, self.port, self.client_id)
        self.wait_for_connection()

        logger.info('Connect attempted to IBKR')
        self.run()

    def run_in_thread(self):
        print('Connecting to IBKR. Running in a separate thread.')
        self.api_thread = threading.Thread(target=self.make_connection)
        self.api_thread.start()
        return self.api_thread

    def stop_thread(self):
        self.disconnect()
        self.api_thread.join()
        print('Disconnected from IBKR')

    def error(self, req_id: TickerId, errorCode: int, errorString: str, advancedOrderRejectJson=""):
        print("Error. Id: ", req_id, " Code: ", errorCode, " Msg: ", errorString)


def replace_in_queue(q: queue.Queue, req_id: int, bar: BarData) -> (queue.Queue, bool):
    replaced = False
    temp_list = []

    while not q.empty():
        current_item = q.get()
        if not replaced and current_item[0] == req_id and current_item[1].date == bar.date:
            temp_list.append([req_id, bar])
            replaced = True
        else:
            temp_list.append(current_item)

    if not replaced:
        temp_list.append([req_id, bar])

    for item in temp_list:
        q.put(item)

    return q, replaced


if __name__ == '__main__':
    app = IBClient(Config.IBGW_PAPER_PORT, 234)
