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
        print(f'Adding {df.shape[0]} rows from {file}')
        df_list.append(df)
        row_count += df.shape[0]
print(f'Total rows imported:  {row_count}')
concatenated_df = pd.concat(df_list, axis=0, ignore_index=True).drop_duplicates(keep='first') # concatenate all dataframes into a single dataframe
concatenated_df.sort_values(by='perf_score', ascending=False,inplace=True) # Sort by specified parameter
concatenated_df.reset_index(drop=True,inplace=True) # Reset index after sort
top_100_df = concatenated_df[:100]
top_100_df.to_csv(f'{script_path}/top_100_df.csv', index=False)
print(f'concatenated_df rows: {concatenated_df.shape[0]}')

# Display interactive df with styling using Streamlit dataframe method
st.write("Disply interactive df with styling using st.dataframe:")
st.dataframe(top_100_df.style.highlight_max(axis=0))
