from queue import Queue
from src.events import OrderEvent, FillEvent, SignalEvent
from src.data import HistoricYFinanceDataHandler
from src.strategy import Strategy
import pandas as pd
import numpy as np
import datetime as dt

from typing import Tuple, List

import warnings
warnings.filterwarnings('ignore')


class Backtester:

    def __init__(self, symbols: List, from_to=None):
        self.from_to = from_to
        self.symbol_list = symbols

        # Reset the initial parameters
        self.open_trades = {}
        self.closed_trades = []
        self.event = None

        self.amount = None
        self.running_amount = None
        self.id = 1

        self.trades = pd.DataFrame()

    def run_backtest(self):
        """
        This method runs the backtesting loop, it is designed to work with/without
        multiprocessing.
        """       

        # create the queue object
        self.event = Queue()

        self.amount = 100000
        self.running_amount = self.amount

        # import the historical data and clean it
        self.data = HistoricYFinanceDataHandler(self.event, self.symbol_list, self.from_to)

        # create the strategy instance
        strategy = Strategy(self.event, self.data)

        # run the loop
        while True:

            # check if there is more self.data
            if self.data.continue_backtest:
                self.data.update_bars()
                # self.log(self.data.get_latest_bars())
            else:
                # exit the backtest
                break

            while True:
                if self.event.qsize() != 0:
                    the_event = self.event.get()
                else:
                    # we should exit the loop to update the self.data.df
                    break

                if the_event is not None:
                    if the_event.type == 'MARKET':
                        # check market data with strategy
                        strategy.compute_signal(the_event)
                    # check if signal to trade
                    if the_event.type == 'SIGNAL':
                        self.update_from_signal(the_event)
                    # check if order to fill
                    if the_event.type == 'ORDER':
                        self.update_from_order(the_event)
                    if the_event.type == 'FILL':
                        self.update_from_fill(the_event)

        # get and clean the trades
        self.trades = pd.DataFrame(self.closed_trades)

    def update_from_signal(self, event: SignalEvent):
        if event.type == 'SIGNAL':
            self._generate_order(event)
    
    def _generate_order(self, event: SignalEvent):
        order = OrderEvent(event.information)
        self.event.put(order)

    def update_from_order(self, event: OrderEvent):
        fill_event = FillEvent(event.information)
        self.event.put(fill_event)

    def update_from_fill(self, event: FillEvent):

        information = event.information
        sym = information['symbol']

        if information['type'] in ['Long', 'Short']:

            # we don't have any position
            self.open_trades['UniqueID'] = self.id
            self.id += 1
            self.open_trades['Entry Date'] = information['datetime']
            self.open_trades['Entry Price'] = information['price']
            self.open_trades['Quantity'] = information['quantity']
            self.open_trades['Amount'] = information['amount']
            self.open_trades['Type'] = information['type']
            self.open_trades['Symbol'] = information['symbol']

        elif 'Exit' in information['type']:

            # we only have one open position
            self.open_trades['Exit Date'] = information['datetime']
            self.open_trades['Exit Price'] = information['price']
            self.open_trades['Exit Type'] = information['type']

            # PnL computation
            direction = 1 if self.open_trades['Type'] == 'Long' else -1
            self.open_trades['Profit/Loss in Dollars'] = \
                (self.open_trades['Exit Price'] - self.open_trades['Entry Price'])
            self.open_trades['Profit/Loss in Dollars'] = \
                self.open_trades['Profit/Loss in Dollars'] * self.open_trades['Quantity']
            self.open_trades['Profit/Loss in Dollars'] *= direction

            # % PnL computation
            self.open_trades['Profit/Loss in %'] = \
                (self.open_trades['Profit/Loss in Dollars']/self.open_trades['Amount'])*100

            # update the running amount
            self.running_amount += self.open_trades['Profit/Loss in Dollars']

            # storing and cleaning
            self.closed_trades.append(self.open_trades)
            self.open_trades = {}
