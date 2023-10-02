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
#from backtesting.test import GOOG

data_location = 'csv' # 'db' 'csv'
ticker = 'BTC-USD' #'SPY' 'eurusd=x' 'BTC-USD' 'tqqq'

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

start_date = '2000-01-01' #Start date for data
end_date = '2022-08-01'
df = df.loc[start_date:end_date]


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
bt = Backtest (df, RsiOscillator, cash = 10_000, commission = .002)
stats = bt.run()
print(stats)
bt.plot()
