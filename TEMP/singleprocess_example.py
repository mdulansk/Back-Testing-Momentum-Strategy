# SuperFastPython.com
# execute tasks sequentially in a for loop
from time import sleep
from random import random
 
# execute a task
def task(arg):
    # generate a random value between 0 and 1
    value = random()
    # block for a fraction of a second
    sleep(value)
    # report a message
    print(f'.done {arg}, generated {value}', flush=True)
 
# protect the entry point
if __name__ == '__main__':
    # run tasks sequentially
    for i in range(20):
        task(i)
    print('Done', flush=True)