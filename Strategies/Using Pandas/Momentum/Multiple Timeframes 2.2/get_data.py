import os
import sys
import pandas as pd
import numpy as np

# Import project modules:
import get_parameters, get_data, optimization, strategies, signals, risk_management, analysis

HOME_DIR = os.path.expanduser('~/')
sys.path.append(f"{HOME_DIR}/Documents/Algo/Stock Price DB/")
#from StockPriceData import process_ticker
import StockPriceData

def get_nasdaq_tickers(parameter_data):
    if parameter_data.refresh_tickers == True:
        try:
            tickers_df = pd.read_html("https://en.wikipedia.org/wiki/Nasdaq-100")[4]
            #tickers_df.to_csv(f'{parameter_data.cached_data}/nasdaq100_tickers.csv', index=False)
            tickers_df.to_csv(parameter_data.ticker_csv, index=False)
        except:
            print(f"Can't connect to https://en.wikipedia.org/wiki/Nasdaq-100, reading from nasdaq100_tickers.csv")
            #tickers_df = pd.read_csv(f'{parameter_data.cached_data}/nasdaq100_tickers.csv')
            tickers_df = pd.read_csv(parameter_data.ticker_csv)
    else:
        #tickers_df = pd.read_csv(f'{parameter_data.cached_data}/nasdaq100_tickers.csv')
        tickers_df = pd.read_csv(parameter_data.ticker_csv)
    tickers = tickers_df['Ticker'].to_list()
    #tickers.remove('GOOGL') # This is essentially a duplicate of GOOG
    print(f'Loaded {len(tickers)} tickers.')
    return(tickers)


def get_user_tickers(parameter_data):
    if parameter_data.refresh_tickers == True:
        #pd.Series(tickers,name='Ticker').to_csv(f'{parameter_data.cached_data}/tickers.csv', index=False)#, header=False) #Convert to pandas series to write out to csv
        pd.Series(tickers,name='Ticker').to_csv(parameter_data.ticker_csv, index=False)#, header=False) #Convert to pandas series to write out to csv
    else:
        #tickers_df = pd.read_csv(f'{parameter_data.cached_data}/tickers.csv')
        tickers_df = pd.read_csv(parameter_data.ticker_csv)
        tickers = tickers_df['Ticker'].to_list()
    print(f'Loaded {len(tickers)} tickers.')
    return(tickers)


def get_benchmark_data(returns_df,parameter_data):
    if parameter_data.refresh_data == True:
        benchmark_price_df = pd.DataFrame(StockPriceData.process_ticker(parameter_data.benchmark_ticker,parameter_data.data_start_date,parameter_data.data_end_date)['Adj_Close'])#, name = benchmark) # Grab more data than we need since we'll be losing some to indicator warmup
        #benchmark_price_df.to_csv(f'{parameter_data.cached_data}/benchmark_price_df.csv')
        benchmark_price_df.to_csv(parameter_data.benchmark_price_csv)
        #benchmark_daily_returns = benchmark_price_df['Adj_Close'].pct_change().fillna(0) # Simple returns
        benchmark_daily_returns = (np.log(benchmark_price_df['Adj_Close']).diff()).fillna(0) # Log returns
    else:
        #benchmark_price_df = pd.read_csv(f'{parameter_data.cached_data}/benchmark_price_df.csv', index_col=['Date'], parse_dates=True)
        benchmark_price_df = pd.read_csv(parameter_data.benchmark_price_csv, index_col=['Date'], parse_dates=True)
        #benchmark_daily_returns = benchmark_price_df['Adj_Close'].pct_change().fillna(0) # Simple returns
        benchmark_daily_returns = (np.log(benchmark_price_df['Adj_Close']).diff()).fillna(0) # Log returns
        
    if parameter_data.synthetic_benchmark == True: # Take mean return of universe as benchmark
        benchmark_returns = returns_df.mean(axis=1) # Instead of using index as benchmark, use mean of returns for all stocks in universe
        benchmark_price_df.to_csv(parameter_data.benchmark_price_csv)
    else: # Use actual benchmark
        #benchmark_returns = (benchmark_daily_returns + 1)[1:].resample(parameter_data.resample_period).prod().fillna(0) # Need to subtract 1 to get actual returns.   
        # Why do we resample the actual benchmark in the next line?
        benchmark_returns = (benchmark_daily_returns)[1:].resample(parameter_data.resample_period).sum().fillna(0) # Resample using sum function since we're using log returns
        
    #print(f'Benchmark Returns: {benchmark_returns.head(3)}')  
    #benchmark_return_series = pd.Series(benchmark_returns, index=returns_df.index[1:])-1 #Convert from list to Series with DateTime index from monthly returns df, then subtract 1 to get return %
    benchmark_return_series = pd.Series(benchmark_returns, index=returns_df.index[1:]) #Convert from list to Series with DateTime index from monthly returns df, then subtract 1 to get return %
    #print(f'Benchmark Series: {benchmark_return_series.head(3)}')  
    tot_ret_b, cagr_b, sharpe_b, max_dd_b = analysis.calc_stats(benchmark_return_series, 'Benchmark')
    print(f'\nBacktest Period: {parameter_data.start_date} - {parameter_data.end_date}')
    print(f'\nBenchmark Tot Ret: {tot_ret_b},  CAGR: {cagr_b},  Sharpe Ratio:  {sharpe_b},  Max DD:  {max_dd_b}')
    return (benchmark_price_df,benchmark_return_series)

