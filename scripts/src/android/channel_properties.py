#!/usr/bin/python
# -*- coding: UTF-8 -*-
# application channel property
# channel_name-->channel properties dicitionary
# create at: 2019/4/21 15:34:30
import os

class ChannelProperty:
	'渠道配置信息'

	def __init__(self, name):
		self.name = name
		self.properties = {}

	# 设置渠道属性
	def setProperty(self, key, value):
		self.properties[key] = value

	# 获取渠道名称
	def getName(self):
		return self.name

	# 获取渠道属性字典
	def getProperties(self):
		return self.properties
		
	# 显示渠道信息
	def toString(self):
		print "Name: ", self.name, ", properties dictionary: ", self.properties



