from events import MarketEvent, SignalEvent, FillEvent
from data import HistoricYFinanceDataHandler
from queue import Queue

import numpy as np
import pandas as pd
import collections
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
            bars = self.data.get_latest_bars()

            if len(self.CurrentPosition) == 0:
                pass
            else:
                pass
