#!/usr/bin/python
# -*- coding: utf-8 -*-  

"""Usage:
  ci_android_app_jiagu.py init [--projectname=<projectname>]
  ci_android_app_jiagu.py deliver [--projectname=<projectname>] [--appname=<app_name>] [--versionname=<version_name>] [--branch=<branch>] [--buildversion=<builder_number>] [--buildtype=build_type] [--channel=<channel>] [--buildtime=<build_time>]

"""

import os, sys, time, json, shutil, glob
from docopt import docopt
from biplist import *
import qrcode
from PIL import Image
from BeautifulSoup import BeautifulSoup
from gradle_properties import GradleProperties

# 配置文件相关信息
# 加固助手目录
JIAGU_HOME = '/home/t1/software/360jiagubao'
# Jenkins目录
JENKINS_HOME = '/home/t1/jenkins'
# WorkSpace目录
WORKSPACE_PATH = JENKINS_HOME + '/workspace'
# 执行脚本目录
CI_ANDROID_PATH = JENKINS_HOME + '/scripts/src/android'
# 模板文件
CI_ANDROID_TEMPLATES_PATH = CI_ANDROID_PATH + '/templates'


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
	build_type = arguments['--buildtype']
        if build_type == None:
            build_type = 'release'
        # 渠道打包
        channel = arguments['--channel']
        if channel == None:
            channel = 'wxdw'

        app_name = arguments['--appname']
        if app_name == None:
            app_name = projectname

	# 判断是否是安卓工程
	project_path = r'%s/%s' % (WORKSPACE_PATH, projectname)
	if os.path.exists(project_path) == False:
		raise "project folder not found"

	listdir = os.listdir(project_path)
	is_android_project = False
	gradle_property_path = ''
	for t_dir in listdir:
		if t_dir.find('gradle.properties') != -1:
			is_android_project = True
			gradle_property_path = r'%s/%s' % (project_path, t_dir)
					

	if is_android_project == False:
		raise 'current path is not an android project'

	project_build_path = project_path + '/builds'
	if os.path.exists(project_build_path) == False:
		# 创建build文件夹
		os.system('mkdir ' + project_build_path)

	if os.path.exists(project_build_path) == False:
		raise 'could not create builds path'

	# copy 配置文件
	ci_config_path = CI_ANDROID_TEMPLATES_PATH + '/config.json'
	project_config_path = project_build_path + '/config.json'
	if os.path.exists(project_config_path) == False:
		copy_cmd = r'cp %s %s' % (ci_config_path, project_config_path)
		#print copy_cmd
		os.system(copy_cmd)

	# copy download.html
	ci_download_path = CI_ANDROID_TEMPLATES_PATH + '/download.html'
	project_download_path = project_build_path + '/download.html'
	if os.path.exists(project_download_path) == False:
		copy_cmd = r'cp %s %s' % (ci_download_path, project_download_path)
		os.system(copy_cmd)

		# copy info.plist
		# ci_info_plist_path = CI_ANDROID_TEMPLATES_PATH + '/info.plist'
		# copy_cmd = r'cp %s %s' % (ci_info_plist_path, project_build_path)
		# os.system(copy_cmd)
	#else:
	#	raise 'app has init'

	# Gemfile
	ci_gemfile_path = CI_ANDROID_TEMPLATES_PATH + '/Gemfile'
	copy_cmd = r'cp %s %s' % (ci_gemfile_path, project_path)
	os.system(copy_cmd)
	os.system('bundle install')

	# fastlane文件夹
	ci_fastlane_path = CI_ANDROID_TEMPLATES_PATH + '/fastlane'
	copy_cmd = r'cp -R %s %s' % (ci_fastlane_path, project_path)
	os.system(copy_cmd)

        print gradle_property_path
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
				update_config_value(config_data, 'app_name', app_name)
				update_config_value(config_data, 'output_directory', project_build_path)
				update_config_value(config_data, 'gradle_properties_path', gradle_property_path)
				update_config_value(config_data, 'project_name', projectname)
				update_config_value(config_data, 'build_type', build_type)
				update_config_value(config_data, 'channel', channel)

			if config_data:
				with open(project_config_path, 'w') as json_file:
					json_file.write(json.dumps(config_data))
		except Exception as e:
			raise e

