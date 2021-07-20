from queue import Queue
from typing import Tuple, List

import pandas as pd
import datetime as dt
import yfinance as yf
from src.events import MarketEvent


class HistoricYFinanceDataHandler:

    def __init__(self, events: Queue, symbol: List, from_to: Tuple):

        self.symbol = symbol[0]
        self.from_date = from_to[0]
        self.to_date = from_to[1]
        self.events = events
        self.latest_symbol_data = []
        self.continue_backtest = True

        self._get_data_from_yfinance()

    def _get_data_from_yfinance(self):

        # iterate over the ranges and append into df
        df = yf.download(
            self.symbol,
            start=self.from_date,
            end=self.to_date,
        )

        df.index = df.index.tz_localize(None)
        self.data_df = df.copy()
        self.data = df.iterrows()

    def _get_new_bar(self):
        """
        Returns the latest bar from the data feed as a tuple of
        (symbol, datetime, open, low, high, close, volume).
        """
        for mkt_data in self.data:
            yield tuple([mkt_data[0],
                        mkt_data[1][0],  # open
                        mkt_data[1][1],  # high
                        mkt_data[1][2],  # low
                        mkt_data[1][3],  # close
                        mkt_data[1][5]]  # volume - skip the adj close
                        )

    def get_latest_bars(self, N=1):
        """
        Returns the last N bars2 from the latest_symbol list,
        or N-k if less available.
        """
        try:
            # This is updated every time self.update_bars is executed
            bars_list = self.latest_symbol_data
        except KeyError:
            print("That symbol is not available in the historical data set.")
        else:
            return bars_list[-N:]

    def update_bars(self):
        """
        Pushes the latest bar to the latest_symbol_data structure
        for all symbols in the symbol list.
        """

        try:
            bar = self._get_new_bar().__next__()  # This works because we have an iterator
        except StopIteration:
            self.continue_backtest = False
        else:
            if bar is not None:
                # update this for the method self.get_latest_bar
                self.latest_symbol_data.append(bar)
        self.events.put(MarketEvent())  # put a market event


