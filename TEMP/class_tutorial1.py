# From "Python OOP Tutorial 1: Classes and Instances" on Youtube

from dataclasses import dataclass
import class_tutorial_module1
import pandas as pd

cached_data = '/test'

class Employee:
    #  Class attributes
    num_of_emps = 0
    raise_amount = 1.04
    
    def __init__(self, first, last, salary, start_date):
        self.first = first  # Instance attribute
        self.last = last
        self.salary = salary
        self.email = first+'.'+last+'@company.com'
        self.start_date = start_date
        Employee.num_of_emps += 1  # If we reference the class attribute using class name, it will update the class attribute instead 
        # of just for an instance of this class.

    def fullname(self):
        return '{} {}'.format(self.first, self.last)

    def emp_details(self):
        return(f'{self.first} {self.last}\n{self.email}\n{self.start_date}\n${self.salary}')
    
    # Instance method
    def apply_raise(self):
        self.salary = int(self.salary * self.raise_amount)  # If we reference the class attribute using
        # the instance reference, self, we can override it if desired. This will also allow any subclass to override value as well.

emp_1 = Employee('Corey','Schafer',50000, '2000-01-01')
emp_2 = Employee('Carrie','Schafer',60000, '2005-01-01')
emp_3 = Employee('John','Smith',70000, '2015-01-01')
print(f'\nNumber of employees: {Employee.num_of_emps}')

emp_list = [emp_1, emp_2, emp_3]
emp_dict = dict([(emp, emp.salary) for emp in emp_list])
#emp_dict = {'one':100,'two':200,'three':300}
print(f'emp_dict: {emp_dict}')

#print(f'emp_dict.items(): {emp_dict.items()}')
emp_items_df = (pd.DataFrame(list(emp_dict.items()), columns=['obj','salary'])) # Create dataframe from list of tuples from dictionary
print(f'\nemp_items_df: {emp_items_df}')
emp_items_df.sort_values(by='salary', ascending=False, inplace=True) # Sort the df by salary descending
print(f'\nemp_items_df: {emp_items_df}')

# Use object's str method
print(f'\n{emp_1.emp_details()}\n')

# Reference instance attributes directly. Instance methods can be accessed directly or by referencing the class and passing the instance reference.
print(Employee.fullname(emp_1), emp_1.email)

print(f"Today's date: {class_tutorial_module1.get_todays_date()}")
print(f"Start date from obj: {class_tutorial_module1.get_date_from_string(emp_1.start_date)}")
print(f"Start date from obj2: {class_tutorial_module1.get_date_from_object(emp_2)}")

Employee.raise_amount = 1.05  # Update the class attribute
emp_1.raise_amount = 1.07  # Update the instance attribute. Doesn't change the class attribute.

print(f'Employee.raise_amount: {Employee.raise_amount}')
print(f'emp_1.raise_amount: {emp_1.raise_amount}')  # Inherited from class, unless set directly, which overrides class attribute.
print(f'emp_2.raise_amount: {emp_2.raise_amount}')  # Inherited from class
print(f'Employee 1 salary:  {emp_1.salary}')
emp_1.apply_raise()
print(f'Employee 1 salary (after raise):  {emp_1.salary}')

#  Let's play around with a dataclass now

@dataclass
class DataClassSettings:
    pass  # We'll move some of the non-optimization settings from DataClassParameters here.
    resample_period: str = 'M' #'M' #'W'
    processes: int = 15#16
    cached_data = cached_data # Set Dataclass attribute to value of global variable

@dataclass
class DataClassParams:
    pass  # We'll move some of the non-optimization settings from DataClassParameters here.
    ma_s_length: int = 20
    ma_l_length: int = 50
    all_params = {'ma_s_length':ma_s_length,'ma_l_length':ma_l_length}

settings1 = DataClassSettings()  # Don't set any parameters when initializing
settings2 = DataClassSettings(resample_period='W', processes=8)  # Initialize with parameter values
params = DataClassParams()
print(f'\nsettings1:  {settings1}')
print(f'settings2:  {settings2}')
print(f'params:  {params}')
print(f'params.all_params: {params.all_params} before changing value to 70')
params.ma_l_length = 70
# Note: even though the dataclass attribute is updated, the dictionary reference to it shows the old value!!!
print(f'params.all_params: {params.all_params} after changing value to 70')
print(f'params:  {params}')

class_tutorial_module1.copy_dataclass_settings(settings1)
print(f'settings1 after passing to function which copies it:  {settings1}')

class_tutorial_module1.change_dataclass_settings(settings1)
print(f'settings1 after passing to function which updates it:  {settings1}')
print('It looks like the dataclass is passed by reference to the function and gets updated by the function.')

print(f'\nsettings1:  {settings1.cached_data}')

all_dataclasses = (settings1, settings2, params)
print(f'all_dataclasses:  {all_dataclasses}')
a,b,c = all_dataclasses
print(f'a: {a}')
print(f'b: {b}')
print(f'c: {c}')

settings_list = ['processes']
#print(f'settings2.__dict__:{settings2.__dict__}')
#print({k: settings2.__dict__[k] for k in settings2.__dict__.keys()})
print({k: settings2.__dict__[k] for k in settings2.__dict__.keys() if k in settings_list})