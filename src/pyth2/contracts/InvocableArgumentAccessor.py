'''
Created on 2015/11/08

@author: _
'''
from __builtin__ import ValueError, TypeError, KeyError
import inspect
import types

from pyth2.PythUtil import toStrTuple
from pyth2.contracts.ContractsUtil import ORIGINAL_ARGSPEC_ATTRIBUTE


class InvocableArgumentAccessor(object):
    '''
    A class for wrapping to invoke function
    '''
    
    _func = None
    _argSpec = None
    _paramNames = [] # list<string>
    _paramIndex = {} # map<string, int>
    
    def __init__(self, generatorFunc):
        '''
        Initiaize
        
        @param generatorFunc: a target function
        '''
        if not isinstance(generatorFunc, types.FunctionType):
            raise ValueError("%s is not FunctionType" % str(generatorFunc))
        self._func = generatorFunc
        self._argSpec = inspect.getargspec(generatorFunc) if not hasattr(generatorFunc, ORIGINAL_ARGSPEC_ATTRIBUTE) else generatorFunc.__originArgSpec__
        self._paramNames = self._argSpec.args
        self._paramIndex = {para: index for para, index in zip(self._paramNames, range(len(self._paramNames)))}
        
    def attach(self, *Args, **kwArgs):
        '''
        Attaches Args and kwArgs to invoke the function
        
        @param Args: arguments
        @param kwArgs: keyword arguments
        @return: an instance of ArgumentManipulator
        '''
        return ArgumentManipulator(self, *Args, **kwArgs)

class ArgumentManipulator(object):
    '''
    A class for manipulating function invoking
    '''
    
    argSize = 0 # Function signature's parameter size
    iaa = None # an associated instance of InvocableArgumentAccessor
    fullArgs = None # Full arguments
    args = None # Partial arguments which required for invoking a function. This value refer to fullArgs
    varargs = None # Partial arguments which may require for invoking a function
    kwArgs = {} # Reminder of keyword arguments
    
    def __init__(self, iaa, *Args, **kwArgs):
        '''
        Initializer
        
        @param iaa: an associated instance of InvocableArgumentAccessor
        @param Args: arguments
        @param kwArgs: keyword arguments
        '''
        
        self.iaa = iaa
        
        # decides fullArgs, args and varargs
        self.fullArgs = list(Args)
        self.argSize = len(iaa._paramNames)
        if len(self.fullArgs) < self.argSize:
            # number of fullArgs is less than arguments size to invoke function.
            # fill up the fullArgs with defaulted value or raise error if no defaults are specified
            requireDefaults = self.argSize - len(self.fullArgs)
            if iaa._argSpec.defaults is None or len(iaa._argSpec.defaults) < requireDefaults:
                raise TypeError("Arguments size mismatch")
            self.fullArgs += iaa._argSpec.defaults[len(iaa._argSpec.defaults) - requireDefaults:]
            self.args = self.fullArgs # refer to fullArgs
            self.varargs = None
        elif len(self.fullArgs) > self.argSize:
            # number of fullArgs is more than arguments size to invoke function.
            # args is clipped to minimum size for function invoking, and assigns varargs to remains 
            if iaa._argSpec.varargs is None:
                raise TypeError("The function takes exactly %d arguments (%d given)" % (self.argSize, len(self.fullArgs)))
            self.args = self.fullArgs[:self.argSize] # refer to fullArgs
            self.varargs = tuple(self.fullArgs[self.argSize:]) # refer to fullArgs
        else:
            # number of fullArgs is equal to arguments size to invoke function.
            self.args = self.fullArgs
            self.varargs = None if iaa._argSpec.varargs is None else tuple([])
        
        # decides kwArgs
        for key, value in kwArgs.items():
            if key in iaa._paramNames:
                # if key in kwArgs is defined in parameter name, the key is remove from the kwArgs and assigns value to the parameter
                self.fullArgs[iaa._paramIndex[key]] = value
                kwArgs.pop(key)
        self.kwArgs = kwArgs
        
    def __str__(self):
        return "ArgumentManipulator(params=%s, fullArgs=%s, args=%s, varargs=%s, kwargs=%s)" % toStrTuple(self.iaa._paramNames, self.fullArgs, self.args, self.varargs, self.kwArgs)
    
    def __repr__(self):
        return self.__str__()
    
    
    def getByParam(self, param):
        '''
        Get value of the parameter
        
        @param param: a name of parameter
        @return: arguments of the parameter
        '''
        if param in self.iaa._paramIndex:
            return self.fullArgs[self.iaa._paramIndex[param]]
        else:
            if not param in self.kwArgs:
                # varargs name
                if param == self.iaa._argSpec.varargs:
                    return self.varargs
                else:
                    raise KeyError("'%s' is not defined in keyword arguments %s" % (param, str(self.kwArgs)))
            return self.kwArgs[param]
    
    def setByParam(self, param, value):
        '''
        Set value of the parameter
        
        @param param: a name of parameter
        @param value: a value of the parameter
        @return: value
        '''
        if param in self.iaa._paramIndex:
            self.fullArgs[self.iaa._paramIndex[param]] = value
            return value
        else:
            # varargs name
            if param == self.iaa._argSpec.varargs:
                self.varargs = value
            else:
                self.kwArgs[param] = value
            return value
    
    def getByIndex(self, index):
        '''
        Get value of position at the index
        
        @param index: an index of parameter
        @return: arguments of the parameter
        '''
        return self.fullArgs[index]
    
    def setByIndex(self, index, value):
        '''
        Set value of the parameter
        
        @param index: an index of parameter
        @param value: a value of the parameter
        @return: value
        '''
        self.fullArgs[index] = value
        return value
    
    def invoke(self, func):
        '''
        Invokes the func with current arguments(fullArgs, kwArgs)
        
        @param func: target function to invoke
        @return: a return value of the invocation
        '''
        return func(*self.fullArgs, **self.kwArgs)

