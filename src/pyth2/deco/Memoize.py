#coding: UTF-8
'''
Created on 2016/02/09

@author: _
'''
from datetime import time
import sys

from pyth2.deco.Decorators import ConsProxy


class MemoizeInvocator(object):
    '''
    Proxy for memoize decorator
    '''
    maximumMemoSize = None
    annotatee = None
    __memo = dict()
    
    @staticmethod
    def __freeze(val):
        if isinstance(val, (dict, set)):
            return frozenset((key, MemoizeInvocator.__freeze(value)) for key, value in val.items())
        elif isinstance(val, (list, tuple)):
            return tuple(MemoizeInvocator.__freeze(value) for value in val)
        return val
    
    @staticmethod
    def _argTuple_Freezed(args, kwds):
        return MemoizeInvocator.__freeze((args, kwds))
    
    @staticmethod
    def _argTuple_Serialized(args, kwds):
        import cPickle
        return cPickle.dumps((args, kwds))
    
    def setDecoratorParams(self, func, memoSize = None, compaction = None):
        '''
        Setup function
        
        @param annotatee: a function
        @param memoSize: maximum memo size, or None for unlimited memo
        @param compaction: a function(timestamp: double, argTuple: a, argTuple: b) to select a removable memo when memo size is reached to maximum memo size, or None selects a oldest memo
        '''
        self.maximumMemoSize = None if memoSize is None else max((1, int(memoSize)))
        self.compaction = compaction if callable(compaction) else lambda maxMemoSize, index, item: item[0]
        self.annotatee = func
        self.annotatee._argTuple = MemoizeInvocator._argTuple_Freezed
        self.annotatee._argTupleFailed = False 
    
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
        if not self.annotatee._argTupleFailed:
            try:
                argTuple = self.annotatee._argTuple(args, kwds)
            except:
                self.annotatee._argTupleFailed = True
                self.annotatee._argTuple = MemoizeInvocator._argTuple_Serialized
                argTuple = self.annotatee._argTuple(args, kwds)
        else:
            argTuple = self.annotatee._argTuple(args, kwds)                                                                                                                                 
        memo = self._findMemo(argTuple)
        if not memo:
            # miss cache
            try:
                getSafe = self.annotatee(*args, **kwds)
                self._addMemo(argTuple, getSafe, None)
                return getSafe
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
