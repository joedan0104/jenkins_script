# editor manifest file and change channel information
# uncompyle6 version 3.2.4
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.12 (default, Dec  4 2017, 14:50:18) 
# [GCC 5.4.0 20160609]
# Compiled at: 2017-10-30 19:11:07


import re
#
# replace meta data
# 
# key: meta data key
# value: meta data value
# manifest: manifest content
#
def replace_meta_data(key, value, manifest):
    pattern = r'(<meta-data\s+android:name="%s"\s+android:value=")(\S+)("\s+/>)' % (key)
    replacement = r"\g<1>{replace_value}\g<3>".format(replace_value=value)
    return re.sub(pattern, replacement, manifest)






