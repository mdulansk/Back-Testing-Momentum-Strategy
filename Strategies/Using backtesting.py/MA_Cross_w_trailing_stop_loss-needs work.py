'''
Buy when short MA crosses above long MA
Optional: trailing stop, ATR stop, max loss stop,

'''

# Import libraries
import os
from os.path import exists
import datetime
import time
import pandas as pd
import pandas_ta as ta
#import MySQLdb as mdb # https://github.com/PyMySQL/mysqlclient-python/blob/master/doc/user_guide.rst#cursor-objects
import sqlalchemy as sql
from backtesting import Backtest
from backtesting import Strategy
from backtesting.lib import crossover
from backtesting.lib import SignalStrategy, TrailingStrategy
from backtesting.lib import crossover, plot_heatmaps, resample_apply, barssince
#from backtesting.test import GOOG

data_location = 'csv' # 'db' 'csv'
ticker = 'SPY' #'SPY' 'eurusd=x' 'BTC-USD' 'tqqq'
optimize = False
long_only = False
short_only = False

if data_location == 'csv':
    # Set variables and load data from csv
    data_folder = '/home/lantro/Documents/Algo Trading/Data/yahoo/daily_data'
    df = pd.read_csv(f"{data_folder}/{ticker}.csv", index_col=[0], parse_dates=True, skipinitialspace=True)
    df = df.rename(columns={"open": "Open", "close": "Close", "low": "Low", "high": "High", "volume": "Volume"})
    
elif data_location == 'db':
    # Obtain a database connection to the MySQL instance
    db_host = 'rpi4' #'localhost'
    db_user = 'sec_user'
    db_pass = 'securities'
    db_name = 'stock_data'
    unix_socket = "/var/run/mysqld/mysqld.sock"
    #dbconn = mdb.connect(host="localhost",unix_socket=unix_socket,user="sec_user",passwd="securities",db="securities_master")
    dbconn = mdb.connect(host=db_host,unix_socket=unix_socket,user=db_user,passwd=db_pass,db=db_name)
    #query = f"select Date,Open,High,Low,Close,Adj_Close,Volume from daily_data where ticker_id = (select id from security where ticker = 'SPY');"
    query = f"select Date,Open,High,Low,Close,Adj_Close,Volume from daily_data where ticker_id = (select id from security where ticker = '{ticker}');"
    df = pd.read_sql_query(query, dbconn)
    #df.reset_index(drop=True, inplace=True)
    #df.set_index('Date', inplace=True)
    df.index= pd.to_datetime(df.Date) #Convert index to DateTime index
    df.drop('Date',1, inplace=True)
    dbconn.close()

start_date = '2020-01-01' #Start date for data
end_date = '2022-08-01'
df = df.loc[start_date:end_date]



'''
The next function is a utility to load the necessary OHLC price files which you would like to use.
Backtests can be done for multiple time periods and assets, to match the design of your strategy. 
One thing to point out here is that the backtesting.py framework needs the column names in a specific format:
 (Open, Close, High, Low, Volume) so you can rename your columns using this statement:
'''

