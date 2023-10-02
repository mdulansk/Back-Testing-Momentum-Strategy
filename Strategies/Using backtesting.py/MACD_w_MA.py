'''
Description: From Financial Wisdom Youtube channel
"BITCOIN TRADING - Arguably The Best Bitcoin Trading strategy"
Indicators:
    MACD: 26 period EMA, 12 period EMA, 9 period EMA (signal)
    Use daily MACD indicator using settings above.
Rules:
    BUY: price above 200 ma & macd > signal
    SELL stop:
        If DAILY MACD closes below signal line:
            Set stop loss at LOW of that day's closing candle
    RENTRY: after DAILY MACD line crosses above signal line AND price above 200 ma


'''



# Import libraries
import os
from os.path import exists
import datetime
import time
import pandas as pd
import pandas_ta as ta
from backtesting import Backtest
from backtesting import Strategy
from backtesting.lib import crossover
from backtesting.lib import SignalStrategy, TrailingStrategy
from backtesting.lib import crossover, plot_heatmaps, resample_apply, barssince
#from backtesting.test import GOOG

# Set variables and load data from csv

data_folder = '/home/lantro/Documents/Algo Trading/LEAN/data/yahoo/'
ticker = 'spy' #'spy' 'eurusd=x' 'BTC-USD' 'tqqq'
df = pd.read_csv(f"{data_folder}{ticker}.csv", index_col=[0], parse_dates=True, skipinitialspace=True)
df = df.rename(columns={"open": "Open", "close": "Close", "low": "Low", "high": "High", "volume": "Volume"})
start_date = '2008-01-01' #Start date for data
end_date = '2022-06-01'
df = df.loc[start_date:end_date].copy()

'''
The next function is a utility to load the necessary OHLC price files which you would like to use.
Backtests can be done for multiple time periods and assets, to match the design of your strategy. 
One thing to point out here is that the backtesting.py framework needs the column names in a specific format:
 (Open, Close, High, Low, Volume) so you can rename your columns using this statement:
'''

class DualMACDStrategy(Strategy):
    buy_atr_level = 8
    sell_atr_level = 7
    stop_pct = 20
    current_stop = -1
    # Do as much initial computation as possible
    def init(self) :
        self.MA200 = self.I(ta.sma, pd.Series(self.data.Close), 200)
        self.daily_MACD = self.I(ta.macd, pd.Series(self.data.Close), fast=12, slow=26, signal=9, talib=None, offset=None)
        #Note: The MACD indicator call returns an ndarray with 3 columns: fast, hist, and signal, The first index indicates the array,
        # and the second index indicates the row, where [-1] is latest value.
        # This magical function does all the resampling. #Note the use of the .s accessor to access the Close data as a Pandas series.
        #self.weekly_MACD = resample_apply('W-FRI', ta.macd, self.data.Close.s, fast=12, slow=26, signal=9, talib=None, offset=None)
        
        
    # Step through bars one by one
    # Note that multiple buys are a thing here
    def next(self):
        current_bar_idx = len(self.data) - 1
        current_date = self.data.index[-1]
        close_price = self.data.Close[-1] # Yesterday's closing price
        #print((self.daily_MACD[0][-1], self.daily_MACD[1][-1], self.daily_MACD[2][-1]))
        daily_MACDf = self.daily_MACD[0][-1]
        daily_MACDh = self.daily_MACD[1][-1]
        daily_MACDs = self.daily_MACD[2][-1]
        #print(f'{current_date}  Daily MACD,HIST,SIGNAL:\t{daily_MACDf},\t{daily_MACDh},\t{daily_MACDs}')
        if close_price > self.MA200: # Trading "window" open
            if (daily_MACDf < daily_MACDs):
                if close_price < self.current_stop and self.position:
                    print(f'{current_date}  Daily MACD,HIST,SIGNAL:\t{daily_MACDf},\t{daily_MACDh},\t{daily_MACDs}')
                    print(f'{current_date} D CLOSE POS at ${round(close_price,2)}')
                    self.position.close()
                    
                else: #Set sell stop
                    self.current_stop = max(self.current_stop, close_price*(1-self.stop_pct*.01)) #Don't keep moving DOWN!
                    #print(f'{current_date} Price ${round(close_price,2)} Stop ${round(self.current_stop,2)}')
                    
            elif daily_MACDf > daily_MACDs:
                if not self.position:
                    print(f'{current_date}  Daily MACD,HIST,SIGNAL:\t{daily_MACDf},\t{daily_MACDh},\t{daily_MACDs}')
                    print(f'{current_date} OPEN  POS at ${round(close_price,2)}')
                    #self.buy(sl=0.85*close_price)
                    self.buy()
                    self.current_stop = close_price*(1-self.stop_pct*.01)
                    print(f'Initial stop:  {self.current_stop}')
        else: # Trend not positive
            if close_price < self.current_stop and self.position:
                print(f'{current_date}  Daily MACD,HIST,SIGNAL:\t{daily_MACDf},\t{daily_MACDh},\t{daily_MACDs}')
                print(f'{current_date} W CLOSE POS at ${round(close_price,2)}')
                self.position.close()
            else: #Set sell stop = closing price
                self.current_stop = max(self.current_stop, close_price*(1-self.stop_pct*.01)) #Don't keep moving DOWN!
                #print(f'{current_date} Price ${round(close_price,2)} Stop ${round(self.current_stop,2)}')
#bt = Backtest(GOOG, DualMACDStrategy, cash=10000, commission=.00075, trade_on_close=True, exclusive_orders=True, hedging=False)
bt = Backtest(df, DualMACDStrategy, cash=10000, commission=.00075, trade_on_close=True, exclusive_orders=True, hedging=False)
#stats = bt.run()

stats = bt.optimize(
stop_pct = range( 5 , 30 , 1 ),
maximize = 'Return [%]',
max_tries=100)

print(stats)
print(f"\nB&H Return %:  {round(stats['Buy & Hold Return [%]'],2)}")
print(f"Return %  {round(stats['Return [%]'],2)}")
print(f"Sharpe Ratio:  {round(stats['Sharpe Ratio'],2)}")

strategy = stats [ "_strategy" ]
print(f'\nIdeal stop_pct: {strategy.stop_pct}') # Idea parameter from optimization

bt.plot()