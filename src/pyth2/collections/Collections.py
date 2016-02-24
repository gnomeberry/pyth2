#coding: UTF-8
'''
Created on 2016/02/23

@author: _
'''
from numbers import Number, Complex


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
            
            def __add__(self, other):
                """self + other"""
                return EachableGenerator(elm + other for elm in _collector())
            
            def __radd__(self, other):
                """other + self"""
                return EachableGenerator(other + elm for elm in _collector())
            
            def __neg__(self):
                """-self"""
                return EachableGenerator(-elm for elm in _collector())
            
            def __pos__(self):
                """+self"""
                return EachableGenerator(_collector())
            
            def __sub__(self, other):
                """self - other"""
                return EachableGenerator(elm - other for elm in _collector())
            
            def __rsub__(self, other):
                """other - self"""
                return EachableGenerator(other - elm for elm in _collector())
            
            def __mul__(self, other):
                """self * other"""
                return EachableGenerator(elm * other for elm in _collector())
            
            def __rmul__(self, other):
                """other * self"""
                return EachableGenerator(other * elm for elm in _collector())
            
            def __div__(self, other):
                """self / other without __future__ division
        
                May promote to float.
                """
                other = float(other)
                return EachableGenerator(elm / other for elm in _collector())
            
            def __rdiv__(self, other):
                """other / self without __future__ division"""
                return EachableGenerator(other / elm for elm in _collector())
            
            def __truediv__(self, other):
                """self / other with __future__ division.
                
                Should promote to float when necessary.
                """
                other = float(other)
                return EachableGenerator(elm / other for elm in _collector())
            
            def __rtruediv__(self, other):
                """other / self with __future__ division"""
                other = float(other)
                return EachableGenerator(other / elm for elm in _collector())
            
            def __pow__(self, exponent):
                """self**exponent; should promote to float or complex when necessary."""
                return EachableGenerator(elm ** exponent for elm in _collector())
            
            def __rpow__(self, base):
                """base ** self"""
                return EachableGenerator(base ** elm for elm in _collector())
            
            def __abs__(self):
                """Returns the Real distance from 0. Called for abs(self)."""
                return EachableGenerator(abs(elm) for elm in _collector())
            
            def __eq__(self, other):
                """self == other"""
                return EachableGenerator(elm == other for elm in _collector())
            
            def __ne__(self, other):
                """self != other"""
                return EachableGenerator(elm != other for elm in _collector())
            
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
    def length(self):
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
    
    def __add__(self, other):
        """self + other"""
        return EachableGenerator(elm + other for elm in self.gen)
    
    def __radd__(self, other):
        """other + self"""
        return EachableGenerator(other + elm for elm in self.gen)
    
    def __neg__(self):
        """-self"""
        return EachableGenerator(-elm for elm in self.gen)
    
    def __pos__(self):
        """+self"""
        return self
    
    def __sub__(self, other):
        """self - other"""
        return EachableGenerator(elm - other for elm in self.gen)
    
    def __rsub__(self, other):
        """other - self"""
        return EachableGenerator(other - elm for elm in self.gen)
    
    def __mul__(self, other):
        """self * other"""
        return EachableGenerator(elm * other for elm in self.gen)
    
    def __rmul__(self, other):
        """other * self"""
        return EachableGenerator(other * elm for elm in self.gen)
    
    def __div__(self, other):
        """self / other without __future__ division

        May promote to float.
        """
        other = float(other)
        return EachableGenerator(elm / other for elm in self.gen)
    
    def __rdiv__(self, other):
        """other / self without __future__ division"""
        return EachableGenerator(other / elm for elm in self.gen)
    
    def __truediv__(self, other):
        """self / other with __future__ division.
        
        Should promote to float when necessary.
        """
        other = float(other)
        return EachableGenerator(elm / other for elm in self.gen)
    
    def __rtruediv__(self, other):
        """other / self with __future__ division"""
        other = float(other)
        return EachableGenerator(other / elm for elm in self.gen)
    
    def __pow__(self, exponent):
        """self**exponent; should promote to float or complex when necessary."""
        return EachableGenerator(elm ** exponent for elm in self.gen)
    
    def __rpow__(self, base):
        """base ** self"""
        return EachableGenerator(base ** elm for elm in self.gen)
    
    def __abs__(self):
        """Returns the Real distance from 0. Called for abs(self)."""
        return EachableGenerator(abs(elm) for elm in self.gen)
    
    def __eq__(self, other):
        """self == other"""
        return EachableGenerator(elm == other for elm in self.gen)
    
    def __ne__(self, other):
        """self != other"""
        return EachableGenerator(elm != other for elm in self.gen)
    

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
    b.where(lambda x: x.Bar < 3).each.Bar = 10
    print b
    b.where(lambda x: x.Bar < 3).toList.each.Bar = 10
    print b
    
    c = List(())
    print c.each.bit_length().toList
    print c.length
    
    d = List([1, 2.0, -3, 0 + 4j])
    print (d.each ** 2).toList
    print (8 + (d.each ** 2) / 3.0).toList
    print ((2 + 3j) ** (d.each ** 2) / 3.0).toList
