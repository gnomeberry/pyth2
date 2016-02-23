'''
Created on 2015/11/07

@author: _
'''
from pyth2.contracts import TypeValidator as tv
from pyth2.io.Stream import StreamDirection, Stream


class CharStream(Stream):
    '''
    A character stream
    '''
    
    @tv.forms(object, StreamDirection, str)
    def __init__(self, direction, encoding):
        super(CharStream, self).__init__(direction, unicode)
        self._encoding = encoding
    
    @tv.returns(str)
    def encoding(self):
        return self._encoding
    
