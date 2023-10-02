# %% [markdown]
# Momentum Trading Strategy on the Nasdaq with Python using multiple lookbacks

# %% [markdown]
# Strategy Rules:
# Trade frequency: monthly, same day each month
# Select the top 50 nasdaq stocks with highest returns for past 12 months
# Of top 50, select the top 30 with highest returns for past 6 months
# Of top 30, select the top 10 stocks with highest returns for past 3 months.
# Remove survivorship bias:
#     For this script, we only remove stocks that are in the Nasdaq index the entire period. To actually remove survivorship bias, we would need to get the Nasdaq constituents over time and adjust the stocks used in our strategy.
# 

# %% [markdown]
# #### Improvements:
# ###### Add "Regime filter to only buy when benchmark index > its 200MA - DONE
# ######    Change np.where() usage to use a function to set cross signal: -1, 0, 1
# ###### Get index constituents for each time period and add / remove stocks as necessary to minimize survivorship bias
# ###### Optimize regime filter by adjusting SMA lenth for BUY / SELL decisions
# ###### Scale in/out based on regime filter. i.e. benchmark below 50 day MA, only invest 50%, if benchmark below 200 day MA, don't invest.
# ###### Add function to implement fixed stop for portfolio as a whole
# ###### Add function to implement trailing stop for portfolio as a whole
# ###### Add function to implement trailing stop for individual stocks in portfolio
# # Change from min/max values to single starting value and adjust for each recursive run:
#   Run 1: parameter values +/- 50%, large divisor (10?)
#   Run 2: parameter values +/- 40%, large divisor (10?)
#   Run 3: parameter values +/- 30%, medium divisor (5)
#   Run 4: parameter values +/- 20%, small divisor (1)
# Alternatively, just reduce multiplier each run until it is 1
# Try different time periods, such as weekly


#
# Multiprocessing: 
#  https://superfastpython.com/multiprocessing-for-loop/
#  https://superfastpython.com/multiprocessing-in-python/#How_to_Return_a_Value_From_a_Process
# 

# %%
import logging
import pprint
logging.basicConfig(level=logging.ERROR)
import os
import sys
from time import perf_counter
from math import ceil, floor
from dataclasses import dataclass
import pandas as pd
from pandas.tseries.offsets import MonthEnd, DateOffset
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
from StockPriceData import process_ticker
script_path = os.path.dirname(__file__)
cached_data = script_path+'/'+'cached_data'
stats_data = script_path+'/'+'stats'


# %%
#start_date = '2010-01-01'
#end_date = '2022-12-23'
#benchmark = '^IXIC' # NASDAQ #'SPY'
#refresh_data = False #True
#all_stats = [] # List to hold individual dictionaries containing strategy performance for various parameters
#performance_measure = 'perf_score' #'tot_ret' # What we'll use to sort our return data

# %%
# Get price data  for our benchmark, then convert to series with name set to ticker symbol
#benchmark_sma_200 = pd.Series(round(benchmark_price_df['Adj_Close'].rolling(100).apply(np.mean),2),name='SMA200')
#benchmark_sma_50 = pd.Series(round(benchmark_price_df['Adj_Close'].rolling(50).apply(np.mean),2),name='SMA50')
#benchmark_sma_20 = pd.Series(round(benchmark_price_df['Adj_Close'].rolling(20).apply(np.mean),2),name='SMA20')
#benchmark_sma_10 = pd.Series(round(benchmark_price_df['Adj_Close'].rolling(10).apply(np.mean),2),name='SMA10')
#benchmark_price_df=benchmark_price_df.join(benchmark_sma_200)



# %%
def generate_signals(benchmark_price_df, SMA_short, SMA_long):
    signals_df = benchmark_price_df.copy()
    '''This function takes the price df for our benchmark and 2 period lengths to be used to caculate SMAs which are used 
    to set uptrend, downtrend, and cross signals in the signals_df dataframe.'''
    #signals_df['SMA200'] = pd.Series(round(signals_df['Adj_Close'].rolling(200).apply(np.mean),2),name='SMA200')
    #signals_df['SMA20'] = pd.Series(round(signals_df['Adj_Close'].rolling(20).apply(np.mean),2),name='SMA20')
    signals_df['SMA_short'] = pd.Series(round(signals_df['Adj_Close'].rolling(SMA_short).apply(np.mean),2),name='SMA_short')
    #signals_df['SMA_medium'] = pd.Series(round(signals_df['Adj_Close'].rolling(SMA_medium).apply(np.mean),2),name='SMA_medium')
    signals_df['SMA_long'] = pd.Series(round(signals_df['Adj_Close'].rolling(SMA_long).apply(np.mean),2),name='SMA_long')
    #signals_df['uptrend'] = signals_df['Adj_Close'] > signals_df['SMA_long']
    signals_df['uptrend'] = signals_df['SMA_short'] > signals_df['SMA_long']
    #signals_df['downtrend'] = signals_df['Adj_Close'] < signals_df['SMA_long']
    signals_df['downtrend'] = signals_df['SMA_short'] < signals_df['SMA_long']
    signals_df['cross_up'] = np.where((signals_df['uptrend'] == True) & (signals_df.shift(1)['uptrend'] == False) ,1,0)
    signals_df['cross_down'] = np.where((signals_df['downtrend'] == True) & (signals_df.shift(1)['downtrend'] == False) ,1,0)
    #signals_df[signals_df['cross'] == 1]
    #signals_df['2001-11-30':'2001-12-04']
    #signals_df["cross"][signals_df["cross"]==1]
    crosses = np.where((signals_df['cross_up'] == True) | (signals_df['cross_down'] == True) ,1,0) # Returns numpy array of 0's and 1's
    num_crosses = len(crosses[crosses==1])
    #print(f'num_crosses: {num_crosses}')
    idx = pd.date_range(signals_df.index[0], signals_df.index[-1])
    signals_df = signals_df.reindex(idx, method='ffill') # We re-index and forward-fill missing values so that our regime df has values for all possible end-of-month dates, even non-business days
    return(signals_df, num_crosses)

