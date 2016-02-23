# encoding: utf-8
'''
Created on 2015/11/07

@author: _
'''
from pyth2.contracts import TypeValidator as tv
from pyth2.fs.Path import Path


class LiveFile(object):
    '''
    classdocs
    '''
    
    @tv.forms(object, Path)
    def __init__(self, path):
        '''
        Constructor
        '''
        path.toNativeUnicodePath()
        