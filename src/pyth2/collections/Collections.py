#coding: UTF-8
'''
Created on 2016/02/23

@author: _
'''

class IterableExtension(object):
    
    @property
    def each(self):
        selv = self
        rest = iter(selv)
        first = rest.next() if selv else None
        class _each(object):
            def __getattr__(self, name):
                piv = getattr(first, name)
                if callable(piv):
                    return lambda *args, **kwds: EachableGenerator((getattr(elm, name)(*args, **kwds) for elm in selv))
                else:
                    return EachableGenerator((getattr(elm, name) for elm in selv))
            
            def __setattr__(self, name, value):
                for elm in selv:
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
    
    def select(self, predOp):
        return EachableGenerator(transed for transed in (predOp(elm) for elm in self) if transed)
    
    def where(self, predOp):
        return EachableGenerator(elm for elm in self if predOp(elm))
    
    def asList(self):
        return self if isinstance(self, List) else List(self)
    
    def asTuple(self):
        return self if isinstance(self, Tuple) else Tuple(self)
    
    def asSet(self):
        return self if isinstance(self, Set) else Set(self)
    

class EachableGenerator(IterableExtension):
    
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
    print a.where(lambda x: x.bit_length() > 1).each.bit_length().asList()
    
    class Foo(object):
        Bar = None
        def __init__(self, v):
            self.Bar = v
        
        def __str__(self):
            return "%s" % self.Bar
        
        def __repr__(self, *args, **kwargs):
            return self.__str__()
        
    b = List((1, 2, 3, 4)).select(lambda x: Foo(x)).asList()
    print b
    print b.where(lambda x: x.Bar < 3).asList()
    b.where(lambda x: x.Bar < 3).each.Bar = 10 # BUG
    print b
    b.where(lambda x: x.Bar < 3).asList().each.Bar = 10
    print b
