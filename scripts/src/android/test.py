#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Usage: test.py deliver [--projectname=<name>]
"""

import os, sys, json, shutil, glob
import qrcode
from gradle_properties import GradleProperties
from manifest_editor import ManifestEditor
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

def detact_apk_output_path(project_directory):
	# 检查目录是否有效
	if os.path.exists(project_directory) == False:
		return None
	# 首先优先探测app目录
	target_path = project_directory + '/app/build/outputs/apk'
	apk_folder_path = search_apk_path(target_path)
	if apk_folder_path != None:
		print "find apk output path:" + apk_folder_path
		return apk_folder_path
	# 查找输出目录下的子文件夹
	listdir = os.listdir(project_directory)
	for t_dir in listdir:
		if t_dir.startWith('build') == True:
			continue
		target_path = project_directory + os.sep + t_dir + '/build/outputs/apk'
		# 过滤文件
		if os.path.isdir(target_path) == False:
			continue
		# 查找APK目标

		apk_folder_path = search_apk_path(target_path)
		if apk_folder_path != None:
                	print "find apk output path:" + apk_folder_path
                	return apk_folder_path
	return None	

# 当前目录或者父目录对应的查找APK目录
def search_apk_path(project_directory):
	# 文件夹是否存在
	if os.path.exists(project_directory) == False:
		return None
        # 首先优先探测app目录
        if has_apk_file(project_directory) == True:
                return project_directory

        # 查找低版本路径
        apk_folder_path = os.path.dirname(project_directory)
	print "parent path:" + apk_folder_path
	if has_apk_file(apk_folder_path) == True:
		return apk_folder_path
	# 未找到返回None
	return None
		

def has_apk_file(output_directory):
	if os.path.exists(output_directory):
		for fn in glob.glob(output_directory + os.sep + '*.apk'):
                        print fn
                        # 查找一个有效的包
                        return True
	return False


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
					#target_file_name = r'%s_%s' % (sub_file, file)
					target_file_name = target_directory + os.sep + file
					print target_file_name
					copy_cmd = r'cp %s %s' % (file_path, target_file_name)
					os.system(copy_cmd)
					print copy_cmd
					return
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

	gradle_property_path = r'/home/dell/DEV/project/accmobile/gradle.properties'
	version_name = '1.4.0'
	version_code = 4
	gradle_properties =  GradleProperties(gradle_property_path)

	# 测试AndroidMainifest编辑
	#manifest = r'/home/dell/DEV/developer/jenkins_script/scripts/src/android/AndroidManifest.xml'
	#manifest_editor = ManifestEditor(manifest)
	#content = manifest_editor.readManifest()
	#content = manifest_editor.replace_meta_data('UMENG_CHANNEL', 'agent127', content)
	#content = manifest_editor.replace_meta_data('UNIONID', '127', content)
	#print content 
	#success = False
	#success = manifest_editor.saveManifest()
    #if !success:
    #    print 'saveManifest failed'
    #else:
    #    print 'saveManifest success'

	gradle_properties.readProperties()
	gradle_properties.updateProperties('VERSION_NAME', version_name)
	gradle_properties.updateProperties('VERSION_CODE', version_code)
	gradle_properties.saveProperties()

	print 'find mapping file'
	build_output_directory = '/home/dell/DEV/project/accmobile/app/build/outputs/mapping'
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
	project_direcoty = '/home/dell/DEV/project/accmobile'
	apk_folder_directory = detact_apk_output_path(project_direcoty)
	if apk_folder_directory != None and len(apk_folder_directory) > 0:
		print 'find apk directory success:' + apk_folder_directory

	target_directory = '/home/dell/DEV/project/accmobile/builds'
	copy_cmd = r'mkdir %s' % (target_directory)
	os.system(copy_cmd)
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
