#!/usr/bin/python
# -*- coding: utf-8 -*-  

"""Usage:
  ci_ios_app.py init [--projectname=<projectname>]
  ci_ios_app.py deliver [--projectname=<name>] [--versionname=<si>] 
  [--branch=<branch>] [--channelpackage=<ss>] [--channelname=<name>]
  [--channelvalue=<name>] [--bundleversion=<name>]
  
"""

import os, sys, json , shutil
from docopt import docopt
from biplist import *
import qrcode
from PIL import Image
from BeautifulSoup import BeautifulSoup
from gradle_properties import GradleProperties

CI_ANDROID_PATH = os.environ['HOME'] + '/Desktop/Jenkins/src/android'
CI_ANDROID_TEMPLATES_PATH = CI_ANDROID_PATH + '/templates'
WORKSPACE_PATH = os.environ['HOME'] + '/Desktop/Projects'

def handle_args(arguments):
	print arguments
	if arguments['init'] == True:
		# 初始化app
		init_app(arguments)
	elif arguments['deliver'] == True:
		# 打包一个app		
		deliver_app(arguments)
	else:
		raise "not support command"
	

def init_app(arguments):
	projectname = arguments['--projectname']
	if projectname == None:
		raise "projectname is nil"

	# 判断是否是安卓工程
	project_path = r'%s/%s' % (WORKSPACE_PATH, projectname)
	if os.path.exists(project_path) == False:
		raise "project folder not found"

	listdir = os.listdir(project_path)
	is_android_project = False
	gradle_property_path = ''
	for t_dir in listdir:
		#print t_dir
		if t_dir.find('gradle.properties') != -1:
			is_android_project = True
			gradle_property_path = r'%s/%s' % (project_path, t_dir)
					

	if is_android_project == False:
		raise 'current path is not an android project'

	project_build_path = project_path + '/builds'
	if os.path.exists(project_build_path) == False:		
		# 创建build文件夹
		os.system('mkdir ' + project_build_path)

		# copy 配置文件
		ci_config_path = CI_ANDROID_TEMPLATES_PATH + '/config.json'
		copy_cmd = r'cp %s %s' % (ci_config_path, project_build_path)
		#print copy_cmd
		os.system(copy_cmd)

		# copy download.html
		ci_download_path = CI_ANDROID_TEMPLATES_PATH + '/download.html'
		copy_cmd = r'cp %s %s' % (ci_download_path, project_build_path)
		os.system(copy_cmd)

		# copy info.plist
		# ci_info_plist_path = CI_ANDROID_TEMPLATES_PATH + '/info.plist'
		# copy_cmd = r'cp %s %s' % (ci_info_plist_path, project_build_path)
		# os.system(copy_cmd)
	else:
		raise 'app has init'

	# Gemfile
	ci_gemfile_path = CI_ANDROID_TEMPLATES_PATH + '/Gemfile'
	copy_cmd = r'cp %s %s' % (ci_gemfile_path, project_path)
	os.system(copy_cmd)
	os.system('bundle install')

	# fastlane文件夹
	ci_fastlane_path = CI_ANDROID_TEMPLATES_PATH + '/fastlane'
	copy_cmd = r'cp -R %s %s' % (ci_fastlane_path, project_path)
	os.system(copy_cmd)

	#修改config文件
	if gradle_property_path == None:
		print "you should modify config file by youself, eg:plist_path"
	else:
		try:
			gradle_properties =  GradleProperties(gradle_property_path)
			gradle_properties.readProperties()
			# writePlist(plist, "example.plist") 

			project_config_path = r'%s/config.json' % project_build_path
			config_data = None
			with open(project_config_path, 'r') as json_data:

				config_data = json.load(json_data)
				update_config_value(config_data, 'version_code', gradle_properties.getProperty('VERSION_CODE'))
				update_config_value(config_data, 'version_name', gradle_properties.getProperty('VERSION_NAME'))
				update_config_value(config_data, 'project_path', project_path)
				update_config_value(config_data, 'output_directory', project_build_path)
				update_config_value(config_data, 'gradle_properties_path', gradle_property_path)
				update_config_value(config_data, 'project_name', projectname)

			if config_data:
				with open(project_config_path, 'w') as json_file:
					json_file.write(json.dumps(config_data))
		except Exception as e:
			raise e

