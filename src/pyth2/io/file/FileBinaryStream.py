'''
Created on 2015/11/07

@author: _
'''
import os
from types import NoneType

from pyth2.contracts.TypeValidator import TypeValidator as tv
from pyth2.fs import Path
from pyth2.io.BinaryStream import BinaryStream
from pyth2.io.Stream import StreamDirection


class FileBinaryStream(BinaryStream):
    '''
    A binary stream for native FileSystem
    '''
    
    @tv.forms(object, Path, StreamDirection)
    def __init__(self, path, direction):
        '''
        Initializer
        '''
        super(FileBinaryStream, self).__init__(direction)
        self._path = path
    
    @tv.forms(object, tv.MoreThan(0, False))
    @tv.returns((bytearray, NoneType))
    @tv.raises(IOError)
    def read(self, bufferSize=1):
        buf = bytearray(bufferSize)
        with os.open(aaa, >>>)
