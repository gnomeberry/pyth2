# -*- coding: utf-8 -*-
'''
Created on 2015/11/03

@author: _
'''

from functools import wraps
import sys
import types

from pyth2.PythUtil import toStrTuple, raiseException
from pyth2.contracts.ContractsUtil import inheritOriginalArgSpec
from pyth2.contracts.InvocableArgumentAccessor import InvocableArgumentAccessor


def validateTypeIdentifier(type_or_tuple_or_list):
    '''
    Validate the type_or_tuple_or_list is valid type identifier
    
    @param type_or_tuple_or_list: a type, a tuple-of-type or a list-of-type
    @raise ValueError: type_or_tuple_or_list is invalid form 
    '''
    if isinstance(type_or_tuple_or_list, (tuple, list)):
        for t in type_or_tuple_or_list:
            try:
                validateTypeIdentifier(t)
            except ValueError as e:
                raise ValueError("%s in %s is invalid(%s)" % toStrTuple(t, type_or_tuple_or_list, e))
    elif not isinstance(type_or_tuple_or_list, type):
        raise ValueError("%s is invalid type" % type_or_tuple_or_list)

class ValidationException(Exception):
    '''
    Exceptions while validating a contract for invocation.
    '''
    pass

def toTypeValidator(a):
    '''
    Converts a python type or a tuple-of-type or a tuple-of-type-or-TypeValidator to a TypeValidator

    @param a: a type, tuple-of-type or a tuple-of-type-or-TypeValidator
    @return: instance of TypeValidator
    '''

    if isinstance(a, type):
        return typeOf(a)
    elif isinstance(a, TypeValidator):
        return a
    elif isinstance(a, tuple) or isinstance(a, list):
        hasNonType = False
        for v in a:
            if not isinstance(v, type):
                hasNonType = True
                break
        
        if hasNonType:
            return anyOf(a)
        else:
            return typeOf(a) if isinstance(a, tuple) else typeOf(tuple(a))

class TypeValidator(object):
    '''
    A type validator
    '''
    
    def isValid(self, value):
        '''
        Checks whether the target value is valid
        
        @param value: a target value
        @return: true if the target value is valid type
        '''
        raise Exception("Abstract method")
    
    def validate(self, value):
        '''
        Through if the target value is valid type or raises ValidationException if invalid
        
        @param value: a target value
        @return: the valud if and only of the value is valid
        '''
        raise Exception("Abstract method")
    
    def __repr__(self):
        return self.__str__()
    

class typeOf(TypeValidator):
    '''
    A type validator for python's value
    '''
    
    _pythonType = None
    
    def __init__(self, pythonType):
        '''
        Initializer
        
        @param pythonType: a type or tuple-of-type
        '''
        validateTypeIdentifier(pythonType)
        self._pythonType = pythonType
    
    def isValid(self, value):
        return isinstance(value, self._pythonType)
    
    def validate(self, value):
        if not self.isValid(value):
            raise ValidationException("%s is not a instance of %s" % toStrTuple(value, self._pythonType))
        return value
    
    def __str__(self):
        return str(self._pythonType)

class anyOf(TypeValidator):
    '''
    A type validator to accept to each one of a type
    '''
    
    _typeValidatorList = None
    
    def __init__(self, containsTypeValidatorTuple):
        '''
        Initializer
        
        @param containsTypeValidatorTuple: a tuple which has at least one TypeValidator instance
        '''
        if not isinstance(containsTypeValidatorTuple, (tuple, list)):
            raise ValueError("%s is not a tuple or a list" % str(containsTypeValidatorTuple))
        
        self._typeValidatorList = [toTypeValidator(t) for t in containsTypeValidatorTuple]
    
    def isValid(self, value):
        for t in self._typeValidatorList:
            if t.isValid(value):
                return True
        return False
    
    def validate(self, value):
        if not self.isValid(value):
            raise ValidationException("%s is not valid value. Must be one of %s" % toStrTuple(value, self._typeValidatorList))
        return value
    
    def __str__(self):
        return "anyOf%s" % str(self._typeValidatorList)

