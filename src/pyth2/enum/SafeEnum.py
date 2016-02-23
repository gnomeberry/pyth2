'''
Created on 2015/11/07

@author: _
'''
from pyth2.contracts import TypeValidator as tv
from types import NoneType

acc = tv.anonyClassCount()

class Enum(object):
    '''
    Base type of Enum<br />
    This class is not able to be instantiate directory.
    
    '''
    
    def __init__(self):
        raise Exception("Cannot instantiate directly Enum class")

@tv.forms(Enum, (Enum, tuple, list, set))
@tv.returns((tuple, list))
def _enum_add_(selv, other):
    if other is list:
        return other if selv in other else [selv] + other
    elif other is tuple:
        return other if selv in other else (selv,) + other
    else:
        return (selv, other)

@tv.forms((type, NoneType), str)
def enumOf(baseType = int, enumName = "", **kwArgs):
    '''
    Defines an anonymous class of Enum.
    Enumerated value can be access by attribute.<br/>
    <pre>
    ex.)
    weekday = enumOf(SUNDAY = 1, MONDAY = 2, TUESDAY = 3, WEDENSDAY = 4, THURSDAY = 5, FRIDAY = 6, SATURDAY = 7)
    print "SUNDAY=" + weekday.SUNDAY # SUNDAY=SUNDAY
    print weekday.SUNDAY == weekday.MONDAY # true
    print weekday.valudOf("TUESDAY") == weekday.TUESDAY # true
    print weekday.hasEnum("WEDENSDAY") # true
    print isinstance(weekday, Enum) # true
    </pre>
    '''
    
    if baseType is None:
        baseType = object
    
    if len(enumName) == 0:
        enumName = "_".join(kwArgs.keys())
    enumType = type(enumName, (Enum, ), {})
    enumType.names = kwArgs.keys()
    enumType.values = []
    #enumType.__contains__ = staticmethod(lambda elementName: elementName in enumType.names)
    enumType.hasEnum = staticmethod(lambda elementName: elementName in enumType.names)
    enumType.valueOf = staticmethod(lambda elementName: getattr(enumType, elementName))
    order = 0
    for elementName, value in kwArgs.items():
        if not isinstance(value, baseType):
            raise ValueError("name=%s value=%s is not applicable for enum of %s" % tv.toStrTuple(elementName, value, baseType))
        if hasattr(enumType, elementName):
            raise ValueError("name=%s is already defined" % elementName)
            
        enumValue = type("_EnumValue%d_" % acc.next(), (enumType,),
                        {
                            "__init__": lambda self: None,
                            "__str__": lambda self: self.enumName,
                            "__repr__": lambda self: self.enumName,
                            "__add__": lambda self, other: _enum_add_(self, other),
                        })()
        
        enumValue.enumName = elementName
        enumValue.__eq__ = lambda self, other: isinstance(other, enumType) and other.order == order
        enumValue.__ne__ = lambda self, other: not self.__eq__(other)
        enumValue.value = value
        enumValue.baseType = enumType
        enumValue.order = order
        enumType.values.append(enumValue)
        setattr(enumType, elementName, enumValue)
        order += 1
    
    return enumType
