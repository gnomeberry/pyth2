'''
Created on 2016/02/25

@author: oreyou
'''
from abc import abstractmethod
from threading import Lock

from pyth2.concurrent import Synchronized
from pyth2.enum.SafeEnum import enumOf


TASK_STATUS = enumOf(int, "TaskStatus", WAITING = 0, RUNNING = 1, CANCELLED = 2, COMPLETE = 3)

TODO

class TaskError(Exception):
    pass

class Executor(object):
    
    def __init__(self, daemonize = True, poolMaxSize = None):
        self.__submittionLock = Lock()
        self.__pool = []
        self.__submitted = []
        self.__namedSubmitted = {}
        self.__daemonize = daemonize
        self.__maxSize = poolMaxSize
    
    @property
    def daemonize(self):
        return self.__daemonize
    
    def submit(self, someCallable, name = None):
        f = Future(self, someCallable)
        try:
            self.__submittionLock.acquire()
            if name is None:
                self.__submitted.append(f)
            elif not name in self.__namedSubmitted:
                self.__namedSubmitted[name] = f
            else:
                raise ValueError("Task name %s already submitted" % name)
        finally:
            self.__submittionLock.release()
    
    def __acception(self):
        

class Task(object):
    
    def __init__(self, functionBody, *args, **kwds):
        if not callable(functionBody):
            raise ValueError("%s is not callable" % functionBody)
        
        self.function = functionBody
        self.args = args
        self.kwds = kwds
    
    def __call__(self, *partialArgs, **partialKwds):
        args = self.args
        if partialArgs:
            args += partialArgs
        
        kwds = self.kwds
        if partialKwds:
            kwds = dict(self.kwds)
            kwds.update(partialKwds)
        return self.function(*args, **kwds)

class Future(object):
    
    __lockObject = Lock()
    
    def __init__(self, executor, task):
        self.__task = task
        self.__taskArgs = taskArgs
        self.__taskKwds = taskKwds
        self.__status = TASK_STATUS.WAITING
    
    @Synchronized.synchronized(__lockObject)
    def run(self, *partialArgs, **partialKwds):
        if self.__status != TASK_STATUS.WAITING:
            raise TaskError("Already started or exited task: status = %s" % self.__status)
        
        self.__status = TASK_STATUS.RUNNING
        
        
    