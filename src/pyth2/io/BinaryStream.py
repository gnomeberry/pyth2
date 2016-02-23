'''
Created on 2015/11/07

@author: _
'''
from types import NoneType

from pyth2.contracts import TypeValidator as tv
from pyth2.io.Stream import Stream, StreamDirection


class BinaryStream(Stream):
    
    @tv.forms(object, StreamDirection)
    def __init__(self, direction):
        super(BinaryStream, self).__init__(direction, bytearray)
        
    @tv.forms(object, tv.MoreThan(0, False))
    @tv.returns((bytearray, NoneType))
    @tv.raises(IOError)
    def read(self, bufferSize = 1):
        raise Exception("Not implemented")
    
    @tv.forms(object, bytearray)
    @tv.raises(IOError)
    def write(self, contents):
        raise Exception("Not implemented")