#signals_df,num_crosses = generate_signals(benchmark_price_df,1,200) # Setting short-term period = 1 is the same as using actual price for cross signal
#signals_df.index[0]
#signals_df.head(10)



# %%
def plot_signals(signals_df):
    xdate = [x.date() for x in signals_df.index]
    plt.figure(figsize=(35, 15))
    plt.text(0.05, 0.95, f"Total Crosses: {num_crosses:.2f}", transform=plt.gca().transAxes)
    plt.plot(xdate, signals_df.Adj_Close, label="Close")
    plt.plot(xdate, signals_df.SMA_short,label="SMA_short")
    plt.plot(xdate, signals_df.SMA_long,label="SMA_long")
    #plt.scatter(signals_df["cross"][signals_df["cross"]==1].index, signals_df["cross"][signals_df["cross"]==1], marker="^", s=50, color="b", alpha=0.9)
    plt.scatter(signals_df["cross_up"][signals_df["cross_up"]==1].index, signals_df.loc[signals_df["cross_up"][signals_df["cross_up"]==1].index].Adj_Close, marker="^", s=100, color="orange", alpha=0.9)
    plt.scatter(signals_df["cross_down"][signals_df["cross_down"]==1].index, signals_df.loc[signals_df["cross_down"][signals_df["cross_down"]==1].index].Adj_Close, marker="v", s=100, color="red", alpha=0.9)
    plt.xlim(xdate[0], xdate[-1])
    plt.grid()
    plt.show

#signals_df,num_crosses = generate_signals(benchmark_price_df,1,200) # Setting short-term period = 1 is the same as using actual price for cross signal
#plot_signals(signals_df)



# %%
def get_nasdaq_tickers(refresh_data):
    if refresh_data == True:
        try:
            tickers_df = pd.read_html("https://en.wikipedia.org/wiki/Nasdaq-100")[4]
            tickers_df.to_csv(f'{cached_data}/nasdaq100_tickers.csv', index=False)
            #tickers = ticker_df.Ticker.to_list()
        except:
            print(f"Can't connect to https://en.wikipedia.org/wiki/Nasdaq-100, reading from nasdaq100_tickers.csv")
            tickers_df = pd.read_csv(f'{cached_data}/nasdaq100_tickers.csv')
    else:
        tickers_df = pd.read_csv(f'{cached_data}/nasdaq100_tickers.csv')
        #tickers = tickers_df['Ticker'].to_list()
    tickers = tickers_df['Ticker'].to_list()
    tickers.remove('GOOGL') # This is essentially a duplicate of GOOG
    return(tickers)


#def get_user_tickers(refresh_data):
def get_user_tickers(refresh_data):
    if refresh_data == True:
        #tickers=['VFINX','VINEX','VUSTX']
        pd.Series(tickers,name='Ticker').to_csv(f'{cached_data}/tickers.csv', index=False)#, header=False) #Convert to pandas series to write out to csv
    else:
        tickers_df = pd.read_csv(f'{cached_data}/tickers.csv')
        tickers = tickers_df['Ticker'].to_list()
    return(tickers)

#tickers = get_tickers(refresh_data)
#tickers = get_nasdaq_tickers(refresh_data)
#print(f'Tickers: {tickers}')



# Get adjusted close price data for all tickers and concatenate to one dataframe

# We'll import the price data for the tickers from our database:
def get_price_data(parameter_data):
    if parameter_data.refresh_data == True:
        tickers_and_prices = {}
        for ticker in parameter_data.tickers[:]:
            tickers_and_prices[ticker] = process_ticker(ticker,parameter_data.start_date,parameter_data.end_date)['Adj_Close']
            # This next line concatenates the series to the dataframe, but doesn't include the series name as the column name.
            #daily_prices = pd.concat([price_data, prices],names=[ticker])
        all_daily_prices_df = pd.concat(tickers_and_prices, axis=1)
        all_daily_prices_df.to_csv(f'{cached_data}/all_daily_prices.csv')
    else:
        all_daily_prices_df = pd.read_csv(f'{cached_data}/all_daily_prices.csv', index_col=['Date'], parse_dates=True)
    # Clean up price df by removing stocks which don't have data for entire period, then calculate daily an monthly returns
    daily_prices_df = all_daily_prices_df.copy()#.dropna(axis=1) # Drop any stocks that are missing values
    symbols_missing_start_data = (daily_prices_df.loc[:, daily_prices_df.iloc[0].isnull()]).columns
    daily_prices_df.drop(columns=symbols_missing_start_data,inplace=True)
    # Add column for cash option for when there are no positive returns 
    daily_prices_df['CASH'] = 0.0 # We set to 0 to simulate 0% return as alternative to other investments when they're negative
    daily_returns = (daily_prices_df.pct_change()+1)[1:] # Adding 1 allows us to take the product of returns. Can't use cumsum though.
    weekly_returns = daily_returns.resample('W').prod() # Need to subtract 1 to get actual % returns.
    monthly_returns = daily_returns.resample('M').prod() # Need to subtract 1 to get actual % returns.
    #benchmark_monthly_returns = monthly_returns.mean(axis=1) # Instead of using index as benchmark, use product of returns for all stocks in universe
    return(daily_prices_df,daily_returns,weekly_returns,monthly_returns)


