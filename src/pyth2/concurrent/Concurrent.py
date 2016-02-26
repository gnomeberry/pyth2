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

WORKER_THREAD_LIFETIME = 3 # seconds

class TaskError(Exception):
    pass

class FutureError(Exception):
    pass

class Executor(object):
    """
    Simple thread-pool based executor.
    """
    
    class WrappedThread(threading.Thread):
        """
        Threads for Executor
        """
        def __init__(self, parent):
            threading.Thread.__init__(self)
            self.__parent = parent
            self.__taskQueue = Queue.Queue()
            self.__exitLoop = False
        
        def addTask(self, task):
            """
            Adds a task into this thread.
            
            @param task: a task
            """
            self.__taskQueue.put(task, True)
        
        def terminate(self): # no way to forcibly abort..?
            """
            Sets termination flag to True
            """
            self.__exitLoop = True
        
        def run(self):
            while not self.__exitLoop:
                try:
                    currentTask = self.__taskQueue.get(True, timeout = WORKER_THREAD_LIFETIME)
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
                self.__parent._detachThread(self)
#             print "(UNASSOCIATE Thread %s)" % id(self)
            self.__parent._purgeThread(self)
    
    def __init__(self, daemonize = True, poolMaxSize = None, unhandledExceptionHandler = None, taskType = None):
        """
        Initializer
        
        @param daemonize: all threads are daemon thread if True 
        @param poolMaxSize: maximum number of threads are spawn if the argument is natural(more than 1 integral) number, or number of demand threads are spawn if None
        @param unhandledExceptionHandler: a function which is invoked at a unhandled exception has occurred(forms like (lambda worker_thread, task: ..)), or exception are ignored if None
        @param taskType: subtype of Task which is used for creation of new Task
        """
        if not poolMaxSize is None and int(poolMaxSize) <= 0:
            raise ValueError("Pool max size must be more than 0")
        
        self.__pool = set()
        self.__poolCondition = threading.Condition()
        self.__submitted = Queue.Queue()
#         self.__namedSubmitted = {}
        self.__daemonize = daemonize
        self.__creationTime = 0
        self.__maxSize = int(poolMaxSize) if not poolMaxSize is None else None
        
        self.unhandledExceptionHandler = unhandledExceptionHandler
        self.taskType = taskType if isinstance(taskType, Task) else Task
        
        self.__worker = threading.Thread(target = self.__acception)
        self.__worker.daemon = True
        with self.__poolCondition:
            self.__worker.start()
    
    def _detachThread(self, wrappedThread):
        """
        (internal) Adds thread into thread pool
        """
        with self.__poolCondition:
            self.__pool.add(wrappedThread)
            self.__poolCondition.notifyAll()
    
    def _purgeThread(self, wrappedThread):
        """
        (internal) Purges thread from thread pool
        """
        with self.__poolCondition:
            self.__pool.remove(wrappedThread)
            self.__poolCondition.notifyAll()
            self.__creationTime -= 1
    
    def _takeThread(self):
        """
        (internal) Takes next available thread from thread pool, or creates new thread if no threads in the thread pool and the pool has space
        """
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
        """
        True if threads in thread pool are daemonized
        """
        return self.__daemonize
    
    def submit(self, someCallable, *args, **kwds):
        """
        Submits a new task into the Executor
        
        @param someCallable: callable object to be wrapped into Task object or subtype of self.taskType object
        @param args: positional arguments for the callable object
        @param kwds: keyword arguments for the callable object
        @return: new Future object
        """
#         print "(SUBMITTED %s)" % args
        task = self.taskType(someCallable, *args, **kwds) if not isinstance(someCallable, self.taskType) else someCallable
        future = Future(task)
        task._setFuture(future)
        self.__submitted.put(task)
        return future
    
    def __acception(self):
        """
        (internal private) Takes available threads and throw next task into the threads
        """
        while True:
            last = self.__submitted.get()
            t = self._takeThread()
#             print "(Accepted %s, thread=%s)" % (last.args, id(t))
            t.addTask(last)
            self.__submitted.task_done()

