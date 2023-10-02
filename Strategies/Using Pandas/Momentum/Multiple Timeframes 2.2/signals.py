import numpy as np
import pandas as pd

# Import project modules:
import get_parameters, get_data, optimization, strategies, signals, risk_management, analysis

def get_top_tickers(current_tickers,date,top_n,rolling_returns):
    #ticks = ['AAL','AAPL','ADBE','ADI','ADP','ADSK']
    #print(f'rolling_returns[0]: {rolling_returns[0].loc["2022-10-31":"2022-12-31",ticks]}')
    #rolling_long, rolling_med, rolling_short = rolling_returns[0],rolling_returns[1],rolling_returns[2]
    
    rolling_long = rolling_returns[0].loc[:,current_tickers] # All rows, but only current Nasdaq tickers.
    rolling_med = rolling_returns[1].loc[:,current_tickers] # All rows, but only current Nasdaq tickers.
    rolling_short = rolling_returns[2].loc[:,current_tickers] # All rows, but only current Nasdaq tickers.

    top_coarse = rolling_long.loc[date].nlargest(top_n[0]).index # Get the top performing n stocks from longest rolling average returns
    top_med = rolling_med.loc[date, top_coarse].nlargest(top_n[1]).index # Get the top n performing stocks from medium length rolling average returns
    top_fine = rolling_short.loc[date, top_med].nlargest(top_n[2]).index # Get the top n performing stocks from shortest rolling average returns
    top_tickers_and_returns = rolling_short.loc[date, top_med].nlargest(top_n[2]) # Returns a series
    #print(f'{date}\tget_top_tickers top_tickers_and_returns:\t{top_tickers_and_returns.values.mean()}')
    #Note printing holding returns when optimizing will result in a mess of things printed from multiple processes
    #print(f'\n{date}\tTop ticker returns:\t{round(top_tickers_and_returns.values.mean(),2)}\t{[(ticker, round(ret,2)) for ticker, ret in top_tickers_and_returns.iteritems()]}', flush=True)
    #top_10 = rolling_short.loc[date, top_30].nlargest(10).ge(1).index # From the top 30 ,get the top 10 from the 3 month rolling average returns
    #top_10 = rolling_short.loc[date, top_30].nlargest(10) # From the top 30 ,get the top 10 from the 3 month rolling average returns
    #top_10_above_zero = top_10[top_10.ge(1)] ## Try getting just tickers with a positive return for the current period.
    #print(f'top_10_above_zero: ({len(top_10_above_zero)}): {top_10_above_zero}')
    ##Example: curr = all_mtl_ret_lb.iloc[row][all_mtl_ret_lb.iloc[row].ge(0)] # Only stocks with prices >= 0
    #print(f'top_10 > 1 ({len(top_10)}): {rolling_short.loc[date, top_10]}')
    return top_fine


def get_top_tickers_reversed(current_tickers,date,rolling_long, rolling_med, rolling_short):
    top_50 = rolling_short.loc[date].nlargest(50).index # Get the top 50 from the 12 month rolling average returns
    top_30 = rolling_med.loc[date, top_50].nlargest(30).index # From the top 50 ,get the top 30 from the 6 month rolling average returns
    top_10 = rolling_long.loc[date, top_30].nlargest(10).index # From the top 30 ,get the top 10 from the 3 month rolling average returns
    return top_10


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
    signals_df['bullishness'] = (signals_df['SMA_short'] / signals_df['SMA_long'])-1 # How much higher is short ma over long ma?
    #signals_df[signals_df['cross'] == 1]
    #signals_df['2001-11-30':'2001-12-04']
    #signals_df["cross"][signals_df["cross"]==1]
    crosses = np.where((signals_df['cross_up'] == True) | (signals_df['cross_down'] == True) ,1,0) # Returns numpy array of 0's and 1's
    num_crosses = len(crosses[crosses==1])
    #print(f'num_crosses: {num_crosses}')
    idx = pd.date_range(signals_df.index[0], signals_df.index[-1])
    signals_df = signals_df.reindex(idx, method='ffill') # We re-index and forward-fill missing values so that our regime df has values for all possible end-of-month dates, even non-business days
    return(signals_df, num_crosses)


def main():
    import os
    print('Imported ', os.path.basename(__file__))


if __name__ == "__main__":
    main()