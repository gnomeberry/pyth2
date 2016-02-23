#coding: UTF-8
'''
Created on 2016/02/09

@author: _
'''
import sys
from pyth2.fs.Path import Path
import os

def main(*args):
    for fpath in map(Path, args[1:]):
        if not os.path.isfile(fpath):
            print "%s is not a file" % fpath
            continue
        
        
    pass

if __name__ == "__main__":
    main(*sys.argv)

