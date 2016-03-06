#coding: UTF-8
'''
Created on 2016/02/09

@author: _
'''

import threading

from pyth2.deco.Decorators import ConsProxy


class SynchronizedInvocator(object):
    
    def __init__(self, generatorFunc, condition = None):
        self.__func = generatorFunc
        self.__lock = threading.Condition() if not isinstance(condition, threading.Condition) else condition
    
    @property
    def lock(self):
        return self.__lock
    
    def __call__(self, *args, **kwds):
        try:
            self.__lock.acquire()
            return self.__func(*args, **kwds)
        finally:
            self.__lock.release()
    
    def __enter__(self):
        self.__lock.acquire()
        
    def __exit__(self, exc_type, exc_instance, exc_trace): # @UnusedVariable
        try:
            if exc_instance:
                raise
        finally:
            self.__lock.release()

synchronized = ConsProxy(SynchronizedInvocator) # synchronized decorator
