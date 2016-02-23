'''
Created on 2016/01/27

@author: _
'''
import StringIO

try:
    import cPickle as pik
except:
    import pickle as pik

import pickletools as pikt

buf = StringIO.StringIO()
ser = pik.Pickler(buf, protocol = pik.HIGHEST_PROTOCOL)
ser.dump("abc")
ser.dump(1)
ser.dump(1.0)
ser.dump({1, 2, 3})
ser.dump([4, 5, 6])
buf.flush()

print buf.getvalue()