class listOf(TypeValidator):
    '''
    A type validator for python's list
    '''
    _elementType = None
    _minLength = 0
    _maxLength = None
    
    def __init__(self, type_or_tuple, min_length=0, max_length=None):
        '''
        Initializer
        
        @param type_or_tuple: a type or tuple-of-type
        @param min_length: default=0, a minimum length for a validation targetting list
        @param max_length: default=None, a maximum length for a validation targetting list, or represents infinite elements if is None
        '''
        self._elementType = toTypeValidator(type_or_tuple)
        self._minLength = min_length
        self._maxLength = max_length
    
    def isValid(self, value):
        if not isinstance(value, list):
            return False
        elif not (self._minLength <= len(value) and (len(value) <= self._maxLength if self._maxLength is not None else True)):
            return False
        
        for v in value:
            self._elementType.validate(v)
        
        return True
    
    def validate(self, value):
        if not self.isValid(value):
            raise ValidationException("%s is not a valid %s" % toStrTuple(value, self))
        return value
    
    def __str__(self):
        return "listOf(%s, min=%s, max=%s)" % toStrTuple(self._elementType, self._minLength, self._maxLength)
        
class tupleOf(TypeValidator):
    '''
    A type validator for python's tuple
    '''
    
    _eachElementType = None
    
    def __init__(self, *type_list):
        '''
        Initializer
        
        @param type_list: a list-of-type
        '''
        self._eachElementType = tuple(toTypeValidator(t) for t in type_list)
    
    def isValid(self, value):
        if not isinstance(value, tuple):
            return False
        elif len(value) != len(self._eachElementType):
            return False
        
        for v, t in zip(value, self._eachElementType):
            if not t.isValid(v):
                return False
        
        return True
    
    def validate(self, value):
        if not self.isValid(value):
            raise ValidationException("%s is not a valid %s" % toStrTuple(value, self))
        return value
    
    def __str__(self):
        return "tupleOf%s" % str(self._eachElementType)

def generatorWrapper(generator, validator):
    '''
    Creates wrapped generator which validates each value from the original generator
    
    @param generator: a generator
    @param validator: a type validator to check each value of the generator
    @return: wrapped generator
    '''
    def wrappedGenerator():
        for work in generator:
            yield validator.validate(work)
    return wrappedGenerator()

class generatesOf(TypeValidator):
    '''
    A type validator for generator
    '''
    
    _eachElementType = None
    
    def __init__(self, type_or_tuple):
        '''
        Initializer
        
        @param type_list: a list-of-type
        '''
        self._eachElementType = toTypeValidator(type_or_tuple)
    
    def isValid(self, value):
        return isinstance(value, types.GeneratorType)
        
    def validate(self, value):
        if not self.isValid(value):
            raise ValidationException("%s is not a valid %s" % toStrTuple(value, self))
        return generatorWrapper(value, self._eachElementType)
    
    def __str__(self):
        return "tupleOf%s" % str(self._eachElementType)

def validateBefore(func, validator=None):
    '''
    Function wrapper for pre-invocation-validation
    
    @param func: a target function
    @param validator: default=None, no validation is if this is None, or validate before calling the function if this is a function
    @return: a function which is wrapped by validator
    '''
    if validator is None:
        return func
    else:
        iaa = InvocableArgumentAccessor(func)
        @wraps(func)
        def wrapped(*Args, **kwArgs):
            if isinstance(validator, types.FunctionType):
                checkArguments_ArgumentManipulator = validator(func, iaa, *Args, **kwArgs)
                return func(*checkArguments_ArgumentManipulator.fullArgs, **checkArguments_ArgumentManipulator.kwArgs)
            else:
                raise ValidationException("Cannot Value-validation")
        
        return inheritOriginalArgSpec(wrapped, func)

def validateAfter(func, validator=None):
    '''
    Function wrapper for post-invocation-validation
     
    @param func: a target function
    @param validator: default=None, checks result and returns the result(may be transformed) is the value if this is None or not-function type, or invokes the value with 'result' if this is a function
    @return: a wrapped function 
    '''
     
    @wraps(func)
    def wrapped(*Args, **kwArgs):
        result = func(*Args, **kwArgs)
        if validator is None and result is not None:
            raise ValidationException("result=%s expect=None")
        elif isinstance(validator, types.FunctionType):
            result = validator(func, result, *Args, **kwArgs)
        return result
     
    return inheritOriginalArgSpec(wrapped, func)

