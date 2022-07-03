import datetime
import json
import os
from threading import Thread
from time import sleep
from typing import Optional

import psutil as psutil

MEMORY_SAMPLER: Optional[Thread] = None
START_STOP_FLAG = True


def get_process_memory():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss


def collect_samples(fname: str, delay: float):
    with open(fname, 'w', encoding='utf8') as f:
        while START_STOP_FLAG:
            f.write(json.dumps({'time': datetime.datetime.now().timestamp(), 'memory': get_process_memory()}) + '\n')
            sleep(delay)


def start_collecting_samples(fname: str, delay: float = 1.0):
    global MEMORY_SAMPLER
    MEMORY_SAMPLER = Thread(target=collect_samples, args=(fname, delay))
    MEMORY_SAMPLER.daemon = True
    MEMORY_SAMPLER.start()


def stop_collecting_samples():
    global START_STOP_FLAG
    if MEMORY_SAMPLER is None:
        raise Exception('Memory samples wasn\'t started')
    START_STOP_FLAG = False
    MEMORY_SAMPLER.join()
