#coding: UTF-8
'''
Created on 2016/02/09

@author: _
'''
from threading import Lock

from pyth2.deco.Decorators import ConsProxy


class SynchronizedInvocator(object):
    __lockObject = Lock()
    
    def setDecoratorParams(self, func, lockObject = None):
        self.__func = func
        self.__lockObject = Lock() if not lockObject else lockObject
    
    def __call__(self, *args, **kwds):
        try:
            self.__lockObject.acquire()
            return self.__func(*args, **kwds)
        finally:
            self.__lockObject.release()
    
    def __enter__(self):
        self.__lockObject.acquire()
        
    def __exit__(self, exc_type, exc_instance, exc_trace): # @UnusedVariable
        try:
            if exc_instance:
                raise
        finally:
            self.__lockObject.release()

synchronized = ConsProxy(SynchronizedInvocator) # synchronized decorator
