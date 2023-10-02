'''
Description: From Financial Wisdom Youtube channel
"BITCOIN TRADING - Arguably The Best Bitcoin Trading strategy"
Indicators:
    MACD: 26 period EMA, 12 period EMA, 9 period EMA (signal)
    Use daily and weekly MACD indicators using settings above.
Rules:
    Trading window (only long if true):  Weekly MACD line crosses above its signal line
    BUY: at opening of week after weekly MACD line crossed and closed above the signal line
    SELL stop:
        If DAILY MACD closes below signal line:
            Set stop loss at LOW of that day's closing candle
    RENTRY: after DAILY MACD line crosses above signal line AND WEEKLY MACD line above its signal line


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

data_folder = '/home/lantro/Documents/Algo Trading/Data/yahoo/daily_data/'
ticker = 'BTC-USD' #'spy' 'eurusd=x' 'BTC-USD' 'tqqq'
df = pd.read_csv(f"{data_folder}{ticker}.csv", index_col=[0], parse_dates=True, skipinitialspace=True)
df = df.rename(columns={"open": "Open", "close": "Close", "low": "Low", "high": "High", "volume": "Volume"})
start_date = '2000-01-01' #Start date for data
end_date = '2022-08-01'
df = df.loc[start_date:end_date].copy()
trade_on_close = False # If set to True, will trade at close price on same day as signal, which doesn't make sense if your 
# signals are based on closing prices! 

'''
The next function is a utility to load the necessary OHLC price files which you would like to use.
Backtests can be done for multiple time periods and assets, to match the design of your strategy. 
One thing to point out here is that the backtesting.py framework needs the column names in a specific format:
 (Open, Close, High, Low, Volume) so you can rename your columns using this statement:
