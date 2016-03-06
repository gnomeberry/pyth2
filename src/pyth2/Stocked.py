'''
Created on 2016/03/07

@author: _
'''
import weakref

class Stocker(object):
    
    class Stocked(object):
        
        def __init__(self, stocker, value):
            self.__stocker = weakref.ref(stocker)
            self.__released = True
            self.__value = value
        
        @property
        def value(self):
            if self.__released:
                raise ValueError("The object is already stored")
            return self.__value
        
        @value.setter
        def value(self, value):
            if self.__released:
                raise ValueError("The object is already stored")
            self.__value = value
        
        def release(self):
            if self.__released:
                return
            self.__released = True
            maybeStocker = self.__stocker()
            if not maybeStocker is None:
                maybeStocker._release(self)
        
        def purge(self):
            if self.__released:
                return
            self.__released = True
        
        @property
        def isReleased(self):
            return self.__released
        
        def _taken(self):
            self.__released = False
        
    def __init__(self, valueConstructor = None, *valueConstructorArgs, **valueConstructorKwds):
        self.__stock = []
        self.__constructor = (lambda: valueConstructor(*valueConstructorArgs, **valueConstructorKwds)) if callable(valueConstructor) else None
    
    def size(self):
        return len(self.__stock)
    
    def add(self, value):
        self.__stock.append(self.Stocked(self, value))
    
    def take(self):
        if len(self.__stock):
            so = self.__stock.pop()
        else:
            if self.__constructor is None:
                raise ValueError("No more stocked object")
            so = self.Stocked(self, self.__constructor())
        so._taken()
        return so
    
    def _release(self, stocked):
        self.__stock.append(stocked)

class ManagedStocker(object):
    
    def __init__(self, stocker):
        self.__stocker = stocker
    
    def take(self):
        so = self.__stocker.take()
        self.__taken.add(so)
        return so
    
    def __enter__(self):
        self.__taken = set()
        return self
    
    def __exit__(self, excType, excInstance, excTrace):
        try:
            if excInstance:
                raise
        finally:
            for elm in self.__taken:
                elm.release()

if __name__ == "__main__":
    stk = Stocker(int)
    for i in xrange(100):
        stk.add(i)
    with ManagedStocker(stk) as u:
        a1 = u.take()
        a2 = u.take()
        a1.value = 10
        a2.value = 100
        print a1.value
        print a2.value
        print stk.size()
    print stk.size()
    