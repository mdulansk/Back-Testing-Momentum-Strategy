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

def get_tested_parameters(parameter_data):
    # Get parameter combos from all stats files
    #past_stats_df = concat_stats_files() # This function returns stats from previous backtests
    if parameter_data.all_time_stats.shape[0] >= 1:
        param_columns = [column for column in parameter_data.all_time_stats.columns if column in parameter_data.all_parameters] # Get list of parameters we're testing
        parameter_data.tested_parameter_combos = parameter_data.all_time_stats.loc[:,param_columns] # We only want the parameter values
    else:
        parameter_data.tested_parameter_combos = pd.DataFrame(columns = parameter_data.all_parameters)
    #print(f'tested_parameter_combos:\n{parameter_data.tested_parameter_combos}')
    
def param_combos_already_tested(parameter_data, param_dict):
    # Verify if proposed parameter combinonations have already been tested. Return True if tested.
    #print(f'\nparam_dict: {param_dict}')
    query_keys_values = [] # List to store proposed parameter combos to create query
    combo_dict = {} # Create a dict of combo, value pairs to add to parameter_data.tested_parameter_combos
    params = parameter_data.tested_parameter_combos.columns.to_list()
    if parameter_data.all_time_stats.shape[0] < 1:
        print(f'parameter_data.all_time_stats.shape[0]: {parameter_data.all_time_stats.shape[0]}')
        return(False) # Nothing to check against
    #print(f'tested_parameter_combos:\n{parameter_data.tested_parameter_combos}')
    for param in params:
        if param in param_dict: # Param exists in stats and params dict
            query_keys_values.append(f'{param}=={param_dict[param]}')
            combo_dict[param] = param_dict[param]
    query_str = ((' and ').join(query_keys_values)) # Create query string from our proposed parameter combos to query \
    # parameter_data.tested_parameter_combos to see if we've tested before
    #print(f'\nquery_str: {query_str}')
    matched_rows = parameter_data.tested_parameter_combos.query(query_str)
    #print(f'matched_rows: {len(matched_rows)}')
    if len(matched_rows) == 0: # If we don't find proposed combo in parameter_data.tested_parameter_combos, we'll add so we don't test again during this run
        #print(f'combo_dict: {combo_dict}')
        print(f'Param combo not used before, adding to combos to test:  {combo_dict}')
        combos_df = pd.DataFrame(data=combo_dict, index=[0])
        parameter_data.tested_parameter_combos = pd.concat([parameter_data.tested_parameter_combos, combos_df], ignore_index=True).drop_duplicates(keep='first')
        return(False)
    else:
        print(f'Param combo already tested:  {combo_dict}')
        return(True)
def filter_parameters(parameter_data, parameter_combos_df):
    # Filter out invalid parameter combinations
    print(f'parameter_combos_df.head()\n:{parameter_combos_df.head()}')
    if parameter_data.allow_any_param_combos == False:
        #print(f'\nUnfiltered parameter_combos_df:\n{parameter_combos_df}')
        parameter_combos_df = parameter_combos_df.loc[(parameter_combos_df['SMA_L'] >= parameter_combos_df['SMA_S'])
        & (parameter_combos_df['qty_long'] >= parameter_combos_df['qty_med']) & (parameter_combos_df['qty_med'] >= parameter_combos_df['qty_short'])
        & (parameter_combos_df['rolling_l'] >= parameter_combos_df['rolling_m']) & (parameter_combos_df['rolling_m'] >= parameter_combos_df['rolling_s'])]
        print(f'\nFiltered parameter_combos_df:\n{parameter_combos_df}')
    # Filter out previously tested parameter combinations
    print(f'parameter_data.tested_parameter_combos.head()\n:{parameter_data.tested_parameter_combos.head()}')
    
    return(parameter_combos_df)

