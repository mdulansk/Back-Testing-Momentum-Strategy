# Import Libraries:
import time
import logging
import pprint
logging.basicConfig(level=logging.ERROR)
import os
import sys
from time import perf_counter
from math import ceil, floor
from dataclasses import dataclass
import pandas as pd
from pandas.tseries.offsets import MonthEnd, BDay, DateOffset
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
# %matplotlib inline
import quantstats as qs
import itertools as it
from multiprocessing import Process, Pool
qs.extend_pandas() # # extend pandas functionality with metrics, etc.

#sys.path.append('/home/lantro/Documents/Algo Trading/Stock Price DB/')
HOME_DIR = os.path.expanduser('~/')
sys.path.append(f"{HOME_DIR}/Documents/Algo/Stock Price DB/")
#from StockPriceData import process_ticker
import StockPriceData

# Set some global variables:
script_path = os.path.dirname(__file__)
cached_data = script_path+'/'+'cached_data'
stats_data = script_path+'/'+'stats'
data_folder = f'{HOME_DIR}/Documents/Algo/Data'
ticker_folder = f'{data_folder}/Tickers/Nasdaq-100'
current_date = time.strftime("%Y.%m.%d.%H%M%S")
instrument = 'nasdaq100'#'ETF' # 'nasdaq100'

# Call get_parameters to get initial parameters for backtests.

# Import project modules:
import get_parameters, get_data, optimization, strategies, signals, risk_management, analysis

# Create Backtest class to hold all data
class Backtest:
    def __init__(self):
        pass

# Create data classes

@dataclass
class DataClassSettings:
    pass  # We'll move some of the non-optimization settings from DataClassParameters here.


@dataclass
class DataClassParameters:
    #benchmark_start_date: str = '2010-01-01'
    data_start_date: str = '2007-01-01'# '2010-01-01'
    data_end_date: str = '2022-12-23' # '2022-12-23'
    start_date: str = '2007-12-24'#'2010-01-01' # Strategy start
    end_date: str = '2022-12-23' # Strategy end
    benchmark_ticker: str = '^IXIC' # (NASDAQ) #'SPY' # (S&P500)
    cached_data: str = cached_data
    ticker_csv: str = None
    daily_price_csv: str = None
    stats_csv: str = None
    tickers: list = None
    current_tickers = []
    ticker_selections = dict()
    refresh_tickers: bool = False
    refresh_data: bool = False  #True
    resample_period: str = 'W' #'M' #'W'
    
    processes: int = None #15#16 # Set to None to use all CPU cores
    allow_any_param_combos = False # Filter out undesirable param combos in optimization
    synthetic_benchmark: bool = True#True
    index_yearly_members = None # DF containing the index members for each year
    all_stats: list = None # List to hold individual dictionaries containing strategy performance for various parameters
    performance_measure: str = 'perf_score' #'tot_ret' # What we'll use to sort our return data
    run_number: int = 1 # Don't change this.
    parameter_combos: list = None
    range_divisor: int = 1 #10 We divide the range of numbers for a parameter by this to determine how many data points to test
    param_multiplier: float = 1.5 #2.5 #1.5 #.8 #This is used to create range of parameter values for optimization. For example, specifying .8 means expanding value +/- 80%
    optimize_method: int = 1 # 1=original, 2=new method (not as good)
    optimize_params: bool = True#True
    run_max: int = 1 #5 # How many times to run the optimization function
    
    rebal_int: int = 5 #4 # 1 for monthly resample period, 4 for weekly?
    stop_type: str =  'indiv' #'avg'
    stop_enable: bool = False #True # Note: Stop function only works with monthly data (for the moment).
    stop: int = 80 #5 #15 #25 # Percentage stop
    qty_long_period: int = 25 #30 #3 Number of stocks to hold from longest rolling period
    qty_med_period: int = 20 #20 #2 Number of stocks to hold from medium rolling period
    qty_short_period: int = 5 #2 #1 Number of stocks to hold from shortest rolling period
    SMA_L: int = 139 # Days
    SMA_S: int = 9 #9 # Days
    rolling_l: int = 64 #16 # Months (or weeks depending on value of resample_period)
    rolling_m: int = 44 #11 # Months (or weeks depending on value of resample_period)
    rolling_s: int = 40 #10 # Months (or weeks depending on value of resample_period)
    all_parameters = ['rebal_int','stop_type', 'stop', 'qty_long_period', 'qty_med_period', 'qty_short_period', 'SMA_L', 'SMA_S', 'rolling_l', 'rolling_m', 'rolling_s']
    params_to_optimize = ['rolling_s']

@dataclass
class DataClassPriceData:
    benchmark_prices: pd.core.frame.DataFrame = None
    benchmark_returns: pd.core.frame.DataFrame = None
    stock_prices: pd.core.frame.DataFrame = None
    stock_returns: pd.core.frame.DataFrame = None #We can reference whichever return period we want for this
    daily_returns: pd.core.frame.DataFrame = None # We use this for calculating trailing stop
    
