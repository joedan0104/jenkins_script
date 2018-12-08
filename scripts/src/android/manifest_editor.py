#!/usr/bin/python
# -*- coding: UTF-8 -*-
# editor manifest file and change channel information
# uncompyle6 version 3.2.4
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.12 (default, Dec  4 2017, 14:50:18) 
# [GCC 5.4.0 20160609]
# Compiled at: 2017-10-30 19:11:07

import os, sys, time, json, shutil, glob
import re

class ManifestEditor:

    def __init__(self, path):
        # manifest file path
        self.path = path
        self.content = None

    #
    # read manifest file content into string
    #
    def readManifest(self):
        # 检测文件是否存在
        if os.path.exists(self.path) == False:
            print r'manifest file %s not exists' % (self.path)
            return None
    	# 打开一个文件
    	fo = open(self.path, "r+")
        # 读取文件内容
    	self.content = fo.read()
    	print "读取的字符串是 : ", self.content
    	# 关闭文件
    	fo.close()
    	return self.content

    #
    # save content into manifest file
    #
    # return boolean. True: SUCCESS False: Failed
    def saveManifest(self):
        if self.content == None or len(self.content) == 0:
            print 'manifest content is empty'
            return False
        # 打开一个文件
        fo = open(self.path, "w")
        count = fo.write(self.content)
        fo.close()
        if count <= 0:
            print 'save manifest failed'
            return False
        return True

    #
    # replace meta data
    #
    # key: meta data key
    # value: meta data value
    # manifest: manifest content
    #
    def replace_meta_data(self, key, value, manifest):
        pattern = r'(<meta-data\s+android:name="%s"\s+android:value=")(\S+)("\s+/>)' % (key)
        replacement = r"\g<1>{replace_value}\g<3>".format(replace_value=value)
        self.content = re.sub(pattern, replacement, manifest)
        return self.content





