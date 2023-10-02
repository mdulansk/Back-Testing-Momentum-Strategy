'''
Rules:
Trade Frequency: Monthly (end of month)
	BUY if SP500 above 200 day EMA at end of month and ATR is below threshold
	SELL when SP500 is below 200 day EMA at end of month unless ATR above threshold,
    then sell when price goes below 20 day

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
start_date = '2000-01-01' #Start date for data
end_date = '2022-06-01'
df = df.loc[start_date:end_date]
stoploss = .85


'''
The next function is a utility to load the necessary OHLC price files which you would like to use.
Backtests can be done for multiple time periods and assets, to match the design of your strategy. 
One thing to point out here is that the backtesting.py framework needs the column names in a specific format:
 (Open, Close, High, Low, Volume) so you can rename your columns using this statement:
'''

class PaulTudorJonesStrategy(Strategy):
    buy_atr_level = 8
    sell_atr_level = 7
    # Do as much initial computation as possible
    def init(self) :
        self.MA200 = self.I(ta.sma, pd.Series(self.data.Close), 200)
        self.MA50 = self.I(ta.sma, pd.Series(self.data.Close), 50)
        self.MA20 = self.I(ta.sma, pd.Series(self.data.Close), 50)
        self.ATR = self.I(ta.atr, high=pd.Series(self.data.High), low=pd.Series(self.data.Low), close=pd.Series(self.data.Close), length=30)
        
    # Step through bars one by one
    # Note that multiple buys are a thing here
    def next(self):
        current_bar_idx = len(self.data) - 1
        current_date = self.data.index[-1]
        close_price = self.data.Close[-1] # Yesterday's closing price
        # Determine if this is the end of the month before trading
        if current_date == current_date + pd.offsets.BMonthEnd(0):
            # then check if yesterday's close price was above or below the 200 day MA
            if self.ATR < self.buy_atr_level:
                if (close_price < self.MA200):
                    #print(f'{current_date} CLOSE POS at ${round(close_price,2)}')
                    self.position.close()
                elif close_price > self.MA200:
                    if not self.position:
                        #print(f'{current_date} OPEN  POS at ${round(close_price,2)}')
                        self.buy(sl=stoploss * close_price)
        if self.ATR > self.sell_atr_level: # High volatility, possibly seel before monthly rebalance period
            if (close_price < self.MA50):
                    #print(f'{current_date} CLOSE POS at ${round(close_price,2)}')
                    self.position.close()
            #print(f'Not end of month: {current_date}')

bt = Backtest(df, PaulTudorJonesStrategy, cash=10000, commission=.00075, trade_on_close=True, exclusive_orders=True, hedging=False)
#stats = bt.run()
stats = bt.optimize(
buy_atr_level = range( 1 , 10 , 1 ) ,
sell_atr_level = range ( 1 , 10 , 1 ) ,
maximize = 'Return [%]',
max_tries=100)

print(stats)
print(f"\nB&H Return %:  {round(stats['Buy & Hold Return [%]'],2)}")
print(f"Return %  {round(stats['Return [%]'],2)}")
print(f"Sharpe Ratio:  {round(stats['Sharpe Ratio'],2)}")

bt.plot()