#coding: UTF-8
'''
Created on 2016/02/23

@author: _
'''

class IterableExtension(object):
    
    @property
    def each(self):
        sentry = object()
        selv = self
        rest = iter(selv)
        first = next(rest, sentry)
        def _collector():
            if first is sentry:
                return
            yield first
            for elm in rest:
                yield elm
        
        class _each(object):
            def __getattr__(self, name):
                if first is sentry:
                    return lambda *args, **kwds: EachableGenerator.nullObject() # for invocation safety
                
                piv = getattr(first, name)
                if callable(piv):
                    return lambda *args, **kwds: EachableGenerator((getattr(elm, name)(*args, **kwds) for elm in _collector()))
                else:
                    return EachableGenerator((getattr(elm, name) for elm in _collector()))
            
            def __setattr__(self, name, value):
                for elm in _collector():
                    setattr(elm, name, value)
                return selv
        return _each()
    
    def agg(self, init, transOp = None):
        if transOp is None:
            for elm in self:
                init = init + elm
        else:
            for elm in self:
                init = init + transOp(elm)
        return init
    
    def convolve(self, init, reduceOp):
        for elm in self:
            init = reduceOp(init, elm)
        return init
    
    def select(self, transOp):
        return EachableGenerator(transed for transed in (transOp(elm) for elm in self))
    
    def where(self, predOp):
        return EachableGenerator(elm for elm in self if predOp(elm))
    
    @property
    def count(self):
        return self.agg(0, lambda x: 1)
    
    @property
    def toList(self):
        return self if isinstance(self, List) else List(self)
    
    @property
    def toTuple(self):
        return self if isinstance(self, Tuple) else Tuple(self)
    
    @property
    def toSet(self):
        return self if isinstance(self, Set) else Set(self)
    

class EachableGenerator(IterableExtension):
    
    @staticmethod
    def nullObject():
        return EachableGenerator((_ for _ in []))
    
    def __init__(self, gen):
        self.gen = gen
    
    def __iter__(self):
        return self.gen
    
    def next(self):
        return self.gen.next()
    

class List(list, IterableExtension):
    pass

class Set(set, IterableExtension):
    pass

class Tuple(tuple, IterableExtension):
    pass

if __name__ == "__main__":
    a = List((1, 2, 3, 4))
    print a.where(lambda x: x.bit_length() > 1).each.bit_length().toList
    
    class Foo(object):
        Bar = None
        def __init__(self, v):
            self.Bar = v
        
        def __str__(self):
            return "%s" % self.Bar
        
        def __repr__(self, *args, **kwargs):
            return self.__str__()
        
    b = List((1, 2, 3, 4)).select(lambda x: Foo(x)).toList
    print b
    print b.where(lambda x: x.Bar < 3).toList
    b.where(lambda x: x.Bar < 3).each.Bar = 10 # BUG
    print b
    b.where(lambda x: x.Bar < 3).toList.each.Bar = 10
    print b
    
    c = List(())
    print c.each.bit_length().toList