'''

class DualMACDStrategy(Strategy):
    buy_atr_level = 8
    sell_atr_level = 7
    stop_pct = 13
    current_stop = -1
    # Do as much initial computation as possible
    def init(self) :
        self.daily_MACD = self.I(ta.macd, pd.Series(self.data.Close), fast=12, slow=26, signal=9, talib=None, offset=None)
        #Note: The MACD indicator call returns an ndarray with 3 columns: fast, hist, and signal, The first index indicates the array,
        # and the second index indicates the row, where [-1] is latest value.
        
        # This magical function does all the resampling
        self.weekly_MACD = resample_apply('W-FRI', ta.macd, self.data.Close.s, fast=12, slow=26, signal=9, talib=None, offset=None)
        #Note the use of the .s accessor to access the Close data as a Pandas series
        
    # Step through bars one by one
    # Note that multiple buys are a thing here
    def next(self):
        current_bar_idx = len(self.data) - 1
        signal_date = self.data.index[-2] #
        trade_date = self.data.index[-1]
        close_price = self.data.Close[-2] # Closing price, 2 days ago
        open_price =  self.data.Open[-1] # Yesterday's opening price, since all prices seem to be based on yesterday's bar
        #print((self.daily_MACD[0][-1], self.daily_MACD[1][-1], self.daily_MACD[2][-1]))
        daily_MACDfast = self.daily_MACD[0][-1] # Fast, 2 days ago, since trade will place at open of yesterday's bar
        daily_MACDhist = self.daily_MACD[1][-1] # Histogram, 2 days ago
        daily_MACDsig = self.daily_MACD[2][-1] # Signal, 2 days ago
        weekly_MACDfast = self.weekly_MACD[0][-1]
        weekly_MACDhist = self.weekly_MACD[1][-1]
        weekly_MACDsig = self.weekly_MACD[2][-1]
        #print(f'{signal_date}  Daily MACD,HIST,SIGNAL:\t{daily_MACDf},\t{daily_MACDs},\t{daily_MACDh}')
        #print(f'{signal_date}  Weekly MACD,HIST,SIGNAL:\t{daily_MACDf},\t{daily_MACDs},\t{daily_MACDh}')
        # Check if weekly MACD is above its signal line.
        if weekly_MACDfast > weekly_MACDsig: # Trading "window" open
            if (daily_MACDfast < daily_MACDsig): # Check if weekly MACD fast value above its signal line
                if close_price < self.current_stop and self.position:
                    print(f'{signal_date} EOD Daily MACD,HIST,SIGNAL:\t{daily_MACDfast},\t{daily_MACDsig},\t{daily_MACDhist}')
                    print(f'{signal_date} EOD Weekly MACD,HIST,SIGNAL:\t{weekly_MACDfast},\t{weekly_MACDsig},\t{weekly_MACDhist}')
                    if trade_on_close == True:
                        print(f'{trade_date} D STOPPED OUT at yesterday\'s close ${round(close_price,2)}')
                    else:
                        print(f'{trade_date} D STOPPED OUT at today\'s open') #We can't access today's open price, only yesterday's price bar
                    self.position.close()
                else: #Set sell stop = closing price
                    self.current_stop = max(self.current_stop, close_price*(1-self.stop_pct*.01)) #Don't keep moving DOWN!
                    #print(f'{signal_date} Price ${round(close_price,2)} Stop ${round(self.current_stop,2)}')
                    
            elif daily_MACDfast > daily_MACDsig:
                if not self.position:
                    print(f'{signal_date}  EOD Daily MACD,HIST,SIGNAL:\t{daily_MACDfast},\t{daily_MACDsig},\t{daily_MACDhist}')
                    print(f'{signal_date}  EOD Weekly MACD,HIST,SIGNAL:\t{daily_MACDfast},\t{daily_MACDsig},\t{daily_MACDhist}')
                    #print(f'{signal_date} OPEN Pos at ${round(close_price,2)}')
                    if trade_on_close == True:
                        print(f'{trade_date} D OPEN Pos at yesterday\'s close ${round(close_price,2)}')
                    else:
                        print(f'{trade_date} D OPEN Pos at today\'s open') #We can't access today's open price, only yesterday's price bar
                    #self.buy(sl=0.85*close_price)
                    self.buy()
                    self.current_stop = close_price*(1-15*.01)
                    print(f'{signal_date} Initial stop:  {self.current_stop}')
        else: # Weekly MACD fast value below signal, so trading window closed
            if close_price < self.current_stop and self.position:
                print(f'{signal_date}  EOD Daily MACD,HIST,SIGNAL:\t{daily_MACDfast},\t{daily_MACDsig},\t{daily_MACDhist}')
                print(f'{signal_date}  EOD Weekly MACD,HIST,SIGNAL:\t{daily_MACDfast},\t{daily_MACDsig},\t{daily_MACDhist}')
                #print(f'{signal_date} W CLOSE POS at ${round(close_price,2)}')
                if trade_on_close == True:
                        print(f'{trade_date} D CLOSE POS at yesterday\'s close ${round(close_price,2)}')
                else:
                    print(f'{trade_date} D CLOSE POS at today\'s open') #We can't access today's open price, only yesterday's price bar
                self.position.close()
            else: #Set sell stop = closing price
                self.current_stop = max(self.current_stop, close_price*(1-self.stop_pct*.01)) #Don't keep moving DOWN!
                #print(f'{signal_date} Price ${round(close_price,2)} Stop ${round(self.current_stop,2)}')
#bt = Backtest(GOOG, DualMACDStrategy, cash=10000, commission=.00075, trade_on_close=True, exclusive_orders=True, hedging=False)
bt = Backtest(df, DualMACDStrategy, cash=100000, commission=.00075, trade_on_close=trade_on_close, exclusive_orders=True, hedging=False)
stats = bt.run()
'''
stats = bt.optimize(
stop_pct = range( 0 , 25 , 1 ),
maximize = 'Return [%]',
max_tries=100)
'''
print(stats)
print(stats['_trades'].to_string())
print(f"\nB&H Return %:  {round(stats['Buy & Hold Return [%]'],2)}")
print(f"Return %  {round(stats['Return [%]'],2)}")
print(f"Sharpe Ratio:  {round(stats['Sharpe Ratio'],2)}")
strategy = stats [ "_strategy" ]
print(f'\nIdeal stop_pct: {strategy.stop_pct}') # Idea parameter from optimization
#bt.plot()