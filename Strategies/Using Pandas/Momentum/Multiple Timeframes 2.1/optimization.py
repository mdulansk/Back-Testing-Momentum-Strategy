import pandas as pd
from dataclasses import dataclass
from math import ceil, floor
from multiprocessing import Process, Pool
import concurrent.futures

# Import project modules:
import get_parameters, get_data, optimization, strategies, signals, risk_management, analysis


def task(args):
    top_n,periods,stop,stop_type,signal_lookbacks = args[0],args[1],args[2],args[3],args[4]
    print(f'task args: {args}')
    print(top_n,periods,stop,stop_type,signal_lookbacks)

def create_new_param_vals(current_val, pct):
    # Take in old value and create new min/max pair based on supplied percentage
    min_max = tuple([ceil(current_val * (1-pct)),ceil(current_val * (1+pct))])
    if min_max[0] <= 0: # Set minimum value
        min_max = (1,min_max[1])
    if min_max[1] - min_max[0] <= 0: # If max value is less than min
        min_max = (min_max[0],min_max[1]+1)
    #print(f'original: {current_val}  new min_max: {min_max}', flush=True)
    return(min_max)

def set_best_parameters(parameter_data,performance_data):
    # Set new parameter values from the last run best
    parameter_data.SMA_L = performance_data.all_stats_df.iloc[0]['SMA_L']
    parameter_data.SMA_S = performance_data.all_stats_df.iloc[0]['SMA_S']
    parameter_data.rolling_l = performance_data.all_stats_df.iloc[0]['rolling_l']
    parameter_data.rolling_m = performance_data.all_stats_df.iloc[0]['rolling_m']
    parameter_data.rolling_s = performance_data.all_stats_df.iloc[0]['rolling_s']
    parameter_data.stop = performance_data.all_stats_df.iloc[0]['stop']
    print(f'Setting best parameter values')
    
def run_backtest(strategy_obj):
    stats = strategy_obj.strategy()
    #return stats
    return strategy_obj


