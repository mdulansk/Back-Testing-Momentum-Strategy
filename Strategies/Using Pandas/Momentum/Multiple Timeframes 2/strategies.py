import pandas as pd
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
    
    def __init__(self, index_yearly_members, ticker_selections, price_data, resample_period,  
                 qty_long_period, qty_med_period, qty_short_period, SMA_S, SMA_L, rolling_l, 
                 rolling_m, rolling_s, stop, stop_enable, stop_type):
        self.index_yearly_members = index_yearly_members
        self.ticker_selections = ticker_selections # This will hold dict of ticker lists for each period
        self.price_data = price_data
        self.resample_period = resample_period
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
        self.return_series = None # Returns from this strategy instance
        
        StrategyMultiMomentum.total_runs += 1  # Increment class attribute to keep track of total runs.
    
    def strategy(self):
        '''iterate through monthly periods, calculate performance and return as series, along with performance stats'''
        returns = [] #List to store all portfolio monthly returns
        period_returns = self.price_data.stock_returns
        signals_df,num_crosses = signals.generate_signals(self.price_data.benchmark_prices, self.SMA_S, self.SMA_L)
        
        #rolling_returns = [get_rolling_ret(period_returns,periods[0]), get_rolling_ret(period_returns,periods[1]), get_rolling_ret(period_returns,periods[2])]
        rolling_returns = [get_data.get_rolling_ret(self.price_data.stock_returns,self.rolling_l), 
                        get_data.get_rolling_ret(self.price_data.stock_returns,self.rolling_m), 
                        get_data.get_rolling_ret(self.price_data.stock_returns,self.rolling_s)]
        top_n = (self.qty_long_period,self.qty_med_period,self.qty_short_period)
        for date in period_returns.index[:-1]: #Loop over all dates in monthly returns df
            #print(f'\nPeriod end: {date}\t{type(date)}')
                ##curr_ret = portfolio_perf(date,rolling_long,rolling_med,rolling_short,stop,stop_type,signals_df)
            if signals_df.loc[date]["uptrend"] == True:
                last_period_end = date
                period_start = last_period_end + DateOffset(days=1) # Increment next period start by one day to avoid overlap with prior period.
                #period_start = last_period_end + BDay(1)#, normalize=True) # Increment next period start by one day to avoid overlap with prior period.
                if self.resample_period == 'M':
                    period_end = date+MonthEnd(1)# Date for end of following month
                elif self.resample_period == 'W':
                    period_end = period_start+BDay(4)#, normalize=True)
                #print(f'last_period_end:  {last_period_end}\tperiod_start:  {period_start}\tperiod_end:  {period_end}',flush=True)
                # We should try modifying this to get only tickers with positive return for prior month
                # Before calling get_top_tickers, we'll set the current_tickers parameter so we can use it to limit which tickers
                # are used for selection based on index members for the specified date.
                #parameter_data.current_tickers = ['AAL','AAPL','ABNB','ADBE','ADI','AMLN','APOL','BMC','WDAY','RIVN']
                current_tickers = (self.index_yearly_members.loc[:,self.index_yearly_members.loc[date] == True].loc[date]).index.values
                ##print(f'current_tickers: {len(current_tickers)}')
                #for t in parameter_data.current_tickers:
                #   print(f'{t} in price_data: {t in price_data.stock_returns}')
                # Get tickers for top performing stocks of LAST period. Our returns will be based on dates for following period
                top_tickers = signals.get_top_tickers(current_tickers,date,top_n,rolling_returns)
                self.ticker_selections[date.date()] = top_tickers.values # Save these instance attribute, then we'll write to csv when we've got our best parameters
                if self.stop_enable != False:
                    if self.stop != 0:        
                        #period_daily_ret = daily_returns.loc[period_start:period_end,top_tickers] # Daily returns of winning stocks for this period
                        period_daily_ret = self.price_data.daily_returns.loc[period_start:period_end,top_tickers] # Daily returns of winning stocks for this period
                        portfolio_month_ret = risk_management.trailing_stop(period_daily_ret, self.stop, self.stop_type)
                        #portfolio_month_ret = fixed_stop(period_daily_ret, stop, stop_type)
                        curr_ret = portfolio_month_ret.mean()#(axis=0)
                        
                        print(f'{period_end}\tHolding returns:\t{round(curr_ret-1,2)}\t{[(ticker, round(ret,2)) for ticker, ret in portfolio_month_ret.items()]}', flush=True)
                        
                        #print(f'{period_end}\tcurr_ret: {curr_ret}', flush=True)
                    else:
                        portfolio_month_ret = period_returns.loc[date:, top_tickers][1:2] # Get returns for month following the one passed by slicing the dataframe
                        #portfolio = period_returns.loc[date:, get_top_tickers(parameter_data,date,rolling_long, rolling_med, rolling_short)][1:2] # Get returns for month following the one passed by slicing the dataframe
                        #portfolio = period_returns.loc[date:, get_top_tickers_reversed(parameter_data,date,rolling_long, rolling_med, rolling_short)][1:2] # Try reversing the order of the rolling period selections.
                        curr_ret = portfolio_month_ret.mean(axis=1).values[0]
                else: # Just return the mean stocks return for next month
                    portfolio_month_ret = period_returns.loc[date:, top_tickers][1:2] # Get returns for month following the one passed by slicing the dataframe
                    curr_ret = portfolio_month_ret.mean(axis=1).values[0]
                #print(f'portfolio_month_ret:  {portfolio_month_ret}')
                #print(f'CURR_RET:  {curr_ret}')
                #curr_ret = 0
                #print(f'{date}\tPurchased : {top_tickers.values}\t{round(curr_ret-1,2)} Return for our holding period')
            else: # Benchmark in downtrend, so assume we go to cash for period
                #print(f'Benchmark in downtrend for period ending {date}, nothing to do.',flush=True)
                curr_ret = 1 # return of 1 means no change since we're calculating returns using cumprod.
            returns.append(curr_ret) # append portfolio returns for each date
            portfolio_cum_returns = pd.Series(returns).cumprod() # Convert returns to Series and set index
            #print(f'Cumulative Portfolio Return: {portfolio_cum_returns[len(portfolio_cum_returns)-1]}')
        self.return_series = pd.Series(returns, index=period_returns.index[1:],name='Adj_Close')-1 #Convert from list to Series with DateTime index from monthly returns df, then subtract 1 to get return %
        #print(f'self.return_series max: {self.return_series.max()}')
        #print(f'self.return_series mean: {self.return_series.mean()}')
        tot_ret, cagr, sharpe, max_dd = analysis.calc_stats(self.return_series, 'Strategy')
        perf_score = round((tot_ret*sharpe),2) #Create a combined performance measure which we can sort by
        
        # Let's set these in the strategy instance instead of returning as dict.
        self.stats = {'top_n':top_n,'SMA_S':self.SMA_S,'SMA_L':self.SMA_L, 'stop':self.stop,'rolling_l':self.rolling_l,
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