def get_rolling_ret(df, lookback):
    # Calculates rolling cumulative return for supplied df for specified lookback period
    return df.rolling(lookback).apply(np.prod)


def get_top_tickers(date,top_n,rolling_returns):
    rolling_long, rolling_med, rolling_short = rolling_returns[0],rolling_returns[1],rolling_returns[2]
    top_coarse = rolling_long.loc[date].nlargest(top_n[0]).index # Get the top 50 from the 12 month rolling average returns
    top_med = rolling_med.loc[date, top_coarse].nlargest(top_n[1]).index # From the top 50 ,get the top 30 from the 6 month rolling average returns
    top_fine = rolling_short.loc[date, top_med].nlargest(top_n[2]).index # From the top 30 ,get the top 10 from the 3 month rolling average returns
    #top_10 = rolling_short.loc[date, top_30].nlargest(10).ge(1).index # From the top 30 ,get the top 10 from the 3 month rolling average returns
    #top_10 = rolling_short.loc[date, top_30].nlargest(10) # From the top 30 ,get the top 10 from the 3 month rolling average returns
    #top_10_above_zero = top_10[top_10.ge(1)] ## Try getting just tickers with a positive return for the current period.
    #print(f'top_10_above_zero: ({len(top_10_above_zero)}): {top_10_above_zero}')
    ##Example: curr = all_mtl_ret_lb.iloc[row][all_mtl_ret_lb.iloc[row].ge(0)] # Only stocks with prices >= 0
    #print(f'top_10 > 1 ({len(top_10)}): {rolling_short.loc[date, top_10]}')
    return top_fine

# get_top_tickers('2010-12-31',12,5,3)

# %%
def get_top_tickers_reversed(date,rolling_long, rolling_med, rolling_short):
    top_50 = rolling_short.loc[date].nlargest(50).index # Get the top 50 from the 12 month rolling average returns
    top_30 = rolling_med.loc[date, top_50].nlargest(30).index # From the top 50 ,get the top 30 from the 6 month rolling average returns
    top_10 = rolling_long.loc[date, top_30].nlargest(10).index # From the top 30 ,get the top 10 from the 3 month rolling average returns
    return top_10

# get_top_tickers('2010-12-31',12,5,3)

# %%
def fixed_stop(period_daily_ret, stop_loss, stop_type='avg'):
    ''' This function just iterates through a dataframe of stocks and determines if the price over the period falls to the stop level.  
    If the return for any portfolio stocks fall below the stop loss level, the remaining return values for that stock are
    set to 0, which would be our return on the stock if we sold it on the next day.'''
    # IMPORTANT: you need to subtract 1 from entire returns dataframe instead of just when calculating trailing stop 
    # return since we sometimes take original return
    stop_loss = -1*(stop_loss)
    period_daily_ret = period_daily_ret-1
    #print(f'period_daily_ret:\n{period_daily_ret.iloc[0]}')
    if stop_type == 'avg':
        period_daily_ret = pd.DataFrame(period_daily_ret.mean(axis=1),columns=['avg_ret']) # Average the individual returns                
    for stock_idx in range(len(period_daily_ret.columns)): #Iterate through each stock
        ticker = period_daily_ret.columns[stock_idx]
        cum_ret = 0 # To keep track of cumulative return for a stock
        for row in range(len(period_daily_ret)-0): # go through daily return for entire rolling lookback period
            curr_date = period_daily_ret.iloc[row].name
            period_ret = period_daily_ret.iloc[row,stock_idx]
            #print(f'{curr_date}\tPeriod return:  {period_ret}')
            cum_ret += period_ret
            #print(f'cum_ret:  {cum_ret}')
            if cum_ret <= stop_loss:
                #print(f'{curr_date}\t{ticker}\tCumulative return ({cum_ret}) < stop loss level ({stop_loss})  SELL!')
                period_daily_ret.iloc[row+1:,stock_idx] = 0 # Set values for stock to 0 from next day to end of period df
                break # Exit the loop since we're no longer in the stock
            else:
                #print(f'{curr_date}\t(cum_ret) {cum_ret} < {peak_cum_return} (peak_cum_return)\ttrailing_stop:  {trailing_stop}')
                pass
    period_total_returns = period_daily_ret.cumsum().iloc[-1,:] # This gives us the cumulative returns for all stocks
    #print(f'period_total_returns:  {period_total_returns}')
    #curr_ret = period_total_returns.prod() # Only use if you added 1 to return percentages
    curr_ret = period_total_returns.mean()#(axis=0).values[0] # Use this if you are using actual percentage returns
    #return period_daily_ret
    return(curr_ret+1) # Add 1 to entire return so we take prod of return series

