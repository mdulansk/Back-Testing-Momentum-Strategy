'''
Using Yahoo Data

In order to backtest locally and used valid market data, 
we need to convert the data to LEAN format or write a custom reader, 
as explained here: https://www.quantconnect.com/docs/algorithm-reference/importing-custom-data.
To use the yahoo custom data we will need two main things:

    Data loader (yahoo_loader.py): something to grab data from yahoo and write it to CSV.
    Data reader (yahoo_reader.py): custom type (inherited from BaseData class) to instruct LEAN where to get the data and how to read it.

Then we will add a line to output the values from the CSV and adjust the date to 2021 to see if it works.
To use YahooData in our algorithm:
1. import YahooData from yahoo_reader module
2. Instead of using self.AddEquity, we will use self.AddData and 
pass our YahooData class as the argument. 

'''
#tickers = ['SPY','AAPL']
ticker = 'TSLA'
# Download price data from Yahoo for all tickers
#from yahoo_loader import get_yahoo_data # << Can't get this to import from lean
#get_yahoo_data(tickers, '1998-01-01', '2022-03-11')


from AlgorithmImports import *
from yahoo_reader import YahooData # << You need this in your algo

class Yahoodata(QCAlgorithm):
    def Initialize(self):
        #self.SetStartDate(2013, 10, 7)  # Set Start Date
        self.SetStartDate(2021, 1, 1)  # Set Start Date
        #self.SetEndDate(2013, 10, 11)  # Set End Date
        self.SetEndDate(2021, 12, 31)  # Set End Date
        self.SetCash(100000)  # Set Strategy Cash
        #self.AddEquity("SPY", Resolution.Minute)
        self.symbol = self.AddData(YahooData, ticker, Resolution.Daily).Symbol # << You need this in your algo

    def OnData(self, data):
        """OnData event is the primary entry point for your algorithm. Each new data point will be pumped in here.
            Arguments:
                data: Slice object keyed by symbol containing the stock data
        """
        if not self.Portfolio.Invested:
            #self.SetHoldings("SPY", 1)
            self.SetHoldings(self.symbol, 1)
            self.Debug("Purchased Stock")

        # Keep track of the values
        self.Debug(f"{self.symbol.Value} - {self.Time}: Close={data[self.symbol].Close}")