# encoding: utf-8
'''
Created on 2016/02/25

@author: _
'''

from pyth2.enum.SafeEnum import enumOf
import threading
import weakref
import sys
import random
import time
import Queue


TASK_STATUS = enumOf(int, "TaskStatus",
    WAITING = 0,
    RUNNING = 1,
#     CANCELLED = 2,
    COMPLETE = 3)

THREAD_LIFETIME = 3 # seconds

class TaskError(Exception):
    pass

class Executor(object):
    
    class WrappedThread(threading.Thread):
        
        def __init__(self, parent):
            threading.Thread.__init__(self)
            self.__parent = parent
            self.__taskQueue = Queue.Queue()
            self.__exitLoop = False
        
        def replace(self, task):
            self.__taskQueue.put(task, True)
        
        def terminate(self): # no way to forcibly abort..?
            self.__exitLoop = True
        
        def run(self):
            while not self.__exitLoop:
                try:
                    currentTask = self.__taskQueue.get(True, timeout = THREAD_LIFETIME)
                    self.currentTask = None
#                     print "(EXECUTE %s, %s)" % (currentTask.args, id(self))
                    currentTask()
                except Queue.Empty:
                    # Cannot obtain next task
                    break
                except:
                    # unhandled exception
                    if callable(self.__parent.unhandledExceptionHandler):
                        self.__parent.unhandledExceptionHandler(self, currentTask)
                self.__parent._detatchThread(self)
#             print "(UNASSOCIATE Thread %s)" % id(self)
            self.__parent._purgeThread(self)
    
    def __init__(self, daemonize = True, poolMaxSize = None, unhandledExceptionHandler = None):
        if not poolMaxSize is None and int(poolMaxSize) <= 0:
            raise ValueError("Pool max size must be more than 0")
        
        self.unhandledExceptionHandler = unhandledExceptionHandler
        self.__pool = set()
        self.__poolCondition = threading.Condition()
        self.__submitted = Queue.Queue()
#         self.__namedSubmitted = {}
        self.__daemonize = daemonize
        self.__creationTime = 0
        self.__maxSize = int(poolMaxSize) if not poolMaxSize is None else None
        
        self.__worker = threading.Thread(target = self.__acception)
        self.__worker.daemon = True
        with self.__poolCondition:
            self.__worker.start()
    
    def _detatchThread(self, wrappedThread):
        with self.__poolCondition:
            self.__pool.add(wrappedThread)
            self.__poolCondition.notifyAll()
    
    def _purgeThread(self, wrappedThread):
        with self.__poolCondition:
            self.__pool.remove(wrappedThread)
            self.__poolCondition.notifyAll()
            self.__creationTime -= 1
    
    def _takeThread(self):
        with self.__poolCondition:
            if self.__pool:
                return self.__pool.pop()
            
            if self.__maxSize is None or self.__creationTime < self.__maxSize:
                t = self.WrappedThread(self)
                t.start()
                self.__creationTime += 1
                return t
            else:
                # wait for free thread
                while len(self.__pool) == 0:
                    self.__poolCondition.wait()
                return self.__pool.pop()
    
    @property
    def daemonize(self):
        return self.__daemonize
    
    def submit(self, someCallable, *args, **kwds):
#         print "(SUBMITTED %s)" % args
        task = Task(someCallable, *args, **kwds)
        future = Future(task)
        task._setFuture(future)
        self.__submitted.put(task)
        return future
    
    def __acception(self):
        while True:
            last = self.__submitted.get()
            t = self._takeThread()
#             print "(Accepted %s, thread=%s)" % (last.args, id(t))
            t.replace(last)
            self.__submitted.task_done()

class Task(object):
    
    def __init__(self, functionBody, *args, **kwds):
        if not callable(functionBody):
            raise ValueError("%s is not callable" % functionBody)
        
        self.function = functionBody
        self.args = args
        self.kwds = kwds
        self.__future = None
    
    def _setFuture(self, strongRefFuture):
        self.__future = weakref.ref(strongRefFuture)
    
    def __call__(self):
        resultPair = None
        try:
            resultPair = (self.function(*self.args, **self.kwds), None)
        except:
            resultPair = (None, sys.exc_info())
            sys.exc_clear()
        
        maybeRef = self.__future() if not self.__future is None else None
        if maybeRef:
            maybeRef._Future__taskCompleted(*resultPair)
        return resultPair

class Future(object):
    
    def __init__(self, task):
        self.__task = task
        self.__status = TASK_STATUS.WAITING
        self.__result = None
        self.__excInfo = None
        self.__completedCondition = threading.Condition()
    
    def __taskCompleted(self, result, excInfo = None):
        self.__result = result
        self.__excInfo = excInfo
        self.__setStatus(TASK_STATUS.COMPLETE)
    
    @property
    def task(self):
        return self.__task
    
    @property
    def status(self):
        with self.__completedCondition:
            return self.__status
    
    def __setStatus(self, status):
        with self.__completedCondition:
            self.__status = status
            self.__completedCondition.notifyAll()
    
    @property
    def completed(self):
        with self.__completedCondition:
            return self.__status == TASK_STATUS.COMPLETE
    
    def cancel(self):
        # TODO
        pass
    
    def get(self, timeout = None):
        result, exc_info = self.getSafe(timeout)
        if exc_info:
            raise exc_info[0], exc_info[1], exc_info[2]
        else:
            return result
    
    def getSafe(self, timeout = None):
        with self.__completedCondition:
            while self.__status != TASK_STATUS.COMPLETE:
                self.__completedCondition.wait(timeout)
                pass
            
            return self.__result, self.__excInfo

if __name__ == "__main__":
    ex = Executor(True, 5)
    def heavyTask(taskId):
        n = random.randint(10, 1000)
        print "(TASK %2d await %s msec)" % (taskId, n)
        time.sleep(n / 1000.0)
        print "(TASK %2d exit)" % taskId
        return taskId
    futures = [ex.submit(heavyTask, i) for i in xrange(20)]
    terms = []
    for f in futures:
        terms.append(f.get())
        print terms
    print "TERMINATED, waiting"
    time.sleep(THREAD_LIFETIME + 1)
    t = Task(lambda a, b: a / b, 1, 0)
    print t()
