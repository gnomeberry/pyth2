'''
Created on 2016/03/03

@author: oreyou
'''
from pyth2.deco import Decorators
from pyth2.concurrent import Concurrent
import time

DEFAULT_EXECUTOR = Concurrent.Executor(True, None)

class AsyncProxy(object):
    
    def __init__(self, generatorFunc, group = None):
        group = group if not group is None else DEFAULT_EXECUTOR
        if not isinstance(group, Concurrent.Executor):
            raise ValueError("%s is not Executor" % group)
        self.__func = generatorFunc
        self.__group = group
    
    def __call__(self, *args, **kwds):
        return self.__group.submit(self.__func, *args, **kwds)

async = Decorators.ConsProxy(AsyncProxy)

if __name__ == "__main__":
    import urllib2
    @async()
    def contents(url):
        return urllib2.urlopen(url).read()
    
    hoge = async()(lambda x: time.sleep(x))
    
    c1 = contents(r"http://www.google.co.jp/")
    print c1
    c2 = contents(r"http://www.bing.com/")
    print c2
    
    print c1().decode("utf8")
    print c2()
    print hoge(1)()