# %%
def trailing_stop(period_daily_ret, stop_loss, stop_type='avg'):
    ''' This function just calculates a trailing stop on all the stock returns in the daily return df that is passed to it.
    If the return for any portfolio stocks fall below the stop loss level, the remaining return values for that stock are
    set to 0, which would be our return on the stock if we sold it on the next day.'''
    # Improvement: add trailing loss based on mean of all stocks.
    print(f'period_daily_ret.head(10):\n{period_daily_ret.head(10)}')
    ##print(f'{(period_daily_ret.index[0]).date()} - {(period_daily_ret.index[-1]).date()}\t{period_daily_ret.columns.values}, Stop Loss:  {stop_loss}')
    # Iterate through the dates in winning_returns_df
    #for stock in period_daily_ret.columns:
    # IMPORTANT: you need to subtract 1 from entire returns dataframe instead of just when calculating trailing stop 
    # return since we sometimes take original return
    stop_loss = stop_loss*.01 #Convert back to percentage since it was expressed as integer to be used with range function
    period_daily_ret = period_daily_ret-1
    if stop_type == 'avg':
        period_daily_ret = pd.DataFrame(period_daily_ret.mean(axis=1),columns=['avg_ret'])
    print(f'\nApplying {stop_loss*10}% stop loss for {pd.to_datetime(period_daily_ret.iloc[0].name).date()} - {pd.to_datetime(period_daily_ret.iloc[-1].name).date()}',flush=True)
    #print(f'Applying stop {stop_loss} loss for {period_daily_ret.values[0]} - {period_daily_ret.values[-1]}',flush=True)
    for stock_idx in range(len(period_daily_ret.columns)): #Iterate through each stock
        ticker = period_daily_ret.columns[stock_idx]
        cum_ret = 0 # To keep track of cumulative return for a stock
        peak_cum_return = 0 # This is to keep track of highest return for each stock
        trailing_stop = -1*(stop_loss)
        print(f'\n{stock_idx}\t{ticker}\tInitial stop:  {trailing_stop}',flush=True)
        for row in range(len(period_daily_ret)-0): # go through daily return for entire rolling lookback period
            curr_date = period_daily_ret.iloc[row].name
            period_ret = period_daily_ret.iloc[row,stock_idx]
            print(f'{row} {curr_date}\tPeriod return:  {period_ret}',flush=True)
            cum_ret += period_ret
            print(f'{curr_date}\tcum_ret:  {cum_ret}',flush=True)
            if cum_ret > peak_cum_return:
                print(f'{curr_date}\t Cum_ret ({cum_ret}) > {peak_cum_return} (peak_cum_return)\ttrailing_stop:  {peak_cum_return - stop_loss}',flush=True)
                peak_cum_return = cum_ret
                print(f'{curr_date}\tPeak Cum. return:  {peak_cum_return}',flush=True)
                trailing_stop = peak_cum_return - stop_loss
                print(f'{curr_date}\ttrailing_stop:  {trailing_stop}',flush=True)
                
            elif cum_ret <= trailing_stop:
                print(f'{curr_date}\t{ticker}\tCumulative return ({cum_ret}) < stop loss level ({trailing_stop})  SELL!',flush=True)
                period_daily_ret.iloc[row+1:,stock_idx] = 0 # Set values for stock to 0 from next day to end of period df
                break # Exit the loop since we're no longer in the stock
            else:
                print(f'{curr_date}\t(cum_ret) {cum_ret} < {peak_cum_return} (peak_cum_return)\ttrailing_stop:  {trailing_stop}',flush=True)
                pass
        #print(f'Cumulative period return for {ticker}:  {cum_ret}')
    #print(f'period_daily_ret head(3):  {period_daily_ret.head(3)}')
    #print(f'period_daily_ret tail(3):  {period_daily_ret.tail(3)}')
    period_total_returns = period_daily_ret.cumsum().iloc[-1,:] # This gives us the cumulative returns for all stocks
    #print(f'period_total_returns:  {period_total_returns}')
    #curr_ret = period_total_returns.prod() # Only use if you added 1 to return percentages
    curr_ret = period_total_returns.mean()#(axis=0).values[0] # Use this if you are using actual percentage returns
    #return period_daily_ret
    return(curr_ret+1)

