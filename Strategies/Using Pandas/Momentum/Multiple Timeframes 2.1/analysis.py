import quantstats as qs
import matplotlib.pyplot as plt

# Import project modules:
import get_parameters, get_data, optimization, strategies, signals, risk_management, analysis

def calc_stats(returns, name):
    # Calculate Portfolio returns using Quantstats
    #return_series = pd.Series(returns, index=returns.index[1:])-1
    tot_ret = round(qs.stats.comp(returns),2)
    sharpe = round(qs.stats.sharpe(returns),2)
    max_dd = round(qs.stats.max_drawdown(returns),2)
    cagr = round(qs.stats.cagr(returns),2)
    #print(f'{name} Tot Ret: {tot_ret},  Sharpe Ratio:  {sharpe},  Max DD:  {max_dd}')
    return(tot_ret, cagr, sharpe, max_dd)


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


def plot_parameters(performance_series, parameter_series):
    plt.figure(figsize=(25, 10))
    plt.grid()
    plt.plot(parameter_series, performance_series, label="Performance")
    #plt.plot(benchmark_cum_returns.index, benchmark_cum_returns, label="Benchmark")
    plt.legend()
    plt.plot()
    plt.show()


def main():
    import os
    print('Imported ', os.path.basename(__file__))


if __name__ == "__main__":
    main()