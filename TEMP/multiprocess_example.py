# SuperFastPython.com
# https://superfastpython.com/multiprocessing-for-loop/
# execute tasks in parallel in a for loop
from time import sleep
from random import random
from multiprocessing import Process
 
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
    # create all tasks
    processes = [Process(target=task, args=(i,)) for i in range(20)]
    # start all processes
    for process in processes:
        process.start()
    # wait for all processes to complete
    for process in processes:
        process.join()
    # report that all tasks are completed
    print('Done', flush=True)