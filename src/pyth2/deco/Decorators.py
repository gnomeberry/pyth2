'''
Created on 2016/01/27

@author: _
'''

import functools


def getOriginalDecoratee(decorated):
    return decorated._original_decoratee if hasattr(decorated, "_original_decoratee") else decorated

def updateOriginalDecoratee(wrapped, decorated):
    wrapped._original_decoratee = getOriginalDecoratee(decorated)

def ConsProxy(delegatorType):
    '''
    Constructs a decorator which is delegated to the delegator
    
    example))
    class DecoratorDelegator(object):
        
        def setDecoratorParams(self, func, *args, **kwds): # optional setter for decorator's parameters
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

ANNOTATION_FIELD_NAME = "_annotations"
def ConsAnnotation(annotatorType):
    
    if not isinstance(annotatorType, type):
        raise ValueError("%s is not a type" % annotatorType)
    
    def annotate(*annotationArgs, **annotationKwds):
        def annotation(func):
            annos = None
            if not hasattr(func, ANNOTATION_FIELD_NAME):
                annos = {}
                setattr(func, ANNOTATION_FIELD_NAME, annos)
            else:
                annos = getattr(func, ANNOTATION_FIELD_NAME)
            if not isinstance(annos, dict):
                raise ValueError("Annotation container %s of %s is not a dict: %s" % (ANNOTATION_FIELD_NAME, func, type(annos)))
            lastAnnotation = None if not annotatorType in annos else annos[annotatorType]
            annos[annotatorType] = annotatorType(func, lastAnnotation, *annotationArgs, **annotationKwds)
            return func
        return annotation
    return annotate

def isAnnotated(func):
    if not hasattr(func, ANNOTATION_FIELD_NAME):
        return False
    else:
        return isinstance(getattr(func, ANNOTATION_FIELD_NAME), dict)

def getAnnotation(func, annotationType = None):
    if not isAnnotated(func):
        return None
    
    annos = getattr(func, ANNOTATION_FIELD_NAME)
    if annotationType is None:
        return annos
    else:
        return annos[annotationType]

class AbstractAnnotator(object):
    
    def __init__(self, func, predefined, *args, **kwds):
        self.func = func
        self.predefined = predefined
        self.args = args
        self.keywords = kwds
    
    def __str__(self):
        return u"%s(%s; %s%s)" % (self.__class__.__name__, self.args, self.keywords, u" <overrides: %s>" % self.predefined if not self.predefined is None else u"")
    
    def __repr__(self):
        return self.__str__()


if __name__ == "__main__":
    class DecoratorDelegator(object):
        
        def __init__(self, func, *args, **kwds):
            print "func, deco args, deco kwds=", func, args, kwds
            self.func = func
        
        def __call__(self, *args, **kwds):
            return self.func(*args, **kwds)
    
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
    
    class FooAnnotation(AbstractAnnotator):
        pass
    
    anno = ConsAnnotation(FooAnnotation)
    @anno(1, "a", x = int, y = basestring)
    @anno(2, "b")
    def foo(x, y):
        print x, y
    print foo(1,2), isAnnotated(foo), getAnnotation(foo)
    print foo
    