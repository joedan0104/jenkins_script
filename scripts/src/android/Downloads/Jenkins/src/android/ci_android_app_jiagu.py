#!/usr/bin/python
# -*- coding: utf-8 -*-  

"""Usage:
  ci_android_app_jiagu.py init [--projectname=<projectname>]
  ci_android_app_jiagu.py deliver [--projectname=<name>] [--versionname=<si>] 
  [--branch=<branch>] [--channel=<ss>] [--channelpackage=<ss>] [--channelname=<name>]
  [--channelvalue=<name>] [--bundleversion=<name>]
  
"""

import os, sys, json, shutil
from docopt import docopt
from biplist import *
import qrcode
from PIL import Image
from BeautifulSoup import BeautifulSoup
from gradle_properties import GradleProperties

# 配置文件相关信息
CI_ANDROID_PATH = os.environ['HOME'] + '/Desktop/Jenkins/src/android'
# 模板文件
CI_ANDROID_TEMPLATES_PATH = CI_ANDROID_PATH + '/templates'
# 工作区目录
WORKSPACE_PATH = os.environ['HOME'] + '/Desktop/workspace'

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
	if os.path.exists(project_build_path) == False or os.path.exists(project_fastlane_path) == False or os.path.exists(project_config_path) == False :
		init_app(arguments)

	config_data = None
	try:	
		with open(project_config_path, 'r') as json_data:
			config_data = json.load(json_data)
		if config_data == None:
			raise "config error"
	except Exception as e:
		raise e
	version_name = arguments['--versionname']
	if version_name == None:
		raise "version name is nil"
	update_config_value(config_data, 'version_name', version_name)
	# update_config_value(config_data, 'version_code', version_name.replace('.',''))

	channel_package = arguments['--channelpackage']
	if channel_package == None:
		update_config_value(config_data, 'channel_package', '0')
	else:
		update_config_value(config_data, 'channel_package', channel_package)
		
	channel_name = arguments['--channelname']
	if channel_name == None:
		update_config_value(config_data, 'channelname', 'internal')
	else:
		update_config_value(config_data, 'channelname', channel_name)
		
	channel_value = arguments['--channelvalue']
	if channel_value == None:
		update_config_value(config_data, 'channelvalue', 'internal')
	else:
		update_config_value(config_data, 'channelvalue', channel_value)

	branch = arguments['--branch']
	if branch == None:
		raise "branch can not nil"
	update_config_value(config_data, 'branch', branch)

	build_version_code = arguments['--bundleversion']
	update_config_value(config_data, 'build_version_code', build_version_code)
	
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
	version_name = get_config_value(config_data, 'version_name')
	version_code = get_config_value(config_data, 'version_code')
	gradle_properties =  GradleProperties(gradle_property_path)
	gradle_properties.readProperties()
	build_version_code = gradle_properties.getProperty('BUILD_VERSION_CODE')
	output_directory = get_config_value(config_data, 'output_directory')
	output_name = r'%s_%s.%s.apk' % (projectname, version_name, build_version_code)	
	build_type = get_config_value(config_data, 'build_type')
	#app_name = get_config_value(config_data, 'app_name')
	#if export_method != 'release':
	#	app_name = r'%s#%s' % (app_name, bundle_version)
	

	# 删除旧文件
	rm_history_cmd = r'rm -rf %s/*.apk' % (output_directory)
	os.system(rm_history_cmd)

	# 更新gradle文件
	gradle_properties =  GradleProperties(gradle_property_path)
	gradle_properties.readProperties()
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
	apk_folder_path = project_path + '/app/build/outputs/apk'
	listdir = os.listdir(apk_folder_path)
	apk_file = ''
	for t_dir in listdir:
		if t_dir.find('.apk') != -1:
			apk_file = apk_folder_path + '/' + t_dir

	if apk_file == '':
		raise "not found apk file"

	apk_ori_path = output_directory + '/' + output_name
	copy_apk_cmd = r'cp %s %s' %(apk_file, apk_ori_path)
	os.system(copy_apk_cmd)
	print '3333333333333333333333333'
	channel_package = get_config_value(config_data, 'channel_package')
	channel_name = get_config_value(config_data, 'channelname')
	channel_value = get_config_value(config_data, 'channelvalue')
	if channel_package == '1' or channel_package == '2':
		os.system('java -jar /Users/mac/Desktop/360jiagubao_mac/jiagu/jiagu.jar -login 18911540740 dubojdlc562314')
		import_sgin = r'java -jar /Users/mac/Desktop/360jiagubao_mac/jiagu/jiagu.jar -importsign'
		sgin_path_and_info = r'/Users/mac/Desktop/Projects/jindanlicai_android/app/release.keystore jindanlicai88 jindanlicai jindanlicai88'
		sign_cmd = '%s %s' % (import_sgin, sgin_path_and_info)
		os.system(sign_cmd)
		#java -jar /Users/mac/Desktop/360jiagubao_mac/jiagu/jiagu.jar -jiagu /Users/mac/Desktop/jindanlicai_android-6.3.1.71.apk /Users/mac/Desktop/
		channleinfo_all_cmd = r'java -jar /Users/mac/Desktop/360jiagubao_mac/jiagu/jiagu.jar -importmulpkg'
		channleinfo_path = r'/Users/mac/Desktop/channel/channle.txt'
		print '================= %s' % (channel_name)
		if channel_package == '1':
			if(channel_name == 'all'):
				channel_cmd = '%s %s' % (channleinfo_all_cmd, channleinfo_path)
			else:
				mk_channelInfo_file(channel_name,channel_package)
				channleinfo_path = r'/Users/mac/Desktop/channel/singlechannle.txt'
				
		elif channel_package == '2':
			mk_channelInfo_file(channel_value,channel_package)
			channleinfo_path = r'/Users/mac/Desktop/channel/muchannle.txt'
			
		channel_cmd = '%s %s' % (channleinfo_all_cmd, channleinfo_path)
		os.system(channel_cmd)
		jiagu_cmd = r'java -jar /Users/mac/Desktop/360jiagubao_mac/jiagu/jiagu.jar -jiagu %s %s -autosign -pkgparam %s -automulpkg '  % (apk_ori_path, output_directory,channleinfo_path)
		os.system(jiagu_cmd)
		delete_temp_file(output_directory);
	
	print '4444444444444444444444444'
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

def delete_temp_file(filePath):
	if os.path.exists(filePath) == False:
		return
	delList = os.listdir(filePath)
	for f in delList:
		print 'filePath========='+f
		if 'temp' in f:
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