class ManyIndicatorStrategy(Strategy):
    short_ma_period  = 60
    long_ma_period = 200
    long_stop_pct = 8
    short_stop_pct = 2
    current_sell_stop = 0
    current_buy_stop = 0
    current_stop = 0
    upper_bound = 70
    lower_bound = 30
    rsi_window = 14
    long = True
    short = True

    # Do as much initial computation as possible
    def init(self):
        #print(f"self.data: {self.data}")
        #self.daily_rsi = self.I(ta.rsi, pd.Series(self.data.Close), self.rsi_window)
        # This magical function does all the resampling
        #self.weekly_rsi = resample_apply('W-FRI', ta.rsi, self.data.Close.s, self.rsi_window)
        #Note the use of the .s accessor to access the Close data as a Pandas series
        #self.MACD = self.I(ta.macd, pd.Series(self.data.Close), fast=12, slow=26, signal=9, talib=None, offset=None)
        self.MA_short = self.I(ta.sma, pd.Series(self.data.Close), self.short_ma_period)
        self.MA_long = self.I(ta.sma, pd.Series(self.data.Close), self.long_ma_period)
        

    # Step through bars one by one
    # Note that multiple buys are a thing here
    def next(self):
        current_bar_idx = len(self.data) - 1
        current_date = self.data.index[-1]
        price = self.data.Close[-1] # Yesterday's closing price
        if self.short == True:
            self.current_stop = max(self.current_stop, (1-self.long_stop_pct*.01)*price) #Don't keep moving DOWN!
            print(f'{current_date}  LONG:  current price:  {price}  current_stop :  {self.current_stop}')
            if price < self.current_stop and self.position:
                self.position.close()
                print(f'{current_date}  LONG: price ({price}) dropped {1-price/self.current_stop} below stop ({self.current_stop})')
            elif crossover(self.MA_short, self.MA_long):
            #print(f'{current_date} Buying {ticker}')
            #self.buy()
                if short_only == False:
                    #self.buy(sl=(1-self.long_stop_pct*.01)*price)
                    self.buy()
                    self.long_short = 'long'
        elif self.long == True:
            self.current_stop = min(self.current_stop, (1+self.short_stop_pct*.01)*price) #Don't keep moving UP!
            print(f'{current_date}  SHORT:  current price:  {price}  current_stop :  {self.current_stop}')
            if price > self.current_stop and self.position:
                self.position.close()
                print(f'{current_date}  SHORT: price ({price}) rose {1-self.current_stop/price} above stop ({self.current_stop})')
            elif crossover(self.MA_long, self.MA_short):
                #print(f'{current_date} Closing position in {ticker}')
                self.position.close()
                if self.long_only == False:
                    #self.sell(sl=(1+self.short_stop_pct*.01)*price)
                    self.sell()
                    self.long_short = 'short'
        

#bt = Backtest (GOOG, ManyIndicatorStrategy, cash = 10_000, commission = .002)
bt = Backtest(df, ManyIndicatorStrategy, cash=100000, commission=.00075, trade_on_close=True, exclusive_orders=True, hedging=False)
if optimize == True:
    stats = bt.optimize(
    long_ma_period = range( 50 , 300 , 10 ) ,
    short_ma_period = range ( 10 , 100 , 10 ) ,
    long_stop_pct = range ( 2 , 30 , 2 ) ,
    short_stop_pct = range ( 2 , 30 , 2 ) ,
    maximize = 'Equity Final [$]',
    constraint=(lambda p: p.short_ma_period < p.long_ma_period),
    max_tries=1000)
    print(stats)
    #print(stats['_trades'].to_string())
    #View best parameters:
    strategy = stats["_strategy"]
    print(f'\nshort_ma_period: {strategy.short_ma_period}')
    print(f'long_ma_period: {strategy.long_ma_period}')
    print(f'long_stop_pct: {strategy.long_stop_pct}')
    print(f'short_stop_pct: {strategy.short_stop_pct}')
    #bt.plot(filename=f"{strategy}.html")
else:
    stats = bt.run()
    print(stats)
    #print(stats['_trades']) #You can extract the series of trades made by the backtester for further analysis.
    bt.plot()


#Best Parameters:
# SPY:  short_ma_period: 60, long_ma_period: 200, long_stop_pct: 8, short_stop_pct: 2
# BTC-USD:  short_ma_period  = 10, long_ma_period = 50, long_stop_pct = 26, short_stop_pct = 8
# QQQ:  short_ma_period  = 40, long_ma_period = 130, long_stop_pct = 24, short_stop_pct = 8
# QQQ (long-only):  short_ma_period  = 90, long_ma_period = 220, long_stop_pct = 18, short_stop_pct = 8