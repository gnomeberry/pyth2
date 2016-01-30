# encoding: utf-8
'''
Created on 2016/01/24

@author: oreyou
'''
import codecs
import json
import os
import sys


FILESYSTEM_CHARACTER_ENCODING = sys.getfilesystemencoding()
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

class FilesystemView(FilesystemBoundObject):
    
    def __init__(self, stage, files, autoCommit):
        super(FilesystemView, self).__init__(False)
        self.__stage = stage
        self.__files = tuple(files)
        self.autoCommit = autoCommit
    
    def assocFile(self):
        return self.__stage.assocFile()
    
    def listFiles(self, sort_comparator = None):
        if callable(sort_comparator):
            return tuple(sorted(self.__files, cmp = sort_comparator))
        else:
            return self.__files
    
    def commit(self):
        self.__stage.__commit_currentView(self)
    
    def __enter__(self):
        pass
    
    def __exit__(self, excType, excInstance, excTrace):
        if not excInstance:
            raise
        elif self.autoCommit:
            self.commit()

class Stages(object):
    '''
    Stageをまとめたもの
    '''
    
    baseDirectory = None
    stages = []
    
    def __init__(self, baseDirectory):
        self.baseDirectory = unicode(baseDirectory, FILESYSTEM_CHARACTER_ENCODING) if not isinstance(baseDirectory, unicode) else baseDirectory
        ensureDirectory(self.baseDirectory)
        
    def addStage(self, stageName = "", changeBaseDir = None):
        if changeBaseDir:
            changeBaseDir = unicode(changeBaseDir, FILESYSTEM_CHARACTER_ENCODING) if not isinstance(changeBaseDir, unicode) else changeBaseDir
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
        
        def __init__(self, stage):
            super(stage.StageContext, self).__init__(True)
            self.stage = stage
            self.__frozen = self.__dict__.keys() + ["_StageContext__frozen"]
        
        def assocFile(self):
            return os.path.join(self.stage._baseDirectory, STAGING_CONTEXT_FILE_PATTERN % self.stage._name)
        
        def __attributes(self):
            return {k: getattr(self, k) for k in self.__dict__ if not k in self.__frozen}
        
        def __contains__(self, k):
            return hasattr(self, k)
        
        def clear(self):
            for k in [_ for _ in self.__dict__ if not _ in self.__frozen]:
                delattr(self, k)
        
        def store(self):
            self.ensureFile()
            with codecs.open(self.assocFile(), "wb", "utf-8", buffering = 1) as fp:
                json.dump(self.__attributes(), fp, indent = 4)
        
        def load(self):
            self.ensureFile()
            self.clear()
            with codecs.open(self.assocFile(), "rb", "utf-8", buffering = 1) as fp:
                for k, v in json.load(fp).items():
                    setattr(self, k, v)
    
    def __init__(self, stageManager, baseDirectory, name):
        super(Stage, self).__init__(False)
        if not stageManager:
            raise ValueError("Must specify stage manager")
        if not name:
            raise ValueError("%s is not valid for stage name" % name)
        self.__stageManager = stageManager
        self._name = unicode(name, FILESYSTEM_CHARACTER_ENCODING) if not isinstance(name, unicode) else name
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
    
    def currentView(self, pathSelector = None, autoCommit = False):
        files = (os.path.join(self.__stageDirectory, (unicode(fpath, FILESYSTEM_CHARACTER_ENCODING) if not isinstance(fpath, unicode) else fpath)) for fpath in os.listdir(self.assocFile()))
        if pathSelector and callable(pathSelector):
            files = (fpath for fpath in files if pathSelector(fpath))
        return FilesystemView(self, list(files), autoCommit)
    
    def __commit_currentView(self, filesystemView):
        print "Commit current view", filesystemView.listFiles()
        nextStage = self.nextStage()
        print "Next stage=%s" % nextStage
        if nextStage:
            pass
        else:
            # delete?
            pass
    
if __name__ == "__main__":
    x=Stages("z:\\hoge")
    print x.baseDirectory
    stage1 = x.addStage("stage1")
    ctx = stage1.context()
    ctx.load()
    if "initial" in ctx:
        print ctx.val1, ctx.val2
    ctx.initial = False
    ctx.val1 = 1
    ctx.val2 = "abc"
    ctx.store()
    ctx.clear()
    print ctx.val1
    fsv = stage1.currentView()
    for fn in fsv.listFiles(fileRegexComparator(r"(.*)(\d+).*$", True, False, unicode, int)):
        print fn