# 通过命令打包app
def deliver_app(arguments):
	projectname = arguments['--projectname']
	if projectname == None:
		raise "projectname is nil"

	# 检查工程文件是配置了打包环境
	project_path = r'%s/%s' % (WORKSPACE_PATH, projectname)
	project_build_path = project_path + '/builds'
	print project_build_path
	project_fastlane_path = project_path + '/fastlane'
	print project_fastlane_path
	project_config_path = project_build_path + '/config.json'
	print project_config_path
	gradle_property_path = project_path + '/gradle.properties'
	print gradle_property_path
	if os.path.exists(project_build_path) == False or os.path.exists(project_fastlane_path) == False \
		or os.path.exists(project_config_path) == False or os.path.exists(gradle_property_path) == False:
		init_app(arguments)

	config_data = None
	try:	
		with open(project_config_path, 'r') as json_data:
			config_data = json.load(json_data)
		if config_data == None:
			raise "config error"
	except Exception as e:
		raise e
	
	#read version info from project configuratuin
	gradle_properties =  GradleProperties(gradle_property_path)
        gradle_properties.readProperties()
        version_name = gradle_properties.getProperty('VERSION_NAME')
	if version_name == None:
                version_name = arguments['--versionname']
	if version_name == None:
                raise 'version_name is nil'        
	version_code = gradle_properties.getProperty('VERSION_CODE')
 	if version_code == None:
                raise 'version_code is nil'

	build_version_code = arguments['--bundleversion']
	if build_version_code == None:
		build_version_code = os.environ['BUILD_NUMBER']
	if build_version_code == None:
          	raise 'build_version_code is nil'

	update_config_value(config_data, 'build_version_code', build_version_code)

	app_build_version_code = gradle_properties.getProperty('BUILD_VERSION_CODE')
	if app_build_version_code == None:
                app_build_version_code = 1
	app_name = gradle_properties.getProperty('APP_NAME')
	if app_name == None:
        	app_name = projectname
	package_name = gradle_properties.getProperty('PACKAGE_NAME')
	if package_name == None:
		raise 'gradle properties package_name is nil'	

	update_config_value(config_data, 'app_name', app_name)
	update_config_value(config_data, 'package_name', package_name)
	update_config_value(config_data, 'version_name', version_name)
	update_config_value(config_data, 'version_code', version_code)
	update_config_value(config_data, 'build_version_code', build_version_code)
	update_config_value(config_data, 'app_build_version_code', app_build_version_code)

	channel_package = arguments['--channelpackage']
	if channel_package == None:
		update_config_value(config_data, 'channel_package', '0')
	else:
		update_config_value(config_data, 'channel_package', channel_package)
		
	# default channel name set main
	channel_name = arguments['--channelname']
	if channel_name == None:
		update_config_value(config_data, 'channelname', 'main')
	else:
		update_config_value(config_data, 'channelname', channel_name)
		
	channel_value = arguments['--channelvalue']
	if channel_value == None:
		if channel_name == None:
			update_config_value(config_data, 'channelvalue', 'main')
		else:
			update_config_value(config_data, 'channelvalue', channel_name)
	else:
		update_config_value(config_data, 'channelvalue', channel_value)

	branch = arguments['--branch']
	if branch == None:
		raise "branch can not nil"
	update_config_value(config_data, 'branch', branch)

	try:
		with open(project_config_path, 'w') as json_file:
			json_file.write(json.dumps(config_data))
	except Exception as e:
		raise e

	# 从config文件部署app
	deliver_from_config(project_config_path, projectname)

