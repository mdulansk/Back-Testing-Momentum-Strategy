'''
Details: Moving Average strategies Youtube video by Financial Wisdom
Buy when price above 200day MA, sell when below
Timeframe: 
Trade Interval: month-end

Note: 10-15% stop loss is ideal according to Financial Wisdom video
'''

import datetime
import pandas_ta as ta
import pandas as pd
from backtesting import Backtest
from backtesting import Strategy
from backtesting.lib import crossover, plot_heatmaps, resample_apply, barssince
from backtesting.test import GOOG


class RsiOscillator(Strategy):
    upper_bound = 70
    lower_bound = 30
    rsi_window = 14
    # Do as much initial computation as possible
    def init(self) :
        #print(f"self.data: {self.data.index}")
        #self.rsi = self.I(ta.rsi, pd.Series(self.data.Close) , self.rsi_window)
        self.daily_rsi = self.I(ta.rsi, pd.Series(self.data.Close), self.rsi_window)
        # This magical function does all the resampling
        self.weekly_rsi = resample_apply('W-FRI', ta.rsi, self.data.Close.s, self.rsi_window)
        #Note the use of the .s accessor to access the Close data as a Pandas series
        
        self.MACD = self.I(ta.macd, pd.Series(self.data.Close), fast=12, slow=26, signal=9, talib=None, offset=None)
        self.MA200 = self.I(ta.sma, pd.Series(self.data.Close), 200)
        
    # Step through bars one by one
    # Note that multiple buys are a thing here
    def next(self):
        print(f"self.data: {self.data}")
        #Determine if this is the last trading day of the month,
        # then check if yesterday's close price was above or below the 200 day MA
        price = self.data.Close[-1] # Yesterday's closing price
        if (price < self.MA200 and
                barssince(self.daily_rsi < self.upper_bound)==3): #If this happend 3 bars ago
            self.position.close()
        elif price > self.MA200:
            self.buy(sl=.85 * price)
            #print('buy')
bt = Backtest (GOOG, RsiOscillator, cash = 10_000, commission = .002)
stats = bt.run()
print(stats)
bt.plot()
