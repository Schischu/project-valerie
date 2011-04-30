# -*- coding: utf-8 -*-

import os

from Components.config import config
from Tools.Import import my_import

from Plugins.Extensions.ProjectValerie.__common__ import printl2 as printl

#------------------------------------------------------------------------------------------

gPlugins = []

def loadPlugins(dir, imp):
	for f in os.listdir(dir):
		file = os.path.join(dir, f)
		if os.path.isfile(file):
			pos = f.find(".py")
			if pos > 0:
				f = f[:pos]
				#printl("f: " + str(f), __name__)
				if f == "__init__":
					continue
				try:
					m = __import__(imp + f)
				except Exception, ex:
					printl("Exception: " + str(ex), __name__)
					printl("\tf: " + str(f), __name__)

def registerPlugin(plugin):
	#printl("name=" + str(plugin.name) + " where=" + str(plugin.where), __name__)
	ps = []
	if type(plugin) is list:
		ps = plugin
	else:
		ps.append(plugin)
	for p in ps:
		if p not in gPlugins:
			printl("registered: name=" + str(p.name) + " where=" + str(p.where), __name__)
			gPlugins.append(p)

def getPlugins(where=None):
	if where is None:
		return gPlugins
	else:
		list = []
		for plugin in gPlugins:
			if plugin.where == where:
				list.append(plugin)
		return list

class Plugin():

	MENU_MAIN = 1
	MENU_PICTURES = 2
	MENU_MUSIC = 3
	MENU_VIDEOS = 4
	MENU_MOVIES = 5
	MENU_TVSHOWS = 6
	MENU_PROGRAMS = 7
	MENU_SYSTEM = 8
	
	AUTOSTART = 9
	
	SETTINGS = 10
	
	MENU_MOVIES_PLUGINS = 11
	
	INFO_PLAYBACK = 100

	name  = None
	start = None
	fnc   = None
	where = None
	supportStillPicture = False

	def __init__(self, name=None, start=None, fnc=None, where=None, supportStillPicture=False):
		self.name = name
		self.start = start
		self.fnc = fnc
		self.where = where
		self.supportStillPicture = supportStillPicture
