
Using Yahoo Data

In order to backtest locally and used valid market data we need to convert the data to LEAN format or write a custom reader
as explained here: https://www.quantconnect.com/docs/algorithm-reference/importing-custom-data.

To use the yahoo custom data we will need two main things:
    Data loader (yahoo_loader.py): something to grab data from yahoo using yahoo_fin.stock_info and write it to CSV.
    Data reader (yahoo_reader.py): custom type (inherited from BaseData class) to instruct LEAN where to get the data and how to read it.

To download data from Yahoo, create Jupyter Notebook or python script:
    %load_ext autoreload # required to use from Jupyter Notebook
    %autoreload 2 # required to use from Jupyter Notebook
    from yahoo_loader import get_yahoo_data
    get_yahoo_data('SPY', '2021-01-01', '2022-01-01')

Sample CSV data file:
    date,open,high,low,close,adjclose,volume,ticker
    2020-12-29,373.80999755859375,374.0,370.8299865722656,371.4599914550781,366.5736083984375,53680500,SPY

To use YahooData in our algorithm:
    1. import YahooData from yahoo_reader module
    2. Instead of using self.AddEquity, we will use self.AddData and 
    pass our YahooData class as the argument. 

To run our yahoo_data test algorithm which outputs the price for each day:
    conda activate algo     # Activate our "algo" Conda environment where all the required libraries are installed.
    cd ~/Documents/Algo Trading/LEAN    # Change directory to LEAN folder
    lean backtest yahoo_data    # Run backtest using lean
