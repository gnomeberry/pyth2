'''
Created on 2015/11/07

@author: _
'''
'''
A enum of direction of a stream: READ, WRITE, READOrWRITE
'''

from pyth2.contracts import TypeValidator as tv
from pyth2.enum.SafeEnum import enumOf


StreamDirection = enumOf(int, READ = 0, WRITE = 1, READOrWRITE = 2)

class Stream(object):
    '''
    Base class of stream
    '''
    
    @tv.forms(object, StreamDirection, type)
    def __init__(self, direction, manipulateType):
        self._direction = direction
        self._manipulateType = manipulateType
    
    @tv.returns((StreamDirection, tv.listOf(StreamDirection)))
    def direction(self):
        return self._direction
    
    @tv.returns(type)
    def manipulateType(self):
        return self._manipulateType
    
