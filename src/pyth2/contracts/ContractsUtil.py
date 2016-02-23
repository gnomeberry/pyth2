'''
Created on 2015/11/08

@author: _
'''
from inspect import getargspec


ORIGINAL_ARGSPEC_ATTRIBUTE = "__originArgSpec__"

def getOriginalArgSpec(func):
    '''
    Returns a ArgSpec of the function
    
    @param func: a target function
    @return: ArgSpec instance of the function
    '''
    if not hasattr(func, ORIGINAL_ARGSPEC_ATTRIBUTE):
        return getargspec(func)
    else:
        return func.__originArgSpec__

def inheritOriginalArgSpec(func, originFunc):
    '''
    Save a ArgSpec of the originalFunc to func
    
    @param func: a target function
    @param originalFunc: an original function
    @return: func which is save ArgSpec of the original function to attribute ORIGINAL_ARGSPEC_ATTRIBUTE
    '''
    func.__originArgSpec__ = getOriginalArgSpec(originFunc)
    return func