# 通过config文件打包app
def deliver_from_config(project_config_path, projectname):
	config_data = None
	try:
		with open(project_config_path) as json_data:
			config_data = json.load(json_data)
		if config_data == None:
			raise "config error"
		print config_data
	except Exception as e:
		raise e	
	print '11111111111111111111111'
	project_path = get_config_value(config_data, 'project_path')
	gradle_property_path = get_config_value(config_data, 'gradle_properties_path')
	app_name = get_config_value(config_data, 'app_name')
	version_name = get_config_value(config_data, 'version_name')
	version_code = get_config_value(config_data, 'version_code')
	channel_name = get_config_value(config_data, 'channelname')
	build_version_code = get_config_value(config_data, 'build_version_code')
	gradle_properties =  GradleProperties(gradle_property_path)
        gradle_properties.readProperties()
	app_build_version_code = gradle_properties.getProperty('BUILD_VERSION_CODE')
	output_directory = get_config_value(config_data, 'output_directory')
	output_name = r'%s_build%s.apk' % (app_name, app_build_version_code)	
	build_type = get_config_value(config_data, 'build_type')
	#if export_method != 'release':
	#	app_name = r'%s#%s' % (app_name, bundle_version)
	

	# 删除旧文件
	rm_history_cmd = r'rm -rf %s/*.apk' % (output_directory)
	os.system(rm_history_cmd)

	# 更新gradle文件
	#gradle_properties =  GradleProperties(gradle_property_path)
	#gradle_properties.readProperties()
	gradle_properties.updateProperties('VERSION_NAME', version_name)
	gradle_properties.updateProperties('VERSION_CODE', version_code)
	gradle_properties.saveProperties()
	
	# 更新fir文件
	# fir publish /Users/tommy/Desktop/ci/Project/TesBm/金蛋理财-1.0.0.60.ipa -T ec84ed490c01da5725cae153c558590a
	# fir_str = r'fir publish %s/%s -T ec84ed490c01da5725cae153c558590a' % (output_directory, output_name)
	# fir_path = r'%s/fastlane/fir.sh' % (project_path)
	# with open(fir_path, 'w') as fir_file:
	# 	fir_file.write(fir_str)

	# 更新gem
	# ret = os.system("bundle update")
	# print r'bundle update value:%s:%s' % (os.getcwd(), str(ret))
	if os.system("bundle update") != 0:
		raise "bundle update failed"

	# 修改权限, gradle执行需要权限
	oa_cmd = r'chmod -R 777 %s' % project_path
	os.system(oa_cmd)
	
	# 拼接fastlane命令
	fastlane_cmd = r'fastlane android deploy output_name:%s version_name:%s build_version_code:%s gradle_properties_path:%s build_type:%s output_directory:%s project_path:%s' % (output_name, version_name, build_version_code, get_config_value(config_data, 'gradle_properties_path'), build_type, output_directory, get_config_value(config_data, 'project_path'))
	print fastlane_cmd
	
	# 执行fastlane命令
	if os.system(fastlane_cmd) != 0:
		raise "fastlane excute failed"
	print '222222222222222222222222'
	# copy apk文件
	apk_folder_path = project_path + '/app/build/outputs/apk/internal/release'
	listdir = os.listdir(apk_folder_path)
	apk_file = ''
	for t_dir in listdir:
		if t_dir.find('.apk') != -1:
			apk_file = apk_folder_path + '/' + t_dir

	if apk_file == '':
		raise "not found apk file"

	# start copy apk file
	apk_ori_path = output_directory + '/' + output_name
	copy_apk_cmd = r'cp %s %s' %(apk_file, apk_ori_path)
	os.system(copy_apk_cmd)

	# start copy mapping file
        map_folder_path = project_path + '/app/build/outputs/mapping/internal/release'
	map_listdir = os.listdir(map_folder_path)
        map_file = ''
        for t_dir in map_listdir:
                if t_dir.find('mapping.') != -1:
                        map_file = map_folder_path + '/' + t_dir

        if map_file == '':
                raise "not found mapping file"

	map_file_name = 'mapping.txt'
        map_ori_path = output_directory + '/' + map_file_name
        copy_map_cmd = r'cp %s %s' %(map_file, map_ori_path)
        os.system(copy_map_cmd)

	print '3333333333333333333333333'
	channel_package = get_config_value(config_data, 'channel_package')
	channel_name = get_config_value(config_data, 'channelname')
	channel_value = get_config_value(config_data, 'channelvalue')
        keystore_file = gradle_properties.getProperty('RELEASE_KEYSTORE_FILE')
        keystore_password = gradle_properties.getProperty('RELEASE_KEYSTORE_PASSWORD')
        keystore_alias = gradle_properties.getProperty('RELEASE_KEYSTORE_ALIAS')
        keystore_key_password = gradle_properties.getProperty('RELEASE_KEYSTORE_KEY_PASSWORD')
	#if channel_package == '1' or channel_package == '2':
	#	os.system('java -jar /Users/mac/Desktop/360jiagubao_mac/jiagu/jiagu.jar -login 18911540740 dubojdlc562314')
	#	import_sgin = r'java -jar /Users/mac/Desktop/360jiagubao_mac/jiagu/jiagu.jar -importsign'
	#	sgin_path_and_info = r'%s/app/%s %s %s %s' % (project_path, keystore_file, keystore_password, keystore_alias, keystore_key_password)
	#	sign_cmd = '%s %s' % (import_sgin, sgin_path_and_info)
	#	print('sign_cmd', sign_cmd)
	#	os.system(sign_cmd)
	#	#java -jar /Users/mac/Desktop/360jiagubao_mac/jiagu/jiagu.jar -jiagu /Users/mac/Desktop/jindanlicai_android-6.3.1.71.apk /Users/mac/Desktop/
	#	channleinfo_all_cmd = r'java -jar /Users/mac/Desktop/360jiagubao_mac/jiagu/jiagu.jar -importmulpkg'
	#	channleinfo_path = r'/Users/mac/Desktop/channel/channle.txt'
	#	print ('=================', channel_name)
	#	if channel_package == '1':
	#		if(channel_name == 'all'):
	#			channel_cmd = '%s %s' % (channleinfo_all_cmd, channleinfo_path)
	#		else:
	#			mk_channelInfo_file(channel_name,channel_package)
	#			channleinfo_path = r'/Users/mac/Desktop/channel/singlechannle.txt'
	#			
	#	elif channel_package == '2':
	#		mk_channelInfo_file(channel_value,channel_package)
	#		channleinfo_path = r'/Users/mac/Desktop/channel/muchannle.txt'
	#		
	#	channel_cmd = '%s %s' % (channleinfo_all_cmd, channleinfo_path)
	#	os.system(channel_cmd)

	#set channel config file info	
	channleinfo_path = r'%s/channel.txt' % (project_path)
	if os.path.exists(channleinfo_path) == False:
		channleinfo_path = r'/Users/mac/Desktop/channel/channle.txt'
	jiagu_cmd = r'java -jar /Users/mac/Desktop/360jiagubao_mac/jiagu/jiagu.jar -jiagu %s %s -autosign -pkgparam %s -automulpkg '  % (apk_ori_path, output_directory, channleinfo_path)
	
	os.system(jiagu_cmd)
	# 删除临时文件(包括未加固文件和加固临时文件)
	delete_temp_file(output_directory, output_name);

	print '4444444444444444444444444'
	# 获取新的加固文件作为output_name
	listdir = os.listdir(output_directory)
	output_name = ''
	for t_dir in listdir:
		if t_dir.find('main_sign.') != -1:
			output_name = t_dir
	if output_name == '':
		raise 'not find main channel apk file' 
	# 生成文件部署到nginx
	deloy_nginx_static_file(project_config_path, projectname, output_name)

