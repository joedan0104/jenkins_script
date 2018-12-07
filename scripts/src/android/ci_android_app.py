#!/usr/bin/python
# -*- coding: utf-8 -*-  

"""Usage:
  ci_ios_app.py init [--projectname=<projectname>]
  ci_ios_app.py deliver [--projectname=<name>] [--buildtype=<name>] [--versionname=<si>] 
  [--buildversioncode=<abc>] [--branch=<branch>]
"""

import os, sys, json
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
				update_config_value(config_data, 'version_name', gradle_properties.getProperty('VERSION_NAME'))
				update_config_value(config_data, 'build_version_code', gradle_properties.getProperty('BUILD_VERSION_CODE'))
				update_config_value(config_data, 'project_path', project_path)
				update_config_value(config_data, 'output_directory', project_build_path)
				update_config_value(config_data, 'gradle_properties_path', gradle_property_path)

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


	build_type = arguments['--buildtype']
	if build_type == None:
		raise "build type is nil"
	elif build_type not in ['debug', 'release']:
		raise "build type not support"
	update_config_value(config_data, 'build_type', build_type)

	version_name = arguments['--versionname']
	if version_name == None:
		raise "version name is nil"
	update_config_value(config_data, 'version_name', version_name)

	build_version_code = arguments['--buildversioncode']
	if build_version_code == None:
		raise "build version code is nil"
	update_config_value(config_data, 'build_version_code', build_version_code)

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

	project_path = get_config_value(config_data, 'project_path')
	gradle_property_path = get_config_value(config_data, 'gradle_properties_path')
	build_version_code = get_config_value(config_data, 'build_version_code')
	version_name = get_config_value(config_data, 'version_name')
	output_directory = get_config_value(config_data, 'output_directory')
	output_name = r'%s-%s.%s.apk' % (projectname, version_name, build_version_code)	
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
	gradle_properties.updateProperties('BUILD_VERSION_CODE', build_version_code)
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
	cmd_project = r"cd %s" % project_path
	c_project_path = os.getcwd()
	if cmd_project != c_project_path:
		print cmd_project
		os.system(cmd_project)

	if os.system(fastlane_cmd) != 0:
		raise "fastlane excute failed"

	# copy apk文件
	apk_folder_path = project_path + '/app/build/outputs/apk'
	listdir = os.listdir(apk_folder_path)
	apk_file = ''
	for t_dir in listdir:
		if t_dir.find('.apk') != -1:
			apk_file = apk_folder_path + '/' + t_dir

	if apk_file == '':
		raise "not found apk file"
	copy_apk_cmd = r'cp %s %s/%s' %(apk_file, output_directory, output_name)
	os.system(copy_apk_cmd)

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

if __name__ == '__main__':
	reload(sys)
	sys.setdefaultencoding('utf8')
	arguments = docopt(__doc__)
	handle_args(arguments)
