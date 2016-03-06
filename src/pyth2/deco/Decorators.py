'''
Created on 2016/01/27

@author: _
'''

import functools
import types


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

# field name for annotations
ANNOTATION_FIELD_NAME = "__annotations"
ANNOTATION_GETTER_NAME = "_getAnnotation"
ANNOTATION_HAS_NAME = "_hasAnnotation"

def ConsAnnotator(annotationType):
    """
    Constructs annotations.
    Annotations are not like Decorators. The annotation does not modify original function, but it only appends 'annotation'.
    
    ex)
    class SomeAnnotation(AbstractAnnotation): pass
    some_annotation = ConsAnnotator(SomeAnnotation)
    @some_annotation(a = 1, b = 2) # outer one. "inner" annotation might be shadowed by the outer
    @some_annotation(x = "a", y = "b") # inner annotation
    def func(*args):
        print getAnnotation(func) # outputs whole annotations which is attached to "func"(i.e self) object
        print getAnnotation(func, SomeAnnotation) # annotations for "func" object is accessible because it is not modified by "some_annotation".
        print getAnnotation(func, object) # annotation type "object" is not attached to "func" object. Outputs None.
        print args
    
    @param annotationType: annotation type
    @return: an annotation decorator
    """
    if not isinstance(annotationType, type):
        raise ValueError("%s is not a type" % annotationType)
    
    def annotate(*annotationArgs, **annotationKwds):
        def annotation(annotatee):
            annos = None
            if not hasattr(annotatee, ANNOTATION_FIELD_NAME):
                annos = {}
                setattr(annotatee, ANNOTATION_FIELD_NAME, annos)
                setattr(annotatee, ANNOTATION_GETTER_NAME, types.MethodType(lambda self, name: getAnnotation(self, name), annotatee, type(annotatee)))
                setattr(annotatee, ANNOTATION_HAS_NAME, types.MethodType(lambda self, name: isAnnotated(self, name), annotatee, type(annotatee)))
            else:
                annos = getattr(annotatee, ANNOTATION_FIELD_NAME)
            if not isinstance(annos, dict):
                raise ValueError("Annotation container %s of %s is not a dict: %s" % (ANNOTATION_FIELD_NAME, annotatee, type(annos)))
            lastAnnotation = None if not annotationType in annos else annos[annotationType]
            annos[annotationType] = annotationType(annotatee, lastAnnotation, *annotationArgs, **annotationKwds)
            return annotatee
        return annotation
    return annotate

def isAnnotated(func, annotationType = None):
    """
    
    """
    if not hasattr(func, ANNOTATION_FIELD_NAME):
        return False
    else:
        annos = getattr(func, ANNOTATION_FIELD_NAME)
        if not isinstance(annos, dict):
            return False
        else:
            return True if annotationType is None else annotationType in annos 

def getAnnotation(func, annotationType = None):
    if not isAnnotated(func):
        return None
    
    annos = getattr(func, ANNOTATION_FIELD_NAME)
    if annotationType is None:
        return annos
    else:
        return annos[annotationType]

class AbstractAnnotation(object):
    
    def __init__(self, generatorFunc, predefined, *args, **kwds):
        self.func = generatorFunc
        self.predefined = predefined
        self.args = args
        self.keywords = kwds
    
    def __iter__(self):
        cur = self
        while cur:
            yield cur
            cur = cur.predefined
    
    def __str__(self):
        return u"%s(%s; %s%s)" % (self.__class__.__name__, self.args, self.keywords, u" <overrides: %s>" % self.predefined if not self.predefined is None else u"")
    
    def __repr__(self):
        return self.__str__()


if __name__ == "__main__":
    class DecoratorDelegator(object):
        
        def __init__(self, generatorFunc, *args, **kwds):
            print "generatorFunc, deco args, deco kwds=", generatorFunc, args, kwds
            self.func = generatorFunc
        
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
    
    class FooAnnotation(AbstractAnnotation):
        pass
    
    anno = ConsAnnotator(FooAnnotation)
    @anno(1, "a", x = int, y = basestring)
    @anno(2, "b")
    def foo(x, y):
        for a in getAnnotation(foo, FooAnnotation):
            print "foo.annotations=", a.args, a.keywords
        print x, y
    print foo, getAnnotation(foo), isAnnotated(foo)
    print foo._getAnnotation(None)
    print foo._hasAnnotation(None)
    foo(1,2)
    