def returns(*resultType):
    '''
    A decorator function to check results of the invocation

    @param typeList: a list of a type or a TypeValidator
    '''
    resultType = toTypeValidator(resultType) if not isinstance(resultType, TypeValidator) else resultType
    
    def _resultIs(targetFunction, result, *args, **kwargs): # @UnusedVariable
        return resultType.validate(result)

    def adapter(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            return validateAfter(func, _resultIs)(*args, **kwargs)
        return inheritOriginalArgSpec(wrapped, func)

    return adapter

def raises(*excepts):
    '''
    A decorator function to check whether error type is raise being invoking the function.
    ValidationException is raise if an error/exception which is NOT defined in the excepts.

    @param excepts: a list of type of errors/exceptions
    '''
    excepts = toTypeValidator(excepts) if not isinstance(excepts, TypeValidator) else excepts

    def adapter(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except BaseException as e:
                if excepts.isValid(e):
                    raise
                else:
                    raise ValidationException("%s is not a checked error" % str(type(e)))
            except:
                excInfo = sys.exc_info()
                if excepts.isValid(excInfo[0]):
                    raise
                else:
                    raise ValidationException("%s is not a checked error(exc_info=%s)" % toStrTuple(excInfo[0], excInfo))
        return inheritOriginalArgSpec(wrapped, func)

    return adapter

def forms(*typeList, **paramTypeList):
    '''
    A decorator function to check arguments type
    
    @param typeList: a list of type or a tuple-of-type
    @param paramTypeList: a dictionary of parameter-type or parameter-tuple-of-type
    '''
    typeList = map(toTypeValidator, typeList)
    paramTypeList = {k: toTypeValidator(v) for k, v in paramTypeList.items()}
    
    def _instanceOf(func, iaa, *args, **kwargs): # @UnusedVariable
        am = iaa.attach(*args, **kwargs)
        for i in range(len(typeList)):
            am.setByIndex(i, typeList[i].validate(am.getByIndex(i)))
        
        for paramName, typeConstraints in paramTypeList.items():
            am.setByParam(paramName, typeConstraints.validate(am.getByParam(paramName)))
        
        return am
    
    def adapter(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            return validateBefore(func, _instanceOf)(*args, **kwargs)
        
        return inheritOriginalArgSpec(wrapped, func)
    
    return adapter

def numerical():
    return toTypeValidator((int, float, long))

def arithNumerical():
    return toTypeValidator((int, float, long, complex))

def anonyClassCount():
    '''
    Internal value to naming anonymous classes

    @return: a int generator function which used to name to anonymous classes
    '''
    n = 0
    while True:
        yield n
        n += 1
acc = anonyClassCount()

# TypeValidator: Not None value
NotNull = type("_%d" % acc.next(), (TypeValidator,), {
            "isValid": lambda self, value: not value is None,
            "validate": lambda self, value: raiseException(ValidationException("None is not applicable") if not self.isValid(value) else value),
            "__str__": lambda self: "NotNull"
        })()

# TypeValidator: no validation
AnyValue = type("_%d" % acc.next(), (TypeValidator,), {
            "isValid": lambda self, value: True, # @UnusedVariable
            "validate": lambda self, value: value,
            "__str__": lambda self: "AnyValue"
        })()


def hasattrTypeValidator(validator_name, *attr_names):
    '''
    Creates an instance of an anonymous class which can validate a value has the attribute name

    @param validator_name: a name of the validation
    @param attr_names: enumeration of string of attribute names
    '''
    
    if not isinstance(validator_name, basestring) or len(validator_name) == 0:
        raise ValueError("<%s> is not an applicable validator name" % str(validator_name))
    for name in attr_names:
        if not isinstance(name, basestring) or len(name) == 0:
            raise ValueError("<%s> is not an applicable attribute name" % str(name))
    
    validator_name = "hasattr(%s)" % ", ".join(map(str, attr_names)) if validator_name is None else str(validator_name)
    return type("_%d" % acc.next(), (TypeValidator,), {
            "isValid": lambda self, value: all(map(lambda attr: hasattr(value, attr), attr_names)),
            "validate": lambda self, value: raiseException(ValidationException("%s is not satisfy hasattr(%s)" % (str(value), ", ".join(attr_names)))) if not self.isValid(value) else value,
            "__str__": lambda self: validator_name
        })()

# TypeValidator: has __add__ attribute value
Addable = hasattrTypeValidator("Addable", "__add__")
# TypeValidator: has __mul__ attribute value
Multiplicable = hasattrTypeValidator("Multiplicable", "__mul__")
# TypeValidator: has __iter__ attribute value
Iterable = hasattrTypeValidator("Iterable", "__iter__")
# TypeValidator: has next and __iter__ attribute value
Generatable = hasattrTypeValidator("Generatable", "next")
# TypeValidator: has __contains__
Containable = hasattrTypeValidator("Containable", "__contains__")
# TypeValidator: has __call__
Callable = hasattrTypeValidator("Callable", "__call__")
# TypeValidator: has __enter__ and __exit__
Withable = hasattrTypeValidator("With-able", "__enter__", "__exit__")


class DomainTypeValidator(TypeValidator):
    '''
    An base class of validate value.
    '''

def valueSpecValidator(validatorName="", valueValidation=lambda _: True):
    '''
    Constructs a type which can validate whether a value is valid or not
    
    @param validatorName: a name of the validator
    @param valueValidation: a function to be invoked in validation, must be 1 or more parameter is defined
    @return: Instance of TypeValidator
    '''
    return type("_%d" % acc.next(), (DomainTypeValidator,),
            {
                "isValid": lambda self, value: valueValidation(value),
                "validate": lambda self, value: raiseException(ValidationException("%s is not valid value for %s" % (str(value), validatorName))) if not self.isValid(value) else value,
                "__str__": lambda self: validatorName,
            })()

def MoreThan(bound, boundInclude=True):
    '''
    Validate value is more than bound, or more than or equal to bound if the boundInclude is true
    
    @param bound: a upper bound of value
    @param boundInclude: true if the bound is include
    @return: Instance of TypeValidator
    '''
    return valueSpecValidator("%s%s, ...)" % toStrTuple("[" if boundInclude else "(", bound), lambda value: bound <= value if boundInclude else bound < value)

def LessThan(bound, boundInclude=True):
    '''
    Validate value is less than bound, or less than or equal to bound if the boundInclude is true
    
    @param bound: a lower bound of value
    @param boundInclude: true if the bound is include
    @return: Instance of TypeValidator
    '''
    return valueSpecValidator("(..., %s%s" % toStrTuple(bound, "]" if boundInclude else ")"), lambda value: value <= bound if boundInclude else value < bound)

def Inner(lbound, ubound, lboundInclude=True, uboundInclude=True):
    '''
    Validate value is in the range
    
    @param lbound: a lower bound
    @param ubound: a upper bound
    @param lboundInclude: true if the lbound is included in the range
    @param uboundInclude: true if the ubound is included in the range
    @return: Instance of TypeValidator
    '''
    return valueSpecValidator("%s%s, %s%s" % toStrTuple("[" if lboundInclude else "(", lbound, ubound, "]" if uboundInclude else ")"), lambda value: (lbound <= value if lboundInclude else lbound < value) and (value <= ubound if uboundInclude else value < ubound))

def EqualTo(eqv):
    '''
    Validate value is equal to the eqv
    
    @param eqv: an expected value
    @return: Instance of TypeValidator
    '''
    return valueSpecValidator("Is equal to %s" % str(eqv), lambda value: eqv == value)

try:
    import re
    def Matches(regex, re_flags=re.MULTILINE + re.DOTALL):
        '''
        Validate value is matched to the regex pattern
        
        @param regex: a regular expression pattern of string
        @param re_flags: second parameter of re.compile
        @return: Instance of TypeValidator
        '''
        pat = re.compile(regex, re_flags)
        return valueSpecValidator("Pattern(%s)" % regex, lambda value: not pat.match(value if isinstance(value, basestring) else str(value)) is None)
except:
    pass
