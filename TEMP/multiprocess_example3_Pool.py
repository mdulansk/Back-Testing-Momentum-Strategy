import multiprocessing
from os import getpid
from random import random
import time


def task(arg):
    # generate a random value between 0 and 1
    value = random()
    # block for a fraction of a second
    print(f'Starting {arg}, proc num: {getpid()}', flush=True)
    time.sleep(value)
    # report a message
    print(f'Done {arg}, proc num: {getpid()} generated {value}', flush=True)
    return(value)

def worker(procnum):
    print('I am number %d in process %d' % (procnum, getpid()))
    return getpid()

if __name__ == '__main__':
    start_script_counter_ns = time.perf_counter_ns()
    proc_count = 16 # How many processes to spawn?
    loops = range(15)
    pool = multiprocessing.Pool(processes = proc_count)
    #print(pool.map(worker, loops))
    print(pool.map(task, loops))
    end_script_counter_ns = time.perf_counter_ns()
    script_timer_sec = (end_script_counter_ns - start_script_counter_ns)/1e9
    print(f'Script run time: {round(script_timer_sec,2)} sec', flush=True)