def get_price_data(parameter_data):
    if parameter_data.refresh_data == True:
        tickers_and_prices = {}
        for ticker in parameter_data.tickers[:]:
            tickers_and_prices[ticker] = StockPriceData.process_ticker(ticker,parameter_data.data_start_date,parameter_data.data_end_date)['Adj_Close']
            # This next line concatenates the series to the dataframe, but doesn't include the series name as the column name.
            #daily_prices = pd.concat([price_data, prices],names=[ticker])
        all_daily_prices_df = pd.concat(tickers_and_prices, axis=1)
        #all_daily_prices_df.to_csv(f'{parameter_data.cached_data}/all_daily_prices.csv')
        #all_daily_prices_df.fillna(0).to_csv(parameter_data.daily_price_csv)
        all_daily_prices_df.to_csv(parameter_data.daily_price_csv)
        
    else:
        #all_daily_prices_df = pd.read_csv(f'{parameter_data.cached_data}/all_daily_prices.csv', index_col=['Date'], parse_dates=True)
        all_daily_prices_df = pd.read_csv(parameter_data.daily_price_csv, index_col=['Date'], parse_dates=True)
    print(f'Loaded prices for {all_daily_prices_df.shape[1]} tickers.')
    # Clean up price df by removing stocks which don't have data for entire period, then calculate daily an monthly returns
    #daily_prices_df = all_daily_prices_df.fillna(0).copy() #.dropna(axis=1) # Drop any stocks that are missing values? <-NO
    daily_prices_df = all_daily_prices_df.copy() #.dropna(axis=1) # Drop any stocks that are missing values? <-NO
    
    #We can't just drop tickers with missing data, since that will skew our results!
    #symbols_missing_start_data = (daily_prices_df.loc[:, daily_prices_df.iloc[0].isnull()]).columns
    #daily_prices_df.drop(columns=symbols_missing_start_data,inplace=True)
    
    # Add column for cash option for when there are no positive returns 
    daily_prices_df['CASH'] = 0.0 # We set to 0 to simulate 0% return as alternative to other investments when they're negative
    #daily_returns = (daily_prices_df.pct_change()+1)[1:] # Adding 1 allows us to take the product of returns. Can't use cumsum though. This messes things up for stocks that go to zero!
    #daily_returns = (daily_prices_df.pct_change())[1:] # Adding 1 allows us to take the product of returns. Can't use cumsum though. This messes things up for stocks that go to zero!
    daily_returns = (np.log(daily_prices_df).diff()).fillna(0)
    weekly_returns = daily_returns.resample('W').sum().fillna(0)
    monthly_returns = daily_returns.resample('M').sum().fillna(0)
    daily_returns.to_csv(f'{parameter_data.cached_data}/nasdaq_daily_log_returns.csv')
    weekly_returns.to_csv(f'{parameter_data.cached_data}/nasdaq_weekly_log_returns.csv')
    monthly_returns.to_csv(f'{parameter_data.cached_data}/nasdaq_monthly_log_returns.csv')
    #benchmark_monthly_returns = monthly_returns.mean(axis=1) # Instead of using index as benchmark, use product of returns for all stocks in universe
    return(daily_prices_df,daily_returns,weekly_returns,monthly_returns)


def get_rolling_ret(df, lookback):
    # Calculates individual rolling cumulative return for all stocks in supplied df over specified lookback period
    #return df.rolling(lookback).apply(np.prod)
    return df.rolling(lookback).apply(np.sum)


# Not sure why I put this stuff in here since we won't run this file directly.
def main():
    import os
    print('Imported ', os.path.basename(__file__))


if __name__ == "__main__":
    main()