# 通过命令打包app
def deliver_app(arguments):
	print 'start deliver app'
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
	project_download_path = project_build_path + '/download.html'
	if os.path.exists(project_build_path) == False or os.path.exists(project_fastlane_path) == False or os.path.exists(project_config_path) == False or os.path.exists(project_download_path) == False :
		init_app(arguments)

	# 实时更新config.json模板(fix: 防止模板更新后参数丢失问题)
	# copy 配置文件
        ci_config_path = CI_ANDROID_TEMPLATES_PATH + '/config.json'
        copy_cmd = r'cp %s %s' % (ci_config_path, project_build_path)
        print copy_cmd
        os.system(copy_cmd)
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

        build_type = arguments['--buildtype']
        if build_type == None:
                raise "build type is nil"
        update_config_value(config_data, 'build_type', build_type)

        build_time = arguments['--buildtime']
        if build_time == None:
		# 初始化为当前时间
                #获得当前时间时间戳 
		now = int(time.time()) 
		#转换为其他日期格式,如:"yyyyMMddHHmmss" 
		timeStruct = time.localtime(now) 
		build_time = time.strftime("%Y%m%d%H%M%S", timeStruct) 
		print(build_time)
        update_config_value(config_data, 'build_time', build_time)

        app_name = arguments['--appname']
	if app_name == None:
		app_name = projectname
        update_config_value(config_data, 'app_name', app_name)

        #version_code = arguments['--versioncode']
	#if version_code = None:
	#	version_code = 1
	#update_config_value(config_data, 'version_code', version_name.replace('.',''))


	channel_name = arguments['--channel']
	if channel_name == None:
            channel_name = 'main'
	update_config_value(config_data, 'channel', channel_name)

	branch = arguments['--branch']
	if branch == None:
            branch = 'master'
	update_config_value(config_data, 'branch', branch)

	build_version_code = arguments['--buildversion']
	if build_version_code == None:
            build_version_code = 1 
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
	app_name = get_config_value(config_data, 'app_name')
	gradle_property_path = get_config_value(config_data, 'gradle_properties_path')
	version_name = get_config_value(config_data, 'version_name')
	version_code = get_config_value(config_data, 'version_code')
        build_version_code = get_config_value(config_data, 'build_version_code')
	build_type = get_config_value(config_data, 'build_type')
	build_time = get_config_value(config_data, 'build_time')
	channel_name = get_config_value(config_data, 'channel')
	gradle_properties =  GradleProperties(gradle_property_path)
	gradle_properties.readProperties()
	output_directory = get_config_value(config_data, 'output_directory')
	output_name = r'%s_V%s_%s_%s_%s.apk' % (app_name, version_name, build_type, channel_name, build_time)
	# 多渠道打包功能适配
	assemble_type = ''
	if cmp(channel_name, 'all') == 0:
		assemble_type = 'assemble'
	else:
		assemble_type = r'assemble%s' % (channel_name)
		
	build_type = get_config_value(config_data, 'build_type')
	#app_name = get_config_value(config_data, 'app_name')
	#if export_method != 'release':
	#	app_name = r'%s#%s' % (app_name, bundle_version)
	

	# 删除旧文件
	rm_history_cmd = r'rm -rf %s/*.apk' % (output_directory)
	os.system(rm_history_cmd)

	# 更新gradle文件
	gradle_properties = GradleProperties(gradle_property_path)
	gradle_properties.readProperties()
	gradle_properties.updateProperties('APPNAME', app_name)
	gradle_properties.updateProperties('VERSION_NAME', version_name)
	#gradle_properties.updateProperties('VERSION_CODE', version_code)
        gradle_properties.updateProperties('PRODUCT_FLAVORS', channel_name)
        gradle_properties.updateProperties('BUILD_TYPE', build_type)
        gradle_properties.updateProperties('BUILD_TIME', build_time)
	gradle_properties.updateProperties('MULTI_PRODUCT_ENABLE', 'true')
	gradle_properties.updateProperties('org.gradle.jvmargs', '-Xmx4096m -XX:MaxPermSize=512m -XX:+HeapDumpOnOutOfMemoryError -Dfile.encoding=UTF-8')
	gradle_properties.saveProperties()
        #raise 'save config file'

	# 更新fir文件
	# fir publish /Users/tommy/Desktop/ci/Project/TesBm/金蛋理财-1.0.0.60.ipa -T ec84ed490c01da5725cae153c558590a
	# fir_str = r'fir publish %s/%s -T ec84ed490c01da5725cae153c558590a' % (output_directory, output_name)
	# fir_path = r'%s/fastlane/fir.sh' % (project_path)
	# with open(fir_path, 'w') as fir_file:
	# 	fir_file.write(fir_str)

	# 更新gem
	#ret = os.system("bundle update")
	#print r'bundle update value:%s:%s' % (os.getcwd(), str(ret))
	#if os.system("bundle update") != 0:
	#	raise "bundle update failed"

	# 修改权限, gradle执行需要权限
	oa_cmd = r'chmod -R 777 %s' % project_path
	os.system(oa_cmd)
	
	# 拼接fastlane命令
	fastlane_cmd = r'fastlane android deploy output_name:%s version_name:%s build_version_code:%s gradle_properties_path:%s assemble_type:%s  build_type:%s output_directory:%s project_path:%s' % (output_name, version_name, build_version_code, get_config_value(config_data, 'gradle_properties_path'), assemble_type, build_type, output_directory, get_config_value(config_data, 'project_path'))
	print fastlane_cmd
	
	# 执行fastlane命令
	if os.system(fastlane_cmd) != 0:
		raise "fastlane excute failed"
	print '222222222222222222222222'
	# copy apk文件到输出目录(兼容渠道打包)
	apk_folder_path = detact_apk_output_path(project_path)
	if apk_folder_path == None:
		raise "not find output directory"
	listdir = os.listdir(apk_folder_path)
	apk_file = ''
	for t_dir in listdir:
		if t_dir.find('.apk') != -1:
			apk_file = apk_folder_path + '/' + t_dir
                        apk_ori_path = output_directory + '/' + t_dir
        		copy_apk_cmd = r'cp %s %s' %(apk_file, apk_ori_path)
        		os.system(copy_apk_cmd)

	if apk_file == '':
		raise "not found apk file"

	print '3333333333333333333333333'
	channel_name = get_config_value(config_data, 'channel')
        # 关闭加固
	if channel_name == None:
                jiagu_path = r'%s/jiagu/jiagu.jar' % (JIAGU_HOME)
                login_cmd = r'java -jar %s -login joedan0104 YNjoe674121' % (jiagu_path)
		os.system(login_cmd)
		import_sgin = r'java -jar %s -importsign' % (jiagu_path)
		sgin_path_and_info = r'%s/app/keystore/mykey 123456 cdel 123456' % (project_path)
		sign_cmd = '%s %s' % (import_sgin, sgin_path_and_info)
		os.system(sign_cmd)
		#java -jar /Users/mac/Desktop/360jiagubao_mac/jiagu/jiagu.jar -jiagu /Users/mac/Desktop/jindanlicai_android-6.3.1.71.apk /Users/mac/Desktop/
		channelinfo_all_cmd = r'java -jar %s -importmulpkg' % (jiagu_path)
		channelinfo_path = r'%s/channel.txt' % (CI_ANDROID_TEMPLATES_PATH)
		print '================= %s' % (channel_name)
		if(channel_name == 'all'):
                    # 初始化全部渠道
		    if os.path.exists(channelinfo_path) == False:
		        mk_channelInfo_file('wxdw,agent127,agent1679,agent1824,wxbaidu,wx360,wxyyb,wxxiaomi,wxvivo', channelinfo_path)
		    channel_cmd = '%s %s' % (channelinfo_all_cmd, channelinfo_path)
		else:
                    channelinfo_path = r'%s/singlechannel.txt' % (CI_ANDROID_TEMPLATES_PATH)
		    mk_channelInfo_file(channel_name, channelinfo_path)
		
		channel_cmd = '%s %s' % (channelinfo_all_cmd, channelinfo_path)
		os.system(channel_cmd)
		jiagu_cmd = r'java -jar %s -jiagu %s %s -autosign -pkgparam %s -automulpkg '  % (jiagu_path, apk_ori_path, output_directory, channelinfo_path)
		print jiagu_cmd
		os.system(jiagu_cmd)
		# 输出目录临时文件删除
		delete_temp_file(output_directory)        
	
	print '4444444444444444444444444'
	# 部署mapping文件
	mapping_folder_path = os.path.dirname(apk_folder_path) + os.sep + 'mapping'
	deloy_mapping_file(mapping_folder_path, output_directory)

	# 生成文件部署到nginx
	deloy_nginx_static_file(project_config_path, projectname, output_name)

