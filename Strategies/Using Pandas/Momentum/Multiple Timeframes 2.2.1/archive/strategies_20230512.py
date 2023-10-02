import pandas as pd
from pandas.tseries.offsets import MonthEnd, BDay, DateOffset

# Import project modules:
import get_parameters, get_data, optimization, strategies, signals, risk_management, analysis



#def strategy(parameter_combos):
def strategy(all_dataclasses):
    price_data,parameter_data,performance_data = all_dataclasses
    parameter_combos = parameter_data.parameter_combos
    #print(f'\nparameter_combos: {parameter_combos}')
    #top_n,periods,stop,stop_type,signal_lookbacks = args[0],args[1],args[2],args[3],args[4]
    '''iterate through monthly periods, calculate performance and return as series, along with performance stats'''
    #print(f'Arguments: {top_n},{periods},{stop},{stop_type},{signal_lookbacks}', flush=True)
    returns = [] #List to store all portfolio monthly returns
    #print(f'Parameter Combos:\n{parameter_combos}')
    period_returns = price_data.stock_returns
    signals_df,num_crosses = signals.generate_signals(price_data.benchmark_prices,parameter_combos['SMA_S'],parameter_combos['SMA_L'])
    
    #rolling_returns = [get_rolling_ret(period_returns,periods[0]), get_rolling_ret(period_returns,periods[1]), get_rolling_ret(period_returns,periods[2])]
    rolling_returns = [get_data.get_rolling_ret(price_data.stock_returns,parameter_combos['rolling_l']), 
                       get_data.get_rolling_ret(price_data.stock_returns,parameter_combos['rolling_m']), 
                       get_data.get_rolling_ret(price_data.stock_returns,parameter_combos['rolling_s'])]
    top_n = (parameter_combos['qty_long_period'],parameter_combos['qty_med_period'],parameter_combos['qty_short_period'])
    for date in period_returns.index[:-1]: #Loop over all dates in monthly returns df
        #print(f'\nPeriod end: {date}\t{type(date)}')
            ##curr_ret = portfolio_perf(date,rolling_long,rolling_med,rolling_short,stop,stop_type,signals_df)
        if signals_df.loc[date]["uptrend"] == True:
            last_period_end = date # Date for beginning of following month. We should increment this by 1 so we don't overlap with the end of last monthly period
            period_start = last_period_end + DateOffset(days=1) # Increment next period start by one day to avoid overlap with prior period.
            #period_start = last_period_end + BDay(1)#, normalize=True) # Increment next period start by one day to avoid overlap with prior period.
            if parameter_data.resample_period == 'M':
                period_end = date+MonthEnd(1)# Date for end of following month
            elif parameter_data.resample_period == 'W':
                period_end = period_start+BDay(4)#, normalize=True)
            #print(f'last_period_end:  {last_period_end}\tperiod_start:  {period_start}\tperiod_end:  {period_end}',flush=True)
            # We should try modifying this to get only tickers with positive return for prior month
            # Before calling get_top_tickers, we'll set the current_tickers parameter so we can use it to limit which tickers are used for selection
            #parameter_data.current_tickers = ['AAL','AAPL','ABNB','ADBE','ADI','AMLN','APOL','BMC','WDAY','RIVN']
            #print(f'Updating parameter_data.current_tickers: {len(parameter_data.current_tickers)}')
            parameter_data.current_tickers = (parameter_data.index_yearly_members.loc[:,parameter_data.index_yearly_members.loc[date] == True].loc[date]).index.values
            #print(f'parameter_data.current_tickers: {len(parameter_data.current_tickers)}')
            #for t in parameter_data.current_tickers:
             #   print(f'{t} in price_data: {t in price_data.stock_returns}')

            #curr_tickers = (index_yearly_members.loc[:,index_yearly_members.loc[end_date] == True].loc[end_date]).index.values
            top_tickers = signals.get_top_tickers(parameter_data,date,top_n,rolling_returns)
            parameter_data.ticker_selections[date.date()] = top_tickers.values # Save these to dictionary, then we'll write to csv when we've got our best parameters
            #print(f'Top tickers for {date}: {top_tickers}')
            if parameter_data.stop_enable != False:
                if parameter_combos['stop'] != 0:        
                    #period_daily_ret = daily_returns.loc[period_start:period_end,top_tickers] # Daily returns of winning stocks for this period
                    period_daily_ret = price_data.daily_returns.loc[period_start:period_end,top_tickers] # Daily returns of winning stocks for this period
                    portfolio_month_ret = risk_management.trailing_stop(period_daily_ret, parameter_combos['stop'], parameter_combos['stop_type'])
                    #portfolio_month_ret = fixed_stop(period_daily_ret, stop, stop_type)
                    curr_ret = portfolio_month_ret#.mean(axis=0)
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
        else: # Benchmark in downtrend, so assume we go to cash for period
            #print(f'Benchmark in downtrend for period ending {date}, nothing to do.',flush=True)
            curr_ret = 1 # return of 1 means no change since we're calculating returns using cumprod.
        returns.append(curr_ret) # append portfolio returns for each date
        portfolio_cum_returns = pd.Series(returns).cumprod() # Convert returns to Series and set index
        #print(f'Cumulative Portfolio Return: {portfolio_cum_returns[len(portfolio_cum_returns)-1]}')
    return_series = pd.Series(returns, index=period_returns.index[1:],name='Adj_Close')-1 #Convert from list to Series with DateTime index from monthly returns df, then subtract 1 to get return %
    #print(f'return_series max: {return_series.max()}')
    #print(f'return_series mean: {return_series.mean()}')
    #performance_data.return_series = return_series
    tot_ret, cagr, sharpe, max_dd = analysis.calc_stats(return_series, 'Strategy')
    perf_score = round((tot_ret*sharpe),2) #Create a combined performance measure which we can sort by
    stats = {'top_n':top_n,'SMA_S':parameter_combos['SMA_S'],'SMA_L':parameter_combos['SMA_L'],
    'stop':parameter_combos['stop'],'rolling_l':parameter_combos['rolling_l'],'rolling_m':parameter_combos['rolling_m'],
    'rolling_s':parameter_combos['rolling_s'],'tot_ret':tot_ret,'cagr':cagr,'sharpe':sharpe,'perf_score':perf_score,
    'max_dd':max_dd} #Dictionary to hold current stats
    #all_stats.append(stats)
    #all_stats.append({'top_n':top_n,'SMA_short':signal_lookbacks[0],'SMA_long':signal_lookbacks[1],'stop':stop,'rolling_l':periods[0],'rolling_m':periods[1],'rolling_s':periods[2],'tot_ret':tot_ret,'sharpe':sharpe,'max_dd':max_dd}) #Append dictionary of portfolio performance statistics to list which we'll use to create dataframe for analysis
    #print(f'Current Stats: {stats}')
    return(stats)


def main():
    import os
    print('Imported ', os.path.basename(__file__))


if __name__ == "__main__":
    main()