def optimize(price_data,parameter_data,performance_data):
    #all_dataclasses = [price_data,parameter_data,performance_data]  # Reference the dataclasses in one tuple
    parameter_combos=[] # List to hold all the parameters combinations
    strategy_objs = []  # List to store strategy object references for this run
    # Make a copy of the dictionaries which hold our initial parameter values, since we don't want to update these until this optimization sequence is complete
    all_parameters = {key: parameter_data.__dict__[key] for key in parameter_data.__dict__.keys() if key in parameter_data.all_parameters}
    params_to_optimize = {key: parameter_data.__dict__[key] for key in parameter_data.__dict__.keys() if key in parameter_data.params_to_optimize}
    
    print(f'\n  Initial parameter values for run {parameter_data.run_number}:', flush=True)
    print("\n".join("    {}: {}".format(k, v) for k, v in all_parameters.items()), flush=True)
    if parameter_data.optimize_params == False:
        print(f'\nBacktesting without optimizing parameters.', flush=True)
        parameter_combos.append(all_parameters)
    else:
        print(f'\nOptimizing parameters for backtests.', flush=True)
        for param_to_optimize, val in params_to_optimize.items(): # Select a parameter to optimize by testing a range of values
            #print(f'call create_new_param_vals for {param_to_optimize}, current val: {val}')
            val = create_new_param_vals(val, parameter_data.param_multiplier) # Get min/max values for parameter based on multiplier used to determine range of values
            params_to_optimize[param_to_optimize] = val # Update dictionary with new values
            step = ceil((val[1]-val[0])/parameter_data.range_divisor) # Calculate step value to be used for parameter value range
            #print(f'    {param_to_optimize}  min/max: {val}  step: {step}')
            #print(f'OPTIMIZE: {param_to_optimize}: {val}   poss values: {val[1]-val[0]}   step: {step}')
            curr_param_values = range(val[0],val[1],step)
            print(f'Values to test for {param_to_optimize}: {[curr_value for curr_value in curr_param_values]}')
            for curr_value in curr_param_values: #Iterate through all values for parameter to optimize
                current_parameters={} # Dictionary to store current combination of parameters
                for param,val in all_parameters.items(): # Iterate through list of all parameters
                    if param == param_to_optimize:
                        current_parameters[param] = curr_value
                        #print(f'CURR: {param}: {current_parameters[param]}')
                    else: # We will calculate the mean value for the current parameter
                        #current_parameters[param] = int(np.mean(val))
                        current_parameters[param] = val
                        #print(f'OTHER: {param}: {val}')
                #print(f'current_parameters: {current_parameters}')
                parameter_combos.append((current_parameters))

    # Optional: At this point we can get rid of unwanted parameter combinations, such as rolling period lengths where longer period < shorter period.
    # The easiest way to do this is convert parameter combos to DF, then filter to get only rows where rollin_l > rolling_m > rolling_s.
    parameter_combos_df = (pd.DataFrame(parameter_combos, columns=parameter_combos[0].keys())) # Create dataframe from list of dictionaries
    if parameter_data.allow_any_param_combos == False:
        parameter_combos_df = parameter_combos_df.loc[(parameter_combos_df['SMA_L'] >= parameter_combos_df['SMA_S'])
        & (parameter_combos_df['qty_long_period'] >= parameter_combos_df['qty_med_period']) & (parameter_combos_df['qty_med_period'] >= parameter_combos_df['qty_short_period'])
        & (parameter_combos_df['rolling_l'] >= parameter_combos_df['rolling_m']) & (parameter_combos_df['rolling_m'] >= parameter_combos_df['rolling_s'])]
        #print(f'\nFiltered parameter_combos_df:\n{parameter_combos_df}')
                
    print(f'Total parameter combos {len(parameter_combos_df)} for run {parameter_data.run_number}.\n', flush=True)
    print(f'{" ".join(parameter_combos_df.columns.values)}')
    strategies.StrategyMultiMomentum.performance_measure = parameter_data.performance_measure
    #  Create Strategy objects for each combination of parameters to pass to the strategy method for testing.
    #for parameter_combo in parameter_combos:
    for index, parameter_combo in parameter_combos_df.iterrows(): # Using df instead of dict
        print(f'Test combo: {[param for param in parameter_combo]}')
        strategy_obj = strategies.StrategyMultiMomentum(
            index_yearly_members=parameter_data.index_yearly_members,
            ticker_selections=parameter_data.ticker_selections,
            price_data=price_data,
            resample_period=parameter_data.resample_period,
            qty_long_period=parameter_combo['qty_long_period'],
            qty_med_period=parameter_combo['qty_med_period'],
            qty_short_period=parameter_combo['qty_short_period'],
            SMA_L=parameter_combo['SMA_L'],
            SMA_S=parameter_combo['SMA_S'],
            rolling_l=parameter_combo['rolling_l'],
            rolling_m=parameter_combo['rolling_m'],
            rolling_s=parameter_combo['rolling_s'],
            stop=parameter_combo['stop'],
            stop_enable=parameter_data.stop_enable,
            stop_type=parameter_combo['stop_type'])
        strategy_objs.append(strategy_obj)
    
    all_stats = []
    # Use multiprocess pool to spawn multiple concurrent processes.
    
    #### Run strategy with multiprocess ####
    with Pool() as pool:
        strategy_objs = (pool.map(run_backtest, strategy_objs)) # Map the parameter combos to the strategy function and assign data returned to all_stats
    
    #### Run strategy without multiprocess ####
    #strategy_objs = list(map(run_backtest, strategy_objs)) # Map the parameter combos to the strategy function - returns list
    
    all_stats = [strategy_obj.stats for strategy_obj in strategy_objs]
    #print(f'\nall_stats: {all_stats}')

    
    #print(f'Done processing run {parameter_data.run_number}.', flush=True)
    all_stats_df = pd.DataFrame(all_stats) #Convert list of dictionaries to dataframe
    all_stats_df.sort_values(by=parameter_data.performance_measure, ascending=False,inplace=True) # Sort by specified parameter
    all_stats_df.reset_index(drop=True,inplace=True) # Reset index after sort
    performance_data.all_stats_df = pd.concat([all_stats_df, performance_data.all_stats_df]).drop_duplicates(keep='first') # Add current stats to total stats df
    performance_data.all_stats_df.sort_values(by=parameter_data.performance_measure, ascending=False,inplace=True) # Sort by specified parameter
    performance_data.all_stats_df.reset_index(drop=True,inplace=True) # Reset index after sort
    performance_data.strategy_objs.extend(strategy_objs) # Append list of strategy objects from this run to comprehensive list stored in performance_data class
    
    print(f'Run {parameter_data.run_number} best performance:\n {all_stats_df.head(1)}', flush=True)
    parameter_data.run_number +=1
    # If optimization is enabled, set parameter defaults to best values from last optimization run, then run optimize recursively.
    if (parameter_data.run_number <= parameter_data.run_max) and (parameter_data.optimize_params) == True:
        # Set new parameter values from the last run best
        #parameter_data.SMA_S = all_stats_df.iloc[0]['SMA_S']
        #parameter_data.SMA_L = all_stats_df.iloc[0]['SMA_L']
        #parameter_data.rolling_l = all_stats_df.iloc[0]['rolling_l']
        #parameter_data.rolling_m = all_stats_df.iloc[0]['rolling_m']
        #parameter_data.rolling_s = all_stats_df.iloc[0]['rolling_s']
        #parameter_data.stop = all_stats_df.iloc[0]['stop']
        set_best_parameters(parameter_data,performance_data)
        parameter_data.param_multiplier = (parameter_data.param_multiplier)*.7 # Reduce each run to reduce the range of values
        #parameter_data.range_divisor = max(1,ceil(parameter_data.range_divisor - 2)) #Decrease divisor each loop with a minimum value of 1.
        parameter_data.range_divisor = max(1,ceil(parameter_data.range_divisor + 2)) #Increase divisor each loop to reduce the calculated step size
        optimize(price_data,parameter_data,performance_data)
    #print(f'Top performance:\n{performance_data.all_stats_df.head(10)}',flush=True)

    # Find best performance from all strategy instances, then reference in class attribute
    # Instead of having strategy method return stats, have it return returns series for analysis
    strategy_obj_dict = dict([(strategy_obj, strategy_obj.performance) for strategy_obj in performance_data.strategy_objs]) # Create a dictionary of strategy objects and assoc. perf
    #print(f'strategy_obj_dict: {strategy_obj_dict}')
    strategy_obj_df = (pd.DataFrame(list(strategy_obj_dict.items()), columns=['strategy_obj','performance'])) # Create dataframe from list of tuples from dictionary
    strategy_obj_df.sort_values(by='performance', ascending=False, inplace=True) # Sort the df of strategy objects by performance measure in descending order
    best_strategy_obj = strategy_obj_df.iloc[0]["strategy_obj"]
    #print(f'\nstrategy_obj_df.head(5): {strategy_obj_df.head(5)}')
    print(f'\nBest strategy_obj: {best_strategy_obj} {best_strategy_obj.performance}')
    performance_data.best_return_series = best_strategy_obj.return_series
    performance_data.best_return_tickers = best_strategy_obj.ticker_selections
    # StrategyMultiMomentum.best_return_series = strategy_obj.strategy()

    #return(performance_data.all_stats_df)
    return(performance_data.all_stats_df)

def main():
    import os
    print('Imported ', os.path.basename(__file__))

if __name__ == "__main__":
    main()