# 探测项目下的APK输出目录路径
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
	if os.path.exists(output_directory) == True:
		for fn in glob.glob(output_directory + os.sep + '*.apk'):
                        print fn
                        # 查找一个有效的包
                        return True
	return False

# 输出目录生成用于二维码显示的APK文件
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

	app_name = get_config_value(config_data, 'app_name')
	version_name = get_config_value(config_data, 'version_name')
	build_type = get_config_value(config_data, 'build_type')
        build_version_code = get_config_value(config_data, 'build_version_code')
	build_time = get_config_value(config_data, 'build_time')
	output_directory = get_config_value(config_data, 'output_directory')
	nginx_html_path = get_config_value(config_data, 'nginx_html_path')
	server_ip = get_config_value(config_data, 'server_ip')
        channel_name = get_config_value(config_data, 'channel')

	# 创建需要的文件夹
	server_project_folder = nginx_html_path + '/' + projectname
	if os.path.exists(server_project_folder) == False:
		os.system('mkdir ' + server_project_folder)
	# nginx部署当前版本的目录
	server_bundle_folder = server_project_folder + '/' + version_name
	if os.path.exists(server_bundle_folder) == False:
		os.system('mkdir ' + server_bundle_folder)
	# 按照时间进行文件处理
	server_bundle_folder = server_project_folder + '/' + version_name + '/' + build_time
	if os.path.exists(server_bundle_folder) == False:
		os.system('mkdir ' + server_bundle_folder)
	
	root_http_url = 'http://' + server_ip + '/' + projectname + '/' +  version_name + '/' + build_time
	apk_server_url = root_http_url + '/' + output_name
	download_url = root_http_url + '/' + 'download.html'

	# builds下文件路径
	download_html_path = output_directory + '/download.html'
	apk_path = output_directory + '/' + output_name
        # 重新定位输出文件(如果是渠道包的情况优先使用渠道包)
        if os.path.exists(output_directory):
            for fn in glob.glob(output_directory + os.sep + '*.apk'):
                print fn
                # 将目标文件拷贝到nginx目录
                apk_path = fn
                copy_apk_cmd = r'cp %s %s' % (apk_path, server_bundle_folder)
                os.system(copy_apk_cmd)
        else:
            raise 'could not find output directory'

	# 修改二维码目标文件路径(默认采用主渠道)
	apk_qr_path = server_bundle_folder + os.sep + output_name
	apk_server_url = root_http_url + '/' + output_name
	if os.path.exists(apk_qr_path) == False:
		# 新创建一个用于显示二维码的APK文件(all渠道的时候)
		copy_apk_cmd = r'cp %s %s' % (apk_path, apk_qr_path)
                os.system(copy_apk_cmd)
	if os.path.exists(apk_qr_path) == False:
		raise 'can not find server qrcode apk file'

	# 将mapping.txt部署到nginx目录下
        if os.path.exists(output_directory):
            for fn in glob.glob(output_directory + os.sep + 'mapping.txt'):
                print fn
                # 将目标文件拷贝到nginx目录
                mapping_path = fn
                copy_mapping_cmd = r'cp %s %s' % (mapping_path, server_bundle_folder)
                os.system(copy_mapping_cmd)
		print copy_mapping_cmd

	# 重命名为目标文件用于生成二维码
	if os.path.exists(apk_qr_path) == False:
		raise 'qrcode apk file not exists'
        apk_server_url = root_http_url + '/' + os.path.basename(apk_qr_path)

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
	generate_qrcode_image(apk_server_url, server_bundle_folder)
	#print "download html: " + download_url	
	#img_code_path = server_bundle_folder + '/' + 'qr.png'
	#print "qrcode path: " + img_code_path
	#qr = qrcode.QRCode(version=1, box_size=10, border=1)
	#qr.add_data(download_url)
	#img = qr.make_image()	
	#img.save(img_code_path)	

	# 创建nginx需要的文件(download.html)
	copy_download_html_cmd = r'cp %s %s' % (download_html_path, server_bundle_folder)
	os.system(copy_download_html_cmd)

	# 修改权限
	oa_cmd = r'chmod -R 777 %s' % server_project_folder
	os.system(oa_cmd)

