# encoding: utf-8
'''
Created on 2016/01/24



@author: oreyou
'''
import os
import codecs
import encodings
import json


STAGING_CONTEXT_FILE_PATTERN = "%s_context"

def ensureDirectory(path):
    if not os.path.isdir(path):
        os.mkdir(path)
        if not os.path.isdir(path):
            raise ValueError("Cannot ensure directory(s) %s" % path)
    return True

def ensureFile(path):
    if os.path.isfile(path):
        return True
    ensureDirectory(os.path.join(path, os.pardir))
    with open(path, "w") as f:  # @UnusedVariable
        pass
    if os.path.isfile(path):
        return True
    else:
        raise ValueError("Cannot ensure file %s" % path)

def fileDateComparator(dateFunctor):
    def comparator(f1, f2):
        return dateFunctor(f1) < dateFunctor(f2)
    return comparator

def fileRegexComparator(regex, onlyBaseName = True, errorOnMismatch = True, *foundTranslators):
    import re
    pat = re.compile(regex, re.DOTALL)
    def comparator(f1, f2):
        m1 = pat.match(os.path.basename(f1) if onlyBaseName else f1)
        m2 = pat.match(os.path.basename(f2) if onlyBaseName else f2)
        if errorOnMismatch:
            if not m1:
                raise ValueError("Mismatch %s for %s" % (f1, regex))
            if not m2:
                raise ValueError("Mismatch %s for %s" % (f2, regex))
        g1 = [] if not m1 else m1.groups()
        g2 = [] if not m2 else m2.groups()
        if len(g1) != len(g2):
            return len(g1) - len(g2)
        else:
            for i, s in enumerate(zip(g1, g2)):
                s = map(foundTranslators[i], s) if i < len(foundTranslators) else s
                c = cmp(s[0], s[1])
                if c != 0:
                    return c
            return 0
    return comparator


class FilesystemBoundObject(object):
    
    def __init__(self, isFileObject = True):
        self.isFileObject = isFileObject
    
    def assocFile(self):
        raise ValueError("Abstract method")
    
    def ensureFile(self):
        if self.isFileObject:
            ensureFile(self.assocFile())
        else:
            ensureDirectory(self.assocFile())

class Stages(object):
    '''
    Stageをまとめたもの
    '''
    
    baseDirectory = None
    stages = []
    
    def __init__(self, baseDirectory):
        self.baseDirectory = unicode(baseDirectory)
        ensureDirectory(self.baseDirectory)
        
    def addStage(self, stageName = "", changeBaseDir = None):
        if changeBaseDir:
            ensureDirectory(changeBaseDir)
        else:
            changeBaseDir = self.baseDirectory
        
        stage = Stage(self, changeBaseDir, stageName)
        if stage in self.stages:
            raise ValueError("%s is already exist in %s" % (stage, self.stages))

        self.stages.append(stage)
        return stage
    
    def __contains__(self, val):
        return val in self.stages
    
    def findStageIndex(self, stageName):
        for i, s in enumerate(self.stages):
            if s._name == stageName:
                return i
        return None
    
class Stage(FilesystemBoundObject):
    
    __stageManager = None
    _name = ""
    
    class StageContext(FilesystemBoundObject):
        
        obj = dict()
        
        def __init__(self, stage):
            super(stage.StageContext, self).__init__(True)
            self.stage = stage
        
        def assocFile(self):
            return os.path.join(self.stage._baseDirectory, STAGING_CONTEXT_FILE_PATTERN % self.stage._name)
        
        def store(self):
            self.ensureFile()
            with codecs.open(self.assocFile(), "wb", "utf-8", buffering = 1) as fp:
                json.dump(self.obj, fp, indent = 4)
        
        def load(self):
            self.ensureFile()
            try:
                with codecs.open(self.assocFile(), "rb", "utf-8", buffering = 1) as fp:
                    self.obj = json.load(fp)
            except:
                self.obj = dict()
            return self.obj
    
    def __init__(self, stageManager, baseDirectory, name):
        super(Stage, self).__init__(False)
        if not stageManager:
            raise ValueError("Must specify stage manager")
        if not name:
            raise ValueError("%s is not valid for stage name" % name)
        self.__stageManager = stageManager
        self._name = unicode(name)
        self._baseDirectory = baseDirectory
        self.__stageDirectory = os.path.join(self._baseDirectory, self._name)
        self.__context = self.StageContext(self)
        ensureDirectory(self.__stageDirectory)
    
    def __str__(self, *args, **kwargs):
        return "Stage[%s, dir=%s]" % (self._name, self.__stageDirectory)
    
    def __eq__(self, other):
        return isinstance(other, Stage) and other._name == self._name
    
    def __hash__(self, *args, **kwargs):
        return self._name.__hash__()
    
    def assocFile(self):
        return self.__stageDirectory
    
    def stageManager(self):
        return self.__stageManager
    
    def stageName(self):
        return self._name
    
    def previousStage(self):
        index = self.__stageManager.findStageIndex(self._name)
        if index:
            return self.__stageManager.stage[index - 1] if index >= 1 else None
    
    def nextStage(self):
        index = self.__stageManager.findStageIndex(self._name)
        if index:
            return self.__stageManager.stage[index + 1] if index <= len(self.__stageManager) - 1 else None
    
    def context(self):
        return self.__context
    
    def listFiles(self, sort_comparator = None):
        entries = os.listdir(self.assocFile())
        if callable(sort_comparator):
            return sorted(entries, cmp = sort_comparator)
        else:
            return entries

x=Stages("z:\\hoge")
print x.baseDirectory
stage1 = x.addStage("stage1")
ctx = stage1.context().load()
ctx["val1"] = 1
ctx["val2"] = "abc"
stage1.context().store()