class Task(object):
    """
    Represents a "Task".
    Task object is null-ary callable object and if and only if results are filled when is invoked.
    
    Results can be obtain by "getSafe" and "get" method when "isDone" method returns True(i.e "getSafe" and "get" can raise TaskError if task is incomplete).
    "getSafe" is exception free and this method returns a pair of (task result, exc_info).
    "get" returns if and only if 2nd value of the return value of "getSafe" is NOT None, or raises exception(2nd value) if the 2nd value IS None.
    
    All methods are thread-safety.
    """
    def __init__(self, taskBody, *args, **kwds):
        """
        Initializer
        
        @param taskBody: task body function
        @param args: positional arguments of the taskBody
        @param kwds: keyword arguments of the taskBody
        @raise ValueError: the taskBody is not callable
        """
        if not callable(taskBody):
            raise ValueError("%s is not callable" % taskBody)
        
        self.function = taskBody
        self.args = args
        self.kwds = kwds
        self.__resultPair = None
        self.__future = None
        self.__then = None
        self.__completeCondition = threading.Condition()
    
    def isDone(self):
        """
        Returns True if the task is completed.
        """
        with self.__completeCondition:
            return not self.__resultPair is None
    
    def await(self, timeout = None):
        """
        Awaits by threads.Condition.wait method while the task is incomplete.
        
        @param timeout: a timeout value in seconds.
        @see threads.Condition.wait
        """
        with self.__completeCondition:
            while self.__resultPair is None:
                self.__completeCondition.wait(timeout)
    
    def getSafe(self):
        """
        Returns task results in the form of a pair of (task result, exc_info)
        
        @return: a pair of (task result, exc_info)
        """
        with self.__completeCondition:
            if self.__resultPair is None:
                #raise TaskError("%s is not done" % self)
                return self.__call__()
            return self.__resultPair
    
    def get(self):
        """
        Returns task results or raises exception.
        
        @return: a results of the task
        @raise: exception if the task is done with unhandled exception
        """
        resultPair = self.getSafe()
        if not resultPair[1] is None:
            raise resultPair[1][0], resultPair[1][1], resultPair[1][2]
        else:
            return resultPair[0]
    
    def then(self, thenBody, *args, **kwds):
        """
        Appends then-clause into this task.
        The then-clause is performed after task body and chain of then-clause in series if no exception raises.
        Last then-clause results are introduced as task results.
        
        @param thenBody: then-clause body function(forms like lambda lastResult, *args, **kwds: ..)
        @param args: positional arguments of thenBody
        @param kwds: keyword arguments of thenBody
        @return: this Task object
        """
        with self.__completeCondition:
            if self.__resultPair:
                raise TaskError("Task is already done")
            
            thenParam = (thenBody, args, kwds)
            if self.__then is None:
                self.__then = [thenParam]
            else:
                self.__then.append(thenParam)
            
            return self
    
    def _setFuture(self, strongRefFuture):
        """
        (internal) sets associated Future object by weakref
        """
        self.__future = weakref.ref(strongRefFuture)
    
    def __call__(self):
        """
        Perform tasks and returns results in the form of like "getSafe" method.
        The task is performed if and only if first time invocation.
        
        @return: a pair of (task result, exc_info)
        """
        with self.__completeCondition:
            if not self.__resultPair is None:
                return self.__resultPair
            
            try:
                partialResult = self.function(*self.args, **self.kwds)
                if not self.__then is None:
                    for thenParam in self.__then:
                        partialResult = thenParam[0](partialResult, *thenParam[1], **thenParam[2])
                self.__resultPair = (partialResult, None)
            except:
                self.__resultPair = (None, sys.exc_info())
                sys.exc_clear()
            
            self.__completeCondition.notifyAll()
            maybeRef = self.__future() if not self.__future is None else None
            if maybeRef:
                maybeRef._markCompleted()
            return self.__resultPair

class Future(object):
    """
    Represents Future pattern.
    Future is a results of corresponding task in this context.
    """
    
    def __init__(self, task):
        """
        Initializer
        
        @param task: Task object which to be performed in the future
        """
        self.__task = task
        self.__completed = False
        self.__completedCondition = threading.Condition()
    
    def _markCompleted(self):
        """
        (internal) Marks this future object is decided
        """
        with self.__completedCondition:
            self.__completed = True
            self.__completedCondition.notifyAll()
    
    @property
    def task(self):
        """
        Associated Task object
        """
        return self.__task
    
    @property
    def completed(self):
        """
        Whether this future object is decided
        """
        with self.__completedCondition:
            return self.__completed
    
    def cancel(self):
        # TODO
        pass
    
    def getSafe(self, timeout = None):
        """
        Returns associated Task object's results.
        This method may be blocking while the Task object is performed.
        
        @param timeout: timeout in seconds
        @return: the results of the associated Task object
        @see: threading.Condition.wait
        @see: Task.getSafe
        """
        with self.__completedCondition:
            while not self.__completed:
                self.__completedCondition.wait(timeout)
            
            return self.__task.getSafe()
    
    def get(self, timeout = None):
        """
        Return associated Task object's results, or raises exception if the Task object is done in anomaly.
        This method may be blocking while the Task object is performed.
        
        @param timeout: timeout in seconds
        @return: the results of the associated Task object
        @raise: exception if the task is done with unhandled exception
        @see: threading.Condition.wait
        """
        result, exc_info = self.getSafe(timeout)
        if exc_info:
            raise exc_info[0], exc_info[1], exc_info[2]
        else:
            return result

if __name__ == "__main__":
    ex = Executor(True, 10)
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
    time.sleep(WORKER_THREAD_LIFETIME + 1)
    print "May all worker threads are dead"
    
    def fooTask(a, b):
        a = float(a)
        b = float(b)
        c = a / b
        print "%f/%f = %f" % (a, b, c)
        return c
    t = Task(fooTask, 3, 2).then(fooTask, 2).then(fooTask, 1).then(fooTask, 0)
    print t.get()
