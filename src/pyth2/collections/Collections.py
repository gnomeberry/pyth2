#coding: UTF-8
'''
Created on 2016/02/23

@author: _
'''
import operator


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
    
    def group(self, labelOp):
        grp = {}
        for elm in self:
            label = labelOp(elm)
            if label in grp:
                grp[label].append(elm)
            else:
                grp[label] = List([elm])
        return grp
    
    @property
    def flat(self):
        def _flatten(ao):
            if hasattr(ao, "__iter__"):
                for elm in ao:
                    if hasattr(elm, "__iter__"):
                        for inElm in _flatten(elm):
                            yield inElm
                    else:
                        yield elm
            else:
                yield ao
        return EachableGenerator(_flatten(self))
    
    def flatMap(self, transOp):
        return EachableGenerator(transOp(elm) for elm in self.flat)
    
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
    
    @property
    def toGenerator(self):
        return self if isinstance(object, EachableGenerator) else EachableGenerator(self)
    

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
        return EachableGenerator(operator.truediv(elm, other) for elm in self.gen)
    
    def __rtruediv__(self, other):
        """other / self with __future__ division"""
        return EachableGenerator(operator.truediv(other, elm) for elm in self.gen)
    
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
    print (d.toGenerator ** 2).toList
    print (8 + (d.toGenerator ** 2) / 3.0).toList
    print ((2 + 3j) ** (d.toGenerator ** 2) / 3.0).toList
    
    e = List((1, (2, 3), 4, (5, (6, (7,))), 8))
    eGroup = e.flat.group(lambda x: x < 4)
    print eGroup
    print (-(eGroup[True].toGenerator / 3.0)).toList
    print (eGroup[False].toGenerator * 3.0).toList
    
    f = List(("abc", "DEF", "gHi"))
    print f
    print List(f.each.upper())
    print f.select(lambda x: List(x)).toList
    print f.select(lambda x: List(x)).flatMap(lambda x: x.upper()).toList
    print "".join(f.select(lambda x: List(x)).flatMap(lambda x: x.upper()).toList)
    
    from pyth2.concurrent import Concurrent
    executor = Concurrent.Executor(True, 10)
    def hanoi(n, start, end, work):
        if n > 0:
            k = hanoi(n - 1, start, work, end)
            return hanoi(n - 1, work, end, start) + k + 1
        return 0
    g = List(range(22))
    print g
    print g.select(lambda x: executor.submit(lambda: hanoi(x, "A", "B", "C"))).each.getSafe().toList