@dataclass
class DataClassPerformanceData:
    benchmark_performance: pd.core.frame.DataFrame = None
    strategy_performance: pd.core.frame.DataFrame = None
    strategy_objs = []
    all_stats_df: pd.core.frame.DataFrame = pd.DataFrame()
    best_return_series: pd.Series = None
    best_return_tickers: dict = None

def main():
    #global price_data
    #global performance_data
    #global parameter_data
    performance_data = DataClassPerformanceData()
        
    t1_start = perf_counter()
    if instrument == 'nasdaq100':
        parameter_data = DataClassParameters(qty_long_period=25,qty_med_period=20,qty_short_period=10,SMA_S=(9),SMA_L=(139),
                                         rolling_l=(34), rolling_m=(16),rolling_s=(8),stop=40,resample_period='M',rebal_int= 3) # Monthly values
        #parameter_data = DataClassParameters(qty_long_period=25,qty_med_period=20,qty_short_period=10,SMA_S=(2),SMA_L=(139),
        #                                 rolling_l=(71), rolling_m=(21),rolling_s=(10),stop=15,resample_period='W',rebal_int= 4) # Weekly values
        #parameter_data.ticker_csv = f'{cached_data}/{instrument}_tickers.csv'
        parameter_data.ticker_csv = f'{ticker_folder}/nasdaq_all_historic_tickers.csv'
        parameter_data.tickers = get_data.get_nasdaq_tickers(parameter_data)
        #parameter_data.index_yearly_members = pd.read_csv(f'{ticker_folder}/nasdaq_yearly_members_2007-12-24_2023-03-12.csv') #This file contains yearly index members 
        parameter_data.index_yearly_members = pd.read_csv(f'{ticker_folder}/nasdaq_yearly_members_2007-12-24_2023-03-12.csv', parse_dates=True, index_col=0) #This file contains yearly index members 
    elif instrument == 'ETF':
        parameter_data = DataClassParameters(qty_long_period=3,qty_med_period=2,qty_short_period=1,SMA_S=(10),SMA_L=(200),
                                         rolling_l=(12), rolling_m=(6),rolling_s=(3),stop=15)
        parameter_data.tickers = ['VFINX','VINEX','VUSTX']
        
    parameter_data.benchmark_price_csv = f'{cached_data}/{instrument}_benchmark_daily_prices.csv'
    parameter_data.daily_price_csv = f'{cached_data}/{instrument}_daily_prices.csv'
    parameter_data.stats_csv = f'{stats_data}/{parameter_data.resample_period}_{instrument}_stats_{current_date}.csv'
    print(f'{parameter_data.ticker_csv}\n{parameter_data.daily_price_csv}\n{parameter_data.stats_csv}')
    
    daily_prices_df,daily_returns,weekly_returns,monthly_returns = get_data.get_price_data(parameter_data)
    benchmark_price_df,benchmark_return_series = get_data.get_benchmark_data(monthly_returns,parameter_data)

    if parameter_data.resample_period == 'W': stock_returns = weekly_returns
    else: stock_returns = monthly_returns
    price_data = DataClassPriceData(benchmark_prices=benchmark_price_df,benchmark_returns=benchmark_return_series,
                                    stock_prices=daily_prices_df,stock_returns=stock_returns,daily_returns=daily_returns)
    
    all_stats_df = optimization.optimize(price_data,parameter_data,performance_data)
    all_stats_df.to_csv(parameter_data.stats_csv, index=False)
    
    #print(f'Top performance:\n{performance_data.all_stats_df.head(10)}',flush=True)    
    print(f'Final Top performance:\n{all_stats_df.head(10)}',flush=True)    
    
    ###################################################################################################
    # NOTE: Instead of outputting all_stats and finding top parameters, then re-running the strategy
    # with those parameters to get the best returns, why not have each strategy instance keep track of it's 
    # performance parameter, then in the optimize function, reference the best performing instance? We could then run the strategy
    # method for that instance to get the returns. Alternatively, we cound have each strategy instance store it's 
    # returns series ( unless this takes up too much memory and affects performance )
    ###################################################################################################
    
    # NOTE: We need a better way to pass the return series from the best performing strategy run instead of passing around the performance data dataclass
    best_returns_series = performance_data.best_return_series # Simple returns.
    print(f'Best Return Series Cumprod: {round((best_returns_series+1).cumprod()[-1]-1,2)}')
    #print(f'benchmark_return_series total return using log returns: {np.exp(((benchmark_return_series).cumsum()[-1]))-1}')
    #print(f'best_returns_series total return using log returns: {np.exp(((best_returns_series).cumsum()[-1]))-1}')
    
    benchmark_return_series = np.exp(benchmark_return_series)-1 # Convert log returns to simple returns
    benchmark_return_series = benchmark_return_series.loc[parameter_data.start_date:parameter_data.end_date]
    best_returns_series = performance_data.best_return_series

    print((f'benchmark_return_series: {len(benchmark_return_series.index)} periods\t{benchmark_return_series.index[0]} - {benchmark_return_series.index[-1]}'))
    print((f'best_returns_series: {len(best_returns_series.index)} periods\t{best_returns_series.index[0]} - {best_returns_series.index[-1]}'))
    #print(f'benchmark_return_series\tmin: {round(benchmark_return_series.values.min(),2)}\tmax: {round(benchmark_return_series.values.max(),2)}\tmean: {round(benchmark_return_series.values.mean(),2)}')
    #print(f'best_returns_series\t\tmin: {round(best_returns_series.values.min(),2)}\tmax: {round(best_returns_series.values.max(),2)}\tmean: {round(best_returns_series.values.mean(),2)}')
    #print(f'benchmark_return_series total return using cumprod: {((benchmark_return_series+1).cumprod()[-1])-1}')
    #print(f'best_returns_series total return using cumprod: {((best_returns_series+1).cumprod()[-1])-1}')
    
    benchmark_return_series.to_csv(f'{cached_data}/benchmark_return_series.csv', index=True)
    best_returns_series.to_csv(f'{cached_data}/best_returns_series.csv', index=True)
    
    #tot_ret, cagr, sharpe, max_dd = analysis.calc_stats(best_returns_series, 'Strategy')
    #print(f'Strategy Tot Ret: {tot_ret},  CAGR: {cagr},  Sharpe Ratio:  {sharpe},  Max DD:  {max_dd}')
    qs.reports.metrics(best_returns_series, benchmark_return_series, mode='basic') # Compare returns to benchmark
    #qs.reports.metrics(best_returns_series, benchmark_return_series, mode='full') # Compare returns to benchmark
    qs.reports.plots(best_returns_series, benchmark_return_series, mode='full') # Compare returns to benchmark

    #print(f'best_return_tickers:\n{performance_data.best_return_tickers}')

    #Same reports, but specifying a df?
    ##qs.reports.plots(best_returns_df, benchmark_return_series, mode='full') # Compare returns to benchmark
    
    #analysis.plot_returns(best_returns_series,benchmark_return_series)
    '''
    Improvements:
    During parameter optimization, only test combinations that have been teseted before by comparing to paramter combos from all_stats.
    Split data into train/test dataframes when optimizing
    Only select stocks with positive performance
    Add ability to turn off strategy parameters such as stop, SMA_L & SMA_S check, rolling periods to see which ones matter most.

    
    Best monthly data performance:
    rebal_int    top_n  SMA_S  SMA_L  stop  rolling_l  rolling_m  rolling_s  tot_ret  cagr  sharpe  perf_score  max_dd
    1  (25, 20, 3)      9    139    80         34         16          8   175.45  0.96    7.17     1257.98   -0.52
    1  (25, 20, 4)      9    139    80         34         16          8   110.91  0.85    7.29      808.53   -0.49
    1  (25, 20, 5)      9    139    80         34         16          8    87.34  0.79    7.26      634.09   -0.45
    1  (25, 20, 5)      9    139    80         34         16          8    87.34  0.79    7.26      634.09   -0.45
    1  (25, 20, 5)      9    139    80         34         16          9    82.39  0.78    7.05      580.85   -0.48
    1  (25, 20, 5)      9    139    80         38         16          9    77.78  0.77    6.93      539.02   -0.46
    1  (25, 20, 5)      9    139    80         34         16         11    73.42  0.75    7.13      523.48   -0.44
    1  (25, 20, 5)      9    139    80         34         16         10    72.93  0.75    6.97      508.32   -0.47
    1  (25, 20, 5)      9    139    80         37         16          8    72.15  0.75    7.02      506.49   -0.45
    1  (25, 20, 5)      9    139    80         37         16          9    71.51  0.75    6.84      489.13   -0.46
    1  (25, 20, 5)      9    139    80         23         16          9    69.86  0.74    6.84      477.84   -0.46
    1  (25, 20, 5)      9    139    80         16         16          9    67.11  0.73    6.79      455.68   -0.46
    1  (25, 20, 5)      9    139    80         19         16          9    66.14  0.73    6.77      447.77   -0.46
    1  (25, 20, 6)      9    139    80         34         16          8    65.17  0.73    7.13      464.66   -0.43
    Best weekly data performance:
    rebal_int    top_n   SMA_S  SMA_L  stop  rolling_l  rolling_m  rolling_s  tot_ret  cagr  sharpe  perf_score  max_dd
    6  (25, 20, 5)      2    150    80         64         44         40    15.79  0.43    6.81      107.53   -0.29
    6  (25, 20, 5)      2    139    80         34         21         10    14.22  0.42    7.28      103.52   -0.23
    6  (25, 20, 5)      2    139    80         34         19         10    13.63  0.41    7.25       98.82   -0.23
    6  (25, 20, 5)      2    139    80         44         21         10    12.89  0.40    7.32       94.35   -0.23
    6  (25, 20, 4)      2    139    80         34         21         10    13.75  0.41    6.73       92.54   -0.28
    '''    
    t1_stop = perf_counter()
    print("Elapsed time during the whole program in seconds:", round(t1_stop-t1_start, 2))

main()