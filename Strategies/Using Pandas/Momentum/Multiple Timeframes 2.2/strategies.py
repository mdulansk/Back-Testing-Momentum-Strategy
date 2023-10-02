import pandas as pd
import numpy as np
from pandas.tseries.offsets import MonthEnd, BDay, DateOffset

# Import project modules:
import get_parameters, get_data, optimization, strategies, signals, risk_management, analysis


class StrategyMultiMomentum:
    #  Class attributes
    total_runs = 0  # Keep track of total number of combos run.
    all_stats_df = None
    best_parameters = None
    best_return_series = None  # Return series for best performing parameter combination.
    performance_measure = None
    best_performing_instance = None
    
    def __init__(self, index_yearly_members, ticker_selections, price_data, start_date, end_date, 
                 resample_period, rebal_int, qty_long_period, qty_med_period, qty_short_period, 
                 SMA_S, SMA_L, rolling_l, rolling_m, rolling_s, stop, stop_enable, stop_type):
        self.index_yearly_members = index_yearly_members
        self.ticker_selections = ticker_selections # This will hold dict of ticker lists for each period
        self.price_data = price_data
        self.start_date = start_date
        self.end_date = end_date
        self.resample_period = resample_period
        self.rebal_int = rebal_int
        self.qty_long_period = int(qty_long_period)
        self.qty_med_period = int(qty_med_period)
        self.qty_short_period = int(qty_short_period)
        self.SMA_S = int(SMA_S)
        self.SMA_L = int(SMA_L)
        self.rolling_l = int(rolling_l)
        self.rolling_m = int(rolling_m)
        self.rolling_s = int(rolling_s)
        self.stop = stop
        self.stop_enable = stop_enable
        self.stop_type = stop_type
        self.stats = None
        self.performance = None # Set the perormance of this instance when complete.
        self.return_series = None # LOG returns from this strategy instance
        
        StrategyMultiMomentum.total_runs += 1  # Increment class attribute to keep track of total runs.
    
    def strategy(self):
        '''iterate through monthly periods, calculate performance and return as series, along with performance stats'''
        returns = [] #List to store all portfolio monthly returns
        dates = [] # List to hold period dates
        period_returns = self.price_data.stock_returns.loc[self.start_date:self.end_date] # Limit the date range for the strategy
        signals_df,num_crosses = signals.generate_signals(self.price_data.benchmark_prices, self.SMA_S, self.SMA_L)
        #rolling_returns = [get_rolling_ret(period_returns,periods[0]), get_rolling_ret(period_returns,periods[1]), get_rolling_ret(period_returns,periods[2])]
        rolling_returns = [get_data.get_rolling_ret(self.price_data.stock_returns,self.rolling_l), 
                        get_data.get_rolling_ret(self.price_data.stock_returns,self.rolling_m), 
                        get_data.get_rolling_ret(self.price_data.stock_returns,self.rolling_s)]
        top_n = (self.qty_long_period,self.qty_med_period,self.qty_short_period)
        #for date in period_returns.index[:-1]: #Loop over all dates in period returns df
        #for i in range(0, len(period_returns)-(1+self.rebal_int), self.rebal_int): # Not sure why subtract 1 from range end
        for i in range(0, len(period_returns)-(self.rebal_int), self.rebal_int):
            last_period_end_idx = i
            current_period_start_idx = last_period_end_idx + 1
            ### Just changed next line since periods we're overlapping. Make sure change is correct. ###
            current_period_end_idx = last_period_end_idx + self.rebal_int # Changed to use the last_period_end_idx instead of current_period_start_idx for starting index
            last_period_end_date = period_returns.iloc[i].name
            current_period_start_date = last_period_end_date + DateOffset(days=1)
            current_period_end_date = period_returns.iloc[current_period_end_idx].name
            dates.append(current_period_end_date.date())
            #print(f'\nlast_period_end:  {last_period_end_date.date()}\tcurrent_period_start_date:  {current_period_start_date.date()}\tcurrent_period_end_date:  {current_period_end_date.date()}',flush=True)
            ### Try changing last_period_end_date to current_period_start_date for the next line
            if signals_df.loc[last_period_end_date]["uptrend"] == True:
                # Before calling get_top_tickers, we'll set the current_tickers parameter so we can use it to limit which tickers
                # are used for selection based on index members for the specified date.
                current_tickers = (self.index_yearly_members.loc[:,self.index_yearly_members.loc[last_period_end_date] == True].loc[last_period_end_date]).index.values
                ##print(f'current_tickers: {len(current_tickers)}')
                #   print(f'{t} in price_data: {t in price_data.stock_returns}')
                # Get tickers for top performing stocks of LAST period. Our returns will be based on dates for following period
                top_tickers = signals.get_top_tickers(current_tickers,last_period_end_date,top_n,rolling_returns)
                #print(f'{last_period_end_date.date()} Top Tickers: {top_tickers.values}')
                self.ticker_selections[last_period_end_date.date()] = top_tickers.values # Save these instance attribute, then we'll write to csv when we've got our best parameters
                if self.stop_enable != False:
                    #period_daily_ret = daily_returns.loc[period_start:period_end,top_tickers] # Daily returns of winning stocks for this period
                    #period_daily_ret = self.price_data.daily_returns.iloc[current_period_start_idx:current_period_end_idx].loc[:,top_tickers] # Daily returns of winning stocks for this period
                    #period_daily_ret = self.price_data.daily_returns.loc[last_period_end_date:, top_tickers][1:(2+self.rebal_int)] # Get returns for periods following the one passed by slicing the dataframe
                    period_daily_ret = self.price_data.daily_returns.loc[current_period_start_date:current_period_end_date, top_tickers] # Get returns for periods following the one passed by slicing the dataframe
                    #print(f'period_daily_ret Start: {period_daily_ret.index[0]}\tEnd: {period_daily_ret.index[-1]}')
                    portfolio_period_ret = risk_management.trailing_stop(period_daily_ret, self.stop, self.stop_type)
                    #print(f'portfolio_period_ret:\n{(portfolio_period_ret)}')
                    #portfolio_period_ret = fixed_stop(period_daily_ret, stop, stop_type)
                    curr_ret = portfolio_period_ret.mean()#(axis=0)
                    #Note printing holding returns when optimizing will result in a mess of things printed from multiple processes
                    #print(f'Holding LOG returns (stop)\t{(period_daily_ret.index[0]).date()} - {(period_daily_ret.index[-1].date())}:\t{round(curr_ret,4)}\t{[(ticker, round(ret,4)) for ticker, ret in portfolio_period_ret.items()]}', flush=True)
                    #print(f'{period_end}\tcurr_ret: {curr_ret}', flush=True)
                    
                else: # Just return the mean stocks return for next month
                    #portfolio_period_ret = period_returns.loc[last_period_end_date:, top_tickers][1:(2+self.rebal_int)] # Get returns for periods following the one passed by slicing the dataframe
                    #print(f'portfolio_period_ret:\n{(portfolio_period_ret)}')
                    #curr_ret = portfolio_period_ret.mean(axis=1).values.sum() # Make sure this makes sense. We're taking avg of each row, then suming avgs for all periods
                    #print(f'{current_period_end_date.date()}\tHolding LOG returns:\t{round(curr_ret,4)}\t{[(ticker, round(ret,4)) for ticker, ret in portfolio_period_ret.items()]}', flush=True)
                    curr_period_returns = period_returns.loc[last_period_end_date:, top_tickers][1:(1+self.rebal_int)] # Get returns for periods following the one passed by slicing the dataframe
                    portfolio_period_ret = curr_period_returns.cumsum().iloc[-1,:]
                    #print(f'portfolio_period_ret:\n{(portfolio_period_ret)}')
                    curr_ret = portfolio_period_ret.mean()#(axis=1).values.sum() # Make sure this makes sense. We're taking avg of each row, then suming avgs for all periods
                    #print(f'Holding LOG returns\t{curr_period_returns.index[0].date()} - {curr_period_returns.index[-1].date()}:\t{round(curr_ret,4)}\t{[(ticker, round(ret,4)) for ticker, ret in portfolio_period_ret.items()]}', flush=True)

                #print(f'{current_period_end_date.date()}\tportfolio_period_ret:  {portfolio_period_ret}<<')
                #print(f'CURR_RET:  {curr_ret} total')
                #print(f'{date}\tPurchased : {top_tickers.values}\t{round(curr_ret-1,2)} Return for our holding period')
            else: # Benchmark in downtrend, so assume we go to cash for period
                #print(f'Benchmark in downtrend for period ending {date}, nothing to do.',flush=True)
                curr_ret = 0 # return of 0 means no change if we're using cumsum
            returns.append(curr_ret) # append portfolio returns for each date
            portfolio_cum_returns = pd.Series(returns).cumsum() # Convert log returns to Series and set index
            #print(f'{current_period_end_date.date()}\tCURR SIMPLE RET:  {round(np.exp(curr_ret)-1,4)}\t\tCURR LOG RET:  {round(curr_ret,4)}\tCumulative Portfolio LOG Return:  {round(portfolio_cum_returns[len(portfolio_cum_returns)-1],2)}\t{len(returns)} rows')
        # Need to fix the creation of the log_return_series since we can't use the period_returns as the index since it doesn't 
        # match the length of our returns list if we have a rebalance period > 1.
        #log_return_series = pd.Series(returns, index=period_returns.index[1:],name='Adj_Close')#-1 #Convert from list to Series with DateTime index from monthly returns df, then subtract 1 to get return %
        log_return_series = pd.Series(returns, index=pd.to_datetime(dates),name='Adj_Close')#-1 #Convert from list to Series with DateTime index from monthly returns df, then subtract 1 to get return %
        #print(f'log_return_series: {log_return_series.dtypes}\n{log_return_series[:3]}')
        self.return_series = np.exp(log_return_series)-1 # Convert to simple returns and assign to strategy instance attribute
        #print(f'self.return_series max: {self.return_series.max()}')
        #print(f'self.return_series mean: {self.return_series.mean()}')
        tot_ret, cagr, sharpe, max_dd = analysis.calc_stats(self.return_series, 'Strategy')
        perf_score = round((tot_ret*sharpe),2) #Create a combined performance measure which we can sort by
        
        # Let's set these in the strategy instance instead of returning as dict.
        self.stats = {'rebal_int':self.rebal_int,'top_n':top_n,'SMA_S':self.SMA_S,'SMA_L':self.SMA_L, 'stop':self.stop,'rolling_l':self.rolling_l,
                 'rolling_m':self.rolling_m, 'rolling_s':self.rolling_s,'tot_ret':tot_ret,'cagr':cagr,'sharpe':sharpe,
                 'perf_score':perf_score, 'max_dd':max_dd} #Dictionary to hold current stats
        
        self.performance = self.stats[self.performance_measure] # We reference it by performance measure in case it changes.
        #print(f'In instance {self}, performance: {self.performance}')
        #print(f'Current strategy run stats: {stats}')
        #return(self.stats)
        return(self) # Return strategy object instance reference, since the instances are disconnected from the original references when using the multiprocessing pool

def main():
    import os
    print('Imported ', os.path.basename(__file__))


if __name__ == "__main__":
    main()