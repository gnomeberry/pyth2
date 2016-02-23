'''
Created on 2015/11/08

@author: wildberry
'''
from __builtin__ import basestring
import types

def raiseException(excp):
    '''
    Raises an error if the excp is a instance of an error/exception

    @param excp: an error/exception instance
    @return: excp if and only if the excp is not a class or a sub-class of BaseException
    '''
    if isinstance(excp, BaseException):
        raise excp
    else:
        return excp

def toStrTuple(*args):
    '''
    Returns tuple(map(str, fullArgs))

    @param fullArgs: varargs to map str function
    @return: a tuple-of-str
    '''
    return tuple(map(str, args))

def switch(cases):
    '''
    C-like switch-case statement.(But no-through and matching is not ordinal)<br/>
    <pre>
    example)
    # ['0-th', 'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth']
    nth10 = switch({
            1: lambda v: "first",
            2: lambda v: "second",
            3: lambda v: "third",
            4: lambda v: "fourth",
            5: lambda v: "fifth",
            6: lambda v: "sixth",
            7: lambda v: "seventh",
            8: lambda v: "eighth",
            9: lambda v: "ninth",
            10: lambda v: "tenth",
            None: lambda v: str(v) + "-th"}) # key == None is default
    print map(nth10, range(11))
    </pre>
    
    @param cases: an instance of dict(key = any value, value = 1-ary function)
    @return: a function
    '''
    if not isinstance(cases, dict):
        raise ValueError("%s is not an instance of dict" % str(cases))
    
    if None in cases:
        defaulted = cases[None]
        cases.pop(None)
    else:
        defaulted = lambda _: None
    
    def find(value):
        if not value in cases:
            return defaulted(value) if defaulted else None
        else:
            return cases[value](value)
    return find

def _match_split_defaulted(cases):
    '''
    Private function for match(cases), regmatch(cases) and switch(cases) function
    
    @param cases: an instance of dict
    @return: a tuple of (defaulted, cases)
    '''
    if not isinstance(cases, dict):
        raise ValueError("%s is not an instance of dict" % str(cases))
    
    if None in cases:
        defaulted = cases[None]
        cases.pop(None)
    else:
        defaulted = lambda _: None
    return defaulted, cases
    
def match(cases):
    '''
    Creates a function which can find and evaluate a value<br />
    <pre>
    example)
    # ['0 == 0', '0 < 1 <= 3', '0 < 2 <= 3', '0 < 3 <= 3', '4 is not in 0 to 3']
    print map(match({
             (lambda v: v == 0): (lambda v: str(v) + " == 0"),
             (lambda v: 0 < v and v <= 3): (lambda v: "0 < " + str(v) + " <= 3"),
             None: (lambda v: str(v) + " is not in 0 to 3")}), (i for i in range(5))) # key == None is default
    </pre>
    
    @param cases: an instance of dict(key = 1-ary boolean function, value = 1-ary function) 
    @return: a function
    '''
    defaulted, cases = _match_split_defaulted(cases)
    
    def find(value):
        for pat, lmd in cases.items():
            if pat(value):
                return lmd(value)
        if defaulted:
            return defaulted(value)
        return None
    return find

try:
    import re
    def regmatch(cases):
        '''
        Creates a function which can search and evaluate a value<br />
        <pre>
        example)
        # ['Starts with x: xyz', 'Starts with y: yzx', 'Starts with z: zxy', 'Prefix is not x, y or z: abc']
        finder = regmatch({
                r"^x.*$": lambda v: "Starts with x: " + v,
                r"^y.*$": lambda v: "Starts with y: " + v,
                re.compile(r"^z.*$"): lambda v: "Starts with z: " + v,
                None: lambda v: "Prefix is not x, y or z: " + v}) # key == None is default
        print map(finder, ["xyz", "yzx", "zxy", "abc"])
        </pre>
        
        @param cases: a dictionary object(key = basestring or compiled regular expression(re.compile(..)), value = 1-ary function)
        @return: a function
        '''
        defaulted, cases = _match_split_defaulted(cases)
        cases = {(lambda target, keyregex=key: re.search(keyregex, target, re.DOTALL) if isinstance(keyregex, basestring) else keyregex.search(target))
                 : lmd for key, lmd in cases.items()}
        if defaulted:
            cases[None] = defaulted
        return match(cases)
except:
    pass

def select(values, pred = (lambda: True)):
    '''
    Select a value which satisfies pred
    
    @param values: iterable object
    @param pred: function for predicating value or value to compare to each value in values
    @return: a sequence of value which satisfies pred
    '''
    if isinstance(pred, types.FunctionType):
        for v in values:
            if pred(v):
                yield v
        return
    else:
        for v in values:
            if v == pred:
                yield v
        return

