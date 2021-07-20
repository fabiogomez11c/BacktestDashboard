from src.events import MarketEvent, SignalEvent, FillEvent
from src.data import HistoricYFinanceDataHandler
from queue import Queue

import numpy as np
import pandas as pd
import datetime as dt
from typing import Tuple


class Strategy:

    def __init__(self, events: Queue, data: HistoricYFinanceDataHandler):

        # store the parameters
        self.events = events
        self.data = data

        self.quantity = 100

        # initial values in the strategy
        self.CurrentPosition = []

    def compute_signal(self, event: MarketEvent):

        if event.type == 'MARKET':  # there is a new bar
            # get the bars needed
            bars = self.data.get_latest_bars(10)
            if len(bars) < 10:
                return

            close = [x[-2] for x in bars]
            avg = np.mean(close)

            if len(self.CurrentPosition) == 0:
                # check for long signal
                if close[-1] > avg:

                    # create a long order
                    information = {
                        'datetime': bars[-1][0],
                        'price': bars[-1][-2],
                        'quantity': self.quantity,
                        'amount': self.quantity * bars[-1][-2],
                        'type': 'Long',
                        'symbol': 'symbol'
                    }

                    # send the order
                    signal = SignalEvent(information)
                    self.events.put(signal)

                    # update current position
                    self.CurrentPosition = [information]
            else:
                # check for sell signal
                if close[-1] < avg:

                    # create a sell order
                    information = {
                        'datetime': bars[-1][0],
                        'price': bars[-1][-2],
                        'type': 'Exit',
                        'symbol': 'symbol'
                    }

                    # send the order
                    signal = SignalEvent(information)
                    self.events.put(signal)

                    # update the current position
                    self.CurrentPosition = []