# %%
def strategy(parameter_combos):
    #top_n,periods,stop_loss,stop_type,signal_lookbacks = args[0],args[1],args[2],args[3],args[4]
    '''iterate through monthly periods, calculate performance and return as series, along with performance stats'''
    #print(f'Arguments: {top_n},{periods},{stop_loss},{stop_type},{signal_lookbacks}', flush=True)
    returns = [] #List to store all portfolio monthly returns
    monthly_returns = price_data.stock_returns
    signals_df,num_crosses = generate_signals(price_data.benchmark_prices,parameter_combos['benchmark_sma_short'],parameter_combos['benchmark_sma_long'])
    #rolling_returns = [get_rolling_ret(monthly_returns,periods[0]), get_rolling_ret(monthly_returns,periods[1]), get_rolling_ret(monthly_returns,periods[2])]
    rolling_returns = [get_rolling_ret(price_data.stock_returns,parameter_combos['rolling_period_long']), 
                       get_rolling_ret(price_data.stock_returns,parameter_combos['rolling_period_med']), 
                       get_rolling_ret(price_data.stock_returns,parameter_combos['rolling_period_short'])]
    top_n = (parameter_combos['qty_long_period'],parameter_combos['qty_med_period'],parameter_combos['qty_short_period'])
    for date in monthly_returns.index[:-1]: #Loop over all dates in monthly returns df
            ##curr_ret = portfolio_perf(date,rolling_long,rolling_med,rolling_short,stop_loss,stop_type,signals_df)
        if signals_df.loc[date]["uptrend"] == True:
                last_period_end = date # Date for beginning of following month. We should increment this by 1 so we don't overlap with the end of last monthly period
                period_start = last_period_end + DateOffset(days=1) # Increment next period start by one day to avoid overlap with prior period.
                period_end = date+MonthEnd(1)# Date for end of following month
                #print(f'last_period_end:  {last_period_end}\tperiod_start:  {period_start}\tperiod_end:  {period_end}')
                # We should try modifying this to get only tickers with positive return for prior month
                top_tickers = get_top_tickers(date,top_n,rolling_returns)
                if parameter_data.stop_enable != False:
                    if parameter_combos['stop_loss'] != 0:        
                        #period_daily_ret = daily_returns.loc[period_start:period_end,top_tickers] # Daily returns of winning stocks for this period
                        period_daily_ret = price_data.daily_returns.loc[period_start:period_end,top_tickers] # Daily returns of winning stocks for this period
                        portfolio_month_ret = trailing_stop(period_daily_ret, parameter_combos['stop_loss'], parameter_combos['stop_type'])
                        #portfolio_month_ret = fixed_stop(period_daily_ret, stop_loss, stop_type)
                        curr_ret = portfolio_month_ret#.mean(axis=0)
                    else:
                        portfolio_month_ret = monthly_returns.loc[date:, top_tickers][1:2] # Get returns for month following the one passed by slicing the dataframe
                        #portfolio = monthly_returns.loc[date:, get_top_tickers(date,rolling_long, rolling_med, rolling_short)][1:2] # Get returns for month following the one passed by slicing the dataframe
                        #portfolio = monthly_returns.loc[date:, get_top_tickers_reversed(date,rolling_long, rolling_med, rolling_short)][1:2] # Try reversing the order of the rolling period selections.
                        curr_ret = portfolio_month_ret.mean(axis=1).values[0]
                else: # Just return the mean stocks return for next month
                    portfolio_month_ret = monthly_returns.loc[date:, top_tickers][1:2] # Get returns for month following the one passed by slicing the dataframe
                    curr_ret = portfolio_month_ret.mean(axis=1).values[0]
                #print(f'portfolio_month_ret:  {portfolio_month_ret}')
                #print(f'CURR_RET:  {curr_ret}')
                #curr_ret = 0
        else: # Benchmark in downtrend, so assume we go to cash for period
                curr_ret = 1 # return of 1 means no change since we're calculating returns using cumprod.
        returns.append(curr_ret) # append portfolio returns for each date
        #portfolio_cum_returns = pd.Series(returns).cumprod() # Convert returns to Series and set index
        #print(f'Cumulative Portfolio Return: {portfolio_cum_returns[len(portfolio_cum_returns)-1]}')
    return_series = pd.Series(returns, index=monthly_returns.index[1:])-1 #Convert from list to Series with DateTime index from monthly returns df, then subtract 1 to get return %
    tot_ret, cagr, sharpe_ratio, max_dd = calc_stats(return_series, 'Strategy')
    perf_score = round((tot_ret*sharpe_ratio),2) #Create a combined performance measure which we can sort by
    stats = {'top_n':top_n,'SMA_S':parameter_combos['benchmark_sma_short'],'SMA_L':parameter_combos['benchmark_sma_long'],
    'stop':parameter_combos['stop_loss'],'rolling_l':parameter_combos['rolling_period_long'],'rolling_m':parameter_combos['rolling_period_med'],
    'rolling_s':parameter_combos['rolling_period_short'],'tot_ret':tot_ret,'cagr':cagr,'sharpe':sharpe_ratio,'perf_score':perf_score,
    'max_dd':max_dd} #Dictionary to hold current stats
    #all_stats.append(stats)
    #all_stats.append({'top_n':top_n,'SMA_short':signal_lookbacks[0],'SMA_long':signal_lookbacks[1],'stop':stop_loss,'rolling_l':periods[0],'rolling_m':periods[1],'rolling_s':periods[2],'tot_ret':tot_ret,'sharpe':sharpe_ratio,'max_dd':max_dd}) #Append dictionary of portfolio performance statistics to list which we'll use to create dataframe for analysis
    #print(f'Current Stats: {stats}')
    return(stats)


