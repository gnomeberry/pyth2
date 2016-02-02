'''
Created on 2016/01/27

@author: oreyou
'''

import functools
import sys
from threading import Lock
from time import time
from datetime import datetime


def getOriginalDecoratee(decorated):
    return decorated._original_decoratee if hasattr(decorated, "_original_decoratee") else decorated

def updateOriginalDecoratee(wrapped, decorated):
    wrapped._original_decoratee = getOriginalDecoratee(decorated)

def ConsProxy(delegatorType):
    '''
    Constructs a decorator which is delegated to the delegator
    
    example))
    class DecoratorDelegator(object):
        
        def __init__(self, func, *args, **kwds): # decorator's parameters
            print "func, deco args, deco kwds=", func, args, kwds
        
        def __call__(self, *args, **kwds):
            return self._decorator_args[0](*args, **kwds)
    
    bar = ConsProxy(DecoratorDelegator)
    
    @bar(1, 2, "aa")
    def foo(a, b):
        print a, b
        
    foo(1, "a")
    
    @param delegatorType: type of delegator 
    '''
    
    if not isinstance(delegatorType, type):
        raise ValueError("%s is not a type" % delegatorType)
    
    def decorate(*decoArgs, **decoKwds):
        def wrapper(func):
            delegator = delegatorType(func, *decoArgs, **decoKwds)
            delegator._decorator_args = (func, decoArgs, decoKwds)
            @functools.wraps(func)
            def wrapped(*args, **kwds):
                return delegator(*args, **kwds)
            updateOriginalDecoratee(wrapped, func)
            return wrapped
        return wrapper
    
    return decorate

def ConsTranslator(translator):
    '''
    example))
    def puts(args):
        print args
        return args
    
    baz = ConsTranslator(lambda decoArgs, decoKwds, func, *args, **kwds: func(*puts(args), **puts(kwds)))
    
    @baz()
    def foofoo(a, b):
        print a, b
    foofoo(1, "a")
    '''
    def decorate(*decoArgs, **decoKwds):
        def wrapper(func):
            @functools.wraps(func)
            def wrapped(*args, **kwds):
                return translator(decoArgs, decoKwds, func, *args, **kwds)
            updateOriginalDecoratee(wrapped, func)
            return wrapped
        return wrapper
    
    return decorate

class SynchronizedInvocator(object):
    
    def __init__(self, func, lockObject = None):
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
        
    def __exit__(self, exc_type, exc_instance, exc_trace):
        try:
            if exc_instance:
                raise
        finally:
            self.__lockObject.release()

synchronized = ConsProxy(SynchronizedInvocator) # synchronized decorator

class MemoizeInvocator(object):
    '''
    Proxy for memoize decorator
    '''
    maximumMemoSize = None
    func = None
    __memo = dict()
    
    @staticmethod
    def __freeze(val):
        if isinstance(val, (dict, set)):
            return frozenset((key, MemoizeInvocator.__freeze(value)) for key, value in val.items())
        elif isinstance(val, (list, tuple)):
            return tuple(MemoizeInvocator.__freeze(value) for value in val)
        elif not hasattr(val, "__hash__"):
            return id(val)
        return val
    
    @staticmethod
    def _argTuple_Freezed(args, kwds):
        return MemoizeInvocator.__freeze((args, kwds))
    
    @staticmethod
    def _argTuple_Serialized(args, kwds):
        import cPickle
        return cPickle.dumps((args, kwds))
    
    def __init__(self, func, memoSize = None, compaction = None):
        '''
        Setup function
        
        @param func: a function
        @param memoSize: maximum memo size, or None for unlimited memo
        @param compaction: a function(timestamp: double, argTuple: a, argTuple: b) to select a removable memo when memo size is reached to maximum memo size, or None selects a oldest memo
        '''
        self.maximumMemoSize = None if memoSize is None else max((1, int(memoSize)))
        self.compaction = compaction if callable(compaction) else lambda maxMemoSize, index, item: item[0]
        self.func = func
        self.func._argTuple = MemoizeInvocator._argTuple_Freezed
        self.func._argTupleFailed = False 
    
    def _addMemo(self, argTuple, results, errors):
        self.__memo[argTuple] = [time() * 10000, results, errors]
        if self.maximumMemoSize and len(self.__memo) > self.maximumMemoSize:
            removeKey = min(enumerate(self.__memo.iteritems()), key = lambda a: self.compaction(self.maximumMemoSize, a[0], a[1]))
            self.__memo.pop(removeKey[1][0])
    
    def _findMemo(self, argTuple):
        if self.__memo.has_key(argTuple):
            return self.__memo.get(argTuple)
        else:
            return None
    
    def _updateMemo(self, argTuple):
        self.__memo[argTuple][0] = time() * 10000
    
    def __call__(self, *args, **kwds):
        if not self.func._argTupleFailed:
            try:
                argTuple = self.func._argTuple(args, kwds)
                hash(argTuple) # test argTuple is hashable
            except:
                self.func._argTupleFailed = True
                self.func._argTuple = MemoizeInvocator._argTuple_Serialized
                argTuple = self.func._argTuple(args, kwds)
        else:
            argTuple = self.func._argTuple(args, kwds)                                                                                                                                 
        memo = self._findMemo(argTuple)
        if not memo:
            # miss cache
            try:
                result = self.func(*args, **kwds)
                self._addMemo(argTuple, result, None)
                return result
            except:
                exc_type, exc_value, exc_trace = sys.exc_info()
                self._addMemo(argTuple, None, (exc_type, exc_value, exc_trace))
        else:
            # hits cache
            self._updateMemo(argTuple)
            if memo[2]:
                raise memo[2][2]
            else:
                return memo[1]

