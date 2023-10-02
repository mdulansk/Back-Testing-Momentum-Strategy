import datetime
import copy

def get_todays_date():
    return datetime.datetime.now()

def get_date_from_string(date_str):
    return datetime.datetime.strptime(date_str,'%Y-%m-%d')

def get_date_from_object(obj):
    return datetime.datetime.strptime(obj.start_date,'%Y-%m-%d')

def change_dataclass_settings(dc):
    print(f'\nUpdating dataclass passed to function.')
    dc.resample_period = 'D'
    
def copy_dataclass_settings(dc):
    dc2 = copy.copy(dc)
    dc2.resample_period = 'D'
    print(f'\nUpdated copy of dataclass passed to function:  {dc2}')
    