def deloy_nginx_static_file(project_config_path, projectname, output_name):
	config_data = None
	try:
		with open(project_config_path) as json_data:
			config_data = json.load(json_data)
		if config_data == None:
			raise "config error"
		print config_data
	except Exception as e:
		raise e

	build_version_code = get_config_value(config_data, 'build_version_code')
	output_directory = get_config_value(config_data, 'output_directory')
	nginx_html_path = get_config_value(config_data, 'nginx_html_path')
	server_ip = get_config_value(config_data, 'server_ip')

	# gradle property read
	gradle_property_path = get_config_value(config_data, 'gradle_properties_path')
	gradle_properties =  GradleProperties(gradle_property_path)
        gradle_properties.readProperties()
	keystore_file = gradle_properties.getProperty('RELEASE_KEYSTORE_FILE')
	keystore_password = gradle_properties.getProperty('RELEASE_KEYSTORE_PASSWORD')
	keystore_alias = gradle_properties.getProperty('RELEASE_KEYSTORE_ALIAS')
	keystore_key_password = gradle_properties.getProperty('RELEASE_KEYSTORE_KEY_PASSWORD')

	# 创建需要的文件夹
	server_project_folder = nginx_html_path + '/' + projectname
	if os.path.exists(server_project_folder) == False:
		os.system('mkdir ' + server_project_folder)
	server_bundle_folder = server_project_folder + '/' + build_version_code
	if os.path.exists(server_bundle_folder) == False:
		os.system('mkdir ' + server_bundle_folder)

	
	root_http_url = 'http://' + server_ip + ':8787/' + projectname + '/' +  build_version_code
	apk_server_url = root_http_url + '/' + output_name
	download_url = root_http_url + '/' + 'download.html'

	# builds下文件路径
	download_html_path = output_directory + '/download.html'
	apk_path = output_directory + '/' + output_name

	# 修改download html
	try:
		with open(download_html_path, 'r') as file_data:
			soup = BeautifulSoup(file_data)
			download_tag = soup.body.a
			download_tag['href'] = apk_server_url
			ret_html_str = soup.prettify()
			with open(download_html_path, 'w') as d_file:
				d_file.write(ret_html_str)
	except Exception as e:
		raise e

	# 生成二维码	
	print "download html: " + download_url	
	img_code_path = server_bundle_folder + '/' + 'qr.png'
	print "qrcode path: " + img_code_path
	qr = qrcode.QRCode(version=1, box_size=10, border=1)
	qr.add_data(download_url)
	img = qr.make_image()	
	img.save(img_code_path)	

	# 创建nginx需要的文件
	copy_download_html_cmd = r'cp %s %s' % (download_html_path, server_bundle_folder)
	os.system(copy_download_html_cmd)
	copy_apk_cmd = r'cp %s %s' % (apk_path, server_bundle_folder)
	os.system(copy_apk_cmd)

	# 修改权限
	oa_cmd = r'chmod -R 777 %s' % server_project_folder
	os.system(oa_cmd)
	
	