def set_best_parameters(parameter_data,performance_data):
    # Set new parameter values from the last run best
    print(f'***   Setting best parameter values   ***')
    parameter_data.SMA_L = performance_data.all_stats_df['SMA_L'].iloc[0]
    parameter_data.SMA_S = performance_data.all_stats_df['SMA_S'].iloc[0]
    parameter_data.rolling_l = performance_data.all_stats_df['rolling_l'].iloc[0]
    parameter_data.rolling_m = performance_data.all_stats_df['rolling_m'].iloc[0]
    parameter_data.rolling_s = performance_data.all_stats_df['rolling_s'].iloc[0]
    parameter_data.stop = performance_data.all_stats_df['stop'].iloc[0]
    parameter_data.rebal_int = performance_data.all_stats_df['rebal_int'].iloc[0]
    print(f'Setting best parameter values - rebal_int: {parameter_data.rebal_int}')
        
def run_backtest(strategy_obj):
    print(f'Details for {strategy_obj}: {strategy_obj.get_details()}')
    stats = strategy_obj.strategy()
    return strategy_obj

def optimize(price_data,parameter_data,performance_data):
    parameter_combos=[] # List to hold all the parameters combinations
    strategy_objs = []  # List to store strategy object references for this run
    # Make a copy of the dictionaries which hold our initial parameter values, since we don't want to update these until this optimization sequence is complete
    if parameter_data.stop_enable == False:
        parameter_data.stop = 0 # Set to 0 to match what actually gets saved in all_stats csv file for later comparison.
    all_parameters = {key: parameter_data.__dict__[key] for key in parameter_data.__dict__.keys() if key in parameter_data.all_parameters}
    params_to_optimize = {key: parameter_data.__dict__[key] for key in parameter_data.__dict__.keys() if key in parameter_data.params_to_optimize}
    print(f'all_parameters: {all_parameters}')
    print(f'\n  Initial parameter values for run {parameter_data.run_number}:', flush=True)
    print("\n".join("    {}: {}".format(k, v) for k, v in all_parameters.items()), flush=True)

    if len(params_to_optimize.items()) < 1: parameter_data.optimize_params = False
    if parameter_data.optimize_params == False:
        print(f'\nBacktesting without optimizing parameters.', flush=True)
        parameter_combos.append(all_parameters)
    else:
        print(f'\nOptimizing parameters for backtests.', flush=True)
        print(f'tested_parameter_combos:\n{parameter_data.tested_parameter_combos}')
        for param_to_optimize, val in params_to_optimize.items(): # Select a parameter to optimize by testing a range of values
            print(f'call create_new_param_vals for {param_to_optimize}, current val: {val}')
            val = create_new_param_vals(val, parameter_data.param_multiplier) # Get min/max values for parameter based on multiplier used to determine range of values
            params_to_optimize[param_to_optimize] = val # Update dictionary with new values
            step = ceil((val[1]-val[0])/parameter_data.range_divisor) # Calculate step value to be used for parameter value range
            print(f'    {param_to_optimize}  min/max: {val}  step: {step}')
            print(f'OPTIMIZE: {param_to_optimize}: {val}   poss values: {val[1]-val[0]}   step: {step}')
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
                print(f'current_parameters: {current_parameters}')
                # The next 2 lines are for the old way to check if parameters combo has been tested before adding to dict.
                # Changing this to add all combos to dict, converting to df, then filtering later to remove tested or invalid combos.
                #if param_combos_already_tested(parameter_data, current_parameters) == False:
                #    parameter_combos.append((current_parameters))
                parameter_combos.append((current_parameters))

    parameter_combos_df = (pd.DataFrame(parameter_combos, columns=parameter_combos[0].keys())) # Create dataframe from list of dictionaries
    #print(f'parameter_combos_df.head()\n:{parameter_combos_df.head()}')
    parameter_combos_df = filter_parameters(parameter_data, parameter_combos_df)
    print(f'\nTotal parameter combos for run {parameter_data.run_number}:  {len(parameter_combos_df)}\n', flush=True)
    print(f'{" ".join(parameter_combos_df.columns.values)}')
    strategies.StrategyMultiMomentum.performance_measure = parameter_data.performance_measure
    #  Create Strategy objects for each combination of parameters to pass to the strategy method for testing.
    for index, parameter_combo in parameter_combos_df.iterrows(): # Using df instead of dict
        #print(f'Test combo: {[param for param in parameter_combo]}')
        strategy_obj = strategies.StrategyMultiMomentum(
            index_yearly_members=parameter_data.index_yearly_members,
            ticker_selections=parameter_data.ticker_selections,
            price_data=price_data,
            start_date = parameter_data.start_date,
            end_date = parameter_data.end_date,
            resample_period=parameter_data.resample_period,
            rebal_int = parameter_combo['rebal_int'],
            qty_long=parameter_combo['qty_long'],
            qty_med=parameter_combo['qty_med'],
            qty_short=parameter_combo['qty_short'],
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
    #print(f'Strategy objects: {len(strategy_objs)}')
    #### Run strategy with multiprocess ####
    with Pool() as pool:
        strategy_objs = (pool.map(run_backtest, strategy_objs)) # Map the parameter combos to the strategy function and assign data returned to all_stats
    
    #### Run strategy without multiprocess ####
    #strategy_objs = list(map(run_backtest, strategy_objs)) # Map the parameter combos to the strategy function - returns list
    
    all_stats = [strategy_obj.stats for strategy_obj in strategy_objs]
    #print(f'\nall_stats ({len(all_stats)})')

    # Check for length of all_stats_df to see if we have anything else to test, if not return from function
    if len(all_stats) == 0:
        print(f'!!!  No test results, returning {len(performance_data.all_stats_df)}')
        return(performance_data.all_stats_df)
    #print(f'Done processing run {parameter_data.run_number}.', flush=True)
    all_stats_df = pd.DataFrame(all_stats) #Convert list of dictionaries to dataframe
    all_stats_df.sort_values(by=parameter_data.performance_measure, ascending=False,inplace=True) # Sort by specified parameter
    all_stats_df.reset_index(drop=True,inplace=True) # Reset index after sort
    performance_data.all_stats_df = pd.concat([all_stats_df, performance_data.all_stats_df]).drop_duplicates(keep='first') # Add current stats to total stats df
    performance_data.all_stats_df.sort_values(by=parameter_data.performance_measure, ascending=False,inplace=True) # Sort by specified parameter
    performance_data.all_stats_df.reset_index(drop=True,inplace=True) # Reset index after sort
    print(f'>>> all_stats_df after running strategy {parameter_data.run_number} time(s):\n{all_stats_df}')
    print(f'>>> performance_data.all_stats_df after running strategy {parameter_data.run_number} time(s):\n{performance_data.all_stats_df}')
    # The problem with integers being converted to floats happens after this step.
    performance_data.strategy_objs.extend(strategy_objs) # Append list of strategy objects from this run to comprehensive list stored in performance_data class
    print(f'>>> performance_data.all_stats_df after extending strategy_objs {parameter_data.run_number} time(s):\n{performance_data.all_stats_df}')
    print(f'\nRun {parameter_data.run_number} best performance:\n {all_stats_df.head(10)}', flush=True)
    print(f'\nRun {parameter_data.run_number} best performance_data:\n {performance_data.all_stats_df.head(10)}', flush=True)
    parameter_data.run_number +=1
    
    # If optimization is enabled, set parameter defaults to best values from last optimization run, then run optimize recursively.
    if (parameter_data.run_number <= parameter_data.run_max) and (parameter_data.optimize_params) == True:
        print(f'performance_data just before calling set_best_parameters:\n{performance_data.all_stats_df.head()}')
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
    return(performance_data.all_stats_df)

def main():
    import os
    print('Imported ', os.path.basename(__file__))

if __name__ == "__main__":
    main()