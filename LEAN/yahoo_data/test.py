

import os


# Displaying the script path
print(__file__)
  
# Displaying the parent directory of the script
print(os.path.dirname(__file__))

from yahoo_loader import get_yahoo_data
get_yahoo_data(['IBM'], '1998-01-01', '2022-04-29')