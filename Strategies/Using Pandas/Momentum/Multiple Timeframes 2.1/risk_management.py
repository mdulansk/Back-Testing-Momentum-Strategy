import pandas as pd

# Import project modules:
import get_parameters, get_data, optimization, strategies, signals, risk_management, analysis

def fixed_stop(period_daily_ret, stop, stop_type='avg'):
    ''' This function just iterates through a dataframe of stocks and determines if the price over the period falls to the stop level.  
    If the return for any portfolio stocks fall below the stop loss level, the remaining return values for that stock are
    set to 0, which would be our return on the stock if we sold it on the next day.'''
    # IMPORTANT: you need to subtract 1 from entire returns dataframe instead of just when calculating trailing stop 
    # return since we sometimes take original return
    stop = -1*(stop)
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
            if cum_ret <= stop:
                #print(f'{curr_date}\t{ticker}\tCumulative return ({cum_ret}) < stop loss level ({stop})  SELL!')
                period_daily_ret.iloc[row+1:,stock_idx] = 0 # Set values for stock to 0 from next day to end of period df
                break # Exit the loop since we're no longer in the stock
            else:
                #print(f'{curr_date}\t(cum_ret) {cum_ret} < {peak_cum_return} (peak_cum_return)\ttrailing_stop:  {trailing_stop}')
                pass
    period_total_returns = period_daily_ret.cumsum().iloc[-1,:] # This gives us the total cumulative returns for all stocks.
    #print(f'period_total_returns:  {period_total_returns}')
    #curr_ret = period_total_returns.prod() # Only use if you added 1 to return percentages
    curr_ret = period_total_returns.mean()#(axis=0).values[0] # Use this if you are using actual percentage returns
    #return period_daily_ret
    return(curr_ret+1) # Add 1 to entire return so we take prod of return series


def trailing_stop(period_daily_ret, stop, stop_type='indiv'):
    ''' This function just calculates a trailing stop on all the stock returns in the daily return df that is passed to it.
    If the return for any portfolio stocks fall below the stop loss level, the remaining return values for that stock are
    set to 0, which would be our return on the stock if we sold it on the next day.'''
    # Improvement: add trailing loss based on mean of all stocks.
    #print(f'period_daily_ret.head(10):\n{period_daily_ret.head(10)}')
    ##print(f'{(period_daily_ret.index[0]).date()} - {(period_daily_ret.index[-1]).date()}\t{period_daily_ret.columns.values}, Stop Loss:  {stop}')
    # Iterate through the dates in winning_returns_df
    #for stock in period_daily_ret.columns:
    # IMPORTANT: you need to subtract 1 from entire returns dataframe instead of just when calculating trailing stop 
    # return since we sometimes take original return
    stop = round((stop*.01),2) #Convert back to percentage since it was expressed as integer to be used with range function
    ##period_daily_ret = period_daily_ret-1 # Subtract 1 to get simple returns so we can take sum
    if stop_type == 'avg':
        period_daily_ret = pd.DataFrame(period_daily_ret.mean(axis=1),columns=['avg_ret'])
    #print(f'Applying {stop*10}% stop loss for {pd.to_datetime(period_daily_ret.iloc[0].name).date()} - {pd.to_datetime(period_daily_ret.iloc[-1].name).date()}',flush=True)
    #print(f'Applying stop {stop} loss for {period_daily_ret.values[0]} - {period_daily_ret.values[-1]}',flush=True)
    for stock_idx in range(len(period_daily_ret.columns)): #Iterate through each stock
        ticker = period_daily_ret.columns[stock_idx]
        cum_ret = 0 # To keep track of cumulative return for a stock
        peak_cum_return = 0 # This is to keep track of highest return for each stock
        trailing_stop = -1*(stop)
        #print(f'\n{stock_idx}\t{ticker}\tInitial stop:  {trailing_stop}',flush=True)
        for row in range(len(period_daily_ret)-0): # go through daily return for entire rolling lookback period
            curr_date = period_daily_ret.iloc[row].name
            period_ret = period_daily_ret.iloc[row,stock_idx]
            #print(f'{row} {curr_date}\tPeriod return:  {period_ret}',flush=True)
            cum_ret += period_ret
            #print(f'{curr_date}\tcum_ret:  {cum_ret}',flush=True)
            if cum_ret > peak_cum_return:
                #print(f'{curr_date}\t Cum_ret ({cum_ret}) > {peak_cum_return} (peak_cum_return)\ttrailing_stop:  {peak_cum_return - stop}',flush=True)
                peak_cum_return = cum_ret
                #print(f'{curr_date}\tPeak Cum. return:  {peak_cum_return}',flush=True)
                trailing_stop = peak_cum_return - stop
                #print(f'{curr_date}\ttrailing_stop:  {trailing_stop}',flush=True)
                
            elif cum_ret <= trailing_stop:
                #print(f'{curr_date}\t{ticker}\tCumulative return ({cum_ret}) < stop loss level ({trailing_stop})  SELL!',flush=True)
                period_daily_ret.iloc[row+1:,stock_idx] = 0 # Set values for stock to 0 from next day to end of period df
                break # Exit the loop since we're no longer in the stock
            else:
                #print(f'{curr_date}\t(cum_ret) {cum_ret} < {peak_cum_return} (peak_cum_return)\ttrailing_stop:  {trailing_stop}',flush=True)
                pass
        #print(f'Cumulative period return for {ticker}:  {cum_ret}')
    #print(f'period_daily_ret head(3):  {period_daily_ret.head(3)}')
    #print(f'period_daily_ret tail(3):  {period_daily_ret.tail(3)}')
    period_total_returns = period_daily_ret.cumsum().iloc[-1,:] # This gives us the cumulative returns (last row) for all stocks
    #print(f'{period_total_returns.name}\tperiod_total_returns:  {period_total_returns}')
    #curr_ret = period_total_returns.prod() # Only use if you added 1 to return percentages
    curr_ret = period_total_returns#.mean()#(axis=0).values[0] # Use this if you are using actual percentage returns
    #return period_daily_ret
    #return(curr_ret+1) # Add 1 to get gross? return
    return(curr_ret) # Add 1 to get gross? return



def main():
    import os
    print('Imported ', os.path.basename(__file__))


if __name__ == "__main__":
    main()