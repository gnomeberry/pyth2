'''
Created on 2016/01/27

@author: oreyou
'''
import functools


def ConsProxy(delegator):
    '''
    Constructs a decorator which is delegated to the delegator
    
    example))
    class DecoratorDelegator(object):
        
        def setDecoratorParams(self, func, *args, **kwds):
            print "func, deco args, deco kwds=", func, args, kwds
        
        def __call__(self, *args, **kwds):
            return self._decorator_args[0](*args, **kwds)
    
    bar = ConsProxy(DecoratorDelegator())
    
    @bar(1, 2, "aa")
    def foo(a, b):
        print a, b
        
    foo(1, "a")
    
    @param delegator: callable object 
    '''
    def decorate(*decoArgs, **decoKwds):
        def wrapper(func):
            if callable(delegator.setDecoratorParams):
                delegator.setDecoratorParams(func, decoArgs, decoKwds)
            delegator._decorator_args = (func, decoArgs, decoKwds)
            @functools.wraps(func)
            def wrapped(*args, **kwds):
                return delegator(*args, **kwds)
            return wrapped
        return wrapper
    
    decorate.delegator = delegator
    return decorate

def ConsTranslator(translator):
    '''
    example))
    def puts(args):
        print args
        return args
    
    baz = ConsTranslator(lambda decoParams, *args, **kwds: decoParams[0](*puts(args), **puts(kwds)))
    
    @baz()
    def foofoo(a, b):
        print a, b
    foofoo(1, "a")
    '''
    def decorate(*decoArgs, **decoKwds):
        def wrapper(func):
            decoParams = (func, decoArgs, decoKwds)
            @functools.wraps(func)
            def wrapped(*args, **kwds):
                return translator(decoParams, *args, **kwds)
            return wrapped
        return wrapper
    
    return decorate

if __name__ == "__main__":
    class DecoratorDelegator(object):
        
        def setDecoratorParams(self, func, *args, **kwds):
            print "func, deco args, deco kwds=", func, args, kwds
        
        def __call__(self, *args, **kwds):
            return self._decorator_args[0](*args, **kwds)
    
    bar = ConsProxy(DecoratorDelegator())
    
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