def update_config_value(data, key, value):
	res_item = None
	for item in data:
		if item['key'] == key:
			res_item = item
			break

	if res_item:
		res_item['value'] = value
	else:
		print 'not found ' + key

def get_config_value(data, key):
	res_item = None
	for item in data:
		if item['key'] == key:
			res_item = item
			break
	if res_item:
		return res_item['value']
	return None

def delete_temp_file(filePath, output_name):

	if os.path.exists(filePath) == False:
		return
	delList = os.listdir(filePath)
	for f in delList:
		print 'filePath========='+f
		if 'temp' in f or 'jiagu' in f or f.find(output_name) >= 0:
			delete_file = '%s/%s' % (filePath,f)
			print 'delete_file========='+delete_file
			os.remove(delete_file)
			
	
def mk_channelInfo_file(channlename,channeltype):

	
	filePath = r'/Users/mac/Desktop/channel/'
	if channeltype == '2':
		if ',' in channlename:
			list = channlename.split(',')
			txtname = r'muchannle.txt'
			path = os.path.join(filePath, txtname)
			if os.path.exists(path):
				os.remove(path)
			if len(list):
				for i in range(len(list)):
					print "item==========="+list[i]
					try:
						with open(path, 'a+') as f:
							channle = '%s %s %s\n' % ('UMENG_CHANNEL',list[i], list[i].replace(' ', ''))
							f.write(channle)
					except Exception as e:
						raise e
		else:
			try:
				txtname = r'muchannle.txt'
				path = os.path.join(filePath, txtname)
				with open(path, 'w') as f:
					channle = '%s %s %s' % ('UMENG_CHANNEL',channlename, channlename.replace(' ', ''))
					f.write(channle)
			except Exception as e:
				raise e
			
	else:	
		try:
			txtname = r'singlechannle.txt'
			path = os.path.join(filePath, txtname)
			with open(path, 'w') as f:
				channle = '%s %s %s' % ('UMENG_CHANNEL',channlename, channlename.replace(' ', ''))
				f.write(channle)
		except Exception as e:
			raise e
	
	

	

if __name__ == '__main__':
	reload(sys)
	sys.setdefaultencoding('utf8')
	arguments = docopt(__doc__)
	handle_args(arguments)
