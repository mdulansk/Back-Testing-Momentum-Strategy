'''
Details: from MACD Indicator Explained Youtube video by Financial Wisdom


10-15% stop loss is ideal according to Financial Wisdom video
'''

import datetime
import pandas_ta as ta
import pandas as pd
from backtesting import Backtest
from backtesting import Strategy
from backtesting.lib import crossover
from backtesting.test import GOOG


class RsiOscillator(Strategy):
    upper_bound = 70
    lower_bound = 30
    rsi_window = 14
    # Do as much initial computation as possible
    def init(self) :
        self.rsi = self.I(ta.rsi, pd.Series(self.data.Close) , self.rsi_window)
        self.MACD = self.I(ta.macd, pd.Series(self.data.Close), fast=12, slow=26, signal=9, talib=None, offset=None)
        
    # Step through bars one by one
    # Note that multiple buys are a thing here
    def next(self):
        if crossover(self.rsi, self.upper_bound):
            print('close position')
            self.position.close()
        elif crossover(self.lower_bound, self.rsi):
            self.buy()
            print('buy')
bt = Backtest (GOOG, RsiOscillator, cash = 10_000, commission = .002)
stats = bt.run()
print(stats)
bt.plot()
