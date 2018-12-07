#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Usage: test.py deliver [--projectname=<name>]
"""

import os, sys, json, shutil, glob
import qrcode
from gradle_properties import GradleProperties
from docopt import docopt

def handle_args(arguments):
        if arguments['deliver'] == True:
		# 打包一个app		
		deliver_app(arguments)

def search(a, b):#a为路径，b为关键词
	for file in os.listdir(a):
        	if os.path.isfile(a + '\\' + file):
                	if b in file:
                        	print(file, '==>', a + '\\' + file)
                        else:
                        	search(a + '\\' + file, b)


def deloy_qrcode_apk_file(output_directory, outputname, channel_name):
        print 'generate qrcode apk file'
        if os.path.exists(output_directory) == False:
                raise 'output_directory not exists'
        apk_qr_path = output_directory + os.sep + outputname
	print apk_qr_path
        if os.path.exists(apk_qr_path):
		print 'qrcode apk file exists'
                return

        # 生成标准的输出文件用于二维码下载
	apk_path = ''
        if os.path.exists(output_directory):
            for fn in glob.glob(output_directory + os.sep + '*.apk'):
                # 查找渠道包
                if channel_name in fn:
                    apk_path = fn
                    break

        if len(apk_path) == 0:
                for fn in glob.glob(output_directory + os.sep + '*.apk'):
                        print fn
                        # 查找一个有效的包
                        apk_path = fn
                        break
	if len(apk_path) == 0:
		raise 'can not file apk file'

	copy_apk_cmd = r'mv %s %s' %(apk_path, apk_qr_path)
        print copy_apk_cmd
        os.system(copy_apk_cmd)

def generate_qrcode_image(download_url, server_bundle_folder):
	# 生成二维码	
	print "download html: " + download_url	
	img_code_path = server_bundle_folder + '/' + 'qr.png'
	print "qrcode path: " + img_code_path
	qr = qrcode.QRCode(version=1, box_size=10, border=1)
	qr.add_data(download_url)
	img = qr.make_image()	
	img.save(img_code_path)


def deloy_mapping_file(build_output_directory, target_directory):
	print 'find and copy mapping file to target directory\n'
	if os.path.exists(build_output_directory) == False:
		raise 'build_output_directory not exists'
        for root, dirs, files in os.walk(build_output_directory, True, None, False):
                for file in files:
                        try:
                                print '-----------------------------------'
                                file_name = os.path.splitext(file)[0]
                                file_suffix = os.path.splitext(file)[1]
                                file_path = os.path.join(root, file)
                                file_abs_path = os.path.abspath(file)
                                file_parent = os.path.dirname(file_path)
                                print "file : {0}".format(file)
                                print "file_name : {0}".format(file_name)
                                print "file_suffix : {0}".format(file_suffix)
                                print "file_path : {0}".format(file_path)
                                print "file_abs_path : {0}".format(file_abs_path)
                                print "file_parent : {0}".format(file_parent)
				if file.find('mapping.txt') != -1:
					print r'papping file %s' % (file)
					sub_file = os.path.basename(file_parent)
					if sub_file.find('release') != -1:
						# release目录需要继续查找父目录作为渠道标识
						file_parent = os.path.dirname(file_parent)
						sub_file = os.path.basename(file_parent)
					target_file_name = r'%s_%s' % (sub_file, file)
					target_file_name = target_directory + os.sep + target_file_name
					print target_file_name
					copy_cmd = r'cp %s %s' % (file_path, target_file_name)
					os.system(copy_cmd)
                        except Exception, e:
                                print "Exception", e
 



def deliver_app(arguments):
	projectname = arguments['--projectname']
	if projectname == None:
		raise "projectname is nil"
        print projectname
        path = os.getcwd()
        for fn in glob.glob(path + os.sep + '*.py'):
	    if 'android' in fn or 'ci' in fn:
                print fn
                print r'filename: %s' % (os.path.basename(fn))

        gradle_property_path = '/home/t1/jenkins/workspace/accmobile-git/gradle.properties'
        version_name = '1.4.0'
        version_code = 4
        gradle_properties =  GradleProperties(gradle_property_path)
	gradle_properties.readProperties()
	gradle_properties.updateProperties('VERSION_NAME', version_name)
	gradle_properties.updateProperties('VERSION_CODE', version_code)
	gradle_properties.saveProperties()

	print 'find mapping file'
	build_output_directory = '/home/t1/jenkins/workspace/accmobile-git/app/build/outputs/mapping'
	#for root, dirs, files in os.walk(build_output_directory, True, None, False):
        #	print'\n========================================'
        #	print "root : {0}".format(root)
        #	print "dirs : {0}".format(dirs)
        #	print "files : {0}".format(files)
        #	for file in files:
        #    		try:
        #        		print '-----------------------------------'
        #        		file_name = os.path.splitext(file)[0]
        #        		file_suffix = os.path.splitext(file)[1]
        #        		file_path = os.path.join(root, file)
        #        		file_abs_path = os.path.abspath(file)
        #        		file_parent = os.path.dirname(file_path)
        #       			print "file : {0}".format(file)
        #        		print "file_name : {0}".format(file_name)
        #        		print "file_suffix : {0}".format(file_suffix)
        #        		print "file_path : {0}".format(file_path)
        #        		print "file_abs_path : {0}".format(file_abs_path)
        #        		print "file_parent : {0}".format(file_parent)
        #    		except Exception, e:
        #        		print "Exception", e

	target_directory = '/home/t1/jenkins/workspace/accmobile-git/builds'
	deloy_mapping_file(build_output_directory, target_directory)

	print 'install apk file\n'
	output_name = 'accmobile_V7.7.3_release_20181120113634.apk'
	deloy_qrcode_apk_file(target_directory, output_name, 'wxzpk')

	print '\nsearch mapping file'
	search(build_output_directory, 'mapping.txt')
#        for fn in glob.glob(build_output_directory + os.sep + '**mapping*.txt'):
                #print fn
                #print r'filename: %s' % (os.path.basename(fn))
	download_url = 'http://192.168.190.41/accmobile-git/7.7.2/accmobile_V7.7.2_release_20181120182439.apk'
	server_bundle_path = '/home/t1/jenkins/workspace/accmobile-git/builds'
	generate_qrcode(download_url, server_bundle_path)


if __name__ == '__main__':
	reload(sys)
	sys.setdefaultencoding('utf8')
	arguments = docopt(__doc__)
        handle_args(arguments)