# %%
def calc_stats(returns, name):
    # Calculate Portfolio returns using Quantstats
    #return_series = pd.Series(returns, index=returns.index[1:])-1
    tot_ret = round(qs.stats.comp(returns),2)
    sharpe_ratio = round(qs.stats.sharpe(returns),2)
    max_dd = round(qs.stats.max_drawdown(returns),2)
    cagr = round(qs.stats.cagr(returns),2)
    #print(f'{name} Tot Ret: {tot_ret},  Sharpe Ratio:  {sharpe_ratio},  Max DD:  {max_dd}')
    return(tot_ret, cagr, sharpe_ratio, max_dd)


def task(args):
    top_n,periods,stop_loss,stop_type,signal_lookbacks = args[0],args[1],args[2],args[3],args[4]
    print(f'task args: {args}')
    print(top_n,periods,stop_loss,stop_type,signal_lookbacks)

def create_new_param_vals(current_val, pct):
    # Take in old value and create new min/max pair based on supplied percentage
    #min_max = tuple([int(current_val * (1-pct)),int(current_val * (1+pct))])
    min_max = tuple([ceil(current_val * (1-pct)),ceil(current_val * (1+pct))])
    '''
    if min_max[1] - min_max[0] <= 0:
        min_max = tuple(min_max[0],min_max[1]+1)
    '''
    #print(f'original: {current_val}  new min_max: {min_max}')
    return(min_max)

# %%
def optimize(price_data,parameter_data,performance_data):
    parameter_data.parameter_combos=[] # List to hold all the parameters combinations
    static_parameters = {'qty_long_period':parameter_data.qty_long_period, 'qty_med_period':parameter_data.qty_med_period,'qty_short_period':parameter_data.qty_short_period}
    params_to_optimize = {'benchmark_sma_short':parameter_data.benchmark_sma_short,'benchmark_sma_long':parameter_data.benchmark_sma_long,
                          'rolling_period_long':parameter_data.rolling_period_long,'rolling_period_med':parameter_data.rolling_period_med,
                          'rolling_period_short':parameter_data.rolling_period_short,'stop_loss':parameter_data.stop_loss}
    all_parameters = (static_parameters | params_to_optimize) # Merge both dictionaries to combine all parameters  
    print(f'\n  Initial parameter values for run {parameter_data.run_number}:', flush=True)
    print("\n".join("    {}: {}".format(k, v) for k, v in all_parameters.items()), flush=True)
    print(f'  Parameter ranges for optimization:', flush=True)
    for param_to_optimize, val in params_to_optimize.items(): # Select a parameter to optimize by testing a range of values
        val = create_new_param_vals(val, parameter_data.param_multiplier) # Get min/max values for parameter based on multiplier used to determine range of values
        if val[0] == 0 and param_to_optimize != 'stop_loss': # Parameter value of 0 not appropriate for most parameters, except stop level, so change to 1.
            #print(f'Changing {param_to_optimize} from 0 to 1')
            val = (1,val[1])
        params_to_optimize[param_to_optimize] = val # Update dictionary with new values
        step = ceil((val[1]-val[0])/10) # Calculate step value to be used for parameter value range
        print(f'    {param_to_optimize}  val: {val}  step: {step}')
        #print(f'OPTIMIZE: {param_to_optimize}: {val}   tot values: {val[1]-val[0]}   step: {step}')
        curr_param_values = range(val[0],val[1],step)
        #print(f'Values to test for {param_to_optimize}: {[curr_value for curr_value in curr_param_values]}')
        for curr_value in curr_param_values: #Iterate through all values for parameter to optimize
            current_parameters={} # Dictionary to store current combination of parameters
            for param,val in all_parameters.items(): # Iterate through list of all parameters
                if param == param_to_optimize:
                    current_parameters[param] = curr_value
                    #print(f'CURR: {param}: {current_parameters[param]}')
                else: # We will calculate the mean value for the current parameter
                    current_parameters[param] = int(np.mean(val))
                    #print(f'OTHER: {param}: {val}  Mean val: {current_parameters[param]}')
                current_parameters['stop_type'] = parameter_data.stop_type # Need to add this separately, since it's a bool
            #print(f'current_parameters: {current_parameters}')
            parameter_data.parameter_combos.append((current_parameters))
    print(f'\nTotal parameter combos {len(parameter_data.parameter_combos)} for run {parameter_data.run_number}.', flush=True)
    
    # spawn multiple processes to run several parameter combos at a time
    if parameter_data.test_run == False:
        pool = Pool(processes = parameter_data.processes) # Create Pool, specifying the max number of concurrent processes
        all_stats = (pool.map(strategy, parameter_data.parameter_combos[:])) # Map the parameter combos to the strategy function and assign data returned to all_stats
    else:
        #Run strategy with one parameter set for testing
        all_stats = strategy(parameter_data.parameter_combos[0])

    #print(f'Done processing run {parameter_data.run_number}.', flush=True)
    all_stats_df = pd.DataFrame(all_stats) #Convert list of dictionaries to dataframe
    all_stats_df.sort_values(by=parameter_data.performance_measure, ascending=False,inplace=True) # Sort by specified parameter
    all_stats_df.reset_index(drop=True,inplace=True) # Reset index after sort
    performance_data.all_stats_df = pd.concat([all_stats_df, performance_data.all_stats_df]).drop_duplicates(keep='first') # Add current stats to total stats df
    performance_data.all_stats_df.sort_values(by=parameter_data.performance_measure, ascending=False,inplace=True) # Sort by specified parameter
    performance_data.all_stats_df.reset_index(drop=True,inplace=True) # Reset index after sort
    print(f'Run {parameter_data.run_number} best performance: {all_stats_df.head(1)}', flush=True)
    # If this is our first run, create parameter value ranges around best performing values, set parameter_data.run_number = False, then run optimize recursively.
    parameter_data.run_number +=1
    if parameter_data.run_number <= parameter_data.run_max:
        # Set new parameter values from the last run best
        parameter_data.benchmark_sma_short = all_stats_df.iloc[0]['SMA_S']
        parameter_data.benchmark_sma_long = all_stats_df.iloc[0]['SMA_L']
        parameter_data.rolling_period_long = all_stats_df.iloc[0]['rolling_l']
        parameter_data.rolling_period_med = all_stats_df.iloc[0]['rolling_m']
        parameter_data.rolling_period_short = all_stats_df.iloc[0]['rolling_s']
        parameter_data.stop_loss = all_stats_df.iloc[0]['stop']
        parameter_data.param_multiplier = (parameter_data.param_multiplier)*.8 # Reduce each run to reduce the range of values
        parameter_data.range_divisor = parameter_data.range_divisor-2
        optimize(price_data,parameter_data,performance_data)
    #print(f'Top performance:\n{performance_data.all_stats_df.head(10)}',flush=True)
    return(performance_data.all_stats_df)

