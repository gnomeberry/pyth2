# encoding: utf-8

import os.path as ospath
from pyth2.contracts import TypeValidator as tv


# from pyth.fs.File import File
DIRECTORY_SEP_UNICODE = u"/"
NATIVE_DIRECTORY_SEP_UNICODE = unicode(ospath.sep)
EXTENSION_CHAR = unicode(ospath.extsep)

@tv.forms(basestring)
@tv.returns(unicode)
def normalizeDirectorySeparator(path):
    '''
    Normalizes directory separator characters of the path to DIRECTORY_SEP_PATH
    
    @param path: a path string
    @return: normalized path
    '''
    return unicode(path).replace(NATIVE_DIRECTORY_SEP_UNICODE, DIRECTORY_SEP_UNICODE)

class Path(object):
    '''
    A class represents a path string
    '''

    @tv.forms(object, (str, unicode))
    @tv.raises(ValueError)
    def __init__(self, path, *pathes):
        if len(path) == 0:
            raise ValueError("Empty string path is invalid")
        else:
            self._pathes = normalizeDirectorySeparator(path).split(DIRECTORY_SEP_UNICODE)
        
        if len(pathes) > 0:
            self._pathes += map(unicode, pathes)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.toStringPath()
    
    def __unicode__(self):
        return self.toUnicodePath()
    
    @tv.returns(bool)
    def isAbsolute(self):
        return ospath.isabs(self.toUnicodePath())
    
    @tv.returns(object)
    def toAbsolute(self):
        return Path(ospath.abspath(ospath.expanduser(ospath.expandvars(self.toUnicodePath()))))
    
    @tv.returns(bool)
    def isRoot(self):
        return self.isAbsolute() and (self._pathes) == 0
    
    @tv.returns(object)
    @tv.raises(IOError)
    def rootPath(self):
        if not self.isAbsolute():
            raise IOError(u"Cannot locate root path, %s is not absolute path" % self.toUnicodePath())
        result = Path("tmp")
        result._pathes = [self._pathes[0]]
        return result
    
#     @tv.returns(File)
#     def toFile(self):
#         return File(self)
    
    @tv.returns(unicode)
    def toNativeUnicodePath(self):
        return self.toUnicodePath().replace(DIRECTORY_SEP_UNICODE, NATIVE_DIRECTORY_SEP_UNICODE)
    
    @tv.returns(unicode)
    def toUnicodePath(self):
        result = DIRECTORY_SEP_UNICODE.join(self._pathes)
        if len(self._pathes) == 1:
            result += DIRECTORY_SEP_UNICODE
        return result
    
    @tv.returns(str)
    def toNativeStringPath(self):
        return str(self.toNativeUnicodePath())
    
    @tv.returns(str)    
    def toStringPath(self):
        return str(self.toUnicodePath())
    
    @tv.forms(object, basestring, children = tv.Iterable)
    @tv.returns(object)
    def childOf(self, child, *children):
        ret = Path("tmp")
        ret._pathes = list(self._pathes)
        ret._pathes.append(unicode(child))
        ret._pathes += map(unicode, children)
        return ret
    
    @tv.returns(object, bool)
    @tv.raises(ValueError)
    def parent(self, noCheckRoot = True):
        if len(self._pathes) == 1:
            if not noCheckRoot:
                raise ValueError(u"Cannot locate parent path of " + self.toUnicodePath())
            else:
                return self
        ret = Path("tmp")
        ret._pathes = self._pathes[:-1]
        return ret
    
    @tv.returns(unicode)
    def baseName(self):
        return self._pathes[-1]
    
    @tv.returns(unicode)
    def baseNameWithoutExtension(self):
        splitedBaseName = self.baseName().split(EXTENSION_CHAR)
        return self.baseName() if len(splitedBaseName) == 1 else EXTENSION_CHAR.join(splitedBaseName[:-1])
    
    @tv.forms(object, basestring)
    @tv.returns(unicode)
    def baseNameWithExtension(self, newExtension = u""):
        return self.baseNameWithoutExtension() + EXTENSION_CHAR + unicode(newExtension)
    
    @tv.returns(object)
    def pathWithoutExtension(self):
        result = Path("tmp")
        result._pathes = list(self._pathes[:-1]) + [self.baseNameWithoutExtension()]
        return result
    
    @tv.forms(object, basestring)
    @tv.returns(object)
    def pathWithExtension(self, newExtension = u""):
        result = Path("tmp")
        result._pathes = list(self._pathes[:-1]) + [self.baseNameWithExtension(newExtension)]
        return result
