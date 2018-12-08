#!/usr/bin/python
# -*- coding: UTF-8 -*-
import HtmlTestRunner
import unittest

from manifest_editor import ManifestEditor


class TestManifestEditor(unittest.TestCase):
    def __init__(self, path):
        self.path = path

	def testManifest(self):
	    path = r'/home/dell/DEV/developer/jenkins_script/scripts/src/android/AndroidManifest.xml'
	    manifest_editor = ManifestEditor(path)
	    print '1111'
	    content = manifest_editor.readManifest()
	    print content
	    self.assertIsNone(content)

if __name__ == '__main__':
    # 创建一个测试集合
    test_suite = unittest.TestSuite()
    result_path = r'/home/dell/DEV/developer/jenkins_script/scripts/src/android/res.html'
    path = r'/home/dell/DEV/developer/jenkins_script/scripts/src/android/AndroidManifest.xml'
    # 测试套件中添加测试用例
    test_suite.addTest(TestManifestEditor(result_path))
    # 打开一个保存结果的html文件
    fp = open(result_path,'wb')
    runner = HtmlTestRunner.HTMLTestRunner(output='example_suite')
    # 生成执行用例的对象
    runner.run(test_suite)
    # 执行测试套件
    fp.close()