# %%
def plot_returns(return_series,benchmark_return_series):
    #portfolio_cum_returns = pd.Series(return_series, index=return_series.index[1:]).cumprod() # Convert returns to Series and set index
    #benchmark_cum_returns = pd.Series(benchmark_return_series, index=return_series.index[1:]).cumprod() # Convert returns to Series and set index based on monthly portfolio returns
    portfolio_cum_returns = (return_series+1).cumprod() # Convert returns to Series and set index
    benchmark_cum_returns = (benchmark_return_series+1).cumprod() # Convert returns to Series and set index based on monthly portfolio returns
    #benchmark_return_series = benchmark_return_series.loc[portfolio_returns.index[0]:portfolio_returns.index[-1]].cumprod() # Trim benchmark to match portfolio returns df length
    #print(portfolio_returns.index)
    #print(benchmark_return_series.index)
    portfolio_returns_w_slippage = pd.Series([i - 0.01 for i in return_series], index=return_series.index[1:]).cumprod() # Convert returns to Series and set index 
    #to match index from return_series starting with second row, then take cumulative product of the series.
    plt.figure(figsize=(25, 10))
    plt.grid()
    plt.plot(portfolio_cum_returns.index, portfolio_cum_returns, label="Portfolio")
    plt.plot(benchmark_cum_returns.index, benchmark_cum_returns, label="Benchmark")
    plt.legend()
    plt.plot()

# %%
def plot_parameters(performance_series, parameter_series):
    plt.figure(figsize=(25, 10))
    plt.grid()
    plt.plot(parameter_series, performance_series, label="Performance")
    #plt.plot(benchmark_cum_returns.index, benchmark_cum_returns, label="Benchmark")
    plt.legend()
    plt.plot()


#plot_parameters(all_stats['stop'], all_stats['sharpe'])


@dataclass
class DataClassParameters:
    # Data class to hold all of the various parameter values required by strategy function
    benchmark_start_date: str = '2010-01-01'
    start_date: str = '2010-01-01'#'2010-01-01'
    end_date: str = '2022-12-23'
    benchmark_ticker: str = '^IXIC' # (NASDAQ) #'SPY' # (S&P500)
    synthetic_benchmark: bool = True#True
    tickers: list = None
    refresh_data: bool = True #True
    all_stats: list = None # List to hold individual dictionaries containing strategy performance for various parameters
    performance_measure: str = 'perf_score' #'tot_ret' # What we'll use to sort our return data
    resample_period: str = 'M' #'W'
    run_number: int = None
    run_max: int = 4 #4
    benchmark_sma_short: tuple = None
    benchmark_sma_long: tuple = None
    rolling_period_long: tuple = None
    rolling_period_med: tuple = None
    rolling_period_short: tuple = None
    stop_loss: int = 25 #5 #15
    stop_type: str = 'avg' #'indiv'
    stop_enable: bool = True#True # Stop function only works with monthly data (for the moment)
    qty_long_period: int = 30 # Number of stocks to hold from longest rolling period
    qty_med_period: int = 20 # Number of stocks to hold from medium rolling period
    qty_short_period: int = 2 # Number of stocks to hold from shortest rolling period
    parameter_combos: list = None
    range_divisor: int = 10 # We divide the range of numbers for a parameter by this to determine how many data points to test
    param_multiplier: float = 1 #.8 #This is used to create range of parameter values for optimization. For example, specifying .8 means expanding value +/- 80%
    processes: int = 16
    test_run: bool = False
    
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
    all_stats_df: pd.core.frame.DataFrame = pd.DataFrame()
    
