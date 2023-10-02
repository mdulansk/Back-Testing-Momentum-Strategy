# SuperFastPython.com
# https://superfastpython.com/multiprocessing-for-loop/
# https://stackoverflow.com/questions/10415028/how-to-get-the-return-value-of-a-function-passed-to-multiprocessing-process
# execute tasks in parallel in a for loop

import time
from random import random
from multiprocessing import Process, Manager
 
# execute a task
def task(arg,return_dict):
    # generate a random value between 0 and 1
    value = random()
    # block for a fraction of a second
    time.sleep(value)
    # report a message
    print(f'.done {arg}, generated {value}', flush=True)
    return_dict[arg] = value
 
# protect the entry point
if __name__ == '__main__':
    start_script_counter_ns = time.perf_counter_ns()
    manager = Manager()
    return_dict = manager.dict()
    # create all tasks
    processes = [Process(target=task, args=(i,return_dict)) for i in range(15)]
    # start all processes
    for process in processes:
        process.start()
    # wait for all processes to complete
    for process in processes:
        process.join()
    # report that all tasks are completed
    print('Done', flush=True)
    print(return_dict.values())
    end_script_counter_ns = time.perf_counter_ns()
    script_timer_sec = (end_script_counter_ns - start_script_counter_ns)/1e9
    print(f'Script run time: {round(script_timer_sec,2)} sec', flush=True)