# 生成Qrcode图片文件
def generate_qrcode_image(download_url, server_bundle_folder):
        # 生成二维码    
        print "download html: " + download_url
        img_code_path = server_bundle_folder + '/' + 'qr.png'
        print "qrcode path: " + img_code_path
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(download_url)
        img = qr.make_image()
        img.save(img_code_path)


# 将构建生成的mapping文件部署到输出目录
def deloy_mapping_file(build_output_directory, target_directory):
        print 'find and copy mapping file to target directory\n'
        for root, dirs, files in os.walk(build_output_directory, True, None, False):
                for file in files:
                        try:
                                #print '-----------------------------------'
                                file_name = os.path.splitext(file)[0]
                                file_suffix = os.path.splitext(file)[1]
                                file_path = os.path.join(root, file)
                                file_abs_path = os.path.abspath(file)
                                file_parent = os.path.dirname(file_path)
                                #print "file : {0}".format(file)
                                #print "file_name : {0}".format(file_name)
                                #print "file_suffix : {0}".format(file_suffix)
                                #print "file_path : {0}".format(file_path)
                                #print "file_abs_path : {0}".format(file_abs_path)
                                #print "file_parent : {0}".format(file_parent)
                                if file.find('mapping.txt') != -1:
                                        #print r'mapping file %s' % (file)
                                        sub_file = os.path.basename(file_parent)
                                        if sub_file.find('release') != -1:
                                                # release目录需要继续查找父目录作为渠道标识
                                                file_parent = os.path.dirname(file_parent)
                                                sub_file = os.path.basename(file_parent)
                                        target_file_name = target_directory + os.sep + file
                                        #just copy one mapping file to output directory
                                        copy_cmd = r'cp %s %s' % (file_path, target_file_name)
                                        os.system(copy_cmd)
					print copy_cmd
					return
                        except Exception, e:
                                print "Exception", e
	
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
			delete_file = '%s/%s' % (filePath, f)
			print 'delete_file========='+delete_file
			os.remove(delete_file)
			
	
def mk_channelInfo_file(channelname, channelInfoPath):

	filePath = CI_ANDROID_TEMPLATES_PATH
	if ',' in channelname:
		list = channelname.split(',')
		txtname = r'channel.txt'
		path = os.path.join(filePath, txtname)
		if os.path.exists(path):
			os.remove(path)
		if len(list):
			for i in range(len(list)):
				print "item==========="+list[i]
				try:
					with open(path, 'a+') as f:
						channel = '%s %s %s\n' % ('UMENG_CHANNEL', list[i], list[i].replace(' ', ''))
						f.write(channel)
				except Exception as e:
					raise e
	else:
		try:
			txtname = r'singlechannel.txt'
			path = os.path.join(filePath, txtname)
			with open(path, 'w') as f:
				channel = '%s %s %s' % ('UMENG_CHANNEL',channelname, channelname.replace(' ', ''))
				f.write(channel)
		except Exception as e:
			raise e
			

	

if __name__ == '__main__':
	reload(sys)
	sys.setdefaultencoding('utf8')
	arguments = docopt(__doc__)
	handle_args(arguments)
