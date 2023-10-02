import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import quantstats as qs

script_path = os.path.dirname(__file__)
cached_data = script_path+'/'+'cached_data'

def plot_returns(return_series,benchmark_return_series):
    #portfolio_cum_returns = pd.Series(return_series, index=return_series.index[1:]).cumprod() # Convert returns to Series and set index
    #benchmark_cum_returns = pd.Series(benchmark_return_series, index=return_series.index[1:]).cumprod() # Convert returns to Series and set index based on monthly portfolio returns
    portfolio_cum_returns = (return_series+1).cumprod() # Convert returns to Series and set index
    benchmark_cum_returns = (benchmark_return_series+1).cumprod() # Convert returns to Series and set index based on monthly portfolio returns
    #benchmark_return_series = benchmark_return_series.loc[portfolio_returns.index[0]:portfolio_returns.index[-1]].cumprod() # Trim benchmark to match portfolio returns df length
    #print(portfolio_returns.index)
    #print(benchmark_return_series.index)
    #portfolio_returns_w_slippage = pd.Series([i - 0.01 for i in return_series], index=return_series.index[1:]).cumprod() # Convert returns to Series and set index 
    #to match index from return_series starting with second row, then take cumulative product of the series.
    plt.figure(figsize=(25, 10))
    plt.grid()
    plt.plot(portfolio_cum_returns.index, portfolio_cum_returns, label="Portfolio")
    plt.plot(benchmark_cum_returns.index, benchmark_cum_returns, label="Benchmark")
    plt.legend()
    plt.plot()
    plt.show()

def calc_stats(returns, name):
    # Calculate Portfolio returns using Quantstats
    #return_series = pd.Series(returns, index=returns.index[1:])-1
    tot_ret = round(qs.stats.comp(returns),2)
    sharpe = round(qs.stats.sharpe(returns),2)
    max_dd = round(qs.stats.max_drawdown(returns),2)
    cagr = round(qs.stats.cagr(returns),2)
    #print(f'{name} Tot Ret: {tot_ret},  Sharpe Ratio:  {sharpe},  Max DD:  {max_dd}')
    return(tot_ret, cagr, sharpe, max_dd)



benchmark_return_series = pd.read_csv(f'{cached_data}/benchmark_return_series.csv', index_col=['Date'], parse_dates=True, usecols=['Date','Adj_Close'])
best_returns_series = pd.read_csv(f'{cached_data}/best_returns_series.csv', index_col=['Date'], parse_dates=True, usecols=['Date','Adj_Close'])

print((f'Benchmark dates: {len(benchmark_return_series.index)}\t{benchmark_return_series.index[0]} - {benchmark_return_series.index[-1]}'))
print((f'Best returns dates: {len(best_returns_series.index)}\t{best_returns_series.index[0]} - {best_returns_series.index[-1]}'))

print(f'return_series\t\tmin: {round(best_returns_series.values.min(),2)}\tmax: {round(best_returns_series.values.max(),2)}\tmean: {round(best_returns_series.values.mean(),2)}')
print(f'benchmark_series\tmin: {round(benchmark_return_series.values.min(),2)}\tmax: {round(benchmark_return_series.values.max(),2)}\tmean: {round(benchmark_return_series.values.mean(),2)}')
print(f'best_returns_series:\n {best_returns_series}')
print(f'benchmark_return_series:\n {benchmark_return_series}')

tot_ret, cagr, sharpe, max_dd = calc_stats(best_returns_series, 'Strategy')
print(f'\nStrategy Tot Ret: {(tot_ret)[0]},  CAGR: {cagr[0]},  Sharpe Ratio:  {sharpe[0]},  Max DD:  {max_dd[0]}')
#qs.reports.metrics(best_returns_series, benchmark_return_series, mode='basic') # Compare returns to benchmark
#qs.reports.metrics(best_returns_series, benchmark_return_series, mode='full') # Compare returns to benchmark
#plot_returns(best_returns_series,benchmark_return_series)

