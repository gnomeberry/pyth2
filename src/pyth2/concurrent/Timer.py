'''
Created on 2016/03/06

@author: _
'''
import time

from pyth2.concurrent.Concurrent import StepwiseTask, Executor
from datetime import datetime


class Timer(object):
    pass

class ContinuousTimer(StepwiseTask):
    
    def __init__(self, interval, handler, *args, **kwds):
        def _gen():
            while True:
                begin = time.time()
                if self.__enabled:
                    self.__handler(self, *args, **kwds)
                yield True
                await = self.__interval - (time.time() - begin)
                if await > 0:
                    time.sleep(await)
        super(ContinuousTimer, self).__init__(_gen)
        self.__interval = interval
        self.__handler = handler
        self.__enabled = True
    
    @property
    def enabled(self):
        return self.__enabled
    
    @enabled.setter
    def __set_enabled(self, val):
        self.__enabled = bool(val)
    
    @property
    def interval(self):
        return self.__interval
    
    @interval.setter
    def __set_interval(self, value):
        if not hasattr(value, "__float__"):
            raise ValueError("%s is not a float-like object" % value)
        value = float(value)
        if value <= 0:
            raise ValueError("Interval must be more than 0: %f" % value)
        self.__interval = value
    
    @property
    def handler(self):
        return self.__handler
    
    @handler.setter
    def handler(self, handler):
        if not callable(handler):
            raise ValueError("%s is not a callable object" % handler)
        self.__handler = handler

# class PeriodicalTimer(Task):
#     pass

if __name__ == "__main__":
    def printFunc(timer, *arg):
        print time.time(), timer, arg
    ex = Executor(True)
    timer1 = ContinuousTimer(0.1, printFunc, "timer1")
    ex.submit(timer1)
    time.sleep(3)
    