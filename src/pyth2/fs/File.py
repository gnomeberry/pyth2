# -*- coding: utf-8 -*-
'''
Created on 2015/11/05

@author: _
'''

import os
from types import NoneType

import os.path as ospath
from pyth2.contracts import TypeValidator as tv
from pyth2.fs.Path import normalizeDirectorySeparator, DIRECTORY_SEP_UNICODE, Path


DEFAULT_TEXT_FILE_ENCODING = "utf-8"
Splittable = tv.hasattrTypeValidator("Splitable", "split")
Searchable = tv.hasattrTypeValidator("Searchable", "search")

class File(object):
    '''
    A class represents a file or directory in filesystem
    '''

    @tv.forms(object, (basestring, Path))
    def __init__(self, path):
        self._path = path if isinstance(path, Path) else Path(path)
    
    def __str__(self):
        return "File(%s)" % str(self._path.toUnicodePath())
    
    @tv.returns(Path)
    def path(self):
        return self._path
    
    @tv.returns(bool)
    def isFile(self):
        return ospath.isfile(self._path.toNativeUnicodePath())
    
    @tv.returns(bool)
    def isDirectory(self):
        return ospath.isdir(self._path.toNativeUnicodePath())
    
    @tv.returns(bool)
    def exists(self):
        return ospath.exists(self._path.toNativeUnicodePath())
    
    @tv.forms(object, (basestring, Searchable), bool)
    def findPattern(self, regex = u"", subdir = True):
        if not Searchable.isValid(regex):
            import re
            regex = re.compile(regex, re.DOTALL)
        basePath = self._path.toNativeUnicodePath()
        basePathLen = len(basePath)
        
        for dpath, dnames, fnames in os.walk(basePath, True, followlinks = True):
            dpath = unicode(dpath)
            if regex.search(normalizeDirectorySeparator(dpath[basePathLen:])):
                yield File(dpath)
            relativePath = unicode(dpath[basePathLen:])
            for path in [dpath + DIRECTORY_SEP_UNICODE + unicode(filename) for filename in fnames]:
                if regex.search(path[basePathLen:]):
                    yield File(path)
            if not subdir:
                return
    
    @tv.forms(object, str)
    @tv.returns(tv.Withable)
    def openText(self, encoding = DEFAULT_TEXT_FILE_ENCODING):
        pass
    
    @tv.forms(object, (basestring, Splittable), str)
    @tv.raises(IOError)
    def split(self, regex = u"((\r\n)|\r|\n)", encoding = DEFAULT_TEXT_FILE_ENCODING):
        if not isinstance(regex, basestring) and hasattr(regex, "split"):
            return regex.split(self.textReadAll(encoding))
        else:
            try:
                import re
                regex = re.compile(regex, re.DOTALL | re.MULTILINE)
                return regex.split(self.textReadAll(encoding))
            except:
                raise IOError("Cannot load regex module")
        
    @tv.forms(encoding = str)
    @tv.returns(basestring)
    @tv.raises(IOError)
    def textReadAll(self, encoding = DEFAULT_TEXT_FILE_ENCODING):
        try:
            import codecs
            with codecs.open(self._path.toNativeUnicodePath(), "r", encoding) as f:
                return f.read()
        except IOError as e:
            raise e
        except:
            raise IOError("Cannot load codecs module")
        
    def binaryOpen(self):
        pass
    
    @tv.forms(object, (int, long, NoneType))
    @tv.returns(buffer)
    def binaryReadAll(self, sizeLimit = None):
        pass
    
