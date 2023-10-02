import streamlit as st
import pandas as pd
import numpy as np
import os
import sys

HOME_DIR = os.path.expanduser('~/')
sys.path.append(f"{HOME_DIR}/Documents/Algo/Stock Price DB/")
from StockPriceData import process_ticker
script_path = os.path.dirname(__file__)
cached_data = script_path+'/'+'cached_data'
stats_data = script_path+'/'+'stats'

#tickers_to_download = pd.concat([tickers_with_data,high_volume_tickers]).drop_duplicates(keep='first')
row_count = 0
df_list = []
all_files = os.listdir(stats_data)
for file in all_files:
    if file.endswith(".csv"):
        # Prints only text file present in My Folder
        df = pd.read_csv(f'{stats_data}/{file}', index_col=None, header=0) # read each csv file into a separate dataframe
        df['stats_file'] = file
        if "rebalance_interval" in df.columns: # stats file contains old field name, update and drop
            print(f'{file} contains rebalance_interval field, updating.')
            df['rebal_int'] = df['rebalance_interval']
            df.drop(columns=["rebalance_interval"], inplace=True)
        if not "rebal_int" in df.columns:
            print(f'{file} doesn\'t contain rebal_int, setting to 1.')
            df['rebal_int'] = 1 # Set to 1 for earlier results before interval option existed
        print(f'Adding {df.shape[0]} rows from {file}')
        df_list.append(df)
        row_count += df.shape[0]
print(f'Total rows imported:  {row_count}')
concatenated_df = pd.concat(df_list, axis=0, ignore_index=True).drop_duplicates(keep='first') # concatenate all dataframes into a single dataframe
concatenated_df.sort_values(by='perf_score', ascending=False,inplace=True) # Sort by specified parameter
concatenated_df.reset_index(drop=True,inplace=True) # Reset index after sort
all_stats_df = concatenated_df[:5000]
all_stats_df.to_csv(f'{script_path}/all_stats_df.csv', index=False)
print(f'Rows after removing duplicates: {concatenated_df.shape[0]}')

# Display interactive df with styling using Streamlit dataframe method
st.write("Disply interactive df with styling using st.dataframe:")
st.dataframe(all_stats_df.style.highlight_max(axis=0))