memoize = ConsProxy(MemoizeInvocator) # Memoize decorator

class Timestamper(object):
    
    timestamped = set()
    
    @staticmethod
    def getTimestamper(afunc):
        return afunc._timestamper
    
    def __init__(self, func, storeMinMaxArgs = True):
        self.func = func
        self.storeMinMaxArgs = storeMinMaxArgs
        self.maxStamp = [-float("inf"), None]
        self.minStamp = [float("inf"), None]
        self.invocationTimes = 0
        self.sumStamp = 0
        self.func._timestamper = self
        Timestamper.timestamped.add(self)
    
    def __str__(self):
        return "%s[invoke=%d, mean=%f, min=(%f, args=%s), max=(%f, args=%s)" % (self.func, self.invocationTimes, self.getMeanTime(), self.minStamp[0], self.minStamp[1], self.maxStamp[0], self.maxStamp[1])
    
    def __call__(self, *args, **kwds):
        self.invocationTimes += 1
        begin = datetime.now()
        try:
            return self.func(*args, **kwds)
        finally:
            diff = (datetime.now() - begin).microseconds
            if self.maxStamp[0] < diff:
                self.maxStamp[0] = diff
                if self.storeMinMaxArgs:
                    self.maxStamp[1] = (args, kwds)
            if self.minStamp[0] > diff:
                self.minStamp[0] = diff
                if self.storeMinMaxArgs:
                    self.minStamp[1] = (args, kwds)
            self.sumStamp += diff
    
    def getMeanTime(self):
        return float(self.sumStamp) / self.invocationTimes

timestamp = ConsProxy(Timestamper)

if __name__ == "__main__":
    class DecoratorDelegator(object):
        
        def __init__(self, func, *args, **kwds):
            print "func, deco args, deco kwds=", func, args, kwds
        
        def __call__(self, *args, **kwds):
            return self._decorator_args[0](*args, **kwds)
    
    bar = ConsProxy(DecoratorDelegator)
    
    @bar(1, 2, "aa")
    def foo(a, b):
        print a, b
       
    foo(1, "a")
    
    def puts(args):
        print args
        return args
    baz = ConsTranslator(lambda decoParams, *args, **kwds: puts(decoParams) and decoParams[0](*puts(args), **puts(kwds)))
    @baz()
    def foofoo(a, b):
        print a, b
    foofoo(1, "a")
    
    @memoize()
    def factorial(n):
        return 1 if n <= 0 else n * factorial(n - 1)
    for i in xrange(100):
        print i, factorial(i)
    
    @timestamp()
    def bar(n):
        for i in xrange(n):
            pass
    for i in xrange(100):
        bar(10000 * i)
    print Timestamper.getTimestamper(bar)
    