# uncompyle6 version 3.2.4
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.12 (default, Dec  4 2017, 14:50:18) 
# [GCC 5.4.0 20160609]
# Embedded file name: /Users/mac/Desktop/Jenkins/src/android/gradle_properties.py
# Compiled at: 2017-10-30 19:11:07
import os

class GradleProperties(object):
    """docstring for GradleProperties"""

    def __init__(self, path):
        super(GradleProperties, self).__init__()
        self.path = path
        self.values = {}

    def readProperties(self):
        with open(self.path, 'r') as (file_data):
            for line in file_data:
                rets = line.split('=', 1)
                if len(rets) == 2:
                    self.values[rets[0]] = rets[1].strip()
                del line

        print self.values

    def getProperty(self, key):
        if self.values.has_key(key) == False:
            return None
        return self.values[key]

    def updateProperties(self, key, value):
        if self.values.has_key(key) == False:
            return
        self.values[key] = value

    def saveProperties(self):
        ret_str = ''
        for key, value in self.values.items():
            print r'key:%s value:%s' % (key, value)
	    ret_str += key + '=' + str(value) + '\n'

        print ret_str
        with open(self.path, 'w') as (file):
            file.write(ret_str)
# okay decompiling gradle_properties.pyc