def get_benchmark_data(returns_df,parameter_data):
    if parameter_data.refresh_data == True:
        benchmark_price_df = pd.DataFrame(process_ticker(parameter_data.benchmark_ticker,parameter_data.benchmark_start_date,parameter_data.end_date)['Adj_Close'])#, name = benchmark) # Grab more data than we need since we'll be losing some to indicator warmup
        benchmark_price_df.to_csv(f'{cached_data}/benchmark_price_df.csv')
        benchmark_daily_returns = benchmark_price_df['Adj_Close'].pct_change()
    else:
        benchmark_price_df = pd.read_csv(f'{cached_data}/benchmark_price_df.csv', index_col=['Date'], parse_dates=True)
        benchmark_daily_returns = benchmark_price_df['Adj_Close'].pct_change()
        
    if parameter_data.synthetic_benchmark == True: # Take mean return of universe as benchmark
        benchmark_returns = returns_df.mean(axis=1) # Instead of using index as benchmark, use product of returns for all stocks in universe
    else: # Use actual benchmark
        #benchmark_monthly_returns = (benchmark_daily_returns + 1)[1:].resample('M').prod() # Need to subtract 1 to get actual returns.   
        benchmark_returns = (benchmark_daily_returns + 1)[1:].resample(parameter_data.resample_period).prod() # Need to subtract 1 to get actual returns.   
        
    #print(f'Benchmark Returns: {benchmark_returns.head(3)}')  
    benchmark_return_series = pd.Series(benchmark_returns, index=returns_df.index[1:])-1 #Convert from list to Series with DateTime index from monthly returns df, then subtract 1 to get return %
    #print(f'Benchmark Series: {benchmark_return_series.head(3)}')  
    tot_ret_b, cagr_b, sharpe_ratio_b, max_dd_b = calc_stats(benchmark_return_series, 'Benchmark')
    print(f'\nBacktest Period: {parameter_data.start_date} - {parameter_data.end_date}')
    print(f'\nBenchmark Tot Ret: {tot_ret_b},  CAGR: {cagr_b},  Sharpe Ratio:  {sharpe_ratio_b},  Max DD:  {max_dd_b}')
    return (benchmark_price_df,benchmark_return_series)

# %%
def main():
    global price_data
    global performance_data
    global parameter_data
    #global monthly_returns
    #global daily_returns
    t1_start = perf_counter()
    parameter_data = DataClassParameters(run_number=1,benchmark_sma_short=(8),benchmark_sma_long=(160),rolling_period_long=(13),
                                          rolling_period_med=(6),rolling_period_short=(4))
    performance_data = DataClassPerformanceData()
    parameter_data.tickers = get_nasdaq_tickers(parameter_data.refresh_data)
    #parameter_data.tickers = ['VFINX','VINEX','VUSTX']
    daily_prices_df,daily_returns,weekly_returns,monthly_returns = get_price_data(parameter_data)
    benchmark_price_df,benchmark_return_series = get_benchmark_data(monthly_returns,parameter_data)
    if parameter_data.resample_period == 'W':
        stock_returns = weekly_returns
    else:
        stock_returns = monthly_returns
    price_data = DataClassPriceData(benchmark_prices=benchmark_price_df,benchmark_returns=benchmark_return_series,stock_prices=daily_prices_df,stock_returns=stock_returns,daily_returns=daily_returns)
    
    all_stats_df = optimize(price_data,parameter_data,performance_data)
    all_stats_df.to_csv(f'{stats_data}/all_stats.csv', index=False)
    
    print(f'Top performance:\n{performance_data.all_stats_df.head(10)}',flush=True)    
    
    '''
    best_returns_df = call strategy with best parameters from all_stats
    best_returns_df.to_csv(f'{cached_data}/best_returns_df.csv', index=True)
    print(f'\nBest Strategy Returns:  ')
    tot_ret, cagr, sharpe_ratio, max_dd = calc_stats(best_returns_df, 'Benchmark')
    print(f'Strategy Tot Ret: {tot_ret},  CAGR: {cagr},  Sharpe Ratio:  {sharpe_ratio},  Max DD:  {max_dd}')
    best_stats = all_stats_df.loc[0,['top_n','SMA_short','SMA_long','stop','rolling_l','rolling_m','rolling_s']]
    print(f'\nBest parameters:\n{all_stats_df.loc[0]}')
    print('\nReport for best return:')
    qs.reports.metrics(best_returns_df, benchmark_return_series, mode='basic') # Compare returns to benchmark
    ##qs.reports.plots(best_returns_df, benchmark_return_series, mode='full') # Compare returns to benchmark
'''    
    t1_stop = perf_counter()
    print("Elapsed time during the whole program in seconds:", round(t1_stop-t1_start, 2))

# %%
main()

# %%
#all_stats = pd.read_csv(f'{stats_data}/all_stats.csv')
#best_returns_df = pd.read_csv(f'{cached_data}/best_returns_df.csv', index_col=['Date'], parse_dates=True)



# %%
#print(f'\nTop 10 parameter combos:\n{all_stats.head(10)}')

# %%
#all_stats[['tot_ret','stop']].plot(kind='scatter')
##all_stats.plot(kind='scatter', x='SMA_short', y='tot_ret')
##all_stats.plot(kind='scatter', x='SMA_long', y='tot_ret')




